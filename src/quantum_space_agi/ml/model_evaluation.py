"""Explicit-partition evaluation for numeric regression models."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, Protocol, TypeAlias

from quantum_space_agi.data import Provenance
from quantum_space_agi.ml.dataset_preparation import (
    NumericValue,
    PreparedRegressionDataset,
)
from quantum_space_agi.ml.experiment_manifest import ResearchTask

MetricName: TypeAlias = Literal["MAE", "RMSE", "R2"]
MetricStatus: TypeAlias = Literal["DEFINED", "UNDEFINED"]
_FeatureRows: TypeAlias = tuple[tuple[NumericValue, ...], ...]


class RegressionEvaluationError(ValueError):
    """Invalid evaluation partitions, model behavior, or metric inputs."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class NumericRegressionModel(Protocol):
    """Model interface; fit sees training data and predict sees feature rows only."""

    def fit(
        self, feature_rows: _FeatureRows, target_values: tuple[NumericValue, ...]
    ) -> object:
        """Fit the model using the supplied training partition."""

    def predict(self, feature_rows: _FeatureRows) -> Sequence[NumericValue]:
        """Return one prediction per feature row, in the same order."""


@dataclass(frozen=True, slots=True)
class RegressionMetric:
    """One named metric and its defined or undefined status."""

    name: MetricName
    value: float | None
    status: MetricStatus
    reason: str | None
    unit: str | None

    def __post_init__(self) -> None:
        if type(self.name) is not str or self.name not in ("MAE", "RMSE", "R2"):
            raise RegressionEvaluationError("invalid_result", "unsupported metric name")
        if type(self.status) is not str or self.status not in ("DEFINED", "UNDEFINED"):
            raise RegressionEvaluationError("invalid_result", "invalid metric status")
        if self.status == "DEFINED":
            if (
                type(self.value) is not float
                or not math.isfinite(self.value)
                or self.reason is not None
            ):
                raise RegressionEvaluationError(
                    "invalid_result",
                    "defined metrics require a finite value and no reason",
                )
        elif self.value is not None or type(self.reason) is not str or not self.reason:
            raise RegressionEvaluationError(
                "invalid_result", "undefined metrics require a reason and no value"
            )
        if self.name == "R2":
            if self.unit is not None:
                raise RegressionEvaluationError("invalid_result", "R2 must be unitless")
        elif self.unit is not None and (
            type(self.unit) is not str or not self.unit.strip()
        ):
            raise RegressionEvaluationError(
                "invalid_result", "metric unit must be non-empty text or null"
            )


@dataclass(frozen=True, slots=True)
class RegressionMetrics:
    """MAE, RMSE and R-squared for one evaluation partition."""

    mae: RegressionMetric
    rmse: RegressionMetric
    r2: RegressionMetric

    def __post_init__(self) -> None:
        if (
            type(self.mae) is not RegressionMetric
            or self.mae.name != "MAE"
            or type(self.rmse) is not RegressionMetric
            or self.rmse.name != "RMSE"
            or type(self.r2) is not RegressionMetric
            or self.r2.name != "R2"
        ):
            raise RegressionEvaluationError(
                "invalid_result", "metrics must be ordered as MAE, RMSE and R2"
            )


@dataclass(frozen=True, slots=True)
class RegressionPrediction:
    """Observed and predicted target tied to one source-row identity."""

    source_row_index: int
    observed_target: NumericValue
    predicted_target: NumericValue

    def __post_init__(self) -> None:
        if type(self.source_row_index) is not int or self.source_row_index < 0:
            raise RegressionEvaluationError(
                "invalid_result", "source_row_index must be a non-negative integer"
            )
        for value in (self.observed_target, self.predicted_target):
            if type(value) not in (int, float) or (
                type(value) is float and not math.isfinite(value)
            ):
                raise RegressionEvaluationError(
                    "invalid_result",
                    "prediction values must be finite built-in numbers",
                )


