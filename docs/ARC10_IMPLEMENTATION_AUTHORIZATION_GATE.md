# ARC-10 Implementation Authorization Gate

**Assessment:** 2026-11-13
**Scope:** Repository evidence in the ARC-10 worktree and locally available ARC-09 refs. This is an evidence assessment, not an approval or authorization.

## 1. Gate result

**IMPLEMENTATION_GATE: BLOCKED**

No repository evidence reviewed contains a completed formal approval of the first production use case, target/consumer, contract owner, validator/provenance behavior, framework, endpoint and method, request/response contract, error behavior, security and data handling, resource limits, acceptance, or implementation authorization.

The ARC-10 documents are explicitly proposals, plans, and decision requests. The Project Owner's delegated authority for routine assigned engineering work, as described in task context, is not approval of the reserved architecture, product, security, or contract decisions. No production API implementation should begin on this evidence.

No item below is classified APPROVED. A recommendation, draft, role description, or technical review is not formal approval.

### Current-status clarification (local reconciliation)

This gate's matrix records its 2026-11-13 evidence assessment of formal/production approval. The current worktree also contains `docs/ARC10_PROJECT_OWNER_DECISION_RECONCILIATION_AND_EXECUTION_PLAN.md`, which records conditional internal direction for Modular Monolith/FastAPI/Uvicorn/Python and authorization to draft one operation with bounded behavior. Those statuses are narrower than formal production approval: final contract approval, target compatibility, security/operations, resource limits, deployment, and implementation authorization remain pending or blocked. The matrix below is retained as the gate assessment and must not be read as denying the later-recorded drafting scope. `IMPLEMENTATION_GATE: BLOCKED` remains the current production gate. The supplied decision is recorded evidence, not independently authenticated here.

## 2. Authority levels and evidence

- **Repository fact:** directly verifiable source, test, document, or commit/ref state.
- **Proposed engineering decision:** recommendation or draft in an ARC-10 planning document; it has no approval force.
- **Cross-ARC requirement:** dependency stated by ARC-09 documentation; it does not automatically authorize ARC-10.
- **Formal approval:** explicit authoritative decision in the repository permitting the particular scope. No such completed approval record was found in the inspected ARC-10 documents.

### ARC-09 evidence provenance

Previously available local refs identify origin/arc/09-visualization at 878cb81b69430cdf6c25c419edba587629537768 and origin/main at 9d65c9547e9c3c59f65c3b81265c7152c8385859; this assessment did not fetch or refresh refs.

The backend contract request, prototype handoff, and manual verification report exist in both refs with identical content hashes. The ARC-09 branch additionally contains docs/ARC09_DECISION_REGISTER.md and docs/ARC09_FINAL_DECISION_CONFIRMATION_REQUEST.md, absent from the inspected origin/main ref. The ARC-09 branch is not an ancestor of origin/main and the refs diverge, so branch-wide “newer” status cannot be inferred merely from main's later commit timestamp. For ARC-09 decision evidence, the ARC-09 branch is the more complete source; its decision register says required ARC-09 approvals remain pending/conflicting. That is a cross-workstream finding, not ARC-10 approval.

The ARC-09 backend contract request states that its proposed dashboard P0 is conditional, and deliberately supplies no endpoint, HTTP method, or schema. The prototype handoff says its values are synthetic/conceptual and it has no API/backend integration, persistence, authentication, or team approval. The manual verification report is scoped to prototype behavior and expressly does not establish production readiness or API integration.

## 3. Decision matrix

Classification is exactly one of: APPROVED, PROPOSED, PENDING, BLOCKED, NOT APPLICABLE.

