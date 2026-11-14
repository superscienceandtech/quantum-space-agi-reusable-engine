# ARC-10 API Validation & Integration Test Plan v0.1

**Status:** **PROPOSED — INTERNAL TEST STRATEGY**
**Acceptance criteria:** **PENDING FINAL CONTRACT AND AUTHORITY REVIEW**
**API implementation:** **NOT PRESENT / NOT AUTHORIZED**
**Tests implemented:** **NO**
**Tests executed:** **NO**
**Production readiness:** **NOT DECLARED**
**Production implementation:** **BLOCKED**

This document is a test strategy, not a final API contract, evidence of completed tests, production implementation approval, or a production-readiness declaration. Test cases that depend on unapproved request, response, security, resource, or schema decisions remain proposed or blocked.

## A. Purpose and Scope

ARC-10 needs a layered test strategy so a future implementation can keep transport errors separate from completed structural-validation reports, preserve ARC-08 domain semantics, and verify the static schema selection and provenance trust boundaries.

The proposed scope is the first drafted operation, `POST /api/v1/dataset-validations`, which mechanically validates caller-supplied records against one selected server-controlled schema. The route and request shape are draft concepts; no API server is implemented. Tests use synthetic fixtures only.

Outside scope: NASA/archive access, scientific eligibility, physical correctness, model behavior, data-rights decisions, real user data, deployment, and implementation. This plan does not approve a framework, catalog entry, DTO field rule, numeric limit, or security policy.

## B. Authority and Test Baseline

REQ-ARC10-07 in `docs/ARC10_PROJECT_OWNER_DECISION_RECONCILIATION_AND_EXECUTION_PLAN.md` authorizes these behaviors for contract drafting:

- Malformed request → HTTP 400.
- Empty `records` → HTTP 422.
- Successfully processed records with schema findings → HTTP 200 with a report whose `is_valid` is false.
- Unsupported schema ID/version → explicit rejection, no silent fallback; exact status remains pending.
- Synchronous processing only under approved resource limits; no numeric limits are approved here.
- Final error-envelope and versioning details require further documentation and review.

These are drafting decisions, not proof of implementation or final contract approval. The static schema allowlist direction is approved with conditions under REQ-ARC10-03, but no actual schema ID or content is approved. REQ-ARC10-06 security and operational requirements remain deferred. Internal architecture/runtime direction is conditional and does not authorize implementation.

## C. System Under Test and Boundaries

| Conceptual component | Current evidence/status | Test boundary |
|---|---|---|
| HTTP/API boundary | Proposed only; no ARC-10 server/route is implemented. | Future HTTP integration tests after target and contract approval. |
| Request validation and DTO mapping | Draft concepts in the contract/DTO documents; exact fields, requiredness, wire types, and error shape remain pending. | Unit tests may characterize an approved DTO later; do not assert unresolved wire details now. |
| Static schema catalog | Direction approved with conditions; catalog implementation and actual entries do not exist. | Future catalog unit tests after schema content, version, and governance decisions. |
| Provenance representation | Caller declarations must remain explicitly unverified; requiredness and wire mapping remain pending. | Component tests only after request mapping and validator choice are approved. |
| ARC-08 domain validation | Existing Python capabilities in the separate reusable-engine checkout. | Existing tests verify domain behavior only; they do not test HTTP behavior. |
| Validation-report mapping | Proposed response concept; final DTO and compatibility contract pending. | Future adapter/contract tests after report mapping approval. |
| Error mapping | Drafted behaviors plus proposed unresolved mappings in `docs/ARC10_ERROR_HTTP_MAPPING_PROPOSAL_V0.1.md`. | Assert only approved-for-drafting cases until final mapping is approved. |

The implementation layers above are conceptual. They must not be described as existing ARC-10 software.

## D. Test Levels

