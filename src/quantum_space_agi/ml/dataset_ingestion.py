"""Offline ingestion of an already acquired, complete TAP VOTable payload."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import TypeAlias

from quantum_space_agi.data.models import JSONScalar
from quantum_space_agi.errors import ValidationError
from quantum_space_agi.ml.dataset_validation import (
    VALIDATION_POLICY_VERSION,
    DatasetValidationReport,
    ExcludedRow,
    validate_baseline_records,
)
from quantum_space_agi.ml.votable_validation import (
    VOTABLE_VALIDATOR_VERSION,
    VOTableField,
    VOTableValidationError,
    validate_tap_votable,
)

REQUIRED_COLUMNS = ("pl_rade", "pl_bmasse", "pl_name", "hostname", "pl_refname")
_NUMERIC_COLUMNS = frozenset({"pl_rade", "pl_bmasse"})
_IDENTITY_COLUMNS = frozenset({"pl_name", "hostname", "pl_refname"})
INGESTION_MANIFEST_VERSION = "arc08-offline-ingestion-manifest/1"
INGESTION_PARSER_VERSION = "arc08-votable-tabledata-parser/1"
_MAX_METADATA_VALUE_BYTES = 4096

CallerScalar: TypeAlias = str | int | float | bool | None


class DatasetIngestionError(ValidationError):
    """A payload or its ingestion metadata cannot produce a valid result."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class IngestionMetadata:
    """Optional caller-supplied context; absent values are never synthesized."""

    source_identifier: str | None = None
    tap_endpoint: str | None = None
    adql_query: str | None = None
    query_parameters: tuple[tuple[str, CallerScalar], ...] = ()
    acquisition_timestamp: datetime | None = None
    job_identifier: str | None = None
    http_response_metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "source_identifier",
            "tap_endpoint",
            "adql_query",
            "job_identifier",
        ):
            _validate_optional_text(field_name, getattr(self, field_name))
        if self.acquisition_timestamp is not None and (
            not isinstance(self.acquisition_timestamp, datetime)
            or self.acquisition_timestamp.tzinfo is None
            or self.acquisition_timestamp.utcoffset() is None
        ):
            raise DatasetIngestionError(
                "invalid_metadata",
                "acquisition_timestamp must be a timezone-aware datetime when supplied",
            )
        if type(self.query_parameters) is not tuple:
            raise DatasetIngestionError(
                "invalid_metadata",
                "query_parameters must be a tuple of key/value pairs",
            )
        parameters: list[tuple[str, CallerScalar]] = []
        for item in self.query_parameters:
            if type(item) is not tuple or len(item) != 2:
                raise DatasetIngestionError(
                    "invalid_metadata", "each query parameter must be a two-item tuple"
                )
            key, value = item
            _validate_metadata_text("query parameter name", key)
            _validate_caller_scalar(value)
            if _is_sensitive_name(key):
                raise DatasetIngestionError(
                    "invalid_metadata",
                    "sensitive query parameter metadata is not retained",
                )
            parameters.append((key, value))
        if len({key for key, _ in parameters}) != len(parameters):
            raise DatasetIngestionError(
                "invalid_metadata", "query parameter names must be unique"
            )
        object.__setattr__(self, "query_parameters", tuple(sorted(parameters)))

        if type(self.http_response_metadata) is not tuple:
            raise DatasetIngestionError(
                "invalid_metadata", "http_response_metadata must be a tuple of pairs"
            )
        headers: list[tuple[str, str]] = []
        for item in self.http_response_metadata:
            if type(item) is not tuple or len(item) != 2:
                raise DatasetIngestionError(
                    "invalid_metadata",
                    "each HTTP metadata entry must be a two-item tuple",
                )
            name, value = item
            _validate_metadata_text("HTTP metadata name", name)
            _validate_metadata_text("HTTP metadata value", value)
            if _is_sensitive_name(name):
                raise DatasetIngestionError(
                    "invalid_metadata", "sensitive HTTP metadata is not retained"
                )
            headers.append((name, value))
        if len({name for name, _ in headers}) != len(headers):
            raise DatasetIngestionError(
                "invalid_metadata", "HTTP metadata names must be unique"
            )
        object.__setattr__(self, "http_response_metadata", tuple(sorted(headers)))


