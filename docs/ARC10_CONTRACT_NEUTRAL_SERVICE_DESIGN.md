# ARC-10 Contract-Neutral Service Design

**Status:** Conceptual service-boundary proposal only. This is not an HTTP API, production DTO, approved use case, or implementation authorization.

## 1. Scope

Candidate operation: mechanically validate caller-supplied records against an explicitly identified, trusted structural schema. The candidate is **PROPOSED — PENDING CONTRACT APPROVAL**. It does not assess scientific validity, eligibility, source authenticity, NASA authorization, or mission readiness.

No route, HTTP method, framework, wire format, authentication policy, deployment model, schema registry, or production consumer is selected here.

## 2. Verified engine interfaces

| Interface | Input and output | Error behavior / provenance | Index, mutation, determinism and tests |
|---|---|---|---|
| Schema-based: quantum_space_agi.data.schemas.validate_dataset(dataset: Dataset, schema: DataSchema) -> SchemaValidationReport | Dataset and versioned DataSchema. Report has schema_id, schema_version, record_count, valid_count, invalid_records; is_valid is derived from absence of invalid records. InvalidRecord contains record_index and ValidationIssue(field, code, message). | Dataset construction requires Provenance. DataSchema/FieldSchema validate their own declarations and may raise ValidationError; Dataset rejects invalid provenance/records with ValueError; validator reports record issues rather than raising for missing/null/type mismatches. | Zero-based indexes. Exact Python type check; bool is not int. No coercion, row dropping or record mutation. Deterministic for identical inputs. Tests: tests/data/test_schemas.py and tests/data/test_quality.py. |
| Legacy/record-oriented: quantum_space_agi.data.validator.validate_dataset(...), re-exported as quantum_space_agi.data.validate_records | Accepts DatasetLoadResult, mapping containing records, or record sequence plus a schema Mapping; returns ValidationReport with counts, errors, warnings and validation_timestamp. include_actual_values defaults false. | Does not require Dataset/Provenance. Invalid schema raises SchemaDefinitionError; invalid top-level records container raises TypeError; record-level findings are reported. Detailed schema rules are in data/validator.py. | One-based row indexes. No value coercion or input mutation. Findings are deterministic for same inputs, but the complete report includes current timestamp and is not byte-identical across runs. Public export is tested in tests/data/test_public_api.py; no dedicated legacy-validator suite was found in tests/data. |

Related verified models:

- FieldSchema(name, value_type, required=True, allow_none=False) and DataSchema(identifier, version, fields) are frozen dataclasses. DataSchema stores fields as a tuple and rejects duplicate field names.
- SchemaValidationReport, InvalidRecord, and schema ValidationIssue are frozen dataclasses; nested invalid-record issues are tuples.
- Dataset is frozen, copies top-level record mappings and metadata into read-only mappings, but does not deep-copy/freeze nested lists/dicts.
- Provenance requires dataset_id, DataSource, timezone-aware retrieved_at and DataFormat; dataset_version, transformations and metadata are optional. Its declarations are not authenticated.
- analyze_quality(dataset, validation_report=None) returns DataQualityReport. Missing means absent/None/blank text. Duplicate groups are exact full-record duplicates, independent of key order, not entity identity. Numeric summaries include finite int/float but exclude bool; means are binary64 approximations. It does not mutate source records. Tests: tests/data/test_quality.py.

The ARC-08 package pyproject.toml declares no runtime dependencies and no HTTP framework. These Python APIs do not define HTTP status codes, serialization, auth, transport errors, or request limits.

## 3. Validator comparison and recommendation

| Dimension | Schema-based validator | Legacy/public validator |
|---|---|---|
| Input | Dataset plus DataSchema | DatasetLoadResult / records mapping / sequence plus schema Mapping |
| Schema representation | Frozen DataSchema with explicit identifier, version and FieldSchema tuple | Mapping-based schema with more policy options, including duplicate-detection configuration |
| Provenance | Required indirectly by Dataset | Not required by input form |
| Row index | Zero-based | One-based |
| Report | SchemaValidationReport; typed invalid records and field/code/message issues; no run timestamp | ValidationReport; errors/warnings and detailed issue structure; includes a generated timestamp |
| Actual values | Not part of schema issue structure | Omitted by default; optional include_actual_values can expose them |
| Existing tests | Direct focused coverage in test_schemas.py; quality linkage in test_quality.py | Public export/import coverage; no dedicated validator behavior test module found |
| Service fit | Smaller typed, versioned schema contract; provenance requirement must be handled honestly | Easier record-list boundary without synthetic Dataset provenance, but schema mapping and report are more configurable and need stronger focused tests |

**Recommendation: PROPOSED — PENDING CONTRACT APPROVAL.** Prefer considering the schema-based validator for a bounded first service because its schema identity/version and issue structures are explicit and its behavior has focused tests. This preference is conditional: a service cannot construct Dataset with fabricated provenance. The project must decide whether provenance is required from the caller, whether another input wrapper is approved, or whether the legacy validator better matches the intended operation. Do not silently invent provenance to bridge the API.

The legacy API remains a valid alternative if the contract needs record-list input without Dataset provenance. Its distinct row-index base, schema-mapping policy and timestamp must be explicit, and additional focused tests may be needed. No final choice is made here.

## 4. Proposed service boundary

