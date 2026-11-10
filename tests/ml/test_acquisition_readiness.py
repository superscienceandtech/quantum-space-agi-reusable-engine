import json
from dataclasses import replace
from pathlib import Path

import pytest

from quantum_space_agi.ml import EvidenceReferenceAvailability as PublicAvailability
from quantum_space_agi.ml.acquisition_readiness import (
    PREREQUISITE_DEFINITIONS,
    AcquisitionReadinessError,
    AcquisitionReadinessStatus,
    EvidenceKind,
    EvidenceReference,
    EvidenceReferenceAvailability,
    EvidenceVerificationStatus,
    PrerequisiteDecision,
    PrerequisiteResult,
    PrerequisiteStatus,
    _reference_availability,
    _reference_with_availability,
    _repository_root,
    assess_acquisition_readiness,
    assess_current_repository_readiness,
    serialize_acquisition_readiness,
)


def approved_decisions() -> tuple[PrerequisiteDecision, ...]:
    decisions: list[PrerequisiteDecision] = []
    for definition in PREREQUISITE_DEFINITIONS:
        evidence = tuple(
            EvidenceReference(kind, f"approval-record/{definition.prerequisite_id}")
            for kind in definition.required_evidence_kinds
        )
        decisions.append(
            PrerequisiteDecision(
                prerequisite_id=definition.prerequisite_id,
                status=PrerequisiteStatus.APPROVED,
                evidence=evidence,
                decision_authority="authorized project reviewer",
                explanation="Synthetic approval fixture for gate behavior.",
            )
        )
    return tuple(decisions)


def replace_decision(
    decisions: tuple[PrerequisiteDecision, ...],
    replacement: PrerequisiteDecision,
) -> tuple[PrerequisiteDecision, ...]:
    return tuple(
        replacement if item.prerequisite_id == replacement.prerequisite_id else item
        for item in decisions
    )


def test_caller_approvals_do_not_authenticate_or_make_gate_ready() -> None:
    decisions = approved_decisions()
    result = assess_acquisition_readiness(decisions)

    assert result.status is AcquisitionReadinessStatus.NOT_READY
    assert result.blocking_issues
    assert all(
        item.status is PrerequisiteStatus.BLOCKED
        for item in result.prerequisites
        if item.declared_status is PrerequisiteStatus.APPROVED
    )
    assert all(
        reference.verification_status
        is EvidenceVerificationStatus.DECLARED_NOT_AUTHENTICATED
        for item in result.prerequisites
        for reference in item.evidence
    )
    assert any(
        "not independently authenticated" in item for item in result.blocking_issues
    )
    assert all(item.status is PrerequisiteStatus.APPROVED for item in decisions)


def test_direct_result_rejects_declared_approval_with_pending_effective_status() -> (
    None
):
    pending = assess_acquisition_readiness().prerequisites[0]

    with pytest.raises(AcquisitionReadinessError, match="effectively BLOCKED"):
        PrerequisiteResult(
            prerequisite_id=pending.prerequisite_id,
            title=pending.title,
            status=PrerequisiteStatus.PENDING,
            declared_status=PrerequisiteStatus.APPROVED,
            evidence=pending.evidence,
            decision_authority="caller-declared authority",
            explanation=pending.explanation,
            blocks_acquisition=pending.blocks_acquisition,
            evidence_sufficient=pending.evidence_sufficient,
        )


def test_direct_result_accepts_declared_approval_only_as_blocked() -> None:
    assessed = assess_acquisition_readiness(approved_decisions())
    effective = next(
        item
        for item in assessed.prerequisites
        if item.declared_status is PrerequisiteStatus.APPROVED
    )

    constructed = PrerequisiteResult(
        prerequisite_id=effective.prerequisite_id,
        title=effective.title,
        status=PrerequisiteStatus.BLOCKED,
        declared_status=PrerequisiteStatus.APPROVED,
        evidence=effective.evidence,
        decision_authority=effective.decision_authority,
        explanation=effective.explanation,
        blocks_acquisition=effective.blocks_acquisition,
        evidence_sufficient=effective.evidence_sufficient,
    )

    assert constructed.status is PrerequisiteStatus.BLOCKED
    assert serialize_acquisition_readiness(assessed)


