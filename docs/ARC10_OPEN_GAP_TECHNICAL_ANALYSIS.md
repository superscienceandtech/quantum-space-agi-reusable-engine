# ARC-10 Open Gap Technical Analysis

## Review status

Repository: `/mnt/e/nasa26/nasaq26-develop-worktree`
Branch: `develop`
HEAD: `6a44af34a649a1138cf577b3b16dbaf436c8a203`
Status: B — PARTIALLY VERIFIED

This document records the open technical and governance gaps that remain after local implementation review. It does not change any code, API contract, or policy decision.

## Executive summary

The local Mission API is implemented and functions as a synthetic educational demo. The unresolved issues are mainly about authority, contract control, and evidence quality. The technical gaps are real but limited and do not negate the local demo verification. They do, however, block a production or approval claim.

## Gap register

| ID | Gap | Severity | Evidence | Why it matters |
|---|---|---|---|---|
| MAPI-02 | No canonical production repository/branch | Critical | `docs/ARC10_GAP_AND_DECISION_REGISTER.md` and `docs/ARC10_AUTHORITATIVE_SOURCE_DISCOVERY.md` | The worktree is operationally real but not formally designated as the production target |
| MAPI-07 | No contract owner | Critical | local docs and draft candidate only | Without an accountable owner, the contract cannot become binding |
| MAPI-15 | No approved versioning / control process | Critical | draft v0.1 only; v0.3/v0.4 missing | Versioning is unresolved |
| MAPI-08 | No security review | Critical | no auth/CORS/threat-model record in source | The local loopback demo is not a production service |
| MAPI-09 | No privacy/data-rights approval | Critical | synthetic demo only; no retention policy | Not acceptable for controlled data |
| MAPI-13 | No deployment approval | Critical | loopback Uvicorn launch only | Not a deployed service |
| MAPI-04 / MAPI-05 | No ARC-05/ARC-08 domain review | High | local orchestration exists; independent approval absent | Scientific meaning cannot be claimed |
| Collision metadata gap | ARC-05 collision metadata omitted from public response | Medium | `workflow.py:30-54` vs `service.py:78-104` | Client cannot determine collision threshold/method |
| GET/405 mismatch | `GET` on POST-only routes returns 404 even though docs say 405 | Low | `api.py:119-123` and `tests/mission_demo/test_api.py:164-168` | Error handling documentation is not exact |

## Detailed technical findings

### 1) Missing authoritative source and authority boundaries

The six reports document that the implementation exists in the local worktree but is not formally designated as the production Mission API source. The `develop` branch is ahead of `origin/develop`, and several worktrees exist. This means the read-only verification is real but cannot be treated as the canonical production target without explicit Project Owner direction.

### 2) Contract and documentation drift

The API docs say this service is a local educational demo, but some route and error semantics are documented more broadly than what the implementation does in practice.

The real behavior is visible in code and tests:
- `src/quantum_space_agi/mission_demo/api.py:119-123` maps `404` and `405` to error codes.
- `tests/mission_demo/test_api.py:164-168` verifies `GET /api/v1/missions/unknown` returns `404`.
- `GET /api/v1/missions/run` is not a declared route; the dashboard mount handles the unmatched path and returns `404` instead of a `405`.

This is a real mismatch between the broad wording in documentation and the code-path behavior. It is a documentation gap, not a production-blocking failure.

### 3) Collision metadata omission is an API boundary issue

The underlying ARC-05 workflow returns both collision metadata and collision diagnosis metrics:
- `src/quantum_space_agi/simulation/workflow.py:38-53`

Those fields are emitted by `run_simulation()` as:
- `collision_radius_m`
- `collision_method`

However, the public mission response in `src/quantum_space_agi/mission_demo/service.py:78-102` only exposes:
- `collision_index`
- `collision_time_s`
- `collision_state`
- `diagnostics`

It omits the radius and method. This is a real compatibility issue at the API boundary and should be resolved by contract owner direction before the public contract is declared final.

### 4) Synthetic execution remains synthetic

The code and tests clearly distinguish synthetic and scientific status:
- `src/quantum_space_agi/mission_demo/service.py:55-76` labels the result as a synthetic educational demo and uses `policy_approval_status: "pending"`.
- `tests/ml/test_synthetic_experiment_runner.py:17-41` asserts `scientific_eligibility_status == "NOT_ASSESSED"` and `scientific_acceptance_status == "PENDING_REVIEW"`.

This is the correct and explicit governance model. It should not be treated as scientific readiness evidence.

### 5) Mission API boundary remains separate from Dataset Validation

The documentation states that Dataset Validation is separate from the Mission APIs:
- `docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md:46-59`

The source code also reflects this separation. The file path and behavior are distinct, and no Dataset Validation routes are included in the mission API. This prevents the Mission API from being mistaken for a general scientific validation service.

## Recommended classification

- `MAPI-02` — BLOCKED BY AUTHORITY
- `MAPI-07` — BLOCKED BY AUTHORITY
- `MAPI-15` — BLOCKED BY AUTHORITY
- `collision metadata gap` — OPEN TECHNICAL GAP
- `GET/405 mismatch` — OPEN TECHNICAL GAP
- `scientific_eligibility` boundary — properly constrained; no evidence of incorrect inference in the reviewed code

## Decision implication

The current evidence supports a local demo and a reviewable synthetic API at the implementation level. It does not support a production or scientific approval claim. Project Owner decisions are required before moving beyond the read-only verification state.

No production implementation or approval action was taken as part of this review.
