# ARC-10 Project Owner Decision Reconciliation and Execution Plan

**Decision date:** 13 November 2026
**Decision source:** Project Owner — NASAQ_26, supplied decision response
**Document status:** Reconciliation of supplied decisions and a documentation execution plan. This document is not a canonical governance register, final API contract, external governance approval, or production implementation authorization.

The supplied Project Owner response is treated as authoritative evidence for the seven request-local REQ-ARC10 items in the stated scope. The classifications below preserve the response wording. Request-local REQ identifiers are not D-01–D-16 register numbers.

## 1. Decision matrix

| Request ID | Decision (classification as supplied) | What is authorized now | What remains unresolved | Restrictions/dependencies | Affected deliverable(s) |
|---|---|---|---|---|---|
| REQ-ARC10-01 — Implementation Target | **MODIFY / DEFER** | Continue using the current ARC-10 workspace for planning and documentation. | Target repository, target owner, branch, and integration boundary. | No repository-specific implementation until all four are explicitly confirmed. The ARC-08 checkout is reusable domain capability, not an automatically selected ARC-10 target. | Architecture Decision Record (ADR); implementation-target section of the remaining proposals. |
| REQ-ARC10-02 — Provenance Policy | **MODIFY — APPROVED IN PRINCIPLE** | A proposal may represent caller-declared provenance only when clearly labeled unverified caller-supplied information. | Final fields, request representation, whether provenance is required, and approved disclosure/mapping. | Keep caller-declared dataset/source and caller-declared retrieval timestamp/format distinct from server-observed request receipt time. Receipt time must never replace `retrieved_at`. No authenticated-source claim. Do not modify protected ARC-03 models. | API Contract v0.1; DTO proposal; provenance representation proposal; test plan. |
| REQ-ARC10-03 — Schema Catalog | **APPROVE WITH CONDITIONS** | Prepare a static, read-only schema allowlist design. | Actual schema IDs/content, their reviewers, owners, and review responsibilities. | IDs and versions must be explicitly reviewed; released versions immutable; unknown IDs/versions rejected; arbitrary caller-defined schemas excluded from initial release. This decision approves no actual schema ID/content. | API Contract v0.1; DTO proposal; static schema catalog design; test plan. |
| REQ-ARC10-04 — Contract Ownership and Canonical Location | **MODIFY** | Rafi may be identified as proposed contract-drafting/technical-coordination owner, subject to explicit written acknowledgement; the Project Owner retains internal review/decision responsibilities within delegated scope. | Acknowledgement; final contract approval authority; canonical contract location. | Local package remains **NON-CANONICAL**. Do not alter D-01–D-16 or the D-04/D-05 mapping. | ADR; API Contract v0.1; governance/blocker sections of deliverables. |
| REQ-ARC10-05 — Framework and Runtime | **APPROVE WITH CONDITIONS** | Record this provisional internal direction: Modular Monolith, FastAPI, Uvicorn, Python. | Repository compatibility, dependency constraints, deployment requirements, and approved integration boundary. | Direction is internal and provisional; it is not external architecture approval or production approval. Verify conditions before any implementation. | ADR; API Contract v0.1 assumptions; implementation blocker checklist. |
| REQ-ARC10-06 — Security and Operational Requirements | **DEFER** | Prepare a security and operational requirements proposal for review; use synthetic data only for authorized non-production preparation. | Security, privacy, platform, and release authorities; approved policies and operational requirements. | No public production exposure; no invented auth/authz, CORS, numeric limits, retention, or logging policy. | Security/operations proposal; test plan; blocker checklist. |
| REQ-ARC10-07 — API Behavior | **MODIFY — APPROVED FOR CONTRACT DRAFTING** | Draft the first operation as `POST /api/v1/dataset-validations`, with the behavior below recorded as the supplied contract-drafting direction. | Final API Contract approval; final error envelope and versioning definitions; approved resource limits. | Synchronous execution only under approved limits. Do not claim scientific validation, NASA authenticity, scientific eligibility, or data-rights authorization. | API Contract v0.1; DTO proposal; error/HTTP mapping; validation/integration test plan. |

