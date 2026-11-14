# ARC-10 Error / HTTP Mapping and Behavior Proposal v0.1

**Status:** **PROPOSED — INTERNAL API BEHAVIOR DESIGN**
**Final error mapping and envelope:** **PENDING REVIEW**
**Final API contract:** **PENDING**
**Production implementation:** **BLOCKED**

This document proposes an error classification and HTTP mapping for the drafted `POST /api/v1/dataset-validations` operation. It is not a final API contract, canonical governance record, production implementation authorization, or approval of security, privacy, resource, or deployment policy. The Project Owner's approved drafting behavior is separated below from verified ARC-08 domain behavior and recommendations that still need review.

## A. Purpose and Scope

An API needs to distinguish a request that cannot be processed from a request that was processed and whose records do not conform to the selected structural schema. A stable distinction prevents clients from treating ordinary record findings as transport failures and gives future service code a reviewable boundary for errors.

This proposal addresses request and operation outcomes for the first drafted dataset-validation operation only. It does not implement HTTP behavior, choose a framework, define a production DTO, establish scientific validity or eligibility, authenticate sources, or authorize NASA data access, retention, or redistribution. It does not define numeric limits or an operational logging/retention policy.

## B. Authority and Decision Baseline

The Project Owner's decision dated 13 November 2026 is recorded as REQ-ARC10-07 in `docs/ARC10_PROJECT_OWNER_DECISION_RECONCILIATION_AND_EXECUTION_PLAN.md`. It authorizes the following behavior for contract drafting:

1. Malformed request: HTTP 400.
2. Empty `records`: HTTP 422.
3. Records that are successfully processed but have schema-validation findings: HTTP 200 with a validation report and `is_valid: false`.
4. Unsupported schema ID/version: explicit rejection, with no silent fallback. The exact HTTP status was not specified.
5. Synchronous execution is conditional on approved resource limits; this does not establish that limits have been chosen or approved.
6. API versioning and final error-envelope definitions must be documented and reviewed.

The first three status behaviors are **APPROVED FOR CONTRACT DRAFTING**, not a final approved wire contract. Exact unsupported-schema status, response fields, error-code registry, API version compatibility, resource limits, and production behavior remain unresolved. See also `docs/ARC10_API_CONTRACT_V0.1.md` and `docs/ARC10_DTO_SPECIFICATION_V0.1.md`.

## C. Error Classification

The classifications below distinguish conceptual categories; they do not imply that every category has an approved public code or status.

| Category | Meaning | Evidence/status boundary |
|---|---|---|
| Malformed HTTP/request payload | Request syntax or top-level structure cannot be parsed or accepted. | HTTP 400 is approved for contract drafting. Exact malformed cases and response shape remain pending. |
| Empty `records` | Request is structurally processable but contains no records. | HTTP 422 is approved for contract drafting, independently of ARC-08 domain behavior for an empty `Dataset`. |
| Unsupported schema ID | The requested identifier is not in the server-controlled allowlist. | Explicit rejection/no fallback is approved by REQ-ARC10-03 and -07; exact status/code pending. |
| Unsupported schema version | The ID may be known, but the exact requested version is not supported/released. | Explicit rejection/no substitution is approved; exact status/code pending. |
| Schema-validation findings | A processed record is missing a required field, has forbidden null, or has a wrong exact Python type under the selected ARC-08 `DataSchema`. | These are report findings, not operation exceptions, in the schema-based ARC-08 validator. Drafted API behavior is HTTP 200 with `is_valid: false` when findings exist. |
| Provenance-related request issue | A provenance declaration is absent, malformed, or cannot be mapped under a future approved request contract. | ARC-08 domain construction has concrete requirements, but API provenance requiredness and mapping remain pending. Do not equate caller declarations with authentication. |
| Resource-limit violation | A request exceeds a future approved payload, record, processing, concurrency, or other limit. | Limits, authorities, and HTTP mapping are not approved or implemented. |
| Internal processing failure | An unexpected adapter, runtime, or server failure prevents a completed report. | No ARC-08 function defines an HTTP response. Client response, diagnostics, correlation, and retry policy remain proposals. |
| Unsupported operation/API version | Requested route, method, or API version is outside the eventual published contract. | Only the drafted operation and `/v1/` path convention exist in current planning; general versioning and unsupported-operation mapping remain unresolved. |

A catalog-definition/configuration defect is distinct from a caller selecting an unknown ID. The first is an internal release/configuration problem; the second is an unsupported request selection. The service must not expose internal catalog details as if they were caller record findings.

