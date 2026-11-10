"""Orchestrate a deterministic, synthetic-only ARC-08 experiment bundle."""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from statistics import median
from typing import TypeAlias, cast

from quantum_space_agi.ml.acquisition_readiness import (
    AcquisitionReadinessStatus,
    assess_current_repository_readiness,
    serialize_acquisition_readiness,
)
from quantum_space_agi.ml.dataset_validation import (
    DatasetValidationReport,
    validate_baseline_records,
)
from quantum_space_agi.ml.error_selection_diagnostics import (
    ErrorSelectionDiagnosticReport,
    UncertaintyFieldSpec,
    UncertaintyRole,
    diagnose_error_selection,
    serialize_error_selection_diagnostics,
)
from quantum_space_agi.ml.experiment_manifest import (
    EXPERIMENT_CONFIGURATION_SCHEMA_VERSION,
    EXPERIMENT_MANIFEST_SCHEMA_VERSION,
)
from quantum_space_agi.ml.leakage_diagnostics import (
    ExperimentManifestLinkage,
    LeakageDiagnosticReport,
    diagnose_split_integrity,
    serialize_leakage_diagnostics,
)
from quantum_space_agi.ml.synthetic_baseline import (
    DEFAULT_TEST_FRACTION,
    SYNTHETIC_FIXTURE_ID,
    SyntheticBaselineResult,
    run_synthetic_baseline,
)

SYNTHETIC_EVIDENCE_BUNDLE_SCHEMA_VERSION = (
    "arc08-synthetic-experiment-evidence-bundle/1"
)
SYNTHETIC_EXPERIMENT_RUNNER_VERSION = "arc08-synthetic-experiment-runner/1"
_ROW_ID_FIELD = "synthetic_row_id"
_UNCERTAINTY_FIELDS = (
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
)
JsonScalar: TypeAlias = str | int | float | bool | None


class SyntheticExperimentError(RuntimeError):
    """A stage failed; no success-labelled evidence bundle was produced."""

    execution_status = "FAILED"

    def __init__(self, stage: str, message: str) -> None:
        self.stage = stage
        super().__init__(f"synthetic execution failed at {stage}: {message}")


@dataclass(frozen=True, slots=True)
class SyntheticEvidencePayload:
    """Exact serialized bytes and integrity values for one synthetic payload."""

    name: str
    media_type: str
    synthetic_designation: str
    payload_bytes: bytes
    byte_length: int
    sha256: str

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name.strip():
            raise ValueError("payload name must be non-empty text")
        if type(self.media_type) is not str or not self.media_type.strip():
            raise ValueError("payload media_type must be non-empty text")
        if (
            type(self.synthetic_designation) is not str
            or not self.synthetic_designation
        ):
            raise ValueError("payload must have an explicit synthetic designation")
        if type(self.payload_bytes) is not bytes:
            raise TypeError("payload_bytes must be bytes")
        actual_length = len(self.payload_bytes)
        actual_digest = hashlib.sha256(self.payload_bytes).hexdigest()
        if type(self.byte_length) is not int or self.byte_length != actual_length:
            raise ValueError("payload byte_length does not match exact bytes")
        if type(self.sha256) is not str or self.sha256 != actual_digest:
            raise ValueError("payload sha256 does not match exact bytes")


