# ARC-10 Architecture Decision Record v0.1

## 1. Document Metadata

| Field | Value |
|---|---|
| Document title | ARC-10 Architecture Decision Record |
| Version | v0.1 |
| Status | **APPROVED WITH CONDITIONS — INTERNAL PROJECT DIRECTION** |
| Decision date | 13 November 2026 |
| Decision owner | Project Owner — NASAQ_26 |
| ARC | ARC-10 API Integration |
| Technical coordination owner | Rafi, subject to the explicit written-acknowledgement condition recorded in the decision reconciliation |
| Canonical location | **NOT YET DESIGNATED** |
| Final architecture approval authority | External/governance authority remains to be verified |

This ADR records the supplied Project Owner decision and its limits. It is a local working document, not a canonical governance record, final architecture approval, external governance approval, production approval, or deployment authorization. Do not alter D-01–D-16 numbering or the D-04/D-05 mapping.

## 2. Decision Summary

> **PROVISIONAL INTERNAL TECHNICAL DIRECTION — NOT PRODUCTION APPROVAL**

- Architecture: **Modular Monolith**
- Framework: **FastAPI**
- ASGI server/runtime: **Uvicorn**
- Implementation language: **Python**

The supplied Project Owner response classifies the architecture/framework/runtime direction as **APPROVED WITH CONDITIONS** for internal project direction. It authorizes internal technical preparation and supports API contract drafting within the stated scope. It does **not** authorize production implementation, deployment, public exposure, or repository-specific changes before the target and integration conditions are confirmed.

The contract-drafting direction for `POST /api/v1/dataset-validations` is **API CONTRACT DRAFTING AUTHORIZED — FINAL CONTRACT APPROVAL PENDING**. The endpoint is not a production route at this stage.

## 3. Context

The current `arc/10-api-integration` workspace is a planning/documentation workspace. The target repository, owner, branch, and integration boundary for implementation have not been confirmed. The separate ARC-08 checkout contains reusable domain capability; it is not automatically the ARC-10 implementation target.

ARC-08 includes a schema-based dataset structural validator. Verified domain behavior includes checking declared field presence, nullability, and exact Python types; returning schema-versioned validation reports with zero-based record indices; and reporting findings without coercing or dropping rows. Its `Dataset` construction requires `Provenance`. These are local Python-domain contracts, not an HTTP API and not evidence of scientific validity, source authenticity, or caller-provided provenance truth. The existing domain implementation and ARC-03 models are not changed by this ADR.

The first API operation authorized for contract drafting is mechanical structural validation of caller-supplied records against a selected schema:

`POST /api/v1/dataset-validations`

Its final request/response contract, schema IDs/content, security policy, and implementation target remain unresolved. The operation must not be represented as scientific validation or eligibility analysis.

## 4. Architectural Principles

The following are principles for the proposed internal design. They do not create implementation authorization.

1. **Modular boundaries:** keep transport, request/response DTOs, application orchestration, schema selection, domain validation, and operational concerns separable.
2. **Transport/domain separation:** HTTP parsing and response mapping must not be embedded in scientific/domain validation logic.
3. **Reuse verified domain capability:** where approved and compatible, call an existing validator rather than copying its validation rules into a route. An adapter may be needed; its location is not selected until the target is known.
4. **No unnecessary persistence:** the current proposal requires no persistence for the first validation operation unless later requirements establish a need.
5. **Synchronous initial operation:** synchronous execution is the current drafting direction, conditional on approved resource limits. It is not an unconditional workload guarantee.
6. **Explicit provenance semantics:** caller-declared metadata stays visibly unverified and separate from server-observed request facts.
7. **Determinism where supported:** the schema-based ARC-08 validator is deterministic for identical inputs and schema. A future transport serializer must define its own determinism and compatibility requirements.
8. **Structural result only:** mechanical structural validation must not be described as scientific validation, scientific eligibility, physical plausibility, or mission readiness.
9. **No source or rights overclaim:** neither the validator nor provenance declarations establish NASA authenticity, data rights, or authorization to access, retain, or redistribute data.

