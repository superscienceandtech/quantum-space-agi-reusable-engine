"""Thin offline orchestration for task-driven regression preparation/evaluation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from quantum_space_agi.data import DataSchema, Dataset
from quantum_space_agi.ml.dataset_preparation import (
    PreparedRegressionDataset,
    PreparedRegressionRecord,
    prepare_regression_dataset,
)
from quantum_space_agi.ml.dataset_validation import ExcludedRow
from quantum_space_agi.ml.experiment_manifest import ResearchTask
from quantum_space_agi.ml.model_evaluation import (
    NumericRegressionModel,
    RegressionEvaluationResult,
    evaluate_regression_model,
)


class RegressionWorkflowError(ValueError):
    """An integrated result does not link preparation and evaluation consistently."""


@dataclass(frozen=True, slots=True)
class RegressionWorkflowResult:
    """Preparation ledger and evaluation result with validated row linkage."""

    prepared_dataset: PreparedRegressionDataset
    evaluation: RegressionEvaluationResult

    def __post_init__(self) -> None:
        if type(self.prepared_dataset) is not PreparedRegressionDataset:
            raise RegressionWorkflowError(
                "prepared_dataset must be PreparedRegressionDataset"
            )
        if type(self.evaluation) is not RegressionEvaluationResult:
            raise RegressionWorkflowError(
                "evaluation must be RegressionEvaluationResult"
            )

        prepared = self.prepared_dataset
        evaluation = self.evaluation
        if (
            evaluation.task != prepared.task
            or evaluation.feature_fields != prepared.feature_fields
            or evaluation.target_field != prepared.target_field
            or evaluation.schema_id != prepared.schema_id
            or evaluation.schema_version != prepared.schema_version
            or evaluation.provenance != prepared.provenance
        ):
            raise RegressionWorkflowError(
                "evaluation metadata does not match prepared dataset"
            )

        accepted = {row.source_row_index: row for row in prepared.accepted_records}
        partitions = (
            *evaluation.training_source_row_indices,
            *evaluation.evaluation_source_row_indices,
        )
        if any(index not in accepted for index in partitions):
            raise RegressionWorkflowError(
                "partition identities must refer to mechanically accepted rows"
            )
        if tuple(item.source_row_index for item in evaluation.predictions) != (
            evaluation.evaluation_source_row_indices
        ):
            raise RegressionWorkflowError(
                "predictions do not align with evaluation source-row identities"
            )
        if any(
            prediction.observed_target
            != accepted[prediction.source_row_index].target_value
            for prediction in evaluation.predictions
        ):
            raise RegressionWorkflowError(
                "observed targets do not match prepared source rows"
            )

    @property
    def task(self) -> ResearchTask:
        """The caller-declared task carried through preparation and evaluation."""
        return self.prepared_dataset.task

    @property
    def training_source_row_indices(self) -> tuple[int, ...]:
        """Explicit training source-row identities."""
        return self.evaluation.training_source_row_indices

    @property
    def evaluation_source_row_indices(self) -> tuple[int, ...]:
        """Explicit evaluation source-row identities in prediction order."""
        return self.evaluation.evaluation_source_row_indices

    @property
    def accepted_records(self) -> tuple[PreparedRegressionRecord, ...]:
        """Prepared records accepted by mechanical feature/target validation."""
        return self.prepared_dataset.accepted_records

    @property
    def excluded_rows(self) -> tuple[ExcludedRow, ...]:
        """Original source-row exclusion ledger from data preparation."""
        return self.prepared_dataset.excluded_rows


def prepare_and_evaluate_regression(
    dataset: Dataset,
    task: ResearchTask,
    schema: DataSchema,
    *,
    training_source_row_indices: Sequence[int],
    evaluation_source_row_indices: Sequence[int],
    model: NumericRegressionModel,
    model_identifier: str,
    source_row_indices: Sequence[int] | None = None,
) -> RegressionWorkflowResult:
    """Prepare an existing Dataset then evaluate on explicit caller partitions.

    This function performs no I/O and creates no split. Preparation and
    evaluation validation errors retain their original exception types/codes.
    ``source_row_indices`` maps Dataset positions to upstream source positions.
    """
    prepared = prepare_regression_dataset(
        dataset, task, schema, source_row_indices=source_row_indices
    )
    evaluation = evaluate_regression_model(
        prepared,
        training_source_row_indices=training_source_row_indices,
        evaluation_source_row_indices=evaluation_source_row_indices,
        model=model,
        model_identifier=model_identifier,
    )
    return RegressionWorkflowResult(prepared, evaluation)
