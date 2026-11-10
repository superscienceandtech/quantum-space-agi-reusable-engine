"""Portable, deterministic declarations for future ARC-08 experiments.

This module records caller-declared configuration and evidence links. It does
not acquire data, authenticate approvals, or establish scientific validity.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any

EXPERIMENT_CONFIGURATION_SCHEMA_VERSION = "arc08-experiment-configuration/1"
EXPERIMENT_MANIFEST_SCHEMA_VERSION = "arc08-experiment-manifest/1"
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{7,64}$")
_POSIX_ABSOLUTE_PATH_PATTERN = re.compile(r"(?<![\w./])/(?:[^/\s]+/)+[^/\s,;)}\]]+")
_WINDOWS_ABSOLUTE_PATH_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])[A-Za-z]:[\\/][^\s,;)}\]]+"
)
_UNC_ABSOLUTE_PATH_PATTERN = re.compile(r"(?<![\w/])\\\\[^\\/\s]+[\\/][^\s,;)}\]]+")

POLICY_IDS = (
    "cohort",
    "inclusion_exclusion",
    "missing_values",
    "non_positive_values",
    "limit_codes",
    "uncertainty",
    "controversy_solution_status",
    "identity_duplicates",
    "split_policy",
    "evaluation_metrics_acceptance",
    "scientific_claims",
    "data_access_retention",
)


class ExperimentConfigurationError(ValueError):
    """Experiment configuration or manifest is malformed or inconsistent."""


class DecisionStatus(StrEnum):
    """Declared review state; APPROVED is never independently authenticated."""

    PROPOSED = "PROPOSED"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ExperimentLifecycle(StrEnum):
    """Administrative lifecycle label, not scientific acceptance."""

    DRAFT = "DRAFT"
    PLANNED = "PLANNED"
    EXECUTED = "EXECUTED"


def _text(name: str, value: object, *, optional: bool = False) -> None:
    if optional and value is None:
        return
    if type(value) is not str or not value.strip():
        raise ExperimentConfigurationError(f"{name} must be a non-empty string")
    if _contains_absolute_local_path(value):
        raise ExperimentConfigurationError(
            f"{name} must not contain an absolute local filesystem path"
        )


def _contains_absolute_local_path(value: str) -> bool:
    """Detect obvious absolute path tokens without treating slash prose as paths."""
    return any(
        pattern.search(value) is not None
        for pattern in (
            _POSIX_ABSOLUTE_PATH_PATTERN,
            _WINDOWS_ABSOLUTE_PATH_PATTERN,
            _UNC_ABSOLUTE_PATH_PATTERN,
        )
    )


def _sha256(name: str, value: object, *, optional: bool = False) -> None:
    if optional and value is None:
        return
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ExperimentConfigurationError(f"{name} must be lowercase SHA-256")


def _tuple_of_text(name: str, values: object, *, allow_empty: bool = True) -> None:
    if type(values) is not tuple or any(type(value) is not str for value in values):
        raise ExperimentConfigurationError(f"{name} must be a tuple of strings")
    if not allow_empty and not values:
        raise ExperimentConfigurationError(f"{name} must not be empty")
    for value in values:
        _text(f"{name} value", value)


def _artifact_reference(name: str, value: object) -> None:
    if type(value) is not ArtifactReference:
        raise ExperimentConfigurationError(f"{name} must be an ArtifactReference")


@dataclass(frozen=True, slots=True)
class ArtifactReference:
    """Portable, checkout-relative artifact pointer and optional content hash."""

    path: str
    sha256: str | None = None

    def __post_init__(self) -> None:
        _text("artifact path", self.path)
        path = PurePosixPath(self.path)
        if (
            path.is_absolute()
            or PureWindowsPath(self.path).is_absolute()
            or "\\" in self.path
            or ":" in self.path
            or any(part in {"", ".", ".."} for part in self.path.split("/"))
        ):
            raise ExperimentConfigurationError(
                "artifact path must be a portable relative POSIX path"
            )
        _sha256("artifact sha256", self.sha256, optional=True)


@dataclass(frozen=True, slots=True)
class DecisionDeclaration:
    """Explicit policy state and caller-declared review references."""

    status: DecisionStatus
    evidence_references: tuple[ArtifactReference, ...] = ()
    authority: str | None = None
    rationale: str | None = None

    def __post_init__(self) -> None:
        if type(self.status) is not DecisionStatus:
            raise ExperimentConfigurationError("decision status is invalid")
        if type(self.evidence_references) is not tuple or any(
            type(reference) is not ArtifactReference
            for reference in self.evidence_references
        ):
            raise ExperimentConfigurationError(
                "decision evidence_references must be an immutable tuple"
            )
        if self.authority is not None:
            _text("decision authority", self.authority)
        if self.rationale is not None:
            _text("decision rationale", self.rationale)
        if self.status is DecisionStatus.APPROVED and (
            not self.evidence_references or self.authority is None
        ):
            raise ExperimentConfigurationError(
                "APPROVED requires declared evidence references and an authority"
            )
        if self.status is DecisionStatus.NOT_APPLICABLE and self.rationale is None:
            raise ExperimentConfigurationError(
                "NOT_APPLICABLE requires an explicit rationale"
            )


@dataclass(frozen=True, slots=True)
class VariableDeclaration:
    """Declared feature or target field and its unit, if known."""

    field: str
    unit: str | None

    def __post_init__(self) -> None:
        _text("variable field", self.field)
        _text("variable unit", self.unit, optional=True)


@dataclass(frozen=True, slots=True)
class ResearchTask:
    """Prediction objective and its explicitly declared review state."""

    objective: str | None
    target: VariableDeclaration | None
    features: tuple[VariableDeclaration, ...]
    inference_description: str | None
    decision: DecisionDeclaration

    def __post_init__(self) -> None:
        _text("research objective", self.objective, optional=True)
        if self.target is not None and type(self.target) is not VariableDeclaration:
            raise ExperimentConfigurationError("research target is invalid")
        _text("inference description", self.inference_description, optional=True)
        if type(self.features) is not tuple or any(
            type(feature) is not VariableDeclaration for feature in self.features
        ):
            raise ExperimentConfigurationError("features must be a tuple of variables")
        feature_names = tuple(feature.field for feature in self.features)
        if len(set(feature_names)) != len(feature_names):
            raise ExperimentConfigurationError("feature fields must be unique")
        if self.target is not None and self.target.field in feature_names:
            raise ExperimentConfigurationError("target cannot also be a feature")
        if type(self.decision) is not DecisionDeclaration:
            raise ExperimentConfigurationError("research task decision is invalid")
        if self.decision.status is DecisionStatus.APPROVED and (
            self.objective is None
            or self.target is None
            or not self.features
            or self.inference_description is None
        ):
            raise ExperimentConfigurationError(
                "APPROVED research task requires objective, target, features, "
                "and inference description"
            )


@dataclass(frozen=True, slots=True)
class DatasetDeclaration:
    """Source and portable references for a future dataset or snapshot."""

    source_identity: str | None
    source_table: str | None
    query_artifact: ArtifactReference | None
    raw_snapshot_artifact: ArtifactReference | None
    schema_artifact: ArtifactReference | None
    extraction_metadata_artifact: ArtifactReference | None
    dataset_version: str | None

    def __post_init__(self) -> None:
        for name in ("source_identity", "source_table", "dataset_version"):
            _text(name, getattr(self, name), optional=True)
        for name in (
            "query_artifact",
            "raw_snapshot_artifact",
            "schema_artifact",
            "extraction_metadata_artifact",
        ):
            reference = getattr(self, name)
            if reference is not None:
                _artifact_reference(name, reference)


@dataclass(frozen=True, slots=True)
class PolicyDeclaration:
    """A named policy value with an explicit review state and references."""

    policy_id: str
    value: str | None
    decision: DecisionDeclaration
    references: tuple[ArtifactReference, ...] = ()

    def __post_init__(self) -> None:
        _text("policy_id", self.policy_id)
        if self.policy_id not in POLICY_IDS:
            raise ExperimentConfigurationError(
                f"unsupported policy id: {self.policy_id}"
            )
        _text("policy value", self.value, optional=True)
        if type(self.decision) is not DecisionDeclaration:
            raise ExperimentConfigurationError("policy decision is invalid")
        if type(self.references) is not tuple or any(
            type(reference) is not ArtifactReference for reference in self.references
        ):
            raise ExperimentConfigurationError("policy references must be immutable")
        if self.decision.status is DecisionStatus.APPROVED and self.value is None:
            raise ExperimentConfigurationError(
                "APPROVED policy requires a declared value"
            )
        if self.decision.status is DecisionStatus.PROPOSED and self.value is None:
            raise ExperimentConfigurationError(
                "PROPOSED policy requires a proposed value"
            )
        if (
            self.decision.status is DecisionStatus.NOT_APPLICABLE
            and self.value is not None
        ):
            raise ExperimentConfigurationError(
                "NOT_APPLICABLE policy cannot have a value"
            )


@dataclass(frozen=True, slots=True)
class NamedSeed:
    """Named, reproducible integer random seed."""

    name: str
    value: int

    def __post_init__(self) -> None:
        _text("seed name", self.name)
        if type(self.value) is not int or self.value < 0:
            raise ExperimentConfigurationError(
                "seed value must be a non-negative integer"
            )


@dataclass(frozen=True, slots=True)
class IdentityAndSplit:
    """Identity, grouping and split declarations; no split is generated here."""

    identity_fields: tuple[str, ...]
    duplicate_policy: str | None
    grouping_objective: str | None
    grouping_fields: tuple[str, ...]
    split_strategy: str | None
    train_fraction: float | None
    validation_fraction: float | None
    test_fraction: float | None
    seed: int | None
    ordering_strategy: str | None
    leakage_constraints: tuple[str, ...]
    decision: DecisionDeclaration

    def __post_init__(self) -> None:
        _tuple_of_text("identity_fields", self.identity_fields)
        _tuple_of_text("grouping_fields", self.grouping_fields)
        _tuple_of_text("leakage_constraints", self.leakage_constraints)
        for name in (
            "duplicate_policy",
            "grouping_objective",
            "split_strategy",
            "ordering_strategy",
        ):
            _text(name, getattr(self, name), optional=True)
        fractions = (self.train_fraction, self.validation_fraction, self.test_fraction)
        for fraction in fractions:
            if fraction is not None and (
                type(fraction) is not float
                or not math.isfinite(fraction)
                or not 0 <= fraction <= 1
            ):
                raise ExperimentConfigurationError(
                    "split fractions must be finite floats between zero and one"
                )
        if all(fraction is not None for fraction in fractions) and not math.isclose(
            sum(fraction for fraction in fractions if fraction is not None),
            1.0,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ExperimentConfigurationError("split fractions must sum to one")
        if self.seed is not None and (type(self.seed) is not int or self.seed < 0):
            raise ExperimentConfigurationError(
                "split seed must be a non-negative integer"
            )
        if type(self.decision) is not DecisionDeclaration:
            raise ExperimentConfigurationError("split decision is invalid")
        if self.decision.status is DecisionStatus.APPROVED and (
            not self.identity_fields
            or not self.grouping_objective
            or not self.grouping_fields
            or not self.split_strategy
            or any(fraction is None for fraction in fractions)
            or self.seed is None
            or not self.ordering_strategy
            or not self.leakage_constraints
        ):
            raise ExperimentConfigurationError(
                "APPROVED split policy requires complete grouping and split details"
            )


@dataclass(frozen=True, slots=True)
class ModelEvaluation:
    """Model identifiers, preprocessing and evaluation declarations."""

    baseline_model_identifier: str | None
    optional_model_identifiers: tuple[str, ...]
    preprocessing: str | None
    primary_metric: str | None
    secondary_metrics: tuple[str, ...]
    evaluation_protocol: str | None
    acceptance_criteria_reference: ArtifactReference | None
    decision: DecisionDeclaration

    def __post_init__(self) -> None:
        for name in (
            "baseline_model_identifier",
            "preprocessing",
            "primary_metric",
            "evaluation_protocol",
        ):
            _text(name, getattr(self, name), optional=True)
        _tuple_of_text("optional_model_identifiers", self.optional_model_identifiers)
        _tuple_of_text("secondary_metrics", self.secondary_metrics)
        if self.acceptance_criteria_reference is not None:
            _artifact_reference(
                "acceptance_criteria_reference", self.acceptance_criteria_reference
            )
        if type(self.decision) is not DecisionDeclaration:
            raise ExperimentConfigurationError("model/evaluation decision is invalid")
        if self.decision.status is DecisionStatus.APPROVED and (
            self.baseline_model_identifier is None
            or self.primary_metric is None
            or self.evaluation_protocol is None
        ):
            raise ExperimentConfigurationError(
                "APPROVED evaluation requires a baseline, primary metric, and protocol"
            )


@dataclass(frozen=True, slots=True)
class ExecutionEnvironment:
    """Portable environment record; machine-specific absolute paths are excluded."""

    python_version: str | None
    lockfile_reference: ArtifactReference | None
    lockfile_sha256: str | None
    platform: str | None
    repository_commit: str | None
    branch: str | None
    random_seeds: tuple[NamedSeed, ...]
    execution_command: tuple[str, ...] | None
    entry_point: ArtifactReference | None

    def __post_init__(self) -> None:
        for name in ("python_version", "platform", "branch"):
            _text(name, getattr(self, name), optional=True)
        if self.execution_command is not None:
            _tuple_of_text(
                "execution_command", self.execution_command, allow_empty=False
            )
            for argument in self.execution_command:
                path_argument = argument.split("=", maxsplit=1)[-1]
                if (
                    PurePosixPath(path_argument).is_absolute()
                    or PureWindowsPath(path_argument).is_absolute()
                ):
                    raise ExperimentConfigurationError(
                        "execution_command must not contain absolute machine paths"
                    )
        if self.repository_commit is not None and (
            type(self.repository_commit) is not str
            or _COMMIT_PATTERN.fullmatch(self.repository_commit) is None
        ):
            raise ExperimentConfigurationError(
                "repository_commit must be a hex commit id"
            )
        if self.lockfile_reference is not None:
            _artifact_reference("lockfile_reference", self.lockfile_reference)
        _sha256("lockfile_sha256", self.lockfile_sha256, optional=True)
        if self.lockfile_sha256 is not None and self.lockfile_reference is None:
            raise ExperimentConfigurationError(
                "lockfile checksum requires a lockfile reference"
            )
        if (
            self.lockfile_reference is not None
            and self.lockfile_reference.sha256 is not None
            and self.lockfile_sha256 is not None
            and self.lockfile_reference.sha256 != self.lockfile_sha256
        ):
            raise ExperimentConfigurationError(
                "lockfile reference checksum conflicts with lockfile_sha256"
            )
        if self.entry_point is not None:
            _artifact_reference("entry_point", self.entry_point)
        if type(self.random_seeds) is not tuple or any(
            type(seed) is not NamedSeed for seed in self.random_seeds
        ):
            raise ExperimentConfigurationError(
                "random_seeds must be an immutable tuple"
            )
        seed_names = tuple(seed.name for seed in self.random_seeds)
        if len(set(seed_names)) != len(seed_names):
            raise ExperimentConfigurationError("random seed names must be unique")


@dataclass(frozen=True, slots=True)
class OutputArtifact:
    """Named output/evidence artifact reference and optional checksum."""

    kind: str
    artifact: ArtifactReference

    def __post_init__(self) -> None:
        _text("output artifact kind", self.kind)
        _artifact_reference("output artifact", self.artifact)


@dataclass(frozen=True, slots=True)
class ExperimentConfiguration:
    """Immutable, versioned, portable declaration for one future experiment."""

    experiment_id: str
    schema_version: str
    description: str
    experiment_type: str
    lifecycle: ExperimentLifecycle
    created_at: str | None
    research_task: ResearchTask
    dataset: DatasetDeclaration
    policies: tuple[PolicyDeclaration, ...]
    identity_and_split: IdentityAndSplit
    model_evaluation: ModelEvaluation
    environment: ExecutionEnvironment
    output_artifacts: tuple[OutputArtifact, ...]

    def __post_init__(self) -> None:
        for name in ("experiment_id", "description", "experiment_type"):
            _text(name, getattr(self, name))
        _text("schema_version", self.schema_version)
        if self.schema_version != EXPERIMENT_CONFIGURATION_SCHEMA_VERSION:
            raise ExperimentConfigurationError(
                "unsupported configuration schema version"
            )
        if type(self.lifecycle) is not ExperimentLifecycle:
            raise ExperimentConfigurationError("experiment lifecycle is invalid")
        if self.created_at is not None:
            _text("created_at", self.created_at)
            try:
                timestamp = datetime.fromisoformat(
                    self.created_at.replace("Z", "+00:00")
                )
            except ValueError as exc:
                raise ExperimentConfigurationError(
                    "created_at must be ISO-8601"
                ) from exc
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ExperimentConfigurationError("created_at must include a timezone")
        if type(self.research_task) is not ResearchTask:
            raise ExperimentConfigurationError("research_task is invalid")
        if type(self.dataset) is not DatasetDeclaration:
            raise ExperimentConfigurationError("dataset is invalid")
        if type(self.policies) is not tuple or any(
            type(policy) is not PolicyDeclaration for policy in self.policies
        ):
            raise ExperimentConfigurationError("policies must be an immutable tuple")
        policy_ids = tuple(policy.policy_id for policy in self.policies)
        if len(set(policy_ids)) != len(policy_ids) or set(policy_ids) != set(
            POLICY_IDS
        ):
            raise ExperimentConfigurationError(
                "configuration must declare every version-one policy exactly once"
            )
        if type(self.identity_and_split) is not IdentityAndSplit:
            raise ExperimentConfigurationError("identity_and_split is invalid")
        if type(self.model_evaluation) is not ModelEvaluation:
            raise ExperimentConfigurationError("model_evaluation is invalid")
        if type(self.environment) is not ExecutionEnvironment:
            raise ExperimentConfigurationError("environment is invalid")
        policies_by_id = {policy.policy_id: policy for policy in self.policies}
        if (
            policies_by_id["split_policy"].decision.status
            is not self.identity_and_split.decision.status
        ):
            raise ExperimentConfigurationError(
                "split policy status conflicts with identity_and_split decision"
            )
        if (
            policies_by_id["evaluation_metrics_acceptance"].decision.status
            is not self.model_evaluation.decision.status
        ):
            raise ExperimentConfigurationError(
                "evaluation policy status conflicts with model_evaluation decision"
            )
        if type(self.output_artifacts) is not tuple or any(
            type(output) is not OutputArtifact for output in self.output_artifacts
        ):
            raise ExperimentConfigurationError("output_artifacts must be immutable")
        output_kinds = tuple(output.kind for output in self.output_artifacts)
        if len(set(output_kinds)) != len(output_kinds):
            raise ExperimentConfigurationError("output artifact kinds must be unique")


@dataclass(frozen=True, slots=True)
class ExperimentManifest:
    """Integrity links from canonical configuration to source and outputs."""

    schema_version: str
    experiment_id: str
    configuration_reference: ArtifactReference
    configuration_sha256: str
    source_snapshot_reference: ArtifactReference | None
    environment: ExecutionEnvironment
    output_artifacts: tuple[OutputArtifact, ...]

    def __post_init__(self) -> None:
        _text("manifest schema_version", self.schema_version)
        if self.schema_version != EXPERIMENT_MANIFEST_SCHEMA_VERSION:
            raise ExperimentConfigurationError("unsupported manifest schema version")
        _text("experiment_id", self.experiment_id)
        _artifact_reference("configuration_reference", self.configuration_reference)
        _sha256("configuration_sha256", self.configuration_sha256)
        if self.configuration_reference.sha256 != self.configuration_sha256:
            raise ExperimentConfigurationError(
                "configuration reference checksum does not match manifest checksum"
            )
        if self.source_snapshot_reference is not None:
            _artifact_reference(
                "source_snapshot_reference", self.source_snapshot_reference
            )
        if type(self.environment) is not ExecutionEnvironment:
            raise ExperimentConfigurationError("manifest environment is invalid")
        if type(self.output_artifacts) is not tuple or any(
            type(output) is not OutputArtifact for output in self.output_artifacts
        ):
            raise ExperimentConfigurationError("manifest outputs must be immutable")


def serialize_experiment_configuration(configuration: ExperimentConfiguration) -> bytes:
    """Return canonical compact UTF-8 JSON for a validated configuration."""
    if type(configuration) is not ExperimentConfiguration:
        raise ExperimentConfigurationError("configuration has an invalid type")
    return _canonical_json(configuration)


def experiment_configuration_sha256(configuration: ExperimentConfiguration) -> str:
    """Hash the exact canonical configuration bytes."""
    return hashlib.sha256(serialize_experiment_configuration(configuration)).hexdigest()


def create_experiment_manifest(
    configuration: ExperimentConfiguration,
    configuration_path: str,
) -> ExperimentManifest:
    """Create an integrity manifest using a portable configuration path.

    Checksums are calculated from canonical configuration bytes. Snapshot and
    output links are copied from the caller's configuration; nothing is read
    from the filesystem.
    """
    if type(configuration) is not ExperimentConfiguration:
        raise ExperimentConfigurationError("configuration has an invalid type")
    digest = experiment_configuration_sha256(configuration)
    return ExperimentManifest(
        schema_version=EXPERIMENT_MANIFEST_SCHEMA_VERSION,
        experiment_id=configuration.experiment_id,
        configuration_reference=ArtifactReference(configuration_path, digest),
        configuration_sha256=digest,
        source_snapshot_reference=configuration.dataset.raw_snapshot_artifact,
        environment=configuration.environment,
        output_artifacts=configuration.output_artifacts,
    )


def validate_experiment_manifest(
    manifest: ExperimentManifest,
    configuration: ExperimentConfiguration,
) -> None:
    """Check manifest links against the supplied immutable configuration."""
    if type(manifest) is not ExperimentManifest:
        raise ExperimentConfigurationError("manifest has an invalid type")
    if type(configuration) is not ExperimentConfiguration:
        raise ExperimentConfigurationError("configuration has an invalid type")
    if manifest.experiment_id != configuration.experiment_id:
        raise ExperimentConfigurationError("manifest experiment id does not match")
    if manifest.configuration_sha256 != experiment_configuration_sha256(configuration):
        raise ExperimentConfigurationError(
            "manifest configuration checksum does not match"
        )
    if (
        manifest.source_snapshot_reference
        != configuration.dataset.raw_snapshot_artifact
    ):
        raise ExperimentConfigurationError(
            "manifest source snapshot link does not match"
        )
    if manifest.environment != configuration.environment:
        raise ExperimentConfigurationError("manifest environment does not match")
    if manifest.output_artifacts != configuration.output_artifacts:
        raise ExperimentConfigurationError("manifest outputs do not match")


def serialize_experiment_manifest(
    manifest: ExperimentManifest,
    configuration: ExperimentConfiguration,
) -> bytes:
    """Validate configuration linkage, then serialize canonical manifest JSON."""
    validate_experiment_manifest(manifest, configuration)
    return _canonical_json(manifest)


def _canonical_json(value: object) -> bytes:
    try:
        return json.dumps(
            _json_value(value),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, OverflowError) as exc:
        raise ExperimentConfigurationError(
            "object cannot be serialized as JSON"
        ) from exc


def _json_value(value: object) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_json_value(item) for item in value]
    if value is None or type(value) in (str, int, float, bool):
        return value
    raise ExperimentConfigurationError(
        f"unsupported value in experiment document: {type(value).__name__}"
    )
