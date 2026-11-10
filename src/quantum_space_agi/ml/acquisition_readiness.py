"""Fail-closed, offline readiness assessment for candidate data acquisition.

This module evaluates declared decisions and evidence references. It does not
verify their authenticity, contact NASA, or authorize an acquisition request.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path, PureWindowsPath

from quantum_space_agi.errors import ValidationError


def _require_non_empty_text(field: str, value: str) -> None:
    if type(value) is not str or not value.strip():
        raise AcquisitionReadinessError(f"{field} must be a non-empty string")


class PrerequisiteStatus(StrEnum):
    """Explicit decision state for a readiness prerequisite."""

    APPROVED = "APPROVED"
    PENDING = "PENDING"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class EvidenceKind(StrEnum):
    """What kind of evidence a reference represents."""

    FORMAL_APPROVAL = "FORMAL_APPROVAL"
    AUTHORITATIVE_SOURCE = "AUTHORITATIVE_SOURCE"
    TECHNICAL_VERIFICATION = "TECHNICAL_VERIFICATION"
    CURRENT_QUERY_OBSERVATION = "CURRENT_QUERY_OBSERVATION"
    RETAINED_SNAPSHOT_AUDIT = "RETAINED_SNAPSHOT_AUDIT"
    SOFTWARE_TEST = "SOFTWARE_TEST"
    PROJECT_DOCUMENT = "PROJECT_DOCUMENT"
    RECOMMENDATION = "RECOMMENDATION"
    HISTORICAL_OBSERVATION = "HISTORICAL_OBSERVATION"


class EvidenceReferenceAvailability(StrEnum):
    """On-disk availability of a reference, separate from evidence validity."""

    NOT_CHECKED = "NOT_CHECKED"
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    UNRESOLVABLE = "UNRESOLVABLE"


class EvidenceVerificationStatus(StrEnum):
    """Verification state currently supportable by this offline gate."""

    DECLARED_NOT_AUTHENTICATED = "DECLARED_NOT_AUTHENTICATED"


class AcquisitionReadinessStatus(StrEnum):
    """Overall result; READY means only that this gate's declared criteria pass."""

    READY_FOR_ACQUISITION = "READY_FOR_ACQUISITION"
    NOT_READY = "NOT_READY"


class AcquisitionReadinessError(ValidationError):
    """An assessment contains malformed, incomplete, or duplicate input."""


def _validate_declared_effective_status(
    declared_status: PrerequisiteStatus | None,
    effective_status: PrerequisiteStatus,
) -> None:
    """Keep caller-declared approvals blocked until independent verification exists."""
    if (
        declared_status is PrerequisiteStatus.APPROVED
        and effective_status is not PrerequisiteStatus.BLOCKED
    ):
        raise AcquisitionReadinessError(
            "declared APPROVED prerequisite must be effectively BLOCKED until "
            "caller-declared evidence is independently verified"
        )


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    """Caller-declared evidence pointer; no authenticity check is performed."""

    kind: EvidenceKind
    reference: str
    note: str | None = None
    availability: EvidenceReferenceAvailability = field(
        default=EvidenceReferenceAvailability.NOT_CHECKED, init=False
    )
    verification_status: EvidenceVerificationStatus = field(
        default=EvidenceVerificationStatus.DECLARED_NOT_AUTHENTICATED, init=False
    )

    def __post_init__(self) -> None:
        if type(self.kind) is not EvidenceKind:
            raise AcquisitionReadinessError("evidence kind must be an EvidenceKind")
        _require_non_empty_text("evidence reference", self.reference)
        if self.note is not None:
            _require_non_empty_text("evidence note", self.note)


