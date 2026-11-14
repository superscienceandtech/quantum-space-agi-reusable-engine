# ARC-10 Proposed Request and Response DTO Specification v0.1

**Status:** PROPOSED DTO SPECIFICATION — FINAL CONTRACT APPROVAL PENDING
**API contract drafting:** APPROVED
**Final API contract:** PENDING
**Production implementation:** BLOCKED

This document is a documentation-only DTO proposal. It is not executable DTO or JSON Schema implementation, final contract approval, a canonical governance record, or production authorization. The first operation is `POST /api/v1/dataset-validations`. No implementation or test is created by this specification.

## 1. Purpose

Describe proposed transport shapes for mechanical structural validation of caller-supplied records against one server-selected schema. The conceptual request supports schema selection, record submission, and caller-declared provenance; the conceptual response reports structural findings and explicit request errors.

The API does not establish scientific validity, scientific eligibility, NASA authenticity, source authenticity, data-rights authorization, or domain-specific scientific correctness.

## 2. Verified Existing Domain Structure

The following facts were checked against the separate ARC-08 source and tests. They describe Python-domain objects, not approved JSON fields.

| Domain type | Verified structure/behavior | Evidence |
|---|---|---|
| `Dataset` | Frozen dataclass with required `provenance: Provenance`, `records: Sequence[Record]`, and optional `metadata` mapping (empty by default). Construction copies each top-level record mapping and metadata mapping and exposes those mappings read-only. Nested lists/dictionaries are not deep-copied or frozen and may remain shared/mutable. Records are checked as mappings with string keys. | `src/quantum_space_agi/data/models.py`; `tests/data/test_models.py` |
| `Provenance` | Frozen dataclass fields: required `dataset_id`, `source: DataSource`, timezone-aware `retrieved_at: datetime`, and `data_format: DataFormat`; optional `dataset_version`, `transformations` (tuple, default empty), and `metadata` mapping (empty by default). It validates structure, not truth/authenticity. | `src/quantum_space_agi/data/provenance.py`; `tests/data/test_provenance.py` |
| `DataSource` | Frozen dataclass with required non-empty `identifier`, optional `description`, `url`, `version`, and `metadata` mapping. Metadata is copied at the top level and exposed read-only; it is not authentication evidence. | `src/quantum_space_agi/data/sources.py`; `tests/data/test_sources.py` |
| `DataFormat` | Enum currently has `JSON = "json"` and `CSV = "csv"`. | `src/quantum_space_agi/data/provenance.py`; `tests/data/test_provenance.py` |
| `DataSchema` | Frozen dataclass with `identifier`, `version`, and `fields` tuple of `FieldSchema`. Identifier/version must be non-empty; field names must be unique. | `src/quantum_space_agi/data/schemas.py`; `tests/data/test_schemas.py` |
| `FieldSchema` | Frozen dataclass with `name`, `value_type`, `required=True`, and `allow_none=False`. The name must be non-empty, `value_type` a Python type, and flags booleans. | `src/quantum_space_agi/data/schemas.py`; `tests/data/test_schemas.py` |
| `SchemaValidationReport` | Frozen report fields: `schema_id`, `schema_version`, `record_count`, `valid_count`, `invalid_records`. `is_valid` is a derived property returning whether `invalid_records` is empty; it is not a stored dataclass field. | `src/quantum_space_agi/data/schemas.py`; `tests/data/test_schemas.py` |
| `InvalidRecord` | Frozen object with `record_index` and tuple of `issues`. The schema-based validator enumerates input records from zero. | `src/quantum_space_agi/data/schemas.py`; `tests/data/test_schemas.py` |
| `ValidationIssue` | Frozen object with `field`, `code`, and `message`. The current validator emits `missing`, `null`, and `type` codes for the corresponding structural findings. | `src/quantum_space_agi/data/schemas.py`; `tests/data/test_schemas.py` |
| `validate_dataset` | `validate_dataset(dataset: Dataset, schema: DataSchema) -> SchemaValidationReport` checks declared field presence, nullability, and exact Python type (`type(value) is expected_type`). It reports findings, does not coerce or drop rows, and uses zero-based record indices. An empty dataset currently yields zero counts, no invalid rows, and `is_valid=True`. | `src/quantum_space_agi/data/schemas.py`; `tests/data/test_schemas.py` |

