# ARC-10 Dataset Structural Validation API — Contract v0.1

> **API CONTRACT DRAFTING AUTHORIZED — FINAL CONTRACT APPROVAL PENDING**

This is a documentation-only contract draft. It is not the final API contract, a canonical governance record, production implementation authorization, production deployment authorization, or external governance approval. The first operation and behavior below are recorded for contract drafting under the Project Owner decisions dated 13 November 2026. Unresolved details remain explicitly marked pending.

## 1. Contract Identity

| Field | Value |
|---|---|
| Contract name | ARC-10 Dataset Structural Validation API |
| Version | v0.1 |
| Status | **DRAFT — FINAL APPROVAL PENDING** |
| ARC | ARC-10 API Integration |
| Drafting/technical coordination owner | Rafi, subject to the written-acknowledgement condition recorded in the decision reconciliation |
| Final contract approval authority | **NOT YET RESOLVED** |
| Canonical contract location | **NOT YET DESIGNATED** |
| Architecture direction | Modular Monolith — approved with conditions for internal direction |
| Framework/runtime direction | FastAPI + Uvicorn + Python — approved with conditions for internal direction |

These are internal directions only. They do not establish production architecture approval, a target repository, or deployment authorization. Do not change D-01–D-16 or the D-04/D-05 mapping.

## 2. Purpose and Scope

This draft describes the first proposed operation for mechanically validating caller-supplied records against one selected schema from a server-controlled, static, read-only schema allowlist.

The operation checks only the selected schema's structural rules. It does **not** establish:

- Scientific validity or scientific eligibility.
- Scientific or domain-specific correctness or physical plausibility.
- NASA authenticity or source authenticity.
- Data-rights authorization, permission to access, retain, or redistribute data.

The endpoint must not be described as scientific validation. A structurally conforming record is only conforming to the selected mechanical schema.

## 3. First Use Case

**Operation:** `POST /api/v1/dataset-validations`
**Purpose:** Mechanically validate supplied records against a selected supported schema.

The intended semantics are aligned with verified ARC-08 schema-based validation: field presence, nullability, exact Python type expectations after input mapping, invalid-record identification, and issue reporting. No additional scientific validation rule, range constraint, imputation, coercion, normalization, or deduplication is introduced by this contract draft.

ARC-08's validator is a separate reusable domain capability; it is not an API and is not automatically the ARC-10 implementation target. The final validator/adapter choice remains subject to the approved target and contract details.

## 4. HTTP Method, Path, and Versioning

| Item | Draft direction | Status |
|---|---|---|
| Method | `POST` | Authorized for contract drafting |
| Path | `/api/v1/dataset-validations` | Authorized for contract drafting |
| Major API version | Path contains `/v1/` | Proposed contract convention; not a project-wide versioning policy |
| Contract document version | `v0.1` | Draft version |

Future compatibility guarantees, deprecation rules, and version evolution remain pending review. This proposal does not create an endpoint implementation.

## 5. Request Contract (Conceptual)

The conceptual request includes `schema_id`, `schema_version`, `records`, and `provenance`. The exact wire DTO and field constraints remain pending. In particular, final provenance requiredness and member representation have not been decided.

| Field | Draft purpose | Requiredness/status | Semantic meaning and source | Unresolved details |
|---|---|---|---|---|
| `schema_id` | Select the structural schema to apply. | Included in the conceptual request; requiredness is part of the draft shape, pending final DTO approval. | Caller selects an identifier from the server's approved static allowlist. | No actual schema ID is approved. Exact syntax and unsupported-schema HTTP status/error code remain pending. |
| `schema_version` | Select the reviewed version for `schema_id`. | Included in the conceptual request; requiredness is part of the draft shape, pending final DTO approval. | Caller selects a specific released version; versions are server-controlled and immutable after release. | No actual version is approved. Exact syntax and compatibility rules remain pending. |
| `records` | Supply the collection to validate. | Included and required in this draft; an empty collection receives HTTP 422 under the supplied decision. | Conceptually a collection of record objects/mappings from field names to values. | Final JSON value/type mapping, unknown-field policy, and any limits remain pending. |
| `provenance` | Carry caller-declared dataset/source context separately from request receipt observations. | Included in this conceptual draft shape; exact top-level requiredness, omission/null behavior, and member fields remain pending because provenance policy is approved only in principle. | Caller declarations are unverified caller-supplied information. No provenance member authenticates the source. | Exact wire-level names, required members, allowed formats, timestamp encoding, and disclosure policy remain pending. |

