"""Synthetic-only reproducibility and artifact-integrity audit tests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from quantum_space_agi.ml.acquisition_readiness import AcquisitionReadinessStatus
from quantum_space_agi.ml.reproducibility_audit import (
    AuditStatus,
    MetadataStatus,
    audit_synthetic_evidence_bundle,
    serialize_reproducibility_audit,
)
from quantum_space_agi.ml.synthetic_experiment_runner import (
    SYNTHETIC_EVIDENCE_BUNDLE_SCHEMA_VERSION,
    SyntheticEvidencePayload,
    run_synthetic_experiment,
)


def make_bundle():
    return run_synthetic_experiment(experiment_id="audit-synthetic-01", seed=31)


def payload_by_name(bundle, name: str) -> SyntheticEvidencePayload:
    return next(item for item in bundle.payloads if item.name == name)


def replace_payload(bundle, updated: SyntheticEvidencePayload) -> None:
    object.__setattr__(
        bundle,
        "payloads",
        tuple(
            updated if item.name == updated.name else item for item in bundle.payloads
        ),
    )


def update_json_payload(bundle, name: str, update) -> SyntheticEvidencePayload:
    original = payload_by_name(bundle, name)
    document = json.loads(original.payload_bytes)
    update(document)
    raw = json.dumps(
        document,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    updated = SyntheticEvidencePayload(
        name,
        original.media_type,
        original.synthetic_designation,
        raw,
        len(raw),
        hashlib.sha256(raw).hexdigest(),
    )
    replace_payload(bundle, updated)
    return updated


def test_valid_synthetic_bundle_audits_with_sorted_verified_inventory() -> None:
    report = audit_synthetic_evidence_bundle(make_bundle())

    assert report.audit_status is AuditStatus.VERIFIED
    assert report.integrity_status is AuditStatus.VERIFIED
    assert report.experiment_id == "audit-synthetic-01"
    assert report.fixture_id == "arc08-synthetic-mass-radius-fixture/1"
    assert report.execution_status == "SUCCESSFUL_SYNTHETIC_EXECUTION"
    assert tuple(item.artifact_id for item in report.artifact_inventory) == tuple(
        sorted(item.artifact_id for item in report.artifact_inventory)
    )
    assert all(item.required for item in report.artifact_inventory)
    assert all(
        item.integrity_status == "VERIFIED" for item in report.artifact_inventory
    )
    assert report.acquisition_readiness_status == "NOT_READY"
    assert report.scientific_approval_status == "PENDING_REVIEW"


def test_audit_serialization_is_deterministic_and_utf8() -> None:
    first = serialize_reproducibility_audit(
        audit_synthetic_evidence_bundle(make_bundle())
    )
    second = serialize_reproducibility_audit(
        audit_synthetic_evidence_bundle(make_bundle())
    )

    assert first == second
    assert not first.startswith(b"\xef\xbb\xbf")
    assert json.loads(first)["schema_version"] == "arc08-reproducibility-audit/1"
    assert b"timestamp" not in first
    assert b"random_id" not in first


def test_inventory_recalculates_digest_and_preserves_required_metadata() -> None:
    bundle = make_bundle()
    report = audit_synthetic_evidence_bundle(bundle)
    inventory = {item.artifact_id: item for item in report.artifact_inventory}

    for payload in bundle.payloads:
        item = inventory[payload.name]
        assert item.byte_length == len(payload.payload_bytes)
        assert item.computed_sha256 == hashlib.sha256(payload.payload_bytes).hexdigest()
        assert item.declared_sha256 == item.computed_sha256
        assert item.encoding == "UTF-8"
        assert item.serialization_format == "JSON"
    assert inventory["synthetic-output/arc08-experiment-manifest.json"].references == (
        "synthetic-output/arc08-experiment-configuration.json",
        "synthetic-output/arc08-synthetic-baseline-result.json",
    )
    config = inventory["synthetic-output/arc08-experiment-configuration.json"]
    assert config.artifact_type == "experiment_configuration"
    assert config.schema_version == "arc08-experiment-configuration/1"


@pytest.mark.parametrize("bad_field", ["byte_length", "sha256"])
def test_payload_length_and_checksum_mismatches_fail_audit(bad_field: str) -> None:
    bundle = make_bundle()
    target = payload_by_name(bundle, "predictions.json")
    original_value = getattr(target, bad_field)
    object.__setattr__(
        target,
        bad_field,
        original_value + 1 if bad_field == "byte_length" else "0" * 64,
    )

    report = audit_synthetic_evidence_bundle(bundle)
    codes = {item.code for item in report.findings}

    assert report.audit_status is AuditStatus.FAILED
    assert (
        "BYTE_LENGTH_MISMATCH" in codes
        if bad_field == "byte_length"
        else "SHA256_MISMATCH" in codes
    )
    assert getattr(target, bad_field) == (
        original_value + 1 if bad_field == "byte_length" else "0" * 64
    )


def test_missing_required_artifact_is_reported_without_mutating_bundle() -> None:
    bundle = make_bundle()
    original = bundle.payloads
    object.__setattr__(
        bundle,
        "payloads",
        tuple(item for item in original if item.name != "model.json"),
    )

    report = audit_synthetic_evidence_bundle(bundle)

    assert report.audit_status is AuditStatus.FAILED
    assert any(
        item.code == "MISSING_REQUIRED_ARTIFACT" and item.artifact_id == "model.json"
        for item in report.findings
    )
    assert bundle.payloads == tuple(
        item for item in original if item.name != "model.json"
    )


def test_duplicate_artifact_id_is_reported() -> None:
    bundle = make_bundle()
    object.__setattr__(bundle, "payloads", (*bundle.payloads, bundle.payloads[0]))

    report = audit_synthetic_evidence_bundle(bundle)

    assert report.audit_status is AuditStatus.FAILED
    assert any(item.code == "DUPLICATE_ARTIFACT_ID" for item in report.findings)


def test_conflicting_duplicate_artifact_declarations_are_reported() -> None:
    bundle = make_bundle()
    original = bundle.payloads[0]
    changed_bytes = original.payload_bytes + b" "
    conflict = SyntheticEvidencePayload(
        original.name,
        original.media_type,
        original.synthetic_designation,
        changed_bytes,
        len(changed_bytes),
        hashlib.sha256(changed_bytes).hexdigest(),
    )
    object.__setattr__(bundle, "payloads", (*bundle.payloads, conflict))

    report = audit_synthetic_evidence_bundle(bundle)

    assert any(item.code == "DUPLICATE_ARTIFACT_ID" for item in report.findings)
    assert any(
        item.code == "CONFLICTING_ARTIFACT_DECLARATION" for item in report.findings
    )


def test_unresolved_manifest_reference_is_reported() -> None:
    bundle = make_bundle()
    original = payload_by_name(
        bundle, "synthetic-output/arc08-experiment-manifest.json"
    )
    document = json.loads(original.payload_bytes)
    document["configuration_reference"]["path"] = "outside/not-in-bundle.json"
    raw = json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    updated = SyntheticEvidencePayload(
        original.name,
        original.media_type,
        original.synthetic_designation,
        raw,
        len(raw),
        hashlib.sha256(raw).hexdigest(),
    )
    replace_payload(bundle, updated)

    report = audit_synthetic_evidence_bundle(bundle)

    assert report.audit_status is AuditStatus.FAILED
    assert any(item.code == "UNRESOLVED_PAYLOAD_REFERENCE" for item in report.findings)


def test_manifest_nested_configuration_checksum_is_verified_against_exact_bytes() -> (
    None
):
    bundle = make_bundle()
    manifest_name = "synthetic-output/arc08-experiment-manifest.json"
    baseline_name = "synthetic-output/arc08-synthetic-baseline-result.json"
    updated_manifest = update_json_payload(
        bundle,
        manifest_name,
        lambda document: document["configuration_reference"].update(sha256="0" * 64),
    )
    update_json_payload(
        bundle,
        baseline_name,
        lambda document: document["manifest_linkage"].update(
            manifest_sha256=updated_manifest.sha256
        ),
    )

    report = audit_synthetic_evidence_bundle(bundle)

    assert report.audit_status is AuditStatus.FAILED
    assert any(
        item.code == "MANIFEST_CONFIGURATION_REFERENCE_MISMATCH"
        for item in report.findings
    )


def test_missing_configuration_payload_fails_manifest_linkage_audit() -> None:
    bundle = make_bundle()
    config_name = "synthetic-output/arc08-experiment-configuration.json"
    object.__setattr__(
        bundle,
        "payloads",
        tuple(item for item in bundle.payloads if item.name != config_name),
    )

    report = audit_synthetic_evidence_bundle(bundle)

    assert report.audit_status is AuditStatus.FAILED
    assert any(item.code == "MISSING_REQUIRED_ARTIFACT" for item in report.findings)
    assert any(
        item.code == "MANIFEST_CONFIGURATION_REFERENCE_MISMATCH"
        for item in report.findings
    )


@pytest.mark.parametrize(
    ("path", "digest"),
    [
        ("outside/config.json", "0" * 64),
        ("synthetic-output/arc08-experiment-configuration.json", "not-a-checksum"),
    ],
)
def test_malformed_manifest_configuration_reference_fails(
    path: str, digest: str
) -> None:
    bundle = make_bundle()
    updated = update_json_payload(
        bundle,
        "synthetic-output/arc08-experiment-manifest.json",
        lambda document: document["configuration_reference"].update(
            path=path, sha256=digest
        ),
    )
    update_json_payload(
        bundle,
        "synthetic-output/arc08-synthetic-baseline-result.json",
        lambda document: document["manifest_linkage"].update(
            manifest_sha256=updated.sha256
        ),
    )

    report = audit_synthetic_evidence_bundle(bundle)

    assert report.audit_status is AuditStatus.FAILED
    assert any(
        item.code == "MANIFEST_CONFIGURATION_REFERENCE_MISMATCH"
        for item in report.findings
    )


def test_canonical_not_ready_status_and_pending_approval_are_preserved() -> None:
    report = audit_synthetic_evidence_bundle(make_bundle())

    assert report.audit_status is AuditStatus.VERIFIED
    assert report.acquisition_readiness_status == "NOT_READY"
    assert report.scientific_approval_status == "PENDING_REVIEW"


def test_ready_for_acquisition_with_pending_prerequisites_fails_audit() -> None:
    bundle = make_bundle()
    update_json_payload(
        bundle,
        "acquisition_readiness.json",
        lambda document: document.update(status="READY_FOR_ACQUISITION"),
    )
    ready_bundle = replace(
        bundle,
        acquisition_readiness_status=AcquisitionReadinessStatus.READY_FOR_ACQUISITION,
    )

    report = audit_synthetic_evidence_bundle(ready_bundle)

    assert report.audit_status is AuditStatus.FAILED
    assert any(
        item.code == "READINESS_PREREQUISITE_INCONSISTENCY" for item in report.findings
    )


def test_declared_approval_with_pending_effective_status_fails_audit() -> None:
    bundle = make_bundle()

    def contradict_approval(document: dict[str, object]) -> None:
        prerequisites = document["prerequisites"]
        assert isinstance(prerequisites, list)
        prediction = next(
            item
            for item in prerequisites
            if item["prerequisite_id"] == "prediction_task"
        )
        prediction["declared_status"] = "APPROVED"

    update_json_payload(
        bundle,
        "acquisition_readiness.json",
        contradict_approval,
    )

    report = audit_synthetic_evidence_bundle(bundle)

    assert report.audit_status is AuditStatus.FAILED
    assert any(
        item.code == "READINESS_PREREQUISITE_INCONSISTENCY" for item in report.findings
    )


def test_unsupported_readiness_vocabulary_fails_audit() -> None:
    bundle = make_bundle()
    update_json_payload(
        bundle,
        "acquisition_readiness.json",
        lambda document: document.update(status="READY"),
    )

    report = audit_synthetic_evidence_bundle(bundle)

    assert report.audit_status is AuditStatus.FAILED
    assert any(item.code == "READINESS_STATUS_MISMATCH" for item in report.findings)
    assert any(
        item.code == "READINESS_PREREQUISITE_INCONSISTENCY" for item in report.findings
    )


def test_not_ready_is_not_reported_as_authorization_and_failure_is_deterministic() -> (
    None
):
    bundle = make_bundle()
    update_json_payload(
        bundle,
        "acquisition_readiness.json",
        lambda document: document.update(status="READY_FOR_ACQUISITION"),
    )
    ready_bundle = replace(
        bundle,
        acquisition_readiness_status=AcquisitionReadinessStatus.READY_FOR_ACQUISITION,
    )

    first = audit_synthetic_evidence_bundle(ready_bundle)
    second = audit_synthetic_evidence_bundle(ready_bundle)

    assert serialize_reproducibility_audit(first) == serialize_reproducibility_audit(
        second
    )
    assert "authorization" in " ".join(first.limitations).lower()
    assert ready_bundle.scientific_acceptance_status == "PENDING_REVIEW"


def test_unsupported_bundle_schema_returns_structured_failed_audit() -> None:
    bundle = make_bundle()
    object.__setattr__(
        bundle, "schema_version", "arc08-synthetic-experiment-evidence-bundle/99"
    )

    report = audit_synthetic_evidence_bundle(bundle)

    assert report.audit_status is AuditStatus.FAILED
    assert report.bundle_schema_version.endswith("/99")
    assert any(item.code == "UNSUPPORTED_BUNDLE_SCHEMA" for item in report.findings)


def test_unsupported_artifact_schema_version_fails_audit() -> None:
    bundle = make_bundle()
    original = payload_by_name(
        bundle, "synthetic-output/arc08-experiment-manifest.json"
    )
    document = json.loads(original.payload_bytes)
    document["schema_version"] = "arc08-experiment-manifest/99"
    raw = json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    replace_payload(
        bundle,
        SyntheticEvidencePayload(
            original.name,
            original.media_type,
            original.synthetic_designation,
            raw,
            len(raw),
            hashlib.sha256(raw).hexdigest(),
        ),
    )

    report = audit_synthetic_evidence_bundle(bundle)

    assert report.audit_status is AuditStatus.FAILED
    assert any(item.code == "UNSUPPORTED_ARTIFACT_SCHEMA" for item in report.findings)


def test_missing_environment_fields_are_explicit_and_not_inferred() -> None:
    report = audit_synthetic_evidence_bundle(make_bundle())
    fields = {item.name: item for item in report.reproducibility_record.fields}

    assert report.reproducibility_record.completeness_status == "INCOMPLETE"
    assert report.reproducibility_status == "INCOMPLETE"
    assert fields["dependency_lockfile_reference"].status is MetadataStatus.MISSING
    assert fields["dependency_lockfile_sha256"].status is MetadataStatus.MISSING
    assert fields["repository_revision"].status is MetadataStatus.MISSING


def test_declared_environment_is_not_claimed_as_independently_verified() -> None:
    report = audit_synthetic_evidence_bundle(make_bundle())
    fields = {item.name: item for item in report.reproducibility_record.fields}

    assert (
        fields["python_version"].status
        is MetadataStatus.RECORDED_NOT_INDEPENDENTLY_VERIFIED
    )
    assert (
        fields["platform"].status is MetadataStatus.RECORDED_NOT_INDEPENDENTLY_VERIFIED
    )
    assert fields["scientific_acceptance"].status is MetadataStatus.PENDING_REVIEW
    assert report.scientific_approval_status == "PENDING_REVIEW"


def test_checksum_verification_does_not_claim_authenticity() -> None:
    report = audit_synthetic_evidence_bundle(make_bundle())
    serialized = serialize_reproducibility_audit(report).decode("utf-8")

    assert report.integrity_status is AuditStatus.VERIFIED
    assert "does not authenticate" in serialized
    assert "NASA authorization" in serialized or any(
        "authorization" in item.lower() for item in report.limitations
    )


def test_pending_policies_and_not_ready_status_are_not_upgraded() -> None:
    report = audit_synthetic_evidence_bundle(make_bundle())
    payload = payload_by_name(
        make_bundle(), "synthetic-output/arc08-experiment-configuration.json"
    )
    configuration = json.loads(payload.payload_bytes)

    assert report.scientific_approval_status == "PENDING_REVIEW"
    assert report.acquisition_readiness_status == "NOT_READY"
    assert all(
        item["decision"]["status"] == "PENDING_REVIEW"
        for item in configuration["policies"]
    )


def test_non_bundle_input_returns_structured_failed_report() -> None:
    report = audit_synthetic_evidence_bundle({"not": "a bundle"})

    assert report.audit_status is AuditStatus.FAILED
    assert report.integrity_status is AuditStatus.FAILED
    assert report.reproducibility_record.completeness_status == "INCOMPLETE"


def test_runner_bundle_schema_is_explicit_and_synthetic_only() -> None:
    bundle = make_bundle()
    document = json.loads(
        serialize_reproducibility_audit(audit_synthetic_evidence_bundle(bundle))
    )

    assert bundle.schema_version == SYNTHETIC_EVIDENCE_BUNDLE_SCHEMA_VERSION
    assert all(
        "synthetic-only" in item.synthetic_designation for item in bundle.payloads
    )
    assert document["integrity_status"] == "VERIFIED"
    assert document["reproducibility_status"] == "INCOMPLETE"
