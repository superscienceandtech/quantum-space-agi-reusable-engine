# ARC-10 Consolidated Project Owner Decision Request

**Purpose:** Request decisions and assignments needed to finalize the proposed first API contract and determine whether authorized non-production work can safely proceed.

**Status:** Decision request only. Existing approvals below are limited to their stated scope. This document does not record a response to this consolidated request and does not approve a final API contract or production work.

**Request-local identifiers:** REQ-ARC10-01 through REQ-ARC10-07 organize this request only. They are not canonical D-01–D-16 identifiers and do not resolve the documented D-04/D-05 discrepancy.

## 1. Scope and response instructions

Please select one response for each request: **APPROVE / REJECT / MODIFY / DEFER**. For MODIFY, provide the revised direction. For DEFER, identify the condition or evidence needed to revisit it. A blank response is not approval.

The requests distinguish decisions from recommendations. The Project Owner may decide within their authority or identify the responsible authority. If authority is not established, it is recorded as **NOT IDENTIFIED**; this request does not assign it.

## 2. Verified current position

### ARC-10 worktree snapshot

At preparation, the ARC-10 worktree was on arc/10-api-integration, HEAD 69c8e711b9e8f3af5c39428e23828ade9e55da2a. The tracked baseline is a documentation-planning repository without a Python package, API routes, server framework, deployment configuration, or implementation. Nine ARC-10 planning/governance documents were present as untracked working-tree files. This is a local snapshot, not live GitHub verification or a canonical record.

### Separate ARC-08 domain capability

The inspected separate ARC-08 checkout provides the following relevant evidence:

- quantum_space_agi.data.schemas.validate_dataset(Dataset, DataSchema) checks declared field presence, nullability, and exact Python type; reports zero-based indexes; does not coerce or drop rows; and requires Dataset/Provenance. It does not establish scientific validity.
- Dataset requires Provenance with dataset ID, DataSource, timezone-aware retrieval time, and DataFormat. The model validates structure, not truth or authenticity. Dataset copies top-level record mappings but does not deep-freeze nested values.
- A different record-oriented validator, exported as quantum_space_agi.data.validate_records, does not require Dataset provenance, but has a different report and one-based indexes. The two interfaces are not interchangeable without an explicit choice.
- No API schema catalog, schema owner, API serializer, HTTP status mapping, or service-level provenance policy was found in the inspected code.

Structural validation is not scientific validation, eligibility, source authentication, or authorization to process or retain data.

### Existing ARC-10 evidence and governance status

- The Project Owner evidence-package acceptance is recorded as ACCEPTED WITH DOCUMENTED LIMITATIONS in docs/ARC10_PROJECT_OWNER_EVIDENCE_ACCEPTANCE.md. It applies to that evidence package only.
- The supplied Project Owner decision approves Modular Monolith as an internal direction with conditions, authorizes internal API contract development, and authorizes Rafi to prepare proposals and authorized non-production activities. It does not approve the final API contract, security policy, or production implementation/deployment.
- The selected first use case and proposed endpoint below come from the supplied Deliverables 3–5 context. They remain PROPOSED, pending final API contract approval.
- docs/ARC10_EVIDENCE_INDEX.md records the canonical register as not located in inspected material, its designating authority as unidentified, the D-04/D-05 discrepancy as open, and the local decision package as a non-canonical working mirror. Do not treat that package as canonical or renumber its entries.
- The existing authorization gate reports production implementation as BLOCKED. No live GitHub state is claimed here.

## 3. Decisions already supplied and their limits

| Supplied decision | Status and exact scope | Does not approve |
|---|---|---|
| Modular Monolith | APPROVED WITH CONDITIONS as internal architecture direction | Framework/runtime, final API contract, deployment, or production integration |
| Internal API contract development | APPROVED | Final API Contract Version or production API behavior |
| Rafi’s preparation authority | Authorized to prepare the first use case, endpoint/method proposals, DTOs, schemas, validation/error handling, versioning proposals, and integration/acceptance tests, subject to stated boundaries | Scientific/data-rights/security decisions outside delegation; ARC-03 changes; production implementation/deployment |
| Evidence package | ACCEPTED WITH DOCUMENTED LIMITATIONS | Architecture/contract approval, live GitHub verification, canonical register designation, or implementation authorization |