### REQ-ARC10-07 drafting behavior

- Malformed request: HTTP 400.
- Empty `records`: HTTP 422.
- Successfully processed records with schema-validation findings: HTTP 200 with a validation report indicating `is_valid=false`.
- Unsupported schema ID/version: explicit error; never silently fall back.
- Synchronous processing only under approved resource limits.
- API versioning and final error-envelope definitions remain subject to documentation and review.

These are authorized for **contract drafting** by the supplied decision. They do not constitute final contract approval, production implementation authorization, or permission to expose an endpoint.

## 2. Explicit decision-state distinctions

The following labels are kept distinct and are not collapsed into a generic “approved” status:

- **APPROVED:** API contract drafting is approved in the limited sense specified by REQ-ARC10-07; this is not approval of the finished contract. The REQ-ARC10-02 decision is **APPROVED IN PRINCIPLE**, not unconditional approval.
- **APPROVED IN PRINCIPLE:** caller-declared provenance may be considered only under the stated unverified-labeling and timestamp-separation constraints; detailed representation remains unresolved.
- **APPROVED WITH CONDITIONS:** the static schema allowlist design and provisional internal architecture/framework/runtime direction may be prepared, subject to their listed conditions. No actual schema ID/content or production architecture is thereby approved.
- **DEFERRED:** security and operational requirements require identified authorities and further review. Implementation target selection is also deferred under REQ-ARC10-01.
- **PENDING:** final API contract approval, canonical contract location, written acknowledgement of the proposed contract-drafting owner, external governance approval/authority verification, actual schema review, and resource-limit approval remain pending where applicable.
- **BLOCKED:** production API implementation, deployment, and public exposure remain blocked. The authorization gate must not be changed to READY based on this decision response.

“MODIFY” is preserved as the response classification for REQ-ARC10-01, REQ-ARC10-02, REQ-ARC10-04, and REQ-ARC10-07; it is not itself an approval status. REQ-ARC10-06 remains **DEFER**.

## 3. Architectural direction

> **PROVISIONAL INTERNAL TECHNICAL DIRECTION — NOT PRODUCTION APPROVAL**

- Architecture: Modular Monolith
- Framework: FastAPI
- ASGI server/runtime: Uvicorn
- Language: Python

Before implementation, verify compatibility with the explicitly designated target repository, dependency constraints, deployment requirements, and integration boundary. These directions do not authorize repository changes, production deployment, or public exposure.

## 4. API contract drafting direction

> **API CONTRACT DRAFTING AUTHORIZED — FINAL CONTRACT APPROVAL PENDING**

The first operation to describe in the draft is `POST /api/v1/dataset-validations`, subject to the REQ-ARC10-07 behavior above. The contract must distinguish malformed requests from completed structural-validation reports, and must state the unsupported-schema behavior. The operation is mechanical structural validation only. It does not establish scientific validation, scientific eligibility, NASA authenticity, source authenticity, or data-rights authorization.

## 5. Provenance semantics

The draft must preserve these constraints:

1. Caller-declared dataset identity/source, retrieval timestamp, and data format are unverified caller-supplied information.
2. Server-observed request receipt time is a separate observation with distinct semantics.
3. Server receipt time must never be substituted for caller-declared `retrieved_at`.
4. No provenance declaration is evidence of an authenticated source.
5. Do not modify ARC-03 models as part of this work.
6. Final API fields, requiredness, serialization, and disclosure remain pending contract review.

## 6. Static schema catalog direction

Prepare a design for a static, read-only allowlist with these conditions:

- Schema IDs and versions must be explicitly reviewed before they are supported.
- Released schema versions are immutable; a changed schema requires a new version.
- Schema ownership and review responsibilities must be documented.
- Unknown schema IDs and versions are rejected, with no silent fallback.
- Arbitrary caller-defined schemas are outside the initial release.
- **No actual schema ID or schema content is approved by the supplied decision.**

The design deliverable may define the review and versioning process, but must not invent production schema IDs or contents.

## 7. Ordered execution plan for required deliverables

The following sequence is documentation preparation. It does not authorize implementation. Dependencies may require revisiting earlier drafts after decisions are supplied.