### Verified ARC-08 behavior relevant to classification

The schema-based `quantum_space_agi.data.schemas.validate_dataset` returns a `SchemaValidationReport` for record-level missing/null/type findings; those findings are represented by `InvalidRecord` and `ValidationIssue` values rather than raised as request exceptions. Invalid `FieldSchema`/`DataSchema` declarations raise the existing `quantum_space_agi.errors.ValidationError`. `Dataset` construction rejects a missing/wrong `Provenance` object or malformed record mappings with `ValueError`; `Provenance` construction also raises `ValueError` for invalid domain values, and `DataSource` validation uses `DataSourceError`. These are Python-domain behaviors only and do not select HTTP mappings.

The separate legacy `quantum_space_agi.data.validator.validate_dataset` accepts a different input/schema shape, raises `SchemaDefinitionError` for schema-definition problems and `TypeError` for invalid top-level record containers, and returns its own report for record findings. Its indexes are one-based, unlike the schema-based validator's zero-based indexes; it must not be silently substituted.

## D. Approved HTTP Behavior Matrix

| Scenario | Approved status/behavior for contract drafting | Decision source | Notes |
|---|---|---|---|
| Malformed request syntax or structure | **HTTP 400** | REQ-ARC10-07; reconciliation and API Contract v0.1 | Detailed classification, issue fields, and envelope remain pending. Do not classify ordinary schema findings as malformed requests. |
| Empty `records` | **HTTP 422** | REQ-ARC10-07; API Contract v0.1 and DTO Specification v0.1 | API-boundary behavior only. It does not change ARC-08's empty-dataset result. |
| Processed records contain schema findings | **HTTP 200**, return report with **`is_valid: false`** | REQ-ARC10-07; API Contract v0.1 | The operation completed. Findings remain in the report; they are not converted to 400/422. |
| Unsupported schema ID/version | **Explicit rejection; no fallback**; exact status **PENDING** | REQ-ARC10-03 and -07; Static Schema Catalog Design v0.1 | Do not choose latest/default/another version or accept a caller-defined schema. |
| Synchronous execution | Allowed only **under approved resource limits** | REQ-ARC10-07 and reconciliation | No numeric limits or limit approver are established here. This condition is not evidence that an operation is currently safe to run synchronously. |
| Final API versioning and error envelope | Must be documented and reviewed; exact behavior **PENDING** | REQ-ARC10-07 | `/api/v1/` is a draft path convention, not a completed project-wide compatibility policy. |

## E. Proposed HTTP Mapping for Unresolved Categories

Every status in this table is a **PROPOSAL — NOT APPROVED**. Alternatives are retained where the source decisions do not select one. Any final mapping depends on the request/response contract, framework/runtime target, resource policy, and designated review authority.

| Unresolved scenario | Candidate mapping (proposal only) | Rationale and alternatives/dependencies |
|---|---|---|
| Unknown schema ID or unsupported schema version | Consider HTTP 422 as a semantically unsupported selection; alternatives include 400 as an invalid request value or 404 if schemas are modeled as addressable resources. **No status selected.** | Must preserve explicit rejection and no fallback. The choice depends on final API semantics and error mapping review. Do not imply 404/400/422 has Project Owner approval for this case. |
| Missing or invalid provenance declaration | If the final DTO makes provenance required, consider HTTP 400 for malformed/incomplete request syntax/structure; consider 422 only if a well-formed declaration fails a semantic constraint. **No mapping selected.** | Provenance requiredness, member representation, parser rules, and adapter choice remain unresolved. Missing provenance must not be fabricated or silently replaced with server receipt time. |
| Request body exceeds a future byte-size cap | Consider HTTP 413. **PROPOSED, NOT APPROVED.** | Depends on a defined body-size limit and platform behavior. No limit value or owner is approved. |
| Record-count, nesting, processing-time, or concurrency limit exceeded | Consider an explicit client rejection; candidate statuses may differ by limit class (for example, 422 for a request-bound semantic cap or 429 for a concurrency/rate policy). **No status selected.** | Do not assign one status across unlike limits. Thresholds, authority, whether a request is retryable, and synchronous execution conditions need approval. A server-side timeout mapping also remains open. |
| Unexpected internal processing failure | Consider HTTP 500 with a generic client-safe message. **PROPOSED, NOT APPROVED.** | Avoid stack traces and internal details in the response. Whether a correlation identifier is returned and how diagnostics are handled requires security/operations review. |
| Unsupported route or method | Consider conventional 404 for an unknown route and 405 for a known route with unsupported method. **PROPOSED, NOT APPROVED.** | The eventual routing/framework contract and behavior for unsupported API versions must be reviewed. Do not treat an unsupported schema as an unsupported route. |
| Unsupported API major version | No status selected; consider 404 or a documented client-error response after versioning policy is approved. **PROPOSED, NOT APPROVED.** | Version negotiation, route behavior, deprecation, and compatibility rules are not settled. |
| Unsupported media type, if request content types are constrained | Consider HTTP 415. **PROPOSED, NOT APPROVED.** | Accepted media types and parser boundary are not yet established by the final DTO/contract. |