No response to the seven requests in this document is recorded. The supplied decisions do not settle the questions below.

## 4. Proposed first use case and endpoint

**First API use case:** Mechanical validation of caller-supplied records against one selected, versioned structural schema.

**Proposed endpoint:** POST /api/v1/dataset-validations.

Both are PROPOSED — PENDING FINAL API CONTRACT APPROVAL. The operation would expose only structural validation; it would not perform quality analysis, preprocessing, model evaluation, scientific eligibility, physical plausibility, NASA-source verification, or data-rights decisions. The endpoint and method are not approved production routes.

## 5. Outstanding decision matrix

The request-local IDs below are not D-number assignments in any governance register.

### REQ-ARC10-01 — Implementation target

- **Exact question:** Which repository is the designated ARC-10 implementation target, who owns it, and which branch/integration boundary should be used? Is the current ARC-10 worktree only the planning workspace?
- **Evidence/status:** ARC-10 tracked HEAD contains no implementation package or backend. The separate ARC-08 checkout contains reusable domain code but is not hereby designated as the ARC-10 implementation target. UNRESOLVED.
- **Recommendation — PROPOSED:** Identify the repository owner and target before any code changes; confirm whether the ARC-10 worktree remains documentation-only. No repository is selected here.
- **Alternatives:** Existing approved service repository; a separately designated backend repository; or defer implementation until target selection.
- **Consequence if deferred:** No implementation path can be safely chosen; risk of modifying the wrong checkout or conflicting with co-owner work.
- **Required authority:** Project Owner or project/engineering authority designated by the project. Specific repository-designating authority is NOT IDENTIFIED in inspected material.
- **Response:** APPROVE / REJECT / MODIFY / DEFER — target repository: ___; owner: ___; branch/integration boundary: ___; authority/reference: ___

### REQ-ARC10-02 — Provenance policy

- **Exact question:** May the first API accept caller-declared provenance? If so, how must it label those claims as unverified; which required facts must be supplied; and how must caller-declared values be distinguished from server-observed facts? Confirm that request-received time must not be substituted for retrieved_at.
- **Evidence/status:** Existing Dataset construction requires dataset_id, DataSource, timezone-aware retrieved_at, and DataFormat. The model does not authenticate them. The NASA adapter’s observed provenance is specific to its provider operation and cannot be copied to arbitrary submitted records. UNRESOLVED / BLOCKING for the schema-based validator path.
- **Recommendation — PROPOSED:** Consider caller-supplied declarations only when truthful, explicitly labeled as caller declarations, and never presented as authenticated. Keep API receipt time separate; do not map it to retrieved_at absent an explicit semantic decision. This is not approved.
- **Alternatives:** Select a different existing validation boundary if approved and if its behavior is suitable; or defer this use case. A domain-model change would require separate ARC-03 authority and is not requested here.
- **Consequence if deferred:** No truthful construction/mapping to the selected Dataset-based validator; do not fabricate provenance to proceed.
- **Required authority:** API contract owner and relevant data/provenance authority; roles are NOT IDENTIFIED for this decision.
- **Response:** APPROVE / REJECT / MODIFY / DEFER — accepted provenance policy and field semantics: ___; declaration/observation distinction: ___; authority/reference: ___

### REQ-ARC10-03 — Schema catalog ownership and first-release contents