@dataclass(frozen=True, slots=True)
class SyntheticEvidenceBundle:
    """Immutable, in-memory package of reproducible synthetic evidence."""

    schema_version: str
    execution_status: str
    experiment_id: str
    fixture_id: str
    seed: int
    runner_version: str
    stage_statuses: tuple[tuple[str, str], ...]
    diagnostic_statuses: tuple[tuple[str, str], ...]
    scientific_acceptance_status: str
    acquisition_readiness_status: AcquisitionReadinessStatus
    payloads: tuple[SyntheticEvidencePayload, ...]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            type(self.schema_version) is not str
            or self.schema_version != SYNTHETIC_EVIDENCE_BUNDLE_SCHEMA_VERSION
        ):
            raise ValueError("unsupported synthetic evidence bundle schema")
        if (
            type(self.execution_status) is not str
            or self.execution_status != "SUCCESSFUL_SYNTHETIC_EXECUTION"
        ):
            raise ValueError("bundle execution_status must describe synthetic success")
        if type(self.experiment_id) is not str or not self.experiment_id.strip():
            raise ValueError("experiment_id must be non-empty text")
        if type(self.fixture_id) is not str or self.fixture_id != SYNTHETIC_FIXTURE_ID:
            raise ValueError("fixture_id must identify the built-in synthetic fixture")
        if type(self.seed) is not int or self.seed < 0:
            raise ValueError("seed must be a non-negative built-in integer")
        if type(self.stage_statuses) is not tuple or any(
            type(item) is not tuple
            or len(item) != 2
            or any(type(value) is not str or not value for value in item)
            for item in self.stage_statuses
        ):
            raise ValueError("stage_statuses must be immutable name/status pairs")
        if type(self.diagnostic_statuses) is not tuple or any(
            type(item) is not tuple
            or len(item) != 2
            or any(type(value) is not str or not value for value in item)
            for item in self.diagnostic_statuses
        ):
            raise ValueError("diagnostic_statuses must be immutable name/status pairs")
        if type(self.payloads) is not tuple or any(
            type(item) is not SyntheticEvidencePayload for item in self.payloads
        ):
            raise ValueError("payloads must be an immutable tuple of evidence payloads")
        if len({item.name for item in self.payloads}) != len(self.payloads):
            raise ValueError("payload names must be unique")
        if tuple(item.name for item in self.payloads) != tuple(
            sorted(item.name for item in self.payloads)
        ):
            raise ValueError("payloads must use canonical name order")
        if type(self.limitations) is not tuple or any(
            type(item) is not str or not item.strip() for item in self.limitations
        ):
            raise ValueError("limitations must be an immutable tuple of text")
        if type(self.scientific_acceptance_status) is not str or (
            self.scientific_acceptance_status != "PENDING_REVIEW"
        ):
            raise ValueError("scientific acceptance must remain pending review")
        if type(self.acquisition_readiness_status) is not AcquisitionReadinessStatus:
            raise ValueError("acquisition readiness status is invalid")


