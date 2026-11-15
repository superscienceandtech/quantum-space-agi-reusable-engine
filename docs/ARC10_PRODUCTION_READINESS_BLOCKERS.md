# ARC-10 Production Readiness Blockers

Repository: `/mnt/e/nasa26/nasaq26-develop-worktree`
Branch: `develop`
Full HEAD: `6a44af34a649a1138cf577b3b16dbaf436c8a203`
Current status: `B — PARTIALLY VERIFIED`
Baseline: `LOCAL_SYNTHETIC_DEMO_BASELINE — NOT PRODUCTION APPROVED`

This document lists blockers to any production claim. It is not an implementation plan and does not authorize work beyond the verified local demo baseline.

## Technical gaps

| ID | Blocker | Severity | Evidence | Resolution condition |
|---|---|---|---|---|
| T-01 | Missing canonical repository/branch authority | Critical | `docs/ARC10_AUTHORITATIVE_SOURCE_DISCOVERY.md`, `docs/ARC10_GAP_AND_DECISION_REGISTER.md` | Project Owner names the canonical target |
| T-02 | Hidden contract ownership gap | Critical | `docs/ARC10_PROJECT_OWNER_APPROVAL_REQUEST.md` | Project Owner assigns contract owner and approver |
| T-03 | Missing ARC-10 v0.3/v0.4 documents | High | searched workspaces and refs; no artifacts found | Project Owner designates the controlling version or supplies missing documents |
| T-04 | Collision metadata omission | Medium | `src/quantum_space_agi/simulation/workflow.py`, `src/quantum_space_agi/mission_demo/service.py` | Contract owner decides whether to expose or omit the metadata |
| T-05 | HTTP method semantics drift | Low | `src/quantum_space_agi/mission_demo/api.py`, `tests/mission_demo/test_api.py` | Contract owner decides 404 vs 405 and documents it |
| T-06 | Scientific boundary not formally approved | High | `tests/ml/test_synthetic_experiment_runner.py` asserts `NOT_ASSESSED` and `PENDING_REVIEW` | Domain reviewers approve the boundary and labels |

## Governance and approval gaps

| ID | Blocker | Severity | Evidence | Resolution condition |
|---|---|---|---|---|
| G-01 | No formal production approval record | Critical | `docs/ARC10_PROJECT_OWNER_APPROVAL_REQUEST.md` | Project Owner records formal approval or keeps the work blocked |
| G-02 | No security review / authorization model | Critical | no auth, CORS, or deployment approval is present | security authority reviews and approves the boundary |
| G-03 | No privacy/data-rights approval | Critical | synthetic demo only; no retention/privacy policy observed | privacy authority approves data handling and redaction policy |
| G-04 | No deployment approval | Critical | local loopback Uvicorn is not an approved production deployment | platform/ops authority approves deployment model |
| G-05 | No domain/acceptance approval | High | local demo is verified but not domain-approved | designated reviewers approve scientific and acceptance boundaries |

## Resolution ownership roles

- Project Owner: repository and approval authority
- Contract owner: API contract and versioning decisions
- Security authority: auth, CORS, threat boundary, publication controls
- Privacy authority: data handling, retention, redaction, permission model
- Platform/operations authority: deployment, runtime, runbook, rollback controls
- Domain reviewers: scientific boundary, collision semantics, mission policy language

## Conclusion

The verified local demo baseline remains valid evidence for local behavior and synthetic execution, but it is not a production baseline and it is not approved for deployment or scientific readiness.