The entries above are review candidates, not instructions to implement these status codes. The approved HTTP 400 and 422 cases in Section D remain the only approved request-error status decisions here; the approved HTTP 422 for empty records must not be generalized to other cases.

## F. Validation Failure vs API Error

A request can be accepted, parsed, resolved to a supported schema, and fully processed even though one or more records violate that schema. For this case, the Project Owner-approved drafting behavior is HTTP 200 with a validation report whose `is_valid` is false. Missing required fields, forbidden nulls, and exact-type mismatches are record-level findings under the schema-based ARC-08 validator. They do not by themselves mean that the HTTP request was malformed.

Request-level errors prevent the operation from completing normally: examples include malformed request structure, empty `records` under the approved API rule, or an unsupported schema pair. Their exact public envelope remains pending where not specified. The service must not turn record-level findings into HTTP 400 or 422 merely because `is_valid` is false.

The word “valid” in this report means structural conformance to the selected mechanical schema only. It does not mean scientifically valid, physically plausible, eligible for research, authentic, or authorized for use.

## G. Error Envelope Proposal

No final error-envelope field names or requiredness are approved. The following concepts are **PROPOSED** and should be mapped to final wire names only after DTO/contract review.

| Concept (not a final field name) | Purpose | Proposed requiredness/status |
|---|---|---|
| Stable machine-readable error identifier | Lets clients distinguish supported error classes without parsing prose. | Proposed; registry, spelling, scope, and stability guarantee unresolved. |
| Human-readable summary | Gives a concise explanation suitable for a client. | Proposed; requiredness and localization policy unresolved. |
| Request/correlation reference | Allows a client to refer to one failed operation without echoing payload data. | Optional proposal; generation, uniqueness, exposure, retention, and authority unresolved. |
| Structured safe details | Provides field or category context where approved and useful. | Optional/proposed; shape and redaction rules unresolved. Never include raw record values by default. |
| Retryability indication | Helps clients decide whether to retry. | Unresolved; must not promise retry safety before idempotency, rate, and transient-failure policies are defined. |

Illustrative concept only, **not executable JSON and not an approved response shape**:

```text
error concept:
  stable error identifier: <proposal>
  summary: <synthetic explanation>
  request reference: <optional proposal>
  safe details: <optional proposal>
```

Do not assume these labels become property names. The successful validation report is a distinct response concept and must not be wrapped in or confused with an error envelope solely because `is_valid` is false.

## H. Error Detail and Information Exposure

**Proposed safety guidance, pending security/privacy review:** return only client-useful information needed to correct a request. Do not return stack traces, internal paths, framework exception text, environment details, or full submitted records. Avoid echoing sensitive field values or unnecessary provenance. Keep operational diagnostics separate from public messages.

ARC-08's legacy record-oriented validator omits actual values from its `ValidationIssue` by default and exposes an `include_actual_values` option. That is a verified Python API behavior, not an HTTP privacy policy. The schema-based validator's `ValidationIssue` contains `field`, `code`, and `message`, but the service still needs to review whether/how those are exposed. No logging, retention, access-control, incident, or privacy policy is approved by this proposal.

`analyze_quality` is a separate domain operation and is not part of the drafted validation endpoint. It returns a `DataQualityReport`; unsupported non-JSON-compatible nested values can raise the existing `ValidationError`. Neither that report nor its exceptions define an HTTP response here.

## I. Provenance-Related Errors

ARC-08 `Dataset` requires a `Provenance` instance. `Provenance` requires `dataset_id`, `DataSource`, timezone-aware `retrieved_at`, and a `DataFormat`; `DataFormat` currently has `JSON` and `CSV`. Those are domain construction constraints, not a finalized HTTP DTO. Caller-provided provenance remains caller-declared and unverified under the ARC-10 provenance proposal.