def run_synthetic_experiment(
    *, experiment_id: str, seed: int, test_fraction: float = DEFAULT_TEST_FRACTION
) -> SyntheticEvidenceBundle:
    """Run the existing synthetic baseline and package its offline evidence.

    All data are generated by the built-in synthetic fixtures. No caller-supplied
    dataset mode exists. A failure raises ``SyntheticExperimentError`` carrying
    the failed stage and never returns a partially successful bundle.
    """
    if type(experiment_id) is not str or not experiment_id.strip():
        raise SyntheticExperimentError("configuration", "experiment_id is required")
    if type(seed) is not int or seed < 0:
        raise SyntheticExperimentError("configuration", "seed must be non-negative")

    try:
        baseline = run_synthetic_baseline(
            seed=seed, test_fraction=test_fraction, experiment_id=experiment_id
        )
        rows = _diagnostic_fixture()
        validation = validate_baseline_records(rows)  # type: ignore[arg-type]
        _validate_baseline_result(rows, validation, baseline, experiment_id, seed)
    except Exception as exc:
        if isinstance(exc, SyntheticExperimentError):
            raise
        raise SyntheticExperimentError(
            "baseline_validation_split_fit", str(exc)
        ) from exc

    configuration_sha256 = hashlib.sha256(baseline.configuration_bytes).hexdigest()
    manifest_sha256 = hashlib.sha256(baseline.manifest_bytes).hexdigest()
    if (
        configuration_sha256 != baseline.configuration_sha256
        or manifest_sha256 != baseline.manifest_sha256
    ):
        raise SyntheticExperimentError(
            "manifest_linkage", "manifest or configuration digest mismatch"
        )
    try:
        configuration_doc = _parse_json(baseline.configuration_bytes, "configuration")
        manifest_doc = _parse_json(baseline.manifest_bytes, "manifest")
        if (
            configuration_doc.get("schema_version")
            != EXPERIMENT_CONFIGURATION_SCHEMA_VERSION
            or configuration_doc.get("experiment_id") != experiment_id
            or manifest_doc.get("schema_version") != EXPERIMENT_MANIFEST_SCHEMA_VERSION
            or manifest_doc.get("experiment_id") != experiment_id
            or manifest_doc.get("configuration_sha256") != configuration_sha256
        ):
            raise ValueError("configuration and manifest declarations do not match")
        _require_pending_policy_states(configuration_doc)
        linkage = ExperimentManifestLinkage(
            experiment_id,
            configuration_sha256,
            manifest_sha256,
            EXPERIMENT_MANIFEST_SCHEMA_VERSION,
        )
    except Exception as exc:
        raise SyntheticExperimentError("manifest_linkage", str(exc)) from exc

    accepted_rows = tuple(rows[index] for index in validation.valid_record_indices)
    try:
        leakage = diagnose_split_integrity(
            accepted_rows,
            row_id_field=_ROW_ID_FIELD,
            train_row_ids=baseline.train_row_ids,
            test_row_ids=baseline.test_row_ids,
            prediction_row_ids=tuple(item.row_id for item in baseline.predictions),
            experiment_id=experiment_id,
            fixture_id=SYNTHETIC_FIXTURE_ID,
            split_method="seeded_random_row_split_synthetic_only",
            seed=seed,
            manifest_linkage=linkage,
        )
        if leakage.split_integrity.status != "PASS":
            raise ValueError("split integrity did not pass")
        if leakage.prediction_alignment.status != "PASS":
            raise ValueError("prediction row alignment did not pass")
        if set(baseline.train_row_ids).intersection(baseline.test_row_ids):
            raise ValueError("training and test row IDs overlap")
        if set((*baseline.train_row_ids, *baseline.test_row_ids)) != {
            cast(str, rows[index][_ROW_ID_FIELD])
            for index in validation.valid_record_indices
        }:
            raise ValueError("train/test IDs do not account for accepted rows")
    except Exception as exc:
        raise SyntheticExperimentError("split_integrity_diagnostics", str(exc)) from exc

    try:
        error_diagnostics = diagnose_error_selection(
            rows,
            validation,
            baseline.test_row_ids,
            baseline.predictions,
            experiment_id=experiment_id,
            fixture_id=SYNTHETIC_FIXTURE_ID,
            group_fields=("synthetic_host_group", "synthetic_category"),
            uncertainty_fields=_UNCERTAINTY_FIELDS,
            manifest_linkage=linkage,
        )
    except Exception as exc:
        raise SyntheticExperimentError("error_selection_diagnostics", str(exc)) from exc

    try:
        readiness = assess_current_repository_readiness()
        payloads = _create_payloads(
            rows,
            validation,
            baseline,
            leakage,
            error_diagnostics,
            serialize_acquisition_readiness(readiness),
        )
        bundle = SyntheticEvidenceBundle(
            schema_version=SYNTHETIC_EVIDENCE_BUNDLE_SCHEMA_VERSION,
            execution_status="SUCCESSFUL_SYNTHETIC_EXECUTION",
            experiment_id=experiment_id,
            fixture_id=SYNTHETIC_FIXTURE_ID,
            seed=seed,
            runner_version=SYNTHETIC_EXPERIMENT_RUNNER_VERSION,
            stage_statuses=(
                ("fixture_generation", "COMPLETED"),
                ("dataset_validation", "COMPLETED"),
                ("split_model_metrics", "COMPLETED"),
                ("configuration_manifest", "COMPLETED"),
                ("evidence_bundle", "COMPLETED"),
            ),
            diagnostic_statuses=(
                ("split_leakage_identity", "COMPLETED"),
                ("error_uncertainty_selection", "COMPLETED"),
            ),
            scientific_acceptance_status="PENDING_REVIEW",
            acquisition_readiness_status=readiness.status,
            payloads=payloads,
            limitations=(
                "All records and metrics in this bundle are generated from "
                "synthetic fixtures.",
                "Mechanical acceptance is not scientific eligibility or an "
                "approved cohort.",
                "The seeded row split is an engineering smoke test, not an "
                "approved evaluation policy.",
                "Declared manifest links and calculated payload hashes do not "
                "authenticate source or approval.",
                "No source snapshot exists for this generated fixture; no NASA "
                "acquisition is represented.",
                "This bundle does not establish real-world reproducibility or "
                "scientific performance.",
            ),
        )
        return bundle
    except Exception as exc:
        raise SyntheticExperimentError("evidence_bundle", str(exc)) from exc


