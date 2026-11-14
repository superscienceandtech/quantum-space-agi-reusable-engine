# ARC-10 Outstanding Decision & Authority Request Package v0.1

**Status:** Request package for Project Owner review and, where needed, referral to the appropriate authority.

**Decision state:** No decision is made by this document. It grants no approval, designates no authority or canonical location, and does not authorize production implementation. The package has not been sent, reviewed, or approved.

## A. Purpose and Status

This package consolidates eight outstanding ARC-10 decision and authority requests from the current local evidence. It is intended to help the Project Owner answer matters within the documented scope and identify or refer matters reserved for other authorities. It does not presume the Project Owner holds every authority.

The local ARC-10 decision package remains a **NON-CANONICAL WORKING MIRROR**. The canonical Decision & Approval Register and its designating authority have not been located in inspected evidence. D-01–D-16 numbering, including the D-04/D-05 discrepancy, is preserved without reinterpretation.

## B. Authority Baseline

The supplied Project Owner decisions are recorded in `docs/ARC10_PROJECT_OWNER_DECISION_RECONCILIATION_AND_EXECUTION_PLAN.md`. That document records internal review/decision responsibilities within delegated scope; it does not establish every external, security, platform, release, schema, or final contract authority. Where the available record does not identify an authority, this package says so explicitly.

| Recorded direction | Current status and boundary |
|---|---|
| Modular Monolith; FastAPI/Uvicorn/Python | Approved with conditions as internal technical direction only. Target compatibility and deployment conditions remain open; this is not production architecture approval. |
| `POST /api/v1/dataset-validations` | First operation authorized for contract drafting only. No production route is authorized. |
| Malformed request → HTTP 400 | Approved for contract drafting. Detailed envelope and categories remain pending. |
| Empty API `records` → HTTP 422 | Approved for contract drafting at the API boundary only. Application/service empty-record behavior remains unspecified; ARC-08 domain behavior is distinct. |
| Processed schema findings → HTTP 200 with `is_valid=false` | Approved for contract drafting; indicates mechanical processing, not scientific validity. |
| Unsupported schema ID/version | Explicit rejection and no fallback; exact HTTP status remains pending. |
| Synchronous processing | Only under approved resource limits; no numeric limits are approved. |
| Static, read-only schema allowlist | Approved with conditions as a design direction; no actual schema ID/version or definition is approved. |
| Caller-declared provenance | Approved in principle only with unverified labeling and separation from server-observed receipt time. Exact API representation and requiredness remain pending. |
| Final API contract / production implementation | Final contract approval is pending; production implementation is blocked and not authorized. |

Evidence-package acceptance (**ACCEPTED WITH DOCUMENTED LIMITATIONS**) applies only to the evidence package. It does not approve architecture, the final contract, or implementation.

## C. Decision Request Summary Table

