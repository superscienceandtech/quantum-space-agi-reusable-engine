# ARC-10 Decision-Independent Test Case Catalog

**Status:** Test-design artifact only. The catalog does not approve the use case, API contract, schema catalog, architecture, implementation target, or production implementation. All example inputs described here are synthetic. No tests were executed for this task, and no result below is represented as a new test result.

## Scope and evidence basis

The candidate operation is mechanical validation of caller-supplied records against one explicitly selected, versioned structural schema. It remains proposed pending the applicable project decisions. This operation must not be described as scientific validation, scientific eligibility, source authentication, or NASA authorization.

The ARC-08 domain behavior below was inspected in the separate checkout at `arc/08-ai-ml`, HEAD `de48b077571fe44b1fc8b7ab8fad6ba60016f029`. Relevant implementation: `src/quantum_space_agi/data/models.py`, `provenance.py`, `sources.py`, `schemas.py`, and `quality.py`. Relevant existing tests: `tests/data/test_models.py`, `test_provenance.py`, `test_sources.py`, `test_schemas.py`, and `test_quality.py`. These paths refer to ARC-08, not this ARC-10 worktree. Existing tests document some behaviors; source inspection documents the rest. This catalog does not assert that those tests were run in this task.

ARC-10 references reviewed:

- `docs/ARC10_SERVICE_BOUNDARY_TEST_STRATEGY.md` — proposed service test layers and explicit unresolved API semantics.
- `docs/ARC10_CONTRACT_NEUTRAL_SERVICE_DESIGN.md` — current engine comparison and contract-neutral boundary; no route, framework, or DTO is selected.
- `docs/ARC10_PROJECT_DECISION_REQUEST.md` — pending decisions on implementation target, provenance, schema catalog, ownership, framework/runtime, security/operations, and API behavior.

### Status and layer definitions

- **READY TO SPECIFY:** an offline domain test can be specified against behavior present in ARC-08 today. This does not mean it was executed or that ARC-10 selected that API.
- **PROPOSED:** a conceptual application/service test can be described, but its API-level assertions depend on a decision or implementation boundary that is still pending.
- **BLOCKED:** no executable expectation should be fixed until the identified decision/evidence exists.
- **Domain, application/service, DTO, HTTP integration** identify the proposed test layer. **Blocked** means the layer itself cannot yet be selected or asserted safely.

## A. Decision-independent domain cases

These cases specify synthetic tests against existing ARC-08 domain APIs only. They do not create ARC-10 API semantics.

### 1. Dataset construction and provenance requirements

| ID | Objective; preconditions and synthetic input | Expected behavior (verified) | Evidence | Layer / status | Dependency or unresolved decision |
|---|---|---|---|---|---|
| TC-01 | Construct `Dataset` with synthetic record mappings, first with valid `Provenance`, then with `None` or a non-`Provenance` value. | Valid provenance is required; invalid provenance raises `ValueError`. Each record must be a mapping with string keys. | `data/models.py`; `tests/data/test_models.py` | Domain / READY TO SPECIFY | ARC-10 must decide whether caller provenance is required and how truthful caller declarations enter any service. Do not fabricate provenance. |
| TC-02 | Construct `Provenance` with a synthetic `DataSource`, timezone-aware and naive timestamps, and enum versus string format values. | Requires a `DataSource`, timezone-aware `datetime`, and `DataFormat`; dataset ID must be non-empty. `DataFormat` currently defines JSON and CSV. | `data/provenance.py`; `tests/data/test_provenance.py` | Domain / READY TO SPECIFY | The model validates declarations; it does not authenticate them or prove source identity. Service representation remains undecided. |
| TC-03 | Construct synthetic `DataSource` values with an empty identifier and with optional description, URL, version, or metadata omitted. | Identifier must be non-empty; optional values may remain unset. The in-memory registry rejects duplicate identifiers within that registry instance. | `data/sources.py`; `tests/data/test_sources.py` | Domain / READY TO SPECIFY | This registry is not evidence of an approved production schema or source catalog. |

### 2. Schema definition and schema consistency