## 5. Proposed Logical Modules

These are conceptual boundaries only; no code is created here.

| Module/boundary | Status | Responsibility / evidence limit |
|---|---|---|
| API/transport layer | **Proposed ARC-10 component** | Receives the eventual HTTP request and maps the approved contract to application calls. No framework app, route, or server exists in the confirmed ARC-10 planning workspace. |
| Request/response DTO layer | **Proposed ARC-10 component** | Defines wire shapes after contract review. No production DTO or serialization contract is approved. |
| Application/service layer | **Proposed ARC-10 component** | Selects an approved schema and orchestrates one validation operation. Exact service boundary and validator choice remain to be documented in the contract. |
| Domain/scientific validation capability | **Existing verified capability in separate ARC-08 checkout** | ARC-08 has schema-based structural validation. Its report and index behavior are domain facts; no scientific interpretation is implied. ARC-08 is not the ARC-10 target by default. |
| Domain capability adapter | **Proposed ARC-10 component** | Would map approved DTOs to the selected validator without changing validation semantics. Placement and provenance handling depend on target and contract decisions. |
| Schema catalog | **Design authorized with conditions; implementation/content unresolved** | Static, read-only allowlist design; only explicitly reviewed IDs/versions, immutable released versions, unknown IDs/versions rejected. No actual schema ID/content has been approved. |
| Provenance handling | **Proposed ARC-10 component; policy approved in principle with constraints** | Distinguishes caller-declared unverified provenance from server-observed receipt time. Must not modify ARC-03 models or authenticate caller declarations. |
| Error mapping | **Proposed ARC-10 component** | Drafts HTTP behavior from the supplied contract-drafting direction. Final error envelope/versioning remain pending review. |
| Configuration/security boundary | **Unresolved/deferred** | Security/privacy/platform/release authorities and requirements are not yet established. Do not invent auth, CORS, secrets, retention, logging, or resource policy. |
| Tests | **Test planning authorized; executable API tests pending** | Domain behavior can be tested using ARC-08 contracts. HTTP/service acceptance tests depend on target, DTO, schema, security, and operational decisions. |

## 6. Framework and Runtime Rationale

The supplied internal technical direction is **FastAPI + Uvicorn + Python** within a Modular Monolith. The rationale is limited to technical fit, not measured performance:

- Python aligns with the existing ARC-08 scientific/domain capability.
- FastAPI supports typed request/response model development and OpenAPI-based contract preparation.
- Uvicorn supplies an ASGI server/runtime consistent with the provisional framework direction.
- A Modular Monolith keeps the proposed first integration within separable modules without requiring a distributed service topology.

No benchmark, deployment test, workload study, repository compatibility test, or production suitability assessment is claimed. The conditions in Sections 7 and 15 must be resolved before implementation.

## 7. Repository and Integration Boundary

| Item | Status |
|---|---|
| Target repository | **NOT CONFIRMED** |
| Target owner | **NOT CONFIRMED** |
| Target branch | **NOT CONFIRMED** |
| Integration boundary | **NOT CONFIRMED** |
| Current `arc/10-api-integration` workspace | Planning/documentation workspace |
| Separate ARC-08 checkout | Reusable source capability; not automatically the implementation target |

No production hosting, deployment topology, database, queue, or infrastructure is selected or implied. Repository compatibility and integration ownership cannot be evaluated until the target is named.

## 8. Persistence and Background Processing

For the first validation operation, current internal preparation proposes:

- No persistence is required.
- No background queue or worker is required for the initial synchronous operation.
- Synchronous execution is conditional on approved resource limits.

These are proposals for the initial scope, not immutable production decisions. Numeric resource limits have not been approved. Whether future workload requires long-running or asynchronous execution remains unresolved. No database, cache, queue, or retention behavior is authorized by this ADR.

## 9. Security and Operational Boundary

Security and operational requirements are **DEFERRED**. The responsible security, privacy, platform, and release authorities have not yet been identified and their approval requirements remain outstanding.