The domain `Dataset` requires `Provenance`; that requirement does not establish that an API must accept a particular provenance DTO. The ARC-10 provenance decision remains in-principle and its wire representation/requiredness remain pending. ARC-03 models are protected and are not modified.

## 3. Domain-to-API Mapping Principle

The proposed separation is:

```text
HTTP JSON request
    -> request DTO
    -> application/service boundary
    -> domain Dataset + selected DataSchema + validate_dataset
    -> SchemaValidationReport
    -> response DTO
    -> HTTP JSON response
```

This is a conceptual architectural mapping only. Transport DTOs must not automatically expose internal domain objects directly. No adapter or mapping is implemented or approved by this document.

## 4. Request DTO Overview

The conceptual request field names below follow the authorized contract draft. Wire-level types and constraints are proposals unless explicitly marked as verified domain semantics.

| JSON field | Conceptual type | Required status | Meaning | Validation/mapping | Status |
|---|---|---|---|---|---|
| `schema_id` | String identifier | Included as required in the draft request shape; final DTO constraints pending | Selects a server-supported structural schema; does not contain a schema definition. | Resolve only against the server-controlled static allowlist. Unknown IDs are rejected; no caller-defined schema or silent fallback. No exact syntax or actual ID is established. | PROPOSED; allowlist behavior authorized with conditions |
| `schema_version` | String version identifier | Included as required in the draft request shape; final DTO constraints pending | Selects a version of `schema_id`, distinct from API path version. | Resolve exact ID/version pair from allowlist; unknown versions rejected. Released schema versions immutable. No value is approved. | PROPOSED; version immutability authorized with conditions |
| `records` | Collection/array of record objects | Required in the draft request shape | Records to validate. Each is conceptually a mapping from field names to values. | Map to domain records without coercion or silent row dropping. API rejects an empty collection with HTTP 422. Wire type mapping and constraints await DTO review. | PROPOSED; empty behavior authorized for contract drafting |
| `provenance` | Object containing caller-declared provenance concepts | Included in the conceptual request; exact requiredness and null/omission behavior pending | Caller-declared dataset/source identity, retrieval timestamp, and data format. | If represented, label explicitly as unverified caller-supplied information. Do not map receipt time to `retrieved_at`. Exact mapping to domain `Provenance` is not implemented. | PROPOSED / PENDING; policy approved in principle only |

Top-level field inclusion in this conceptual shape is not a final DTO requiredness decision for provenance. The final request field constraints and malformed-request details remain subject to contract review.

## 5. `schema_id`

- Proposed API field: `schema_id`.
- It identifies a server-supported schema selected by the caller; it never carries the schema definition.
- It resolves against a server-side static, read-only allowlist after the relevant schema is reviewed and published.
- Unknown IDs are explicitly rejected; arbitrary caller-defined schemas are unsupported initially.
- No actual ID or exact string syntax/format has been approved. Those details remain pending.

## 6. `schema_version`

- Proposed API field: `schema_version`.
- It identifies the requested version of the selected schema and is distinct from `/api/v1/`.
- Released schema versions are immutable under the approved-with-conditions catalog direction; an updated schema would require a new reviewed version.
- Unknown versions are explicitly rejected.
- No concrete version value, syntax, or compatibility policy is approved.

## 7. `records`

`records` is conceptually an array of record objects/mappings. For each record, the selected schema defines field names, exact expected Python types, requiredness, and nullability. Domain behavior is limited to those declarations:

- Missing required field → validation finding.
- Missing optional field → allowed according to schema.
- Explicit null → allowed only if schema permits it.
- Exact Python type mismatch → validation finding; no implicit coercion.
- Findings are retained in the report; no silent row dropping.
- Invalid record references use zero-based positions for the schema-based validator.