The following classification is conditional and **PROPOSED, NOT APPROVED**:

- If the final API requires a provenance object and it is absent or malformed, the request may be classified as malformed/incomplete and mapped under the approved general HTTP 400 direction. Whether a missing member qualifies as malformed, and the exact response, remain pending.
- A well-formed but unsupported provenance representation or value may be treated as a semantic request error; whether HTTP 400 or 422 applies is unresolved.
- If provenance is optional or a record-oriented validator is selected, the corresponding missing-provenance case may not be an error. The service boundary and validator choice are still open.
- Never invent `dataset_id`, source identity, `retrieved_at`, format, or trust evidence. Server request receipt time is distinct and must not replace `retrieved_at`.
- A provenance parsing/validation result does not authenticate the claimed source or grant data-use authorization.

The final error policy must be reconciled with `docs/ARC10_PROVENANCE_REPRESENTATION_PROPOSAL_V0.1.md` and the approved DTO/contract review.

## J. Unsupported Schema Behavior

The Project Owner-approved direction requires explicit rejection of an unknown schema ID or version, with no silent fallback. The static catalog design further specifies exact `(schema_id, schema_version)` lookup, no automatic selection of another version, no caller-defined schemas, and no dynamic caller registration.

The service should distinguish an unknown caller selection from an internal catalog defect, but this is a **PROPOSED** internal classification. Exact public status, error code, safe message, and envelope remain pending API error mapping/final contract review. The ARC-08 `DataSchema` model itself is not an HTTP catalog and does not define these responses.

## K. Resource Limits and Synchronous Execution

Synchronous execution is authorized for drafting only under resource limits that must be approved. No numeric threshold is supplied or approved in the inspected decision documents, and this proposal does not invent one.

Potential limit dimensions to evaluate include:

- Request body bytes.
- Number of records.
- Record/field count and nested-value depth, if nested structures are accepted.
- Validation processing time.
- Concurrent requests and queue capacity.

Before synchronous execution is considered operationally acceptable, the project must identify the decision authority and obtain approval for the relevant dimensions and thresholds based on the chosen target and workload. A future over-limit request should be rejected explicitly and before unbounded work where feasible, but its status, response details, and retry guidance remain **PROPOSED / PENDING**. The inspected ARC-08 domain APIs do not define HTTP request-size, concurrency, or service timeout limits.

## L. Internal Errors and Observability

**PROPOSED, pending review:** unexpected internal exceptions should produce a generic client-safe server error rather than exposing stack traces or private implementation details. A request/correlation reference may be useful if the project approves its generation and exposure. Detailed diagnostics should be kept separate from the response and handled under a future approved operational policy.

This proposal does not establish logging, monitoring, audit retention, redaction implementation, retryability, alerting, or incident-response behavior. It does not invent an ARC-08 exception-to-HTTP mapping. Domain exceptions and validation reports must be translated only by a future reviewed API adapter.

## M. Compatibility and API Versioning

The draft operation uses `/api/v1/dataset-validations`; the current contract describes the path version as a draft convention rather than a project-wide version policy. Stable error identifiers, if adopted, should not change meaning silently, but the registry, compatibility promise, and deprecation process are unresolved proposals.

Any change to status semantics, envelope fields, error identifiers, or validation-report behavior should be documented and reviewed with the API contract and DTO. Unsupported API-version behavior is not selected here. This document does not establish compatibility guarantees or authorize a route implementation.

## N. Testing and Acceptance Criteria (Proposed)

These are test-design recommendations only. No API tests were implemented or executed for this document.

| Test layer | Proposed cases | Expected assertion boundary |
|---|---|---|
| Unit | Classification of malformed request, empty records, unsupported ID/version, provenance cases, limit cases, and unexpected exceptions. | Classification is deterministic and separate from record-level findings; unresolved status mappings remain gated until approved. |
| Unit/domain adapter | A processed record with missing/null/type findings; valid records; schema-definition/configuration errors. | Schema-based `validate_dataset` returns findings in `SchemaValidationReport` with zero-based indices and no row dropping; adapter behavior awaits selection/approval. |
| HTTP integration | Valid request completes with a report; malformed JSON or missing required request structure → 400; empty records → 422; processed schema findings → 200 and `is_valid:false`; unknown schema → explicit rejection. | Assert only the three approved status behaviors; assert unknown-schema status only after it is selected and approved. |
| Contract/acceptance | Final envelope fields, error-code registry, unsupported schema mapping, provenance error policy, operation/version behavior. | Blocked until final DTO and API contract review records these decisions. |
| Resource/security review | Requests at/beyond approved body/record/time/concurrency limits; safe diagnostics; no stack trace or raw input echo. | Blocked until numeric limits and security/privacy/operational requirements are approved. |

