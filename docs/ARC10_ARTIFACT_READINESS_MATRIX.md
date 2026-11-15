# ARC-10 Artifact Readiness Matrix

**Audit date:** 2026-11-15
**Authority boundary:** The repository contains a working local educational
mission API, but its documentation explicitly says it is not the ARC-10
production contract. The `ARC10_DECISION_APPROVAL_REGISTER.md` states that no
decisions are approved and that production API/client implementation remains
blocked. Drafts and local implementation details below are not canonical.

| # | Required artifact | Exists? | Exact source and version/status | Authoritative? | Formal approval? | Missing information | Safe for production implementation to depend on? |
|---:|---|---|---|---|---|---|---|
| 1 | API endpoints, methods, and routes | Partial: local demo routes exist | `src/quantum_space_agi/mission_demo/api.py`; local `/api/v1` demo, described in `docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md`; not an ARC-10 contract | **No** — local only | **No approval evidence** | Production service/repository, approved use case, paths/methods, auth, compatibility and ownership | **No** |
| 2 | Request/response DTOs | Partial: strict local Pydantic DTOs exist | `src/quantum_space_agi/mission_demo/dto.py`; local demo schema; local API guide describes request and response fields | **No** — local only | **No approval evidence** | Canonical schema, field semantics/nullability, version policy, unknown-field handling, domain review | **No** |
| 3 | Unified mission result structure | Partial: local `MissionRunResponseDTO` exists | `src/quantum_space_agi/mission_demo/dto.py`; local mission run response is versioned by the demo URL, not approved for production | **No** | **No approval evidence** | Production top-level result fields, statuses, provenance, limitations, component compatibility | **No** |
| 4 | Validation and error formats | Partial: local error DTO/handler and documented local behavior exist | `src/quantum_space_agi/mission_demo/api.py`, `dto.py`, and `docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md`; local demo status/error mapping | **No** | **No approval evidence** | Canonical status/code/body, valid-empty semantics, field errors, redaction and upstream failure rules | **No** |
| 5 | Local backend setup and base URL | Yes for the local educational demo | `docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md`; loopback `http://127.0.0.1:8765/`; Python module startup; local-only | **No production authority** | No production approval evidence | Production/local-team target, configurable environments, deployment ownership and policy | **Yes, only to reproduce the local demo; no for production** |
| 6 | Verified synthetic request/response examples | Partial | Synthetic request example and response description in `docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md`; response assertions in `tests/mission_demo/test_api.py`; local demo only | **No** | **No approval evidence** | A complete canonical request-and-response fixture, schema/version reference, named reviewers, and provenance approval | **No** |

## Existing records and their limits

- `docs/ARC09_BACKEND_DATA_CONTRACT_REQUEST.md` is a request for decisions and
  authoritative contracts, not a published contract.
- `docs/ARC09_API_INTEGRATION_DECISION_REQUEST.md` records unresolved
  integration decisions; it does not authorize implementation.
- `docs/ARC10_DECISION_APPROVAL_REGISTER.md` is a tracking register, not an API
  contract or architecture approval. It says no decision is approved and
  production API/client integration is blocked.
- `docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md` explicitly identifies its routes
  and schemas as a local educational demo, not an ARC-10 production API.
- The remote `origin/arc/10-api-integration` tip observed in this audit is
  `61d8c520b84cb7f28e0c7ba61863649bafe8c61c`; this hash does not establish
  that any contract is approved.

## Closure requirements

For each artifact, ARC-10 should provide or link the canonical source, a
version and owner, explicit DRAFT/APPROVED status, decision/review evidence,
and representative examples where applicable. Production use is allowed only
after the designated authority records formal approval and the project owner
authorizes implementation against the confirmed repository and branch.
