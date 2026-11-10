"""Task-driven mechanical preparation of numeric Dataset records.

Preparation preserves values and row positions. It does not apply scientific
eligibility rules, impute values, or establish that a task is approved.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeAlias, cast

from quantum_space_agi.data import DataSchema, Dataset, JSONValue, Provenance
from quantum_space_agi.ml.dataset_validation import ExcludedRow, ValidationFinding
from quantum_space_agi.ml.experiment_manifest import ResearchTask

NumericValue: TypeAlias = int | float
_MAX_RETAINED_VALUE_BYTES = 256


class DatasetPreparationError(ValueError):
    """A task declaration or Dataset structure cannot be prepared."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class PreparedRegressionRecord:
    """One aligned feature/target row linked to its original source position."""

    source_row_index: int
    feature_values: tuple[NumericValue, ...]
    target_value: NumericValue

    def __post_init__(self) -> None:
        if type(self.source_row_index) is not int or self.source_row_index < 0:
            raise DatasetPreparationError(
                "invalid_result", "source_row_index must be a non-negative integer"
            )
        if type(self.feature_values) is not tuple or not self.feature_values:
            raise DatasetPreparationError(
                "invalid_result", "feature_values must be a non-empty tuple"
            )
        for value in (*self.feature_values, self.target_value):
            if type(value) not in (int, float) or (
                type(value) is float and not math.isfinite(value)
            ):
                raise DatasetPreparationError(
                    "invalid_result", "prepared values must be finite built-in numbers"
                )


@dataclass(frozen=True, slots=True)
class PreparedRegressionDataset:
    """Immutable prepared rows and exclusions linked to task, schema and source."""

    task: ResearchTask
    feature_fields: tuple[str, ...]
    target_field: str
    schema_id: str
    schema_version: str
    provenance: Provenance
    input_source_row_indices: tuple[int, ...]
    accepted_records: tuple[PreparedRegressionRecord, ...]
    excluded_rows: tuple[ExcludedRow, ...]

    def __post_init__(self) -> None:
        if type(self.task) is not ResearchTask:
            raise DatasetPreparationError("invalid_result", "task must be ResearchTask")
        if (
            type(self.feature_fields) is not tuple
            or not self.feature_fields
            or any(type(field) is not str or not field for field in self.feature_fields)
            or len(set(self.feature_fields)) != len(self.feature_fields)
        ):
            raise DatasetPreparationError(
                "invalid_result", "feature_fields must be unique non-empty strings"
            )
        if (
            type(self.target_field) is not str
            or not self.target_field
            or self.target_field in self.feature_fields
        ):
            raise DatasetPreparationError(
                "invalid_result", "target_field must be non-empty and distinct"
            )
        if (
            self.task.objective is None
            or self.task.target is None
            or not self.task.features
            or tuple(item.field for item in self.task.features) != self.feature_fields
            or self.task.target.field != self.target_field
        ):
            raise DatasetPreparationError(
                "invalid_result", "task declaration must match prepared fields"
            )
        if type(self.schema_id) is not str or not self.schema_id:
            raise DatasetPreparationError("invalid_result", "schema_id is invalid")
        if type(self.schema_version) is not str or not self.schema_version:
            raise DatasetPreparationError("invalid_result", "schema_version is invalid")
        if type(self.provenance) is not Provenance:
            raise DatasetPreparationError(
                "invalid_result", "provenance must be Dataset provenance"
            )
        if type(self.input_source_row_indices) is not tuple or any(
            type(index) is not int or index < 0
            for index in self.input_source_row_indices
        ):
            raise DatasetPreparationError(
                "invalid_result", "input source row indices must be non-negative ints"
            )
        if len(set(self.input_source_row_indices)) != len(
            self.input_source_row_indices
        ):
            raise DatasetPreparationError(
                "invalid_result", "input source row indices must be unique"
            )
        if type(self.accepted_records) is not tuple or any(
            type(record) is not PreparedRegressionRecord
            for record in self.accepted_records
        ):
            raise DatasetPreparationError(
                "invalid_result", "accepted_records must be a tuple of prepared rows"
            )
        if any(
            len(record.feature_values) != len(self.feature_fields)
            for record in self.accepted_records
        ):
            raise DatasetPreparationError(
                "invalid_result", "prepared feature rows must align with feature_fields"
            )
        if type(self.excluded_rows) is not tuple or any(
            type(row) is not ExcludedRow for row in self.excluded_rows
        ):
            raise DatasetPreparationError(
                "invalid_result", "excluded_rows must be a tuple of ExcludedRow"
            )

        accepted_indices = tuple(row.source_row_index for row in self.accepted_records)
        excluded_indices = tuple(row.row_index for row in self.excluded_rows)
        input_indices = self.input_source_row_indices
        accepted_set = set(accepted_indices)
        excluded_set = set(excluded_indices)
        if (
            accepted_indices
            != tuple(index for index in input_indices if index in accepted_set)
            or excluded_indices
            != tuple(index for index in input_indices if index in excluded_set)
            or accepted_set.intersection(excluded_set)
            or accepted_set.union(excluded_set) != set(input_indices)
        ):
            raise DatasetPreparationError(
                "invalid_result",
                "accepted and excluded rows must account for input source rows "
                "in order",
            )