| # | Decision item | Status | Evidence and reason |
|---:|---|---|---|
| 1 | First production use case | PROPOSED | Mechanical dataset validation is recommended in ARC10_USE_CASE_COMPARISON_AND_RECOMMENDATION.md and ARC10_PROJECT_DECISION_REQUEST.md; both label it proposed. No completed decision response exists. |
| 2 | Intended consumer/client | PENDING | ARC-09 is a possible consumer, but its production frontend and selected workflow are not confirmed. The ARC-09 contract request and ARC-10 decision request leave this open. |
| 3 | Production backend/service target | PENDING | ARC-10 readiness/architecture/implementation reports say the target repository/service remains unresolved. No target approval record found. |
| 4 | Contract owner | PENDING | ARC-10 decision package and decision request ask that an owner/canonical contract location be identified; no accepted owner record found. |
| 5 | Validator selection | PROPOSED | Contract-neutral service design recommends considering schema-based validation, pending contract approval, and records the legacy API as an alternative. |
| 6 | Provenance policy | PENDING | Schema-based validator requires Dataset/Provenance, while legacy record validator does not. Contract-neutral design forbids fabricated provenance and leaves policy open. |
| 7 | API framework | PENDING | Architecture proposal compares candidates but selects none; implementation reports framework decision as a gate. |
| 8 | Endpoint path(s) | PENDING | Endpoint requirements document marks paths illustrative/not approved; no authoritative route found. |
| 9 | HTTP method(s) | PENDING | Same draft document marks methods illustrative; ARC-09 request deliberately defines none. |
| 10 | Request schema | PROPOSED | Contract package and service design offer conceptual input fields/schema-selection ideas, explicitly not an approved request DTO. |
| 11 | Response schema | PROPOSED | Draft schema and contract package offer illustrative result concepts; no approved response DTO exists. |
| 12 | Error contract | PROPOSED | A conceptual taxonomy and illustrative error envelope exist, both explicitly pending approval. |
| 13 | API versioning policy | PROPOSED | Contract package recommends independent API versioning as a proposal; no selected policy or approval exists. |
| 14 | Authentication | PENDING | No authentication policy or implementation approved. ARC-10 reports classify it as unresolved. |
| 15 | Authorization | PENDING | No access-control policy or authorization implementation approved. |
| 16 | CORS policy | PENDING | No production frontend target or allowed-origin policy approved. |
| 17 | Resource limits | PROPOSED | Planning documents propose bounding bytes, rows, depth, compute and concurrency, but numeric limits and enforcement are unresolved. |
| 18 | Data handling/retention | PENDING | Privacy, logging/redaction, retention and deletion decisions are requested but not resolved. |
| 19 | Scientific field semantics | PENDING | Candidate structural validation could omit scientific interpretation, but first use case and any scientific-data scope are unapproved. If a purely structural use case is approved, scientific semantics may become not applicable to that operation. |
| 20 | Units | PENDING | No selected operation or data fields; ARC-09 requires unit definitions for any displayed metrics. Not applicable only if an approved scope has no unit-bearing values. |
| 21 | Timestamp/timezone rules | PENDING | Existing validators differ: legacy report has a generated timestamp; schema-based report has none. Wire timestamp semantics are unresolved. |
| 22 | Provenance representation | PROPOSED | Contract package proposes separating caller-declared from server-observed provenance. Required fields and representation remain unapproved. |
| 23 | Empty-result behavior | PENDING | Existing validators differ: schema-based empty dataset produces zero invalid rows; legacy validator reports empty_dataset. Service semantics have not been decided. |
| 24 | Invalid-input behavior | PROPOSED | ARC-10 docs propose distinguishing malformed input/service failure from completed validation findings, but exact rules and response behavior await contract approval. |
| 25 | Acceptance criteria | PROPOSED | Decision request lists measurable criteria explicitly requiring review/approval; no accepted criteria record found. |
| 26 | Backend implementation authorization | BLOCKED | Explicit implementation authorization for a production API is absent; reserved decisions remain open. Delegated routine execution authority is not a substitute. |
| 27 | Frontend/API integration authorization | BLOCKED | No confirmed production client/target or approved API contract; ARC-09 prototype is not production integration authorization. |
| 28 | Production deployment authorization | BLOCKED | No deployment target, operational/security policy, or release approval found. |

## 4. What is and is not formally approved

**Formally approved:** No production API decision in the required matrix is supported as approved by the inspected repository evidence.

**Verified facts:** ARC-08 has reusable Python data/schema/quality interfaces, but they are not HTTP APIs; two validator interfaces differ in provenance, output and row-index conventions. ARC-09 requests a backend contract and its prototype is synthetic/conceptual, not a production client. ARC-10 planning documents identify candidate options and unresolved gates.

**Proposed only:** Mechanical validation as a candidate use case; schema-based validator as a candidate; conceptual service input/output/error ideas; layered backend architecture; general resource-boundary and privacy recommendations.

**Not evidence of approval:** Contributor roles, delegated execution authority for routine work, technical recommendations, test plans, synthetic fixtures, ARC-09 prototype behavior, or an unfilled approval template.

## 5. Required decision and approval handoff

The following are the actual unresolved decisions needed to reconsider the implementation gate. Options below are discussion choices, not selections.

| Required decision | Why it matters | Existing proposal | Options for decision-maker | Current unresolved issue |
|---|---|---|---|---|
| First use case and consumer | Defines whether a service is needed and who uses it. | Mechanical validation is proposed; Dashboard Summary and process liveness are alternatives. | A: select mechanical validation; B: select Dashboard Summary after metric/source definition; C: select process liveness with explicit operational semantics; D: defer API. | No selected product need/consumer. |
| Target service and contract owner | Establishes where the work belongs and who controls the authoritative contract. | Planning documents request target and accountable owner. | A: identify existing service/repository and owner; B: authorize a new target and owner; C: defer. | Neither target nor owner is recorded as approved. |
| Service boundary, validator and provenance | Determines inputs, truthful metadata and report/index mapping. | Contract-neutral design prefers considering schema-based validation; legacy record validator is an alternative. | A: schema-based API with an approved truthful provenance policy; B: legacy record validator with explicit schema mapping; C: another specifically reviewed boundary. | No validator or provenance policy selected. |
| API contract and framework | Establishes client/server compatibility. | Framework-neutral DTO concepts; framework options are only compared. | Approve owner-maintained route/method/version, request/response and error contract plus a framework; or defer. | No final endpoint, method, wire schema, error contract or framework. |
| Security and operations | Prevents unsafe exposure and unbounded or unintended data handling. | Proposals recommend least privilege, redacted logging and bounded inputs. | Approve auth/authz/CORS, configuration, logging/retention, resource/time/concurrency limits and deployment expectations; or keep operation internal/defer. | No concrete policy, limits, or authorization. |
| Acceptance and implementation authorization | Separates implementation from acceptance/release. | Proposed acceptance criteria are in the project decision request. | Approve measurable acceptance criteria, reviewers/process, then explicitly authorize the bounded implementation. | No completed approval response or authorization record. |

A decision-maker should record each selected option, required revisions, authority, date/reference and explicit authorization in the project's authoritative decision location. This document does not identify or sign on behalf of the decision-maker.

## 6. Next action

**Single most important next action:** obtain a completed Project Owner decision response selecting or rejecting the first use case and consumer, and identifying the target service and contract owner. The remaining API, provenance, security and operational decisions can then be finalized against that scope.

Do not begin production implementation based solely on this gate document or on the presence of proposals. Reassess the gate after explicit repository evidence of the required decisions is supplied.

## 7. Scope and status

This assessment did not modify ARC-08 or ARC-09, make network requests, add code, or authorize production work. No formal approval was invented.