- **Exact question:** Who owns and approves schemas? Which schema IDs and versions, if any, are approved for first release? Who reviews schema changes? Is a static, read-only allowlist acceptable initially?
- **Evidence/status:** DataSchema has identifier/version fields, but no catalog, approved schema ID/content, catalog owner, or version lifecycle was found. UNRESOLVED / BLOCKING for implementation.
- **Recommendation — PROPOSED:** Consider a small static, read-only allowlist of reviewed schemas, with released versions immutable and changes made under a new version. No actual IDs, contents, owner, or process are proposed as facts.
- **Alternatives:** A separately approved registry mechanism or defer schema-validation API work. Caller-defined arbitrary schemas are not recommended for the first release because they make requesters define the rules being assessed.
- **Consequence if deferred:** No supported schema can be advertised or selected, and unknown-schema behavior cannot be finalized.
- **Required authority:** Schema owner/reviewer and project technical authority; NOT IDENTIFIED.
- **Response:** APPROVE / REJECT / MODIFY / DEFER — catalog approach: ___; owner: ___; approved first-release IDs/versions: ___; change review: ___; authority/reference: ___

### REQ-ARC10-04 — API contract ownership and canonical location

- **Exact question:** Who owns the API contract, where must the authoritative version live, who approves the final contract, and how should this local working package relate to that source?
- **Evidence/status:** docs/ARC10_EVIDENCE_INDEX.md records the canonical register as NOT LOCATED IN INSPECTED MATERIAL, the designating authority as NOT IDENTIFIED, and the local decision package as NON-CANONICAL WORKING MIRROR. UNRESOLVED.
- **Recommendation — PROPOSED:** Identify an accountable contract owner and authoritative location through project governance before labeling any local document canonical. Preserve the local package as non-canonical until then. Do not renumber D-01–D-16 or resolve D-04/D-05 here.
- **Alternatives:** Designate an existing authoritative source through the proper authority, establish another location through that authority, or defer final contract recording.
- **Consequence if deferred:** Conflicting drafts and approval ambiguity remain; a local proposal cannot be treated as the approved contract.
- **Required authority:** Project governance/register-designating authority, NOT IDENTIFIED in inspected material; contract approver also NOT IDENTIFIED.
- **Response:** APPROVE / REJECT / MODIFY / DEFER — contract owner: ___; canonical location/revision: ___; approval authority: ___; relationship to local mirror: ___; authority/reference: ___

### REQ-ARC10-05 — Framework/runtime

- **Exact question:** Approve FastAPI + Uvicorn as the framework/runtime proposal, select an alternative, or defer pending target and deployment decisions?
- **Evidence/status:** No framework exists in ARC-10 tracked HEAD. Existing planning compared frameworks. FastAPI + Uvicorn is the current technical recommendation from internal preparation, PROPOSED — PENDING FINAL APPROVAL.
- **Recommendation — PROPOSED:** Consider FastAPI + Uvicorn for the Python modular-monolith proposal because typed request/response validation, OpenAPI generation, and pytest-compatible testing suit contract preparation. This does not establish developer familiarity or deployment fit.
- **Alternatives:** Flask with separately chosen schema/OpenAPI tools; another selected framework; or defer. No option is approved by this request.
- **Consequence if deferred:** No framework-specific implementation, dependencies, test client, or serving configuration should be selected.
- **Required authority:** Architecture/framework decision authority is NOT IDENTIFIED in inspected governance evidence. The Project Owner is asked to identify that authority or provide a decision if authorized under the applicable process.
- **Response:** APPROVE / REJECT / MODIFY / DEFER — framework: ___; runtime/server: ___; constraints/reason: ___; authority/reference: ___

### REQ-ARC10-06 — Security and operational requirements

- **Exact question:** Who is authorized to decide authentication/authorization, CORS/allowed origins, secret/configuration handling, logging/privacy, payload/record/depth/concurrency/timeout/response-size limits, and deployment/runtime ownership? What direction applies to this use case?
- **Evidence/status:** No production security, privacy, numeric-limit, deployment, or runtime policy was verified. UNRESOLVED / BLOCKING where applicable.
- **Recommendation — PROPOSED:** Assign accountable decision roles and derive numeric limits from workload and platform evidence before implementation. Do not infer public access, logging/retention permission, or security configuration.
- **Alternatives:** Keep the operation unexposed and defer; or authorize a scoped internal deployment only after responsible authorities define requirements.
- **Consequence if deferred:** No safe production exposure or operational deployment design; do not invent authentication or numeric limits.
- **Required authority:** Security, privacy/data, and platform/deployment decision-makers; each is NOT IDENTIFIED in inspected material.
- **Response:** APPROVE / REJECT / MODIFY / DEFER — auth/authz authority and direction: ___; CORS: ___; secrets: ___; privacy/logging: ___; limits/workload owner: ___; deployment owner: ___; authority/reference: ___