| Request ID | Decision needed | Current evidence/status | Requested authority | Blocking effect | Required written response |
|---|---|---|---|---|---|
| DR-01 | Application/service behavior for empty records | API HTTP 422 is approved for contract drafting; service semantics are unspecified; ARC-08 validators differ. | Project Owner if within recorded delegated scope; otherwise the designated service/API decision authority, which is not identified in available evidence. | Blocks a determinate service contract and service-level acceptance test for empty input. | Select an explicit service behavior or identify the authority/process that will decide it. |
| DR-02 | Canonical Decision & Approval Register | Not located in inspected material; local package is non-canonical; register-designating authority/custodian unidentified. | Register-designating authority; not identified. Project Owner is asked to identify or refer, not presumed to designate. | Blocks canonical decision tracking and authoritative linkage. | Identify canonical location, revision/version, custodian, designating authority, and authoritative D-01–D-16 source. |
| DR-03 | D-04/D-05 numbering and mapping | Supplied Work Order context says D-05 is framework; local mirror says D-04 is architecture/framework and D-05 is endpoints/method/versioning. | Authority responsible for the canonical register/numbering; not identified. | Blocks reliable cross-reference and any canonical numbering correction. | Confirm authoritative meanings for D-04 and D-05 and whether a future canonical record should correct the mapping. |
| DR-04 | Contract drafting ownership and canonical contract location | Rafi is proposed as drafting/technical coordination owner subject to written acknowledgement; final approver and canonical location unresolved. | Project Owner for acknowledgment/designation within documented scope; final approval authority remains unidentified. | Blocks accountable contract maintenance, final approval, and authoritative publication. | Acknowledge or identify a different drafting coordinator; identify final approval authority and canonical location/process, or refer these questions. |
| DR-05 | Production implementation target and integration boundary | Production backend repository, branch, owner, environment, and integration boundary are not designated. ARC-08 is reusable capability, not an automatic target. | Project/engineering authority; not identified in available evidence. Project Owner is asked to identify or refer. | Blocks repository-specific implementation and integration planning. | Name or designate the repository, branch, owner, deployment environment, integration boundary, and ARC-08 consumption approach. |
| DR-06 | Security, privacy, and operational authorities/decisions | Authentication, authorization, CORS, privacy/retention, logging, exposure, limits, concurrency, timeouts, deployment, and operations remain deferred/unapproved. | Security, privacy/data, platform, operations, and release authorities as applicable; identities not identified. | Blocks security design, bounded synchronous execution, deployment, and production exposure. | Identify responsible authorities and the process for their written requirements/decisions; do not infer defaults. |
| DR-07 | First-release schema catalog contents and governance | Static read-only allowlist direction is conditional; actual IDs, versions, definitions, owners, reviewers, and release authority are absent. | Schema content/release authority; not identified. Project Owner is asked to identify or refer. | Blocks releasing a supported schema catalog and claims about supported schemas. | Provide or route exact reviewed definitions and identify ownership, review, release, and version responsibilities. |
| DR-08 | Final API contract approval process | Drafting is authorized within limits; DTO, provenance, catalog, error envelope/statuses, limits, target, security/operations, canonical location, and final approver remain unresolved. | Final contract approval authority and process; not identified. Project Owner may identify or refer but is not presumed to be final approver. | Blocks final contract approval and implementation against a stable contract. | Identify the approver/canonical review process and required closure evidence; schedule final approval only after prerequisites are resolved. |

## D. Detailed Decision Requests DR-01 to DR-08

### DR-01 — Application/Service Empty-Record Semantics

- **Background:** The API and service/domain layers have distinct boundaries. A drafting decision at the HTTP boundary does not itself define application-service orchestration.
- **Verified facts:** REQ-ARC10-07 records HTTP 422 for an empty API `records` collection for contract drafting. In the separate ARC-08 checkout, schema-based `validate_dataset(Dataset, DataSchema)` on an empty `Dataset` returns zero records, zero valid records, no invalid records, and derived `is_valid=True` (`src/quantum_space_agi/data/schemas.py`). The legacy `data.validator.validate_dataset` instead reports an `empty_dataset` finding (`src/quantum_space_agi/data/validator.py`; `tests/test_data_validation.py::test_empty_dataset_is_invalid`). These are distinct domain interfaces; neither determines service orchestration.
- **Existing written decision:** HTTP 422 remains approved for API contract drafting only. The service-boundary design identifies empty collection behavior as unresolved. The Prompt 12 addenda in the service strategy and API test plan preserve that distinction.
- **Unresolved question:** Should the application/service layer reject empty records before invoking a domain validator, pass an empty dataset to a selected validator, or follow another explicitly specified behavior?
- **Options for consideration, not recommendations:** (1) reject before domain invocation; (2) pass through to the selected domain validator; (3) another behavior described with its consequences. None is selected here.
- **Recommended response format:** State the selected service behavior, scope, selected validator if relevant, and whether it changes any existing API drafting behavior. If the decision is outside the responder's authority, identify the decision authority/process.
- **Required authority:** Project Owner only insofar as this falls within the recorded delegated internal decision scope; otherwise **Authority not identified in available evidence**.
- **Consequence of no decision:** Service behavior and its acceptance test remain pending. Do not infer behavior from HTTP 422.

### DR-02 — Canonical Decision Register