@dataclass(frozen=True, slots=True)
class PrerequisiteDecision:
    """Caller-declared decision and evidence for one known prerequisite."""

    prerequisite_id: str
    status: PrerequisiteStatus
    evidence: tuple[EvidenceReference, ...] = ()
    decision_authority: str | None = None
    explanation: str = ""
    not_applicable_reason: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_text("prerequisite_id", self.prerequisite_id)
        if type(self.status) is not PrerequisiteStatus:
            raise AcquisitionReadinessError("status must be a PrerequisiteStatus")
        if type(self.evidence) is not tuple or any(
            type(item) is not EvidenceReference for item in self.evidence
        ):
            raise AcquisitionReadinessError(
                "evidence must be a tuple of EvidenceReference values"
            )
        if self.decision_authority is not None:
            _require_non_empty_text("decision_authority", self.decision_authority)
        _require_non_empty_text("explanation", self.explanation)
        if self.not_applicable_reason is not None:
            _require_non_empty_text("not_applicable_reason", self.not_applicable_reason)


@dataclass(frozen=True, slots=True)
class PrerequisiteDefinition:
    """Fixed gate policy; callers cannot waive blocking status per assessment."""

    prerequisite_id: str
    title: str
    blocks_acquisition: bool
    required_evidence_kinds: tuple[EvidenceKind, ...]
    allows_not_applicable: bool = False

    def __post_init__(self) -> None:
        _require_non_empty_text("prerequisite_id", self.prerequisite_id)
        _require_non_empty_text("title", self.title)
        if type(self.blocks_acquisition) is not bool:
            raise AcquisitionReadinessError("blocks_acquisition must be a boolean")
        if type(self.required_evidence_kinds) is not tuple or any(
            type(item) is not EvidenceKind for item in self.required_evidence_kinds
        ):
            raise AcquisitionReadinessError(
                "required_evidence_kinds must be a tuple of EvidenceKind values"
            )
        if type(self.allows_not_applicable) is not bool:
            raise AcquisitionReadinessError("allows_not_applicable must be a boolean")


@dataclass(frozen=True, slots=True)
class PrerequisiteResult:
    """Effective prerequisite state; declared approvals require external review."""

    prerequisite_id: str
    title: str
    status: PrerequisiteStatus
    declared_status: PrerequisiteStatus | None
    evidence: tuple[EvidenceReference, ...]
    decision_authority: str | None
    explanation: str
    blocks_acquisition: bool
    evidence_sufficient: bool

    def __post_init__(self) -> None:
        _require_non_empty_text("prerequisite_id", self.prerequisite_id)
        _require_non_empty_text("title", self.title)
        if type(self.status) is not PrerequisiteStatus or (
            self.declared_status is not None
            and type(self.declared_status) is not PrerequisiteStatus
        ):
            raise AcquisitionReadinessError("result statuses are invalid")
        if self.status is PrerequisiteStatus.APPROVED:
            raise AcquisitionReadinessError(
                "this gate cannot authenticate caller-declared evidence"
            )
        _validate_declared_effective_status(self.declared_status, self.status)
        if type(self.evidence) is not tuple or any(
            type(item) is not EvidenceReference for item in self.evidence
        ):
            raise AcquisitionReadinessError(
                "result evidence must be an immutable tuple"
            )
        if self.decision_authority is not None:
            _require_non_empty_text("decision_authority", self.decision_authority)
        _require_non_empty_text("explanation", self.explanation)
        if (
            type(self.blocks_acquisition) is not bool
            or type(self.evidence_sufficient) is not bool
        ):
            raise AcquisitionReadinessError("result flags must be booleans")