1. **Unit tests — PROPOSED:** exercise pure request classification, catalog lookup, mapping, and error classification without a server or network. Test only approved decisions; gate unresolved rules.
2. **Component/service tests — PROPOSED:** verify one service operation coordinates approved DTO parsing, exact catalog lookup, provenance mapping, and one selected ARC-08 validator. Inject or isolate dependencies where possible; do not fabricate provenance.
3. **API integration tests — BLOCKED:** exercise the actual HTTP route, parsing, status codes, and serialized responses only after implementation target, framework, DTO, error envelope, and final contract are approved.
4. **Contract tests — BLOCKED:** check request/response field names, requiredness, error codes, compatibility, and version behavior against the approved canonical contract. The local contract remains a draft/non-canonical.
5. **Acceptance tests — BLOCKED:** verify end-to-end user-visible requirements only after the use case, supported schemas, limits, ownership, and acceptance authority are established.
6. **Security tests — PROPOSED / BLOCKED:** test schema-injection rejection, data redaction, provenance trust boundaries, and access controls after security/privacy requirements and authority are established.
7. **Regression tests — PROPOSED:** preserve the approved behavior distinctions and verified ARC-08 semantics across changes. A passing test is software evidence only, not scientific validation or authorization.

## E. Request Validation Test Matrix

Request field names below are conceptual references to the current draft; this plan does not finalize DTO names or validation rules.

| ID | Case and synthetic input concept | Expected assertion boundary | Status / dependency |
|---|---|---|---|
| REQ-01 | Valid request structure with one synthetic record and a supported schema pair. | Once DTO and catalog are approved, request is parsed and produces a structural report. No actual schema value is supplied here. | PROPOSED; DTO, schema, provenance, and service decisions pending. |
| REQ-02 | Malformed JSON or malformed top-level request structure. | HTTP 400 is the approved drafting behavior; exact details/envelope remain unapproved. | READY TO SPECIFY at behavior level; final integration assertion pending contract. |
| REQ-03 | Missing a field later declared required by the final request DTO. | Treat as malformed request under the approved general 400 direction, subject to final definition of required fields. | PROPOSED; required DTO fields unresolved. |
| REQ-04 | Top-level request member has a transport type inconsistent with the final DTO. | Classify as malformed request; exact field diagnostics and serialization remain pending. | PROPOSED; wire types not finalized. |
| REQ-05 | Schema identifier has invalid syntax. | Do not reject according to an invented grammar. Add a test only if identifier syntax is explicitly approved; then test boundary cases. | BLOCKED; no ID grammar or actual IDs approved. |
| REQ-06 | `records` is empty. | HTTP 422 at the API boundary, as approved for contract drafting. | READY TO SPECIFY at behavior level; final envelope pending. |
| REQ-07 | A record omits a schema-required field. | If request and schema are processable, report a schema finding; this is not malformed JSON. | Domain behavior verified; API report mapping pending. |
| REQ-08 | A record supplies `None` for a field with nullability disallowed/allowed by the selected schema. | Disallowed null is a finding; allowed null passes the domain nullability check. Distinguish absent optional field from explicit null. | Domain behavior verified; schema and API mapping pending. |
| REQ-09 | Record contains an undeclared key. | Characterize the selected engine: schema-based ARC-08 `validate_dataset` does not inspect/reject undeclared keys. Do not assert API rejection or acceptance until an extra-field policy is approved. | BLOCKED for API acceptance; domain behavior verified. |
| REQ-10 | Two identical synthetic records. | Schema-based validation does not deduplicate or drop rows; both positions remain represented. Quality duplicate analysis is separate and must not be invoked implicitly. | Domain behavior verified; API behavior should preserve it unless contract changes. |
| REQ-11 | Float field includes NaN or positive/negative infinity. | Exact Python type checking accepts these as `float`; schema validation alone does not reject non-finite values. Any rejection requires an approved rule. | Domain behavior verified; finite-value policy unresolved. |
| REQ-12 | Repeat the same request with fixed schema/data and no time-dependent output requirement. | Compare deterministic status classification, finding order, counts, and row indexes; do not assert byte-identical output until serialization/correlation fields are defined. | PROPOSED; response determinism contract pending. |

## F. Static Schema Catalog Test Matrix

No actual schema ID, version, or definition may be invented for these tests. Use clearly synthetic test-only catalog fixtures once catalog implementation is authorized.