- **Background:** Governance records need an authoritative source of record, but this package cannot designate one.
- **Verified facts:** `docs/ARC10_EVIDENCE_INDEX.md` records the canonical register as NOT LOCATED IN INSPECTED MATERIAL, the local decision package as NON-CANONICAL WORKING MIRROR, and the register-designating authority/custodian as unidentified. Its search excludes live GitHub, external organization storage, private messages, and unpushed work.
- **Existing written decision:** No canonical register location or custodian is established in the inspected records. Evidence-package acceptance did not designate a register.
- **Unresolved question:** Which register is authoritative, at what exact location and revision/version, who maintains it, and who has authority to designate it?
- **Options:** No register options are proposed; the responsible authority should identify the source of record.
- **Recommended response format:** Provide the exact location/reference, current revision/version, custodian, designating authority, and authoritative D-01–D-16 mapping, or state that the matter is being referred and identify the process (without inventing an authority).
- **Required authority:** Register-designating authority; **Authority not identified in available evidence**. Project Owner is requested to identify or refer only.
- **Consequence of no decision:** Keep the local package non-canonical and do not cite its D labels as authoritative.

### DR-03 — D-04/D-05 Numbering and Mapping Discrepancy

- **Background:** Conflicting numbering appears in non-canonical or task-supplied material and cannot be resolved by inference.
- **Verified facts:** `docs/ARC10_EVIDENCE_INDEX.md` §1 and §3 reports that the supplied Work Order context calls D-05 the framework decision. The local mirror, `docs/ARC10_API_CONTRACT_AND_DECISION_PACKAGE.md` §6, labels D-04 as backend architecture/framework/runtime and D-05 as endpoint paths, methods, and versioning. The recovery report `docs/ARC10_WORK_ORDER_V2_REGISTER_RECOVERY_AND_READINESS.md` states that its named original Work Order was absent from the inspected worktree and tracked HEAD; the available copy is a recovery report and does not make the underlying mapping canonical.
- **Existing written decision:** The discrepancy remains OPEN. No D-01–D-16 renumbering or authoritative mapping was approved in the inspected evidence.
- **Unresolved question:** What are the authoritative meanings of D-04 and D-05, and should a future canonical record correct the existing mapping?
- **Options:** No mapping is selected here. A response may confirm either mapping or provide another authoritative reference, with provenance and effective revision.
- **Recommended response format:** Cite the governing register/document and revision, state each D-number's exact meaning, and give instructions for reconciling the non-canonical mirror without erasing its historical record.
- **Required authority:** Authority responsible for the canonical register/numbering; **Authority not identified in available evidence**. Project Owner is asked to route the question if needed.
- **Consequence of no decision:** Keep the discrepancy OPEN; do not renumber, reinterpret, or promote the mirror.

### DR-04 — Contract Ownership and Canonical Location

- **Background:** A drafting coordinator, contract custodian, final approver, and canonical document location are separate roles.
- **Verified facts:** REQ-ARC10-04 allows Rafi to be identified as proposed drafting/technical coordination owner subject to explicit written acknowledgement. It records Project Owner internal review/decision responsibilities within delegated scope. It leaves final contract approval authority and canonical contract location unresolved. The current draft contract labels both unresolved.
- **Existing written decision:** No evidence reviewed establishes that Rafi has acknowledged/been acknowledged as owner, that a final approver is designated, or that a canonical contract location exists.
- **Unresolved question:** Is Rafi explicitly acknowledged/designated for the proposed coordination role, or should another coordinator be named? Who approves the final contract and where is its canonical revision maintained?
- **Options:** Acknowledge the proposed coordinator; designate another person/role; or defer and specify the route to resolution. These options do not appoint a final approver by implication.
- **Recommended response format:** Record coordinator and scope, acknowledgement, final approver role/process, canonical path/reference, and any conditions. If approval authority is external or delegated elsewhere, identify the referral path.
- **Required authority:** Project Owner for any acknowledgment/designation within documented scope; final contract authority **not identified in available evidence**.
- **Consequence of no decision:** Keep Rafi's role proposed, the final approver unidentified, and the local contract non-canonical; no final contract approval can be claimed.

### DR-05 — Production Implementation Target