| ID | Objective; preconditions and synthetic input | Expected behavior (verified) | Evidence | Layer / status | Dependency or unresolved decision |
|---|---|---|---|---|---|
| TC-04 | Construct `FieldSchema` with a valid name/type and boolean flags, then with empty name, non-type `value_type`, or non-boolean `required`/`allow_none`. | Field name must be non-empty, `value_type` must be a Python type, and both flags must be booleans; invalid declarations raise `ValidationError`. | `data/schemas.py` | Domain / READY TO SPECIFY | None for this domain contract. This does not define a public JSON Schema or wire type mapping. |
| TC-05 | Construct `DataSchema` with synthetic identifier/version and a tuple or iterable of `FieldSchema` values; try empty identity or a non-`FieldSchema` member. | Identifier and version must be non-empty. Fields are stored as a tuple and must contain `FieldSchema` values. | `data/schemas.py`; `tests/data/test_schemas.py` | Domain / READY TO SPECIFY | No production schema IDs, contents, ownership, or registry are established. |
| TC-06 | Construct a synthetic `DataSchema` with two fields sharing a name. | Duplicate field names raise `ValidationError`. | `data/schemas.py`; `tests/data/test_schemas.py::test_schema_rejects_duplicate_field_names` | Domain / READY TO SPECIFY | None for domain consistency; catalog ownership remains a separate blocked decision. |

### 3. Valid record validation

| ID | Objective; preconditions and synthetic input | Expected behavior (verified) | Evidence | Layer / status | Dependency or unresolved decision |
|---|---|---|---|---|---|
| TC-07 | Use a synthetic `Dataset` and matching versioned `DataSchema`; include required fields with exact Python types and omit an optional field. | Report identifies schema ID/version, counts all rows, reports no invalid rows, and derives `is_valid=True`. | `data/schemas.py`; `tests/data/test_schemas.py::test_schema_reports_all_valid_rows_and_schema_version` | Domain / READY TO SPECIFY | No decision for engine behavior. This does not approve a schema or indicate scientific correctness. |

### 4. Missing required fields

| ID | Objective; preconditions and synthetic input | Expected behavior (verified) | Evidence | Layer / status | Dependency or unresolved decision |
|---|---|---|---|---|---|
| TC-08 | Schema has a required field; one synthetic record omits it while another is valid. | Missing required field is reported with issue code `missing`; the invalid row index and valid/record counts are retained. | `data/schemas.py`; `tests/data/test_schemas.py::test_schema_reports_missing_required_fields_by_record_index` | Domain / READY TO SPECIFY | API mapping of findings versus request errors remains undecided. |

### 5. Optional fields

| ID | Objective; preconditions and synthetic input | Expected behavior (verified) | Evidence | Layer / status | Dependency or unresolved decision |
|---|---|---|---|---|---|
| TC-09 | Schema declares a field `required=False`; synthetic record omits it. | Absence of an optional field creates no issue. | `data/schemas.py`; `tests/data/test_schemas.py::test_schema_allows_optional_and_nullable_field` | Domain / READY TO SPECIFY | Public absent-field representation remains a DTO decision. |

### 6. Nullability

| ID | Objective; preconditions and synthetic input | Expected behavior (verified) | Evidence | Layer / status | Dependency or unresolved decision |
|---|---|---|---|---|---|
| TC-10 | Required, non-nullable synthetic field is present with `None`. | A `null` issue is reported; this is distinct from a missing-field issue. | `data/schemas.py`; `tests/data/test_schemas.py::test_schema_reports_disallowed_none_and_wrong_types` | Domain / READY TO SPECIFY | API encoding of null and issue details require contract decisions. |
| TC-11 | Synthetic field uses `allow_none=True` and is present as `None`. | Explicit null passes that field's nullability check. | `data/schemas.py`; `tests/data/test_schemas.py::test_schema_allows_optional_and_nullable_field` | Domain / READY TO SPECIFY | Does not decide whether a production DTO allows null. |

### 7. Exact Python type behavior

| ID | Objective; preconditions and synthetic input | Expected behavior (verified) | Evidence | Layer / status | Dependency or unresolved decision |
|---|---|---|---|---|---|
| TC-12 | Integer field receives synthetic string `"3"`; also try another non-exact type. | Exact type mismatch is reported with issue code `type`; values are not converted. | `data/schemas.py`; `tests/data/test_schemas.py::test_schema_reports_disallowed_none_and_wrong_types` | Domain / READY TO SPECIFY | Wire-format-to-Python-type mapping is unresolved. |
| TC-13 | Integer field receives `True`. | Boolean is rejected for an `int` field because validator uses exact `type(value) is expected_type`. | `data/schemas.py`; `tests/data/test_schemas.py::test_schema_does_not_accept_boolean_as_integer` | Domain / READY TO SPECIFY | None for this engine behavior. |

