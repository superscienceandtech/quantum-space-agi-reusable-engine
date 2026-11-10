"""Offline integrity inventory and reproducibility audit for synthetic bundles."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from typing import TypeAlias, cast

from quantum_space_agi.ml.acquisition_readiness import (
    PREREQUISITE_DEFINITIONS,
    AcquisitionReadinessStatus,
    EvidenceKind,
    EvidenceReferenceAvailability,
    EvidenceVerificationStatus,
    PrerequisiteStatus,
)
from quantum_space_agi.ml.error_selection_diagnostics import (
    ERROR_DIAGNOSTICS_SCHEMA_VERSION,
)
from quantum_space_agi.ml.synthetic_baseline import (
    SYNTHETIC_BASELINE_SCHEMA_VERSION,
    SYNTHETIC_FIXTURE_ID,
)
from quantum_space_agi.ml.synthetic_experiment_runner import (
    SYNTHETIC_EVIDENCE_BUNDLE_SCHEMA_VERSION,
    SyntheticEvidenceBundle,
    SyntheticEvidencePayload,
)

REPRODUCIBILITY_AUDIT_SCHEMA_VERSION = "arc08-reproducibility-audit/1"
_CONFIGURATION_ID = "synthetic-output/arc08-experiment-configuration.json"
_MANIFEST_ID = "synthetic-output/arc08-experiment-manifest.json"
_BASELINE_ID = "synthetic-output/arc08-synthetic-baseline-result.json"
_REQUIRED_ARTIFACTS = (
    _CONFIGURATION_ID,
    _MANIFEST_ID,
    _BASELINE_ID,
    "fixture_metadata.json",
    "validation_report.json",
    "exclusion_ledger.json",
    "split.json",
    "model.json",
    "predictions.json",
    "evaluation_metrics.json",
    "leakage_diagnostics.json",
    "error_selection_diagnostics.json",
    "acquisition_readiness.json",
)
_ARTIFACT_TYPES = {
    _CONFIGURATION_ID: "experiment_configuration",
    _MANIFEST_ID: "experiment_manifest",
    _BASELINE_ID: "baseline_result",
    "fixture_metadata.json": "synthetic_fixture_metadata",
    "validation_report.json": "mechanical_validation_report",
    "exclusion_ledger.json": "mechanical_exclusion_ledger",
    "split.json": "synthetic_split_assignments",
    "model.json": "synthetic_model_configuration",
    "predictions.json": "synthetic_predictions",
    "evaluation_metrics.json": "synthetic_metrics",
    "leakage_diagnostics.json": "leakage_diagnostics",
    "error_selection_diagnostics.json": "error_selection_diagnostics",
    "acquisition_readiness.json": "acquisition_readiness_assessment",
}
_SCHEMA_BY_ARTIFACT = {
    _CONFIGURATION_ID: "arc08-experiment-configuration/1",
    _MANIFEST_ID: "arc08-experiment-manifest/1",
    _BASELINE_ID: SYNTHETIC_BASELINE_SCHEMA_VERSION,
    "leakage_diagnostics.json": "arc08-leakage-diagnostics/1",
    "error_selection_diagnostics.json": ERROR_DIAGNOSTICS_SCHEMA_VERSION,
}

JsonScalar: TypeAlias = str | int | float | bool | None


class AuditStatus(StrEnum):
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    INCOMPLETE = "INCOMPLETE"


class MetadataStatus(StrEnum):
    VERIFIED = "VERIFIED"
    RECORDED_NOT_INDEPENDENTLY_VERIFIED = "RECORDED_NOT_INDEPENDENTLY_VERIFIED"
    MISSING = "MISSING"
    PENDING_REVIEW = "PENDING_REVIEW"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True, slots=True)
class AuditFinding:
    code: str
    status: str
    artifact_id: str
    message: str


@dataclass(frozen=True, slots=True)
class ArtifactInventoryEntry:
    artifact_id: str
    artifact_type: str
    schema_version: str | None
    byte_length: int | None
    declared_sha256: str | None
    computed_sha256: str | None
    encoding: str
    serialization_format: str
    required: bool
    integrity_status: str
    references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReproducibilityField:
    name: str
    status: MetadataStatus
    value: JsonScalar
    source_artifact_id: str | None
    explanation: str


@dataclass(frozen=True, slots=True)
class ReproducibilityRecord:
    schema_version: str
    fields: tuple[ReproducibilityField, ...]
    completeness_status: str


@dataclass(frozen=True, slots=True)
class ReproducibilityAuditReport:
    schema_version: str
    audit_status: AuditStatus
    integrity_status: AuditStatus
    reproducibility_status: str
    experiment_id: str | None
    fixture_id: str | None
    execution_status: str | None
    bundle_schema_version: str | None
    artifact_inventory: tuple[ArtifactInventoryEntry, ...]
    reproducibility_record: ReproducibilityRecord
    validation_input_row_count: int | None
    mechanically_accepted_row_count: int | None
    excluded_row_count: int | None
    split_status: str
    prediction_alignment_status: str
    baseline_identity: str | None
    metric_names: tuple[str, ...]
    acquisition_readiness_status: str
    scientific_approval_status: str
    unresolved_decisions: tuple[str, ...]
    findings: tuple[AuditFinding, ...]
    limitations: tuple[str, ...]


def audit_synthetic_evidence_bundle(bundle: object) -> ReproducibilityAuditReport:
    """Inventory and verify an in-memory bundle without filesystem access.

    The report verifies bytes relative to their declared digests. It does not
    establish payload authorship, source authenticity, scientific validity, or
    approval. Verification findings are returned in deterministic order.
    """
    findings: list[AuditFinding] = []
    if type(bundle) is not SyntheticEvidenceBundle:
        return _failed_report("input", "unsupported_bundle_type")

    bundle_schema = _string_or_none(getattr(bundle, "schema_version", None))
    if bundle_schema != SYNTHETIC_EVIDENCE_BUNDLE_SCHEMA_VERSION:
        findings.append(
            AuditFinding(
                "UNSUPPORTED_BUNDLE_SCHEMA",
                "FAILED",
                "bundle",
                "bundle schema version is not supported by this verifier",
            )
        )

    raw_payloads = getattr(bundle, "payloads", None)
    payloads = raw_payloads if type(raw_payloads) is tuple else ()
    if type(raw_payloads) is not tuple:
        findings.append(
            AuditFinding(
                "MALFORMED_PAYLOAD_COLLECTION",
                "FAILED",
                "bundle",
                "payload collection must be a tuple",
            )
        )

    payload_by_id: dict[str, SyntheticEvidencePayload] = {}
    duplicate_ids: set[str] = set()
    for item in payloads:
        if type(item) is not SyntheticEvidencePayload:
            findings.append(
                AuditFinding(
                    "MALFORMED_PAYLOAD",
                    "FAILED",
                    "bundle",
                    "payload entry has an unsupported type",
                )
            )
            continue
        artifact_id = _string_or_none(getattr(item, "name", None))
        if artifact_id is None:
            findings.append(
                AuditFinding(
                    "MISSING_ARTIFACT_ID",
                    "FAILED",
                    "bundle",
                    "payload has no valid artifact identifier",
                )
            )
            continue
        designation = _string_or_none(getattr(item, "synthetic_designation", None))
        if designation is None or "synthetic" not in designation.lower():
            findings.append(
                AuditFinding(
                    "SYNTHETIC_SCOPE_NOT_DECLARED",
                    "FAILED",
                    artifact_id,
                    "every evidence payload must carry a synthetic designation",
                )
            )
        if artifact_id in payload_by_id:
            duplicate_ids.add(artifact_id)
            previous = payload_by_id[artifact_id]
            findings.append(
                AuditFinding(
                    "DUPLICATE_ARTIFACT_ID",
                    "FAILED",
                    artifact_id,
                    "artifact identifier appears more than once",
                )
            )
            if (
                getattr(previous, "payload_bytes", None)
                != getattr(item, "payload_bytes", None)
                or getattr(previous, "sha256", None) != getattr(item, "sha256", None)
                or getattr(previous, "byte_length", None)
                != getattr(item, "byte_length", None)
            ):
                findings.append(
                    AuditFinding(
                        "CONFLICTING_ARTIFACT_DECLARATION",
                        "FAILED",
                        artifact_id,
                        "duplicate identifiers declare different bytes or "
                        "integrity metadata",
                    )
                )
        else:
            payload_by_id[artifact_id] = item

    for artifact_id in _REQUIRED_ARTIFACTS:
        if artifact_id not in payload_by_id:
            findings.append(
                AuditFinding(
                    "MISSING_REQUIRED_ARTIFACT",
                    "FAILED",
                    artifact_id,
                    "required synthetic evidence payload is missing",
                )
            )

    inventory: list[ArtifactInventoryEntry] = []
    parsed: dict[str, dict[str, object]] = {}
    for artifact_id in sorted(set(payload_by_id).union(duplicate_ids)):
        item = payload_by_id.get(artifact_id)
        if item is None:
            continue
        raw_bytes = getattr(item, "payload_bytes", None)
        declared_length = getattr(item, "byte_length", None)
        declared_digest = _string_or_none(getattr(item, "sha256", None))
        expected_length = len(raw_bytes) if type(raw_bytes) is bytes else None
        computed_digest = (
            hashlib.sha256(raw_bytes).hexdigest() if type(raw_bytes) is bytes else None
        )
        refs: tuple[str, ...] = ()
        document: dict[str, object] | None = None
        if type(raw_bytes) is not bytes:
            findings.append(
                AuditFinding(
                    "INVALID_PAYLOAD_BYTES",
                    "FAILED",
                    artifact_id,
                    "payload bytes must be immutable bytes",
                )
            )
        else:
            document, parse_error = _parse_payload(raw_bytes)
            if parse_error is not None:
                findings.append(
                    AuditFinding(
                        "INVALID_JSON_PAYLOAD", "FAILED", artifact_id, parse_error
                    )
                )
            else:
                assert document is not None
                parsed[artifact_id] = document
                schema = document.get("schema_version")
                expected_schema = _SCHEMA_BY_ARTIFACT.get(artifact_id)
                if expected_schema is not None and schema != expected_schema:
                    findings.append(
                        AuditFinding(
                            "UNSUPPORTED_ARTIFACT_SCHEMA",
                            "FAILED",
                            artifact_id,
                            "payload schema version is missing or unsupported",
                        )
                    )
                refs = _references_for_artifact(artifact_id, document)
        length_ok = type(declared_length) is int and declared_length == expected_length
        digest_ok = (
            computed_digest is not None
            and declared_digest == computed_digest
            and _is_sha256(declared_digest)
        )
        if not length_ok:
            findings.append(
                AuditFinding(
                    "BYTE_LENGTH_MISMATCH",
                    "FAILED",
                    artifact_id,
                    "declared byte length differs from the actual payload bytes",
                )
            )
        if not digest_ok:
            findings.append(
                AuditFinding(
                    "SHA256_MISMATCH",
                    "FAILED",
                    artifact_id,
                    "declared SHA-256 differs from the digest of exact payload bytes",
                )
            )
        integrity_status = "VERIFIED" if length_ok and digest_ok else "FAILED"
        inventory.append(
            ArtifactInventoryEntry(
                artifact_id=artifact_id,
                artifact_type=_ARTIFACT_TYPES.get(artifact_id, "additional_payload"),
                schema_version=(
                    _string_or_none(document.get("schema_version"))
                    if document is not None
                    else None
                ),
                byte_length=expected_length,
                declared_sha256=declared_digest,
                computed_sha256=computed_digest,
                encoding="UTF-8",
                serialization_format="JSON",
                required=artifact_id in _REQUIRED_ARTIFACTS,
                integrity_status=integrity_status,
                references=refs,
            )
        )

    for entry in inventory:
        for reference in entry.references:
            if reference not in payload_by_id:
                findings.append(
                    AuditFinding(
                        "UNRESOLVED_PAYLOAD_REFERENCE",
                        "FAILED",
                        entry.artifact_id,
                        f"declared payload reference does not resolve: {reference}",
                    )
                )

    _check_cross_artifact_consistency(bundle, parsed, findings)
    findings.sort(key=lambda item: (item.code, item.artifact_id, item.message))
    failed = any(item.status == "FAILED" for item in findings)
    audit_status = AuditStatus.FAILED if failed else AuditStatus.VERIFIED
    record, completeness = _reproducibility_record(bundle, parsed)
    reproducibility_status = "INCOMPLETE" if completeness else "RECORDED"
    if record.completeness_status != reproducibility_status:
        raise AssertionError("reproducibility completeness status mismatch")

    baseline = parsed.get(_BASELINE_ID, {})
    validation = parsed.get("validation_report.json", {})
    leakage = parsed.get("leakage_diagnostics.json", {})
    acquisition = parsed.get("acquisition_readiness.json", {})
    metrics_doc = parsed.get("evaluation_metrics.json", {})
    metric_names = _metric_names(metrics_doc)
    readiness_unresolved = acquisition.get("unresolved_decisions")
    unresolved_items: tuple[str, ...] = (
        "Scientific task, cohort, eligibility, and split policies remain pending "
        "review.",
        "NASA acquisition and data-use authorization remain unresolved.",
        "No original ARC-08 evidence archive or independent scientific acceptance "
        "is verified here.",
    )
    if type(readiness_unresolved) is list:
        unresolved_items += tuple(
            item for item in readiness_unresolved if type(item) is str
        )
    unresolved = tuple(sorted(set(unresolved_items)))
    limitations = (
        "Audit verification establishes integrity relative to recorded digests "
        "only; it does not authenticate authorship or source.",
        "The report audits synthetic software artifacts and does not establish "
        "scientific reproducibility or validity.",
        "Environment declarations are caller/configuration metadata unless "
        "independently checked by a separate process.",
        "Unavailable lockfile and repository revision metadata are reported as "
        "missing, not inferred.",
        "A complete synthetic audit does not authorize real NASA data acquisition "
        "or model evaluation; checksums do not establish NASA authorization.",
    )
    return ReproducibilityAuditReport(
        schema_version=REPRODUCIBILITY_AUDIT_SCHEMA_VERSION,
        audit_status=audit_status,
        integrity_status=audit_status,
        reproducibility_status=reproducibility_status,
        experiment_id=_string_or_none(getattr(bundle, "experiment_id", None)),
        fixture_id=_string_or_none(getattr(bundle, "fixture_id", None)),
        execution_status=_string_or_none(getattr(bundle, "execution_status", None)),
        bundle_schema_version=bundle_schema,
        artifact_inventory=tuple(inventory),
        reproducibility_record=record,
        validation_input_row_count=_int_or_none(validation.get("input_row_count")),
        mechanically_accepted_row_count=_count_indices(
            validation.get("mechanically_accepted_source_row_indices")
        ),
        excluded_row_count=_int_or_none(validation.get("excluded_row_count")),
        split_status=_nested_text(leakage, "split_integrity", "status"),
        prediction_alignment_status=_nested_text(
            leakage, "prediction_alignment", "status"
        ),
        baseline_identity=_nested_text(baseline, "experiment", "model", key="name"),
        metric_names=metric_names,
        acquisition_readiness_status=_string_or_none(acquisition.get("status"))
        or "MISSING",
        scientific_approval_status=_string_or_none(
            getattr(bundle, "scientific_acceptance_status", None)
        )
        or "MISSING",
        unresolved_decisions=unresolved,
        findings=tuple(findings),
        limitations=limitations,
    )


def serialize_reproducibility_audit(report: ReproducibilityAuditReport) -> bytes:
    """Serialize the immutable audit as deterministic compact UTF-8 JSON."""
    if type(report) is not ReproducibilityAuditReport:
        raise TypeError("report must be ReproducibilityAuditReport")
    return _canonical_json(_report_document(report))


def _failed_report(code: str, message: str) -> ReproducibilityAuditReport:
    finding = AuditFinding(code.upper(), "FAILED", "bundle", message)
    record = ReproducibilityRecord(
        "arc08-reproducibility-record/1",
        (),
        "INCOMPLETE",
    )
    return ReproducibilityAuditReport(
        REPRODUCIBILITY_AUDIT_SCHEMA_VERSION,
        AuditStatus.FAILED,
        AuditStatus.FAILED,
        "INCOMPLETE",
        None,
        None,
        None,
        None,
        (),
        record,
        None,
        None,
        None,
        "NOT_AVAILABLE",
        "NOT_AVAILABLE",
        None,
        (),
        "NOT_AVAILABLE",
        "PENDING_REVIEW",
        ("The bundle could not be inspected as a supported object.",),
        (finding,),
        ("This failed report contains no verified artifact inventory.",),
    )


def _reproducibility_record(
    bundle: SyntheticEvidenceBundle, parsed: dict[str, dict[str, object]]
) -> tuple[ReproducibilityRecord, bool]:
    config = parsed.get(_CONFIGURATION_ID, {})
    manifest = parsed.get(_MANIFEST_ID, {})
    baseline = parsed.get(_BASELINE_ID, {})
    dataset = config.get("dataset")
    dataset_doc = dataset if isinstance(dataset, dict) else {}
    environment = config.get("environment")
    env_doc = environment if isinstance(environment, dict) else {}
    identity_split = config.get("identity_and_split")
    split_doc = identity_split if isinstance(identity_split, dict) else {}
    task = config.get("research_task")
    task_doc = task if isinstance(task, dict) else {}
    target = task_doc.get("target")
    target_doc = target if isinstance(target, dict) else {}
    features = task_doc.get("features")
    feature = features[0] if isinstance(features, list) and features else None
    feature_doc = feature if isinstance(feature, dict) else {}
    model_eval = config.get("model_evaluation")
    model_doc = model_eval if isinstance(model_eval, dict) else {}
    baseline_model = baseline.get("experiment")
    baseline_experiment = baseline_model if isinstance(baseline_model, dict) else {}
    model_section = baseline_experiment.get("model")
    model_configuration = (
        model_section.get("configuration") if isinstance(model_section, dict) else None
    )
    model_configuration_doc = (
        model_configuration if isinstance(model_configuration, dict) else {}
    )
    manifest_linkage = baseline.get("manifest_linkage")
    link_doc = manifest_linkage if isinstance(manifest_linkage, dict) else {}

    fields: list[ReproducibilityField] = []
    fields.append(
        _field(
            "experiment_id",
            getattr(bundle, "experiment_id", None),
            MetadataStatus.VERIFIED
            if config.get("experiment_id") == getattr(bundle, "experiment_id", None)
            and manifest.get("experiment_id") == getattr(bundle, "experiment_id", None)
            else MetadataStatus.MISSING,
            _CONFIGURATION_ID,
            "Compared across bundle, configuration, and manifest declarations.",
        )
    )
    fields.append(
        _field(
            "bundle_schema_version",
            getattr(bundle, "schema_version", None),
            MetadataStatus.VERIFIED,
            None,
            "Checked against supported bundle schema.",
        )
    )
    fields.append(
        _field(
            "experiment_configuration_schema_version",
            config.get("schema_version"),
            MetadataStatus.VERIFIED
            if config.get("schema_version") == "arc08-experiment-configuration/1"
            else MetadataStatus.MISSING,
            _CONFIGURATION_ID,
            "Read from serialized configuration; digest is separately checked.",
        )
    )
    fields.append(
        _field(
            "manifest_schema_version",
            manifest.get("schema_version"),
            MetadataStatus.VERIFIED
            if manifest.get("schema_version") == "arc08-experiment-manifest/1"
            else MetadataStatus.MISSING,
            _MANIFEST_ID,
            "Read from serialized manifest; digest is separately checked.",
        )
    )
    for name, artifact_id in (
        ("configuration_canonical_bytes_sha256", _CONFIGURATION_ID),
        ("manifest_canonical_bytes_sha256", _MANIFEST_ID),
    ):
        entry = next(
            (
                item
                for item in _bundle_payloads(bundle)
                if getattr(item, "name", None) == artifact_id
            ),
            None,
        )
        raw_bytes = getattr(entry, "payload_bytes", None)
        actual_digest = (
            hashlib.sha256(raw_bytes).hexdigest() if type(raw_bytes) is bytes else None
        )
        fields.append(
            _field(
                name,
                getattr(entry, "sha256", None),
                MetadataStatus.VERIFIED
                if entry is not None and getattr(entry, "sha256", None) == actual_digest
                else MetadataStatus.MISSING,
                artifact_id,
                "Recalculated from exact payload bytes.",
            )
        )
    fields.extend(
        (
            _field(
                "fixture_id",
                getattr(bundle, "fixture_id", None),
                MetadataStatus.VERIFIED
                if getattr(bundle, "fixture_id", None) == SYNTHETIC_FIXTURE_ID
                else MetadataStatus.MISSING,
                "fixture_metadata.json",
                "Compared with the supported built-in synthetic fixture ID.",
            ),
            _field(
                "seed",
                getattr(bundle, "seed", None),
                MetadataStatus.VERIFIED
                if split_doc.get("seed") == getattr(bundle, "seed", None)
                else MetadataStatus.MISSING,
                _CONFIGURATION_ID,
                "Compared with the serialized split declaration.",
            ),
            _field(
                "split_strategy",
                split_doc.get("split_strategy"),
                MetadataStatus.RECORDED_NOT_INDEPENDENTLY_VERIFIED,
                _CONFIGURATION_ID,
                "Caller/configuration declaration; assignments are separately checked.",
            ),
            _field(
                "feature_definition",
                feature_doc.get("field"),
                MetadataStatus.RECORDED_NOT_INDEPENDENTLY_VERIFIED,
                _CONFIGURATION_ID,
                "Declared feature field; not a scientific approval.",
            ),
            _field(
                "target_definition",
                target_doc.get("field"),
                MetadataStatus.RECORDED_NOT_INDEPENDENTLY_VERIFIED,
                _CONFIGURATION_ID,
                "Declared target field; not a scientific approval.",
            ),
            _field(
                "baseline_model",
                model_doc.get("baseline_model_identifier"),
                MetadataStatus.RECORDED_NOT_INDEPENDENTLY_VERIFIED,
                _CONFIGURATION_ID,
                "Model identity is declared in configuration.",
            ),
            _field(
                "baseline_model_configuration",
                model_configuration_doc.get("strategy"),
                MetadataStatus.VERIFIED
                if model_configuration_doc.get("strategy") == "median"
                else MetadataStatus.MISSING,
                _BASELINE_ID,
                "Model strategy is read from the synthetic baseline result payload.",
            ),
            _field(
                "python_version",
                env_doc.get("python_version"),
                MetadataStatus.RECORDED_NOT_INDEPENDENTLY_VERIFIED
                if env_doc.get("python_version") is not None
                else MetadataStatus.MISSING,
                _CONFIGURATION_ID,
                "Configuration declaration; not independently checked against "
                "the executing interpreter.",
            ),
            _field(
                "platform",
                env_doc.get("platform"),
                MetadataStatus.RECORDED_NOT_INDEPENDENTLY_VERIFIED
                if env_doc.get("platform") is not None
                else MetadataStatus.MISSING,
                _CONFIGURATION_ID,
                "Configuration declaration; not independently verified.",
            ),
            _field(
                "dependency_lockfile_reference",
                None,
                MetadataStatus.MISSING,
                _CONFIGURATION_ID,
                "No lockfile reference was supplied.",
            ),
            _field(
                "dependency_lockfile_sha256",
                None,
                MetadataStatus.MISSING,
                _CONFIGURATION_ID,
                "No lockfile checksum was supplied.",
            ),
            _field(
                "runtime_dependency_versions",
                None,
                MetadataStatus.MISSING,
                None,
                "No resolved runtime dependency inventory is embedded in this bundle.",
            ),
            _field(
                "repository_revision",
                env_doc.get("repository_commit"),
                MetadataStatus.RECORDED_NOT_INDEPENDENTLY_VERIFIED
                if env_doc.get("repository_commit") is not None
                else MetadataStatus.MISSING,
                _CONFIGURATION_ID,
                "No revision is inferred when the configuration has none.",
            ),
            _field(
                "acquisition_readiness",
                _readiness_status_value(
                    getattr(bundle, "acquisition_readiness_status", None)
                ),
                MetadataStatus.VERIFIED
                if type(getattr(bundle, "acquisition_readiness_status", None))
                is AcquisitionReadinessStatus
                else MetadataStatus.MISSING,
                "acquisition_readiness.json",
                "Readiness status does not grant data authorization.",
            ),
            _field(
                "scientific_acceptance",
                getattr(bundle, "scientific_acceptance_status", None),
                MetadataStatus.PENDING_REVIEW,
                None,
                "Scientific acceptance remains pending; no approval is inferred.",
            ),
            _field(
                "dataset_identity",
                dataset_doc.get("source_identity"),
                MetadataStatus.RECORDED_NOT_INDEPENDENTLY_VERIFIED,
                _CONFIGURATION_ID,
                "Declared synthetic source identity.",
            ),
            _field(
                "source_snapshot",
                None,
                MetadataStatus.NOT_APPLICABLE,
                _MANIFEST_ID,
                "This generated synthetic fixture has no acquired raw snapshot.",
            ),
            _field(
                "baseline_manifest_linkage",
                link_doc.get("manifest_sha256"),
                MetadataStatus.RECORDED_NOT_INDEPENDENTLY_VERIFIED,
                _BASELINE_ID,
                "Link is checked against bundle payload bytes; it does not "
                "authenticate their origin.",
            ),
        )
    )
    incomplete = any(item.status is MetadataStatus.MISSING for item in fields)
    record = ReproducibilityRecord(
        "arc08-reproducibility-record/1",
        tuple(sorted(fields, key=lambda item: item.name)),
        "INCOMPLETE" if incomplete else "RECORDED",
    )
    return record, incomplete


def _field(
    name: str,
    value: object,
    status: MetadataStatus,
    source: str | None,
    explanation: str,
) -> ReproducibilityField:
    safe_value: JsonScalar = (
        cast(JsonScalar, value) if type(value) in (str, int, float, bool) else None
    )
    return ReproducibilityField(name, status, safe_value, source, explanation)


def _check_cross_artifact_consistency(
    bundle: SyntheticEvidenceBundle,
    parsed: dict[str, dict[str, object]],
    findings: list[AuditFinding],
) -> None:
    configuration = parsed.get(_CONFIGURATION_ID, {})
    manifest = parsed.get(_MANIFEST_ID, {})
    baseline = parsed.get(_BASELINE_ID, {})
    config_payload = next(
        (
            item
            for item in _bundle_payloads(bundle)
            if getattr(item, "name", None) == _CONFIGURATION_ID
        ),
        None,
    )
    manifest_payload = next(
        (
            item
            for item in _bundle_payloads(bundle)
            if getattr(item, "name", None) == _MANIFEST_ID
        ),
        None,
    )
    config_digest = _string_or_none(getattr(config_payload, "sha256", None))
    manifest_digest = _string_or_none(getattr(manifest_payload, "sha256", None))
    experiment_id = getattr(bundle, "experiment_id", None)
    for artifact_id, document in (
        (_CONFIGURATION_ID, configuration),
        (_MANIFEST_ID, manifest),
    ):
        if document.get("experiment_id") != experiment_id:
            findings.append(
                AuditFinding(
                    "EXPERIMENT_ID_MISMATCH",
                    "FAILED",
                    artifact_id,
                    "experiment ID differs from bundle",
                )
            )
    actual_config_digest = _payload_digest(config_payload)
    if manifest.get("configuration_sha256") != actual_config_digest:
        findings.append(
            AuditFinding(
                "CONFIGURATION_LINK_MISMATCH",
                "FAILED",
                _MANIFEST_ID,
                "manifest configuration digest differs from configuration payload",
            )
        )
    config_reference = manifest.get("configuration_reference")
    if (
        not isinstance(config_reference, dict)
        or config_reference.get("path") != _CONFIGURATION_ID
        or not _is_sha256(_string_or_none(config_reference.get("sha256")))
        or config_reference.get("sha256") != actual_config_digest
    ):
        findings.append(
            AuditFinding(
                "MANIFEST_CONFIGURATION_REFERENCE_MISMATCH",
                "FAILED",
                _MANIFEST_ID,
                "manifest configuration reference must resolve to the bundled "
                "configuration and declare its exact-byte SHA-256",
            )
        )
    task = configuration.get("research_task")
    task_doc = task if isinstance(task, dict) else {}
    config_target = task_doc.get("target")
    config_target_doc = config_target if isinstance(config_target, dict) else {}
    config_features = task_doc.get("features")
    config_feature = (
        config_features[0]
        if isinstance(config_features, list) and config_features
        else None
    )
    config_feature_doc = config_feature if isinstance(config_feature, dict) else {}
    base_experiment = baseline.get("experiment")
    base_experiment_doc = base_experiment if isinstance(base_experiment, dict) else {}
    base_feature = base_experiment_doc.get("feature")
    base_feature_doc = base_feature if isinstance(base_feature, dict) else {}
    base_target = base_experiment_doc.get("target")
    base_target_doc = base_target if isinstance(base_target, dict) else {}
    if config_target_doc.get("field") != base_target_doc.get(
        "field"
    ) or config_feature_doc.get("field") != base_feature_doc.get("field"):
        findings.append(
            AuditFinding(
                "FEATURE_TARGET_DECLARATION_MISMATCH",
                "FAILED",
                _CONFIGURATION_ID,
                "configuration feature/target differ from baseline result declarations",
            )
        )
    baseline_link = baseline.get("manifest_linkage")
    link = baseline_link if isinstance(baseline_link, dict) else {}
    if (
        link.get("configuration_sha256") != config_digest
        or link.get("manifest_sha256") != manifest_digest
    ):
        findings.append(
            AuditFinding(
                "BASELINE_MANIFEST_LINK_MISMATCH",
                "FAILED",
                _BASELINE_ID,
                "baseline result digest links differ from exact bundle payload bytes",
            )
        )
    split_doc = configuration.get("identity_and_split")
    split = split_doc if isinstance(split_doc, dict) else {}
    if split.get("seed") != getattr(bundle, "seed", None):
        findings.append(
            AuditFinding(
                "SEED_MISMATCH",
                "FAILED",
                _CONFIGURATION_ID,
                "bundle seed differs from configuration",
            )
        )
    if getattr(bundle, "execution_status", None) != "SUCCESSFUL_SYNTHETIC_EXECUTION":
        findings.append(
            AuditFinding(
                "INVALID_EXECUTION_STATUS",
                "FAILED",
                "bundle",
                "bundle does not record successful synthetic execution",
            )
        )
    if getattr(bundle, "fixture_id", None) != SYNTHETIC_FIXTURE_ID:
        findings.append(
            AuditFinding(
                "UNSUPPORTED_FIXTURE_ID",
                "FAILED",
                "bundle",
                "bundle does not identify the supported synthetic fixture",
            )
        )
    if getattr(bundle, "scientific_acceptance_status", None) != "PENDING_REVIEW":
        findings.append(
            AuditFinding(
                "SCIENTIFIC_STATUS_MISMATCH",
                "FAILED",
                "bundle",
                "synthetic runner must not mark science approved",
            )
        )
    _check_validation_accounting(parsed, findings)
    _check_split_prediction_accounting(parsed, findings)
    readiness = parsed.get("acquisition_readiness.json", {})
    if readiness.get("status") != _readiness_status_value(
        getattr(bundle, "acquisition_readiness_status", None)
    ):
        findings.append(
            AuditFinding(
                "READINESS_STATUS_MISMATCH",
                "FAILED",
                "acquisition_readiness.json",
                "readiness payload status differs from bundle summary",
            )
        )
    _check_readiness_consistency(readiness, findings)
    if any(
        status != "PENDING_REVIEW"
        for status in _declared_decision_statuses(configuration)
    ):
        findings.append(
            AuditFinding(
                "SCIENTIFIC_DECISION_NOT_PENDING",
                "FAILED",
                _CONFIGURATION_ID,
                "synthetic experiment policy declarations must remain pending review",
            )
        )


def _check_validation_accounting(
    parsed: dict[str, dict[str, object]], findings: list[AuditFinding]
) -> None:
    validation = parsed.get("validation_report.json", {})
    input_count = validation.get("input_row_count")
    accepted = validation.get("mechanically_accepted_source_row_indices")
    excluded_count = validation.get("excluded_row_count")
    ledger = parsed.get("exclusion_ledger.json", {}).get("_root_array")
    if (
        type(input_count) is not int
        or input_count < 0
        or type(excluded_count) is not int
        or excluded_count < 0
        or type(accepted) is not list
        or any(type(index) is not int or index < 0 for index in accepted)
        or type(ledger) is not list
    ):
        findings.append(
            AuditFinding(
                "VALIDATION_ACCOUNTING_MISSING",
                "FAILED",
                "validation_report.json",
                "validation counts or exclusion ledger are malformed",
            )
        )
        return
    excluded_indices = tuple(
        item.get("source_row_index") for item in ledger if isinstance(item, dict)
    )
    valid_ledger = len(excluded_indices) == len(ledger) and all(
        type(index) is int
        and index >= 0
        and isinstance(item, dict)
        and type(item.get("findings")) is list
        and bool(item.get("findings"))
        and all(
            isinstance(finding, dict)
            and type(finding.get("field")) is str
            and type(finding.get("reason_code")) is str
            and bool(finding.get("reason_code"))
            for finding in item.get("findings", [])
        )
        for index, item in zip(excluded_indices, ledger, strict=True)
    )
    accepted_indices = tuple(accepted)
    if (
        not valid_ledger
        or excluded_count != len(ledger)
        or len(set(accepted_indices)) != len(accepted_indices)
        or len(set(excluded_indices)) != len(excluded_indices)
        or set(accepted_indices).intersection(excluded_indices)
        or set(accepted_indices).union(excluded_indices) != set(range(input_count))
    ):
        findings.append(
            AuditFinding(
                "VALIDATION_ACCOUNTING_MISMATCH",
                "FAILED",
                "validation_report.json",
                "accepted indices, exclusion ledger, and input count do not reconcile",
            )
        )
    baseline_validation = parsed.get(_BASELINE_ID, {}).get("validation")
    if not isinstance(baseline_validation, dict) or (
        baseline_validation.get("input_row_count") != input_count
        or baseline_validation.get("mechanically_accepted_source_row_indices")
        != accepted
        or baseline_validation.get("excluded_row_count") != excluded_count
        or baseline_validation.get("exclusion_ledger") != ledger
    ):
        findings.append(
            AuditFinding(
                "BASELINE_VALIDATION_MISMATCH",
                "FAILED",
                _BASELINE_ID,
                "baseline validation and standalone validation/exclusion "
                "payloads differ",
            )
        )


def _check_split_prediction_accounting(
    parsed: dict[str, dict[str, object]], findings: list[AuditFinding]
) -> None:
    split = parsed.get("split.json", {})
    leakage = parsed.get("leakage_diagnostics.json", {})
    predictions = parsed.get("predictions.json", {}).get("_root_array")
    baseline = parsed.get(_BASELINE_ID, {}).get("predictions")
    train_ids = split.get("train_row_ids")
    test_ids = split.get("test_row_ids")
    baseline_experiment = parsed.get(_BASELINE_ID, {}).get("experiment")
    baseline_split = (
        baseline_experiment.get("split")
        if isinstance(baseline_experiment, dict)
        else None
    )
    split_integrity = leakage.get("split_integrity")
    alignment = leakage.get("prediction_alignment")
    fixture_meta = parsed.get("fixture_metadata.json", {})
    fixture_ids = fixture_meta.get("row_ids")
    validation = parsed.get("validation_report.json", {})
    accepted_indices = validation.get("mechanically_accepted_source_row_indices")
    if (
        type(train_ids) is not list
        or type(test_ids) is not list
        or type(predictions) is not list
        or type(baseline) is not list
        or not isinstance(baseline_split, dict)
        or type(fixture_ids) is not list
        or type(accepted_indices) is not list
    ):
        findings.append(
            AuditFinding(
                "SPLIT_PREDICTION_ACCOUNTING_MISSING",
                "FAILED",
                "split.json",
                "split or prediction payloads are malformed",
            )
        )
        return
    prediction_ids = tuple(
        item.get("row_id") for item in predictions if isinstance(item, dict)
    )
    baseline_prediction_ids = tuple(
        item.get("row_id") for item in baseline if isinstance(item, dict)
    )
    accepted_source_ids_valid = (
        all(type(row_id) is str and bool(row_id) for row_id in fixture_ids)
        and len(set(fixture_ids)) == len(fixture_ids)
        and all(
            type(index) is int and 0 <= index < len(fixture_ids)
            for index in accepted_indices
        )
    )
    expected_accepted_ids = (
        {fixture_ids[index] for index in accepted_indices}
        if accepted_source_ids_valid
        else set()
    )
    if (
        not accepted_source_ids_valid
        or train_ids != baseline_split.get("train_row_ids")
        or test_ids != baseline_split.get("test_row_ids")
        or any(
            type(row_id) is not str or not row_id for row_id in (*train_ids, *test_ids)
        )
        or len(set(train_ids)) != len(train_ids)
        or len(set(test_ids)) != len(test_ids)
        or len(prediction_ids) != len(predictions)
        or tuple(test_ids) != prediction_ids
        or prediction_ids != baseline_prediction_ids
        or set(train_ids).intersection(test_ids)
        or set(train_ids).union(test_ids) != expected_accepted_ids
        or not isinstance(split_integrity, dict)
        or split_integrity.get("status") != "PASS"
        or not isinstance(alignment, dict)
        or alignment.get("status") != "PASS"
    ):
        findings.append(
            AuditFinding(
                "SPLIT_PREDICTION_ACCOUNTING_MISMATCH",
                "FAILED",
                "split.json",
                "split IDs, leakage diagnostics, and prediction IDs do not reconcile",
            )
        )
    baseline_experiment = parsed.get(_BASELINE_ID, {}).get("experiment")
    baseline_model = (
        baseline_experiment.get("model")
        if isinstance(baseline_experiment, dict)
        else None
    )
    if parsed.get("model.json") != baseline_model:
        findings.append(
            AuditFinding(
                "MODEL_DECLARATION_MISMATCH",
                "FAILED",
                "model.json",
                "standalone model payload differs from baseline result",
            )
        )
    baseline_metrics = parsed.get(_BASELINE_ID, {}).get("metrics")
    if parsed.get("evaluation_metrics.json") != baseline_metrics:
        findings.append(
            AuditFinding(
                "METRIC_DECLARATION_MISMATCH",
                "FAILED",
                "evaluation_metrics.json",
                "standalone metric payload differs from baseline result",
            )
        )


def _declared_decision_statuses(
    configuration: dict[str, object],
) -> tuple[object, ...]:
    statuses: list[object] = []
    task = configuration.get("research_task")
    if isinstance(task, dict) and isinstance(task.get("decision"), dict):
        statuses.append(task["decision"].get("status"))
    policies = configuration.get("policies")
    if isinstance(policies, list):
        statuses.extend(
            policy.get("decision", {}).get("status")
            for policy in policies
            if isinstance(policy, dict) and isinstance(policy.get("decision"), dict)
        )
    for key in ("identity_and_split", "model_evaluation"):
        section = configuration.get(key)
        if isinstance(section, dict) and isinstance(section.get("decision"), dict):
            statuses.append(section["decision"].get("status"))
    return tuple(statuses)


def _check_readiness_consistency(
    document: dict[str, object], findings: list[AuditFinding]
) -> None:
    """Check serialized readiness against the fixed acquisition gate policy."""
    artifact_id = "acquisition_readiness.json"
    try:
        status_value = document.get("status")
        if type(status_value) is not str:
            raise ValueError("readiness status must be text")
        status = AcquisitionReadinessStatus(status_value)
        items = document.get("prerequisites")
        if type(items) is not list:
            raise ValueError("prerequisites must be a list")
        by_id: dict[str, dict[str, object]] = {}
        for item in items:
            if (
                not isinstance(item, dict)
                or type(item.get("prerequisite_id")) is not str
            ):
                raise ValueError("prerequisite entry is malformed")
            prerequisite_id = cast(str, item["prerequisite_id"])
            if prerequisite_id in by_id:
                raise ValueError("prerequisite identifiers must be unique")
            by_id[prerequisite_id] = cast(dict[str, object], item)
        expected_ids = {item.prerequisite_id for item in PREREQUISITE_DEFINITIONS}
        if set(by_id) != expected_ids:
            raise ValueError("prerequisite identifiers do not match the gate policy")

        unresolved: list[str] = []
        blockers: list[str] = []
        limitations: list[str] = []
        for definition in PREREQUISITE_DEFINITIONS:
            item = by_id[definition.prerequisite_id]
            effective_value = item.get("status")
            if type(effective_value) is not str:
                raise ValueError("prerequisite status must be text")
            effective = PrerequisiteStatus(effective_value)
            declared_value = item.get("declared_status")
            if declared_value is not None and type(declared_value) is not str:
                raise ValueError("declared prerequisite status must be text or null")
            declared = (
                None if declared_value is None else PrerequisiteStatus(declared_value)
            )
            explanation = item.get("explanation")
            if type(explanation) is not str or not explanation.strip():
                raise ValueError("prerequisite explanation is missing")
            if type(item.get("blocks_acquisition")) is not bool or (
                item["blocks_acquisition"] is not definition.blocks_acquisition
            ):
                raise ValueError("prerequisite blocking policy is inconsistent")
            evidence = item.get("evidence")
            if type(evidence) is not list:
                raise ValueError("prerequisite evidence must be a list")
            kinds: set[EvidenceKind] = set()
            for reference in evidence:
                if not isinstance(reference, dict):
                    raise ValueError("prerequisite evidence reference is malformed")
                if (
                    type(reference.get("reference")) is not str
                    or not reference["reference"].strip()
                ):
                    raise ValueError("prerequisite evidence reference is empty")
                note = reference.get("note")
                if note is not None and (type(note) is not str or not note.strip()):
                    raise ValueError("prerequisite evidence note is malformed")
                kind = reference.get("kind")
                availability = reference.get("availability")
                if type(kind) is not str or type(availability) is not str:
                    raise ValueError(
                        "prerequisite evidence kind/availability is malformed"
                    )
                kinds.add(EvidenceKind(kind))
                EvidenceReferenceAvailability(availability)
                verification_status = reference.get("verification_status")
                if type(verification_status) is not str or (
                    EvidenceVerificationStatus(verification_status)
                    is not EvidenceVerificationStatus.DECLARED_NOT_AUTHENTICATED
                ):
                    raise ValueError(
                        "readiness evidence verification status is unsupported"
                    )
            has_required_evidence = bool(evidence) and set(
                definition.required_evidence_kinds
            ).issubset(kinds)
            if EvidenceKind.FORMAL_APPROVAL in definition.required_evidence_kinds:
                authority = item.get("decision_authority")
                has_required_evidence = has_required_evidence and (
                    type(authority) is str and bool(authority.strip())
                )
            evidence_sufficient = item.get("evidence_sufficient")
            if type(evidence_sufficient) is not bool:
                raise ValueError("evidence_sufficient must be a boolean")
            if (
                evidence_sufficient
                and not has_required_evidence
                and declared is not PrerequisiteStatus.NOT_APPLICABLE
            ):
                raise ValueError("evidence sufficiency is not supported by evidence")
            if (
                declared is not PrerequisiteStatus.NOT_APPLICABLE
                and evidence_sufficient is not has_required_evidence
            ):
                raise ValueError("evidence sufficiency flag conflicts with evidence")
            if effective is PrerequisiteStatus.APPROVED:
                raise ValueError("this gate has no independent evidence authenticator")
            if declared in (
                PrerequisiteStatus.PENDING,
                PrerequisiteStatus.BLOCKED,
            ) and (effective is not declared):
                raise ValueError("declared and effective prerequisite states conflict")
            if declared is PrerequisiteStatus.APPROVED and (
                effective is not PrerequisiteStatus.BLOCKED
            ):
                raise ValueError("declared and effective approval states conflict")
            if declared is None and effective is not PrerequisiteStatus.PENDING:
                raise ValueError("missing declaration must remain pending")
            if effective is PrerequisiteStatus.NOT_APPLICABLE and (
                not definition.allows_not_applicable
                or definition.blocks_acquisition
                or declared is not PrerequisiteStatus.NOT_APPLICABLE
                or not evidence_sufficient
            ):
                raise ValueError("NOT_APPLICABLE cannot waive a prerequisite")
            if declared is PrerequisiteStatus.NOT_APPLICABLE and (
                effective
                is not (
                    PrerequisiteStatus.NOT_APPLICABLE
                    if definition.allows_not_applicable
                    and not definition.blocks_acquisition
                    else PrerequisiteStatus.BLOCKED
                )
            ):
                raise ValueError("declared non-applicability is inconsistent")
            if declared is PrerequisiteStatus.NOT_APPLICABLE and (
                effective is PrerequisiteStatus.NOT_APPLICABLE
                and not evidence_sufficient
            ):
                raise ValueError("non-applicable state lacks required evidence")
            explanation_text = explanation
            if effective is not PrerequisiteStatus.NOT_APPLICABLE:
                unresolved.append(f"{definition.prerequisite_id}: {explanation_text}")
            if definition.blocks_acquisition:
                blockers.append(f"{definition.prerequisite_id}: {explanation_text}")
            if not definition.blocks_acquisition:
                limitations.append(f"{definition.prerequisite_id}: {explanation_text}")

        expected_status = (
            AcquisitionReadinessStatus.NOT_READY
            if blockers
            else AcquisitionReadinessStatus.READY_FOR_ACQUISITION
        )
        if status is not expected_status:
            raise ValueError("overall readiness conflicts with prerequisite states")
        for key, expected in (
            ("unresolved_decisions", unresolved),
            ("blocking_issues", blockers),
            ("non_blocking_limitations", limitations),
        ):
            if document.get(key) != expected:
                raise ValueError(f"{key} does not match prerequisite states")
    except (TypeError, ValueError) as exc:
        findings.append(
            AuditFinding(
                "READINESS_PREREQUISITE_INCONSISTENCY",
                "FAILED",
                artifact_id,
                "readiness status and prerequisite declarations are inconsistent: "
                f"{exc}",
            )
        )


def _payload_digest(payload: object) -> str | None:
    raw_bytes = getattr(payload, "payload_bytes", None)
    return hashlib.sha256(raw_bytes).hexdigest() if type(raw_bytes) is bytes else None


def _readiness_status_value(value: object) -> str | None:
    return value.value if type(value) is AcquisitionReadinessStatus else None


def _references_for_artifact(
    artifact_id: str, document: dict[str, object]
) -> tuple[str, ...]:
    references: list[str] = []
    if artifact_id == _MANIFEST_ID:
        config_ref = document.get("configuration_reference")
        if isinstance(config_ref, dict) and type(config_ref.get("path")) is str:
            references.append(cast(str, config_ref["path"]))
        outputs = document.get("output_artifacts")
        if isinstance(outputs, list):
            for output in outputs:
                if isinstance(output, dict):
                    reference = output.get("artifact", output.get("reference"))
                    if (
                        isinstance(reference, dict)
                        and type(reference.get("path")) is str
                    ):
                        references.append(cast(str, reference["path"]))
    elif artifact_id == _BASELINE_ID:
        linkage = document.get("manifest_linkage")
        if isinstance(linkage, dict):
            for field in ("configuration_artifact", "manifest_artifact"):
                value = linkage.get(field)
                if type(value) is str:
                    references.append(value)
    return tuple(sorted(set(references)))


def _bundle_payloads(bundle: object) -> tuple[object, ...]:
    payloads = getattr(bundle, "payloads", None)
    return payloads if type(payloads) is tuple else ()


def _parse_payload(raw_bytes: bytes) -> tuple[dict[str, object] | None, str | None]:
    try:
        document = json.loads(
            raw_bytes.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return (
            None,
            "payload is not strict UTF-8 JSON with unique keys and finite numbers",
        )
    try:
        canonical_bytes = json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, OverflowError):
        return None, "payload cannot be represented as canonical UTF-8 JSON"
    if canonical_bytes != raw_bytes:
        return None, "payload JSON is valid but not in the required canonical encoding"
    if isinstance(document, dict):
        return cast(dict[str, object], document), None
    if isinstance(document, list):
        return {"_root_array": document}, None
    return None, "JSON payload root must be an object or array"


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is unsupported: {value}")


def _metric_names(document: dict[str, object]) -> tuple[str, ...]:
    names: set[str] = set()
    primary = document.get("primary")
    if isinstance(primary, dict) and type(primary.get("name")) is str:
        names.add(cast(str, primary["name"]))
    diagnostics = document.get("diagnostics")
    if isinstance(diagnostics, dict):
        names.update(key for key in diagnostics if type(key) is str)
    return tuple(sorted(names))


def _nested_text(
    document: dict[str, object], first: str, second: str, *, key: str = "status"
) -> str:
    nested = document.get(first)
    if isinstance(nested, dict):
        value = nested.get(second)
        if isinstance(value, dict):
            return _string_or_none(value.get(key)) or "NOT_AVAILABLE"
        return _string_or_none(value) or "NOT_AVAILABLE"
    return "NOT_AVAILABLE"


def _count_indices(value: object) -> int | None:
    return (
        len(value)
        if type(value) is list and all(type(item) is int for item in value)
        else None
    )


def _int_or_none(value: object) -> int | None:
    return value if type(value) is int and value >= 0 else None


def _string_or_none(value: object) -> str | None:
    return value if type(value) is str else None


def _is_sha256(value: str | None) -> bool:
    return (
        value is not None
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _canonical_json(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, OverflowError) as exc:
        raise ValueError("audit report cannot be serialized as canonical JSON") from exc


def _report_document(report: ReproducibilityAuditReport) -> dict[str, object]:
    return {
        "schema_version": report.schema_version,
        "audit_status": report.audit_status.value,
        "integrity_status": report.integrity_status.value,
        "reproducibility_status": report.reproducibility_status,
        "experiment_id": report.experiment_id,
        "fixture_id": report.fixture_id,
        "execution_status": report.execution_status,
        "bundle_schema_version": report.bundle_schema_version,
        "artifact_inventory": [
            {
                "artifact_id": item.artifact_id,
                "artifact_type": item.artifact_type,
                "schema_version": item.schema_version,
                "byte_length": item.byte_length,
                "declared_sha256": item.declared_sha256,
                "computed_sha256": item.computed_sha256,
                "encoding": item.encoding,
                "serialization_format": item.serialization_format,
                "required": item.required,
                "integrity_status": item.integrity_status,
                "references": list(item.references),
            }
            for item in report.artifact_inventory
        ],
        "reproducibility_record": {
            "schema_version": report.reproducibility_record.schema_version,
            "completeness_status": report.reproducibility_record.completeness_status,
            "fields": [
                {
                    "name": item.name,
                    "status": item.status.value,
                    "value": item.value,
                    "source_artifact_id": item.source_artifact_id,
                    "explanation": item.explanation,
                }
                for item in report.reproducibility_record.fields
            ],
        },
        "validation": {
            "input_row_count": report.validation_input_row_count,
            "mechanically_accepted_row_count": report.mechanically_accepted_row_count,
            "excluded_row_count": report.excluded_row_count,
        },
        "split_status": report.split_status,
        "prediction_alignment_status": report.prediction_alignment_status,
        "baseline_identity": report.baseline_identity,
        "metric_names": list(report.metric_names),
        "acquisition_readiness_status": report.acquisition_readiness_status,
        "scientific_approval_status": report.scientific_approval_status,
        "unresolved_decisions": list(report.unresolved_decisions),
        "findings": [
            {
                "code": item.code,
                "status": item.status,
                "artifact_id": item.artifact_id,
                "message": item.message,
            }
            for item in report.findings
        ],
        "limitations": list(report.limitations),
    }