| ID | Test | Expected behavior/status | Dependency |
|---|---|---|---|
| CAT-01 | Resolve an exact known ID/version pair. | Return that exact released test entry only. | Catalog model/lookup implementation and approved lookup contract. |
| CAT-02 | Resolve unknown schema ID. | Explicit rejection; no fallback. Exact HTTP status pending. | Catalog and final error mapping. |
| CAT-03 | Known ID with unknown version. | Explicit rejection; do not select another version. Exact HTTP status pending. | Catalog and final error mapping. |
| CAT-04 | Request a latest/default/nearest version or alias. | No implicit substitution unless a later decision explicitly authorizes a documented alias policy. | Version policy approval. |
| CAT-05 | Include arbitrary schema-definition content in request. | Request cannot define, replace, or execute a caller-owned schema in the initial direction. | Final DTO and service boundary. |
| CAT-06 | Attempt runtime schema registration/mutation. | No public runtime registration path; lookup cannot change catalog contents. | Catalog implementation and security review. |
| CAT-07 | Attempt to mutate a released definition. | Released definition remains immutable; changes require a new reviewed version. | Catalog representation and release governance. |
| CAT-08 | Construct catalog with duplicate ID/version identity. | Reject duplicate identity deterministically. | Proposed catalog invariant; exact behavior needs implementation design. |
| CAT-09 | Repeat exact lookup. | Same pair resolves to the same entry and definition. | Catalog snapshot/versioning. |
| CAT-10 | Map a reviewed structural definition to `DataSchema`. | Map only identifier, version, field name, Python type, requiredness, and nullability; reject/hold unsupported semantics instead of silently translating them. | Approved definitions and wire-to-Python mapping. |

Catalog governance tests (review evidence, owner/reviewer roles, released state) are not substitutes for the actual project approval record.

## G. Provenance Test Matrix

All provenance fixture values must be synthetic and explicitly labeled as caller-declared/unverified. The proposed wire representation is not final.

| ID | Test | Expected assertion boundary | Status / dependency |
|---|---|---|---|
| PROV-01 | Supply caller-declared dataset identity/source. | Preserve the supplied declaration accurately; do not claim it is authenticated or verified. | PROPOSED; DTO mapping pending. |
| PROV-02 | Supply caller-declared retrieval timestamp. | Preserve its declared meaning; do not rewrite it from server receipt time. | PROPOSED; timestamp syntax and mapping pending. |
| PROV-03 | Supply caller-declared data format. | Accept/map only formats defined by the final contract; ARC-08 domain currently has JSON and CSV enum members. | Domain values verified; wire encoding pending. |
| PROV-04 | Capture server-observed request receipt time, if later included. | Keep it separate from caller `retrieved_at`; never substitute one for the other. | PROPOSED; whether exposed or retained is unresolved. |
| PROV-05 | Omit provenance. | Expected error or acceptance cannot be fixed until the API chooses a Dataset-based versus record-oriented input boundary and decides requiredness. | BLOCKED. |
| PROV-06 | Use malformed/naive timestamp or invalid domain format. | Domain construction currently rejects naive datetimes and non-`DataFormat` values; API status and parsing syntax remain pending. | Domain behavior verified; API mapping blocked. |
| PROV-07 | Check trust labeling. | Caller-provided metadata remains explicitly unverified; no authenticated-source evidence is inferred. | Policy direction approved in principle; final representation pending. |
| PROV-08 | Conflicting caller retrieval time and service receipt time. | Preserve separate meanings and values; never use receipt time as retrieval time. | PROPOSED; DTO mapping pending. |

## H. Domain Validation and Report Tests

These cases describe existing ARC-08 Python behavior. They are not ARC-10 HTTP acceptance results.