### 8. Multiple validation findings in one record

| ID | Objective; preconditions and synthetic input | Expected behavior (verified) | Evidence | Layer / status | Dependency or unresolved decision |
|---|---|---|---|---|---|
| TC-14 | One synthetic record omits a required field and supplies a wrong type for another, in a schema with known field order. | All findings are preserved for the row in schema-field order; the row is not dropped. | `data/schemas.py`; `tests/data/test_schemas.py::test_schema_reports_multiple_issues_without_dropping_or_mutating_rows` | Domain / READY TO SPECIFY | Public issue ordering/serialization is not yet an approved API contract. |

### 9. Multiple invalid records

| ID | Objective; preconditions and synthetic input | Expected behavior (verified) | Evidence | Layer / status | Dependency or unresolved decision |
|---|---|---|---|---|---|
| TC-15 | Synthetic records at multiple positions each have distinct missing/null/type findings, with valid records between them. | Each invalid row is represented in `invalid_records`; counts reconcile as `valid_count = record_count - number_of_invalid_records`. | `data/schemas.py`; `tests/data/test_schemas.py` | Domain / READY TO SPECIFY | No domain decision. Exact transport response size limits remain blocked. |

### 10. Zero-based record index preservation

| ID | Objective; preconditions and synthetic input | Expected behavior (verified) | Evidence | Layer / status | Dependency or unresolved decision |
|---|---|---|---|---|---|
| TC-16 | Place invalid synthetic records at the first and a later position, with a valid row between them. | Schema validator uses zero-based positions from `enumerate(dataset.records)`. | `data/schemas.py`; `tests/data/test_schemas.py::test_schema_reports_missing_required_fields_by_record_index`; ARC-10 test strategy | Domain / READY TO SPECIFY | ARC-10 must explicitly select a validator and preserve its index basis if exposed. The legacy validator is one-based. |

### 11. Empty dataset domain behavior

| ID | Objective; preconditions and synthetic input | Expected behavior (verified) | Evidence | Layer / status | Dependency or unresolved decision |
|---|---|---|---|---|---|
| TC-17 | Construct a valid synthetic `Dataset` with an empty record sequence and validate against a valid schema. | Current schema validator returns zero record/valid counts, no invalid rows, and `is_valid=True`. This is a mechanical empty-result behavior, not evidence that useful data was checked. | `data/schemas.py`; `docs/ARC10_SERVICE_BOUNDARY_TEST_STRATEGY.md` | Domain / READY TO SPECIFY | Whether an API accepts or rejects an empty collection is unresolved; do not carry this domain result over as HTTP behavior. |

### 12. No coercion and no row dropping

| ID | Objective; preconditions and synthetic input | Expected behavior (verified) | Evidence | Layer / status | Dependency or unresolved decision |
|---|---|---|---|---|---|
| TC-18 | Keep a synthetic invalid value (for example string in integer field) and compare input, dataset rows, and report counts before/after validation. | Validator reports issues without coercing values, deleting rows, or mutating record contents; `record_count` still includes invalid rows. | `data/schemas.py`; `tests/data/test_schemas.py::test_schema_reports_multiple_issues_without_dropping_or_mutating_rows` | Domain / READY TO SPECIFY | HTTP/service adapters need their own boundary tests after approved input semantics exist. |

### 13. Mutation and nested mutable-value risks

| ID | Objective; preconditions and synthetic input | Expected behavior (verified) | Evidence | Layer / status | Dependency or unresolved decision |
|---|---|---|---|---|---|
| TC-19 | Construct a synthetic `Dataset` from caller-owned top-level record and metadata dicts, then mutate the original top-level dicts and attempt writes through dataset mappings. | Dataset copies top-level maps and exposes them read-only; later top-level caller changes do not alter those maps. | `data/models.py`; `tests/data/test_models.py::test_dataset_preserves_records_and_metadata_without_aliasing_top_level_maps`, `test_dataset_records_are_read_only_mappings` | Domain / READY TO SPECIFY | None for stated shallow-copy behavior. |
| TC-20 | Construct a synthetic dataset with nested list/dict values; mutate the original nested object and observe the dataset. | Nested values are not deep-copied or frozen and remain shared/mutable. This case documents a limitation; it must not assert deep immutability. | `data/models.py`; `tests/data/test_models.py::test_dataset_nested_dicts_and_lists_remain_mutable_and_shared` | Domain / READY TO SPECIFY | Service isolation/copy policy is undecided; do not imply current nested-value isolation. |