def serialize_synthetic_evidence_bundle(bundle: SyntheticEvidenceBundle) -> bytes:
    """Serialize the complete bundle deterministically as UTF-8 JSON."""
    if type(bundle) is not SyntheticEvidenceBundle:
        raise TypeError("bundle must be SyntheticEvidenceBundle")
    document = {
        "schema_version": bundle.schema_version,
        "execution_status": bundle.execution_status,
        "experiment_id": bundle.experiment_id,
        "fixture_id": bundle.fixture_id,
        "seed": bundle.seed,
        "runner_version": bundle.runner_version,
        "stage_statuses": [
            {"stage": stage, "status": status}
            for stage, status in bundle.stage_statuses
        ],
        "diagnostic_statuses": [
            {"diagnostic": name, "status": status}
            for name, status in bundle.diagnostic_statuses
        ],
        "scientific_acceptance_status": bundle.scientific_acceptance_status,
        "acquisition_readiness_status": bundle.acquisition_readiness_status.value,
        "payloads": [
            {
                "name": item.name,
                "media_type": item.media_type,
                "synthetic_designation": item.synthetic_designation,
                "byte_length": item.byte_length,
                "sha256": item.sha256,
                "payload_base64": base64.b64encode(item.payload_bytes).decode("ascii"),
            }
            for item in bundle.payloads
        ],
        "limitations": list(bundle.limitations),
    }
    try:
        return json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, OverflowError) as exc:
        raise ValueError("synthetic evidence bundle is not JSON serializable") from exc


def _diagnostic_fixture() -> tuple[dict[str, object], ...]:
    from quantum_space_agi.ml.error_selection_diagnostics import (
        create_synthetic_error_diagnostic_fixture,
    )

    return create_synthetic_error_diagnostic_fixture()


def _validate_baseline_result(
    rows: tuple[dict[str, object], ...],
    validation: DatasetValidationReport,
    baseline: SyntheticBaselineResult,
    experiment_id: str,
    seed: int,
) -> None:
    if type(baseline) is not SyntheticBaselineResult:
        raise ValueError("baseline runner returned an invalid result")
    if baseline.validation_report != validation:
        raise ValueError("baseline validation report differs from runner fixture")
    if not baseline.train_row_ids or not baseline.test_row_ids:
        raise ValueError("training and test partitions must both be non-empty")
    baseline_document = _parse_json(baseline.result_bytes, "baseline result")
    experiment = baseline_document.get("experiment")
    if (
        not isinstance(experiment, dict)
        or experiment.get("experiment_id") != experiment_id
    ):
        raise ValueError("baseline experiment ID does not match requested ID")
    if experiment.get("seed") != seed:
        raise ValueError("baseline seed does not match requested seed")
    split = experiment.get("split")
    if not isinstance(split, dict):
        raise ValueError("baseline split declaration is unavailable")
    if (
        tuple(split.get("train_row_ids", ())) != baseline.train_row_ids
        or tuple(split.get("test_row_ids", ())) != baseline.test_row_ids
    ):
        raise ValueError("baseline split IDs do not match split declaration")
    if tuple(item.row_id for item in baseline.predictions) != baseline.test_row_ids:
        raise ValueError("prediction IDs do not exactly match test IDs")
    train_rows = {
        cast(str, row[_ROW_ID_FIELD]): row
        for row in rows
        if row[_ROW_ID_FIELD] in set(baseline.train_row_ids)
    }
    expected_training_targets = tuple(
        float(cast(int | float, train_rows[row_id]["pl_bmasse"]))
        for row_id in baseline.train_row_ids
    )
    model = experiment.get("model")
    if not isinstance(model, dict) or tuple(model.get("training_targets", ())) != (
        expected_training_targets
    ):
        raise ValueError("model training targets do not match training rows only")
    model_configuration = model.get("configuration")
    if not isinstance(model_configuration, dict) or model_configuration.get(
        "fitted_value"
    ) != median(expected_training_targets):
        raise ValueError("median baseline is not fitted to training targets only")


def _require_pending_policy_states(configuration: dict[str, object]) -> None:
    task = configuration.get("research_task")
    policies = configuration.get("policies")
    split = configuration.get("identity_and_split")
    evaluation = configuration.get("model_evaluation")
    decisions: list[object] = []
    if isinstance(task, dict):
        decisions.append(task.get("decision"))
    if isinstance(policies, list):
        decisions.extend(
            item.get("decision") for item in policies if isinstance(item, dict)
        )
    if isinstance(split, dict):
        decisions.append(split.get("decision"))
    if isinstance(evaluation, dict):
        decisions.append(evaluation.get("decision"))
    if not decisions or any(
        not isinstance(item, dict) or item.get("status") != "PENDING_REVIEW"
        for item in decisions
    ):
        raise ValueError("synthetic run must preserve pending scientific decisions")


