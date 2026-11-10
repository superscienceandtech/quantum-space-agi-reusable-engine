"""Offline synthetic residual, uncertainty-metadata, and selection diagnostics.

The module consumes already-created predictions and validation reports. It does
not fit a model, select a cohort, infer NASA field semantics, or assess science.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import TypeAlias, cast

from quantum_space_agi.ml.dataset_validation import (
    DatasetValidationReport,
)
from quantum_space_agi.ml.identity_diagnostics import diagnose_identity_groups
from quantum_space_agi.ml.leakage_diagnostics import ExperimentManifestLinkage
from quantum_space_agi.ml.synthetic_baseline import (
    FEATURE_FIELD,
    TARGET_FIELD,
    SyntheticPrediction,
    create_synthetic_regression_fixture,
)

ERROR_DIAGNOSTICS_SCHEMA_VERSION = "arc08-error-selection-diagnostics/1"
_RESIDUAL_QUANTILES = (0.05, 0.25, 0.50, 0.75, 0.95)
JsonScalar: TypeAlias = str | int | float | bool | None
Row: TypeAlias = Mapping[str, object]


class ErrorDiagnosticsError(ValueError):
    """Invalid diagnostics input or unsupported output value."""


class UncertaintyRole(StrEnum):
    """Caller-declared role; no scientific semantics are inferred."""

    LOWER_UNCERTAINTY = "lower_uncertainty"
    UPPER_UNCERTAINTY = "upper_uncertainty"
    LOWER_BOUND = "lower_bound"
    UPPER_BOUND = "upper_bound"
    METADATA = "metadata"


@dataclass(frozen=True, slots=True)
class UncertaintyFieldSpec:
    """Schema declaration for one optional uncertainty-related source field."""

    field: str
    role: UncertaintyRole
    pair_id: str | None = None

    def __post_init__(self) -> None:
        if type(self.field) is not str or not self.field.strip():
            raise ErrorDiagnosticsError("uncertainty field must be non-empty text")
        if type(self.role) is not UncertaintyRole:
            raise ErrorDiagnosticsError("uncertainty role is invalid")
        if self.pair_id is not None and (
            type(self.pair_id) is not str or not self.pair_id.strip()
        ):
            raise ErrorDiagnosticsError("pair_id must be non-empty text or None")
        if self.role in (UncertaintyRole.LOWER_BOUND, UncertaintyRole.UPPER_BOUND):
            if self.pair_id is None:
                raise ErrorDiagnosticsError("bound fields require an explicit pair_id")


@dataclass(frozen=True, slots=True)
class ResidualQuantile:
    """Quantile value using linear interpolation at (n - 1) * probability."""

    probability: float
    value: float


@dataclass(frozen=True, slots=True)
class ResidualRecord:
    """A held-out target and its signed, row-aligned error decomposition."""

    row_id: str
    observed_target: float
    predicted_target: float
    residual: float
    absolute_error: float
    squared_error: float


@dataclass(frozen=True, slots=True)
class ErrorSummary:
    """Aggregate residual metrics with an explicit sample-size status."""

    status: str
    row_count: int
    mae: float | None
    rmse: float | None
    mean_signed_residual: float | None
    median_signed_residual: float | None
    median_absolute_error: float | None
    minimum_residual: float | None
    maximum_residual: float | None
    quantiles: tuple[ResidualQuantile, ...]


@dataclass(frozen=True, slots=True)
class MissingGroupValue:
    """Missing or unsupported group metadata for one held-out row."""

    field: str
    row_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class GroupErrorSummary:
    """Descriptive residual metrics for one exact group value."""

    field: str
    value: JsonScalar
    row_ids: tuple[str, ...]
    row_count: int
    mae: float | None
    rmse: float | None
    mean_signed_residual: float | None
    metric_status: str


@dataclass(frozen=True, slots=True)
class UncertaintyValue:
    """One supplied uncertainty metadata value, retained without conversion."""

    row_id: str
    value: JsonScalar
    status: str
    value_omitted: bool


@dataclass(frozen=True, slots=True)
class UncertaintyFieldDiagnostic:
    """Coverage and mechanical representation checks for a declared field."""

    field: str
    role: UncertaintyRole
    pair_id: str | None
    row_count: int
    present_count: int
    missing_row_ids: tuple[str, ...]
    invalid_numeric_row_ids: tuple[str, ...]
    invalid_type_row_ids: tuple[str, ...]
    inconsistent_bound_row_ids: tuple[str, ...]
    values: tuple[UncertaintyValue, ...]


@dataclass(frozen=True, slots=True)
class FieldCoverage:
    """Availability and numeric representation counts for one field."""

    field: str
    population: str
    row_count: int
    present_count: int
    missing_count: int
    finite_numeric_count: int
    non_finite_count: int
    invalid_value_count: int


@dataclass(frozen=True, slots=True)
class NumericDistribution:
    """Descriptive distribution for available finite values only."""

    status: str
    value_count: int
    minimum: float | None
    maximum: float | None
    mean: float | None


@dataclass(frozen=True, slots=True)
class IdentityCoverage:
    """Mechanical coverage of one identity field over all input rows."""

    field: str
    missing_count: int
    invalid_type_count: int
    present_count: int


@dataclass(frozen=True, slots=True)
class SelectionDiagnostics:
    """Validation-ledger counts and descriptive pre/post-validation coverage."""

    input_row_count: int
    mechanically_accepted_row_count: int
    excluded_row_count: int
    exclusions_by_reason: tuple[tuple[str, int], ...]
    exclusions_by_field_and_reason: tuple[tuple[str, str, int], ...]
    feature_target_coverage: tuple[FieldCoverage, ...]
    identity_coverage: tuple[IdentityCoverage, ...]
    feature_distribution_in_accepted_rows: NumericDistribution
    feature_distribution_in_excluded_rows: NumericDistribution
    scientific_eligibility_status: str
    cohort_selection_status: str
    sampling_bias_status: str


@dataclass(frozen=True, slots=True)
class ErrorSelectionDiagnosticReport:
    """Immutable result of offline error and selection diagnostics."""

    schema_version: str
    experiment_id: str
    fixture_id: str
    residual_convention: str
    test_row_ids: tuple[str, ...]
    residual_records: tuple[ResidualRecord, ...]
    aggregate_errors: ErrorSummary
    group_errors: tuple[GroupErrorSummary, ...]
    missing_group_values: tuple[MissingGroupValue, ...]
    uncertainty_fields: tuple[UncertaintyFieldDiagnostic, ...]
    selection: SelectionDiagnostics
    warnings: tuple[str, ...]
    limitations: tuple[str, ...]
    scientific_policy_status: str
    manifest_linkage: ExperimentManifestLinkage | None


def diagnose_error_selection(
    rows: Sequence[Row],
    validation_report: DatasetValidationReport,
    test_row_ids: Sequence[str],
    predictions: Sequence[SyntheticPrediction],
    *,
    row_id_field: str = "synthetic_row_id",
    feature_field: str = FEATURE_FIELD,
    target_field: str = TARGET_FIELD,
    experiment_id: str,
    fixture_id: str,
    group_fields: tuple[str, ...] = (),
    uncertainty_fields: tuple[UncertaintyFieldSpec, ...] = (),
    manifest_linkage: ExperimentManifestLinkage | None = None,
) -> ErrorSelectionDiagnosticReport:
    """Calculate residuals and descriptive selection diagnostics offline.

    Predictions must exactly cover ``test_row_ids`` and match their source
    feature/target values. Test IDs must be unique mechanically accepted rows.
    No invalid prediction is silently omitted.
    """
    normalized_rows = _rows(rows)
    if type(validation_report) is not DatasetValidationReport:
        raise ErrorDiagnosticsError("validation_report must be DatasetValidationReport")
    if validation_report.record_count != len(normalized_rows):
        raise ErrorDiagnosticsError("validation report row count does not match rows")
    for name, value in (
        ("row_id_field", row_id_field),
        ("feature_field", feature_field),
        ("target_field", target_field),
        ("experiment_id", experiment_id),
        ("fixture_id", fixture_id),
    ):
        _required_text(name, value)
    if type(group_fields) is not tuple or any(
        type(field) is not str or not field.strip() for field in group_fields
    ):
        raise ErrorDiagnosticsError("group_fields must be a tuple of non-empty strings")
    if len(set(group_fields)) != len(group_fields):
        raise ErrorDiagnosticsError("group_fields must be unique")
    if type(uncertainty_fields) is not tuple or any(
        type(spec) is not UncertaintyFieldSpec for spec in uncertainty_fields
    ):
        raise ErrorDiagnosticsError("uncertainty_fields must be a tuple of field specs")
    if len({spec.field for spec in uncertainty_fields}) != len(uncertainty_fields):
        raise ErrorDiagnosticsError("uncertainty fields must be unique")
    _validate_bound_specs(uncertainty_fields)
    if manifest_linkage is not None:
        if type(manifest_linkage) is not ExperimentManifestLinkage:
            raise ErrorDiagnosticsError("manifest_linkage has an invalid type")
        if manifest_linkage.experiment_id != experiment_id:
            raise ErrorDiagnosticsError("manifest experiment ID does not match report")

    ids_by_position = _source_row_ids(normalized_rows, row_id_field)
    position_by_id = {row_id: index for index, row_id in enumerate(ids_by_position)}
    if len(position_by_id) != len(ids_by_position):
        raise ErrorDiagnosticsError("source row identifiers must be unique")
    test_ids = _strings("test_row_ids", test_row_ids)
    if len(set(test_ids)) != len(test_ids):
        raise ErrorDiagnosticsError("test row identifiers must be unique")
    prediction_tuple = tuple(predictions)
    if any(type(item) is not SyntheticPrediction for item in prediction_tuple):
        raise ErrorDiagnosticsError(
            "predictions must contain SyntheticPrediction values"
        )
    prediction_ids = tuple(item.row_id for item in prediction_tuple)
    if any(type(row_id) is not str or not row_id for row_id in prediction_ids):
        raise ErrorDiagnosticsError(
            "prediction row identifiers must be non-empty strings"
        )
    if len(set(prediction_ids)) != len(prediction_ids):
        raise ErrorDiagnosticsError("prediction row identifiers must be unique")
    if set(prediction_ids) != set(test_ids):
        missing = sorted(set(test_ids) - set(prediction_ids))
        extra = sorted(set(prediction_ids) - set(test_ids))
        raise ErrorDiagnosticsError(
            f"predictions must match test IDs exactly; missing={missing}, extra={extra}"
        )

    accepted_ids = {
        ids_by_position[index] for index in validation_report.valid_record_indices
    }
    if not set(test_ids).issubset(accepted_ids):
        raise ErrorDiagnosticsError("test IDs must refer to mechanically accepted rows")
    prediction_by_id = {item.row_id: item for item in prediction_tuple}
    residuals: list[ResidualRecord] = []
    for row_id in test_ids:
        index = position_by_id[row_id]
        row = normalized_rows[index]
        prediction = prediction_by_id[row_id]
        feature_value = _finite_number(prediction.feature_value, "prediction feature")
        observed = _finite_number(prediction.observed_target, "observed target")
        predicted = _finite_number(prediction.predicted_target, "predicted target")
        source_feature = _finite_number(
            row.get(feature_field), f"source {feature_field}"
        )
        source_target = _finite_number(row.get(target_field), f"source {target_field}")
        if feature_value != source_feature or observed != source_target:
            raise ErrorDiagnosticsError(
                f"prediction values do not match source row {row_id}"
            )
        residual = observed - predicted
        squared_error = residual * residual
        if not math.isfinite(residual) or not math.isfinite(squared_error):
            raise ErrorDiagnosticsError(
                f"residual metrics overflow for prediction row {row_id}"
            )
        residuals.append(
            ResidualRecord(
                row_id,
                observed,
                predicted,
                residual,
                abs(residual),
                squared_error,
            )
        )

    residual_tuple = tuple(residuals)
    aggregate = _error_summary(tuple(item.residual for item in residual_tuple))
    group_summaries, missing_groups = _group_summaries(
        normalized_rows,
        position_by_id,
        residual_tuple,
        group_fields,
    )
    uncertainty = _uncertainty_diagnostics(
        normalized_rows, ids_by_position, uncertainty_fields
    )
    selection = _selection_diagnostics(
        normalized_rows,
        validation_report,
        feature_field,
        target_field,
    )
    warnings = []
    if missing_groups:
        warnings.append("Some requested group metadata is missing or invalid.")
    if any(item.inconsistent_bound_row_ids for item in uncertainty):
        warnings.append(
            "Declared lower/upper value bounds are inconsistent on some rows."
        )
    warnings.append(
        "Synthetic residual, uncertainty-metadata, and coverage summaries do not "
        "establish scientific behavior."
    )
    return ErrorSelectionDiagnosticReport(
        schema_version=ERROR_DIAGNOSTICS_SCHEMA_VERSION,
        experiment_id=experiment_id,
        fixture_id=fixture_id,
        residual_convention="observed_target - predicted_target",
        test_row_ids=test_ids,
        residual_records=residual_tuple,
        aggregate_errors=aggregate,
        group_errors=group_summaries,
        missing_group_values=missing_groups,
        uncertainty_fields=uncertainty,
        selection=selection,
        warnings=tuple(warnings),
        limitations=(
            "This report uses synthetic fixtures only and is not real ARC-08 "
            "performance evidence.",
            "Mechanical validation exclusions do not define scientific "
            "eligibility or an approved cohort.",
            "Included/excluded distributions are descriptive fixture summaries, "
            "not a real-data selection-bias estimate.",
            "Uncertainty metadata is retained and checked mechanically; it is "
            "not statistical uncertainty or a calibrated interval.",
            "Uncertainty values are not model features, weights, filters, or "
            "symmetric-error conversions.",
            "No NASA limit-code semantics are inferred from supplied values.",
            "Small group summaries have no minimum-size threshold and are not "
            "asserted to be reliable.",
            "No automatic acceptance threshold or scientific decision is applied.",
        ),
        scientific_policy_status="PENDING_REVIEW",
        manifest_linkage=manifest_linkage,
    )


def create_synthetic_error_diagnostic_fixture() -> tuple[dict[str, object], ...]:
    """Return a separate synthetic copy with diagnostic-only metadata fields."""
    base_rows = create_synthetic_regression_fixture()
    rows: list[dict[str, object]] = []
    for index, source in enumerate(base_rows):
        row: dict[str, object] = dict(source)
        row["synthetic_category"] = "category-A" if index % 2 == 0 else "category-B"
        row["synthetic_host_group"] = f"synthetic-host-{index % 4}"
        row["synthetic_mass_lower_uncertainty"] = 0.2 + index / 100
        row["synthetic_mass_upper_uncertainty"] = 0.5 + index / 100
        row["synthetic_radius_lower_uncertainty"] = 0.08 + index / 1000
        row["synthetic_radius_upper_uncertainty"] = 0.13 + index / 1000
        row["synthetic_interval_lower_bound"] = 1.0 + index
        row["synthetic_interval_upper_bound"] = 2.0 + index
        rows.append(row)
    rows[1]["synthetic_mass_lower_uncertainty"] = None
    rows[2]["synthetic_mass_upper_uncertainty"] = "invalid numeric metadata"
    rows[4]["synthetic_radius_lower_uncertainty"] = "invalid radius metadata"
    rows[5]["synthetic_radius_upper_uncertainty"] = float("inf")
    rows[3]["synthetic_interval_lower_bound"] = 9.0
    rows[3]["synthetic_interval_upper_bound"] = 8.0
    return tuple(rows)


def serialize_error_selection_diagnostics(
    report: ErrorSelectionDiagnosticReport,
) -> bytes:
    """Return deterministic compact UTF-8 JSON for an immutable report."""
    if type(report) is not ErrorSelectionDiagnosticReport:
        raise ErrorDiagnosticsError("report must be ErrorSelectionDiagnosticReport")
    try:
        return json.dumps(
            _report_document(report),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, OverflowError) as exc:
        raise ErrorDiagnosticsError("diagnostic report is not valid JSON") from exc


def _rows(rows: Sequence[Row]) -> tuple[Row, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ErrorDiagnosticsError("rows must be a sequence of mappings")
    normalized = tuple(rows)
    if any(not isinstance(row, Mapping) for row in normalized):
        raise ErrorDiagnosticsError("each row must be a mapping")
    if any(any(type(key) is not str for key in row) for row in normalized):
        raise ErrorDiagnosticsError("row keys must be built-in strings")
    return normalized


def _required_text(name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ErrorDiagnosticsError(f"{name} must be non-empty text")


def _strings(name: str, values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ErrorDiagnosticsError(f"{name} must be a sequence of strings")
    result = tuple(values)
    if any(type(value) is not str or not value for value in result):
        raise ErrorDiagnosticsError(f"{name} contains an invalid identifier")
    return result


def _source_row_ids(rows: tuple[Row, ...], row_id_field: str) -> tuple[str, ...]:
    identifiers: list[str] = []
    for index, row in enumerate(rows):
        value = row.get(row_id_field)
        if type(value) is not str or not value.strip():
            raise ErrorDiagnosticsError(f"source row {index} has an invalid row ID")
        identifiers.append(value)
    if len(set(identifiers)) != len(identifiers):
        raise ErrorDiagnosticsError("source row identifiers must be unique")
    return tuple(identifiers)


def _finite_number(value: object, name: str) -> float:
    if type(value) not in (int, float):
        raise ErrorDiagnosticsError(f"{name} must be an integer or float")
    try:
        numeric = float(cast(int | float, value))
    except OverflowError as exc:
        raise ErrorDiagnosticsError(
            f"{name} is outside the supported numeric range"
        ) from exc
    if not math.isfinite(numeric):
        raise ErrorDiagnosticsError(f"{name} must be finite")
    return numeric


def _error_summary(residuals: tuple[float, ...]) -> ErrorSummary:
    if not residuals:
        return ErrorSummary(
            "UNDEFINED_EMPTY_SAMPLE", 0, None, None, None, None, None, None, None, ()
        )
    absolute = tuple(abs(value) for value in residuals)
    try:
        mae = math.fsum(absolute) / len(absolute)
        scale = max(absolute)
        rmse = (
            0.0
            if scale == 0.0
            else scale
            * math.sqrt(
                math.fsum((value / scale) ** 2 for value in residuals) / len(residuals)
            )
        )
        mean_residual = math.fsum(residuals) / len(residuals)
    except (OverflowError, ValueError) as exc:
        raise ErrorDiagnosticsError("residual metrics overflow") from exc
    if not all(math.isfinite(value) for value in (mae, rmse, mean_residual)):
        raise ErrorDiagnosticsError("residual metrics are non-finite")
    ordered = tuple(sorted(residuals))
    ordered_absolute = tuple(sorted(absolute))
    quantiles = tuple(
        ResidualQuantile(probability, _linear_quantile(ordered, probability))
        for probability in _RESIDUAL_QUANTILES
    )
    return ErrorSummary(
        "DEFINED_SINGLE_ROW" if len(residuals) == 1 else "DEFINED",
        len(residuals),
        mae,
        rmse,
        mean_residual,
        _linear_quantile(ordered, 0.5),
        _linear_quantile(ordered_absolute, 0.5),
        ordered[0],
        ordered[-1],
        quantiles,
    )


def _linear_quantile(ordered: tuple[float, ...], probability: float) -> float:
    if not ordered or not 0.0 <= probability <= 1.0:
        raise ErrorDiagnosticsError(
            "quantile requires values and probability in [0, 1]"
        )
    position = (len(ordered) - 1) * probability
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = position - lower_index
    return (1.0 - fraction) * ordered[lower_index] + fraction * ordered[upper_index]


def _group_summaries(
    rows: tuple[Row, ...],
    position_by_id: dict[str, int],
    residuals: tuple[ResidualRecord, ...],
    group_fields: tuple[str, ...],
) -> tuple[tuple[GroupErrorSummary, ...], tuple[MissingGroupValue, ...]]:
    summaries: list[GroupErrorSummary] = []
    missing: list[MissingGroupValue] = []
    for field in group_fields:
        by_value: dict[tuple[str, JsonScalar], list[ResidualRecord]] = defaultdict(list)
        for record in residuals:
            row = rows[position_by_id[record.row_id]]
            value = row.get(field)
            if (
                field not in row
                or value is None
                or (type(value) is str and not value.strip())
            ):
                missing.append(MissingGroupValue(field, record.row_id, "missing"))
                continue
            if type(value) not in (str, int, float, bool) or (
                type(value) is float and not math.isfinite(value)
            ):
                missing.append(MissingGroupValue(field, record.row_id, "invalid_type"))
                continue
            key = (type(value).__name__, cast(JsonScalar, value))
            by_value[key].append(record)
        for (_, value), group_records in sorted(
            by_value.items(), key=lambda item: (item[0][0], repr(item[0][1]))
        ):
            errors = tuple(item.residual for item in group_records)
            summary = _error_summary(errors)
            summaries.append(
                GroupErrorSummary(
                    field,
                    value,
                    tuple(item.row_id for item in group_records),
                    len(group_records),
                    summary.mae,
                    summary.rmse,
                    summary.mean_signed_residual,
                    summary.status,
                )
            )
    return tuple(summaries), tuple(missing)


def _uncertainty_diagnostics(
    rows: tuple[Row, ...],
    row_ids: tuple[str, ...],
    specs: tuple[UncertaintyFieldSpec, ...],
) -> tuple[UncertaintyFieldDiagnostic, ...]:
    output: list[UncertaintyFieldDiagnostic] = []
    for spec in specs:
        missing: list[str] = []
        invalid_numeric: list[str] = []
        invalid_type: list[str] = []
        values: list[UncertaintyValue] = []
        numeric_by_row: dict[str, float] = {}
        for row, row_id in zip(rows, row_ids, strict=True):
            if spec.field not in row or row[spec.field] is None:
                missing.append(row_id)
                values.append(UncertaintyValue(row_id, None, "MISSING", False))
                continue
            value = row[spec.field]
            if spec.role is UncertaintyRole.METADATA:
                safe_value, omitted = _safe_scalar(value)
                status = "PRESENT" if not omitted else "UNSUPPORTED_TYPE"
                if omitted:
                    invalid_type.append(row_id)
                values.append(UncertaintyValue(row_id, safe_value, status, omitted))
                continue
            if type(value) not in (int, float):
                safe_value, omitted = _safe_scalar(value)
                status = "INVALID_NUMERIC"
                invalid_numeric.append(row_id)
                values.append(UncertaintyValue(row_id, safe_value, status, omitted))
                continue
            try:
                numeric = float(cast(int | float, value))
            except OverflowError:
                invalid_numeric.append(row_id)
                values.append(UncertaintyValue(row_id, None, "OUT_OF_RANGE", True))
                continue
            if not math.isfinite(numeric):
                invalid_numeric.append(row_id)
                values.append(UncertaintyValue(row_id, None, "NON_FINITE", True))
                continue
            numeric_by_row[row_id] = numeric
            values.append(
                UncertaintyValue(row_id, cast(JsonScalar, value), "PRESENT", False)
            )
        inconsistent: list[str] = []
        if spec.role in (UncertaintyRole.LOWER_BOUND, UncertaintyRole.UPPER_BOUND):
            pair_specs = tuple(
                item
                for item in specs
                if item.pair_id == spec.pair_id
                and item.role
                in (UncertaintyRole.LOWER_BOUND, UncertaintyRole.UPPER_BOUND)
            )
            lower_spec = next(
                (
                    item
                    for item in pair_specs
                    if item.role is UncertaintyRole.LOWER_BOUND
                ),
                None,
            )
            upper_spec = next(
                (
                    item
                    for item in pair_specs
                    if item.role is UncertaintyRole.UPPER_BOUND
                ),
                None,
            )
            if lower_spec is not None and upper_spec is not None:
                lower_by_row = _finite_field_values(rows, row_ids, lower_spec.field)
                upper_by_row = _finite_field_values(rows, row_ids, upper_spec.field)
                inconsistent = [
                    row_id
                    for row_id in row_ids
                    if row_id in lower_by_row
                    and row_id in upper_by_row
                    and lower_by_row[row_id] > upper_by_row[row_id]
                ]
        output.append(
            UncertaintyFieldDiagnostic(
                spec.field,
                spec.role,
                spec.pair_id,
                len(rows),
                len(rows) - len(missing),
                tuple(missing),
                tuple(invalid_numeric),
                tuple(invalid_type),
                tuple(inconsistent),
                tuple(values),
            )
        )
    return tuple(output)


def _validate_bound_specs(specs: tuple[UncertaintyFieldSpec, ...]) -> None:
    roles_by_pair: dict[str, Counter[UncertaintyRole]] = defaultdict(Counter)
    for spec in specs:
        if spec.pair_id is not None and spec.role in (
            UncertaintyRole.LOWER_BOUND,
            UncertaintyRole.UPPER_BOUND,
        ):
            roles_by_pair[spec.pair_id][spec.role] += 1
    if any(count > 1 for roles in roles_by_pair.values() for count in roles.values()):
        raise ErrorDiagnosticsError(
            "each bound pair may declare at most one lower and one upper field"
        )


def _finite_field_values(
    rows: tuple[Row, ...], row_ids: tuple[str, ...], field: str
) -> dict[str, float]:
    values = {}
    for row, row_id in zip(rows, row_ids, strict=True):
        value = row.get(field)
        if type(value) in (int, float):
            try:
                numeric = float(cast(int | float, value))
            except OverflowError:
                continue
            if math.isfinite(numeric):
                values[row_id] = numeric
    return values


def _safe_scalar(value: object) -> tuple[JsonScalar, bool]:
    if value is None or type(value) in (str, int, bool):
        return cast(JsonScalar, value), False
    if type(value) is float:
        return (value, False) if math.isfinite(value) else (None, True)
    return None, True


def _selection_diagnostics(
    rows: tuple[Row, ...],
    report: DatasetValidationReport,
    feature_field: str,
    target_field: str,
) -> SelectionDiagnostics:
    accepted_indices = report.valid_record_indices
    excluded_indices = tuple(item.row_index for item in report.excluded_rows)
    counts_by_reason: Counter[str] = Counter()
    counts_by_field_reason: Counter[tuple[str, str]] = Counter()
    for excluded in report.excluded_rows:
        for finding in excluded.findings:
            counts_by_reason[finding.reason_code] += 1
            counts_by_field_reason[(finding.field, finding.reason_code)] += 1
    coverage = tuple(
        _field_coverage(rows, field, "all_input_rows")
        for field in (feature_field, target_field)
    ) + tuple(
        _field_coverage(
            tuple(rows[index] for index in accepted_indices),
            field,
            "mechanically_accepted_rows",
        )
        for field in (feature_field, target_field)
    )
    identity_report = diagnose_identity_groups(rows)
    identity_coverage = tuple(
        IdentityCoverage(
            item.field,
            len(item.missing_row_indices),
            len(item.invalid_type_row_indices),
            len(rows)
            - len(item.missing_row_indices)
            - len(item.invalid_type_row_indices),
        )
        for item in identity_report.identity_fields
    )
    accepted_features = tuple(
        rows[index].get(feature_field) for index in accepted_indices
    )
    excluded_features = tuple(
        rows[index].get(feature_field) for index in excluded_indices
    )
    return SelectionDiagnostics(
        len(rows),
        len(accepted_indices),
        len(excluded_indices),
        tuple(sorted(counts_by_reason.items())),
        tuple(
            (field, reason, count)
            for (field, reason), count in sorted(counts_by_field_reason.items())
        ),
        coverage,
        identity_coverage,
        _numeric_distribution(accepted_features),
        _numeric_distribution(excluded_features),
        "NOT_ASSESSED",
        "NOT_ASSESSED",
        "NOT_ESTABLISHED_FROM_SYNTHETIC_DATA",
    )


def _field_coverage(rows: Sequence[Row], field: str, population: str) -> FieldCoverage:
    present = missing = finite = non_finite = invalid = 0
    for row in rows:
        if (
            field not in row
            or row[field] is None
            or (type(row[field]) is str and not cast(str, row[field]).strip())
        ):
            missing += 1
            continue
        present += 1
        value = row[field]
        if type(value) is int:
            finite += 1
        elif type(value) is float:
            if math.isfinite(value):
                finite += 1
            else:
                non_finite += 1
        else:
            invalid += 1
    return FieldCoverage(
        field, population, len(rows), present, missing, finite, non_finite, invalid
    )


def _numeric_distribution(values: Sequence[object]) -> NumericDistribution:
    numeric_values: list[float] = []
    for value in values:
        if type(value) not in (int, float):
            continue
        try:
            numeric_value = float(cast(int | float, value))
        except OverflowError:
            continue
        if math.isfinite(numeric_value):
            numeric_values.append(numeric_value)
    numeric = tuple(numeric_values)
    if not numeric:
        return NumericDistribution("UNDEFINED_NO_FINITE_VALUES", 0, None, None, None)
    return NumericDistribution(
        "DESCRIPTIVE_ONLY",
        len(numeric),
        min(numeric),
        max(numeric),
        sum(numeric) / len(numeric),
    )


def _report_document(report: ErrorSelectionDiagnosticReport) -> dict[str, object]:
    link = report.manifest_linkage
    manifest = (
        {
            "experiment_id": link.experiment_id,
            "configuration_sha256": link.configuration_sha256,
            "manifest_sha256": link.manifest_sha256,
            "manifest_schema_version": link.manifest_schema_version,
            "integrity_note": "caller-declared linkage; artifacts are not "
            "authenticated here",
        }
        if link is not None
        else None
    )
    return {
        "schema_version": report.schema_version,
        "experiment_id": report.experiment_id,
        "fixture_id": report.fixture_id,
        "scientific_policy_status": report.scientific_policy_status,
        "residual_convention": report.residual_convention,
        "test_row_ids": list(report.test_row_ids),
        "residual_records": [
            {
                "row_id": item.row_id,
                "observed_target": item.observed_target,
                "predicted_target": item.predicted_target,
                "residual": item.residual,
                "absolute_error": item.absolute_error,
                "squared_error": item.squared_error,
            }
            for item in report.residual_records
        ],
        "aggregate_errors": _summary_document(report.aggregate_errors),
        "group_errors": [
            {
                "field": item.field,
                "value": item.value,
                "row_ids": list(item.row_ids),
                "row_count": item.row_count,
                "mae": item.mae,
                "rmse": item.rmse,
                "mean_signed_residual": item.mean_signed_residual,
                "metric_status": item.metric_status,
            }
            for item in report.group_errors
        ],
        "missing_group_values": [
            {"field": item.field, "row_id": item.row_id, "reason": item.reason}
            for item in report.missing_group_values
        ],
        "uncertainty_fields": [
            {
                "field": item.field,
                "role": item.role.value,
                "pair_id": item.pair_id,
                "row_count": item.row_count,
                "present_count": item.present_count,
                "missing_row_ids": list(item.missing_row_ids),
                "invalid_numeric_row_ids": list(item.invalid_numeric_row_ids),
                "invalid_type_row_ids": list(item.invalid_type_row_ids),
                "inconsistent_bound_row_ids": list(item.inconsistent_bound_row_ids),
                "values": [
                    {
                        "row_id": value.row_id,
                        "value": value.value,
                        "status": value.status,
                        "value_omitted": value.value_omitted,
                    }
                    for value in item.values
                ],
            }
            for item in report.uncertainty_fields
        ],
        "selection": _selection_document(report.selection),
        "warnings": list(report.warnings),
        "limitations": list(report.limitations),
        "manifest_linkage": manifest,
    }


def _summary_document(summary: ErrorSummary) -> dict[str, object]:
    return {
        "status": summary.status,
        "row_count": summary.row_count,
        "mae": summary.mae,
        "rmse": summary.rmse,
        "mean_signed_residual": summary.mean_signed_residual,
        "median_signed_residual": summary.median_signed_residual,
        "median_absolute_error": summary.median_absolute_error,
        "minimum_residual": summary.minimum_residual,
        "maximum_residual": summary.maximum_residual,
        "quantiles": [
            {"probability": item.probability, "value": item.value}
            for item in summary.quantiles
        ],
    }


def _selection_document(selection: SelectionDiagnostics) -> dict[str, object]:
    return {
        "input_row_count": selection.input_row_count,
        "mechanically_accepted_row_count": selection.mechanically_accepted_row_count,
        "excluded_row_count": selection.excluded_row_count,
        "exclusions_by_reason": [
            {"reason": reason, "count": count}
            for reason, count in selection.exclusions_by_reason
        ],
        "exclusions_by_field_and_reason": [
            {"field": field, "reason": reason, "count": count}
            for field, reason, count in selection.exclusions_by_field_and_reason
        ],
        "feature_target_coverage": [
            {
                "field": item.field,
                "population": item.population,
                "row_count": item.row_count,
                "present_count": item.present_count,
                "missing_count": item.missing_count,
                "finite_numeric_count": item.finite_numeric_count,
                "non_finite_count": item.non_finite_count,
                "invalid_value_count": item.invalid_value_count,
            }
            for item in selection.feature_target_coverage
        ],
        "identity_coverage": [
            {
                "field": item.field,
                "missing_count": item.missing_count,
                "invalid_type_count": item.invalid_type_count,
                "present_count": item.present_count,
            }
            for item in selection.identity_coverage
        ],
        "feature_distribution_in_accepted_rows": _distribution_document(
            selection.feature_distribution_in_accepted_rows
        ),
        "feature_distribution_in_excluded_rows": _distribution_document(
            selection.feature_distribution_in_excluded_rows
        ),
        "scientific_eligibility_status": selection.scientific_eligibility_status,
        "cohort_selection_status": selection.cohort_selection_status,
        "selection_bias_status": selection.sampling_bias_status,
    }


def _distribution_document(distribution: NumericDistribution) -> dict[str, object]:
    return {
        "status": distribution.status,
        "value_count": distribution.value_count,
        "minimum": distribution.minimum,
        "maximum": distribution.maximum,
        "mean": distribution.mean,
    }
