# ARC-10 Service Boundary Test Strategy

**Status:** Proposed test design only. No service code or HTTP server is implemented; these tests have not been run. Expected service behavior below requires approval where marked proposed.

## 1. Test boundary

Test a future framework-neutral application/service function with in-memory inputs and an injected/selected ARC-08 validator. Do not construct HTTP requests, select a web framework, or make network calls. Use synthetic records only. Tests must not imply an approved production payload shape.

The service design recommends considering the schema-based API, but final validator selection is pending. Tests involving its report mechanics can rely on current engine behavior; service input/error mapping and output concepts remain proposals until contract approval.

## 2. Test matrix

| Case | Input concept | Expected result | Evidence/status |
|---|---|---|---|
| Valid dataset | Records satisfy every field in a fixed test DataSchema; construct Dataset only with explicit truthful test provenance if using schema validator. | All rows reported valid, counts reconcile, findings empty. | Engine behavior verified by tests/data/test_schemas.py. Service result mapping is proposed and needs contract approval. |
| Missing required field | One record omits a required schema field. | A completed validation report identifies row and field; no row is removed. | Schema engine behavior verified; service classification and field mapping proposed pending approval. |
| Nullable/non-nullable | Compare absent optional field, explicit null allowed, and explicit null disallowed. | Optional absence/null follows schema declaration; disallowed null is a finding. | Engine behavior verified; public distinction between absent and null must be approved. |
| Wrong Python type | Supply wrong exact type, including bool for integer. | Type issue appears; no coercion. | Engine behavior verified by test_schemas.py; service envelope is proposed. |
| Empty dataset | Empty records with otherwise valid schema/provenance as required. | Schema-based validator currently reports zero records and no invalid rows, so is_valid is true; service must not silently equate this with useful non-empty input. Decide whether to return empty success or reject at boundary. Legacy validator instead reports empty_dataset invalid. | Engine difference verified; expected service policy unresolved and requires approval. |
| Missing provenance | Attempt schema-based validation without Dataset provenance; separately evaluate a record-oriented boundary. | Dataset construction rejects missing/non-Provenance value. A service must not fabricate source/time to satisfy it; it may require truthful provenance or select legacy interface if approved. | Dataset behavior verified in data/models.py; service decision unresolved. |
| Duplicate records, quality excluded | Exact duplicate synthetic rows passed only to validation operation. | Validation does not deduplicate; both rows remain represented. | Schema validator behavior verified. No quality API invoked in proposed initial scope. |
| Duplicate records, quality later included | Dataset with byte/value-identical logical records in different key order passed to analyze_quality. | Exact whole-record duplicate group is reported; not a domain identity duplicate. | Engine behavior verified by tests/data/test_quality.py; inclusion in service requires approval. |
| Non-finite values, quality later included | Finite, NaN, +infinity and -infinity values passed to quality analysis. | Numeric statistics include only finite int/float, excluding bool; schema exact-type validator accepts float NaN/Infinity if field type is float, so scientific or finite checks are not implied. | Engine behavior verified in quality tests/source; exposing this behavior or adding finite validation requires contract/domain decision. |
| Index convention | Invalid rows at first and later positions, through each candidate validator. | Schema API indexes from zero; legacy API indexes from one. Adapter tests assert mapping to original submitted rows and never mix conventions. | Engine convention verified; service convention requires explicit selection/approval. |
| Determinism | Repeat same structural validation with same schema and records. | Finding order/counts and schema report match. Legacy report timestamp may differ; compare stable fields or define timestamp policy rather than asserting byte-identical full result. | Engine behavior inspected; exact service determinism contract is proposed pending approval. |
| No mutation/coercion | Keep caller records and nested values; validate wrong types and nested data. | Input equality remains unchanged; strings/numbers are not converted; no records silently removed. | Engine test_schemas.py covers no drop/mutation; service boundary must add its own adapter regression test. |
| Unknown schema | Request an unregistered schema ID/version concept. | Rejected/identified as unsupported; no fallback schema is silently selected. | Proposed service policy; requires approval of schema registry and error semantics. |
| Invalid schema definition | Use duplicate field names or invalid type declaration in test-only schema. | Schema construction raises ValidationError before validating dataset. | Engine behavior verified by test_schemas.py; mapping to service configuration failure requires approval. |
| Resource boundary | Synthetic input at, below, and above each eventually approved byte/row/depth/time cap. | At/below accepted for validation; above rejected before unbounded processing and without mutation/retention. | Limits and expected values do not exist; entirely proposed and blocked pending platform/workload approval. |
| Error classification | Separate malformed top-level input, schema finding, unsupported schema, provenance failure and injected unexpected internal exception. | Input/service failures are distinguishable from a completed report containing invalid rows; internal errors do not echo raw records. | Proposed service behavior; exact classifications and recovery require contract approval. |
| Provenance disclosure | Supply test provenance metadata or omit it where interface allows. | Preserve only supplied/observed fields, label caller declarations as declarations, and never create source or retrieval time. | Provenance structure verified; service exposure/required fields unresolved. |
| Quality not scientific | A structurally valid synthetic record with arbitrary scientific-looking field names. | Output states only structural result; no eligibility, truth, unit, or NASA authorization is inferred. | Proposed claim boundary; must be an acceptance test if service is approved. |