| ID | Case | Verified domain behavior / test assertion | Evidence and boundary |
|---|---|---|---|
| DOM-01 | Dataset conforms to every `FieldSchema`. | `validate_dataset` returns a `SchemaValidationReport` with all rows valid and no invalid records. | `src/quantum_space_agi/data/schemas.py`; `tests/data/test_schemas.py`. |
| DOM-02 | Required field is absent. | Emits a `missing` `ValidationIssue` for the corresponding zero-based row; does not drop the row. | Same source/test. |
| DOM-03 | Present `None` where `allow_none=False`. | Emits a `null` issue. When `allow_none=True`, that nullability check passes. | Same source/test. |
| DOM-04 | Exact Python type mismatch, including bool for int. | Emits a `type` issue; no coercion. | Same source/test. |
| DOM-05 | Invalid records at first and later positions. | Schema-based `InvalidRecord.record_index` is zero-based and findings retain source-list positions. | Same source/test. Do not substitute legacy indexing. |
| DOM-06 | Empty Dataset and valid schema. | `record_count=0`, `valid_count=0`, no invalid records, and derived `is_valid=True`. | Same source; API empty-`records` rule separately returns 422. |
| DOM-07 | Exact duplicate records passed to schema validation. | Structural validation does not deduplicate or drop rows. | `schemas.py`; duplicate analysis belongs to separate quality API. |
| DOM-08 | `analyze_quality` on exact duplicate JSON-compatible records. | Reports exact whole-record duplicate index groups; this is not identity resolution or schema validity. | `src/quantum_space_agi/data/quality.py`; `tests/data/test_quality.py`. |
| DOM-09 | `analyze_quality` on finite/non-finite numeric values and bools. | Numeric statistics include finite int/float and exclude bool, NaN, and infinities. The schema type validator alone can accept non-finite floats for a float field. | Quality source/tests and `schemas.py`; no automatic quality call is implied. |
| DOM-10 | Repeat schema validation on identical in-memory inputs. | Stable findings/counts/order and row indexes are expected from the deterministic traversal. | `schemas.py`; existing domain tests. Full serialized API determinism remains a contract question. |
| DOM-11 | Verify input state after validation/quality analysis. | No coercion, row dropping, or record mutation is performed by schema validation; quality analysis is documented/tested as non-mutating. Dataset only freezes/copies top-level mappings; nested lists/dicts are not deep-copied. | `models.py`, `schemas.py`, `quality.py`; `test_models.py`, `test_quality.py`. |

The separate legacy `data.validator.validate_dataset` has different inputs/report semantics: it uses one-based record indexes, has its own `SchemaDefinitionError`, reports an empty dataset as invalid, includes a generated validation timestamp, and can include actual values only when its option is enabled (default is to omit them). It must not be silently substituted or mixed with the schema-based behavior. Evidence: `src/quantum_space_agi/data/validator.py` and `tests/test_data_validation.py`.

Quality-analysis findings do not automatically change `SchemaValidationReport.is_valid`. The domain report's `is_valid` is derived from its invalid-record collection; no API rule currently combines `DataQualityReport` with that value.

## I. HTTP and Error Behavior Test Matrix

| ID | Scenario | Expected behavior/status | Approval boundary |
|---|---|---|---|
| HTTP-01 | Malformed request JSON/top-level structure. | HTTP 400 for contract drafting. | Approved under REQ-ARC10-07; detailed envelope pending. |
| HTTP-02 | Empty records. | HTTP 422 at API boundary. | Approved under REQ-ARC10-07; not ARC-08 empty Dataset behavior. |
| HTTP-03 | Request is processed but one or more records violate schema. | HTTP 200 with report `is_valid:false`. | Approved under REQ-ARC10-07. |
| HTTP-04 | Unknown schema ID/version. | Explicit rejection and no fallback. | Rejection approved; exact status pending. |
| HTTP-05 | Provenance missing/invalid. | Request classification/status pending requiredness and final representation. | Blocked. |
| HTTP-06 | Resource limit exceeded. | Explicit rejection is a candidate; exact status and retry guidance pending. | Blocked by unapproved limits. |
| HTTP-07 | Unexpected internal exception. | Generic client-safe failure without stack trace is proposed. | Not an approved status/envelope. |
| HTTP-08 | Response contains internal stack/path or raw sensitive record values. | Security test should reject such leakage under a future approved redaction policy. | Security/privacy requirements deferred; test details pending. |