The HTTP JSON to Python mapping for exact types, unknown-field behavior, and resource constraints are pending. No numeric limits or extra normalization are proposed here.

Empty records at the API boundary → HTTP 422, as authorized for contract drafting. This does not change the ARC-08 domain behavior described in Section 16.

## 8. Proposed Provenance DTO

The conceptual provenance representation must account for:

- Caller-declared dataset identity (domain analogue: `Provenance.dataset_id`).
- Caller-declared source identity (domain analogue: `Provenance.source`, whose domain object has `identifier` and optional descriptive metadata).
- Caller-declared `retrieved_at` (domain type: timezone-aware `datetime`).
- Caller-declared data format (domain type: `DataFormat`, currently JSON or CSV).
- Server-observed request receipt time, which is not a caller declaration and is not part of ARC-08 `Provenance`.

These names are semantic references to domain fields, not a finalized nested JSON property list. A possible conceptual decomposition is shown below; labels in angle brackets are placeholders, not final field names or values:

```text
provenance (caller-declared; trust label required)
  dataset identity: <proposed wire field; pending>
  source identity: <proposed wire field/object; pending>
  retrieved_at: <proposed wire field and timestamp encoding; pending>
  data format: <proposed wire field and encoding; pending>

server-observed request receipt time:
  <separate response/metadata concept; exact field and encoding pending>
```

### Provenance constraints

- Caller declarations are labeled **UNVERIFIED CALLER-SUPPLIED INFORMATION**.
- Server receipt time is an API observation, conceptually **OBSERVED BY API**; these words describe trust semantics, not an approved enum.
- Server receipt time MUST NOT replace `retrieved_at` or be represented as dataset retrieval time.
- Caller-supplied source metadata is not authenticated source evidence.
- Provenance fields do not establish authentication or authorization.
- No authentication mechanism is defined.
- Do not modify ARC-03 data models.

The proposed request field `provenance` and the receipt-time concept do not settle whether caller provenance is required or where a server observation belongs in a final DTO. Exact JSON names, trust-status field (if any), timestamp format, source representation, and `DataFormat` encoding remain pending. No formal trust enum is introduced here.

## 9. Provenance Trust Semantics

The conceptual trust distinction is:

- Caller-declared provenance: **UNVERIFIED**.
- Request receipt time: **OBSERVED BY API**.

These are explanatory labels only. This specification does not define a status enum or authentication claim. If a future DTO adds an explicit status property, that would be a proposal requiring final contract review; it must not be inferred from the presence of provenance fields.

## 10. Successful Response DTO

The proposed successful response maps from `SchemaValidationReport` without changing its semantics.

| JSON field | Conceptual type | Meaning | Domain source | Status |
|---|---|---|---|---|
| `schema_id` | String | Schema identifier used for completed validation. | `SchemaValidationReport.schema_id` | PROPOSED wire mapping; domain field VERIFIED |
| `schema_version` | String | Schema version used for completed validation. | `SchemaValidationReport.schema_version` | PROPOSED wire mapping; domain field VERIFIED |
| `record_count` | Integer | Number of input records processed by domain validator. | `SchemaValidationReport.record_count` | PROPOSED wire mapping; domain field VERIFIED |
| `valid_count` | Integer | Number of records without schema findings. | `SchemaValidationReport.valid_count` | PROPOSED wire mapping; domain field VERIFIED |
| `invalid_records` | Array | Invalid record references and their validation issues. | `SchemaValidationReport.invalid_records` | PROPOSED wire mapping; domain field VERIFIED |
| `is_valid` | Boolean | Derived as absence of invalid records; structural conformance only. | `SchemaValidationReport.is_valid` property | PROPOSED wire mapping; derived domain behavior VERIFIED |

No additional success fields are fixed. A server receipt timestamp may be considered separately as noted in Section 8; its response inclusion, name, and encoding are pending. A successful validation result must not imply scientific validity.