@dataclass(frozen=True, slots=True)
class IngestionManifest:
    """Immutable caller context plus values calculated by this ingestion."""

    manifest_version: str
    caller_metadata: IngestionMetadata
    raw_response_byte_count: int
    raw_response_sha256: str
    validation_status: str
    serialization: str
    detected_fields: tuple[VOTableField, ...]
    extracted_row_count: int
    accepted_row_count: int
    excluded_row_count: int
    validation_policy_version: str
    validator_version: str
    parser_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.caller_metadata, IngestionMetadata):
            raise DatasetIngestionError(
                "invalid_metadata", "caller_metadata must be IngestionMetadata"
            )
        if any(
            type(value) is not int or value < 0
            for value in (
                self.raw_response_byte_count,
                self.extracted_row_count,
                self.accepted_row_count,
                self.excluded_row_count,
            )
        ):
            raise DatasetIngestionError(
                "count_inconsistency", "manifest counts must be non-negative integers"
            )
        if (
            self.accepted_row_count + self.excluded_row_count
            != self.extracted_row_count
        ):
            raise DatasetIngestionError(
                "count_inconsistency", "accepted and excluded counts must reconcile"
            )
        if (
            type(self.raw_response_sha256) is not str
            or len(self.raw_response_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in self.raw_response_sha256
            )
        ):
            raise DatasetIngestionError(
                "invalid_manifest", "raw_response_sha256 must be lowercase SHA-256"
            )
        if type(self.detected_fields) is not tuple or any(
            not isinstance(item, VOTableField) for item in self.detected_fields
        ):
            raise DatasetIngestionError(
                "invalid_manifest", "detected_fields must be a tuple"
            )


@dataclass(frozen=True, slots=True)
class DatasetIngestionResult:
    """Accepted, immutable records and a complete exclusion ledger."""

    manifest: IngestionManifest
    accepted_records: tuple[Mapping[str, JSONScalar], ...]
    accepted_source_row_indices: tuple[int, ...]
    exclusion_ledger: tuple[ExcludedRow, ...]
    validation_report: DatasetValidationReport

    def __post_init__(self) -> None:
        records_list: list[Mapping[str, JSONScalar]] = []
        for record in self.accepted_records:
            if not isinstance(record, Mapping):
                raise DatasetIngestionError(
                    "invalid_result", "accepted records must be mappings"
                )
            copied = dict(record)
            if any(type(field) is not str for field in copied):
                raise DatasetIngestionError(
                    "invalid_result", "accepted record field names must be strings"
                )
            if any(
                value is not None and type(value) not in (str, int, float, bool)
                for value in copied.values()
            ):
                raise DatasetIngestionError(
                    "invalid_result", "accepted record values must be immutable scalars"
                )
            records_list.append(MappingProxyType(copied))
        records = tuple(records_list)
        accepted_indices = tuple(self.accepted_source_row_indices)
        excluded_rows = tuple(self.exclusion_ledger)
        if not isinstance(self.manifest, IngestionManifest):
            raise DatasetIngestionError(
                "invalid_result", "manifest must be IngestionManifest"
            )
        if not isinstance(self.validation_report, DatasetValidationReport):
            raise DatasetIngestionError(
                "invalid_result", "validation_report must be DatasetValidationReport"
            )
        if (
            accepted_indices != self.validation_report.valid_record_indices
            or excluded_rows != self.validation_report.excluded_rows
        ):
            raise DatasetIngestionError(
                "validation_mismatch",
                "accepted row indices and exclusion ledger must match the "
                "validation report",
            )
        if (
            self.manifest.validation_policy_version
            != self.validation_report.policy_version
        ):
            raise DatasetIngestionError(
                "validation_mismatch",
                "manifest validation policy version must match the validation report",
            )
        if any(type(index) is not int for index in accepted_indices):
            raise DatasetIngestionError(
                "invalid_result", "accepted row indices must be integers"
            )
        if any(not isinstance(row, ExcludedRow) for row in excluded_rows):
            raise DatasetIngestionError(
                "invalid_result", "exclusion_ledger has invalid entries"
            )
        if len(records) != self.manifest.accepted_row_count:
            raise DatasetIngestionError(
                "count_inconsistency", "accepted record count is inconsistent"
            )
        if len(excluded_rows) != self.manifest.excluded_row_count:
            raise DatasetIngestionError(
                "count_inconsistency", "exclusion ledger count is inconsistent"
            )
        if len(accepted_indices) != len(records):
            raise DatasetIngestionError(
                "count_inconsistency", "accepted row indices are inconsistent"
            )
        excluded_indices = tuple(row.row_index for row in excluded_rows)
        all_indices = accepted_indices + excluded_indices
        expected_indices = tuple(range(self.manifest.extracted_row_count))
        if tuple(sorted(all_indices)) != expected_indices or len(
            set(all_indices)
        ) != len(all_indices):
            raise DatasetIngestionError(
                "count_inconsistency",
                "accepted rows and exclusions must account for every source row",
            )
        if accepted_indices != tuple(
            sorted(accepted_indices)
        ) or excluded_indices != tuple(sorted(excluded_indices)):
            raise DatasetIngestionError(
                "invalid_result", "row traceability indices must preserve order"
            )
        if self.validation_report.record_count != self.manifest.extracted_row_count:
            raise DatasetIngestionError(
                "count_inconsistency", "validation report row count is inconsistent"
            )
        object.__setattr__(self, "accepted_records", records)
        object.__setattr__(self, "accepted_source_row_indices", accepted_indices)
        object.__setattr__(self, "exclusion_ledger", excluded_rows)