### REQ-ARC10-07 — API behavior decisions

- **Exact question:** Decide or assign decision authority for the proposed endpoint/method, empty records, HTTP status/error envelope, unsupported schema/version behavior, API compatibility/versioning, and synchronous/bounded-work assumptions.
- **Evidence/status:** POST /api/v1/dataset-validations is proposed only. The schema validator currently returns an empty report with zero counts and is_valid=True; API behavior is not set by that fact. There is no HTTP error mapping or project-wide versioning policy. UNRESOLVED.
- **Recommendation — PROPOSED:** Keep the proposed endpoint/method under review; consider rejecting empty records at the API boundary to avoid implying records were checked; return validation findings separately from request/processing errors; reject unsupported schemas without fallback; and use synchronous execution only under approved limits. These behaviors are not approved.
- **Alternatives:** Approve different empty/error/versioning semantics, or defer endpoint definition until contract ownership and schema policy are settled.
- **Consequence if deferred:** DTO, client behavior, compatibility guarantees, and acceptance tests cannot be finalized.
- **Required authority:** API contract owner and operational authority; NOT IDENTIFIED in inspected evidence.
- **Response:** APPROVE / REJECT / MODIFY / DEFER — endpoint/method: ___; empty input: ___; error/status model: ___; unknown schema: ___; versioning: ___; execution model: ___; authority/reference: ___

## 6. Critical-path dependencies

1. Identify the implementation target and its owner before repository-specific changes.
2. Identify the contract owner and authoritative location; preserve local material as non-canonical and leave D-04/D-05 and D-01–D-16 unchanged.
3. Resolve truthful provenance handling and assign schema ownership; identify actual approved schema content before defining a complete request DTO.
4. Decide framework/runtime and request/response, empty-input, error, versioning, security, privacy, and resource-limit policies.
5. Only then determine whether authorized non-production implementation is sufficiently specified. Production implementation/deployment remains separately unauthorized by the supplied context.

Deferring a decision does not authorize an implicit default. No recommendation in this request should be promoted to an approval by implementation or by passing tests.

## 7. Work that can continue and work that remains blocked

**Can continue under supplied preparation authorization:** Refine draft contract materials, ADR and test plans; inspect verified engine behavior; prepare synthetic-only proposals; and coordinate to identify decision authorities. Continue labeling all proposals and local records as non-canonical.

**Must remain blocked:** Final API contract publication as authoritative; framework-specific code/dependency changes pending framework and target decisions; schema catalog implementation pending owner and approved schemas; use of fabricated provenance; production API implementation, integration, or deployment; security policy invention; ARC-03 changes; NASA access/data-rights decisions outside delegation; canonical register designation; and D-01–D-16 renumbering.

## 8. Project Owner response template

Complete one line per request through the established project decision process. This template does not itself establish authority or record approval.

| Request-local ID | Response: APPROVE / REJECT / MODIFY / DEFER | Selected direction or revision | Decision-maker/authority (as recorded by project) | Reference/date |
|---|---|---|---|---|
| REQ-ARC10-01 — Implementation target |  |  |  |  |
| REQ-ARC10-02 — Provenance policy |  |  |  |  |
| REQ-ARC10-03 — Schema catalog |  |  |  |  |
| REQ-ARC10-04 — Contract owner/location |  |  |  |  |
| REQ-ARC10-05 — Framework/runtime |  |  |  |  |
| REQ-ARC10-06 — Security/operations |  |  |  |  |
| REQ-ARC10-07 — API behavior |  |  |  |  |