@dataclass(frozen=True, slots=True)
class AcquisitionReadinessAssessment:
    """Immutable, deterministic result of the acquisition-readiness gate."""

    status: AcquisitionReadinessStatus
    prerequisites: tuple[PrerequisiteResult, ...]
    unresolved_decisions: tuple[str, ...]
    blocking_issues: tuple[str, ...]
    non_blocking_limitations: tuple[str, ...]
    explanation: str

    def __post_init__(self) -> None:
        if type(self.status) is not AcquisitionReadinessStatus:
            raise AcquisitionReadinessError("assessment status is invalid")
        if type(self.prerequisites) is not tuple or any(
            type(item) is not PrerequisiteResult for item in self.prerequisites
        ):
            raise AcquisitionReadinessError("prerequisites must be an immutable tuple")
        for field_name in (
            "unresolved_decisions",
            "blocking_issues",
            "non_blocking_limitations",
        ):
            values = getattr(self, field_name)
            if type(values) is not tuple or any(
                type(value) is not str for value in values
            ):
                raise AcquisitionReadinessError(
                    f"{field_name} must be a tuple of strings"
                )
        _require_non_empty_text("explanation", self.explanation)
        item_ids = tuple(item.prerequisite_id for item in self.prerequisites)
        expected_ids = tuple(
            definition.prerequisite_id for definition in PREREQUISITE_DEFINITIONS
        )
        if len(set(item_ids)) != len(item_ids) or set(item_ids) != set(expected_ids):
            raise AcquisitionReadinessError(
                "assessment must contain each defined prerequisite exactly once"
            )
        definition_by_id = {
            definition.prerequisite_id: definition
            for definition in PREREQUISITE_DEFINITIONS
        }
        for item in self.prerequisites:
            definition = definition_by_id[item.prerequisite_id]
            if item.blocks_acquisition is not definition.blocks_acquisition:
                raise AcquisitionReadinessError(
                    "result cannot override prerequisite blocking policy"
                )
            if item.status is PrerequisiteStatus.APPROVED:
                raise AcquisitionReadinessError(
                    "assessment cannot authenticate caller-declared evidence; "
                    "approved results require an independent verification mechanism"
                )
            if item.status is PrerequisiteStatus.NOT_APPLICABLE and (
                definition.blocks_acquisition
                or not definition.allows_not_applicable
                or item.declared_status is not PrerequisiteStatus.NOT_APPLICABLE
                or not item.evidence_sufficient
            ):
                raise AcquisitionReadinessError(
                    "NOT_APPLICABLE cannot waive a blocking prerequisite"
                )
        expected_blockers = tuple(
            f"{item.prerequisite_id}: {item.explanation}"
            for item in self.prerequisites
            if item.blocks_acquisition
            and item.status is not PrerequisiteStatus.APPROVED
        )
        expected_unresolved = tuple(
            f"{item.prerequisite_id}: {item.explanation}"
            for item in self.prerequisites
            if item.status
            not in (PrerequisiteStatus.APPROVED, PrerequisiteStatus.NOT_APPLICABLE)
        )
        expected_limitations = tuple(
            f"{item.prerequisite_id}: {item.explanation}"
            for item in self.prerequisites
            if not item.blocks_acquisition
            and item.status is not PrerequisiteStatus.APPROVED
        )
        if (
            self.blocking_issues != expected_blockers
            or self.unresolved_decisions != expected_unresolved
            or self.non_blocking_limitations != expected_limitations
        ):
            raise AcquisitionReadinessError(
                "assessment summaries do not match prerequisite states"
            )
        expected_status = (
            AcquisitionReadinessStatus.NOT_READY
            if expected_blockers
            else AcquisitionReadinessStatus.READY_FOR_ACQUISITION
        )
        if self.status is not expected_status:
            raise AcquisitionReadinessError(
                "overall status does not match blocking prerequisite states"
            )


_APPROVAL = (EvidenceKind.FORMAL_APPROVAL,)
_NASA_TECHNICAL = (
    EvidenceKind.AUTHORITATIVE_SOURCE,
    EvidenceKind.TECHNICAL_VERIFICATION,
)
_REUSE_TERMS = (EvidenceKind.AUTHORITATIVE_SOURCE, EvidenceKind.FORMAL_APPROVAL)