def prepare_regression_dataset(
    dataset: Dataset,
    task: ResearchTask,
    schema: DataSchema,
    *,
    source_row_indices: Sequence[int] | None = None,
) -> PreparedRegressionDataset:
    """Select declared numeric columns without coercion or scientific filtering.

    ``ResearchTask`` is reused as the task declaration. This API prepares only
    scalar numeric regression inputs. A missing ``source_row_indices`` maps each
    record to its zero-based position in ``dataset.records``; callers holding an
    upstream row map can supply it to preserve those original positions.
    """
    if type(dataset) is not Dataset:
        raise DatasetPreparationError("invalid_dataset", "dataset must be a Dataset")
    if type(task) is not ResearchTask:
        raise DatasetPreparationError("invalid_task", "task must be a ResearchTask")
    if type(schema) is not DataSchema:
        raise DatasetPreparationError("invalid_schema", "schema must be a DataSchema")
    if not dataset.records:
        raise DatasetPreparationError("empty_dataset", "dataset contains no records")
    if task.objective is None or task.target is None or not task.features:
        raise DatasetPreparationError(
            "incomplete_task", "task requires an objective, target, and features"
        )

    feature_fields = tuple(feature.field for feature in task.features)
    target_field = task.target.field
    schema_fields = {field.name: field for field in schema.fields}
    for field_name in (*feature_fields, target_field):
        if field_name not in schema_fields:
            raise DatasetPreparationError(
                "unknown_field",
                f"declared task field {field_name!r} is absent from schema",
            )
        if schema_fields[field_name].value_type not in (int, float):
            raise DatasetPreparationError(
                "invalid_schema",
                f"task field {field_name!r} must have an int or float schema type",
            )

    indices = _source_indices(source_row_indices, len(dataset.records))
    accepted: list[PreparedRegressionRecord] = []
    excluded: list[ExcludedRow] = []
    for source_index, record in zip(indices, dataset.records, strict=True):
        findings: list[ValidationFinding] = []
        values: list[NumericValue] = []
        target_value: NumericValue | None = None
        for field_name in (*feature_fields, target_field):
            value, finding = _numeric_value(
                record, field_name, schema_fields[field_name].value_type
            )
            if finding is not None:
                findings.append(finding)
            else:
                assert value is not None
                if field_name == target_field:
                    target_value = value
                else:
                    values.append(value)
        if findings:
            excluded.append(ExcludedRow(source_index, tuple(findings)))
        else:
            assert target_value is not None
            accepted.append(
                PreparedRegressionRecord(
                    source_row_index=source_index,
                    feature_values=tuple(values),
                    target_value=target_value,
                )
            )

    return PreparedRegressionDataset(
        task=task,
        feature_fields=feature_fields,
        target_field=target_field,
        schema_id=schema.identifier,
        schema_version=schema.version,
        provenance=dataset.provenance,
        input_source_row_indices=indices,
        accepted_records=tuple(accepted),
        excluded_rows=tuple(excluded),
    )


def _source_indices(
    source_row_indices: Sequence[int] | None, record_count: int
) -> tuple[int, ...]:
    if source_row_indices is None:
        return tuple(range(record_count))
    if isinstance(source_row_indices, (str, bytes)) or not isinstance(
        source_row_indices, Sequence
    ):
        raise DatasetPreparationError(
            "invalid_source_rows", "source_row_indices must be a sequence of integers"
        )
    indices = tuple(source_row_indices)
    if len(indices) != record_count or any(
        type(index) is not int or index < 0 for index in indices
    ):
        raise DatasetPreparationError(
            "invalid_source_rows",
            "source_row_indices must contain one non-negative integer per record",
        )
    if len(set(indices)) != len(indices):
        raise DatasetPreparationError(
            "invalid_source_rows", "source_row_indices must be unique"
        )
    return indices


def _numeric_value(
    record: Mapping[str, JSONValue], field_name: str, expected_type: type[object]
) -> tuple[NumericValue | None, ValidationFinding | None]:
    if field_name not in record:
        return None, ValidationFinding(field_name, "missing_field", None, False)
    value = record[field_name]
    if value is None:
        return None, ValidationFinding(field_name, "null_value", None, False)
    if type(value) not in (int, float):
        return None, _finding(field_name, "non_numeric", value)
    if type(value) is not expected_type:
        return None, _finding(field_name, "type_mismatch", value)
    if type(value) is float and not math.isfinite(value):
        return None, ValidationFinding(field_name, "non_finite", None, True)
    return cast(NumericValue, value), None


def _finding(field_name: str, reason_code: str, value: object) -> ValidationFinding:
    try:
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, OverflowError):
        return ValidationFinding(field_name, reason_code, None, True)
    if len(encoded) > _MAX_RETAINED_VALUE_BYTES or type(value) not in (
        str,
        int,
        float,
        bool,
    ):
        return ValidationFinding(field_name, reason_code, None, True)
    return ValidationFinding(
        field_name,
        reason_code,
        cast(str | int | float | bool | None, value),
        False,
    )
