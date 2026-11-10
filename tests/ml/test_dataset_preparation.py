"""Synthetic tests for reusable task-driven numeric data preparation."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

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
    ExperimentConfigurationError,
    ResearchTask,
    VariableDeclaration,
)
from quantum_space_agi.ml.dataset_preparation import (
    DatasetPreparationError,
    prepare_regression_dataset,
)


def make_dataset(records: list[dict[str, object]]) -> Dataset:
    return Dataset(
        provenance=Provenance(
            dataset_id="synthetic-task-preparation-fixture",
            source=DataSource("synthetic-fixture"),
            retrieved_at=datetime(2026, 11, 10, tzinfo=UTC),
            data_format=DataFormat.JSON,
            metadata={"fixture": "invented-test-data"},
        ),
        records=records,  # type: ignore[arg-type]
    )


def make_schema() -> DataSchema:
    return DataSchema(
        identifier="synthetic-regression-fixture",
        version="1",
        fields=(
            FieldSchema("feature_a", float),
            FieldSchema("feature_b", int),
            FieldSchema("other_feature", int),
            FieldSchema("target", float),
        ),
    )


def make_task(
    features: tuple[str, ...] = ("feature_a",), target: str = "target"
) -> ResearchTask:
    pending = DecisionDeclaration(
        DecisionStatus.PENDING_REVIEW,
        rationale="Synthetic preparation test; approval is not implied.",
    )
    return ResearchTask(
        objective="Prepare synthetic numeric values for a regression task.",
        target=VariableDeclaration(target, None),
        features=tuple(VariableDeclaration(field, None) for field in features),
        inference_description="Synthetic fixture only.",
        decision=pending,
    )


def test_declared_fields_and_multiple_features_are_task_driven() -> None:
    dataset = make_dataset(
        [
            {
                "feature_a": 1.5,
                "feature_b": 2,
                "other_feature": 100,
                "target": 7.0,
            },
            {
                "feature_a": 2.5,
                "feature_b": 3,
                "other_feature": 200,
                "target": 9.0,
            },
        ]
    )

    result = prepare_regression_dataset(
        dataset, make_task(("feature_b", "feature_a")), make_schema()
    )

    assert result.feature_fields == ("feature_b", "feature_a")
    assert result.target_field == "target"
    assert [row.feature_values for row in result.accepted_records] == [
        (2, 1.5),
        (3, 2.5),
    ]
    assert [row.target_value for row in result.accepted_records] == [7.0, 9.0]
    assert result.excluded_rows == ()

    alternate_task = make_task(("feature_b",), "other_feature")
    alternate = prepare_regression_dataset(dataset, alternate_task, make_schema())
    assert alternate.feature_fields == ("feature_b",)
    assert alternate.target_field == "other_feature"
    assert [row.target_value for row in alternate.accepted_records] == [100, 200]


def test_original_source_indices_and_provenance_are_preserved() -> None:
    dataset = make_dataset(
        [
            {"feature_a": 1.0, "target": 2.0},
            {"feature_a": 2.0, "target": None},
            {"feature_a": 3.0, "target": 4.0},
        ]
    )

    result = prepare_regression_dataset(
        dataset,
        make_task(),
        make_schema(),
        source_row_indices=(14, 27, 51),
    )

    assert result.provenance is dataset.provenance
    assert result.input_source_row_indices == (14, 27, 51)
    assert [row.source_row_index for row in result.accepted_records] == [14, 51]
    assert [row.row_index for row in result.excluded_rows] == [27]
    assert result.excluded_rows[0].findings[0].reason_code == "null_value"


@pytest.mark.parametrize(
    ("record", "expected"),
    [
        ({"target": 2}, ("feature_a", "missing_field")),
        ({"feature_a": 1.0}, ("target", "missing_field")),
        ({"feature_a": 1.0, "target": None}, ("target", "null_value")),
        ({"feature_a": "bad", "target": 2.0}, ("feature_a", "non_numeric")),
        ({"feature_a": float("nan"), "target": 2.0}, ("feature_a", "non_finite")),
        ({"feature_a": 1.0, "target": float("inf")}, ("target", "non_finite")),
        ({"feature_a": True, "target": 2.0}, ("feature_a", "non_numeric")),
    ],
)
def test_invalid_numeric_rows_have_explicit_exclusion_reasons(
    record: dict[str, object], expected: tuple[str, str]
) -> None:
    result = prepare_regression_dataset(
        make_dataset([record]), make_task(), make_schema()
    )

    assert result.accepted_records == ()
    assert result.excluded_rows[0].findings[0].field == expected[0]
    assert result.excluded_rows[0].findings[0].reason_code == expected[1]


def test_non_positive_finite_values_are_preserved() -> None:
    result = prepare_regression_dataset(
        make_dataset([{"feature_a": 0.0, "target": -2.0}]),
        make_task(),
        make_schema(),
    )

    assert result.accepted_records[0].feature_values == (0.0,)
    assert result.accepted_records[0].target_value == -2.0
    assert result.excluded_rows == ()


@pytest.mark.parametrize("task", [make_task(("unknown",)), make_task(target="unknown")])
def test_unknown_task_fields_fail_as_structural_errors(task: ResearchTask) -> None:
    with pytest.raises(DatasetPreparationError, match="absent from schema") as error:
        prepare_regression_dataset(
            make_dataset([{"feature_a": 1, "target": 2}]),
            task,
            make_schema(),
        )

    assert error.value.code == "unknown_field"


def test_non_numeric_schema_declaration_fails_structurally() -> None:
    schema = DataSchema(
        "invalid-synthetic-schema",
        "1",
        (FieldSchema("feature_a", str), FieldSchema("target", float)),
    )
    with pytest.raises(DatasetPreparationError, match="int or float schema type"):
        prepare_regression_dataset(
            make_dataset([{"feature_a": 1, "target": 2}]), make_task(), schema
        )


def test_value_inconsistent_with_schema_type_is_excluded_without_coercion() -> None:
    result = prepare_regression_dataset(
        make_dataset([{"feature_a": 1, "target": 2.0}]),
        make_task(),
        make_schema(),
    )

    finding = result.excluded_rows[0].findings[0]
    assert (finding.field, finding.reason_code, finding.original_value) == (
        "feature_a",
        "type_mismatch",
        1,
    )


def test_incomplete_task_and_empty_dataset_fail_clearly() -> None:
    pending = DecisionDeclaration(
        DecisionStatus.PENDING_REVIEW, rationale="Incomplete synthetic declaration."
    )
    incomplete = ResearchTask(None, None, (), None, pending)
    with pytest.raises(
        DatasetPreparationError, match="objective, target, and features"
    ):
        prepare_regression_dataset(
            make_dataset([{"feature_a": 1}]), incomplete, make_schema()
        )
    with pytest.raises(DatasetPreparationError, match="no records"):
        prepare_regression_dataset(make_dataset([]), make_task(), make_schema())


def test_existing_task_contract_rejects_duplicate_or_overlapping_fields() -> None:
    pending = DecisionDeclaration(
        DecisionStatus.PENDING_REVIEW, rationale="Synthetic declaration test."
    )
    with pytest.raises(ExperimentConfigurationError, match="unique"):
        ResearchTask(
            "Duplicate feature declaration.",
            VariableDeclaration("target", None),
            (VariableDeclaration("feature_a", None),) * 2,
            "Synthetic only.",
            pending,
        )
    with pytest.raises(ExperimentConfigurationError, match="cannot also be a feature"):
        ResearchTask(
            "Overlapping feature and target.",
            VariableDeclaration("feature_a", None),
            (VariableDeclaration("feature_a", None),),
            "Synthetic only.",
            pending,
        )


@pytest.mark.parametrize("indices", [(True,), (-1,), (1, 2)])
def test_invalid_source_row_mapping_is_rejected(indices: tuple[object, ...]) -> None:
    dataset = make_dataset([{"feature_a": 1.0, "target": 2.0}])
    with pytest.raises(DatasetPreparationError, match="source_row_indices"):
        prepare_regression_dataset(
            dataset,
            make_task(),
            make_schema(),
            source_row_indices=indices,  # type: ignore[arg-type]
        )


def test_duplicate_source_row_mapping_is_rejected() -> None:
    dataset = make_dataset(
        [
            {"feature_a": 1.0, "target": 2.0},
            {"feature_a": 3.0, "target": 4.0},
        ]
    )
    with pytest.raises(DatasetPreparationError, match="must be unique"):
        prepare_regression_dataset(
            dataset, make_task(), make_schema(), source_row_indices=(8, 8)
        )


def test_all_excluded_rows_are_returned_with_complete_ledger() -> None:
    result = prepare_regression_dataset(
        make_dataset([{"feature_a": None, "target": None}]),
        make_task(),
        make_schema(),
    )

    assert result.accepted_records == ()
    assert result.excluded_rows[0].row_index == 0
    assert [finding.field for finding in result.excluded_rows[0].findings] == [
        "feature_a",
        "target",
    ]


def test_preparation_is_deterministic_immutable_and_does_not_mutate_input() -> None:
    source_records = [
        {"feature_a": 1.5, "target": 3.0, "nested": {"values": [1, 2]}},
        {"feature_a": [], "target": 4.0},
    ]
    original = deepcopy(source_records)
    dataset = make_dataset(source_records)
    task = make_task()

    first = prepare_regression_dataset(dataset, task, make_schema())
    second = prepare_regression_dataset(dataset, task, make_schema())

    assert first == second
    assert source_records == original
    with pytest.raises(FrozenInstanceError):
        first.accepted_records = ()  # type: ignore[misc]
    with pytest.raises(AttributeError):
        first.accepted_records[0].feature_values.append(2)  # type: ignore[attr-defined]