@dataclass(frozen=True, slots=True)
class RegressionEvaluationResult:
    """Immutable evaluation metadata, partitions, aligned predictions and metrics."""

    task: ResearchTask
    model_identifier: str
    feature_fields: tuple[str, ...]
    target_field: str
    target_unit: str | None
    schema_id: str
    schema_version: str
    provenance: Provenance
    training_source_row_indices: tuple[int, ...]
    evaluation_source_row_indices: tuple[int, ...]
    predictions: tuple[RegressionPrediction, ...]
    metrics: RegressionMetrics
    evaluation_protocol: str = "explicit caller-supplied source-row partitions"

    def __post_init__(self) -> None:
        if type(self.task) is not ResearchTask:
            raise RegressionEvaluationError(
                "invalid_result", "task must be ResearchTask"
            )
        if type(self.model_identifier) is not str or not self.model_identifier.strip():
            raise RegressionEvaluationError(
                "invalid_result", "model_identifier must be non-empty text"
            )
        if (
            type(self.feature_fields) is not tuple
            or not self.feature_fields
            or any(type(field) is not str or not field for field in self.feature_fields)
            or len(set(self.feature_fields)) != len(self.feature_fields)
        ):
            raise RegressionEvaluationError(
                "invalid_result", "feature_fields are invalid"
            )
        if (
            type(self.target_field) is not str
            or not self.target_field
            or self.target_field in self.feature_fields
        ):
            raise RegressionEvaluationError("invalid_result", "target_field is invalid")
        if (
            self.task.objective is None
            or self.task.target is None
            or not self.task.features
            or tuple(item.field for item in self.task.features) != self.feature_fields
            or self.task.target.field != self.target_field
            or self.task.target.unit != self.target_unit
        ):
            raise RegressionEvaluationError(
                "invalid_result", "task metadata is inconsistent"
            )
        if type(self.schema_id) is not str or not self.schema_id:
            raise RegressionEvaluationError("invalid_result", "schema_id is invalid")
        if type(self.schema_version) is not str or not self.schema_version:
            raise RegressionEvaluationError(
                "invalid_result", "schema_version is invalid"
            )
        if type(self.provenance) is not Provenance:
            raise RegressionEvaluationError("invalid_result", "provenance is invalid")
        training = _validated_id_tuple(
            self.training_source_row_indices, "training_source_row_indices"
        )
        evaluation = _validated_id_tuple(
            self.evaluation_source_row_indices, "evaluation_source_row_indices"
        )
        if not training or not evaluation:
            raise RegressionEvaluationError(
                "invalid_result", "training and evaluation identities must be non-empty"
            )
        if set(training).intersection(evaluation):
            raise RegressionEvaluationError(
                "invalid_result", "training and evaluation identities must be disjoint"
            )
        if type(self.predictions) is not tuple or any(
            type(item) is not RegressionPrediction for item in self.predictions
        ):
            raise RegressionEvaluationError("invalid_result", "predictions are invalid")
        if tuple(item.source_row_index for item in self.predictions) != evaluation:
            raise RegressionEvaluationError(
                "invalid_result", "predictions must align with evaluation identities"
            )
        if type(self.metrics) is not RegressionMetrics:
            raise RegressionEvaluationError("invalid_result", "metrics are invalid")
        expected_metrics = calculate_regression_metrics(
            tuple(item.observed_target for item in self.predictions),
            tuple(item.predicted_target for item in self.predictions),
            target_unit=self.target_unit,
        )
        if self.metrics != expected_metrics:
            raise RegressionEvaluationError(
                "invalid_result", "metrics do not match aligned predictions"
            )
        if type(self.evaluation_protocol) is not str or not self.evaluation_protocol:
            raise RegressionEvaluationError(
                "invalid_result", "evaluation_protocol must be non-empty text"
            )

    @property
    def observed_targets(self) -> tuple[NumericValue, ...]:
        """Observed evaluation targets in source-row order."""
        return tuple(item.observed_target for item in self.predictions)

    @property
    def predicted_targets(self) -> tuple[NumericValue, ...]:
        """Predictions in evaluation source-row order."""
        return tuple(item.predicted_target for item in self.predictions)


