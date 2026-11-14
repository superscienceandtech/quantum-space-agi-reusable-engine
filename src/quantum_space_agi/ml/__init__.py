"""AI/ML utilities for the reusable engineering package."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from quantum_space_agi.ml.acquisition_readiness import (
    PREREQUISITE_DEFINITIONS,
    AcquisitionReadinessAssessment,
    AcquisitionReadinessError,
    AcquisitionReadinessStatus,
    EvidenceKind,
    EvidenceReference,
    EvidenceReferenceAvailability,
    EvidenceVerificationStatus,
    PrerequisiteDecision,
    PrerequisiteResult,
    PrerequisiteStatus,
    assess_acquisition_readiness,
    assess_current_repository_readiness,
    serialize_acquisition_readiness,
)
from quantum_space_agi.ml.dataset_ingestion import (
    DatasetIngestionError,
    DatasetIngestionResult,
    IngestionManifest,
    IngestionMetadata,
    ingest_votable_payload,
    serialize_ingestion_manifest,
)
from quantum_space_agi.ml.dataset_preparation import (
    DatasetPreparationError,
    PreparedRegressionDataset,
    PreparedRegressionRecord,
    prepare_regression_dataset,
)
from quantum_space_agi.ml.dataset_validation import (
    DatasetValidationReport,
    ExcludedRow,
    ValidationFinding,
    validate_baseline_dataset,
    validate_baseline_records,
)
from quantum_space_agi.ml.experiment_manifest import (
    EXPERIMENT_CONFIGURATION_SCHEMA_VERSION,
    EXPERIMENT_MANIFEST_SCHEMA_VERSION,
    POLICY_IDS,
    ArtifactReference,
    DatasetDeclaration,
    DecisionDeclaration,
    DecisionStatus,
    ExecutionEnvironment,
    ExperimentConfiguration,
    ExperimentConfigurationError,
    ExperimentLifecycle,
    ExperimentManifest,
    IdentityAndSplit,
    ModelEvaluation,
    NamedSeed,
    OutputArtifact,
    PolicyDeclaration,
    ResearchTask,
    VariableDeclaration,
    create_experiment_manifest,
    experiment_configuration_sha256,
    serialize_experiment_configuration,
    serialize_experiment_manifest,
    validate_experiment_manifest,
)
from quantum_space_agi.ml.group_splitter import (
    GroupSplitError,
    GroupSplitResult,
    HostPartitionAssignment,
    PartitionSummary,
    SplitConfiguration,
    split_by_host,
)
from quantum_space_agi.ml.identity_diagnostics import (
    ComponentPartitionOverlap,
    ConnectedComponent,
    GroupingFeasibility,
    HostGroup,
    IdentityFieldDiagnostics,
    IdentityGroupingReport,
    LeakageAuditReport,
    PartitionIdentityOverlap,
    RepeatedIdentityTuple,
    RepeatedIdentityValue,
    audit_partition_assignments,
    diagnose_identity_groups,
)
from quantum_space_agi.ml.model_evaluation import (
    NumericRegressionModel,
    RegressionEvaluationError,
    RegressionEvaluationResult,
    RegressionMetric,
    RegressionMetrics,
    RegressionPrediction,
    calculate_regression_metrics,
    evaluate_regression_model,
)
from quantum_space_agi.ml.preprocessing import (
    FieldConversion,
    PreprocessingError,
    preprocess_dataset,
)
from quantum_space_agi.ml.regression_workflow import (
    RegressionWorkflowError,
    RegressionWorkflowResult,
    prepare_and_evaluate_regression,
)
from quantum_space_agi.ml.snapshot_artifact import (
    SnapshotArtifactError,
    SnapshotArtifactManifest,
    SnapshotArtifactVerification,
    SnapshotArtifactWriteResult,
    deserialize_snapshot_manifest,
    serialize_snapshot_manifest,
    verify_snapshot_artifact,
    write_snapshot_artifact,
)
from quantum_space_agi.ml.verified_ingestion import (
    VerifiedSnapshotIngestionResult,
    ingest_verified_snapshot,
)
from quantum_space_agi.ml.votable_validation import (
    VOTableField,
    VOTableValidationError,
    VOTableValidationResult,
    validate_tap_votable,
)

if TYPE_CHECKING:
    from quantum_space_agi.ml.mission_configuration import (
        EducationalMissionConfiguration,
    )
    from quantum_space_agi.ml.mission_evaluator import (
        ConstraintViolation,
        EducationalMissionResult,
        ResourceTotals,
        evaluate_educational_mission,
        serialize_educational_mission_result,
    )

_LAZY_MISSION_EXPORTS = {
    "EducationalMissionConfiguration": "mission_configuration",
    "ConstraintViolation": "mission_evaluator",
    "EducationalMissionResult": "mission_evaluator",
    "ResourceTotals": "mission_evaluator",
    "evaluate_educational_mission": "mission_evaluator",
    "serialize_educational_mission_result": "mission_evaluator",
}


def __getattr__(name: str) -> Any:
    """Load separate educational evaluator exports only when requested."""
    module_name = _LAZY_MISSION_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(f"{__name__}.{module_name}")
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_LAZY_MISSION_EXPORTS))


__all__ = [
    "AcquisitionReadinessAssessment",
    "AcquisitionReadinessError",
    "AcquisitionReadinessStatus",
    "EducationalMissionConfiguration",
    "EducationalMissionResult",
    "FieldConversion",
    "PreprocessingError",
    "SnapshotArtifactError",
    "SnapshotArtifactManifest",
    "SnapshotArtifactVerification",
    "SnapshotArtifactWriteResult",
    "VerifiedSnapshotIngestionResult",
    "ConstraintViolation",
    "ResourceTotals",
    "EvidenceKind",
    "EvidenceReference",
    "EvidenceReferenceAvailability",
    "EvidenceVerificationStatus",
    "EXPERIMENT_CONFIGURATION_SCHEMA_VERSION",
    "EXPERIMENT_MANIFEST_SCHEMA_VERSION",
    "POLICY_IDS",
    "ArtifactReference",
    "DatasetDeclaration",
    "DecisionDeclaration",
    "DecisionStatus",
    "ExecutionEnvironment",
    "ExperimentConfiguration",
    "ExperimentConfigurationError",
    "ExperimentLifecycle",
    "ExperimentManifest",
    "IdentityAndSplit",
    "ModelEvaluation",
    "NamedSeed",
    "OutputArtifact",
    "PolicyDeclaration",
    "ResearchTask",
    "VariableDeclaration",
    "create_experiment_manifest",
    "experiment_configuration_sha256",
    "serialize_experiment_configuration",
    "serialize_experiment_manifest",
    "validate_experiment_manifest",
    "PREREQUISITE_DEFINITIONS",
    "PrerequisiteDecision",
    "PrerequisiteResult",
    "PrerequisiteStatus",
    "DatasetValidationReport",
    "DatasetPreparationError",
    "PreparedRegressionDataset",
    "PreparedRegressionRecord",
    "prepare_regression_dataset",
    "NumericRegressionModel",
    "RegressionEvaluationError",
    "RegressionEvaluationResult",
    "RegressionMetric",
    "RegressionMetrics",
    "RegressionPrediction",
    "calculate_regression_metrics",
    "evaluate_regression_model",
    "RegressionWorkflowError",
    "RegressionWorkflowResult",
    "prepare_and_evaluate_regression",
    "DatasetIngestionError",
    "DatasetIngestionResult",
    "IngestionManifest",
    "IngestionMetadata",
    "ExcludedRow",
    "ValidationFinding",
    "evaluate_educational_mission",
    "assess_acquisition_readiness",
    "assess_current_repository_readiness",
    "serialize_acquisition_readiness",
    "validate_baseline_dataset",
    "validate_baseline_records",
    "ingest_votable_payload",
    "serialize_ingestion_manifest",
    "ComponentPartitionOverlap",
    "ConnectedComponent",
    "GroupingFeasibility",
    "HostGroup",
    "IdentityFieldDiagnostics",
    "IdentityGroupingReport",
    "LeakageAuditReport",
    "PartitionIdentityOverlap",
    "RepeatedIdentityTuple",
    "RepeatedIdentityValue",
    "audit_partition_assignments",
    "diagnose_identity_groups",
    "GroupSplitError",
    "GroupSplitResult",
    "HostPartitionAssignment",
    "PartitionSummary",
    "SplitConfiguration",
    "split_by_host",
    "preprocess_dataset",
    "deserialize_snapshot_manifest",
    "serialize_snapshot_manifest",
    "verify_snapshot_artifact",
    "write_snapshot_artifact",
    "ingest_verified_snapshot",
    "serialize_educational_mission_result",
    "VOTableValidationError",
    "VOTableField",
    "VOTableValidationResult",
    "validate_tap_votable",
]
