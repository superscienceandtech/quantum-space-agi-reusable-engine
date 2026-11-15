# ARC-10 Governance Decision Register

Repository: `/mnt/e/nasa26/nasaq26-develop-worktree`
Branch: `develop`
Head: `6a44af34a649a1138cf577b3b16dbaf436c8a203`
Current status: `B — PARTIALLY VERIFIED`
Baseline: `LOCAL_SYNTHETIC_DEMO_BASELINE — NOT PRODUCTION APPROVED`

This register tracks governance decisions only. It does not approve implementation or deployment.

The Project Owner has now supplied explicit decisions for D-01 through D-05. D-06 remains pending clarification.

| Decision ID | Title | State | Evidence path(s) | Role authorized to decide | Notes |
|---|---|---|---|---|---|
| D-01 | Canonical repository/branch authority for ARC-10 | `APPROVED — LIMITED SCOPE` | `docs/ARC10_AUTHORITATIVE_SOURCE_DISCOVERY.md`, `docs/ARC10_GAP_AND_DECISION_REGISTER.md` | Project Owner | `develop` is the verification baseline only; it is not the canonical production repository |
| D-02 | Contract owner and approval authority | `APPROVED` | `docs/ARC10_PROJECT_OWNER_APPROVAL_REQUEST.md`, `docs/ARC10_GAP_AND_DECISION_REGISTER.md` | Project Owner | Project Owner owns final contract approval; contributors prepare evidence and drafts |
| D-03 | Contract versioning baseline and missing v0.3/v0.4 artifacts | `APPROVED — PROPOSAL ONLY` | `docs/ARC10_GAP_AND_DECISION_REGISTER.md`, `docs/ARC10_PROJECT_OWNER_APPROVAL_REQUEST.md` | Project Owner | Controlled reconstruction proposal only; no canonical version is designated |
| D-04 | Collision metadata in the public Mission API contract | `APPROVED — CURRENT SCOPE ONLY` | `src/quantum_space_agi/simulation/workflow.py`, `src/quantum_space_agi/mission_demo/service.py`, `docs/ARC10_GAP_AND_DECISION_REGISTER.md` | Project Owner | Collision metadata excluded from the public response for now |
| D-05 | Unsupported methods on POST-only routes: 404 vs 405 | `APPROVED — LOCAL DEMO ONLY` | `src/quantum_space_agi/mission_demo/api.py`, `tests/mission_demo/test_api.py`, `docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md` | Project Owner | `404 Not Found` is adopted for the current local demo only |
| D-06 | Formal production boundary and required governance approvals | `APPROVED — REVIEW PREPARATION ONLY` | `docs/ARC10_PRODUCTION_READINESS_BLOCKERS.md`, `docs/ARC10_PROJECT_OWNER_APPROVAL_REQUEST.md`, `docs/ARC10_GAP_AND_DECISION_REGISTER.md`, `docs/ARC10_PROJECT_OWNER_REVIEW_PACKAGE.md` | Project Owner | Review preparation is explicitly authorized; production approval remains separate and not granted |

## Decision status definitions

- `PENDING`: no approved decision recorded
- `APPROVED`: executed by the appropriate authority
- `REJECTED`: explicit rejection documented by the authority
- `DEFERRED`: postponement without approval or rejection

## Current baseline

The design baseline remains:

`LOCAL_SYNTHETIC_DEMO_BASELINE — NOT PRODUCTION APPROVED`

This is a verified local implementation state, not a governance-approved production baseline.