## 9. Evidence references

- docs/ARC10_EVIDENCE_INDEX.md — evidence acceptance scope, canonical-register search boundaries, non-canonical mirror, D-04/D-05 issue, and production gate status.
- docs/ARC10_PROJECT_OWNER_EVIDENCE_ACCEPTANCE.md — evidence-package acceptance and explicit limitations; not API approval.
- docs/ARC10_IMPLEMENTATION_AUTHORIZATION_GATE.md — unresolved production-use-case, target, contract, security, limits, and implementation blockers.
- docs/ARC10_API_CONTRACT_AND_DECISION_PACKAGE.md — prior proposal package; not canonical and not approved.
- docs/ARC10_CONTRACT_NEUTRAL_SERVICE_DESIGN.md and docs/ARC10_USE_CASE_COMPARISON_AND_RECOMMENDATION.md — engine API comparison and proposed mechanical-validation boundary.
- docs/ARC10_WORK_ORDER_V2_REGISTER_RECOVERY_AND_READINESS.md — inspected-material search limits and unresolved register/numbering issues.
- docs/ARC10_REPOSITORY_API_READINESS_REPORT.md — repository evidence and limits.
- docs/ARC10_BACKEND_API_ARCHITECTURE_PROPOSAL.md, docs/ARC10_API_ENDPOINT_REQUIREMENTS_AND_DRAFT_SCHEMAS.md, and docs/ARC10_IMPLEMENTATION_PLAN_AND_TEST_STRATEGY.md — original planning proposals, not approvals.
- Separate ARC-08 source inspected for this update: src/quantum_space_agi/data/models.py, provenance.py, sources.py, schemas.py, ingestion.py, and adapters/exoplanet_archive.py; relevant tests include tests/data/test_models.py, test_provenance.py, and test_schemas.py. These references do not designate ARC-08 as the ARC-10 implementation target.

This remains a decision request, not a decision record. No response to this request, new approval, signature, NASA permission, scientific acceptance, canonical register, or production implementation authorization is claimed.

## Appendix — superseded initial draft retained for history

The material below is the earlier draft of this request. It is retained as history only; where it conflicts with sections 1–9 above, sections 1–9 are the current request. Its numbered rows are not canonical D-01–D-16 assignments.

## A. Current verified position

### ARC-10
The inspected ARC-10 worktree is a documentation/planning branch with six planning documents. No backend routes, HTTP framework, production API contract, or implementation are present in the inspected baseline. Existing planning documents are proposals, not approvals.

### ARC-08 engine
Inspection of the separate ARC-08 checkout at arc/08-ai-ml, HEAD de48b077571fe44b1fc8b7ab8fad6ba60016f029, verified:

- quantum_space_agi.data.schemas.validate_dataset(Dataset, DataSchema) checks declared field presence, nullability, and exact Python type. It returns SchemaValidationReport with zero-based row indexes, does not coerce/drop rows, and requires Dataset/Provenance. It does not establish scientific validity.
- quantum_space_agi.data.quality.analyze_quality(...) reports missing values, exact whole-record duplicate groups, linked schema-invalid indexes, and finite numeric summaries. It does not identify duplicate entities or establish scientific eligibility.
- A separate record-oriented validator, quantum_space_agi.data.validate_records, accepts records and a schema mapping, and returns a different report with one-based row indexes and a generated timestamp. Actual values are omitted by default.
- Dataset copies top-level record mappings but does not deep-freeze nested values. Provenance is declared metadata, not authentication.

pyproject.toml declares no runtime dependencies or HTTP framework. config.Settings covers explicit log-level configuration; no process-health API was found.

### ARC-09
The ARC-09 branch at origin/arc/09-visualization, revision 878cb81b69430cdf6c25c419edba587629537768, contains the backend contract request, prototype handoff, manual verification report, decision register, and final decision confirmation request. The contract request keeps dashboard summary conditional and does not define an endpoint or schema. The prototype is isolated and uses synthetic/conceptual data; it has no API integration, persistence or authentication.