## J. DTO and Response Contract Tests

After final DTO approval, test the following without treating present draft names as final:

- Required, optional, omitted, and null request-member behavior.
- JSON-to-Python type mapping, including booleans versus integers and number representation.
- Supported schema pair selection and unsupported-pair behavior.
- Mapping of `SchemaValidationReport` identity, counts, invalid row indexes, and issue concepts to the response.
- Whether any additional-value or provenance fields are exposed; default behavior should avoid echoing payload values unless explicitly approved.
- Error-envelope field names, requiredness, stable identifiers, structured details, and compatibility.
- Unsupported API/schema version behavior and response compatibility across releases.

Exact field names, requiredness, error registry, and response shape remain **PENDING**. Contract tests asserting them are blocked until the API contract is approved and its canonical location/designating authority is established.

## K. Resource and Synchronous Execution Tests

Future tests should cover below/at/above approved boundaries for record count, request payload size, processing duration, concurrency, and any approved nesting/field limits. Timeout and cancellation handling should be tested against the chosen runtime.

No numeric values are assigned here. Boundary tests cannot be finalized until an identified authority approves limits for the selected implementation target and workload. Synchronous processing must not be described as safe merely because these tests are planned or because an in-memory domain test passes.

## L. Security and Privacy Test Considerations

Proposed future checks include:

- Arbitrary schema definitions cannot be injected or executed by callers.
- No runtime schema registration or mutation is exposed.
- Unknown schema selection never falls back.
- Client responses contain no stack traces, internal paths, or unnecessary diagnostics.
- Raw records and sensitive values are not echoed by default.
- Caller-declared provenance is never promoted to authenticated source evidence.
- Server observations are not confused with caller declarations.
- Internal diagnostics are not accidentally exposed in public responses.

These checks are not a substitute for an approved threat model, access-control design, privacy policy, retention policy, or security authority. REQ-ARC10-06 is deferred; production security acceptance remains blocked.

## M. Determinism and Reproducibility

For synthetic tests with fixed input and fixed catalog/configuration:

- Exact schema pair lookup should be stable.
- Domain validation finding order, counts, and zero-based positions should be repeatable.
- The same failure should receive the same internal classification.
- Test fixtures and expected outcomes should be version-controlled and explicitly synthetic.
- No test should make a network call or depend on NASA/archive availability.
- Test execution instructions and dependency/environment versions should be recorded when implementation work is authorized.

Byte-identical HTTP responses are not required by current decisions. Correlation IDs, timestamps, serialization, and ordering of any future envelope must be defined before that guarantee can be tested.

## N. Test Fixtures and Data Policy

Use synthetic, minimal records constructed locally in tests. If a fixture includes provenance, label it as synthetic and caller-declared/unverified. Do not use real personal/user records, NASA data, external archives, or downloaded snapshots. Do not call synthetic values NASA observations, approved schema examples, or evidence of scientific eligibility.

A passing synthetic unit or integration test demonstrates only the tested software behavior. It does not establish scientific validity, source authenticity, data rights, API authorization, production readiness, or service performance on real workloads.

## O. Acceptance Criteria

### 1. Request-level acceptance

- **Supported for drafting:** malformed request maps to 400; empty `records` maps to 422.
- **Proposed:** distinguish malformed transport/DTO input from record-level findings.
- **Blocked:** exact required fields, wire types, unknown-field policy, and identifier syntax await DTO/contract decisions.

### 2. Schema catalog acceptance

- **Supported with conditions:** exact reviewed static allowlist direction; immutable released versions; explicit unknown ID/version rejection with no fallback; no arbitrary initial caller schemas.
- **Blocked:** actual IDs/definitions, owner/reviewer assignments, catalog representation, and test release evidence.

### 3. Provenance acceptance

- **Approved in principle:** caller declarations remain clearly unverified and distinct from server-observed receipt time.
- **Proposed:** tests prevent receipt-time substitution and trust escalation.
- **Blocked:** provenance requiredness, wire representation, parsing, and API error outcomes.

### 4. Domain validation acceptance