def test_serializer_rejects_result_mutated_to_contradictory_status() -> None:
    assessment = assess_acquisition_readiness(approved_decisions())
    result = next(
        item
        for item in assessment.prerequisites
        if item.declared_status is PrerequisiteStatus.APPROVED
    )
    object.__setattr__(result, "status", PrerequisiteStatus.PENDING)

    with pytest.raises(AcquisitionReadinessError, match="effectively BLOCKED"):
        serialize_acquisition_readiness(assessment)


def test_one_pending_mandatory_prerequisite_blocks_readiness() -> None:
    decisions = replace_decision(
        approved_decisions(),
        PrerequisiteDecision(
            "prediction_task",
            PrerequisiteStatus.PENDING,
            explanation="Scientific task approval is pending.",
        ),
    )

    result = assess_acquisition_readiness(decisions)

    assert result.status is AcquisitionReadinessStatus.NOT_READY
    assert any("prediction_task" in item for item in result.blocking_issues)


def test_one_blocked_prerequisite_blocks_readiness() -> None:
    decisions = replace_decision(
        approved_decisions(),
        PrerequisiteDecision(
            "limit_code_semantics",
            PrerequisiteStatus.BLOCKED,
            explanation="Authoritative semantics are unavailable.",
        ),
    )

    result = assess_acquisition_readiness(decisions)

    assert result.status is AcquisitionReadinessStatus.NOT_READY
    assert any("limit_code_semantics" in item for item in result.blocking_issues)


def test_missing_prerequisite_and_missing_evidence_fail_closed() -> None:
    missing_decisions = tuple(
        item
        for item in approved_decisions()
        if item.prerequisite_id != "candidate_cohort"
    )
    missing_result = assess_acquisition_readiness(missing_decisions)
    assert missing_result.status is AcquisitionReadinessStatus.NOT_READY
    assert any(
        "candidate_cohort" in item for item in missing_result.unresolved_decisions
    )

    no_evidence = replace_decision(
        approved_decisions(),
        PrerequisiteDecision(
            "candidate_cohort",
            PrerequisiteStatus.APPROVED,
            decision_authority="authorized project reviewer",
            explanation="Claimed approved without evidence.",
        ),
    )
    result = assess_acquisition_readiness(no_evidence)
    entry = next(
        item
        for item in result.prerequisites
        if item.prerequisite_id == "candidate_cohort"
    )
    assert entry.status is PrerequisiteStatus.BLOCKED
    assert not entry.evidence_sufficient
    assert result.status is AcquisitionReadinessStatus.NOT_READY


def test_recommendation_cannot_be_presented_as_formal_approval() -> None:
    decisions = replace_decision(
        approved_decisions(),
        PrerequisiteDecision(
            "prediction_task",
            PrerequisiteStatus.APPROVED,
            evidence=(
                EvidenceReference(
                    EvidenceKind.RECOMMENDATION,
                    "docs/ARC08_BASELINE_ML_TASK_SPEC.md",
                ),
            ),
            decision_authority="not recorded",
            explanation="The document recommends the candidate.",
        ),
    )

    result = assess_acquisition_readiness(decisions)
    entry = next(
        item
        for item in result.prerequisites
        if item.prerequisite_id == "prediction_task"
    )

    assert entry.status is PrerequisiteStatus.BLOCKED
    assert "fails closed" in entry.explanation
    assert result.status is AcquisitionReadinessStatus.NOT_READY