## 11. Invalid Record DTO

Proposed conceptual invalid-record object:

| Field | Conceptual type | Semantics | Status |
|---|---|---|---|
| `record_index` | Integer | Zero-based index of the submitted record, preserved from schema-based ARC-08 `InvalidRecord.record_index`. | Domain behavior VERIFIED; wire mapping PROPOSED |
| `issues` | Array of issue objects | All structural issues reported for that record. | Domain field VERIFIED; wire mapping PROPOSED |

Do not convert these indexes to one-based values. The legacy record-oriented validator has different indexing semantics and is not interchangeable without an explicit contract decision.

## 12. Validation Issue DTO

Proposed issue object maps the domain issue fields:

| JSON field | Conceptual type | Meaning | Source/status |
|---|---|---|---|
| `field` | String | Schema field associated with the issue. | `ValidationIssue.field`; domain field VERIFIED, wire mapping PROPOSED |
| `code` | String | Structural finding code. Current domain validator emits `missing`, `null`, and `type`. | `ValidationIssue.code`; current codes VERIFIED, exhaustive public registry PENDING |
| `message` | String | Domain-generated explanatory message. | `ValidationIssue.message`; domain field VERIFIED, wire mapping PROPOSED |

No scientific severity, confidence, recommendation, or classification field is added. The final public code registry and message stability/compatibility policy remain pending.

## 13. Error DTO

> **PROPOSED — PENDING FINAL CONTRACT APPROVAL**

A minimal conceptual error representation may contain:

| Conceptual field | Status |
|---|---|
| Error code | PROPOSED; exact code/name/value type pending; no numeric application codes assigned |
| Message | PROPOSED; exact property name, content, and redaction rules pending |
| Details | PROPOSED; optionality, shape, and safe diagnostic content pending |

No final error body, detailed taxonomy, or numeric error code is established by this DTO proposal.

## 14. HTTP Status to DTO Mapping

| HTTP status | Authorized contract-drafting behavior | DTO/result distinction |
|---|---|---|
| 400 | Malformed request syntax/structure. | Request error; exact error DTO remains proposed/pending. Ordinary record findings are not malformed requests. |
| 422 | Empty `records`. | API boundary rejects the empty collection; exact error DTO remains proposed/pending. |
| 200 | Validation operation successfully processed, including records with structural findings. | Return success report DTO; `is_valid=false` when findings exist and `true` when none exist. HTTP 200 does not mean scientific validity. |
| Unsupported schema | Explicit error, no fallback. | Exact HTTP status and error DTO remain pending final contract approval. |

## 15. Domain Validation to Response Mapping

Conceptual mapping:

```text
SchemaValidationReport.schema_id        -> response.schema_id
SchemaValidationReport.schema_version   -> response.schema_version
SchemaValidationReport.record_count     -> response.record_count
SchemaValidationReport.valid_count      -> response.valid_count
SchemaValidationReport.invalid_records   -> response.invalid_records
SchemaValidationReport.is_valid          -> response.is_valid (derived property)

InvalidRecord.record_index               -> invalid_records[].record_index (zero-based)
InvalidRecord.issues                     -> invalid_records[].issues
ValidationIssue.field                    -> issues[].field
ValidationIssue.code                     -> issues[].code
ValidationIssue.message                  -> issues[].message
```

The mapping is a proposal grounded in the verified domain report. It must preserve counts, all findings, and zero-based positions; it is not implemented.

## 16. Empty Input Semantics

The two layers intentionally differ:

- **ARC-08 domain behavior:** an empty `Dataset` can be processed. The schema validator returns `record_count = 0`, `valid_count = 0`, no invalid records, and derived `is_valid = true`.
- **ARC-10 API behavior:** an empty `records` request returns HTTP 422, as explicitly authorized for contract drafting.

The API rule does not alter the domain validator and does not mean that an empty domain report proves useful data was validated.

## 17. Null and Optional Field Semantics

For the verified schema-based domain validator:

- Missing `required=True` field creates a `missing` issue.
- Missing `required=False` field creates no issue.
- Present `None` with `allow_none=False` creates a `null` issue.
- Present `None` with `allow_none=True` passes that nullability check.

No default value or coercion is applied. How JSON `null`, omitted properties, and unknown properties map into the DTO/domain object remains pending final transport specification.

## 18. Type Semantics

The domain validator uses exact Python type equality (`type(value) is field.value_type`), so it does not treat `bool` as `int` and does not implicitly convert numeric-looking strings. No coercion is performed.

JSON transport parsing can affect the Python values presented to the validator. The precise JSON-to-Python type mapping and any handling for values outside JSON's interoperable data model remain DTO/implementation concerns; this draft does not invent a conversion policy.

## 19. Provenance to Domain Mapping

Conceptually, caller declarations could map to required `Dataset.provenance` / `Provenance` fields, with caller source identity represented by a `DataSource`. This mapping is **not implemented** and is not yet settled. In particular, the API must not fabricate or authenticate values to satisfy the domain constructor.

Pending questions include:

- Exact wire property names.
- How source identity and optional source metadata are represented.
- `DataFormat` wire representation (domain enum values are `json` and `csv`; wire mapping is not approved).
- Timestamp serialization/timezone format for caller `retrieved_at`.
- How caller declarations are visibly marked unverified.
- Whether and where server-observed request receipt time is represented, with separate semantics and encoding.

ARC-03 models remain protected from modification.

## 20. Schema Catalog Mapping

The request selects using `schema_id` plus `schema_version`. The service resolves that pair against a server-side static, read-only allowlist. The request DTO does not carry a `DataSchema` definition. Unknown pairs are rejected explicitly without fallback; caller-defined schemas are unsupported in the initial release. Actual schema contents, identifiers, owner, and review assignments remain unresolved. No catalog is claimed to exist.

## 21. Conceptual JSON Examples (Not Executable Requests)

All examples are synthetic teaching shapes. Placeholder schema strings are not real or approved IDs/versions. `example_field` names below are illustrative only and do not imply an approved schema. Provenance member names and receipt-time representation remain unresolved; the placeholder object below does not define approved members.

### A. Conceptual structurally valid request

Assuming only for illustration that the placeholder schema accepts this toy record:

```json
{
  "schema_id": "<approved-schema-id>",
  "schema_version": "<approved-schema-version>",
  "records": [{"example_field": "synthetic value"}],
  "provenance": {"<pending-member-name>": "<unverified caller-supplied value>"}
}
```

This is not executable: neither schema placeholder nor provenance representation is approved.

### B. Conceptual request with structural findings

Assuming only for illustration that the placeholder schema requires `required_example` and the toy record omits it:

```json
{
  "schema_id": "<approved-schema-id>",
  "schema_version": "<approved-schema-version>",
  "records": [{"example_field": "synthetic value"}],
  "provenance": {"<pending-member-name>": "<unverified caller-supplied value>"}
}
```

Conceptual response finding only; exact JSON DTO remains proposed:

```json
{
  "schema_id": "<approved-schema-id>",
  "schema_version": "<approved-schema-version>",
  "record_count": 1,
  "valid_count": 0,
  "invalid_records": [
    {
      "record_index": 0,
      "issues": [
        {"field": "required_example", "code": "missing", "message": "<domain message>"}
      ]
    }
  ],
  "is_valid": false
}
```

The example uses a current domain code and zero-based index, but the schema, field, and serialized message are illustrative, not approved or executable.

### C. Conceptual malformed request

Illustration of a missing top-level field; exact parser/DTO error details remain pending:

```json
{
  "schema_id": "<approved-schema-id>",
  "schema_version": "<approved-schema-version>",
  "records": [{"example_field": "synthetic value"}]
}
```

Draft status behavior: malformed request → HTTP 400. No final error body is shown.

### D. Conceptual empty-record request

