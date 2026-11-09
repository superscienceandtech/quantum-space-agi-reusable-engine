import json
from dataclasses import replace

import pytest

from quantum_space_agi.ml.acquisition_readiness import (
    PREREQUISITE_DEFINITIONS,
    AcquisitionReadinessError,
    AcquisitionReadinessStatus,
    EvidenceKind,
    EvidenceReference,
    PrerequisiteDecision,
    PrerequisiteStatus,
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


def test_all_prerequisites_approved_with_qualifying_evidence_is_ready() -> None:
    result = assess_acquisition_readiness(approved_decisions())

    assert result.status is AcquisitionReadinessStatus.READY_FOR_ACQUISITION
    assert result.blocking_issues == ()
    assert result.unresolved_decisions == ()


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

    assert result.status is AcquisitionReadinessStatus.READY_FOR_ACQUISITION
    assert result.blocking_issues == ()

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
    assert json.loads(first)["status"] == "READY_FOR_ACQUISITION"
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

    with pytest.raises(AcquisitionReadinessError, match="overall status"):
        replace(result, status=AcquisitionReadinessStatus.NOT_READY)

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
