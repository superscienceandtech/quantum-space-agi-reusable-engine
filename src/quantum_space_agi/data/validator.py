"""Schema-driven structural and data-quality checks for loaded records.

Validation is non-mutating. It checks data against an explicit, lightweight
schema and does not establish scientific correctness.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from .loader import DatasetLoadResult


class SchemaDefinitionError(ValueError):
    """The supplied validation schema is invalid or unsupported."""


@dataclass(frozen=True)
class ValidationIssue:
    """One validation finding; record indexes are one-based."""

    record_index: int | None
    field_name: str | None
    category: str
    severity: str
    expected: str
    actual_value: Any | None
    message: str


@dataclass(frozen=True)
class ValidationReport:
    """Summary and detailed findings for one validation run."""

    dataset_id: str | None
    schema_name: str
    is_valid: bool
    total_records: int
    valid_records: int
    invalid_records: int
    errors: tuple[ValidationIssue, ...]
    warnings: tuple[ValidationIssue, ...]
    validation_timestamp: str


_SUPPORTED_TYPES = {"string", "integer", "float", "boolean", "array", "object"}
_SCHEMA_KEYS = {
    "schema_name",
    "dataset_id",
    "fields",
    "allow_unexpected_fields",
    "duplicate_detection",
}
_FIELD_KEYS = {
    "type",
    "required",
    "nullable",
    "minimum",
    "maximum",
    "min_length",
    "max_length",
    "allowed_values",
    "allow_empty_string",
    "whitespace_only_is_missing",
}
_NUMBER_PATTERN = re.compile(r"^[+-]?(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[eE][+-]?\d+)?$")
_INTEGER_PATTERN = re.compile(r"^[+-]?\d+$")


def validate_dataset(
    dataset: DatasetLoadResult | Mapping[str, Any] | Sequence[Mapping[str, Any]],
    schema: Mapping[str, Any],
    *,
    include_actual_values: bool = False,
) -> ValidationReport:
    """Validate a load result, ``{dataset_id, records}`` mapping, or records.

    Values are checked in place and never coerced. By default issue reports omit
    actual values to reduce accidental disclosure of sensitive data.
    """

    schema_name, schema_dataset_id, fields, allow_unexpected, duplicate_config = (
        _validate_schema(schema)
    )
    if isinstance(dataset, DatasetLoadResult):
        records: Any = dataset.records
        dataset_id = dataset.dataset_id
    elif isinstance(dataset, Mapping):
        if "records" not in dataset:
            raise TypeError("Dataset mapping must contain a 'records' sequence.")
        records = dataset["records"]
        dataset_id = dataset.get("dataset_id")
    else:
        records = dataset
        dataset_id = None

    if isinstance(records, (str, bytes)) or not isinstance(records, Sequence):
        raise TypeError("Dataset records must be a sequence of mappings.")

    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []
    if schema_dataset_id is not None and dataset_id != schema_dataset_id:
        errors.append(
            _issue(
                None,
                None,
                "dataset_id_mismatch",
                "error",
                f"dataset_id {schema_dataset_id!r}",
                dataset_id,
                f"Dataset identifier {dataset_id!r} does not match schema "
                f"identifier {schema_dataset_id!r}.",
                include_actual_values,
            )
        )
    if not records:
        errors.append(
            _issue(
                None,
                None,
                "empty_dataset",
                "error",
                "at least one record",
                None,
                "Dataset contains no records.",
                include_actual_values,
            )
        )

    for record_index, record in enumerate(records, start=1):
        if not isinstance(record, Mapping):
            errors.append(
                _issue(
                    record_index,
                    None,
                    "record_not_object",
                    "error",
                    "object/mapping",
                    record,
                    f"Record {record_index} must be an object or mapping.",
                    include_actual_values,
                )
            )
            continue
        if not record:
            errors.append(
                _issue(
                    record_index,
                    None,
                    "empty_record",
                    "error",
                    "record with declared fields",
                    record,
                    f"Record {record_index} has no fields.",
                    include_actual_values,
                )
            )

        if not allow_unexpected:
            for field_name in sorted(record.keys() - fields.keys(), key=str):
                errors.append(
                    _issue(
                        record_index,
                        str(field_name),
                        "unexpected_field",
                        "error",
                        "field declared by schema",
                        record[field_name],
                        f"Record {record_index} contains unexpected field "
                        f"{field_name!r}.",
                        include_actual_values,
                    )
                )

        for field_name, spec in fields.items():
            if field_name not in record:
                if spec.get("required", False):
                    errors.append(
                        _issue(
                            record_index,
                            field_name,
                            "missing_required",
                            "error",
                            "required field to be present",
                            None,
                            f"Record {record_index} is missing required field "
                            f"{field_name!r}.",
                            include_actual_values,
                        )
                    )
                continue

            value = record[field_name]
            errors.extend(
                _validate_value(
                    record_index, field_name, value, spec, include_actual_values
                )
            )

    duplicate_issues = _find_duplicates(
        records, duplicate_config, include_actual_values
    )
    warnings.extend(duplicate_issues)
    invalid_record_indexes = {
        issue.record_index for issue in errors if issue.record_index is not None
    }
    total_records = len(records)
    invalid_records = len(invalid_record_indexes)
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    return ValidationReport(
        dataset_id=dataset_id,
        schema_name=schema_name,
        is_valid=not errors,
        total_records=total_records,
        valid_records=total_records - invalid_records,
        invalid_records=invalid_records,
        errors=tuple(errors),
        warnings=tuple(warnings),
        validation_timestamp=timestamp,
    )


def _validate_schema(
    schema: Mapping[str, Any],
) -> tuple[str, str | None, dict[str, dict[str, Any]], bool, dict[str, Any]]:
    if not isinstance(schema, Mapping):
        raise SchemaDefinitionError("Schema must be an object/mapping.")
    unknown_schema_keys = set(schema) - _SCHEMA_KEYS
    if unknown_schema_keys:
        raise SchemaDefinitionError(
            f"Unsupported schema keys: {sorted(unknown_schema_keys)!r}."
        )
    schema_name = schema.get("schema_name")
    if not isinstance(schema_name, str) or not schema_name:
        raise SchemaDefinitionError("Schema must define a non-empty 'schema_name'.")
    dataset_id = schema.get("dataset_id")
    if dataset_id is not None and (not isinstance(dataset_id, str) or not dataset_id):
        raise SchemaDefinitionError(
            "Schema 'dataset_id' must be a non-empty string when provided."
        )
    fields = schema.get("fields")
    if not isinstance(fields, Mapping):
        raise SchemaDefinitionError("Schema must define a 'fields' object/mapping.")
    for field_name, spec in fields.items():
        if not isinstance(field_name, str) or not field_name:
            raise SchemaDefinitionError("Schema field names must be non-empty strings.")
        if not isinstance(spec, Mapping):
            raise SchemaDefinitionError(
                f"Schema field {field_name!r} must have an object definition."
            )
        unknown_field_keys = set(spec) - _FIELD_KEYS
        if unknown_field_keys:
            raise SchemaDefinitionError(
                f"Unsupported keys for field {field_name!r}: "
                f"{sorted(unknown_field_keys)!r}."
            )
        field_type = spec.get("type")
        if not isinstance(field_type, str) or field_type not in _SUPPORTED_TYPES:
            raise SchemaDefinitionError(
                f"Field {field_name!r} type must be one of "
                f"{sorted(_SUPPORTED_TYPES)!r}."
            )
        for flag in (
            "required",
            "nullable",
            "allow_empty_string",
            "whitespace_only_is_missing",
        ):
            if flag in spec and not isinstance(spec[flag], bool):
                raise SchemaDefinitionError(
                    f"Field {field_name!r} option {flag!r} must be boolean."
                )
        _validate_field_constraints(field_name, spec)

    unexpected_policy = schema.get("allow_unexpected_fields", False)
    if not isinstance(unexpected_policy, bool):
        raise SchemaDefinitionError("'allow_unexpected_fields' must be boolean.")
    duplicate_config = schema.get("duplicate_detection", {"enabled": False})
    if not isinstance(duplicate_config, Mapping):
        raise SchemaDefinitionError("'duplicate_detection' must be an object/mapping.")
    if set(duplicate_config) - {"enabled", "strategy", "fields"}:
        raise SchemaDefinitionError(
            "Duplicate detection supports only enabled, strategy, and fields."
        )
    enabled = duplicate_config.get("enabled", False)
    if not isinstance(enabled, bool):
        raise SchemaDefinitionError("Duplicate detection 'enabled' must be boolean.")
    strategy = duplicate_config.get("strategy", "all_fields")
    if not isinstance(strategy, str) or strategy not in {"all_fields", "fields"}:
        raise SchemaDefinitionError(
            "Duplicate detection strategy must be 'all_fields' or 'fields'."
        )
    if strategy == "fields":
        key_fields = duplicate_config.get("fields")
        if (
            not isinstance(key_fields, list)
            or not key_fields
            or any(
                not isinstance(name, str) or name not in fields for name in key_fields
            )
        ):
            raise SchemaDefinitionError(
                "Duplicate detection strategy 'fields' requires a non-empty "
                "list of declared field names."
            )
    return (
        schema_name,
        dataset_id,
        dict(fields),
        unexpected_policy,
        dict(duplicate_config),
    )


def _validate_field_constraints(field_name: str, spec: Mapping[str, Any]) -> None:
    field_type = spec["type"]
    numeric_constraints = ("minimum", "maximum")
    length_constraints = ("min_length", "max_length")
    if any(key in spec for key in numeric_constraints) and field_type not in {
        "integer",
        "float",
    }:
        raise SchemaDefinitionError(
            f"Numeric constraints require a numeric type for {field_name!r}."
        )
    if any(key in spec for key in length_constraints) and field_type != "string":
        raise SchemaDefinitionError(
            f"Length constraints require a string type for {field_name!r}."
        )
    for key in numeric_constraints:
        if key in spec and (
            isinstance(spec[key], bool)
            or not isinstance(spec[key], (int, float))
            or (isinstance(spec[key], float) and not math.isfinite(spec[key]))
        ):
            raise SchemaDefinitionError(
                f"Field {field_name!r} {key!r} must be numeric."
            )
    if "minimum" in spec and "maximum" in spec and spec["minimum"] > spec["maximum"]:
        raise SchemaDefinitionError(f"Field {field_name!r} minimum exceeds maximum.")
    for key in length_constraints:
        if key in spec and (
            not isinstance(spec[key], int)
            or isinstance(spec[key], bool)
            or spec[key] < 0
        ):
            raise SchemaDefinitionError(
                f"Field {field_name!r} {key!r} must be a non-negative integer."
            )
    if (
        "min_length" in spec
        and "max_length" in spec
        and spec["min_length"] > spec["max_length"]
    ):
        raise SchemaDefinitionError(
            f"Field {field_name!r} min_length exceeds max_length."
        )
    if "allowed_values" in spec and not isinstance(spec["allowed_values"], list):
        raise SchemaDefinitionError(
            f"Field {field_name!r} 'allowed_values' must be a list."
        )


def _validate_value(
    record_index: int,
    field_name: str,
    value: Any,
    spec: Mapping[str, Any],
    include_actual_values: bool,
) -> list[ValidationIssue]:
    if value is None:
        if spec.get("nullable", False):
            return []
        return [
            _issue(
                record_index,
                field_name,
                "null_not_allowed",
                "error",
                "non-null value",
                value,
                f"Record {record_index} field {field_name!r} is null but "
                "schema does not allow null.",
                include_actual_values,
            )
        ]
    if (
        isinstance(value, str)
        and value == ""
        and not spec.get("allow_empty_string", False)
    ):
        return [
            _issue(
                record_index,
                field_name,
                "empty_string",
                "error",
                "non-empty string",
                value,
                f"Record {record_index} field {field_name!r} is an empty string.",
                include_actual_values,
            )
        ]
    if (
        isinstance(value, str)
        and value != ""
        and not value.strip()
        and spec.get("whitespace_only_is_missing", False)
    ):
        return [
            _issue(
                record_index,
                field_name,
                "whitespace_only",
                "error",
                "non-whitespace value",
                value,
                f"Record {record_index} field {field_name!r} contains only whitespace.",
                include_actual_values,
            )
        ]

    field_type = spec["type"]
    normalized_number = _numeric_value(value, field_type)
    if not _matches_type(value, field_type, normalized_number):
        return [
            _issue(
                record_index,
                field_name,
                "type_mismatch",
                "error",
                field_type,
                value,
                f"Record {record_index} field {field_name!r} must have type "
                f"{field_type}.",
                include_actual_values,
            )
        ]

    issues = []
    if field_type in {"integer", "float"} and normalized_number is not None:
        for bound, category in (
            ("minimum", "minimum_violation"),
            ("maximum", "maximum_violation"),
        ):
            if bound in spec and (
                (bound == "minimum" and normalized_number < Decimal(str(spec[bound])))
                or (
                    bound == "maximum" and normalized_number > Decimal(str(spec[bound]))
                )
            ):
                issues.append(
                    _issue(
                        record_index,
                        field_name,
                        category,
                        "error",
                        f"{bound} {spec[bound]!r}",
                        value,
                        f"Record {record_index} field {field_name!r} violates "
                        f"{bound} {spec[bound]!r}.",
                        include_actual_values,
                    )
                )
    if field_type == "string":
        for bound, category in (
            ("min_length", "min_length"),
            ("max_length", "max_length"),
        ):
            if bound in spec and (
                (bound == "min_length" and len(value) < spec[bound])
                or (bound == "max_length" and len(value) > spec[bound])
            ):
                issues.append(
                    _issue(
                        record_index,
                        field_name,
                        category,
                        "error",
                        f"{bound} {spec[bound]}",
                        value,
                        f"Record {record_index} field {field_name!r} violates "
                        f"{bound} {spec[bound]}.",
                        include_actual_values,
                    )
                )
    if "allowed_values" in spec and not any(
        type(value) is type(candidate) and value == candidate
        for candidate in spec["allowed_values"]
    ):
        issues.append(
            _issue(
                record_index,
                field_name,
                "allowed_value",
                "error",
                f"one of {spec['allowed_values']!r}",
                value,
                f"Record {record_index} field {field_name!r} is not an allowed value.",
                include_actual_values,
            )
        )
    return issues


def _numeric_value(value: Any, field_type: str) -> Decimal | None:
    if field_type not in {"integer", "float"}:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        if field_type == "integer":
            return Decimal(value)
        return Decimal(value)
    if isinstance(value, float):
        return (
            Decimal(str(value))
            if field_type == "float" and math.isfinite(value)
            else None
        )
    if isinstance(value, str):
        pattern = _INTEGER_PATTERN if field_type == "integer" else _NUMBER_PATTERN
        if not pattern.fullmatch(value):
            return None
        try:
            number = Decimal(value)
        except InvalidOperation:
            return None
        return number if number.is_finite() else None
    return None


def _matches_type(value: Any, field_type: str, number: Decimal | None) -> bool:
    if field_type == "string":
        return isinstance(value, str)
    if field_type in {"integer", "float"}:
        return number is not None
    if field_type == "boolean":
        return isinstance(value, bool) or (
            isinstance(value, str) and value in {"true", "false"}
        )
    if field_type == "array":
        return isinstance(value, list)
    if field_type == "object":
        return isinstance(value, Mapping)
    return False


def _find_duplicates(
    records: Sequence[Any],
    config: Mapping[str, Any],
    include_actual_values: bool,
) -> list[ValidationIssue]:
    if not config.get("enabled", False):
        return []
    strategy = config.get("strategy", "all_fields")
    key_fields = config.get("fields", [])
    seen: dict[str, int] = {}
    issues = []
    for record_index, record in enumerate(records, start=1):
        if not isinstance(record, Mapping):
            continue
        selected: Mapping[Any, Any]
        if strategy == "fields":
            if any(
                field not in record or record[field] is None for field in key_fields
            ):
                continue
            selected = {field: record[field] for field in key_fields}
        else:
            selected = record
        fingerprint = json.dumps(
            selected,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=repr,
        )
        if fingerprint in seen:
            issues.append(
                _issue(
                    record_index,
                    None,
                    "duplicate_record",
                    "warning",
                    f"unique record under {strategy!r} comparison; first seen "
                    f"at record {seen[fingerprint]}",
                    record,
                    f"Record {record_index} duplicates record {seen[fingerprint]}.",
                    include_actual_values,
                )
            )
        else:
            seen[fingerprint] = record_index
    return issues


def _issue(
    record_index: int | None,
    field_name: str | None,
    category: str,
    severity: str,
    expected: str,
    actual_value: Any,
    message: str,
    include_actual_values: bool,
) -> ValidationIssue:
    return ValidationIssue(
        record_index=record_index,
        field_name=field_name,
        category=category,
        severity=severity,
        expected=expected,
        actual_value=actual_value if include_actual_values else None,
        message=message,
    )
