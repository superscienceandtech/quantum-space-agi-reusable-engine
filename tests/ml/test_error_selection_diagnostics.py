"""Synthetic-only residual, uncertainty metadata, and selection diagnostics."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace

import pytest

from quantum_space_agi.ml.dataset_validation import validate_baseline_records
from quantum_space_agi.ml.error_selection_diagnostics import (
    ERROR_DIAGNOSTICS_SCHEMA_VERSION,
    ErrorDiagnosticsError,
    UncertaintyFieldSpec,
    UncertaintyRole,
    _error_summary,
    _linear_quantile,
    create_synthetic_error_diagnostic_fixture,
    diagnose_error_selection,
    serialize_error_selection_diagnostics,
)
from quantum_space_agi.ml.leakage_diagnostics import ExperimentManifestLinkage
from quantum_space_agi.ml.synthetic_baseline import (
    run_synthetic_baseline,
)

UNCERTAINTY_SPECS = (
    UncertaintyFieldSpec(
        "synthetic_mass_lower_uncertainty", UncertaintyRole.LOWER_UNCERTAINTY
    ),
    UncertaintyFieldSpec(
        "synthetic_mass_upper_uncertainty", UncertaintyRole.UPPER_UNCERTAINTY
    ),
    UncertaintyFieldSpec(
        "synthetic_radius_lower_uncertainty", UncertaintyRole.LOWER_UNCERTAINTY
    ),
    UncertaintyFieldSpec(
        "synthetic_radius_upper_uncertainty", UncertaintyRole.UPPER_UNCERTAINTY
    ),
    UncertaintyFieldSpec(
        "synthetic_interval_lower_bound",
        UncertaintyRole.LOWER_BOUND,
        "synthetic-interval",
    ),
    UncertaintyFieldSpec(
        "synthetic_interval_upper_bound",
        UncertaintyRole.UPPER_BOUND,
        "synthetic-interval",
    ),
    UncertaintyFieldSpec("synthetic_uncertainty_note", UncertaintyRole.METADATA),
)


def make_diagnostic():
    rows = create_synthetic_error_diagnostic_fixture()
    validation = validate_baseline_records(rows)  # type: ignore[arg-type]
    baseline = run_synthetic_baseline()
    linkage = ExperimentManifestLinkage(
        "arc08-synthetic-mass-radius-smoke-test-v1",
        baseline.configuration_sha256,
        baseline.manifest_sha256,
        "arc08-experiment-manifest/1",
    )
    report = diagnose_error_selection(
        rows,
        validation,
        baseline.test_row_ids,
        baseline.predictions,
        experiment_id=linkage.experiment_id,
        fixture_id="arc08-synthetic-error-diagnostic-fixture/1",
        group_fields=("synthetic_host_group", "synthetic_category"),
        uncertainty_fields=UNCERTAINTY_SPECS,
        manifest_linkage=linkage,
    )
    return rows, validation, baseline, report


def test_residual_convention_and_prediction_to_row_alignment() -> None:
    _, _, baseline, report = make_diagnostic()

    assert report.residual_convention == "observed_target - predicted_target"
    assert (
        tuple(item.row_id for item in report.residual_records) == baseline.test_row_ids
    )
    for residual, prediction in zip(
        report.residual_records, baseline.predictions, strict=True
    ):
        expected = prediction.observed_target - prediction.predicted_target
        assert residual.row_id == prediction.row_id
        assert residual.observed_target == prediction.observed_target
        assert residual.predicted_target == prediction.predicted_target
        assert residual.residual == expected
        assert residual.absolute_error == abs(expected)
        assert residual.squared_error == expected**2


def test_error_metrics_and_documented_linear_quantiles() -> None:
    summary = _error_summary((1.0, 2.0, 3.0, 4.0))

    assert summary.mae == 2.5
    assert summary.rmse == pytest.approx((30 / 4) ** 0.5)
    assert summary.mean_signed_residual == 2.5
    assert summary.median_signed_residual == 2.5
    assert summary.median_absolute_error == 2.5
    assert summary.minimum_residual == 1.0
    assert summary.maximum_residual == 4.0
    assert _linear_quantile((1.0, 2.0, 3.0, 4.0), 0.25) == 1.75
    assert _linear_quantile((1.0, 2.0, 3.0, 4.0), 0.75) == 3.25
    assert tuple(item.probability for item in summary.quantiles) == (
        0.05,
        0.25,
        0.5,
        0.75,
        0.95,
    )


def test_empty_single_and_small_sample_statuses_are_explicit() -> None:
    empty = _error_summary(())
    single = _error_summary((-2.0,))

    assert empty.status == "UNDEFINED_EMPTY_SAMPLE"
    assert empty.row_count == 0
    assert empty.mae is None and empty.rmse is None and empty.quantiles == ()
    assert single.status == "DEFINED_SINGLE_ROW"
    assert single.mae == 2.0
    assert single.rmse == 2.0
    assert single.minimum_residual == single.maximum_residual == -2.0


def test_empty_held_out_sample_returns_explicit_undefined_summary() -> None:
    rows = create_synthetic_error_diagnostic_fixture()
    validation = validate_baseline_records(rows)  # type: ignore[arg-type]
    report = diagnose_error_selection(
        rows,
        validation,
        (),
        (),
        experiment_id="synthetic-empty-test",
        fixture_id="synthetic-empty-fixture/1",
    )

    assert report.aggregate_errors.status == "UNDEFINED_EMPTY_SAMPLE"
    assert report.aggregate_errors.mae is None
    assert report.residual_records == ()


@pytest.mark.parametrize(
    ("ids", "predictions", "message"),
    (
        ("missing", "normal", "match test IDs exactly"),
        ("duplicate", "normal", "test row identifiers must be unique"),
        ("extra", "normal", "match test IDs exactly"),
        ("normal", "duplicate", "prediction row identifiers must be unique"),
    ),
)
def test_missing_duplicate_and_extra_prediction_ids_are_rejected(
    ids: str, predictions: str, message: str
) -> None:
    rows, validation, baseline, _ = make_diagnostic()
    test_ids = baseline.test_row_ids
    prediction_records = baseline.predictions
    if ids == "missing":
        prediction_records = prediction_records[:-1]
    elif ids == "duplicate":
        test_ids = (*test_ids[:-1], test_ids[0])
    elif ids == "extra":
        prediction_records = (
            *prediction_records,
            replace(prediction_records[0], row_id="extra"),
        )
    elif predictions == "duplicate":
        prediction_records = (*prediction_records, prediction_records[0])

    with pytest.raises(ErrorDiagnosticsError, match=message):
        diagnose_error_selection(
            rows,
            validation,
            test_ids,
            prediction_records,
            experiment_id="synthetic-test",
            fixture_id="synthetic-fixture/1",
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("predicted_target", float("nan"), "finite"),
        ("predicted_target", float("inf"), "finite"),
        ("observed_target", True, "integer or float"),
        ("feature_value", -float("inf"), "finite"),
    ),
)
def test_non_finite_or_non_numeric_prediction_values_are_rejected(
    field: str, value: object, message: str
) -> None:
    rows, validation, baseline, _ = make_diagnostic()
    predictions = (
        replace(baseline.predictions[0], **{field: value}),
        *baseline.predictions[1:],
    )

    with pytest.raises(ErrorDiagnosticsError, match=message):
        diagnose_error_selection(
            rows,
            validation,
            baseline.test_row_ids,
            predictions,
            experiment_id="synthetic-test",
            fixture_id="synthetic-fixture/1",
        )


def test_prediction_values_must_match_source_row() -> None:
    rows, validation, baseline, _ = make_diagnostic()
    predictions = (
        replace(baseline.predictions[0], observed_target=999.0),
        *baseline.predictions[1:],
    )

    with pytest.raises(ErrorDiagnosticsError, match="do not match source row"):
        diagnose_error_selection(
            rows,
            validation,
            baseline.test_row_ids,
            predictions,
            experiment_id="synthetic-test",
            fixture_id="synthetic-fixture/1",
        )


def test_group_metrics_preserve_values_and_report_missing_metadata() -> None:
    rows, validation, baseline, _ = make_diagnostic()
    missing_id = baseline.test_row_ids[0]
    source_row = next(row for row in rows if row["synthetic_row_id"] == missing_id)
    source_row["synthetic_category"] = None
    report = diagnose_error_selection(
        rows,
        validation,
        baseline.test_row_ids,
        baseline.predictions,
        experiment_id="synthetic-test",
        fixture_id="synthetic-fixture/1",
        group_fields=("synthetic_host_group", "synthetic_category"),
    )

    assert any(
        item.row_count > 0 and item.mae is not None for item in report.group_errors
    )
    assert len(report.missing_group_values) == 1
    assert report.missing_group_values[0].field == "synthetic_category"
    assert report.missing_group_values[0].row_id == missing_id
    assert report.missing_group_values[0].reason == "missing"


def test_uncertainty_fields_preserve_asymmetric_values_and_validate_coverage() -> None:
    rows, _, _, report = make_diagnostic()
    diagnostics = {item.field: item for item in report.uncertainty_fields}

    lower = diagnostics["synthetic_mass_lower_uncertainty"]
    upper = diagnostics["synthetic_mass_upper_uncertainty"]
    assert lower.role is UncertaintyRole.LOWER_UNCERTAINTY
    assert upper.role is UncertaintyRole.UPPER_UNCERTAINTY
    row_id = rows[0]["synthetic_row_id"]
    lower_value = next(item.value for item in lower.values if item.row_id == row_id)
    upper_value = next(item.value for item in upper.values if item.row_id == row_id)
    assert lower_value == 0.2
    assert upper_value == 0.5
    assert lower_value != upper_value
    assert lower.missing_row_ids == ("synthetic-row-001",)
    assert upper.invalid_numeric_row_ids == ("synthetic-row-002",)
    assert upper.values[2].value == "invalid numeric metadata"
    assert upper.values[2].value_omitted is False

    radius_lower = diagnostics["synthetic_radius_lower_uncertainty"]
    assert "synthetic-row-004" in radius_lower.invalid_numeric_row_ids
    radius_upper = diagnostics["synthetic_radius_upper_uncertainty"]
    assert "synthetic-row-005" in radius_upper.invalid_numeric_row_ids
    assert diagnostics["synthetic_uncertainty_note"].missing_row_ids == tuple(
        f"synthetic-row-{index:03}" for index in range(14)
    )


def test_declared_bounds_report_inconsistent_rows_without_repair() -> None:
    _, _, _, report = make_diagnostic()
    lower = next(
        item
        for item in report.uncertainty_fields
        if item.field == "synthetic_interval_lower_bound"
    )
    upper = next(
        item
        for item in report.uncertainty_fields
        if item.field == "synthetic_interval_upper_bound"
    )

    assert lower.inconsistent_bound_row_ids == ("synthetic-row-003",)
    assert upper.inconsistent_bound_row_ids == ("synthetic-row-003",)


def test_uncertainty_schema_requires_explicit_bound_pair_ids() -> None:
    with pytest.raises(ErrorDiagnosticsError, match="explicit pair_id"):
        UncertaintyFieldSpec("lower", UncertaintyRole.LOWER_BOUND)


def test_selection_diagnostics_reuse_exclusion_ledger_and_report_coverage() -> None:
    _, _, _, report = make_diagnostic()
    selection = report.selection
    coverage = {
        (item.population, item.field): item
        for item in selection.feature_target_coverage
    }

    assert selection.input_row_count == 14
    assert selection.mechanically_accepted_row_count == 12
    assert selection.excluded_row_count == 2
    assert dict(selection.exclusions_by_reason) == {"non_finite": 1, "null_value": 1}
    assert coverage[("all_input_rows", "pl_rade")].missing_count == 1
    assert coverage[("all_input_rows", "pl_bmasse")].non_finite_count == 1
    assert (
        coverage[("mechanically_accepted_rows", "pl_rade")].finite_numeric_count == 12
    )
    assert selection.feature_distribution_in_accepted_rows.value_count == 12
    assert selection.feature_distribution_in_excluded_rows.value_count == 1
    assert selection.scientific_eligibility_status == "NOT_ASSESSED"
    assert selection.cohort_selection_status == "NOT_ASSESSED"
    assert selection.sampling_bias_status == "NOT_ESTABLISHED_FROM_SYNTHETIC_DATA"


def test_manifest_linkage_is_declarative_and_policies_remain_pending() -> None:
    _, _, baseline, report = make_diagnostic()
    document = json.loads(serialize_error_selection_diagnostics(report))
    configuration = json.loads(baseline.configuration_bytes)

    assert report.scientific_policy_status == "PENDING_REVIEW"
    assert all(
        item["decision"]["status"] == "PENDING_REVIEW"
        for item in configuration["policies"]
    )
    assert document["manifest_linkage"]["manifest_sha256"] == baseline.manifest_sha256
    assert "not authenticated" in document["manifest_linkage"]["integrity_note"]


def test_serialization_is_deterministic_utf8_and_report_is_immutable() -> None:
    *_, report = make_diagnostic()
    serialized = serialize_error_selection_diagnostics(report)
    document = json.loads(serialized.decode("utf-8"))

    assert serialized == serialize_error_selection_diagnostics(make_diagnostic()[3])
    assert not serialized.startswith(b"\xef\xbb\xbf")
    assert document["schema_version"] == ERROR_DIAGNOSTICS_SCHEMA_VERSION
    assert document["residual_convention"] == "observed_target - predicted_target"
    with pytest.raises(FrozenInstanceError):
        report.residual_convention = "changed"  # type: ignore[misc]


def test_diagnostics_do_not_mutate_input_rows_or_validation_ledger() -> None:
    rows = create_synthetic_error_diagnostic_fixture()
    original_rows = deepcopy(rows)
    validation = validate_baseline_records(rows)  # type: ignore[arg-type]
    original_validation = validation
    baseline = run_synthetic_baseline()

    diagnose_error_selection(
        rows,
        validation,
        baseline.test_row_ids,
        baseline.predictions,
        experiment_id="synthetic-immutability-check",
        fixture_id="synthetic-error-fixture/1",
        group_fields=("synthetic_category",),
        uncertainty_fields=UNCERTAINTY_SPECS,
    )

    assert rows == original_rows
    assert validation is original_validation
    assert validation.valid_record_indices == tuple(range(12))