def _create_payloads(
    rows: tuple[dict[str, object], ...],
    validation: DatasetValidationReport,
    baseline: SyntheticBaselineResult,
    leakage: LeakageDiagnosticReport,
    error_diagnostics: ErrorSelectionDiagnosticReport,
    acquisition_readiness_bytes: bytes,
) -> tuple[SyntheticEvidencePayload, ...]:
    baseline_doc = _parse_json(baseline.result_bytes, "baseline result")
    excluded = [
        {
            "source_row_index": item.row_index,
            "row_id": rows[item.row_index][_ROW_ID_FIELD],
            "findings": [
                {
                    "field": finding.field,
                    "reason_code": finding.reason_code,
                    "original_value": finding.original_value,
                    "value_omitted": finding.value_omitted,
                }
                for finding in item.findings
            ],
        }
        for item in validation.excluded_rows
    ]
    validation_doc = {
        "policy_version": validation.policy_version,
        "input_row_count": validation.record_count,
        "mechanically_accepted_source_row_indices": list(
            validation.valid_record_indices
        ),
        "excluded_row_count": validation.excluded_row_count,
        "exclusion_ledger": excluded,
        "scientific_eligibility": "NOT_ASSESSED",
    }
    split_doc = {
        "method": "seeded_random_row_split_synthetic_only",
        "train_row_ids": list(baseline.train_row_ids),
        "test_row_ids": list(baseline.test_row_ids),
        "assignment_status": "ASSIGNMENTS_EXIST_FOR_SYNTHETIC_SMOKE_TEST",
        "scientific_policy_status": "PENDING_REVIEW",
    }
    experiment_doc = cast(dict[str, object], baseline_doc["experiment"])
    model_doc = cast(dict[str, object], experiment_doc["model"])
    predictions_doc = baseline_doc["predictions"]
    metrics_doc = baseline_doc["metrics"]
    fixture_doc = {
        "fixture_id": SYNTHETIC_FIXTURE_ID,
        "source": "create_synthetic_error_diagnostic_fixture",
        "record_count": len(rows),
        "row_ids": [row[_ROW_ID_FIELD] for row in rows],
        "classification": "synthetic software fixture only",
    }
    payload_documents: tuple[tuple[str, object], ...] = (
        (
            "synthetic-output/arc08-experiment-configuration.json",
            baseline.configuration_bytes,
        ),
        (
            "synthetic-output/arc08-experiment-manifest.json",
            baseline.manifest_bytes,
        ),
        (
            "synthetic-output/arc08-synthetic-baseline-result.json",
            baseline.result_bytes,
        ),
        ("fixture_metadata.json", fixture_doc),
        ("validation_report.json", validation_doc),
        ("exclusion_ledger.json", excluded),
        ("split.json", split_doc),
        ("model.json", model_doc),
        ("predictions.json", predictions_doc),
        ("evaluation_metrics.json", metrics_doc),
        ("leakage_diagnostics.json", serialize_leakage_diagnostics(leakage)),
        (
            "error_selection_diagnostics.json",
            serialize_error_selection_diagnostics(error_diagnostics),
        ),
        ("acquisition_readiness.json", acquisition_readiness_bytes),
    )
    payloads: list[SyntheticEvidencePayload] = []
    for name, document in payload_documents:
        raw_bytes = document if type(document) is bytes else _canonical_json(document)
        payloads.append(
            SyntheticEvidencePayload(
                name=name,
                media_type="application/json",
                synthetic_designation="synthetic-only; not NASA evidence",
                payload_bytes=raw_bytes,
                byte_length=len(raw_bytes),
                sha256=hashlib.sha256(raw_bytes).hexdigest(),
            )
        )
    return tuple(sorted(payloads, key=lambda item: item.name))


def _canonical_json(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, OverflowError) as exc:
        raise ValueError("evidence payload is not canonical JSON") from exc


def _parse_json(raw_bytes: bytes, name: str) -> dict[str, object]:
    try:
        parsed = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{name} is not valid UTF-8 JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{name} must be a JSON object")
    return cast(dict[str, object], parsed)