def ingest_votable_payload(
    raw_payload: bytes, *, metadata: IngestionMetadata | None = None
) -> DatasetIngestionResult:
    """Validate and ingest an already acquired TABLEDATA VOTable payload offline.

    The exact original bytes are hashed before parsing. Only scalar TABLEDATA
    payloads pass; other VOTable serializations fail explicitly because the
    existing validator does not decode them. No network access or timestamp
    generation occurs. The caller must provide all acquisition metadata it has.
    """
    if type(raw_payload) is not bytes:
        raise DatasetIngestionError(
            "invalid_payload", "raw_payload must be immutable bytes"
        )
    if not raw_payload:
        raise DatasetIngestionError("empty_payload", "raw VOTable payload is empty")
    if metadata is None:
        supplied_metadata = IngestionMetadata()
    elif isinstance(metadata, IngestionMetadata):
        supplied_metadata = metadata
    else:
        raise DatasetIngestionError(
            "invalid_metadata", "metadata must be IngestionMetadata"
        )

    response_digest = hashlib.sha256(raw_payload).hexdigest()
    try:
        validation = validate_tap_votable(
            raw_payload, required_columns=REQUIRED_COLUMNS
        )
    except VOTableValidationError as exc:
        raise DatasetIngestionError(exc.code, str(exc)) from exc
    if validation.serialization != "TABLEDATA":
        raise DatasetIngestionError(
            "unsupported_serialization",
            f"{validation.serialization} is validated structurally but cannot be "
            "extracted offline",
        )
    if validation.tabledata_rows is None or validation.row_count is None:
        raise DatasetIngestionError(
            "incomplete_serialization", "validated TABLEDATA has no decoded rows"
        )
    _validate_required_field_types(validation.fields)

    records: list[Mapping[str, JSONScalar]] = []
    for row_values in validation.tabledata_rows:
        if len(row_values) != len(validation.columns):
            raise DatasetIngestionError(
                "count_inconsistency",
                "parsed row width does not match detected columns",
            )
        records.append(
            MappingProxyType(
                {
                    column: value
                    for column, value in zip(
                        validation.columns, row_values, strict=True
                    )
                }
            )
        )

    report = validate_baseline_records(tuple(records))
    accepted_indices = report.valid_record_indices
    excluded_rows = report.excluded_rows
    accepted_records = tuple(records[index] for index in accepted_indices)
    manifest = IngestionManifest(
        manifest_version=INGESTION_MANIFEST_VERSION,
        caller_metadata=supplied_metadata,
        raw_response_byte_count=len(raw_payload),
        raw_response_sha256=response_digest,
        validation_status=validation.status,
        serialization=validation.serialization,
        detected_fields=validation.fields,
        extracted_row_count=validation.row_count,
        accepted_row_count=len(accepted_records),
        excluded_row_count=len(excluded_rows),
        validation_policy_version=VALIDATION_POLICY_VERSION,
        validator_version=VOTABLE_VALIDATOR_VERSION,
        parser_version=INGESTION_PARSER_VERSION,
    )
    return DatasetIngestionResult(
        manifest=manifest,
        accepted_records=accepted_records,
        accepted_source_row_indices=accepted_indices,
        exclusion_ledger=excluded_rows,
        validation_report=report,
    )