### Why production implementation cannot safely begin
The first use case/consumer, target service/repository, contract owner, framework, endpoints/DTOs, errors, security/access control, retention/privacy, resource limits and acceptance process are unresolved. The two validation APIs differ in provenance requirements, report shape and row-index basis. Resolve these before publishing a wire contract.

## B. First-use-case decision

| Candidate | Evidence/readiness | Main gap | Status |
|---|---|---|---|
| Mechanical dataset validation | ARC-08 contains tested structural schema validation and quality analysis. | Needs a consumer, trusted schema policy, validator choice, transport contract, limits and privacy rules. Mechanical validity is not scientific eligibility. | **PROPOSED — PENDING PROJECT OWNER APPROVAL** |
| ARC-09 Dashboard Summary | ARC-09 contract request calls this a conditional proposed P0 slice. | No authoritative metric source, definitions, units, freshness or provenance; production frontend not confirmed. Synthetic prototype values cannot fill this gap. | NOT DECIDED |
| Process health/status | No process-health API/model found; only log-level configuration. | Needs operational consumer and a definition of process liveness versus dependency readiness. | NOT DECIDED |

**Recommendation — PROPOSED — PENDING PROJECT OWNER APPROVAL:** Consider a bounded, mechanical schema-validation operation as the first slice. It has the most directly relevant tested engine behavior and can avoid scientific interpretation if kept structural-only. This is an engineering recommendation, not evidence of product need or approval.

Exclude quality analysis from the initial scope unless separately justified and approved. analyze_quality uses exact whole-record duplicate equality (not entity identity) and binary64 numeric summaries.

Consider, but do not yet select, either existing interface:
- data.schemas.validate_dataset(Dataset, DataSchema): versioned schema object, Dataset provenance required, zero-based indexes, no generated validation timestamp.
- data.validate_records(...): records plus schema mapping, no Dataset provenance requirement, one-based indexes, generated timestamp, actual values omitted by default.

## C. Required project decisions

No approval is recorded here. Recommendations are proposals, not approvals.

| # | Decision | Recommended option / alternatives | Why needed | Status | Authority | Approval |
|---:|---|---|---|---|---|---|
| 1 | First use case | Consider mechanical validation; alternatives are dashboard summary, process liveness, or defer. | Defines user, input and safety boundary. | PROPOSED — PENDING PROJECT OWNER APPROVAL | Project Owner/project decision process per task context. | NOT GRANTED |
| 2 | Production target service/repository | Identify target and branch; alternatives: new service, existing service, defer. | Avoid wrong integration target. | NOT DECIDED | Project/engineering authority to confirm. | NOT GRANTED |
| 3 | Contract owner | Name accountable owner and canonical versioned location. | Prevent conflicting contracts. | NOT DECIDED | Project technical process; none identified in inspected evidence. | NOT GRANTED |
| 4 | Architecture/framework | Decide after target/use case; alternatives include supported framework choices or defer. | No framework exists in inspected engine. | NOT DECIDED | Architecture authority to confirm. | NOT GRANTED |
| 5 | Validator choice | Select one API or approve a mapping; document index basis. | APIs differ in provenance, indexes, and result shape. | BLOCKED | Contract/schema owner; domain reviewer if semantic rules are added. | NOT GRANTED |
| 6 | Endpoint paths/versioning | Define after target and owner; no route is presumed. | No authoritative route or version policy exists. | NOT DECIDED | Contract/architecture authority to confirm. | NOT GRANTED |
| 7 | Request/response DTO and validation | Specify types, required/optional/null/missing, empty behavior, schema selection and row indexes. | Needed for compatible clients and non-ambiguous behavior. | BLOCKED | Contract owner; domain owner for scientific semantics. | NOT GRANTED |
| 8 | Error contract | Distinguish malformed request/service failure from completed validation with invalid rows. | Engine defines no HTTP error mapping. | NOT DECIDED | Contract owner/product process. | NOT GRANTED |
| 9 | Authentication/authorization/CORS | Decide access model, least privilege, allowed origins and environment configuration. | No policy or production client target verified. | BLOCKED | Security/platform authority to identify. | NOT GRANTED |
| 10 | Retention/privacy/request limits | Decide transient handling, logging/redaction, retention and evidence-based limits. | Records may be sensitive; no service policy exists. | BLOCKED | Project privacy/security/data and platform authorities to identify. | NOT GRANTED |
| 11 | Scientific/data provenance | Keep initial scope structural-only; separate caller-declared from server-observed values. | Provenance metadata does not authenticate or authorize reuse. | NOT DECIDED | Relevant scientific/data owner; NASA authority/terms if archive data is used. | NOT GRANTED |
| 12 | Acceptance/review process | Approve measurable test, security, review and release evidence. | Test completion is not project acceptance. | NOT DECIDED | Project process; named reviewer/authority to confirm. | NOT GRANTED |