PREREQUISITE_DEFINITIONS: tuple[PrerequisiteDefinition, ...] = (
    PrerequisiteDefinition(
        "prediction_task",
        "Prediction objective, unit, and timing approved",
        True,
        _APPROVAL,
    ),
    PrerequisiteDefinition(
        "candidate_cohort",
        "Target interpretation and candidate cohort approved",
        True,
        _APPROVAL,
    ),
    PrerequisiteDefinition(
        "missing_nonfinite_policy",
        "Missing and non-finite target/feature handling approved",
        True,
        _APPROVAL,
    ),
    PrerequisiteDefinition(
        "zero_negative_policy",
        "Zero and negative target/feature handling approved",
        True,
        _APPROVAL,
    ),
    PrerequisiteDefinition(
        "uncertainty_policy",
        "Uncertainty-field handling approved",
        True,
        _APPROVAL,
    ),
    PrerequisiteDefinition(
        "limit_code_semantics",
        "Active-table limit-code semantics resolved authoritatively",
        True,
        (EvidenceKind.AUTHORITATIVE_SOURCE,),
    ),
    PrerequisiteDefinition(
        "limit_eligibility_policy",
        "Scientific effect of limit fields on cohort eligibility approved",
        True,
        _APPROVAL,
    ),
    PrerequisiteDefinition(
        "controversy_solution_policy",
        "Controversy and solution-status handling approved",
        True,
        _APPROVAL,
    ),
    PrerequisiteDefinition(
        "identity_duplicate_policy",
        "Planet identity, duplicate, host, and reference handling approved",
        True,
        _APPROVAL,
    ),
    PrerequisiteDefinition(
        "host_split_policy",
        "Host-disjoint grouping and evaluation policy approved",
        True,
        _APPROVAL,
    ),
    PrerequisiteDefinition(
        "baseline_metric_policy",
        "Baseline, metrics, and acceptance-decision process approved",
        True,
        _APPROVAL,
    ),
    PrerequisiteDefinition(
        "scientific_scope_and_claims",
        "Scientific scope and permitted claims approved",
        True,
        _APPROVAL,
    ),
    PrerequisiteDefinition(
        "archive_access_reuse_terms",
        "Applicable archive access and internal-reuse terms verified and approved",
        True,
        _REUSE_TERMS,
    ),
    PrerequisiteDefinition(
        "internal_snapshot_retention",
        "Internal raw-snapshot storage, access, backup, and retention approved",
        True,
        _APPROVAL,
    ),
    PrerequisiteDefinition(
        "citation_requirements",
        "Applicable archive citation and acknowledgment requirements recorded",
        True,
        (EvidenceKind.AUTHORITATIVE_SOURCE,),
    ),
    PrerequisiteDefinition(
        "extraction_completeness_method",
        "Chosen extraction method and completeness limits verified",
        True,
        _NASA_TECHNICAL,
    ),
    PrerequisiteDefinition(
        "candidate_population_rechecked",
        "Candidate population count rechecked for the planned acquisition attempt",
        True,
        (EvidenceKind.CURRENT_QUERY_OBSERVATION,),
    ),
    PrerequisiteDefinition(
        "offline_ingestion_contract",
        "Offline parsing, completeness, schema, and ledger path verified",
        True,
        (EvidenceKind.SOFTWARE_TEST,),
    ),
    PrerequisiteDefinition(
        "snapshot_consistency_policy",
        "Separate-query snapshot limitations documented and accepted",
        True,
        _APPROVAL,
    ),
    PrerequisiteDefinition(
        "public_redistribution_terms",
        "Public redistribution terms separately resolved if distribution is planned",
        False,
        (EvidenceKind.AUTHORITATIVE_SOURCE, EvidenceKind.FORMAL_APPROVAL),
        allows_not_applicable=True,
    ),
    PrerequisiteDefinition(
        "quantitative_group_feasibility",
        "Eligible host/group counts and split feasibility assessed on a retained "
        "snapshot",
        False,
        (EvidenceKind.RETAINED_SNAPSHOT_AUDIT,),
        allows_not_applicable=True,
    ),
)

_DEFINITION_BY_ID = {item.prerequisite_id: item for item in PREREQUISITE_DEFINITIONS}