| Order / deliverable | Purpose | Current authorization status | Prerequisites | Dependencies | Unresolved items | Type |
|---|---|---|---|---|---|---|
| 1. Architecture Decision Record | Record the provisional Modular Monolith/FastAPI/Uvicorn/Python direction, alternatives/context, conditions, and open target/integration questions. | Documentation may be prepared; direction is **APPROVED WITH CONDITIONS** for internal technical planning only. | Supplied REQ-ARC10-01 and -05 decisions; inspect existing planning evidence. | Informs the API contract and any later target-specific work. | Target repository/owner/branch/integration boundary; compatibility, dependency, deployment checks. | Documentation-only. |
| 2. API Contract v0.1 | Draft the operation, request/response semantics, structural-validation boundary, and compatibility assumptions. | Drafting **APPROVED** under REQ-ARC10-07; final contract approval **PENDING**. | Provisional operation and status behavior in REQ-ARC10-07; ownership/location caveats in -04. | Depends on DTO, provenance, schema catalog, and error mapping drafts; iterate as they converge. | Final approval authority/location, versioning, exact wire details, resource limits, provenance requirements. | Documentation-only. |
| 3. Proposed request/response DTOs | Describe candidate transport fields and mapping without treating them as final. | Proposal preparation authorized as contract drafting; final DTO approval pending with the contract. | Contract v0.1 outline and known engine boundary. | Depends on provenance representation, schema-selection direction, and error/report mapping. | Exact fields, types, nullability, unknown-field policy, receipt-time field, and error envelope. | Documentation-only. |
| 4. Provenance representation proposal | Show how caller declarations remain visibly unverified and distinct from server observations. | Proposal preparation allowed; policy **APPROVED IN PRINCIPLE** only within REQ-ARC10-02 constraints. | Supplied provenance decision; ARC-08 domain interface inspection. | Feeds DTO and contract; cannot require ARC-03 changes. | Requiredness, wire representation, privacy/disclosure and any adapter strategy. | Documentation-only. |
| 5. Static schema catalog design | Specify allowlist lifecycle, immutable releases, ID/version review, unknown-version rejection, and ownership/review process. | Design authorized **WITH CONDITIONS**; no schema content is approved. | REQ-ARC10-03. | Feeds DTO/schema selection and validation test plan. | Named/assigned schema owner and reviewers; reviewed actual IDs and definitions. | Documentation-only. |
| 6. Error and HTTP status mapping | Map supplied malformed/empty/validation-finding/unsupported-schema directions into a draft error/result model. | Drafting authorized under REQ-ARC10-07; final mapping and envelope review pending. | Contract v0.1 and DTO proposal. | Depends on schema lookup and request-validation semantics. | Final envelope, versioning, internal-error behavior, and approval authority. | Documentation-only. |
| 7. API validation/integration test plan | Convert approved draft semantics into layered synthetic test cases, preserving ARC-08 behavior without implying it is API behavior. | Test planning is authorized; executable API acceptance criteria wait for final contract and target. | This decision reconciliation, Prompt 2 test catalog, DTO/contract/error drafts. | Depends on final validator selection, schema catalog, limits, implementation target/framework. | Assertions for boundary errors, row indexes, serialization, limits, auth, and runtime integration. | Documentation-only now; implementation-related tests later. |
| 8. Security/governance/implementation blockers proposal | Present security/operational requirements for review and list unresolved governance/authorization prerequisites. | Proposal preparation authorized; REQ-ARC10-06 remains **DEFER**. | Identify unresolved topics and avoid assigning unidentified authorities. | Required before production requirements and implementation authorization can close. | Security/privacy/platform/release authority identities; policy, retention/logging, limits, deployment and release approval. | Documentation-only. |

## 8. Remaining blockers

The supplied decisions do not close these issues:

