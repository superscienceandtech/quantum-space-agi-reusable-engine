"""Synthetic end-to-end tests for preparation and explicit evaluation."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
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
    RegressionEvaluationError,
    ResearchTask,
    VariableDeclaration,
    prepare_and_evaluate_regression,
)
from quantum_space_agi.ml.dataset_preparation import (
    PreparedRegressionDataset,
    prepare_regression_dataset,
)
from quantum_space_agi.ml.regression_workflow import (
    RegressionWorkflowError,
    RegressionWorkflowResult,
)
from quantum_space_agi.ml.synthetic_baseline import MedianDummyRegressor


def fixture():
    rows = [
        {"x": 1.0, "y": 2.0},
        {"x": 2.0, "y": 4.0},
        {"x": 3.0, "y": 6.0},
        {"x": None, "y": 8.0},
        {"x": 5.0, "y": float("nan")},
    ]
    dataset = Dataset(
        provenance=Provenance(
            dataset_id="synthetic-workflow-fixture",
            source=DataSource("synthetic-workflow-test"),
            retrieved_at=datetime(2026, 11, 10, tzinfo=UTC),
            data_format=DataFormat.JSON,
        ),
        records=rows,  # type: ignore[arg-type]
    )
    task = ResearchTask(
        objective="Predict an invented synthetic value.",
        target=VariableDeclaration("y", "synthetic units"),
        features=(VariableDeclaration("x", "synthetic units"),),
        inference_description="Synthetic fixture only.",
        decision=DecisionDeclaration(
            DecisionStatus.PENDING_REVIEW,
            rationale="Synthetic engineering test; no approval implied.",
        ),
    )
    schema = DataSchema(
        "synthetic-workflow-schema",
        "1",
        (FieldSchema("x", float), FieldSchema("y", float)),
    )
    source_row_indices = (101, 205, 309, 412, 518)
    return rows, dataset, task, schema, source_row_indices


class InspectingMedianModel:
    def __init__(self) -> None:
        self.fit_targets: tuple[int | float, ...] | None = None
        self.fit_features: tuple[tuple[int | float, ...], ...] | None = None

    def fit(
        self,
        feature_rows: tuple[tuple[int | float, ...], ...],
        target_values: tuple[int | float, ...],
    ) -> None:
        self.fit_features = feature_rows
        self.fit_targets = target_values

    def predict(
        self, feature_rows: tuple[tuple[int | float, ...], ...]
    ) -> tuple[float, ...]:
        assert self.fit_targets is not None
        value = float(median(self.fit_targets))
        return (value,) * len(feature_rows)


def run_workflow(model=None):
    _, dataset, task, schema, source_ids = fixture()
    return prepare_and_evaluate_regression(
        dataset,
        task,
        schema,
        source_row_indices=source_ids,
        training_source_row_indices=(101, 205),
        evaluation_source_row_indices=(309,),
        model=model or MedianDummyRegressor(),
        model_identifier="synthetic-median/1",
    )


def test_dataset_preparation_evaluation_preserves_rows_and_exclusion_ledger() -> None:
    result = run_workflow()

    assert result.task.objective == "Predict an invented synthetic value."
    assert result.prepared_dataset.provenance.dataset_id == "synthetic-workflow-fixture"
    assert result.prepared_dataset.input_source_row_indices == (
        101,
        205,
        309,
        412,
        518,
    )
    assert tuple(row.source_row_index for row in result.accepted_records) == (
        101,
        205,
        309,
    )
    assert tuple(row.row_index for row in result.excluded_rows) == (412, 518)
    assert result.excluded_rows[0].findings[0].reason_code == "null_value"
    assert result.excluded_rows[1].findings[0].reason_code == "non_finite"
    assert result.training_source_row_indices == (101, 205)
    assert result.evaluation_source_row_indices == (309,)
    prediction = result.evaluation.predictions[0]
    assert (prediction.source_row_index, prediction.observed_target) == (309, 6.0)
    assert prediction.predicted_target == 3.0


def test_evaluation_fit_receives_training_rows_only() -> None:
    model = InspectingMedianModel()
    result = run_workflow(model)

    assert model.fit_features == ((1.0,), (2.0,))
    assert model.fit_targets == (2.0, 4.0)
    assert result.evaluation.observed_targets == (6.0,)
    assert 6.0 not in model.fit_targets


def test_preparation_excluded_row_cannot_enter_either_partition() -> None:
    _, dataset, task, schema, source_ids = fixture()

    with pytest.raises(RegressionEvaluationError) as error:
        prepare_and_evaluate_regression(
            dataset,
            task,
            schema,
            source_row_indices=source_ids,
            training_source_row_indices=(101, 412),
            evaluation_source_row_indices=(309,),
            model=MedianDummyRegressor(),
            model_identifier="synthetic-median/1",
        )
    assert error.value.code == "unprepared_identity"


@pytest.mark.parametrize(
    ("training", "evaluation", "error_code"),
    [
        ((101, 205), (205,), "partition_overlap"),
        ((101, 205), (999,), "unknown_identity"),
        ((), (309,), "empty_partition"),
    ],
)
def test_invalid_partitions_propagate_evaluator_errors(
    training: tuple[int, ...], evaluation: tuple[int, ...], error_code: str
) -> None:
    _, dataset, task, schema, source_ids = fixture()

    with pytest.raises(RegressionEvaluationError) as error:
        prepare_and_evaluate_regression(
            dataset,
            task,
            schema,
            source_row_indices=source_ids,
            training_source_row_indices=training,
            evaluation_source_row_indices=evaluation,
            model=MedianDummyRegressor(),
            model_identifier="synthetic-median/1",
        )
    assert error.value.code == error_code


def test_identical_runs_are_deterministic_and_do_not_mutate_dataset_records() -> None:
    rows, _, _, _, _ = fixture()
    original = deepcopy(rows)

    first = run_workflow()
    second = run_workflow()

    assert first == second
    assert rows == original


def test_integrated_result_rejects_mismatched_preparation_metadata() -> None:
    result = run_workflow()
    _, dataset, task, schema, source_ids = fixture()
    other_preparation: PreparedRegressionDataset = prepare_regression_dataset(
        dataset, task, schema, source_row_indices=source_ids
    )
    altered = replace(other_preparation, schema_version="different")

    with pytest.raises(RegressionWorkflowError, match="metadata"):
        RegressionWorkflowResult(altered, result.evaluation)


def test_standalone_prompt_9_and_prompt_10_apis_remain_unchanged() -> None:
    _, dataset, task, schema, source_ids = fixture()
    prepared = prepare_regression_dataset(
        dataset, task, schema, source_row_indices=source_ids
    )
    standalone = run_workflow().evaluation
    assert prepared.accepted_records[0].source_row_index == 101
    assert standalone.evaluation_source_row_indices == (309,)