### 4.1 Input boundary

Conceptual input, not a production DTO:

- **PROPOSED SERVICE CONCEPT:** a collection of record mappings.
- **PROPOSED SERVICE CONCEPT:** a schema identifier and version, resolved only from an approved server-controlled registry or a fixed reviewed schema.
- **UNRESOLVED:** whether provenance is required, caller-supplied, absent, or irrelevant for a purely structural caller-submitted-data operation.
- **VERIFIED ENGINE FIELD:** Dataset.provenance is required if using the schema-based validator; Provenance fields are declarations, not verified source facts.
- **PROPOSED:** reject malformed top-level input and unknown schema IDs/versions; do not coerce, normalize, impute, deduplicate or discard records.
- **UNRESOLVED:** empty collection behavior, unknown-field policy, transport serialization and size thresholds.

Request-byte, record-count, nesting-depth, field-count, time and concurrency limits should be proposed and measured for the chosen runtime. No numeric limits are set by this design.

### 4.2 Processing boundary

**PROPOSED:** Resolve only an approved schema/version and invoke one selected engine validator. The schema-based function returns a structural report; the legacy function returns its distinct report. A service adapter may map the chosen report to a service result after the mapping is approved.

Interpret only the selected schema's mechanical checks. Do not infer scientific meaning from names, units, missingness, value ranges, provenance declarations, or source labels. Do not call this result scientific validation or eligibility. Do not automatically invoke analyze_quality in the first slice.

### 4.3 Conceptual output boundary

No production DTO is defined. These are concepts for discussion; labels indicate evidence status.

| Concept | Evidence status | Meaning/boundary |
|---|---|---|
| schema identifier/version | VERIFIED ENGINE FIELD in DataSchema and SchemaValidationReport; exact service exposure is PROPOSED SERVICE CONCEPT | Identifies the selected mechanical rules, not approval. |
| record/valid/invalid counts | VERIFIED ENGINE FIELD or DERIVED VALUE, depending on chosen report | Counts from the completed validation; must reconcile. |
| validation status | DERIVED VALUE from report validity | Means only structural conformance to chosen rules. |
| field findings | VERIFIED ENGINE FIELD in schema ValidationIssue; legacy shape differs | Preserve issues; exact public names/codes require contract approval. |
| row references | VERIFIED ENGINE FIELD in invalid report; base differs by validator | Must declare zero- or one-based mapping and preserve input correspondence. |
| provenance | VERIFIED ENGINE FIELD in Dataset/Provenance; service output behavior is UNRESOLVED | Preserve only actual supplied/observed data and distinguish declared from observed. |
| validated timestamp | Present in legacy ValidationReport only; otherwise UNRESOLVED | Inclusion, timezone and origin are contract decisions. |
| scientific assessment | PROPOSED SERVICE CONCEPT, e.g. explicit “not assessed” meaning | No engine field provides scientific approval. Wording/token requires contract approval. |
| quality summary | UNRESOLVED; excluded from proposed initial scope | If later included, distinguish exact whole-record duplicates and approximate numeric summaries from scientific/identity metrics. |

Do not expose arbitrary actual values in issues by default. No persistence, caching or raw-input echo is proposed.

## 5. Contract-neutral error taxonomy

These are conceptual categories only. They assign no HTTP status or final error envelope.

| Category | Trigger | Client/input or internal | Recovery concept | Contract approval still needed? |
|---|---|---|---|---|
| Invalid input structure | Input is not the agreed collection/mapping shape or contains malformed record objects. | Client/input | Correct request based on documented structure. | Yes: exact accepted structures and diagnostics. |
| Missing required field | A record omits a required schema field; for the schema validator this is a reported finding, not necessarily an operation exception. | Client/input finding | Correct data or inspect schema; service should return completed report if agreed. | Yes: invalid report versus request failure. |
| Null/type mismatch | Field violates schema nullability or exact type. | Client/input finding | Correct input or use appropriate schema. | Yes: issue mapping and null/missing semantics. |
| Unknown/unsupported schema | Requested ID/version is not available in approved registry. | Client/input or configuration | Choose supported schema; internal registry errors remain internal. | Yes: supported choices and response behavior. |
| Missing provenance | Chosen engine path requires Dataset provenance and none is legitimately available. | Input/contract | Supply truthful supported provenance or choose a different approved boundary. Never fabricate it. | Yes: whether provenance is required. |
| Resource limit exceeded | Input exceeds approved bytes/rows/depth/time/concurrency cap. | Client/input or operational | Reduce request or retry only if contract permits. | Yes: thresholds and retry guidance. |
| Internal processing failure | Unexpected engine/adapter/runtime exception. | Internal | Safe generic diagnostic/correlation process; no raw payload leakage. | Yes: reporting, logging and retry behavior. |
| Unsupported operation | Requested operation is not part of selected service scope. | Client/input | Use supported operation after documentation identifies it. | Yes: operation catalogue and compatibility. |

## 6. Explicit non-goals and blockers

This boundary is not an HTTP API and does not select a framework. Production API implementation remains blocked by project decisions about use case/consumer, target service, contract owner, validator/provenance choice, request and response contract, error semantics, security, data retention, limits, architecture and acceptance. Scientific data operations additionally require authoritative scientific semantics and source-use permissions. None is approved by this design.
