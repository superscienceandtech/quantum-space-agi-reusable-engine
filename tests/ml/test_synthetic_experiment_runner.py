"""Synthetic-only end-to-end experiment runner tests."""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import replace
from statistics import median

import pytest

from quantum_space_agi.ml import synthetic_experiment_runner as runner
from quantum_space_agi.ml.acquisition_readiness import AcquisitionReadinessStatus
from quantum_space_agi.ml.synthetic_baseline import (
    SyntheticBaselineError,
    run_synthetic_baseline,
)


def _payload_map(bundle: runner.SyntheticEvidenceBundle) -> dict[str, bytes]:
    return {item.name: item.payload_bytes for item in bundle.payloads}


def _decoded_document(bundle: runner.SyntheticEvidenceBundle) -> dict[str, object]:
    return json.loads(runner.serialize_synthetic_evidence_bundle(bundle))


def test_end_to_end_synthetic_execution_preserves_ledger_and_diagnostics() -> None:
    bundle = runner.run_synthetic_experiment(experiment_id="offline-run-01", seed=37)
    payloads = _payload_map(bundle)
    validation = json.loads(payloads["validation_report.json"])
    exclusions = json.loads(payloads["exclusion_ledger.json"])
    split = json.loads(payloads["split.json"])
    leakage = json.loads(payloads["leakage_diagnostics.json"])
    diagnostics = json.loads(payloads["error_selection_diagnostics.json"])

    assert bundle.execution_status == "SUCCESSFUL_SYNTHETIC_EXECUTION"
    assert bundle.experiment_id == "offline-run-01"
    assert bundle.seed == 37
    assert validation["input_row_count"] == 14
    assert validation["mechanically_accepted_source_row_indices"] == list(range(12))
    assert validation["excluded_row_count"] == 2
    assert len(exclusions) == 2
    assert all(item["findings"] for item in exclusions)
    assert split["assignment_status"] == "ASSIGNMENTS_EXIST_FOR_SYNTHETIC_SMOKE_TEST"
    assert leakage["split_integrity"]["status"] == "PASS"
    assert leakage["prediction_alignment"]["status"] == "PASS"
    assert diagnostics["scientific_policy_status"] == "PENDING_REVIEW"
    assert diagnostics["selection"]["scientific_eligibility_status"] == "NOT_ASSESSED"
    assert bundle.scientific_acceptance_status == "PENDING_REVIEW"
    assert bundle.acquisition_readiness_status is AcquisitionReadinessStatus.NOT_READY


def test_bundle_payload_hashes_are_for_exact_bytes_and_all_are_synthetic() -> None:
    bundle = runner.run_synthetic_experiment(experiment_id="integrity-run", seed=8)

    assert len(bundle.payloads) >= 10
    serialized_payloads = {
        item["name"]: item for item in _decoded_document(bundle)["payloads"]
    }
    for payload in bundle.payloads:
        assert payload.byte_length == len(payload.payload_bytes)
        assert payload.sha256 == hashlib.sha256(payload.payload_bytes).hexdigest()
        assert payload.synthetic_designation == "synthetic-only; not NASA evidence"
        encoded = serialized_payloads[payload.name]["payload_base64"]
        assert base64.b64decode(encoded, validate=True) == payload.payload_bytes


def test_model_fit_uses_training_targets_only_and_predictions_align_to_test_ids() -> (
    None
):
    bundle = runner.run_synthetic_experiment(experiment_id="model-run", seed=1729)
    payloads = _payload_map(bundle)
    split = json.loads(payloads["split.json"])
    model = json.loads(payloads["model.json"])
    predictions = json.loads(payloads["predictions.json"])

    training_targets = model["training_targets"]
    assert model["configuration"]["fitted_value"] == median(training_targets)
    assert [item["row_id"] for item in predictions] == split["test_row_ids"]
    assert not set(split["train_row_ids"]).intersection(split["test_row_ids"])


def test_manifest_linkage_and_scientific_decisions_remain_pending() -> None:
    bundle = runner.run_synthetic_experiment(experiment_id="manifest-run", seed=9)
    payloads = _payload_map(bundle)
    configuration_name = "synthetic-output/arc08-experiment-configuration.json"
    manifest_name = "synthetic-output/arc08-experiment-manifest.json"
    configuration = json.loads(payloads[configuration_name])
    manifest = json.loads(payloads[manifest_name])

    assert configuration["experiment_id"] == manifest["experiment_id"] == "manifest-run"
    assert (
        manifest["configuration_sha256"]
        == hashlib.sha256(payloads[configuration_name]).hexdigest()
    )
    assert all(
        policy["decision"]["status"] == "PENDING_REVIEW"
        for policy in configuration["policies"]
    )
    assert configuration["research_task"]["decision"]["status"] == "PENDING_REVIEW"