- **Background:** Repository-specific implementation requires an authorized target and integration boundary.
- **Verified facts:** REQ-ARC10-01 defers target repository, owner, branch, and integration boundary. The evidence index and remaining-approval report identify the current ARC-10 worktree as a planning workspace, not a designated production backend. ARC-08 is reusable domain capability and is not automatically the ARC-10 implementation target. No deployment environment is confirmed.
- **Existing written decision:** Continue planning/documentation in the ARC-10 workspace; no production target was selected.
- **Unresolved question:** Which backend repository, branch, owner, deployment environment, integration boundary, and ARC-08 consumption model are authorized?
- **Options:** ARC-08 as a dependency, an explicitly approved integration boundary, or another designated target. These are questions, not recommendations or selections.
- **Recommended response format:** Identify each target element separately and cite the project decision/reference. State whether the target decision authorizes implementation; absent explicit bounded authorization, it does not.
- **Required authority:** Project/engineering authority; **Authority not identified in available evidence**. Project Owner is asked to identify or refer.
- **Consequence of no decision:** No repository-specific production implementation or integration work.

### DR-06 — Security, Privacy, and Operations Authorities

- **Background:** Security and operational policy cannot be supplied by technical inference or by a proposed test plan.
- **Verified facts:** REQ-ARC10-06 is DEFERRED. Existing records leave authentication, authorization, CORS, privacy, submitted-data retention/deletion, logging/redaction, public exposure, request/resource limits, concurrency, timeouts, deployment, and operational ownership unapproved or unquantified. Numeric thresholds are absent.
- **Existing written decision:** Preparation of a proposal for review was allowed; no security or operations policy was approved.
- **Unresolved questions:** Which authorities own these decisions? What requirements apply to identity/access, CORS, privacy, retention/deletion, logging/audit, exposure, limits, concurrency, timeouts, deployment, and operations? Which work must remain internal until they decide?
- **Options:** No policy options or numeric limits are selected in this package. The relevant authorities should define scope and requirements.
- **Recommended response format:** Identify each responsible authority/process, then provide or request a separately recorded policy decision with scope and evidence. Mark any unresolved subtopic explicitly.
- **Required authority:** Security, privacy/data, platform, operations, and release authorities as applicable; **Authority not identified in available evidence**.
- **Consequence of no decision:** Security/operations and production exposure remain blocked; do not invent defaults or assume a permissive policy.

### DR-07 — Schema Catalog Approval

- **Background:** A static catalog design is not a released catalog and does not approve schema content.
- **Verified facts:** REQ-ARC10-03 approves with conditions the direction for a static, read-only allowlist with reviewed immutable versions and explicit unknown-ID/version rejection. No actual first-release schema ID, version, or exact definition is approved. Catalog ownership, reviewers, and release responsibility remain unresolved.
- **Existing written decision:** The allowlist direction is conditional; no schema entry is authorized for release by this request package.
- **Unresolved question:** Which exact structural schemas and versions are needed, who owns/reviews their definitions, and who authorizes immutable release?
- **Options:** No schema ID or definition is proposed here. Reviewers may request revisions or defer release.
- **Recommended response format:** For each proposed entry, provide exact ID/version and definition reference/checksum if established, review evidence, owner/reviewer roles, release authority, and immutable-version process. A checksum alone is not approval evidence.
- **Required authority:** Schema content owner, reviewer(s), and release authority; **Authority not identified in available evidence**.
- **Consequence of no decision:** No schema can be represented as supported or released; final contract/schema acceptance remains blocked.

### DR-08 — Final API Contract Approval

- **Background:** Contract drafting permission is bounded and is not approval of the finished contract.
- **Verified facts:** REQ-ARC10-07 authorizes drafting one operation and bounded HTTP behavior. The contract document remains DRAFT; final approval authority and canonical location are unresolved. DTO field semantics, validator/provenance choice, schema contents, exact error envelope and unsupported-schema status, resource limits, target, security/operations, and acceptance criteria remain open.
- **Existing written decision:** API behavior is approved for contract drafting only; no final API Contract approval or production implementation authorization was granted. Evidence-package acceptance has no effect on these statuses.
- **Unresolved question:** Who is authorized to approve the final contract, at what canonical location and revision, and what prerequisites/evidence must be closed before that review?
- **Options:** First resolve the listed dependencies, then route the complete contract through the identified approval process. No premature approval option is requested.
- **Recommended response format:** Identify the approving authority/process and canonical location now; list required closure evidence and any remaining blockers. Conduct final approval only after first use case, endpoint/DTO, catalog, errors, security/operations, and target dependencies are resolved.
- **Required authority:** Final contract approval authority; **Authority not identified in available evidence**. Project Owner may identify or refer the request but is not presumed to be final approver.
- **Consequence of no decision:** Keep the API contract draft pending and production implementation blocked.