def serialize_ingestion_manifest(manifest: IngestionManifest) -> bytes:
    """Serialize a manifest as deterministic compact UTF-8 JSON without a BOM."""
    if not isinstance(manifest, IngestionManifest):
        raise DatasetIngestionError(
            "invalid_manifest", "manifest must be IngestionManifest"
        )
    caller = manifest.caller_metadata
    document = {
        "caller_supplied": {
            "source_identifier": caller.source_identifier,
            "tap_endpoint": caller.tap_endpoint,
            "adql_query": caller.adql_query,
            "query_parameters": {key: value for key, value in caller.query_parameters},
            "acquisition_timestamp": (
                caller.acquisition_timestamp.isoformat()
                if caller.acquisition_timestamp is not None
                else None
            ),
            "job_identifier": caller.job_identifier,
            "http_response_metadata": {
                key: value for key, value in caller.http_response_metadata
            },
        },
        "calculated": {
            "raw_response_byte_count": manifest.raw_response_byte_count,
            "raw_response_sha256": manifest.raw_response_sha256,
            "validation_status": manifest.validation_status,
            "serialization": manifest.serialization,
            "detected_fields": [
                {
                    "name": field.name,
                    "datatype": field.datatype,
                    "arraysize": field.arraysize,
                    "unit": field.unit,
                    "null_value": field.null_value,
                }
                for field in manifest.detected_fields
            ],
            "extracted_row_count": manifest.extracted_row_count,
            "accepted_row_count": manifest.accepted_row_count,
            "excluded_row_count": manifest.excluded_row_count,
            "validation_policy_version": manifest.validation_policy_version,
            "validator_version": manifest.validator_version,
            "parser_version": manifest.parser_version,
        },
        "manifest_version": manifest.manifest_version,
    }
    try:
        return json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, OverflowError) as exc:
        raise DatasetIngestionError(
            "invalid_manifest", "manifest is not safely JSON serializable"
        ) from exc


def _validate_required_field_types(fields: tuple[VOTableField, ...]) -> None:
    by_name = {field.name: field for field in fields}
    for name in REQUIRED_COLUMNS:
        field = by_name[name]
        if field.datatype is None:
            raise DatasetIngestionError(
                "invalid_required_column_type",
                f"required column {name!r} has no VOTable datatype",
            )
        if name in _NUMERIC_COLUMNS:
            if (
                field.datatype
                not in {"float", "double"}
                | {
                    "unsignedByte",
                    "short",
                    "int",
                    "long",
                    "unsignedShort",
                    "unsignedInt",
                    "unsignedLong",
                }
                or field.arraysize is not None
            ):
                raise DatasetIngestionError(
                    "invalid_required_column_type",
                    f"required numeric column {name!r} must have a scalar numeric "
                    "datatype",
                )
        elif name in _IDENTITY_COLUMNS and field.datatype not in {
            "char",
            "unicodeChar",
        }:
            raise DatasetIngestionError(
                "invalid_required_column_type",
                f"required identity column {name!r} must have a character datatype",
            )


def _validate_optional_text(field: str, value: object) -> None:
    if value is not None:
        _validate_metadata_text(field, value)


def _validate_metadata_text(field: str, value: object) -> None:
    if type(value) is not str or not value:
        raise DatasetIngestionError(
            "invalid_metadata", f"{field} must be non-empty text"
        )
    try:
        encoded_value = value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise DatasetIngestionError(
            "invalid_metadata", f"{field} is not valid Unicode"
        ) from exc
    if len(encoded_value) > _MAX_METADATA_VALUE_BYTES:
        raise DatasetIngestionError(
            "invalid_metadata", f"{field} exceeds the metadata size limit"
        )


def _validate_caller_scalar(value: object) -> None:
    if value is not None and type(value) not in (str, int, float, bool):
        raise DatasetIngestionError(
            "invalid_metadata", "query parameter values must be JSON scalar values"
        )
    if type(value) is float and not math.isfinite(value):
        raise DatasetIngestionError(
            "invalid_metadata", "query parameter floats must be finite"
        )
    if type(value) is str:
        _validate_metadata_text("query parameter value", value)


def _is_sensitive_name(value: str) -> bool:
    normalized = value.casefold().replace("_", "-")
    return any(
        marker in normalized
        for marker in (
            "authorization",
            "cookie",
            "password",
            "secret",
            "token",
            "api-key",
            "apikey",
        )
    )
