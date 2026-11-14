"""Synthetic-only regression smoke tests; no archive data or network access."""

from __future__ import annotations

import hashlib
import json
import math
from statistics import median

import pytest

from quantum_space_agi.ml.dataset_validation import validate_baseline_records
from quantum_space_agi.ml.synthetic_baseline import (
    DEFAULT_RANDOM_SEED,
    SYNTHETIC_BASELINE_SCHEMA_VERSION,
    SYNTHETIC_FIXTURE_ID,
    MedianDummyRegressor,
    SyntheticBaselineError,
    _calculate_metrics,
    create_synthetic_regression_fixture,
    run_synthetic_baseline,
)


def test_fixture_has_stable_synthetic_ids_and_validation_cases() -> None:
    first = create_synthetic_regression_fixture()
    second = create_synthetic_regression_fixture()

    assert len(first) == 14
    assert [row["synthetic_row_id"] for row in first] == [
        f"synthetic-row-{index:03d}" for index in range(14)
    ]
    assert all(row["synthetic_fixture_id"] == SYNTHETIC_FIXTURE_ID for row in first)
    assert first[:13] == second[:13]
    assert math.isnan(first[13]["pl_bmasse"])


def test_existing_validator_reports_missing_and_non_finite_synthetic_rows() -> None:
    report = validate_baseline_records(create_synthetic_regression_fixture())  # type: ignore[arg-type]

    assert report.record_count == 14
    assert len(report.valid_record_indices) == 12
    assert [row.row_index for row in report.excluded_rows] == [12, 13]
    assert [row.findings[0].reason_code for row in report.excluded_rows] == [
        "null_value",
        "non_finite",
    ]


def test_existing_validator_reports_missing_required_target_column() -> None:
    records = [dict(create_synthetic_regression_fixture()[0])]
    del records[0]["pl_bmasse"]

    report = validate_baseline_records(records)  # type: ignore[arg-type]

    assert report.valid_record_indices == ()
    assert report.excluded_rows[0].findings[0].reason_code == "missing_field"
    assert report.excluded_rows[0].findings[0].field == "pl_bmasse"


def test_seeded_split_is_deterministic_disjoint_and_traceable() -> None:
    first = run_synthetic_baseline()
    second = run_synthetic_baseline()
    report = json.loads(first.result_bytes)

    assert first.train_row_ids == second.train_row_ids
    assert first.test_row_ids == second.test_row_ids
    assert first.result_bytes == second.result_bytes
    assert len(first.train_row_ids) == 9
    assert len(first.test_row_ids) == 3
    assert not set(first.train_row_ids).intersection(first.test_row_ids)
    assert set(first.train_row_ids).union(first.test_row_ids) == {
        f"synthetic-row-{index:03d}" for index in range(12)
    }
    assert report["experiment"]["seed"] == DEFAULT_RANDOM_SEED
    assert report["experiment"]["split"]["strategy"].startswith("seeded random row")
    assert report["experiment"]["split"]["effective_test_fraction"] == 0.25


def test_baseline_is_fit_to_training_targets_only() -> None:
    run = run_synthetic_baseline()
    report = json.loads(run.result_bytes)
    training_targets = report["experiment"]["model"]["training_targets"]
    held_out_targets = [item.observed_target for item in run.predictions]

    assert report["experiment"]["model"]["configuration"]["fitted_value"] == median(
        training_targets
    )
    assert report["experiment"]["model"]["configuration"]["fitted_value"] != median(
        [*training_targets, *held_out_targets]
    )
    assert {prediction.predicted_target for prediction in run.predictions} == {
        median(training_targets)
    }


def test_prediction_rows_match_held_out_identifiers_and_metrics() -> None:
    result = run_synthetic_baseline()
    report = json.loads(result.result_bytes)
    serialized_predictions = report["predictions"]

    assert (
        tuple(item["row_id"] for item in serialized_predictions) == result.test_row_ids
    )
    assert tuple(item.row_id for item in result.predictions) == result.test_row_ids
    observed = tuple(item.observed_target for item in result.predictions)
    predicted = tuple(item.predicted_target for item in result.predictions)
    expected_mae = sum(
        abs(left - right) for left, right in zip(observed, predicted)
    ) / len(observed)
    expected_rmse = math.sqrt(
        sum((left - right) ** 2 for left, right in zip(observed, predicted))
        / len(observed)
    )
    assert result.metrics.mae == expected_mae
    assert result.metrics.rmse == expected_rmse
    assert result.metrics.r2 is not None
    assert report["metrics"]["primary"]["unit"] == "synthetic target units"
    assert report["metrics"]["threshold"] is None


