"""Synthetic tests for explicit-partition numeric regression evaluation."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from statistics import median

import pytest

from quantum_space_agi.data import (
    DataFormat,
    DataSchema,
    Dataset,
    DataSource,
    FieldSchema,
    Provenance,
)
from quantum_space_agi.ml import (
    DecisionDeclaration,
    DecisionStatus,
    RegressionMetric,
    RegressionMetrics,
    ResearchTask,
    VariableDeclaration,
    calculate_regression_metrics,
    evaluate_regression_model,
)
from quantum_space_agi.ml.dataset_preparation import prepare_regression_dataset
from quantum_space_agi.ml.model_evaluation import RegressionEvaluationError
from quantum_space_agi.ml.synthetic_baseline import MedianDummyRegressor


def prepared_fixture():
    rows = [
        {"feature": 1.0, "target": 2.0},
        {"feature": 2.0, "target": 4.0},
        {"feature": 3.0, "target": 6.0},
        {"feature": 4.0, "target": 8.0},
        {"feature": None, "target": 10.0},
    ]
    dataset = Dataset(
        provenance=Provenance(
            dataset_id="synthetic-evaluation-fixture",
            source=DataSource("synthetic-fixture"),
            retrieved_at=datetime(2026, 11, 10, tzinfo=UTC),
            data_format=DataFormat.JSON,
        ),
        records=rows,  # type: ignore[arg-type]
    )
    task = ResearchTask(
        objective="Predict an invented synthetic target.",
        target=VariableDeclaration("target", "synthetic units"),
        features=(VariableDeclaration("feature", "synthetic units"),),
        inference_description="Synthetic test records only.",
        decision=DecisionDeclaration(
            DecisionStatus.PENDING_REVIEW,
            rationale="Software test; no scientific approval is implied.",
        ),
    )
    schema = DataSchema(
        "synthetic-evaluation-schema",
        "1",
        (FieldSchema("feature", float), FieldSchema("target", float)),
    )
    prepared = prepare_regression_dataset(
        dataset, task, schema, source_row_indices=(10, 20, 30, 40, 50)
    )
    return rows, prepared


class CaptureMedianModel:
    def __init__(self) -> None:
        self.fit_features: tuple[tuple[int | float, ...], ...] | None = None
        self.fit_targets: tuple[int | float, ...] | None = None
        self.constant: float | None = None

    def fit(
        self,
        feature_rows: tuple[tuple[int | float, ...], ...],
        target_values: tuple[int | float, ...],
    ) -> None:
        self.fit_features = feature_rows
        self.fit_targets = target_values
        self.constant = float(median(target_values))

    def predict(
        self, feature_rows: tuple[tuple[int | float, ...], ...]
    ) -> tuple[float, ...]:
        assert self.constant is not None
        return (self.constant,) * len(feature_rows)


class DoubleFeatureModel:
    def fit(
        self,
        feature_rows: tuple[tuple[int | float, ...], ...],
        target_values: tuple[int | float, ...],
    ) -> None:
        assert len(feature_rows) == len(target_values)

    def predict(
        self, feature_rows: tuple[tuple[int | float, ...], ...]
    ) -> tuple[int | float, ...]:
        return tuple(row[0] * 2 for row in feature_rows)


class FixedPredictionModel:
    def __init__(self, predictions: object) -> None:
        self.predictions = predictions

    def fit(
        self,
        feature_rows: tuple[tuple[int | float, ...], ...],
        target_values: tuple[int | float, ...],
    ) -> None:
        pass

    def predict(self, feature_rows: tuple[tuple[int | float, ...], ...]) -> object:
        return self.predictions


def run_evaluation(model: object, *, train=(10, 20), evaluate=(40, 30)):
    _, prepared = prepared_fixture()
    return evaluate_regression_model(
        prepared,
        training_source_row_indices=train,
        evaluation_source_row_indices=evaluate,
        model=model,  # type: ignore[arg-type]
        model_identifier="synthetic-test-model/1",
    )


def test_median_model_fits_training_only_and_preserves_evaluation_order() -> None:
    model = CaptureMedianModel()
    result = run_evaluation(model)

    assert model.fit_features == ((1.0,), (2.0,))
    assert model.fit_targets == (2.0, 4.0)
    assert result.training_source_row_indices == (10, 20)
    assert result.evaluation_source_row_indices == (40, 30)
    assert tuple(row.source_row_index for row in result.predictions) == (40, 30)
    assert result.observed_targets == (8.0, 6.0)
    assert result.predicted_targets == (3.0, 3.0)
    assert result.provenance.dataset_id == "synthetic-evaluation-fixture"
    assert result.task.objective == "Predict an invented synthetic target."
    assert result.metrics.mae.value == 4.0
    assert result.metrics.mae.unit == "synthetic units"
    assert result.metrics.rmse.value == pytest.approx(17**0.5)
    assert result.metrics.r2.value == -16.0


def test_evaluation_targets_are_never_passed_to_model_fit() -> None:
    model = CaptureMedianModel()
    run_evaluation(model)

    assert model.fit_targets == (2.0, 4.0)
    assert 6.0 not in model.fit_targets
    assert 8.0 not in model.fit_targets


def test_second_model_uses_prepared_feature_matrix() -> None:
    result = run_evaluation(DoubleFeatureModel(), train=(10, 20), evaluate=(30, 40))

    assert result.predicted_targets == (6.0, 8.0)
    assert result.metrics.mae.value == 0.0
    assert result.metrics.rmse.value == 0.0
    assert result.metrics.r2.value == 1.0


@pytest.mark.parametrize(
    ("train", "evaluate", "code"),
    [
        ((10,), (10,), "partition_overlap"),
        ((999,), (30,), "unknown_identity"),
        ((10, 10), (30,), "duplicate_identity"),
        ((), (30,), "empty_partition"),
        ((10,), (), "empty_partition"),
        ((50,), (30,), "unprepared_identity"),
        ((True,), (30,), "invalid_identity"),
        ((-1,), (30,), "invalid_identity"),
    ],
)
def test_invalid_partitions_fail_before_model_fitting(
    train: tuple[int, ...], evaluate: tuple[int, ...], code: str
) -> None:
    model = CaptureMedianModel()
    with pytest.raises(RegressionEvaluationError) as error:
        run_evaluation(model, train=train, evaluate=evaluate)
    assert error.value.code == code
    assert model.fit_targets is None


@pytest.mark.parametrize(
    "predictions", [(1.0,), (float("nan"), 1.0), (float("inf"), 1.0), (True, 1.0)]
)
def test_malformed_prediction_outputs_are_rejected(
    predictions: tuple[object, ...],
) -> None:
    with pytest.raises(RegressionEvaluationError):
        run_evaluation(FixedPredictionModel(predictions))


def test_prediction_output_must_be_a_sequence() -> None:
    with pytest.raises(RegressionEvaluationError, match="sequence"):
        run_evaluation(FixedPredictionModel(3.0))


def test_calculate_regression_metrics_matches_definitions() -> None:
    metrics = calculate_regression_metrics(
        (2.0, 4.0), (3.0, 2.0), target_unit="synthetic units"
    )

    assert metrics.mae.value == 1.5
    assert metrics.rmse.value == pytest.approx(2.5**0.5)
    assert metrics.r2.value == -1.5
    assert metrics.mae.status == metrics.rmse.status == metrics.r2.status == "DEFINED"
    assert metrics.r2.unit is None


@pytest.mark.parametrize(
    ("observed", "reason"),
    [
        ((3.0,), "fewer than two evaluation rows"),
        ((3.0, 3.0), "constant evaluation targets"),
    ],
)
def test_degenerate_r2_is_explicitly_undefined(
    observed: tuple[float, ...], reason: str
) -> None:
    metrics = calculate_regression_metrics(observed, (2.0,) * len(observed))

    assert metrics.mae.status == "DEFINED"
    assert metrics.rmse.status == "DEFINED"
    assert metrics.r2.value is None
    assert metrics.r2.status == "UNDEFINED"
    assert metrics.r2.reason == reason


def test_metric_inputs_must_be_finite_aligned_and_non_empty() -> None:
    with pytest.raises(RegressionEvaluationError, match="finite"):
        calculate_regression_metrics((1.0, float("nan")), (1.0, 2.0))
    with pytest.raises(RegressionEvaluationError, match="aligned"):
        calculate_regression_metrics((1.0,), (1.0, 2.0))
    with pytest.raises(RegressionEvaluationError, match="non-empty"):
        calculate_regression_metrics((), ())
    with pytest.raises(RegressionEvaluationError, match="overflow"):
        calculate_regression_metrics((1e308, 1e308), (1e308, 1e308))


def test_evaluation_is_deterministic_and_does_not_mutate_prepared_input() -> None:
    source_rows, prepared = prepared_fixture()
    original = deepcopy(source_rows)
    first = evaluate_regression_model(
        prepared,
        training_source_row_indices=(10, 20),
        evaluation_source_row_indices=(30, 40),
        model=MedianDummyRegressor(),
        model_identifier="median-dummy/1",
    )
    second = evaluate_regression_model(
        prepared,
        training_source_row_indices=(10, 20),
        evaluation_source_row_indices=(30, 40),
        model=MedianDummyRegressor(),
        model_identifier="median-dummy/1",
    )

    assert first == second
    assert source_rows == original


def test_result_structures_are_immutable() -> None:
    result = run_evaluation(MedianDummyRegressor())

    with pytest.raises(FrozenInstanceError):
        result.model_identifier = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.predictions[0].predicted_target = 99.0  # type: ignore[misc]
    assert type(result.predictions) is tuple


def test_result_rejects_metrics_inconsistent_with_predictions() -> None:
    result = run_evaluation(MedianDummyRegressor())
    inconsistent_metrics = RegressionMetrics(
        RegressionMetric(
            "MAE",
            result.metrics.mae.value + 1.0,  # type: ignore[operator]
            "DEFINED",
            None,
            "synthetic units",
        ),
        result.metrics.rmse,
        result.metrics.r2,
    )

    with pytest.raises(RegressionEvaluationError, match="do not match"):
        replace(result, metrics=inconsistent_metrics)


def test_existing_median_baseline_is_backward_compatible_and_accepts_matrix() -> None:
    model = MedianDummyRegressor().fit((1.0, 2.0), (2.0, 4.0))

    assert model.predict((3.0, 4.0)) == (3.0, 3.0)
    assert model.predict(((3.0, 7.0), (4.0, 8.0))) == (3.0, 3.0)