- **Verified:** selected schema-based ARC-08 behavior for requiredness, nullability, exact types, report findings, zero-based indexes, no coercion/row dropping, and empty-domain behavior.
- **Proposed:** adapter tests preserve those semantics.
- **Blocked:** final validator choice and any API mapping beyond the approved drafting behavior.

### 5. HTTP behavior acceptance

- **Supported for drafting:** malformed 400, empty 422, processed findings 200/`is_valid:false`, unsupported schema explicit rejection/no fallback.
- **Blocked:** unsupported-schema status, final error envelope, error identifiers, and versioning details.

### 6. Security/operational acceptance

- **Proposed:** safe error responses, no raw sensitive payload echo, no arbitrary schemas.
- **Blocked:** authentication/authorization, privacy, retention/logging, numeric limits, deployment, operational owner, and security review authority.

### 7. Contract compatibility acceptance

- **Proposed:** versioned contract tests should lock approved names and behavior once approved.
- **Blocked:** final DTO/API contract approval, canonical contract location, approval authority, compatibility policy, and implementation target.

No checklist item is satisfied merely because it is written here. Final acceptance must be tied to an approved contract and actual implemented tests.

## P. Traceability Matrix

| Decision/document | Test-plan coverage |
|---|---|
| REQ-ARC10-03 | Section F: exact static allowlist, reviewed immutable schema pairs, explicit unknown rejection, no arbitrary schemas. |
| REQ-ARC10-05 | Sections C/D/K: implementation/framework-boundary tests depend on conditional internal direction and target compatibility; no implementation approval inferred. |
| REQ-ARC10-06 | Sections D/L/O: security and operations test requirements remain deferred pending authority and policy. |
| REQ-ARC10-07 | Sections B/E/I/O: approved drafting status behavior and sync-only-under-approved-limits constraint. |
| ADR v0.1 | Section C: proposed service/API components are separated from existing ARC-08 domain code. |
| API Contract v0.1 | Sections B, E, I, J: draft route/behavior, unresolved DTO/errors, and structural-only claim boundary. |
| DTO Specification v0.1 | Sections E, G, J: request/provenance/response shape tests are conditional on final field decisions. |
| Provenance Proposal v0.1 | Section G: unverified caller declarations and distinct server receipt time. |
| Static Schema Catalog Design v0.1 | Section F: exact pair lookup, no fallback, immutability, governance, and mapping. |
| Error/HTTP Mapping Proposal v0.1 | Section I: approved outcomes versus proposed/pending mappings and safe error response concepts. |

## Q. Open Decisions and Dependencies

- Final request and response DTO fields, requiredness, exact wire-to-Python mapping, null/unknown-field behavior.
- Actual first-release schema IDs/versions and reviewed definitions.
- Catalog governance, owner/custodian, reviewer, release authority, and immutable storage/representation.
- Provenance requiredness and representation.
- Final error-envelope fields and stable error-code registry.
- Unsupported-schema HTTP status and API version error behavior.
- Resource-limit dimensions, numeric values, and approving authority.
- Security/authentication/authorization and privacy/logging/retention policy.
- Test environment, production implementation target, integration boundary, and operations ownership.
- Canonical contract location and final contract approval authority.
- Production implementation authorization.
- Canonical decision register and D-04/D-05 numbering discrepancy remain unresolved; this plan does not resolve or renumber them.

## R. Approval Status

| Item | Status |
|---|---|
| Test strategy | **PROPOSED** |
| Approved-for-drafting HTTP behavior | **PRESERVED**; not final API contract approval |
| Actual API implementation | **NOT PRESENT / NOT AUTHORIZED** |
| Tests implemented | **NO** |
| Tests executed | **NO** |
| Final acceptance criteria | **PENDING** |
| Production readiness | **NOT DECLARED** |
| Production implementation | **BLOCKED** |

## S. Traceable Next Steps