### 14. Deterministic validation behavior

| ID | Objective; preconditions and synthetic input | Expected behavior (verified) | Evidence | Layer / status | Dependency or unresolved decision |
|---|---|---|---|---|---|
| TC-21 | Validate identical synthetic records with the same `DataSchema` repeatedly. | Schema report fields and issue order are deterministic for identical inputs; the schema report has no generated timestamp. | `data/schemas.py`; `tests/data/test_schemas.py` | Domain / READY TO SPECIFY | Byte-level API determinism and serialization are separate, unresolved contract decisions. |

### 15. Quality analysis distinctions

These are optional domain-analysis cases, not part of the proposed first validation operation. ARC-10's service design proposes excluding automatic quality analysis from the initial slice.

| ID | Objective; preconditions and synthetic input | Expected behavior (verified) | Evidence | Layer / status | Dependency or unresolved decision |
|---|---|---|---|---|---|
| TC-22 | Pass synthetic records with a key absent, `None`, empty text, and whitespace-only text to `analyze_quality`. | Quality analysis counts all four forms as missing for an observed field; this is distinct from schema validation's declared required/nullability checks. | `data/quality.py`; `tests/data/test_quality.py::test_quality_counts_absent_null_and_blank_values_as_missing` | Domain / READY TO SPECIFY | Whether quality analysis belongs in the service is unresolved; do not combine its semantics with schema validation implicitly. |
| TC-23 | Pass synthetic exact duplicate records with differing key insertion order and one non-identical record to `analyze_quality`. | Duplicate groups represent exact whole-record value equality independent of mapping key order; they are not entity identity or scientific duplicate detection. | `data/quality.py`; `tests/data/test_quality.py::test_quality_detects_exact_duplicates_independent_of_key_order` | Domain / READY TO SPECIFY | No identity semantics are provided by this operation; inclusion in API requires a separate decision. |
| TC-24 | Pass synthetic finite numbers, NaN, infinities, booleans, and numeric-looking text to `analyze_quality`. | Numeric summaries include finite integers/floats, exclude booleans and non-finite values, and do not parse numeric strings. These descriptive statistics are not scientific validation. | `data/quality.py`; `tests/data/test_quality.py::test_quality_calculates_finite_numeric_statistics_and_excludes_booleans` | Domain / READY TO SPECIFY | Quality output is outside proposed initial service scope; any inclusion needs explicit contract and interpretation boundaries. |

## B. Decision-dependent conceptual application/service cases

These are not executable API tests yet. They can guide later test design, but the assertion wording and selected service boundary must follow approved decisions.

| ID | Objective; preconditions and synthetic input | Expected behavior | Evidence | Layer / status | Dependency or unresolved decision |
|---|---|---|---|---|---|
| TC-25 | Given an approved service adapter and synthetic valid/invalid input, verify it invokes exactly one selected ARC-08 validator and maps its result without changing counts or findings. | Conceptually preserve the selected engine report's validation meaning; exact mapping is not specified now. | `docs/ARC10_CONTRACT_NEUTRAL_SERVICE_DESIGN.md`; `docs/ARC10_SERVICE_BOUNDARY_TEST_STRATEGY.md` | Application/service / PROPOSED | Validator selection, implementation target, truthful provenance path, and service adapter are not approved. |
| TC-26 | Submit synthetic empty records through a future service boundary. | No expected API result is fixed. Domain behavior for the schema validator is known (TC-17), but empty-service policy may reject or report empty input. | `docs/ARC10_PROJECT_DECISION_REQUEST.md` REQ-ARC10-07 | Application/service / PROPOSED | Project decision on empty input and whether empty success could mislead callers. |
| TC-27 | Submit synthetic invalid records at known positions and check service response row references. | No public index base is fixed. If schema-based validation is selected, preserve zero-based indices; if legacy validator is selected, its one-based convention must be handled explicitly. | `docs/ARC10_CONTRACT_NEUTRAL_SERVICE_DESIGN.md`; ARC-08 `data/schemas.py` | Application/service / PROPOSED | Validator choice and public row-reference convention. |
| TC-28 | Use synthetic records that look scientifically meaningful but satisfy only structural fields; inspect service result wording. | Proposed claim boundary: report structural conformance only and do not imply scientific validity, eligibility, source authenticity, or NASA authorization. Exact response representation is not set. | `docs/ARC10_CONTRACT_NEUTRAL_SERVICE_DESIGN.md`; `docs/ARC10_SERVICE_BOUNDARY_TEST_STRATEGY.md` | Application/service / PROPOSED | Approved use case and contract language; scientific meaning is outside the structural validator. |

