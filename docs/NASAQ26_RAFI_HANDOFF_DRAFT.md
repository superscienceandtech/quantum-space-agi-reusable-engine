# NASAQ26 Handoff Draft — Rafi (ARC-10 API Contract)

**Status:** Draft for the Project Owner to send or revise. No message was sent
and no access or permissions were changed.

## Repository and scope

- Repository remote observed: `https://github.com/superscienceandtech/quantum-space-agi-reusable-engine.git`
- Remote ARC-10 branch observed: `origin/arc/10-api-integration` at
  `61d8c520b84cb7f28e0c7ba61863649bafe8c61c`.
- The repository's `ARC10_DECISION_APPROVAL_REGISTER.md` says no decisions
  are approved and that backend/API implementation and ARC-09 production
  client integration remain blocked.
- The existing `/api/v1` service and DTOs are a synthetic local educational
  demo. `docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md` explicitly says they are not
  the ARC-10 production API contract.
- Prepare contract artifacts and decision requests only until the designated
  authority records approval and the Project Owner separately authorizes
  production implementation.

## Six required contract artifacts

| # | Artifact | Current evidence | Gap to close |
|---:|---|---|---|
| 1 | API endpoints, methods, and routes | Local demo routes in `src/quantum_space_agi/mission_demo/api.py`; local demo table in `docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md` | Select product use case and canonical backend; approve operation names, methods, paths, auth, ownership, and versioning |
| 2 | Request/response DTOs | Local strict Pydantic DTOs in `src/quantum_space_agi/mission_demo/dto.py`; request and field descriptions in the local demo guide | Approve exact field/type/nullability/constraint semantics, compatibility, unknown-field rules, and representative schema examples |
| 3 | Unified mission result structure | Local `MissionRunResponseDTO` with mission, resource evaluation, and trajectory data | Approve production top-level result, provenance/limitations, statuses, versions, and how ARC-05/ARC-08 outputs compose |
| 4 | Validation and error formats | Local error DTO/handlers and error table in the local demo guide | Approve HTTP statuses, stable codes/body, field details, valid-empty behavior, redaction, and upstream/internal error mapping |
| 5 | Local backend setup and base URL | Local loopback startup documented at `http://127.0.0.1:8765/` | Confirm authoritative local backend repository/branch, environment configuration, startup/health check, deployment owner, and production URL policy |
| 6 | Verified synthetic request/response examples | Synthetic request and response description in the demo guide; response assertions in `tests/mission_demo/test_api.py` | Publish a complete contract-versioned request and response fixture, validate it against the approved schema, and record scientific provenance/limitations |

All six existing implementations/examples are local-demo evidence, not
formally approved production artifacts. The detailed artifact inventory is
in `ARC10_ARTIFACT_READINESS_MATRIX.md`.

## Contract decisions to confirm

1. Who owns the canonical API contract and where is its source of record?
2. Which backend repository, branch, runtime, and first approved consumer/use
   case are in scope?
3. What route/method/version policy and compatibility rules are approved?
4. What are the exact request, response, and unified mission-result DTOs?
5. Which ARC-05 model outputs and ARC-08 evaluation fields are supported,
   with what units, provenance, policy state, and limitations?
6. What are the validation, error, and valid-empty response semantics?
7. Which environments and base URLs are approved, and what startup,
   authentication, CORS, timeout, and operational constraints apply?
8. Who reviews scientific semantics and who records formal approval?

Do not fill these answers by copying local demo behavior unless the authorized
contract owner explicitly adopts it.

## Evidence required before backend integration

- A versioned canonical contract document/schema in an approved repository.
- Named contract owner, reviewers, and approval record.
- Explicit product scope and confirmed frontend/backend repository and branch.
- Complete synthetic request/response examples that validate against the
  contract and label synthetic/model-derived information and limitations.
- API and contract tests covering success, validation, empty, and server
  failure semantics.
- Project Owner authorization for production implementation distinct from
  permission to draft the contract.

## Drafting versus implementation approval

Rafi may prepare contract options, DTO drafts, examples, and tests labeled
**DRAFT / NOT CANONICAL** for review. Draft completion alone does not approve
the service architecture, establish contract authority, authorize production
backend implementation, or authorize ARC-09 to integrate against it. Wait for
formal contract approval and separate Project Owner implementation
authorization before production code changes.