def assess_acquisition_readiness(
    decisions: tuple[PrerequisiteDecision, ...] = (),
) -> AcquisitionReadinessAssessment:
    """Assess declared decisions against fixed prerequisites, failing closed.

    Missing decisions become ``PENDING``. Evidence kinds and authority strings
    are caller declarations only. Since this API has no independent evidence or
    authority verifier, every declared ``APPROVED`` decision is downgraded to
    ``BLOCKED``. Historical observations, recommendations, and software tests
    cannot substitute for approval or a current query observation.
    """
    if type(decisions) is not tuple or any(
        type(item) is not PrerequisiteDecision for item in decisions
    ):
        raise AcquisitionReadinessError(
            "decisions must be a tuple of PrerequisiteDecision values"
        )
    ids = tuple(item.prerequisite_id for item in decisions)
    if len(set(ids)) != len(ids):
        raise AcquisitionReadinessError("prerequisite decisions must be unique")
    unknown = tuple(sorted(set(ids) - _DEFINITION_BY_ID.keys()))
    if unknown:
        raise AcquisitionReadinessError(
            "unknown prerequisite identifiers: " + ", ".join(unknown)
        )
    by_id = {item.prerequisite_id: item for item in decisions}

    results: list[PrerequisiteResult] = []
    for definition in PREREQUISITE_DEFINITIONS:
        decision = by_id.get(definition.prerequisite_id)
        results.append(_evaluate_one(definition, decision))
    result_items = tuple(results)
    unresolved = tuple(
        f"{item.prerequisite_id}: {item.explanation}"
        for item in result_items
        if item.status
        not in (
            PrerequisiteStatus.APPROVED,
            PrerequisiteStatus.NOT_APPLICABLE,
        )
    )
    blockers = tuple(
        f"{item.prerequisite_id}: {item.explanation}"
        for item in result_items
        if item.blocks_acquisition and item.status is not PrerequisiteStatus.APPROVED
    )
    limitations = tuple(
        f"{item.prerequisite_id}: {item.explanation}"
        for item in result_items
        if not item.blocks_acquisition
        and item.status is not PrerequisiteStatus.APPROVED
    )
    overall = (
        AcquisitionReadinessStatus.READY_FOR_ACQUISITION
        if not blockers
        else AcquisitionReadinessStatus.NOT_READY
    )
    explanation = (
        "All blocking prerequisites passed the declared-evidence gate. This "
        "assessment is not authorization to access NASA data, proof of evidence "
        "authenticity, or scientific approval."
        if not blockers
        else f"Acquisition readiness is blocked by {len(blockers)} prerequisite(s)."
    )
    return AcquisitionReadinessAssessment(
        status=overall,
        prerequisites=result_items,
        unresolved_decisions=unresolved,
        blocking_issues=blockers,
        non_blocking_limitations=limitations,
        explanation=explanation,
    )