- **Target and integration:** target repository, target owner, target branch, and integration boundary are not confirmed.
- **Contract governance:** written acknowledgement of the proposed drafting owner is outstanding; final API Contract approval authority and canonical contract location remain unresolved.
- **Canonical register:** canonical governance register and its designating authority remain unresolved; the local decision package remains a **NON-CANONICAL WORKING MIRROR**.
- **Numbering:** D-04/D-05 discrepancy remains **OPEN**. Do not change D-01–D-16 numbering or the D-04/D-05 mapping.
- **Schema governance:** actual schema IDs/content and their assigned owners/reviewers have not been approved.
- **Security/operations:** security, privacy, platform, and release authorities remain to be identified; final security and operational requirements are deferred.
- **Resource limits:** approved numeric request, record, nesting, time, concurrency, and response limits are not supplied.
- **Provenance:** only in-principle constraints are given; final representation and requiredness remain to be specified and reviewed.
- **Production authorization:** production implementation, deployment, and public exposure remain **BLOCKED**. Contract-drafting authorization is not implementation authorization.
- **External governance:** no external governance approval is claimed; applicable authority and process must be verified.

## 9. What we can do now

We may prepare the eight documentation deliverables above: an architecture ADR, API Contract v0.1, DTO proposals, provenance proposal, static schema catalog design, error/status mapping, validation/integration test plan, and security/operational proposal.

We may not:

- Implement a production API, deploy it, or expose it publicly.
- Modify protected ARC-03 models or change ARC-08 implementation.
- Declare local governance material canonical or alter D-01–D-16 / D-04/D-05.
- Claim final API contract approval, production approval, scientific validation, source authenticity, data-rights authorization, or NASA permission.
- Invent authentication, authorization, CORS, retention/logging, or numeric resource limits.

Use synthetic data only for any later preparation expressly allowed by project direction. Do not treat a passing software test as a governance or scientific approval.

## 10. Decision traceability

| Request ID | Subject | Reconciled sections |
|---|---|---|
| REQ-ARC10-01 | Implementation target | Decision matrix; blockers; ADR and target dependencies. |
| REQ-ARC10-02 | Provenance | Decision matrix; provenance semantics; DTO/test dependencies. |
| REQ-ARC10-03 | Schema catalog | Decision matrix; static schema catalog direction; catalog/test dependencies. |
| REQ-ARC10-04 | Contract ownership/location | Decision matrix; blockers; canonicality and acknowledgement restrictions. |
| REQ-ARC10-05 | Architecture/framework/runtime | Decision matrix; architectural direction; ADR. |
| REQ-ARC10-06 | Security/operations | Decision matrix; security/governance proposal; blockers. |
| REQ-ARC10-07 | API behavior | Decision matrix; contract drafting direction; error mapping and test plan. |

These REQ identifiers are local traceability labels, not canonical D-number assignments.

## 11. Approval status summary

| Item | Status | Boundary |
|---|---|---|
| Internal architecture direction | **APPROVED WITH CONDITIONS** | Provisional internal technical direction only; target/deployment conditions remain. |
| API contract drafting | **APPROVED** | Drafting scope only, as specified by REQ-ARC10-07. |
| Final API contract | **PENDING** | Requires review and approval through an authority/process not yet established here. |
| Contract canonical location | **PENDING** | Do not treat the local package as canonical. |
| External governance approval | **PENDING / AUTHORITY TO BE VERIFIED** | No external approval is claimed. |
| Production implementation | **BLOCKED** | No implementation authorization. |
| Implementation target | **DEFERRED** | Repository, owner, branch, and boundary must be confirmed. |
| Security/operations | **DEFERRED** | Relevant authorities and requirements remain unresolved. |
| D-04/D-05 | **OPEN** | No mapping or numbering changes authorized. |
| Schema catalog design | **APPROVED WITH CONDITIONS** | Design only; no actual IDs/content approved. |
| Provenance policy | **APPROVED IN PRINCIPLE** | Only under explicit unverified declaration and timestamp-separation constraints. |

## 12. Next execution step

Prepare **Deliverable 1: the Architecture Decision Record** as a documentation-only draft. Record the provisional internal direction, its conditions, alternatives and unresolved target/integration dependencies. Keep the record non-canonical and make no repository-specific implementation changes. After that, proceed in dependency order through the remaining documentation deliverables; do not begin production implementation unless a separate explicit authorization closes its blockers.