### Approval and delegated execution
Task context says Rafi has delegated authority for routine assigned engineering/documentation. This does not itself approve the production use case, target, architecture, API contract, security policy, scientific definitions or release acceptance. Contributor review and technical recommendations are not formal approval. NASA access, retention and redistribution terms are separate and must not be inferred from software readiness.

## D. Proposed initial acceptance criteria

**PROPOSED — REQUIRE REVIEW AND APPROVAL**, only if mechanical validation is selected:

1. One documented engine API and trusted schema/version selection policy are used; unknown schema versions have explicit behavior.
2. Required, optional, nullable, missing and wrong-type cases match the approved schema; bool is rejected as int where exact types require it.
3. Output row indexes use one documented base and map to request rows.
4. Validation does not coerce, normalize, mutate, drop or deduplicate input.
5. Empty input and malformed requests/records have explicit tested behavior.
6. Provenance is supplied under contract or represented as absent/unknown; declarations are not called authenticated facts.
7. Completed validation findings are distinguishable from request/service errors; raw record values are not exposed by default.
8. Byte, row, nesting, time and concurrency limits have approved values and are enforced.
9. Unit, integration and contract tests cover valid, invalid, null/missing, malformed, empty, oversized, error, index mapping and non-mutation cases; actual commands/results are recorded.
10. No response claims scientific eligibility, scientific validation, NASA authenticity/authorization, or mission suitability from structural conformance.
11. Data handling, logging, retention, access control and CORS are reviewed for the actual target.
12. Integration/release acceptance is recorded separately from tests and implementation.

## E. Project Owner response template

Fill statuses through the project's authoritative decision process. Blank fields mean no approval recorded here.

| # | Decision | Status: APPROVED / REJECTED / NEEDS REVISION / NOT DECIDED | Selected option / revision | Authority recorded by project | Approval reference/date |
|---:|---|---|---|---|---|
| 1 | First use case | NOT DECIDED |  |  |  |
| 2 | Production target service/repository | NOT DECIDED |  |  |  |
| 3 | Contract owner/location | NOT DECIDED |  |  |  |
| 4 | Architecture/framework | NOT DECIDED |  |  |  |
| 5 | Validator/schema policy | NOT DECIDED |  |  |  |
| 6 | Endpoint paths/versioning | NOT DECIDED |  |  |  |
| 7 | Request/response DTO/rules | NOT DECIDED |  |  |  |
| 8 | Error contract | NOT DECIDED |  |  |  |
| 9 | Authentication/authorization/CORS | NOT DECIDED |  |  |  |
| 10 | Retention/privacy/limits | NOT DECIDED |  |  |  |
| 11 | Scientific/data provenance | NOT DECIDED |  |  |  |
| 12 | Acceptance/review process | NOT DECIDED |  |  |  |

This is a decision request, not a decision record. No response, signature, approval, NASA permission, scientific acceptance or implementation authorization is simulated or inferred.