The request selects a server-side schema. It does not include an arbitrary schema definition. Unknown IDs or versions must produce an explicit error; there is no silent fallback, automatic schema inference, or caller-defined schema execution in the initial release.

No approved sample schema or schema ID/version exists yet, so this draft intentionally does not provide a request example containing fabricated identifiers or definitions.

## 6. Records Semantics

`records` is the collection submitted for structural validation. Each record is conceptually an object/mapping of field names to values; its final transport representation and exact wire-to-Python type mapping are pending DTO review.

For a selected schema, existing ARC-08 schema-based domain behavior is:

- A missing required field produces a validation finding.
- A missing optional field is allowed according to the schema declaration.
- An explicit null is allowed only when the schema permits it.
- A value whose exact Python type differs from the declared type produces a validation finding; the validator does not coerce it.
- Validation findings do not cause records to be silently dropped.
- The domain report uses zero-based invalid-record indices.

These describe the existing domain validator, not a complete wire-format contract. This API draft adds no other normalization or scientific rule.

## 7. Provenance Semantics

The Project Owner decision is **MODIFY — APPROVED IN PRINCIPLE** for caller-declared provenance under strict limits. Any representation must label caller declarations:

> **UNVERIFIED CALLER-SUPPLIED INFORMATION**

Conceptually distinguish:

- Caller-declared dataset identity.
- Caller-declared source identity.
- Caller-declared `retrieved_at`.
- Caller-declared data format.
- Server-observed request receipt time.

Rules:

1. Caller-declared `retrieved_at` remains the caller's declaration.
2. Server request receipt time is an observation made by the service and has different semantics.
3. Server receipt time **MUST NOT** replace `retrieved_at` or be presented as dataset retrieval time.
4. Caller-declared provenance **MUST NOT** be represented as authenticated source evidence.
5. Provenance fields do not establish authentication or authorization.
6. Protected ARC-03 data models must not be modified for this work.

Exact wire-level names and requiredness remain **DRAFT / PENDING**. No authentication mechanism is proposed here.

## 8. Schema Catalog

The approved direction, subject to conditions, is a:

- Static, read-only, server-controlled allowlist.
- Catalog of explicitly reviewed schema IDs and versions.
- Catalog with immutable released versions; changes require a new reviewed version.
- Catalog with documented ownership and review responsibility.
- Catalog that explicitly rejects unknown IDs/versions without fallback.
- Initial release that does not support arbitrary caller-defined schemas.

**No actual schema ID or schema content has been approved. No production catalog is claimed to exist.** Catalog ownership, review assignments, actual IDs, and definitions remain pending.

## 9. Response Contract (Conceptual)

A successful validation operation returns the conceptual fields of the ARC-08 `SchemaValidationReport`:

| Field | Meaning |
|---|---|
| `schema_id` | Identifier of the selected schema. |
| `schema_version` | Version of the selected schema. |
| `record_count` | Number of records processed. |
| `valid_count` | Number of records with no schema findings. |
| `invalid_records` | Collection of records with one or more findings. |
| `is_valid` | Whether the validation report contains no invalid records; structural meaning only. |

Each invalid record preserves a zero-based `record_index` and its `issues`. Each issue preserves `field`, `code`, and `message`, corresponding to the existing domain `ValidationIssue` fields. Current domain issue codes include `missing`, `null`, and `type`; an exhaustive public API code registry is not approved.

Conceptual JSON shape only (illustrative placeholders are not approved schema values):

```json
{
  "schema_id": "<reviewed-schema-id>",
  "schema_version": "<reviewed-version>",
  "record_count": 0,
  "valid_count": 0,
  "invalid_records": [],
  "is_valid": true
}
```

The placeholder does not designate a supported schema. Exact DTO typing, serialization, and compatibility are pending. The ARC-08 schema-based validator uses zero-based indexes. A separate legacy record-oriented validator has one-based indexing and a different report; it must not be silently substituted or mixed with the schema-based contract.

## 10. Success HTTP Behavior

The supplied decision authorizes this behavior for contract drafting:

### HTTP 200 — validation operation completed

When the request is structurally processable, the schema is supported, and validation completes, return HTTP 200 with a validation report, including when records have structural findings.

- If findings exist: `is_valid = false`.
- If no findings exist: `is_valid = true`.