def calculate_regression_metrics(
    observed_targets: Sequence[NumericValue],
    predicted_targets: Sequence[NumericValue],
    *,
    target_unit: str | None = None,
) -> RegressionMetrics:
    """Calculate MAE, RMSE and R² for aligned finite numeric values.

    R² is undefined with fewer than two rows or constant observed targets.
    This function does not apply a threshold or interpret scientific adequacy.
    """
    observed = _metric_values(observed_targets, "observed_targets")
    predicted = _metric_values(predicted_targets, "predicted_targets")
    if not observed or len(observed) != len(predicted):
        raise RegressionEvaluationError(
            "invalid_metrics", "metric inputs must be non-empty and aligned"
        )
    if target_unit is not None and (
        type(target_unit) is not str or not target_unit.strip()
    ):
        raise RegressionEvaluationError("invalid_metrics", "target_unit is invalid")

    errors = tuple(
        actual - estimate for actual, estimate in zip(observed, predicted, strict=True)
    )
    if any(not math.isfinite(error) for error in errors):
        raise RegressionEvaluationError(
            "metric_overflow", "residual arithmetic overflowed"
        )
    try:
        mae = math.fsum(abs(error) for error in errors) / len(errors)
        rmse = math.sqrt(math.fsum(error * error for error in errors) / len(errors))
    except (OverflowError, ValueError) as exc:
        raise RegressionEvaluationError(
            "metric_overflow", "metric calculation overflowed"
        ) from exc
    if not math.isfinite(mae) or not math.isfinite(rmse):
        raise RegressionEvaluationError("metric_overflow", "MAE/RMSE is non-finite")

    mae_metric = RegressionMetric("MAE", mae, "DEFINED", None, target_unit)
    rmse_metric = RegressionMetric("RMSE", rmse, "DEFINED", None, target_unit)
    if len(observed) < 2:
        r2_metric = RegressionMetric(
            "R2", None, "UNDEFINED", "fewer than two evaluation rows", None
        )
    else:
        try:
            mean_observed = math.fsum(observed) / len(observed)
            total_sum_squares = math.fsum(
                (value - mean_observed) ** 2 for value in observed
            )
            residual_sum_squares = math.fsum(error * error for error in errors)
        except (OverflowError, ValueError) as exc:
            raise RegressionEvaluationError(
                "metric_overflow", "R2 calculation overflowed"
            ) from exc
        if not math.isfinite(mean_observed) or not math.isfinite(total_sum_squares):
            raise RegressionEvaluationError(
                "metric_overflow", "R2 target variance overflowed"
            )
        if total_sum_squares == 0.0:
            r2_metric = RegressionMetric(
                "R2", None, "UNDEFINED", "constant evaluation targets", None
            )
        else:
            r2 = 1.0 - residual_sum_squares / total_sum_squares
            if not math.isfinite(r2):
                raise RegressionEvaluationError("metric_overflow", "R2 is non-finite")
            r2_metric = RegressionMetric("R2", r2, "DEFINED", None, None)
    return RegressionMetrics(mae_metric, rmse_metric, r2_metric)