## E. Decisions Rafi Can Execute Independently

The inspected evidence supports Rafi performing bounded technical/documentation work, not granting governance approvals. Within existing scope, Rafi can:

- Maintain clearly labeled drafts and request packages, cross-reference verified records, and preserve historical/non-canonical status.
- Inspect existing source and tests to report current domain behavior, without changing ARC-03/ARC-08 or converting domain behavior into API policy.
- Prepare options, impact descriptions, test plans, and technical compatibility questions for the identified decision processes.
- Correct objectively verifiable documentation wording within authorized scope while preserving source decisions and approval boundaries.
- Track a request as pending and record a response accurately if supplied, without authenticating external materials or assigning authority beyond the evidence.

Rafi cannot independently designate the canonical register, settle D numbering, appoint an approver, approve security/data policies or schemas, authorize production implementation, or mark the API ready based on this package.

## F. Decisions Reserved for Project Owner

The reconciliation records Project Owner internal review/decision responsibilities **within delegated scope**. It supports asking the Project Owner to:

- Decide DR-01 only if application/service semantics fall within that delegated scope; otherwise identify or refer it to the responsible authority.
- Provide or decline the written acknowledgment/designation requested in DR-04 within that scope.
- Identify the appropriate process/authority for DR-02, DR-03, DR-05, DR-06, DR-07, and DR-08 where these are not within the Project Owner's authority.
- Clarify the scope and evidence needed for subsequent contract review without treating evidence-package acceptance as API approval.

This section does not claim the Project Owner holds canonical-register, security, platform, schema-release, final contract, or production-target authority unless separately established.

## G. Decisions Requiring Unidentified External Authority

The repository does not identify the following decision authorities. Each must be named or referred through the project process; no person is assigned here:

- Canonical register designation, custody, and authoritative D-01–D-16 numbering (DR-02/DR-03).
- Production repository/service, engineering owner, integration boundary, and deployment environment (DR-05).
- Security, privacy/data handling, platform/operations, and release requirements and numeric limits (DR-06).
- Schema content review, ownership, and release authority (DR-07).
- Final API contract approval and canonical contract location (DR-04/DR-08).
- Application/service empty-record semantics if outside the Project Owner's documented delegated scope (DR-01).

Where authority is unresolved, the required action is to identify or refer—not to infer approval from authorship, technical ownership, silence, or prior evidence acceptance.

## H. Evidence and Document References

### ARC-10 decision and governance records inspected