def test_undefined_r2_is_reported_without_failing_other_metrics() -> None:
    metrics = _calculate_metrics((3.0,), (2.0,))

    assert metrics.mae == 1.0
    assert metrics.rmse == 1.0
    assert metrics.r2 is None
    assert metrics.r2_status == "undefined: fewer than two test rows"


def test_constant_held_out_targets_have_undefined_r2() -> None:
    metrics = _calculate_metrics((3.0, 3.0), (2.0, 4.0))

    assert metrics.mae == 1.0
    assert metrics.rmse == 1.0
    assert metrics.r2 is None
    assert metrics.r2_status == "undefined: constant test targets"


def test_result_serialization_is_canonical_and_utf8() -> None:
    result = run_synthetic_baseline()
    parsed = json.loads(result.result_bytes.decode("utf-8"))

    assert result.result_bytes == run_synthetic_baseline().result_bytes
    assert result.result_bytes.startswith(b"{")
    assert not result.result_bytes.startswith(b"\xef\xbb\xbf")
    assert parsed["schema_version"] == SYNTHETIC_BASELINE_SCHEMA_VERSION
    assert parsed["evidence_classification"] == "synthetic software evidence only"


def test_manifest_configuration_linkage_and_pending_scientific_decisions() -> None:
    result = run_synthetic_baseline(seed=23)
    configuration = json.loads(result.configuration_bytes)
    manifest = json.loads(result.manifest_bytes)
    report = json.loads(result.result_bytes)

    assert configuration["experiment_id"] == "arc08-synthetic-mass-radius-smoke-test-v1"
    assert configuration["research_task"]["decision"]["status"] == "PENDING_REVIEW"
    assert all(
        item["decision"]["status"] == "PENDING_REVIEW"
        for item in configuration["policies"]
    )
    assert configuration["identity_and_split"]["decision"]["status"] == "PENDING_REVIEW"
    assert configuration["model_evaluation"]["decision"]["status"] == "PENDING_REVIEW"
    assert manifest["configuration_sha256"] == result.configuration_sha256
    assert (
        result.configuration_sha256
        == hashlib.sha256(result.configuration_bytes).hexdigest()
    )
    assert result.manifest_sha256 == hashlib.sha256(result.manifest_bytes).hexdigest()
    assert report["manifest_linkage"]["manifest_sha256"] == result.manifest_sha256
    assert manifest["source_snapshot_reference"] is None


def test_mechanical_acceptance_is_not_reported_as_scientific_eligibility() -> None:
    result = run_synthetic_baseline()
    report = json.loads(result.result_bytes)

    assert report["validation"]["mechanically_accepted_source_row_indices"] == list(
        result.validation_report.valid_record_indices
    )
    assert report["scientific_acceptance"] == "PENDING_REVIEW"
    assert any("not scientific eligibility" in text for text in report["limitations"])


def test_fixture_and_run_do_not_change_their_returned_source_records() -> None:
    records = create_synthetic_regression_fixture()
    before = [dict(record) for record in records]
    validate_baseline_records(records)  # type: ignore[arg-type]
    run_synthetic_baseline()

    assert all(records[index] == before[index] for index in range(11))
    assert math.isnan(records[13]["pl_bmasse"])
    assert math.isnan(before[13]["pl_bmasse"])


@pytest.mark.parametrize("seed", [True, -1, 1.5])
def test_invalid_seeds_are_rejected(seed: object) -> None:
    with pytest.raises(SyntheticBaselineError, match="seed"):
        run_synthetic_baseline(seed=seed)  # type: ignore[arg-type]


@pytest.mark.parametrize("fraction", [True, 0.0, 1.0, float("nan"), "0.2"])
def test_invalid_test_fractions_are_rejected(fraction: object) -> None:
    with pytest.raises(SyntheticBaselineError, match="test_fraction"):
        run_synthetic_baseline(test_fraction=fraction)  # type: ignore[arg-type]


def test_median_model_rejects_non_finite_training_or_prediction_values() -> None:
    with pytest.raises(SyntheticBaselineError, match="finite numbers"):
        MedianDummyRegressor().fit((1.0,), (float("nan"),))
    with pytest.raises(SyntheticBaselineError, match="finite numbers"):
        MedianDummyRegressor().fit((float("inf"),), (2.0,))