```json
{
  "schema_id": "<approved-schema-id>",
  "schema_version": "<approved-schema-version>",
  "records": [],
  "provenance": {"<pending-member-name>": "<unverified caller-supplied value>"}
}
```

Draft status behavior: empty `records` → HTTP 422. This is not an executable request because schema and provenance values remain placeholders.

### E. Conceptual unsupported-schema request

```json
{
  "schema_id": "<unsupported-schema-id>",
  "schema_version": "<unsupported-version>",
  "records": [{"example_field": "synthetic value"}],
  "provenance": {"<pending-member-name>": "<unverified caller-supplied value>"}
}
```

Draft behavior: explicit error and no fallback. Exact HTTP status and error body remain pending. Placeholder values are not real catalog entries.

## 22. DTO Validation Rules (Draft Summary)

- Conceptual top-level request contains `schema_id`, `schema_version`, `records`, and `provenance`; final wire requiredness, especially for provenance, remains pending.
- `records` is conceptually a collection of objects/mappings.
- `schema_id` and `schema_version` select only a server-supported schema pair.
- Empty `records` is rejected by the API boundary with HTTP 422.
- Caller provenance is unverified and must not be treated as authentication.
- No arbitrary schema definition is accepted in the initial direction.
- Structural findings are reported; values are not coerced and records are not silently dropped.
- No scientific validation claim is made.
- No unapproved numeric constraints are introduced.

## 23. Open DTO Decisions

- Final wire field names and required/optional/null semantics.
- Exact provenance DTO, trust-status representation, and caller-versus-server field placement.
- Timestamp wire format and `DataFormat` wire representation.
- Exact error envelope and safe diagnostic policy.
- Unsupported-schema HTTP status and public error code.
- Numeric resource limits and timeout/retry behavior.
- Authentication, authorization, and CORS.
- Privacy, retention, and logging.
- Target repository, owner, branch, and integration boundary.
- Final contract approval authority/process.
- Canonical contract location and canonical governance register.
- External governance approval and D-04/D-05 discrepancy.

## 24. Approval Status

| Item | Status | Boundary |
|---|---|---|
| DTO drafting | **APPROVED AS REQUIRED DELIVERABLE** | Documentation preparation only. |
| DTO specification | **PROPOSED** | This conceptual v0.1 specification. |
| Final DTO contract | **PENDING FINAL API CONTRACT APPROVAL** | No final wire DTO approved. |
| Production DTO implementation | **BLOCKED** | No implementation authorization or confirmed target. |
| Final API contract | **PENDING** | Final approval authority/location unresolved. |
| Production implementation | **BLOCKED** | Not authorized. |

This document is not canonical and does not grant production authorization.

## 25. Decision Traceability

| Request ID | DTO treatment |
|---|---|
| REQ-ARC10-02 — Provenance | Sections 8–9 and 19 preserve unverified caller declarations and separate request receipt time. |
| REQ-ARC10-03 — Schema catalog | Sections 5–6 and 20 use server-side schema selection; no actual ID/content is invented. |
| REQ-ARC10-04 — Contract ownership/location | Section 1 records drafting owner condition and unresolved approval authority/canonical location. |
| REQ-ARC10-05 — Framework/architecture | Section 1 records provisional internal direction with conditions. |
| REQ-ARC10-07 — API behavior | Sections 7, 10–16, and 21–22 reflect authorized drafting behavior without finalizing unresolved errors. |

The contract reference is `docs/ARC10_API_CONTRACT_V0.1.md`; the ADR reference is `docs/ARC10_ARCHITECTURE_DECISION_RECORD_V0.1.md`. Request-local REQ identifiers are not canonical D-01–D-16 assignments.

## 26. Next Step

**Next authorized deliverable:** Provenance Representation Proposal.

It remains documentation-only. Do not implement DTOs, API routes, JSON Schema files, dependencies, deployment/configuration, or changes to ARC-03/ARC-08. Final contract approval, target confirmation, security/operations, resource limits, and production implementation authorization remain pending or blocked.