def assess_current_repository_readiness() -> AcquisitionReadinessAssessment:
    """Return the explicitly documented current ARC-08 decision snapshot.

    Decision statuses are maintained alongside the policy documents. Reference
    path availability is checked locally for this checkout, but file contents
    and approval authenticity are not inspected. Update the decision snapshot
    only when its referenced evidence changes, and independently verify
    referenced approvals before relying on them.
    """
    repository_root = _repository_root()
    project_docs = (
        "docs/ARC08_RECOMMENDED_DECISION_POLICY.md",
        "docs/ARC08_SCIENTIFIC_ELIGIBILITY_POLICY_REVIEW.md",
        "docs/ARC08_PROVENANCE_SNAPSHOT_REPRODUCIBILITY_GATE.md",
    )
    task_doc = "docs/ARC08_BASELINE_ML_TASK_SPEC.md"
    decisions = (
        _snapshot_decision(
            "prediction_task",
            PrerequisiteStatus.PENDING,
            task_doc,
            EvidenceKind.RECOMMENDATION,
            "The mass-from-radius objective remains exploratory and unapproved.",
            repository_root=repository_root,
        ),
        _snapshot_decision(
            "candidate_cohort",
            PrerequisiteStatus.PENDING,
            task_doc,
            EvidenceKind.RECOMMENDATION,
            "The default/Mass predicate is a candidate, not an approved cohort.",
            repository_root=repository_root,
        ),
        _snapshot_decision(
            "missing_nonfinite_policy",
            PrerequisiteStatus.PENDING,
            project_docs[1],
            EvidenceKind.RECOMMENDATION,
            "Mechanical handling is proposed; final scientific policy is not approved.",
            repository_root=repository_root,
        ),
        _snapshot_decision(
            "zero_negative_policy",
            PrerequisiteStatus.PENDING,
            project_docs[1],
            EvidenceKind.RECOMMENDATION,
            "Quarantine/reporting is proposed; scientific disposition is unresolved.",
            repository_root=repository_root,
        ),
        _snapshot_decision(
            "uncertainty_policy",
            PrerequisiteStatus.PENDING,
            project_docs[1],
            EvidenceKind.RECOMMENDATION,
            "Raw retention is proposed; no scientific uncertainty policy is approved.",
            repository_root=repository_root,
        ),
        _snapshot_decision(
            "limit_code_semantics",
            PrerequisiteStatus.BLOCKED,
            "docs/ARC08_NASA_LIMIT_CODE_SEMANTICS.md",
            EvidenceKind.PROJECT_DOCUMENT,
            "Active ps limit-code meanings remain unresolved in repository evidence.",
            repository_root=repository_root,
        ),
        _snapshot_decision(
            "limit_eligibility_policy",
            PrerequisiteStatus.PENDING,
            project_docs[1],
            EvidenceKind.RECOMMENDATION,
            "No approved eligibility consequence for limit fields is recorded.",
            repository_root=repository_root,
        ),
        _snapshot_decision(
            "controversy_solution_policy",
            PrerequisiteStatus.PENDING,
            project_docs[1],
            EvidenceKind.RECOMMENDATION,
            "Preserve/report without filtering is proposed, not approved.",
            repository_root=repository_root,
        ),
        _snapshot_decision(
            "identity_duplicate_policy",
            PrerequisiteStatus.PENDING,
            project_docs[2],
            EvidenceKind.RECOMMENDATION,
            "Identity and duplicate handling requires scientific-owner approval.",
            repository_root=repository_root,
        ),
        _snapshot_decision(
            "host_split_policy",
            PrerequisiteStatus.PENDING,
            project_docs[2],
            EvidenceKind.RECOMMENDATION,
            "Host-disjoint grouping is recommended but not approved or assessed "
            "on a snapshot.",
            repository_root=repository_root,
        ),
        _snapshot_decision(
            "baseline_metric_policy",
            PrerequisiteStatus.PENDING,
            task_doc,
            EvidenceKind.RECOMMENDATION,
            "Median baseline and metrics are proposed; thresholds and use remain "
            "unresolved.",
            repository_root=repository_root,
        ),
        _snapshot_decision(
            "scientific_scope_and_claims",
            PrerequisiteStatus.PENDING,
            project_docs[1],
            EvidenceKind.RECOMMENDATION,
            "Scope and permitted claims have not received recorded scientific "
            "approval.",
            repository_root=repository_root,
        ),
        _snapshot_decision(
            "archive_access_reuse_terms",
            PrerequisiteStatus.BLOCKED,
            project_docs[2],
            EvidenceKind.PROJECT_DOCUMENT,
            "Applicable retention/reuse permission is not established; silence is "
            "not permission.",
            repository_root=repository_root,
        ),
        _snapshot_decision(
            "internal_snapshot_retention",
            PrerequisiteStatus.PENDING,
            project_docs[2],
            EvidenceKind.RECOMMENDATION,
            "No stakeholder-approved durable storage and retention plan is recorded.",
            repository_root=repository_root,
        ),
        _snapshot_decision(
            "citation_requirements",
            PrerequisiteStatus.APPROVED,
            "docs/ARC08_BASELINE_ML_POLICY_DECISION_MATRIX.md",
            EvidenceKind.AUTHORITATIVE_SOURCE,
            "Official NASA citation guidance is referenced for later use; this is "
            "not redistribution permission.",
            repository_root=repository_root,
        ),
        _snapshot_decision(
            "extraction_completeness_method",
            PrerequisiteStatus.BLOCKED,
            "docs/ARC08_BASELINE_ML_EXTRACTION_DESIGN.md",
            EvidenceKind.PROJECT_DOCUMENT,
            "Full-scale effective limits and extraction completeness remain "
            "unverified.",
            repository_root=repository_root,
        ),
        _snapshot_decision(
            "candidate_population_rechecked",
            PrerequisiteStatus.PENDING,
            task_doc,
            EvidenceKind.HISTORICAL_OBSERVATION,
            "The 2,211 count is historical and cannot establish current "
            "acquisition feasibility.",
            repository_root=repository_root,
        ),
        _snapshot_decision(
            "offline_ingestion_contract",
            PrerequisiteStatus.APPROVED,
            "src/quantum_space_agi/ml/dataset_ingestion.py; "
            "tests/ml/test_dataset_ingestion.py",
            EvidenceKind.SOFTWARE_TEST,
            "Offline synthetic-fixture validation exists; this is software "
            "evidence only.",
            repository_root=repository_root,
        ),
        _snapshot_decision(
            "snapshot_consistency_policy",
            PrerequisiteStatus.PENDING,
            project_docs[2],
            EvidenceKind.RECOMMENDATION,
            "The non-isolation limitation is documented but not recorded as "
            "approved for this task.",
            repository_root=repository_root,
        ),
        PrerequisiteDecision(
            "public_redistribution_terms",
            PrerequisiteStatus.NOT_APPLICABLE,
            evidence=(
                _reference_with_availability(
                    EvidenceKind.PROJECT_DOCUMENT,
                    project_docs[2],
                    repository_root,
                    note=(
                        "No public release is in scope for this acquisition-readiness "
                        "snapshot."
                    ),
                ),
            ),
            explanation=(
                "No public redistribution is planned by this phase; this does "
                "not grant future permission."
            ),
            not_applicable_reason=(
                "Public release is outside the current phase; resolve terms "
                "before any release."
            ),
        ),
        PrerequisiteDecision(
            "quantitative_group_feasibility",
            PrerequisiteStatus.PENDING,
            evidence=(
                _reference_with_availability(
                    EvidenceKind.HISTORICAL_OBSERVATION,
                    task_doc,
                    repository_root,
                    note=(
                        "No retained eligible row-level snapshot or group counts exist."
                    ),
                ),
            ),
            explanation=(
                "Group counts and split feasibility require a future approved "
                "retained snapshot."
            ),
        ),
    )
    return assess_acquisition_readiness(decisions)