def test_historical_candidate_count_does_not_satisfy_current_feasibility() -> None:
    decisions = replace_decision(
        approved_decisions(),
        PrerequisiteDecision(
            "candidate_population_rechecked",
            PrerequisiteStatus.APPROVED,
            evidence=(
                EvidenceReference(
                    EvidenceKind.HISTORICAL_OBSERVATION,
                    "docs/ARC08_BASELINE_ML_TASK_SPEC.md#historical-count",
                    "2,211 prior predicate matches",
                ),
            ),
            explanation="Historical aggregate only.",
        ),
    )

    result = assess_acquisition_readiness(decisions)
    entry = next(
        item
        for item in result.prerequisites
        if item.prerequisite_id == "candidate_population_rechecked"
    )

    assert entry.status is PrerequisiteStatus.BLOCKED
    assert result.status is AcquisitionReadinessStatus.NOT_READY


def test_non_applicable_optional_prerequisite_requires_reason_and_does_not_block() -> (
    None
):
    decisions = replace_decision(
        approved_decisions(),
        PrerequisiteDecision(
            "public_redistribution_terms",
            PrerequisiteStatus.NOT_APPLICABLE,
            explanation="No public release is planned in this phase.",
            not_applicable_reason="Public redistribution is outside scope.",
        ),
    )

    result = assess_acquisition_readiness(decisions)

    assert result.status is AcquisitionReadinessStatus.NOT_READY
    redistribution = next(
        item
        for item in result.prerequisites
        if item.prerequisite_id == "public_redistribution_terms"
    )
    assert redistribution.status is PrerequisiteStatus.NOT_APPLICABLE
    assert any("prediction_task" in item for item in result.blocking_issues)

    mandatory = replace_decision(
        approved_decisions(),
        PrerequisiteDecision(
            "prediction_task",
            PrerequisiteStatus.NOT_APPLICABLE,
            explanation="Claimed not applicable.",
            not_applicable_reason="No reason can waive this mandatory item.",
        ),
    )
    failed = assess_acquisition_readiness(mandatory)
    mandatory_entry = next(
        item
        for item in failed.prerequisites
        if item.prerequisite_id == "prediction_task"
    )
    assert mandatory_entry.status is PrerequisiteStatus.BLOCKED
    assert failed.status is AcquisitionReadinessStatus.NOT_READY


def test_missing_input_decisions_and_blockers_are_reported_without_waiver() -> None:
    result = assess_acquisition_readiness()

    assert result.status is AcquisitionReadinessStatus.NOT_READY
    assert len(result.blocking_issues) == sum(
        definition.blocks_acquisition for definition in PREREQUISITE_DEFINITIONS
    )
    assert len(result.unresolved_decisions) >= len(result.blocking_issues)
    assert all(
        item.blocks_acquisition
        for item in result.prerequisites
        if any(item.prerequisite_id in issue for issue in result.blocking_issues)
    )


def test_current_repository_snapshot_is_not_ready_and_keeps_current_count_blocked() -> (
    None
):
    result = assess_current_repository_readiness()

    assert result.status is AcquisitionReadinessStatus.NOT_READY
    assert any("limit_code_semantics" in item for item in result.blocking_issues)
    assert any(
        "extraction_completeness_method" in item for item in result.blocking_issues
    )
    count = next(
        item
        for item in result.prerequisites
        if item.prerequisite_id == "candidate_population_rechecked"
    )
    assert count.status is PrerequisiteStatus.PENDING
    assert count.evidence[0].kind is EvidenceKind.HISTORICAL_OBSERVATION


def test_assessment_is_deterministic_and_json_serializable() -> None:
    decisions = replace_decision(
        approved_decisions(),
        PrerequisiteDecision(
            "prediction_task",
            PrerequisiteStatus.APPROVED,
            evidence=(
                EvidenceReference(
                    EvidenceKind.FORMAL_APPROVAL,
                    "approval-record/mission-task",
                    "approved by scientific reviewer; title: é",
                ),
            ),
            decision_authority="scientific reviewer",
            explanation="Synthetic Unicode fixture.",
        ),
    )

    first = serialize_acquisition_readiness(assess_acquisition_readiness(decisions))
    second = serialize_acquisition_readiness(assess_acquisition_readiness(decisions))

    assert first == second
    assert json.loads(first)["status"] == "NOT_READY"
    assert not first.startswith(b"\xef\xbb\xbf")
    assert b"\xc3\xa9" in first