## 3. Test organization proposal

If implementation is approved, keep layers independently testable:

1. **Engine adapter unit tests:** selected validator call, schema resolution, index mapping, provenance handling, no mutation.
2. **Service behavior tests:** valid/invalid report distinction, empty behavior, unknown schema, resource rejection and conceptual error categories.
3. **Contract tests:** only after a versioned request/response/error contract is approved; assert required/optional/null fields and compatibility.
4. **Security/resource tests:** approved body/record/depth/time limits, raw-value redaction, retention behavior, access checks where applicable.
5. **Regression tests:** verify no NASA/network calls, no fallback schema, no scientific eligibility claims, and no input mutation.

No fixtures are created in this task because ARC-10 has no test-support package and a reusable serialized fixture could be mistaken for an approved API payload. Tests should construct local domain objects inline or under an explicitly marked future test-only fixture directory after the contract is chosen.

## 4. Approval boundary

The tests above are a plan, not test results. Engine tests establish only the documented local Python behavior. They do not approve a product use case, HTTP contract, framework, security policy, data rights, scientific interpretation or deployment.

## 5. Layer clarification addendum (Prompt 12)

This addendum clarifies the proposed test boundaries without changing the existing case wording or identifiers. It records the supplied REQ-ARC10-07 drafting decision; it is not final API Contract approval or implementation authorization.

| Layer | Responsibility and current empty-input status | Evidence boundary |
|---|---|---|
| API / HTTP boundary | Parses the HTTP request and maps malformed requests to HTTP 400 and empty API `records` to HTTP 422, as approved for contract drafting under REQ-ARC10-07. | This is a supplied API drafting decision, not existing ARC-08 behavior and not an implemented route. |
| Application / service boundary | Orchestrates request-independent work and coordinates the selected validator. Its behavior for an empty record collection remains **UNSPECIFIED**. Do not prescribe empty success, rejection, or a domain invocation until that service behavior is explicitly decided. | `ARC10_CONTRACT_NEUTRAL_SERVICE_DESIGN.md` §4.1 identifies empty collection behavior as unresolved. The API status does not settle this layer. |
| ARC-08 domain | The schema-based `validate_dataset(Dataset, DataSchema)` traverses the supplied records and derives `is_valid` from whether `invalid_records` is empty. For an empty `Dataset`, current source behavior is `record_count=0`, `valid_count=0`, `invalid_records=()`, and `is_valid=True`. | Source: separate ARC-08 checkout, `src/quantum_space_agi/data/schemas.py` (`validate_dataset`, `SchemaValidationReport.is_valid`). Existing `tests/data/test_schemas.py` covers schema findings, zero-based indexes, exact types and no row dropping; it does not contain a dedicated empty-Dataset assertion. |

The separate legacy `data.validator.validate_dataset` has different semantics: `tests/test_data_validation.py::test_empty_dataset_is_invalid` verifies an `empty_dataset` finding, and that validator uses one-based issue indexes. Do not merge its behavior or report/index conventions with the schema-based API.

ARC-08 `analyze_quality` is a separate domain operation (`src/quantum_space_agi/data/quality.py`), not an implicit part of schema validation. A schema-validation result must not be described as a quality-analysis result.

### Existing-case layer labels

- **Domain behavior:** “Valid dataset,” required/null/type findings, duplicates excluded from quality, index convention, determinism, and no mutation/coercion describe candidate engine behavior; they do not establish service or HTTP mapping.
- **API behavior:** the malformed-request and empty-`records` HTTP mappings are API-boundary drafting cases only.
- **Application/service behavior:** the existing “Empty dataset” case's service outcome remains pending. Preserve the case and do not choose a result.
- **Quality analysis:** quality-only cases remain separate from the proposed initial structural-validation operation.

No test identifier or expected service-level empty-input behavior is changed by this clarification.