def serialize_acquisition_readiness(
    assessment: AcquisitionReadinessAssessment,
) -> bytes:
    """Serialize a readiness result as deterministic compact UTF-8 JSON."""
    if type(assessment) is not AcquisitionReadinessAssessment:
        raise AcquisitionReadinessError(
            "assessment must be an AcquisitionReadinessAssessment"
        )
    for item in assessment.prerequisites:
        _validate_declared_effective_status(item.declared_status, item.status)
    payload = {
        "status": assessment.status.value,
        "explanation": assessment.explanation,
        "unresolved_decisions": list(assessment.unresolved_decisions),
        "blocking_issues": list(assessment.blocking_issues),
        "non_blocking_limitations": list(assessment.non_blocking_limitations),
        "prerequisites": [
            {
                "prerequisite_id": item.prerequisite_id,
                "title": item.title,
                "status": item.status.value,
                "declared_status": (
                    item.declared_status.value
                    if item.declared_status is not None
                    else None
                ),
                "evidence": [
                    {
                        "kind": ref.kind.value,
                        "reference": ref.reference,
                        "note": ref.note,
                        "availability": ref.availability.value,
                        "verification_status": ref.verification_status.value,
                    }
                    for ref in item.evidence
                ],
                "decision_authority": item.decision_authority,
                "explanation": item.explanation,
                "blocks_acquisition": item.blocks_acquisition,
                "evidence_sufficient": item.evidence_sufficient,
            }
            for item in assessment.prerequisites
        ],
    }
    try:
        return json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise AcquisitionReadinessError("assessment is not JSON serializable") from exc


