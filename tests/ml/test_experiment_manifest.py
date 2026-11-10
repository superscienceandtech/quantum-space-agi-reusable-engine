"""Synthetic contract tests for portable experiment configurations/manifests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError, replace

import pytest

from quantum_space_agi.ml import (
    ExperimentConfiguration as PublicExperimentConfiguration,
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
    IdentityAndSplit,
    ModelEvaluation,
    NamedSeed,
    OutputArtifact,
    PolicyDeclaration,
    ResearchTask,
    create_experiment_manifest,
    experiment_configuration_sha256,
    serialize_experiment_configuration,
    serialize_experiment_manifest,
    validate_experiment_manifest,
)


def pending_decision() -> DecisionDeclaration:
    return DecisionDeclaration(
        DecisionStatus.PENDING_REVIEW,
        rationale="Awaiting an explicit project review.",
    )


def valid_configuration(
    description: str = "synthetic fixture",
) -> ExperimentConfiguration:
    snapshot_sha = hashlib.sha256(b"synthetic snapshot").hexdigest()
    snapshot = ArtifactReference("data/raw/snapshot.vot", snapshot_sha)
    policies = tuple(
        PolicyDeclaration(policy_id, None, pending_decision())
        for policy_id in POLICY_IDS
    )
    task = ResearchTask(
        objective=None,
        target=None,
        features=(),
        inference_description=None,
        decision=pending_decision(),
    )
    dataset = DatasetDeclaration(
        source_identity="NASA Exoplanet Archive (proposed source)",
        source_table="ps",
        query_artifact=ArtifactReference("queries/candidate.adql"),
        raw_snapshot_artifact=snapshot,
        schema_artifact=ArtifactReference("schemas/ps-columns.json"),
        extraction_metadata_artifact=None,
        dataset_version=None,
    )
    split = IdentityAndSplit(
        identity_fields=("pl_name", "hostname", "pl_refname"),
        duplicate_policy=None,
        grouping_objective=None,
        grouping_fields=(),
        split_strategy=None,
        train_fraction=None,
        validation_fraction=None,
        test_fraction=None,
        seed=None,
        ordering_strategy=None,
        leakage_constraints=(),
        decision=pending_decision(),
    )
    model = ModelEvaluation(
        baseline_model_identifier=None,
        optional_model_identifiers=(),
        preprocessing=None,
        primary_metric=None,
        secondary_metrics=(),
        evaluation_protocol=None,
        acceptance_criteria_reference=None,
        decision=pending_decision(),
    )
    environment = ExecutionEnvironment(
        python_version="3.12.3",
        lockfile_reference=ArtifactReference("requirements/requirements.lock"),
        lockfile_sha256="a" * 64,
        platform="linux-x86_64",
        repository_commit="e35c9d5",
        branch="arc/08-ai-ml",
        random_seeds=(NamedSeed("split", 17),),
        execution_command=("python", "-m", "quantum_space_agi.ml.run_experiment"),
        entry_point=ArtifactReference("src/quantum_space_agi/ml/run_experiment.py"),
    )
    return ExperimentConfiguration(
        experiment_id="arc08-exploratory-mass-radius",
        schema_version=EXPERIMENT_CONFIGURATION_SCHEMA_VERSION,
        description=description,
        experiment_type="exploratory_baseline",
        lifecycle=ExperimentLifecycle.DRAFT,
        created_at=None,
        research_task=task,
        dataset=dataset,
        policies=policies,
        identity_and_split=split,
        model_evaluation=model,
        environment=environment,
        output_artifacts=(
            OutputArtifact(
                "evidence_report", ArtifactReference("reports/evidence.json")
            ),
        ),
    )


def test_valid_configuration_keeps_scientific_decisions_pending() -> None:
    configuration = valid_configuration()
    document = json.loads(serialize_experiment_configuration(configuration))

    assert PublicExperimentConfiguration is ExperimentConfiguration
    assert configuration.research_task.decision.status is DecisionStatus.PENDING_REVIEW
    assert all(
        policy.decision.status is DecisionStatus.PENDING_REVIEW
        for policy in configuration.policies
    )
    assert document["schema_version"] == EXPERIMENT_CONFIGURATION_SCHEMA_VERSION
    assert (
        document["dataset"]["raw_snapshot_artifact"]["sha256"]
        == hashlib.sha256(b"synthetic snapshot").hexdigest()
    )


def test_explicit_approval_metadata_is_required_and_only_declared() -> None:
    with pytest.raises(ExperimentConfigurationError, match="APPROVED requires"):
        DecisionDeclaration(DecisionStatus.APPROVED)

    declared = DecisionDeclaration(
        DecisionStatus.APPROVED,
        evidence_references=(ArtifactReference("approvals/task-review.md"),),
        authority="declared project reviewer",
    )
    assert declared.status is DecisionStatus.APPROVED
    assert declared.evidence_references[0].sha256 is None


def test_lockfile_checksum_declarations_must_agree_when_both_are_present() -> None:
    environment = valid_configuration().environment
    matching_checksum = "b" * 64

    matching = replace(
        environment,
        lockfile_reference=ArtifactReference(
            "requirements/requirements.lock", matching_checksum
        ),
        lockfile_sha256=matching_checksum,
    )
    assert matching.lockfile_reference is not None
    assert matching.lockfile_reference.sha256 == matching_checksum
    assert matching.lockfile_sha256 == matching_checksum

    with pytest.raises(ExperimentConfigurationError, match="conflicts"):
        replace(
            environment,
            lockfile_reference=ArtifactReference(
                "requirements/requirements.lock", "a" * 64
            ),
            lockfile_sha256="b" * 64,
        )


def test_lockfile_checksum_fields_may_both_be_absent() -> None:
    environment = replace(
        valid_configuration().environment,
        lockfile_reference=ArtifactReference("requirements/requirements.lock"),
        lockfile_sha256=None,
    )

    assert environment.lockfile_reference is not None
    assert environment.lockfile_reference.sha256 is None
    assert environment.lockfile_sha256 is None


def test_lockfile_reference_without_embedded_hash_keeps_legacy_valid_form() -> None:
    environment = valid_configuration().environment

    assert environment.lockfile_reference == ArtifactReference(
        "requirements/requirements.lock"
    )
    assert environment.lockfile_sha256 == "a" * 64


@pytest.mark.parametrize(
    "text",
    (
        "/home/user/project/file.csv",
        "Saved from /home/user/project/file.csv for review",
        r"C:\Users\user\project\file.csv",
        r"UNC location \\server\share\file.csv",
    ),
)
def test_free_text_rejects_obvious_absolute_local_paths(text: str) -> None:
    with pytest.raises(
        ExperimentConfigurationError, match="absolute local filesystem path"
    ):
        replace(valid_configuration(), description=text)


def test_free_text_accepts_scientific_slashes_urls_and_backslash_notation() -> None:
    text = (
        r"Mass/radius and x/y relationships; https://archive.example.org/table/ps; "
        r"LaTeX \alpha/\beta; package scikit-learn"
    )

    configuration = replace(valid_configuration(), description=text)

    assert configuration.description == text


def test_absolute_path_check_applies_to_nested_free_text_fields() -> None:
    with pytest.raises(
        ExperimentConfigurationError, match="absolute local filesystem path"
    ):
        DecisionDeclaration(
            DecisionStatus.PENDING_REVIEW,
            rationale=r"Review notes stored at \\server\share\review.md",
        )
    with pytest.raises(
        ExperimentConfigurationError, match="absolute local filesystem path"
    ):
        PolicyDeclaration(
            "cohort",
            "Query file: /home/user/arc08/query.adql",
            pending_decision(),
        )


@pytest.mark.parametrize(
    "path",
    (
        "/home/analyst/data.vot",
        "C:\\Users\\analyst\\data.vot",
        "../secret",
        "a/../b",
        "",
    ),
)
def test_artifact_references_reject_nonportable_paths(path: str) -> None:
    with pytest.raises(ExperimentConfigurationError, match="artifact path"):
        ArtifactReference(path)


def test_invalid_checksums_versions_and_configuration_shapes_are_rejected() -> None:
    with pytest.raises(TypeError):
        ExperimentConfiguration()  # type: ignore[call-arg]
    with pytest.raises(ExperimentConfigurationError, match="lowercase SHA-256"):
        ArtifactReference("data/snapshot.vot", "G" * 64)
    with pytest.raises(ExperimentConfigurationError, match="unsupported configuration"):
        replace(
            valid_configuration(), schema_version="arc08-experiment-configuration/99"
        )
    with pytest.raises(ExperimentConfigurationError, match="every version-one policy"):
        replace(valid_configuration(), policies=valid_configuration().policies[:-1])
    with pytest.raises(ExperimentConfigurationError, match="immutable"):
        replace(valid_configuration(), output_artifacts=[])


def test_configuration_json_and_hash_are_deterministic_and_sensitive_to_changes() -> (
    None
):
    first = valid_configuration()
    same = valid_configuration()
    changed = valid_configuration("changed declaration")
    first_bytes = serialize_experiment_configuration(first)

    assert first_bytes == serialize_experiment_configuration(same)
    assert (
        experiment_configuration_sha256(first)
        == hashlib.sha256(first_bytes).hexdigest()
    )
    assert experiment_configuration_sha256(first) != experiment_configuration_sha256(
        changed
    )
    decoded = json.loads(first_bytes)
    assert (
        json.dumps(
            decoded,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        == first_bytes
    )


def test_configuration_is_immutable_and_serialization_does_not_mutate_it() -> None:
    configuration = valid_configuration()
    before = serialize_experiment_configuration(configuration)

    with pytest.raises(FrozenInstanceError):
        configuration.description = "changed"  # type: ignore[misc]

    assert serialize_experiment_configuration(configuration) == before
    assert type(configuration.policies) is tuple
    assert type(configuration.output_artifacts) is tuple


def test_manifest_links_configuration_snapshot_environment_and_outputs() -> None:
    configuration = valid_configuration()
    manifest = create_experiment_manifest(configuration, "experiments/config.json")

    validate_experiment_manifest(manifest, configuration)
    raw = serialize_experiment_manifest(manifest, configuration)
    decoded = json.loads(raw)
    assert decoded["schema_version"] == EXPERIMENT_MANIFEST_SCHEMA_VERSION
    assert decoded["configuration_sha256"] == experiment_configuration_sha256(
        configuration
    )
    assert (
        decoded["configuration_reference"]["sha256"] == decoded["configuration_sha256"]
    )
    assert (
        decoded["source_snapshot_reference"]
        == json.loads(serialize_experiment_configuration(configuration))["dataset"][
            "raw_snapshot_artifact"
        ]
    )
    assert decoded["environment"]["repository_commit"] == "e35c9d5"


def test_manifest_rejects_inconsistent_configuration_and_unsupported_schema() -> None:
    configuration = valid_configuration()
    manifest = create_experiment_manifest(configuration, "experiments/config.json")
    with pytest.raises(ExperimentConfigurationError, match="checksum does not match"):
        validate_experiment_manifest(manifest, valid_configuration("other config"))
    with pytest.raises(ExperimentConfigurationError, match="unsupported manifest"):
        replace(manifest, schema_version="arc08-experiment-manifest/7")
    with pytest.raises(ExperimentConfigurationError, match="lowercase SHA-256"):
        replace(manifest, configuration_sha256="not-a-checksum")


def test_contradictory_approved_fields_and_invalid_numeric_values_are_rejected() -> (
    None
):
    approved = DecisionDeclaration(
        DecisionStatus.APPROVED,
        evidence_references=(ArtifactReference("approvals/task.md"),),
        authority="declared reviewer",
    )
    with pytest.raises(ExperimentConfigurationError, match="APPROVED research task"):
        ResearchTask(None, None, (), None, approved)
    with pytest.raises(ExperimentConfigurationError, match="non-negative integer"):
        NamedSeed("split", True)  # type: ignore[arg-type]
    with pytest.raises(ExperimentConfigurationError, match="finite floats"):
        replace(
            valid_configuration().identity_and_split,
            train_fraction=float("nan"),
        )


def test_duplicate_split_policy_statuses_cannot_contradict() -> None:
    configuration = valid_configuration()
    policies = tuple(
        replace(
            policy,
            value="Proposed host-disjoint split policy",
            decision=DecisionDeclaration(DecisionStatus.PROPOSED),
        )
        if policy.policy_id == "split_policy"
        else policy
        for policy in configuration.policies
    )

    with pytest.raises(ExperimentConfigurationError, match="status conflicts"):
        replace(configuration, policies=policies)