HTTP 200 means the service successfully processed the structural validation operation. It does not mean the data is scientifically valid.

## 11. Client Error Behavior

### HTTP 400 — malformed request

Use for malformed request syntax or structure, as currently authorized. Detailed malformed-request categories, field-level diagnostics, and the exact error body remain pending. Do not classify ordinary schema-validation findings as malformed requests.

### HTTP 422 — empty records

The Project Owner explicitly authorized empty `records` requests to receive HTTP 422. This is API-level behavior. The ARC-08 domain validator is unchanged: an empty `Dataset` currently produces zero counts, no invalid rows, and `is_valid = true`. The API boundary's HTTP 422 rule intentionally differs from that domain result.

## 12. Unsupported Schema Behavior

An unknown or unsupported schema ID/version must produce an explicit error. There must be:

- No silent fallback.
- No automatic schema inference.
- No execution of caller-defined schemas.

The exact HTTP status and error code for this case were not specified by the supplied decision and remain pending final contract review. This draft assigns no status or numeric application error code.

## 13. Validation Findings vs Request Errors

**Request/contract errors** prevent normal processing of the requested operation. The supplied drafting direction includes malformed request (HTTP 400), empty records (HTTP 422), and an explicit error for an unsupported schema (status pending).

**Validation findings** mean the request is processable and its schema is supported, but one or more records violate declared schema rules. These are returned in the normal validation report with HTTP 200; they are not converted into HTTP 4xx errors merely because a record is invalid.

## 14. Proposed Error Envelope

> **PROPOSED — PENDING FINAL CONTRACT APPROVAL**

A minimal conceptual error body may contain:

```json
{
  "error": {
    "code": "<TBD>",
    "message": "<TBD>",
    "details": "<TBD or omitted>"
  }
}
```

This is a discussion shape only. The `error` wrapper and the `code`, `message`, and `details` members are not final. Their names, requiredness, value types, safe diagnostic content, and relationship to HTTP status remain pending. No numeric application error codes are assigned.

## 15. Synchronous Execution

The initial operation is proposed as synchronous, subject to approved resource limits. No timeout, concurrency, payload-size, record-count, CPU, memory, or response-size values are set here. Those limits and any timeout/retry behavior remain unresolved. No background queue or worker contract is included in v0.1.

## 16. Side Effects and Persistence

Current proposal for the first validation operation:

- No intended persistent side effect.
- No persistence requirement for the first use case.
- No background processing requirement.

These are current scope proposals, not a permanent rejection of persistence or asynchronous processing. Any change requires requirements and review. This draft specifies no storage, retention, or logging behavior.

## 17. Mutation and Data Integrity

The existing schema-based ARC-08 validation does not intentionally coerce values or drop records, and validation is treated as non-mutating. Dataset construction copies top-level record mappings and exposes them read-only, but nested lists/dictionaries can remain shared and mutable. This is not a guarantee of deep immutability.

The API must not promise to mutate caller data. The eventual adapter should preserve submitted values and avoid mutating nested structures. Exact request buffering/copying and transport-level behavior remain implementation details pending a confirmed target; no implementation is authorized by this contract draft.

## 18. Scientific Scope Boundary

This contract covers **MECHANICAL STRUCTURAL VALIDATION ONLY**. It does not establish:

- Scientific correctness or scientific eligibility.
- Physical plausibility.
- NASA authenticity or source authenticity.
- Data-rights compliance or authorization.

A successful structural report must not be described as scientific approval or source verification.

## 19. Versioning and Compatibility

- `/api/v1/` represents the proposed major API version.
- Schema version is separately identified by `schema_id` and `schema_version` in the conceptual contract.
- Released schema versions are immutable under the approved-with-conditions catalog direction.
- Final API backward-compatibility policy is pending review.
- Final compatibility guarantees are not approved.

The path convention does not itself establish a project-wide versioning policy.

## 20. Security and Operations

Security/operational decisions are **DEFERRED**. This draft does not invent or select:

- Authentication or authorization.
- CORS.
- Rate or resource limits.
- Retention or logging policy.
- Privacy policy.
- Secrets management.

The appropriate security, privacy, platform, and release authorities must be identified and consulted. There is no public production exposure. Synthetic data only may be used for authorized non-production preparation.

## 21. Open Contract Items

The following remain unresolved and must not be filled by assumption:

