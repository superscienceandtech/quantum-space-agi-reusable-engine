"""Offline mechanical checks for the proposed ARC-08 mass-radius inputs.

This module checks data representation and basic numeric usability only. Passing
these checks is not scientific eligibility, validation, or model readiness.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeAlias, cast

from quantum_space_agi.data import Dataset
from quantum_space_agi.data.models import Record

FEATURE_FIELD = "pl_rade"
TARGET_FIELD = "pl_bmasse"
IDENTITY_FIELDS = ("pl_name", "hostname", "pl_refname")
VALIDATION_POLICY_VERSION = "arc08-mass-radius-validation/1"
_MAX_ORIGINAL_VALUE_BYTES = 256

SafeScalar: TypeAlias = str | int | float | bool | None


@dataclass(frozen=True, slots=True)
class ValidationFinding:
    """One mechanical validation finding for one source row and field."""

    field: str
    reason_code: str
    original_value: SafeScalar
    value_omitted: bool

    def __post_init__(self) -> None:
        if type(self.field) is not str or not self.field:
            raise ValueError("field must be a non-empty string")
        if type(self.reason_code) is not str or not self.reason_code:
            raise ValueError("reason_code must be a non-empty string")
        if type(self.value_omitted) is not bool:
            raise ValueError("value_omitted must be a boolean")
        if self.original_value is not None and type(self.original_value) not in (
            str,
            int,
            float,
            bool,
        ):
            raise ValueError("original_value must be a JSON scalar or null")
        if type(self.original_value) is float and not math.isfinite(
            self.original_value
        ):
            raise ValueError("original_value must be finite when retained")
        try:
            encoded_value = json.dumps(
                self.original_value, ensure_ascii=False, allow_nan=False
            ).encode("utf-8")
        except (TypeError, ValueError, UnicodeEncodeError, OverflowError) as exc:
            raise ValueError("original_value must be safely JSON serializable") from exc
        if len(encoded_value) > _MAX_ORIGINAL_VALUE_BYTES:
            raise ValueError("original_value exceeds the retention size limit")
        if self.value_omitted and self.original_value is not None:
            raise ValueError("omitted original_value must be null")


@dataclass(frozen=True, slots=True)
class ExcludedRow:
    """A source row excluded from mechanically valid numeric inputs."""

    row_index: int
    findings: tuple[ValidationFinding, ...]

    def __post_init__(self) -> None:
        if type(self.row_index) is not int or self.row_index < 0:
            raise ValueError("row_index must be a non-negative integer")
        findings = tuple(self.findings)
        if not findings or any(
            not isinstance(item, ValidationFinding) for item in findings
        ):
            raise ValueError(
                "findings must be a non-empty sequence of ValidationFinding"
            )
        object.__setattr__(self, "findings", findings)


@dataclass(frozen=True, slots=True)
class DatasetValidationReport:
    """Immutable mechanical validation result with a row-level exclusion ledger.

    ``record_index`` values are zero-based positions in the input Dataset. The
    report does not alter, remove, normalize, or coerce source records.
    """

    policy_version: str
    record_count: int
    valid_record_indices: tuple[int, ...]
    excluded_rows: tuple[ExcludedRow, ...]

    def __post_init__(self) -> None:
        if type(self.policy_version) is not str or not self.policy_version:
            raise ValueError("policy_version must be a non-empty string")
        if type(self.record_count) is not int or self.record_count < 0:
            raise ValueError("record_count must be a non-negative integer")
        valid_indices = tuple(self.valid_record_indices)
        excluded_rows = tuple(self.excluded_rows)
        if any(
            type(index) is not int or not 0 <= index < self.record_count
            for index in valid_indices
        ):
            raise ValueError("valid_record_indices must refer to input records")
        if any(not isinstance(row, ExcludedRow) for row in excluded_rows):
            raise ValueError("excluded_rows must contain ExcludedRow values")
        excluded_indices = tuple(row.row_index for row in excluded_rows)
        if any(index >= self.record_count for index in excluded_indices):
            raise ValueError("excluded row index must refer to an input record")
        if len(set(valid_indices)) != len(valid_indices) or len(
            set(excluded_indices)
        ) != len(excluded_indices):
            raise ValueError("row indices must be unique")
        if set(valid_indices).intersection(excluded_indices):
            raise ValueError("a row cannot be both valid and excluded")
        if set(valid_indices).union(excluded_indices) != set(range(self.record_count)):
            raise ValueError("every input row must be accounted for exactly once")
        object.__setattr__(self, "valid_record_indices", valid_indices)
        object.__setattr__(self, "excluded_rows", excluded_rows)

    @property
    def excluded_row_count(self) -> int:
        """Number of unique rows with at least one validation finding."""
        return len(self.excluded_rows)

    @property
    def is_valid(self) -> bool:
        """Whether all rows pass these mechanical checks."""
        return not self.excluded_rows


def validate_baseline_dataset(dataset: Dataset) -> DatasetValidationReport:
    """Check candidate feature, target, and grouping identity fields offline.

    The candidate feature is ``pl_rade`` (Earth radii) and target is
    ``pl_bmasse`` (Earth masses). Numeric values must be built-in integers or
    finite built-in floats and strictly positive. Booleans, numeric strings,
    missing/null/blank values, and non-finite floats are reported, never fixed.

    Exact non-empty string values are required for ``pl_name``, ``hostname``,
    and ``pl_refname`` so later identity/group audits can be performed. No
    trimming, case folding, alias resolution, or deduplication occurs. These
    operational checks do not settle scientific eligibility or limit semantics.
    """
    if not isinstance(dataset, Dataset):
        raise TypeError("dataset must be a Dataset")

    return validate_baseline_records(dataset.records)


def validate_baseline_records(records: Sequence[Record]) -> DatasetValidationReport:
    """Apply the Phase 4.1 field checks to an ordered sequence of records.

    This records-level entry point lets offline parsers reuse the same policy
    without inventing ARC-03 ``Provenance`` (including ``retrieved_at``) when
    that source metadata was not supplied.
    """
    if isinstance(records, (str, bytes)) or not isinstance(records, Sequence):
        raise TypeError("records must be a sequence of record mappings")
    normalized_records = tuple(records)
    if any(not isinstance(record, Mapping) for record in normalized_records):
        raise TypeError("records must contain mapping values")
    if any(
        any(type(field) is not str for field in record) for record in normalized_records
    ):
        raise TypeError("record field names must be strings")

    valid_indices: list[int] = []
    excluded_rows: list[ExcludedRow] = []
    for row_index, record in enumerate(normalized_records):
        findings: list[ValidationFinding] = []
        _validate_numeric_field(record, TARGET_FIELD, findings)
        _validate_numeric_field(record, FEATURE_FIELD, findings)
        for field in IDENTITY_FIELDS:
            _validate_identity_field(record, field, findings)
        if findings:
            excluded_rows.append(ExcludedRow(row_index, tuple(findings)))
        else:
            valid_indices.append(row_index)

    return DatasetValidationReport(
        policy_version=VALIDATION_POLICY_VERSION,
        record_count=len(normalized_records),
        valid_record_indices=tuple(valid_indices),
        excluded_rows=tuple(excluded_rows),
    )


def _validate_numeric_field(
    record: Record,
    field: str,
    findings: list[ValidationFinding],
) -> None:
    if field not in record:
        findings.append(ValidationFinding(field, "missing_field", None, False))
        return
    value = record[field]
    if value is None:
        findings.append(ValidationFinding(field, "null_value", None, False))
        return
    if isinstance(value, str) and not value.strip():
        findings.append(_finding(field, "blank_value", value))
        return
    if type(value) is int:
        if value <= 0:
            findings.append(_finding(field, "non_positive", value))
        return
    if type(value) is not float:
        findings.append(_finding(field, "non_numeric", value))
        return
    if not math.isfinite(value):
        findings.append(_finding(field, "non_finite", value))
        return
    if value <= 0:
        findings.append(_finding(field, "non_positive", value))


def _validate_identity_field(
    record: Record,
    field: str,
    findings: list[ValidationFinding],
) -> None:
    if field not in record:
        findings.append(ValidationFinding(field, "missing_identity", None, False))
        return
    value = record[field]
    if type(value) is not str or not value.strip():
        findings.append(_finding(field, "missing_identity", value))


def _finding(field: str, reason_code: str, value: object) -> ValidationFinding:
    safe_value, omitted = _safe_original_value(value)
    return ValidationFinding(field, reason_code, safe_value, omitted)


def _safe_original_value(value: object) -> tuple[SafeScalar, bool]:
    """Retain only compact JSON scalar values; omit unsafe/large values."""
    if value is not None and type(value) not in (str, int, float, bool):
        return None, True
    if type(value) is float and not math.isfinite(value):
        return None, True
    try:
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, OverflowError):
        return None, True
    if len(encoded) > _MAX_ORIGINAL_VALUE_BYTES:
        return None, True
    return cast(SafeScalar, value), False