1. Resolve and record the required governance/contract authority and canonical contract location without changing D-04/D-05 locally.
2. Finalize request/response DTO semantics, validator/input boundary, provenance requiredness, and supported schema catalog governance/content.
3. Approve unsupported-schema mapping, error envelope/versioning, security/privacy requirements, and workload-based resource limits.
4. Confirm the implementation repository, owner, branch, framework/runtime compatibility, and integration boundary; obtain explicit implementation authorization.
5. Only then implement the agreed service/API and the unit, component, integration, contract, acceptance, and security tests at their respective boundaries.
6. Review actual test results and operational evidence before making any readiness claim.

These steps are dependency ordered. Completing this document or the earlier planning documents does not waive approvals, authorize production work, or establish API readiness.

## T. Layer clarification addendum (Prompt 12)

This addendum clarifies test ownership and acceptance boundaries. It preserves existing test IDs and planning status. It does not authorize API implementation, executable test creation, or test execution.

| Test layer | What a future test may assert | Current status and limits |
|---|---|---|
| API / HTTP | The approved-for-contract-drafting mapping: malformed request → HTTP 400; empty API `records` → HTTP 422; successfully processed schema findings → HTTP 200 with `is_valid=false`. | Behavior is approved only for contract drafting under REQ-ARC10-07. No route exists and no test is implemented or authorized by this clarification. |
| Application / service | Orchestration and dependency coordination after service semantics are decided. | **Empty-record service behavior remains pending.** Do not infer it from the API's HTTP 422 mapping, and do not prescribe whether the service rejects, returns an empty result, or invokes a domain validator. |
| ARC-08 domain | Existing Python behavior of each selected domain API, tested independently of transport. | These are source-level domain facts, not HTTP decisions. The schema-based and legacy validators have distinct empty-input and index semantics. |
| Cross-layer integration | Correct mapping between an approved API request and the selected service/domain behavior, once the call contract is defined. | Must not infer service behavior solely from the API response status. An API-boundary 422 does not establish whether the service was invoked or what it does with empty records. |

### Source-verified ARC-08 behavior relevant to acceptance criteria

- `src/quantum_space_agi/data/schemas.py`: schema-based `validate_dataset(Dataset, DataSchema)` reports missing required fields, forbidden nulls, and exact-type mismatches; it does not coerce or drop rows. `SchemaValidationReport.is_valid` is derived from an empty `invalid_records` tuple. Thus an empty `Dataset` currently produces zero records, zero valid records, no invalid records, and `is_valid=True`. This empty case follows from the inspected implementation; `tests/data/test_schemas.py` does not currently assert it directly.
- `tests/data/test_schemas.py`: verifies zero-based invalid-record indexes, exact type behavior (including bool rejected as int), multiple findings, and preservation of rows/input. These assertions apply to the schema-based domain layer.
- `src/quantum_space_agi/data/validator.py` and `tests/test_data_validation.py::test_empty_dataset_is_invalid`: the separate legacy validator reports an empty-dataset finding and uses one-based issue indexes. Do not use it as evidence for the schema-based validator's behavior.
- `src/quantum_space_agi/data/quality.py`: `analyze_quality` is a separate operation. Quality-analysis behavior or findings are not implicitly part of schema validation and do not redefine `SchemaValidationReport.is_valid`.

### Layer-specific acceptance criteria

1. **API-level criteria (drafting only):** assert only the three HTTP mappings above. The HTTP 422 assertion applies to an empty API request collection. Keep the final error envelope and other unresolved HTTP behavior blocked.
2. **Domain-level criteria:** assert the selected ARC-08 function's actual report and index semantics independently. If the empty schema-based behavior is tested, assert the current source-derived empty report; do not convert the API 422 decision into a domain finding.
3. **Application/service-level criteria:** leave empty-record expected behavior **PENDING** until an explicit service-level decision is recorded. Do not accept or reject a service implementation against an invented expectation.
4. **Integration-level criteria:** once a service call boundary is defined, test API-to-service mapping explicitly. Do not infer service invocation, service rejection, or a service result from HTTP 422 alone.
5. All criteria remain synthetic-software checks. They establish neither scientific validity nor NASA authenticity, authorization, or data rights.

No existing test identifier is renamed or repurposed. Existing IDs remain plans at their previously stated readiness levels. This documentation clarification changes no implementation or test-execution status.