def evaluate_regression_model(
    prepared: PreparedRegressionDataset,
    *,
    training_source_row_indices: Sequence[int],
    evaluation_source_row_indices: Sequence[int],
    model: NumericRegressionModel,
    model_identifier: str,
) -> RegressionEvaluationResult:
    """Fit on explicit training rows and evaluate on disjoint explicit rows.

    The evaluator never creates a split. IDs must refer to mechanically
    prepared accepted records; records excluded during preparation cannot be
    used for either partition. Model methods receive immutable numeric tuples.
    """
    if type(prepared) is not PreparedRegressionDataset:
        raise RegressionEvaluationError(
            "invalid_prepared_data", "prepared must be PreparedRegressionDataset"
        )
    if prepared.task.target is None:
        raise RegressionEvaluationError(
            "invalid_prepared_data", "prepared task must declare a target"
        )
    target_declaration = prepared.task.target
    if type(model_identifier) is not str or not model_identifier.strip():
        raise RegressionEvaluationError(
            "invalid_model_identifier", "model_identifier must be non-empty text"
        )
    if not callable(getattr(model, "fit", None)) or not callable(
        getattr(model, "predict", None)
    ):
        raise RegressionEvaluationError(
            "invalid_model", "model must provide fit and predict"
        )

    training_ids = _row_ids(training_source_row_indices, "training_source_row_indices")
    evaluation_ids = _row_ids(
        evaluation_source_row_indices, "evaluation_source_row_indices"
    )
    if not training_ids or not evaluation_ids:
        raise RegressionEvaluationError(
            "empty_partition", "training and evaluation partitions must be non-empty"
        )
    if set(training_ids).intersection(evaluation_ids):
        raise RegressionEvaluationError(
            "partition_overlap",
            "training and evaluation row identities must be disjoint",
        )

    accepted = {record.source_row_index: record for record in prepared.accepted_records}
    input_ids = set(prepared.input_source_row_indices)
    requested = set(training_ids).union(evaluation_ids)
    unknown = requested.difference(input_ids)
    if unknown:
        raise RegressionEvaluationError(
            "unknown_identity", f"unknown source-row identities: {sorted(unknown)}"
        )
    excluded = requested.difference(accepted)
    if excluded:
        raise RegressionEvaluationError(
            "unprepared_identity",
            "source-row identities were excluded during preparation: "
            f"{sorted(excluded)}",
        )

    training_records = tuple(accepted[index] for index in training_ids)
    evaluation_records = tuple(accepted[index] for index in evaluation_ids)
    training_features = tuple(record.feature_values for record in training_records)
    training_targets = tuple(record.target_value for record in training_records)
    evaluation_features = tuple(record.feature_values for record in evaluation_records)

    try:
        model.fit(training_features, training_targets)
    except Exception as exc:
        raise RegressionEvaluationError("model_fit_failed", "model.fit failed") from exc
    try:
        raw_predictions = model.predict(evaluation_features)
    except Exception as exc:
        raise RegressionEvaluationError(
            "model_prediction_failed", "model.predict failed"
        ) from exc
    predictions = _prediction_values(raw_predictions)
    if len(predictions) != len(evaluation_records):
        raise RegressionEvaluationError(
            "prediction_count_mismatch",
            "model must return exactly one prediction per evaluation row",
        )

    observations = tuple(record.target_value for record in evaluation_records)
    metrics = calculate_regression_metrics(
        observations, predictions, target_unit=target_declaration.unit
    )
    aligned_predictions = tuple(
        RegressionPrediction(record.source_row_index, record.target_value, prediction)
        for record, prediction in zip(evaluation_records, predictions, strict=True)
    )
    return RegressionEvaluationResult(
        task=prepared.task,
        model_identifier=model_identifier,
        feature_fields=prepared.feature_fields,
        target_field=prepared.target_field,
        target_unit=target_declaration.unit,
        schema_id=prepared.schema_id,
        schema_version=prepared.schema_version,
        provenance=prepared.provenance,
        training_source_row_indices=training_ids,
        evaluation_source_row_indices=evaluation_ids,
        predictions=aligned_predictions,
        metrics=metrics,
    )


def _row_ids(values: Sequence[int], name: str) -> tuple[int, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise RegressionEvaluationError(
            "invalid_identity", f"{name} must be a sequence"
        )
    ids = tuple(values)
    if any(type(index) is not int or index < 0 for index in ids):
        raise RegressionEvaluationError(
            "invalid_identity", f"{name} must contain non-negative built-in integers"
        )
    if len(set(ids)) != len(ids):
        raise RegressionEvaluationError(
            "duplicate_identity", f"{name} contains duplicates"
        )
    return ids


def _validated_id_tuple(values: object, name: str) -> tuple[int, ...]:
    if type(values) is not tuple or any(
        type(index) is not int or index < 0 for index in values
    ):
        raise RegressionEvaluationError("invalid_result", f"{name} is invalid")
    if len(set(values)) != len(values):
        raise RegressionEvaluationError("invalid_result", f"{name} contains duplicates")
    return values


def _metric_values(values: Sequence[NumericValue], name: str) -> tuple[float, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise RegressionEvaluationError("invalid_metrics", f"{name} must be a sequence")
    converted: list[float] = []
    for value in values:
        if type(value) not in (int, float):
            raise RegressionEvaluationError(
                "invalid_metrics", f"{name} must contain finite built-in numbers"
            )
        try:
            number = float(value)
        except (OverflowError, ValueError) as exc:
            raise RegressionEvaluationError(
                "invalid_metrics", f"{name} is out of range"
            ) from exc
        if not math.isfinite(number):
            raise RegressionEvaluationError(
                "invalid_metrics", f"{name} must contain finite built-in numbers"
            )
        converted.append(number)
    return tuple(converted)


def _prediction_values(values: object) -> tuple[NumericValue, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise RegressionEvaluationError(
            "invalid_predictions", "model.predict must return a numeric sequence"
        )
    predictions = tuple(values)
    if any(
        type(value) not in (int, float)
        or (type(value) is float and not math.isfinite(value))
        for value in predictions
    ):
        raise RegressionEvaluationError(
            "invalid_predictions", "predictions must be finite built-in numbers"
        )
    return predictions