def test_results_are_deeply_immutable() -> None:
    result = assess_acquisition_readiness(approved_decisions())

    with pytest.raises((AttributeError, TypeError)):
        result.status = AcquisitionReadinessStatus.NOT_READY  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        result.prerequisites[0].evidence[0].reference = "changed"  # type: ignore[misc]
    with pytest.raises(AcquisitionReadinessError, match="immutable tuple"):
        type(result)(
            status=result.status,
            prerequisites=list(result.prerequisites),  # type: ignore[arg-type]
            unresolved_decisions=result.unresolved_decisions,
            blocking_issues=result.blocking_issues,
            non_blocking_limitations=result.non_blocking_limitations,
            explanation=result.explanation,
        )

    with pytest.raises(AcquisitionReadinessError, match="cannot authenticate"):
        replace(
            result.prerequisites[0],
            status=PrerequisiteStatus.APPROVED,
            declared_status=PrerequisiteStatus.APPROVED,
            evidence_sufficient=True,
        )

    altered = replace(result.prerequisites[0], blocks_acquisition=False)
    with pytest.raises(AcquisitionReadinessError, match="cannot override"):
        replace(
            result,
            prerequisites=(altered, *result.prerequisites[1:]),
        )


def test_gate_makes_no_network_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    def reject_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("readiness assessment must be offline")

    monkeypatch.setattr("urllib.request.urlopen", reject_network)
    monkeypatch.setattr("http.client.HTTPConnection.request", reject_network)

    assert (
        assess_current_repository_readiness().status
        is AcquisitionReadinessStatus.NOT_READY
    )


def test_duplicate_and_unknown_prerequisite_ids_are_rejected() -> None:
    duplicate = approved_decisions()
    with pytest.raises(AcquisitionReadinessError, match="unique"):
        assess_acquisition_readiness((*duplicate, duplicate[0]))

    unknown = PrerequisiteDecision(
        "invented", PrerequisiteStatus.PENDING, explanation="Unknown test item."
    )
    with pytest.raises(AcquisitionReadinessError, match="unknown"):
        assess_acquisition_readiness((unknown,))


def test_evidence_reference_availability_defaults_to_not_checked() -> None:
    reference = EvidenceReference(EvidenceKind.PROJECT_DOCUMENT, "docs/policy.md")

    assert PublicAvailability is EvidenceReferenceAvailability
    assert reference.availability is EvidenceReferenceAvailability.NOT_CHECKED
    with pytest.raises(TypeError, match="availability"):
        EvidenceReference(
            EvidenceKind.PROJECT_DOCUMENT,
            "docs/policy.md",
            availability=EvidenceReferenceAvailability.AVAILABLE,  # type: ignore[call-arg]
        )
    serialized = json.loads(
        serialize_acquisition_readiness(
            assess_acquisition_readiness(
                (
                    PrerequisiteDecision(
                        "prediction_task",
                        PrerequisiteStatus.PENDING,
                        evidence=(reference,),
                        explanation="Awaiting review.",
                    ),
                )
            )
        )
    )
    prediction = next(
        item
        for item in serialized["prerequisites"]
        if item["prerequisite_id"] == "prediction_task"
    )
    assert prediction["evidence"][0]["availability"] == "NOT_CHECKED"
    assert (
        prediction["evidence"][0]["verification_status"] == "DECLARED_NOT_AUTHENTICATED"
    )