- `docs/ARC10_PROJECT_OWNER_DECISION_RECONCILIATION_AND_EXECUTION_PLAN.md` — REQ-ARC10-01–07, especially §§1–4, 8, and 11.
- `docs/ARC10_ARCHITECTURE_DECISION_RECORD_V0.1.md` — conditional internal direction, target and implementation conditions.
- `docs/ARC10_API_CONTRACT_V0.1.md` — drafting scope, HTTP behavior, pending contract details and status.
- `docs/ARC10_DTO_SPECIFICATION_V0.1.md` — proposed wire shape and unresolved mapping/requiredness.
- `docs/ARC10_PROVENANCE_REPRESENTATION_PROPOSAL_V0.1.md` — unverified caller declarations and unresolved representation.
- `docs/ARC10_STATIC_SCHEMA_CATALOG_DESIGN_V0.1.md` — conditional catalog direction; no approved entries.
- `docs/ARC10_ERROR_HTTP_MAPPING_PROPOSAL_V0.1.md` — approved-for-drafting cases versus unresolved mappings.
- `docs/ARC10_API_VALIDATION_INTEGRATION_TEST_PLAN_V0.1.md` — planned layer-specific tests; no implementation/test execution authorized here.
- `docs/ARC10_REMAINING_APPROVAL_AND_DEPENDENCY_REPORT_V0.1.md` — current readiness, authority, target and policy blockers.
- `docs/ARC10_CONSOLIDATED_CONSISTENCY_AND_TRACEABILITY_AUDIT_V0.1.md` and `docs/ARC10_DOCUMENTATION_RECONCILIATION_LOG_V0.1.md` — AUD-F04 layer clarification and unresolved authority findings.
- `docs/ARC10_SERVICE_BOUNDARY_TEST_STRATEGY.md` — API/service/domain separation and pending service empty behavior.
- `docs/ARC10_IMPLEMENTATION_AUTHORIZATION_GATE.md` — `IMPLEMENTATION_GATE: BLOCKED` and no production authorization.
- `docs/ARC10_EVIDENCE_INDEX.md` and `docs/ARC10_PROJECT_OWNER_EVIDENCE_ACCEPTANCE.md` — non-canonical register, D discrepancy, acceptance scope and search limitations.
- `docs/ARC10_API_CONTRACT_AND_DECISION_PACKAGE.md` — explicitly non-canonical local mirror, including its D-04/D-05 labels.
- `docs/ARC10_WORK_ORDER_V2_REGISTER_RECOVERY_AND_READINESS.md` — recovery/search snapshot and statement that the named source Work Order was not located in the inspected worktree/HEAD.

### Original ARC-10 planning reports

- `docs/ARC10_REPOSITORY_API_READINESS_REPORT.md`
- `docs/ARC10_BACKEND_API_ARCHITECTURE_PROPOSAL.md`
- `docs/ARC10_API_ENDPOINT_REQUIREMENTS_AND_DRAFT_SCHEMAS.md`
- `docs/ARC10_IMPLEMENTATION_PLAN_AND_TEST_STRATEGY.md`

These are original planning reports with historical proposal status, not final approval records. Their repository history does not authenticate a decision or designate a governance source.

### ARC-08 source evidence consulted for DR-01

Separate ARC-08 checkout: `src/quantum_space_agi/data/schemas.py`, `src/quantum_space_agi/data/validator.py`, `tests/data/test_schemas.py`, and `tests/test_data_validation.py::test_empty_dataset_is_invalid`. The schema-based empty-Dataset behavior is directly visible in `schemas.py`; `tests/data/test_schemas.py` covers other schema-based behavior but does not include a dedicated empty-Dataset assertion. The legacy validator test covers a different interface and must not be used to infer schema-based or service behavior.

### Evidence gaps and limits

- Canonical register, revision, custodian, and designating authority: not located/identified in the inspected repository evidence.
- D-04/D-05 authoritative mapping: no authoritative source located; the supplied Work Order context is not tied to a canonical register revision in inspected evidence.
- Several authorities for target, security/privacy/platform/release, schemas, and final contract: not identified.
- No final contract approval, production implementation authorization, or production target is established.
- This package does not verify live GitHub, external repositories, private messages, or external governance systems. The Evidence Index's search is bounded to its stated local scope.

## I. Response and Recordkeeping Template

Use one response per request. A response may be “refer to authority” or “pending”; silence is not approval.

```text
Request ID:
Decision / clarification / referral:
Selected behavior or authoritative reference (if applicable):
Scope and conditions:
Authority or role providing the response (only if established):
Canonical record location and revision (if designated):
Required follow-up / owner (if assigned):
Status: DECIDED / REFERRED / PENDING
```

Do not backfill an authority name, date, signature, canonical location, or approval reference unless it is actually supplied and its scope is clear. A response to this package does not, by itself, approve the final API contract or production implementation.

## J. Current Readiness and Implementation Gate

**API readiness: NOT_READY.**

**Production implementation: BLOCKED / NOT AUTHORIZED.**

This request package creates no readiness transition. Documentation and bounded contract drafting may continue only within previously recorded scope. Production implementation, deployment, and public exposure remain blocked pending the required decisions, external evidence, target and policy approvals, and explicit bounded implementation authorization. ARC-03 remains protected; ARC-08 remains reusable domain capability and is not automatically the ARC-10 implementation target.
