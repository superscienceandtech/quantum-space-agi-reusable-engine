# ARC-10 Production Contract Acceptance Criteria

Repository: `/mnt/e/nasa26/nasaq26-develop-worktree`
Branch: `develop`
Full HEAD: `6a44af34a649a1138cf577b3b16dbaf436c8a203`
Current status: `B — PARTIALLY VERIFIED`
Baseline: `LOCAL_SYNTHETIC_DEMO_BASELINE — NOT PRODUCTION APPROVED`
Status: `FORMAL REVIEW PREPARATION COMPLETE — PRODUCTION NOT APPROVED`

This document defines review gates for a future production contract baseline. It is not an approval record and it does not authorize implementation or deployment.

| Gate ID | Requirement | Evidence required | Responsible role | Status | Approval requirement |
|---|---|---|---|---|---|
| A-01 | Endpoint inventory is fully documented and consistent with source and route behavior | Source code, route list, and method mapping | Contract owner | PARTIALLY VERIFIED | Required before any contract approval |
| A-02 | Request/response DTOs are complete and match implemented behavior | DTO definitions and real payloads from source | Contract owner | PARTIALLY VERIFIED | Required before any contract approval |
| A-03 | Error schema is documented and consistent | `ApiErrorDTO`, validation handlers, test evidence | API owner | PARTIALLY VERIFIED | Required before any contract approval |
| A-04 | Unified Mission Result structure is authoritative and confirmed | `MissionRunResponseDTO` and service implementation | Contract owner | PARTIALLY VERIFIED | Required before any contract approval |
| A-05 | Collision metadata treatment is explicit and approved | Source description and Project Owner decision D-04 | Project Owner + contract owner | VERIFIED FOR CURRENT SCOPE | Separate contract approval required for future change |
| A-06 | Scientific eligibility is not inferred from structural validation | Synthetic execution and validation documentation | Domain reviewers | PARTIALLY VERIFIED | Required before scientific or mission claims |
| A-07 | Mission Planning & Simulation API remains separate from Dataset Validation API | Evidence package and architecture record | Architecture owner | PARTIALLY VERIFIED | Required before any production or data claim |
| A-08 | Synthetic execution is labeled and not treated as scientific evidence | Synthetic runner and evidence docs | Domain reviewers | VERIFIED IN CURRENT BASELINE | Required before any scientific claim |
| A-09 | Security and authentication boundary is documented and accepted | Security review evidence | Security authority | PENDING | Must be separately approved |
| A-10 | Privacy and data-retention policy is approved | Privacy review evidence | Privacy authority | PENDING | Must be separately approved |
| A-11 | Operational deployment and runbook are approved | Deployment and ops review evidence | Platform/operations authority | PENDING | Must be separately approved |
| A-12 | Scientific/domain acceptance and resource policy approvals are recorded | Domain review evidence | Scientific/domain reviewers | PENDING | Must be separately approved |
| A-13 | Testing evidence is available and reproducible | Source and test files; commands recorded | QA owner | PARTIALLY VERIFIED | Required before approval |
| A-14 | Acceptance criteria are formally signed off | Project Owner approval record | Project Owner | PENDING | Required for production contract approval |

## 1. Requirement details

### A-01 Endpoint and HTTP method consistency
- Requirement: each public endpoint and method must match the approved contract description.
- Evidence required: source code, method mapping, and route-level documentation.
- Responsible role: contract owner.
- Current status: PARTIALLY VERIFIED.

### A-02 Request and response DTO completeness
- Requirement: all request and response fields must be tracked and documented.
- Evidence required: `MissionRequestDTO`, `MissionRunResponseDTO`, and validation output.
- Responsible role: contract owner.
- Current status: PARTIALLY VERIFIED.

### A-03 Error schema consistency
- Requirement: all application failures must use the documented error envelope and consistent codes.
- Evidence required: exception handlers and local API behavior.
- Responsible role: API owner.
- Current status: PARTIALLY VERIFIED.

### A-04 Mission Result integrity
- Requirement: the unified result object must remain stable and accurate within the current baseline.
- Evidence required: service output and DTO model.
- Responsible role: contract owner.
- Current status: PARTIALLY VERIFIED.

### A-05 Collision metadata treatment
- Requirement: the public contract must explicitly document whether collision metadata is included or excluded.
- Evidence required: Project Owner decision D-04 and corresponding source behavior.
- Responsible role: Project Owner + contract owner.
- Current status: VERIFIED FOR CURRENT SCOPE.

### A-06 Scientific eligibility boundary
- Requirement: scientific eligibility cannot be inferred from structural validation or synthetic outputs.
- Evidence required: synthetic evidence bundle and explicit `PENDING_REVIEW` semantics.
- Responsible role: domain reviewers.
- Current status: PARTIALLY VERIFIED.

### A-07 Dataset Validation separation
- Requirement: Mission Planning & Simulation API and Dataset Validation API remain distinct.
- Evidence required: architecture docs and distinct demo evidence.
- Responsible role: architecture owner.
- Current status: PARTIALLY VERIFIED.

### A-08 Synthetic execution labeling
- Requirement: synthetic execution is disclosed and never described as scientific validation.
- Evidence required: synthetic runner and evidence docs.
- Responsible role: domain reviewers.
- Current status: VERIFIED IN CURRENT BASELINE.

### A-09 Security and authentication
- Requirement: all production access and trust boundaries must be reviewed and approved.
- Evidence required: authorization model, network review, deployment model.
- Responsible role: security authority.
- Current status: PENDING.

### A-10 Privacy and data retention
- Requirement: mission and data-handling policy must be reviewed and approved.
- Evidence required: privacy review and retention policy.
- Responsible role: privacy authority.
- Current status: PENDING.

### A-11 Deployment and operational readiness
- Requirement: runtime environment, scaling, rollback, and operations model must be approved before production claims.
- Evidence required: deployment review and runbook.
- Responsible role: platform/operations authority.
- Current status: PENDING.

### A-12 Scientific/domain acceptance
- Requirement: resource policy, mission semantics, and acceptance criteria must be reviewed by domain owners.
- Evidence required: approval record and review notes.
- Responsible role: domain reviewers.
- Current status: PENDING.

### A-13 Testing and reproducibility
- Requirement: review evidence must be reproducible and tied to actual commands and results.
- Evidence required: commands, outputs, and reviewed file state.
- Responsible role: QA owner.
- Current status: PARTIALLY VERIFIED.

### A-14 Formal acceptance gate
- Requirement: formal approval is recorded only by the Project Owner.
- Evidence required: decision record and approval date or explicit review record.
- Responsible role: Project Owner.
- Current status: PENDING.

## 2. Current status summary

The local demo baseline is reviewable and evidence-backed. Production approval remains out-of-scope and intentionally blocked until the separate approval gates above are satisfied.