- Target repository, target owner, target branch, and integration boundary.
- Final contract approval authority.
- Canonical contract location.
- Actual schema IDs and contents.
- Schema catalog ownership and review authority.
- Exact provenance wire representation, member names, and requiredness.
- Exact error envelope and unsupported-schema HTTP status.
- Numeric resource limits.
- Timeout and retry policy.
- Authentication and authorization.
- CORS.
- Privacy, retention, and logging.
- Deployment requirements.
- External governance approval and authority verification.
- D-04/D-05 discrepancy.

The local decision package and this draft remain non-canonical. Do not alter D-01–D-16 numbering or infer that any open item is approved.

## 22. Contract-Level Acceptance Criteria (Proposed)

These are criteria for later contract and implementation review. They are not implemented tests and have not been executed.

- A supported schema ID/version selects exactly that reviewed server-side schema.
- An unknown ID/version returns an explicit error without fallback; its HTTP status remains pending.
- Required-field absence, optional-field absence, and nullability follow the selected schema.
- Exact type checking follows the selected domain validator's supported type mapping; no coercion occurs.
- Invalid record indices remain zero-based if the schema-based validator is selected.
- Multiple issues for one record and multiple invalid records are preserved.
- Empty `records` at the API boundary returns HTTP 422 even though the ARC-08 domain validator's empty-dataset report is mechanically valid.
- Provenance is labeled unverified caller-supplied information; caller `retrieved_at` remains distinct from server request receipt time.
- No records are silently dropped or values coerced.
- Completed validation with findings returns HTTP 200 and `is_valid=false`; completed validation without findings returns HTTP 200 and `is_valid=true`.
- Malformed request syntax/structure returns HTTP 400.
- Unsupported-schema behavior is explicit and has no automatic inference or fallback.
- Response wording makes no scientific validity, eligibility, authenticity, or data-rights claim.

Final request parsing boundaries, exact mappings, DTOs, error schemas, security/resource checks, and acceptance evidence depend on final contract review and a confirmed implementation target.

## 23. Approval Status

| Item | Status | Boundary |
|---|---|---|
| API contract drafting | **APPROVED** | Drafting authorized within the supplied Project Owner direction. |
| API Contract v0.1 | **DRAFT** | This document only; not canonical or final. |
| Final API Contract | **PENDING** | Final approval authority and review process remain unresolved. |
| Architecture | **APPROVED WITH CONDITIONS — INTERNAL DIRECTION** | Provisional Modular Monolith direction; not production architecture approval. |
| Production implementation | **BLOCKED** | No implementation authorization. |
| Production deployment | **BLOCKED** | No deployment authorization. |
| Target repository | **DEFERRED / NOT CONFIRMED** | Target repository/owner/branch/integration boundary are unresolved. |
| Security/operations | **DEFERRED** | Authorities and requirements remain unresolved. |
| Canonical contract location | **PENDING** | Not designated. |
| Canonical governance register | **PENDING** | Not designated; this draft is not a register. |
| D-04/D-05 | **OPEN** | No mapping or numbering changes made. |

## 24. Decision Traceability

| Request ID | Contract treatment |
|---|---|
| REQ-ARC10-02 — Provenance | Section 7 preserves unverified caller-declared provenance and separates `retrieved_at` from server receipt time; ARC-03 remains protected. |
| REQ-ARC10-03 — Schema catalog | Section 8 records the static, reviewed, immutable-version allowlist direction and the absence of approved schema IDs/content. |
| REQ-ARC10-04 — Contract ownership/location | Section 1 records the coordination-owner condition and unresolved final authority/canonical location; no D-number changes. |
| REQ-ARC10-05 — Architecture/framework/runtime | Sections 1 and 23 reflect conditional internal direction; the updated ADR is `docs/ARC10_ARCHITECTURE_DECISION_RECORD_V0.1.md`. |
| REQ-ARC10-06 — Security/operations | Section 20 records deferred status and avoids inventing security or operational policy. |
| REQ-ARC10-07 — API behavior | Sections 3–4 and 9–15 record the operation and authorized drafting behavior while leaving final envelope/versioning pending. |

Request-local REQ identifiers are not canonical D-01–D-16 register assignments.

## 25. Next Step

**Next authorized deliverable:** Proposed Request and Response DTO Specification.

That work remains documentation/specification only unless a later Project Owner decision explicitly changes implementation authorization. Final contract approval, target confirmation, canonical location, security/operations, resource limits, and production authorization remain pending or blocked as stated above.