## C. Blocked API-level cases

These cases have no safe executable assertions until the named decisions and evidence exist. Do not invent schema IDs/content, numeric limits, DTOs, HTTP status codes, security behavior, or implementation target.

| ID | Objective; preconditions and synthetic input | Expected behavior | Evidence | Layer / status | Dependency or unresolved decision |
|---|---|---|---|---|---|
| TC-29 | Resolve a schema identifier/version from the future approved catalog using synthetic requests for supported and unsupported identifiers. | No schema IDs, catalog contents, fallback behavior, or response expectation is specified. | `docs/ARC10_PROJECT_DECISION_REQUEST.md` REQ-ARC10-03; `docs/ARC10_CONTRACT_NEUTRAL_SERVICE_DESIGN.md` | Blocked / BLOCKED | Schema catalog owner, approved schema definitions and unknown-version policy. |
| TC-30 | Assert request/response DTO fields, required/optional/null semantics, error envelope, and HTTP status for synthetic valid and invalid requests. | No final DTO, HTTP method/status, error envelope, or field mapping is approved. | `docs/ARC10_PROJECT_DECISION_REQUEST.md` REQ-ARC10-07; planning reports are proposals | Blocked / BLOCKED | Contract owner and approved versioned wire contract. |
| TC-31 | Exercise synthetic requests below/at/above approved byte, record-count, nesting, time, or concurrency boundaries. | No numeric resource limits or workload evidence exists; no boundary values may be invented. | `docs/ARC10_PROJECT_DECISION_REQUEST.md` REQ-ARC10-06; `docs/ARC10_SERVICE_BOUNDARY_TEST_STRATEGY.md` | Blocked / BLOCKED | Runtime/platform/workload authority must establish limits and overflow behavior. |
| TC-32 | Exercise synthetic requests with and without credentials/permissions and inspect authorization outcomes. | No authentication, authorization, CORS, or deployment policy is established; expected allow/deny results cannot be specified. | `docs/ARC10_PROJECT_DECISION_REQUEST.md` REQ-ARC10-06 | Blocked / BLOCKED | Relevant security/privacy/platform decision authority and approved policy. |
| TC-33 | Run an HTTP integration test against the chosen app/runtime with a synthetic request, without external services. | No framework, runtime/server, repository target, route, method, or deployment model is selected; there is no approved app endpoint to exercise. | `docs/ARC10_PROJECT_DECISION_REQUEST.md` REQ-ARC10-01, REQ-ARC10-05, REQ-ARC10-07; `docs/ARC10_CONTRACT_NEUTRAL_SERVICE_DESIGN.md` | Blocked / BLOCKED | Implementation target and framework/runtime decision, followed by approved API contract and authorized implementation. |
| TC-34 | Verify caller-declared provenance appears in a synthetic API result without being upgraded to authenticated source evidence. | Domain provenance is metadata, not authentication. Public representation and disclosure rules are not defined. | ARC-08 `data/provenance.py`; `docs/ARC10_CONTRACT_NEUTRAL_SERVICE_DESIGN.md`; `docs/ARC10_PROJECT_DECISION_REQUEST.md` REQ-ARC10-02 | Blocked / BLOCKED | Decision on whether provenance is required, its caller representation, privacy/disclosure rules, and approved DTO mapping. |

## Decision boundary summary

- **Decision-independent:** TC-01–TC-24 are specifiable as synthetic ARC-08 domain tests. They verify existing Python contracts only. TC-22–TC-24 concern `analyze_quality` and are deliberately outside the proposed first service slice unless later approved.
- **Decision-dependent:** TC-25–TC-28 are conceptual service tests, not executable acceptance criteria. Their wording must be finalized after validator/provenance, empty-input, row-index, use-case, and claim-boundary decisions.
- **Blocked:** TC-29–TC-34 require schema ownership/content, final DTO and error/status contract, resource limits, security policy, implementation target/framework, and provenance representation decisions.
- A passing ARC-08 domain test would establish only that local software behaves as tested. It would not approve ARC-10 API semantics or demonstrate scientific validity, NASA access, source authenticity, or production readiness.