def test_local_availability_and_authority_claim_do_not_authenticate_evidence() -> None:
    local_reference = _reference_with_availability(
        EvidenceKind.AUTHORITATIVE_SOURCE,
        "pyproject.toml",
        _repository_root(),
    )
    decision = PrerequisiteDecision(
        "limit_code_semantics",
        PrerequisiteStatus.APPROVED,
        evidence=(local_reference,),
        decision_authority="NASA",
        explanation="Caller claims that local file is authoritative.",
    )

    result = assess_acquisition_readiness((decision,))
    item = next(
        value
        for value in result.prerequisites
        if value.prerequisite_id == "limit_code_semantics"
    )

    assert local_reference.availability is EvidenceReferenceAvailability.AVAILABLE
    assert (
        local_reference.verification_status
        is EvidenceVerificationStatus.DECLARED_NOT_AUTHENTICATED
    )
    assert item.status is PrerequisiteStatus.BLOCKED
    assert "not independently authenticated" in item.explanation
    assert result.status is AcquisitionReadinessStatus.NOT_READY


def test_evidence_verification_state_cannot_be_supplied_by_caller() -> None:
    with pytest.raises(TypeError, match="verification_status"):
        EvidenceReference(
            EvidenceKind.FORMAL_APPROVAL,
            "approval-record/claimed",
            verification_status=EvidenceVerificationStatus.DECLARED_NOT_AUTHENTICATED,  # type: ignore[call-arg]
        )


def test_reference_availability_checks_only_safe_repository_files(
    tmp_path: Path,
) -> None:
    (tmp_path / "present.md").write_text("supporting evidence", encoding="utf-8")
    outside = tmp_path.parent / "outside-reference.md"
    outside.write_text("outside checkout", encoding="utf-8")

    assert (
        _reference_availability("present.md#section", tmp_path)
        is EvidenceReferenceAvailability.AVAILABLE
    )
    assert (
        _reference_availability("missing.md", tmp_path)
        is EvidenceReferenceAvailability.MISSING
    )
    assert (
        _reference_availability("https://example.invalid/evidence", tmp_path)
        is EvidenceReferenceAvailability.UNRESOLVABLE
    )
    assert (
        _reference_availability("../outside-reference.md", tmp_path)
        is EvidenceReferenceAvailability.UNRESOLVABLE
    )
    outside.unlink()


def test_committed_repository_file_is_reported_available() -> None:
    from quantum_space_agi.ml.acquisition_readiness import _repository_root

    assert (
        _reference_availability("pyproject.toml", _repository_root())
        is EvidenceReferenceAvailability.AVAILABLE
    )


def test_reference_presence_does_not_change_readiness_or_approval(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import quantum_space_agi.ml.acquisition_readiness as readiness

    monkeypatch.setattr(readiness, "_repository_root", lambda: tmp_path)
    missing_result = assess_current_repository_readiness()
    missing_prediction = next(
        item
        for item in missing_result.prerequisites
        if item.prerequisite_id == "prediction_task"
    )
    assert missing_prediction.status is PrerequisiteStatus.PENDING
    assert (
        missing_prediction.evidence[0].availability
        is EvidenceReferenceAvailability.MISSING
    )

    task_spec = tmp_path / "docs" / "ARC08_BASELINE_ML_TASK_SPEC.md"
    task_spec.parent.mkdir(parents=True)
    task_spec.write_text("proposal only", encoding="utf-8")
    present_result = assess_current_repository_readiness()
    present_prediction = next(
        item
        for item in present_result.prerequisites
        if item.prerequisite_id == "prediction_task"
    )

    assert (
        present_result.status
        is missing_result.status
        is AcquisitionReadinessStatus.NOT_READY
    )
    assert present_result.blocking_issues == missing_result.blocking_issues
    assert present_prediction.status is PrerequisiteStatus.PENDING
    assert (
        present_prediction.evidence[0].availability
        is EvidenceReferenceAvailability.AVAILABLE
    )