def _evaluate_one(
    definition: PrerequisiteDefinition,
    decision: PrerequisiteDecision | None,
) -> PrerequisiteResult:
    if decision is None:
        return PrerequisiteResult(
            prerequisite_id=definition.prerequisite_id,
            title=definition.title,
            status=PrerequisiteStatus.PENDING,
            declared_status=None,
            evidence=(),
            decision_authority=None,
            explanation="No decision or evidence was supplied.",
            blocks_acquisition=definition.blocks_acquisition,
            evidence_sufficient=False,
        )

    status = decision.status
    explanation = decision.explanation
    evidence_sufficient = _has_required_evidence(definition, decision)
    if status is PrerequisiteStatus.APPROVED:
        status = PrerequisiteStatus.BLOCKED
        if not evidence_sufficient:
            explanation = (
                "Declared APPROVED, but required evidence kinds are missing or "
                "insufficient; the gate fails closed."
            )
        else:
            explanation = (
                "Declared APPROVED, but supplied evidence and authority labels "
                "are not independently authenticated by this gate; human or "
                "external verification is required."
            )
    elif status is PrerequisiteStatus.NOT_APPLICABLE:
        if not definition.allows_not_applicable or not decision.not_applicable_reason:
            status = PrerequisiteStatus.BLOCKED
            explanation = (
                "NOT_APPLICABLE is not permitted for this prerequisite or lacks "
                "an explicit rationale."
            )
        else:
            evidence_sufficient = True
            explanation = decision.explanation or decision.not_applicable_reason

    return PrerequisiteResult(
        prerequisite_id=definition.prerequisite_id,
        title=definition.title,
        status=status,
        declared_status=decision.status,
        evidence=decision.evidence,
        decision_authority=decision.decision_authority,
        explanation=explanation,
        blocks_acquisition=definition.blocks_acquisition,
        evidence_sufficient=evidence_sufficient,
    )


def _has_required_evidence(
    definition: PrerequisiteDefinition,
    decision: PrerequisiteDecision,
) -> bool:
    kinds = {item.kind for item in decision.evidence}
    if not set(definition.required_evidence_kinds).issubset(kinds):
        return False
    if EvidenceKind.FORMAL_APPROVAL in definition.required_evidence_kinds:
        if decision.decision_authority is None:
            return False
    return bool(decision.evidence)


def _snapshot_decision(
    prerequisite_id: str,
    status: PrerequisiteStatus,
    reference: str,
    evidence_kind: EvidenceKind,
    explanation: str,
    *,
    repository_root: Path,
) -> PrerequisiteDecision:
    evidence = _reference_with_availability(
        evidence_kind,
        reference,
        repository_root,
    )
    return PrerequisiteDecision(
        prerequisite_id=prerequisite_id,
        status=status,
        evidence=(evidence,),
        decision_authority=None,
        explanation=explanation,
    )


def _repository_root() -> Path:
    """Locate this checkout from the installed source package, without Git calls."""
    return Path(__file__).resolve().parents[3]


def _reference_with_availability(
    kind: EvidenceKind,
    reference: str,
    repository_root: Path,
    note: str | None = None,
) -> EvidenceReference:
    """Create a reference annotated only with safe local path availability."""
    evidence = EvidenceReference(kind, reference, note)
    object.__setattr__(
        evidence,
        "availability",
        _reference_availability(reference, repository_root),
    )
    return evidence


def _reference_availability(
    reference: str, repository_root: Path
) -> EvidenceReferenceAvailability:
    """Check a repository-relative file reference without following escapes.

    URLs, composite prose references, absolute paths, and paths that resolve
    outside the checkout are UNRESOLVABLE. This reports file presence only; it
    does not establish that the referenced material is authentic or sufficient.
    """
    if type(reference) is not str or not reference:
        return EvidenceReferenceAvailability.UNRESOLVABLE
    if ";" in reference or "\\" in reference:
        return EvidenceReferenceAvailability.UNRESOLVABLE

    path_text = reference.split("#", maxsplit=1)[0]
    candidate_path = Path(path_text)
    if (
        not path_text
        or candidate_path.is_absolute()
        or PureWindowsPath(path_text).is_absolute()
        or any(part in {"", ".", ".."} for part in path_text.split("/"))
        or ":" in path_text
    ):
        return EvidenceReferenceAvailability.UNRESOLVABLE

    try:
        root = repository_root.resolve()
        candidate = (root / candidate_path).resolve()
        candidate.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        return EvidenceReferenceAvailability.UNRESOLVABLE

    try:
        if candidate.is_file():
            return EvidenceReferenceAvailability.AVAILABLE
        if candidate.exists():
            return EvidenceReferenceAvailability.UNRESOLVABLE
    except OSError:
        return EvidenceReferenceAvailability.UNRESOLVABLE
    return EvidenceReferenceAvailability.MISSING