This ADR does not select or invent:

- Authentication or authorization.
- CORS or allowed origins.
- Rate, payload, record-count, depth, concurrency, timeout, or response-size limits.
- Retention, logging, redaction, or deletion policy.
- Secrets management or deployment configuration.

There is to be **no public production exposure**. Only synthetic data may be used for authorized non-production preparation. The requested security/operational proposal is a documentation deliverable, not approval of a policy.

## 10. Provenance Boundary

The supplied Project Owner decision is **MODIFY — APPROVED IN PRINCIPLE** for caller-declared provenance only under these constraints:

- Caller-declared dataset identity/source, retrieval timestamp, and data format are explicitly labeled **unverified caller-supplied information**.
- Server-observed request receipt time is separately identified and semantically distinct.
- Server receipt time must never replace caller-declared `retrieved_at`.
- No declaration is presented as authenticated source evidence.
- Protected ARC-03 data models remain unchanged.

The final representation, requiredness, mapping, and disclosure of provenance remain subject to API contract review. Do not use fabricated values to satisfy the existing ARC-08 `Dataset` constructor.

## 11. Schema Catalog Boundary

A static, read-only allowlist design is approved with conditions for preparation:

- Schema IDs and versions must be explicitly reviewed.
- Released schema versions are immutable; changes require a new version.
- Schema ownership and review responsibilities must be documented.
- Unknown IDs/versions are explicitly rejected with no silent fallback.
- Arbitrary caller-defined schemas are unsupported in the initial release.
- **No actual schema ID or schema content is approved yet.**

This ADR authorizes catalog design, not catalog implementation or publication of invented schemas.

## 12. First API Use Case

**Contract-drafting direction:** `POST /api/v1/dataset-validations`
**Purpose:** Mechanical structural schema validation only.

The supplied Project Owner response authorizes drafting these behaviors:

- Malformed request → HTTP 400.
- Empty `records` → HTTP 422.
- Validly processed records containing structural validation findings → HTTP 200 with a report indicating `is_valid=false`.
- Unsupported schema ID/version → explicit error; no silent fallback.
- Synchronous execution only under approved resource limits.
- Final error-envelope and versioning definitions require documentation and review.

No exact error JSON schema is defined here. These behaviors are contract-drafting input, not a final wire contract or production endpoint. The operation does not claim scientific validation, NASA authenticity, scientific eligibility, or data-rights authorization.

## 13. Alternatives Considered

- **Flask:** a plausible Python framework alternative. It was not selected by this internal direction; no comparative benchmark is claimed.
- **Separate microservices:** an alternative deployment/architecture style. A Modular Monolith is preferred for the bounded first integration because it retains module boundaries without presuming distributed deployment infrastructure. This is not a production topology decision.
- **Background/queue-first architecture:** an alternative for workloads requiring deferred or long-running work. The first operation is currently drafted as synchronous, conditional on approved limits; workload evidence and thresholds are not yet available.

The provisional direction favors FastAPI + Uvicorn + Python in a Modular Monolith because it aligns with the existing Python domain capability and supports typed contract preparation while keeping the first integration relatively bounded. This is qualitative rationale only; there are no benchmark or deployment results.

## 14. Decision Consequences

### Expected benefits

- A clear conceptual boundary for the first operation.
- A typed API contract direction suitable for review.
- Reuse of an existing structural-validation capability rather than duplicating its rules.
- A bounded first integration proposal.
- A straightforward basis for contract and synthetic integration-test preparation.

### Tradeoffs and remaining costs

- FastAPI/Uvicorn dependencies would need to be introduced later in an approved target.
- The target repository and integration boundary remain unresolved.
- Security and operational design is incomplete.
- Schema catalog ownership and actual schema contents remain unresolved.
- Provenance representation and final contract details remain pending.
- Production hosting, deployment, and release decisions remain unresolved.

## 15. Conditions Before Implementation

No repository-specific implementation may begin until the applicable gates are explicitly resolved and recorded. At minimum:

- Target repository, owner, branch, and integration boundary.
- Repository compatibility, dependency constraints, and deployment requirements.
- Approved security and operational requirements from responsible authorities.
- Reviewed schema IDs/content and documented ownership/review responsibilities.
- Final provenance representation details, consistent with Section 10.
- Final API contract approval.
- Canonical contract location and final approval authority.
- Explicit implementation authorization for the confirmed target.

The architecture/framework direction does not waive any of these conditions.

## 16. Approval Status

| Item | Status | Scope/qualification |
|---|---|---|
| Architecture direction | **APPROVED WITH CONDITIONS** | Internal project direction only; not final external/governance or production approval. |
| Framework | **APPROVED WITH CONDITIONS** | FastAPI provisional internal direction; verify target compatibility and dependencies. |
| Runtime | **APPROVED WITH CONDITIONS** | Uvicorn provisional internal direction; verify deployment requirements. |
| Language | **APPROVED WITH CONDITIONS / INTERNAL DIRECTION** | Python; subject to target/integration conditions. |
| API contract drafting | **APPROVED** | Drafting only under REQ-ARC10-07. |
| Final API contract | **PENDING** | Final review/approval not supplied. |
| Production implementation | **BLOCKED** | No production implementation authorization. |
| Production deployment | **BLOCKED** | No deployment authorization or approved operational design. |
| Target repository | **DEFERRED / NOT CONFIRMED** | Repository, owner, branch, and boundary remain unspecified. |
| Security/operations | **DEFERRED** | Authorities and requirements remain to be established. |
| Canonical governance register | **PENDING** | Not designated; this ADR is not canonical. |
| D-04/D-05 | **OPEN** | Preserve existing numbering and mapping; no reconciliation is made here. |

## 17. Decision Traceability

| Request-local decision | ADR treatment |
|---|---|
| REQ-ARC10-01 — Implementation target | Section 7 records the target repository, owner, branch, and integration boundary as not confirmed; Section 15 makes them pre-implementation conditions. |
| REQ-ARC10-04 — Contract ownership/location | Section 1 records Rafi's proposed coordination role subject to acknowledgement; canonical location and final approval authority remain unresolved. No D-number changes. |
| REQ-ARC10-05 — Framework/runtime | Sections 2, 6, and 16 record the conditional internal Modular Monolith/FastAPI/Uvicorn/Python direction. |
| REQ-ARC10-06 — Security/operations | Section 9 records the deferred status, prohibited assumptions, no-public-exposure boundary, and synthetic-only non-production preparation. |
| REQ-ARC10-07 — API behavior | Sections 2 and 12 record contract-drafting authorization and the supplied operation/status direction; final contract remains pending. |

These request-local identifiers are not canonical D-01–D-16 register entries. The D-04/D-05 discrepancy remains open.

## 18. Open Questions / Risks

- Which repository, owner, branch, and integration boundary are designated for implementation?
- Who has final architecture and API contract approval authority, and where is the canonical contract location?
- Will Rafi provide the explicit written acknowledgement required for the proposed coordination-owner designation?
- Which actual schema IDs/versions and definitions will be reviewed, and who owns that review?
- What final DTO and provenance representation preserves the unverified-caller versus server-observed distinction without changing ARC-03?
- Which security, privacy, platform, and release authorities will define access control, logging/retention, and operational requirements?
- What evidence supports numeric resource limits and synchronous execution for the target environment?
- The canonical governance register is not designated and D-04/D-05 remains open; this ADR does not resolve either issue.

These are evidence-supported open items from the supplied Project Owner decision and current ARC-10 planning documents. No owner, infrastructure, approval, or measured result is invented here.

## 19. Next Step

The next authorized documentation deliverable is **API Contract v0.1**. Draft it using the supplied contract-drafting direction and the explicit limits in this ADR. Keep it non-canonical and clearly marked pending final approval. Do not implement the API, add dependencies, change protected ARC-03/ARC-08 files, or deploy anything as part of that drafting step.