ARC-08 domain test evidence establishes Python behavior only. It does not establish that HTTP behavior has been implemented or tested. No test result is claimed.

## O. Open Decisions and Dependencies

1. Exact HTTP status and public error identifier for unsupported schema IDs/versions.
2. Final error-envelope field names, requiredness, safe-details structure, and compatibility guarantees.
3. Stable error-code registry and versioning/retirement policy.
4. Provenance requiredness, accepted wire representation, malformed-versus-semantic classification, and response behavior.
5. Numeric resource-limit dimensions/values and the authority responsible for approving them.
6. Authentication/authorization and broader security requirements.
7. Privacy, input echo/redaction, logging, monitoring, and retention policy.
8. Production implementation target repository, owner, branch, framework/runtime, and integration boundary.
9. Final API contract approval authority and canonical contract location.
10. Canonical governance register and D-04/D-05 numbering discrepancy remain unresolved; this proposal does not resolve or renumber them.

## P. Approval Status

| Behavior or decision | Status | Qualification |
|---|---|---|
| Malformed request → HTTP 400 | **APPROVED FOR CONTRACT DRAFTING** | Detailed categories and envelope remain pending. |
| Empty `records` → HTTP 422 | **APPROVED FOR CONTRACT DRAFTING** | API boundary rule; ARC-08 empty domain behavior differs. |
| Processed schema findings → HTTP 200 and `is_valid: false` | **APPROVED FOR CONTRACT DRAFTING** | Structural report only; not scientific validation. |
| Unsupported schema ID/version → explicit rejection/no fallback | **APPROVED** | Exact HTTP status and public error mapping **PENDING**. |
| Final error envelope and stable code registry | **PENDING** | No final field names or registry approved. |
| Numeric resource limits | **NOT APPROVED** | No values or approving authority established here. |
| Security/privacy policy | **DEFERRED** | This proposal is not a security or privacy approval. |
| Final API contract | **PENDING** | Draft v0.1 remains non-final. |
| Production implementation | **BLOCKED** | This document grants no implementation authorization. |

## Q. Traceability

| Rule or proposal | Source and treatment |
|---|---|
| REQ-ARC10-07: operation and approved drafting behavior | `docs/ARC10_PROJECT_OWNER_DECISION_RECONCILIATION_AND_EXECUTION_PLAN.md`; recorded in Sections B and D without expanding the decision. |
| Architecture direction and implementation boundary | `docs/ARC10_ARCHITECTURE_DECISION_RECORD_V0.1.md`; planning direction only, not production authorization. |
| Request/response and HTTP draft behavior | `docs/ARC10_API_CONTRACT_V0.1.md`; draft facts distinguished from unresolved status/envelope. |
| Candidate request/response DTO and validation semantics | `docs/ARC10_DTO_SPECIFICATION_V0.1.md`; proposed wire shape remains pending. |
| Caller-declared provenance and trust distinction | `docs/ARC10_PROVENANCE_REPRESENTATION_PROPOSAL_V0.1.md`; declarations are not authentication. |
| Exact static schema lookup and no-fallback rule | `docs/ARC10_STATIC_SCHEMA_CATALOG_DESIGN_V0.1.md`; actual IDs/content remain unapproved. |
| Contract-neutral service and test boundaries | `docs/ARC10_CONTRACT_NEUTRAL_SERVICE_DESIGN.md` and `docs/ARC10_SERVICE_BOUNDARY_TEST_STRATEGY.md`; recommendations only. |
| Verified ARC-08 domain behavior | Separate checkout: `src/quantum_space_agi/data/schemas.py`, `models.py`, `provenance.py`, `sources.py`, `quality.py`, `validator.py`, `errors.py`, and `data/errors.py`; relevant evidence includes `tests/data/test_schemas.py`, `tests/data/test_models.py`, `tests/data/test_provenance.py`, `tests/data/test_quality.py`, and `tests/test_data_validation.py`. These do not define HTTP status codes or an API error envelope. |

The local ARC-10 decision package remains non-canonical. D-04/D-05 remains open. This proposal does not designate a canonical register, resolve that discrepancy, approve the final contract, or authorize production implementation.