def test_serialization_is_deterministic_without_implicit_timestamps() -> None:
    first = runner.run_synthetic_experiment(experiment_id="repeat-run", seed=15)
    second = runner.run_synthetic_experiment(experiment_id="repeat-run", seed=15)

    first_bytes = runner.serialize_synthetic_evidence_bundle(first)
    assert first_bytes == runner.serialize_synthetic_evidence_bundle(second)
    document = json.loads(first_bytes)
    assert "timestamp" not in document
    assert not first_bytes.startswith(b"\xef\xbb\xbf")
    assert document["schema_version"] == runner.SYNTHETIC_EVIDENCE_BUNDLE_SCHEMA_VERSION


def test_bundle_is_immutable_and_rejects_mutable_payload_collection() -> None:
    bundle = runner.run_synthetic_experiment(experiment_id="immutable-run", seed=2)

    with pytest.raises(ValueError, match="immutable tuple"):
        replace(bundle, payloads=list(bundle.payloads))  # type: ignore[arg-type]


def test_bundle_rejects_noncanonical_readiness_vocabulary() -> None:
    bundle = runner.run_synthetic_experiment(experiment_id="status-run", seed=2)

    with pytest.raises(ValueError, match="readiness status"):
        replace(bundle, acquisition_readiness_status="READY")  # type: ignore[arg-type]


def test_baseline_failure_returns_failed_stage_not_success_bundle(monkeypatch) -> None:
    def fail(**kwargs):
        raise SyntheticBaselineError("synthetic validation failed")

    monkeypatch.setattr(runner, "run_synthetic_baseline", fail)
    with pytest.raises(runner.SyntheticExperimentError) as error:
        runner.run_synthetic_experiment(experiment_id="failed-run", seed=4)

    assert error.value.execution_status == "FAILED"
    assert error.value.stage == "baseline_validation_split_fit"


def test_split_integrity_failure_does_not_return_bundle(monkeypatch) -> None:
    original = runner.diagnose_split_integrity

    def fail_integrity(*args, **kwargs):
        report = original(*args, **kwargs)
        broken = replace(report.split_integrity, status="FAIL")
        return replace(report, split_integrity=broken)

    monkeypatch.setattr(runner, "diagnose_split_integrity", fail_integrity)
    with pytest.raises(
        runner.SyntheticExperimentError, match="split_integrity_diagnostics"
    ):
        runner.run_synthetic_experiment(experiment_id="bad-split-run", seed=5)


def test_prediction_id_mismatch_fails_before_bundle_creation(monkeypatch) -> None:
    original = runner.run_synthetic_baseline

    def mismatched(**kwargs):
        result = original(**kwargs)
        prediction = replace(result.predictions[0], row_id="unknown-synthetic-row")
        return replace(result, predictions=(prediction, *result.predictions[1:]))

    monkeypatch.setattr(runner, "run_synthetic_baseline", mismatched)
    with pytest.raises(
        runner.SyntheticExperimentError, match="baseline_validation_split_fit"
    ):
        runner.run_synthetic_experiment(experiment_id="bad-prediction-run", seed=6)


def test_diagnostic_failure_does_not_return_partial_success(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise ValueError("injected diagnostic failure")

    monkeypatch.setattr(runner, "diagnose_error_selection", fail)
    with pytest.raises(runner.SyntheticExperimentError) as error:
        runner.run_synthetic_experiment(experiment_id="bad-diagnostic-run", seed=7)

    assert error.value.execution_status == "FAILED"
    assert error.value.stage == "error_selection_diagnostics"


def test_manifest_digest_inconsistency_fails_closed(monkeypatch) -> None:
    original = runner.run_synthetic_baseline

    def bad_manifest(**kwargs):
        return replace(original(**kwargs), manifest_sha256="0" * 64)

    monkeypatch.setattr(runner, "run_synthetic_baseline", bad_manifest)
    with pytest.raises(runner.SyntheticExperimentError, match="manifest_linkage"):
        runner.run_synthetic_experiment(experiment_id="bad-manifest-run", seed=10)


@pytest.mark.parametrize("seed", [True, -1, 2.5])
def test_invalid_explicit_seeds_are_rejected(seed: object) -> None:
    with pytest.raises(runner.SyntheticExperimentError, match="seed"):
        runner.run_synthetic_experiment(experiment_id="invalid-seed", seed=seed)  # type: ignore[arg-type]


def test_explicit_experiment_id_is_written_by_existing_baseline_manifest_api() -> None:
    result = run_synthetic_baseline(seed=17, experiment_id="caller-selected-id")
    report = json.loads(result.result_bytes)
    configuration = json.loads(result.configuration_bytes)
    manifest = json.loads(result.manifest_bytes)

    assert report["experiment"]["experiment_id"] == "caller-selected-id"
    assert configuration["experiment_id"] == "caller-selected-id"
    assert manifest["experiment_id"] == "caller-selected-id"
