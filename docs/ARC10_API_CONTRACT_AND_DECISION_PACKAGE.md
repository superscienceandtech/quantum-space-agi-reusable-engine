# ARC-10 API Contract and Decision Package

**Status:** Proposal for decision. No endpoint, method, DTO, architecture, framework, scientific definition, security policy, or production scope in this document is approved. A completed proposal is not implementation authorization.

## 1. Purpose, scope, and intended consumer

This package asks the project to select an initial ARC-10 use case and resolve the decisions needed for a reviewable contract. It uses the proposed candidate from `docs/ARC10_USE_CASE_COMPARISON_AND_RECOMMENDATION.md`: a narrowly scoped mechanical schema-validation operation over caller-supplied records.

**PROPOSED — PENDING PROJECT APPROVAL:** If selected, the service would check submitted records against a server-controlled, explicitly identified structural schema and return mechanical validation findings. It would not assess scientific validity, scientific eligibility, provenance authenticity, NASA authorization, mission feasibility, or model readiness. “Accepted by schema” must not be represented as scientifically eligible.

**Intended consumer:** unresolved. ARC-09 is a possible consumer only if the product scope and production frontend are confirmed. The ARC-09 prototype is not that confirmation. An internal or other caller is also possible.

**Out of scope:** NASA TAP proxying/acquisition; scientific scoring; hidden schema inference; arbitrary client-authored eligibility rules; persistence; authentication implementation; production deployment; and dashboard summary metrics.

## 2. Verified engine boundary

The contract must be mapped to one explicitly selected engine API; two similarly named validators are not interchangeable:

1. `quantum_space_agi.data.schemas.validate_dataset(dataset: Dataset, schema: DataSchema)` returns `SchemaValidationReport`, uses zero-based indexes, and checks declared field presence/nullability/exact Python type. It requires a `Dataset`, which requires declared `Provenance`.
2. `quantum_space_agi.data.validator.validate_dataset(...)`, re-exported as `quantum_space_agi.data.validate_records`, accepts record input plus a schema mapping and returns `ValidationReport`, whose row indexes are one-based and whose report contains a generated validation timestamp. Its `include_actual_values` defaults to false.

Both are structural/mechanical tools. Neither establishes scientific correctness. The engine uses no HTTP framework and defines no HTTP status, JSON envelope, endpoint, auth, or transport error behavior. An implementation proposal should choose one function, index convention, trusted schema source, and provenance approach before a wire contract is approved.

## 3. Framework-neutral contract proposal

All items below are **proposed service-level concepts**, not actual project routes or accepted DTOs. The route and HTTP method are intentionally undecided; no illustrative URL is offered to avoid implying an endpoint.

### 3.1 Operation purpose

**Proposed operation:** validate one bounded collection of records against one server-registered schema/version and return mechanical structural findings. Initial scope should omit `analyze_quality` unless separately justified. It must not filter rows, repair data, coerce values, assign scientific eligibility, or infer measurements.

### 3.2 Request concepts

| Proposed field/concept | Proposed type | Required/nullable/missing semantics | Evidence classification and open decision |
|---|---|---|---|
| `schema_id` | string identifier | Required; non-empty; null/missing invalid. | **Proposed service-level field.** Derived conceptually from `DataSchema.identifier` / `ValidationReport.schema_name`; exact registry IDs and syntax require owner approval. |
| `schema_version` | string | Required; non-empty; null/missing invalid. | **Derived from existing `DataSchema.version`;** using it in the wire request is a proposal. Whether clients choose a version or service pins one is unresolved. |
| `records` | JSON array of objects | Required; null/missing invalid. Empty behavior is unresolved at service level. | **Proposed service-level input** based on the engine’s record-oriented inputs. Exact JSON value/type/depth/count limits require approval. |
| `dataset_id` | string identifier | Optional only if the selected engine contract permits omission; null semantics unresolved. | Present in existing `Provenance`/legacy report concepts, but service use, uniqueness and authority are unresolved. Do not treat it as identity proof. |
| `provenance` | object | Optional versus required is unresolved; missing/null are not equivalent until contract defines them. | Existing `Provenance` has fields for source, retrieval time, format, version, transforms and metadata. Caller-supplied values are declarations, not authenticated facts. Do not create synthetic provenance to satisfy `Dataset`. |

**Schema handling recommendation:** use a server-maintained allowlist/registry of reviewed schema IDs and versions; reject unknown IDs/versions. This is a **proposed control**, not an existing registry. Do not allow arbitrary caller rules to silently define scientific policy. Whether unknown fields in records are errors must be set by the selected trusted schema and exposed contract.

### 3.3 Response concepts

| Proposed field/concept | Proposed type | Presence/nullability | Evidence classification and caveat |
|---|---|---|---|
| `schema_id`, `schema_version` | strings | Present on a completed validation response. | **Derived** from `DataSchema.identifier/version` or `ValidationReport.schema_name`; exact names/semantics require mapping approval. |
| `is_valid` | boolean | Present for a completed run. | **Derived** from existing report validity (`SchemaValidationReport.is_valid`, `ValidationReport.is_valid`). Means only that the chosen mechanical rules passed. It is not scientific validity. |
| `record_count`, `valid_count`, `invalid_count` | non-negative integers | Present for a completed run. | **Derived** from existing report counts. For the schema report, `invalid_count` can be derived from invalid records. Exact consistency invariants must be tested. |
| `issues` | array of issue objects | Present; empty array means no mechanical issues, not no scientific concern. | **Derived** from `ValidationIssue`/`InvalidRecord` or legacy `ValidationIssue`; index base and issue mapping depend on engine choice. |
| issue `record_index` | integer | Present for row-specific findings; absent/null for dataset-level findings. Exact convention unresolved. | Existing APIs differ: zero-based in `SchemaValidationReport`; one-based in legacy `ValidationReport`. **Do not publish until one is selected.** |
| issue `field`, `code`, `message` | strings | Field may be absent/null for dataset-level issues; exact missing/null behavior requires mapping. | Existing `ValidationIssue` shapes differ: new schema type uses `field/code/message`; legacy uses `field_name/category/severity/expected/message`. These are not one common wire DTO. |
| `scientific_assessment` | fixed status or equivalent | Recommended always explicit as “not assessed” if output needs to state the boundary; exact enum/token unresolved. | **Proposed service-level statement**, not an engine output. Wording and compatibility require approval. It must never imply scientific approval. |
| `provenance` | object or absent | Include only provenance actually supplied/derived under the approved policy. | Existing provenance structures are evidence declarations; authenticity is not established. Never infer unavailable source facts. |
| `validated_at` | timestamp | Whether included is unresolved. | Legacy report has a generated timestamp; `SchemaValidationReport` does not. Timestamp source, timezone, and deterministic-test expectations require approval. |

No production field name or type should be inferred from this table alone. No scientific metric values are proposed.

### 3.4 Error categories and recovery

**Proposed categories** for contract discussion, not approved HTTP statuses:

- malformed request encoding/JSON or top-level shape;
- unsupported/unknown schema identifier or version;
- invalid request metadata or field types;
- payload/resource limit exceeded;
- operational/internal failure.

A successfully evaluated dataset with invalid records should normally be distinguishable from failure to execute validation. Exact response envelope, status codes, safe messages, correlation IDs, retryability, and client recovery are **unresolved** and require contract-owner approval. Do not echo raw record values by default: the legacy validator’s `include_actual_values=False` is a useful privacy-preserving precedent, not a full logging/retention policy.

### 3.5 Validation boundaries, resources, and data handling

- Reject malformed top-level input rather than coercing it.
- Validate against only a known server-side schema/version if the allowlist recommendation is accepted.
- Preserve submitted record values during mechanical validation; do not mutate, normalize, impute, deduplicate, or drop records.
- Bound request bytes, record count, nesting depth, per-record fields, execution time, and concurrent work. **Numbers and enforcement layer are not selected.**
- Treat submitted data and validation findings as potentially sensitive. Decide whether request bodies, field values, provenance, and error details may be logged; prefer redacted/minimal logging pending policy.
- Decide whether request data is strictly transient, retained, cached, or deleted and how that is verified. No retention behavior is established by current engine APIs.
- A schema-valid result does not establish NASA source authenticity, access rights, scientific truth, or permission to retain/redistribute data.

### 3.6 Provenance

If provenance is part of the use case, define the required source, source version, retrieval/acquisition time and timezone, transformations, schema version, and validation software version. Decide which values are server-observed versus caller-declared. Existing `Provenance` can represent declared source/retrieval metadata but does not authenticate it. Do not synthesize the source, timestamp, archive query, or data authorization. If no provenance is supplied, represent it as absent/unknown rather than inventing it.

### 3.7 Versioning and compatibility

**PROPOSED:** version the API contract independently from engine schema versions; maintain explicit schema ID/version selection; treat breaking field/type/meaning changes as a new contract version and document deprecation. These rules require owner approval. There is no API versioning mechanism in the inspected branch. Do not equate a JSON Schema version with scientific-policy approval.

## 4. Endpoint/schema approval boundary

No endpoint path, HTTP method, request DTO, response DTO, HTTP status mapping, or OpenAPI description is approved here. Any later illustrative example must carry a prominent “NOT APPROVED” label and must not be copied into implementation as authoritative. A framework-neutral contract can be reviewed first; selecting FastAPI/Flask/Django or a deployment target remains a separate architecture decision.

## 5. ARC-09 integration implications

`docs/ARC09_BACKEND_DATA_CONTRACT_REQUEST.md` from the inspected `origin/main` asks for a contract and keeps its dashboard P0 conditional. It requires the product/backend to supply metrics, meaning, type/nullability, stable identifiers, units or explicit unitless status, freshness, provenance, validation, and errors. It calls for Loading, Success, Empty, and Error to remain distinct. The prototype (`arc09-ui-prototype/PROTOTYPE_HANDOFF.md`) is plain HTML/CSS/JS with synthetic/conceptual examples, no API/backend/auth/persistence, and no confirmed production requirements.

Before any integration, ARC-09/product/backend must identify:

- whether validation is actually an ARC-09 user workflow and what user submits/selects;
- whether the production frontend repository and stack are known;
- how schema choices and validation results are presented;
- whether an empty record collection is invalid input or a valid empty response;
- how field-level findings are announced/accessibly navigated;
- how operational request failure differs from a completed report containing invalid records;
- whether validation/provenance/freshness information belongs in the UI;
- approved base URL/environment configuration, auth/session behavior, and CORS policy.

No endpoint integration, client configuration, synthetic fallback as live data, or UI work is part of this package.

## 6. Formal decision register

All rows below are **NOT DECIDED** unless explicitly labeled proposed. No approval is granted by this document. “Approval field” remains unfilled/NOT GRANTED; listed role types are not an assignment to a named approver.

| ID | Decision question | Recommended option | Alternatives | Technical rationale / evidence | Risk if unresolved | Required decision-maker/authority (to identify) | Current status | Approval field |
|---|---|---|---|---|---|---|---|---|
| D-01 | What is the first product use case? | **PROPOSED — PENDING PROJECT APPROVAL:** bounded mechanical schema validation. | Dashboard summary; process liveness; defer API. | ARC-08 has tested structural validators; ARC-09 summary metrics lack authoritative source. | Building an unused or wrong service. | Project/product decision authority. | PROPOSED — PENDING APPROVAL | NOT GRANTED |
| D-02 | What repository/service is production target? | Confirm the authoritative backend repository and branch before code. | New service; existing service; defer. | ARC-10 inspected branch has planning docs only at task baseline; no HTTP backend verified. | Changes land in wrong integration target. | Project/engineering owner. | NOT DECIDED | NOT GRANTED |
| D-03 | Who owns the contract? | Name an accountable contract owner and canonical versioned location. | Co-owned contract with documented maintainer. | No authoritative API contract owner/location verified. | Competing DTOs and unreviewed drift. | Project technical process. | NOT DECIDED | NOT GRANTED |
| D-04 | Which backend architecture/framework/runtime? | Decide after target/use case; preserve engine/transport separation. | FastAPI, Flask, Django REST Framework, other. | No framework dependency or route layer in inspected engine. | Unnecessary dependencies or incompatible deployment. | Architecture decision authority. | NOT DECIDED | NOT GRANTED |
| D-05 | What path, HTTP method, and API versioning? | Decide only after operation and contract owner are established. | Versioned route vs service-specific scheme. | No existing route contract. | Placeholder route treated as production API. | Contract/architecture authority. | NOT DECIDED | NOT GRANTED |
| D-06 | Which request/response DTO and field semantics? | Resolve exact types, required/optional/null/missing behavior and index base; choose one validator. | Schema `Dataset` API vs legacy record validator; alternate DTO. | Existing validators differ, including provenance requirement and index basis. | Client/server mismatch or fabricated provenance. | Contract owner; domain reviewer when semantic fields exist. | BLOCKED | NOT GRANTED |
| D-07 | What error/empty/invalid-result contract? | Distinguish request/operational failure, valid empty result, and completed validation findings. | Single error envelope or operation-specific forms. | ARC-09 requests distinct states; engine has no HTTP mapping. | Client may mistake invalid rows for server failure or vice versa. | Contract owner/product. | NOT DECIDED | NOT GRANTED |
| D-08 | What authentication and authorization apply? | Define caller identity, access rules, and least privilege before exposing submitted data. | Public endpoint only if explicitly justified; internal-only. | No auth implementation/policy verified. | Unauthorized data exposure or service abuse. | Project security/platform authority. | BLOCKED | NOT GRANTED |
| D-09 | What CORS and environment configuration apply? | Define production origins, local-dev rules, and secret/config handling. | Same-origin deployment; approved allowlist. | No frontend target or CORS policy verified. | Overexposure or unusable client integration. | Platform/security and frontend owners. | NOT DECIDED | NOT GRANTED |
| D-10 | What data retention, privacy and logging rules apply? | Minimize/ redact request content; explicitly decide transient handling and retention. | Approved retention with controls; no data submission. | Records can be arbitrary; no API retention/log policy exists. | Sensitive content retained or disclosed. | Project privacy/security/data authority. | BLOCKED | NOT GRANTED |
| D-11 | Which scientific definitions/provenance are exposed? | Keep initial scope structural-only and report scientific assessment as not performed, if approved. | Add domain-specific semantics only with authoritative definitions. | ARC-03 validation is structural; provenance is declarative. | Mechanical result misrepresented as scientific truth or source proof. | Relevant scientific/data owner. | NOT DECIDED | NOT GRANTED |
| D-12 | Which schemas and schema versions may clients select? | Proposed server-maintained allowlist with explicit version. | Single fixed schema; reviewed caller-provided schema. | `DataSchema` has ID/version; legacy validator accepts mapping schemas. | Caller can redefine checks or rules drift. | Contract/schema owner; domain review as applicable. | PROPOSED — PENDING APPROVAL | NOT GRANTED |
| D-13 | What payload/compute/concurrency limits apply? | Bound bytes, rows, depth, time and concurrency based on deployment evidence. | Reject large inputs; asynchronous job if justified. | No API workload profile or limit values found. | Resource exhaustion or arbitrary limits. | Technical/platform owner. | BLOCKED | NOT GRANTED |
| D-14 | Is quality analysis included? | Defer aggregates from first slice; add only if a consumer need is approved. | Include missing/duplicate/numeric summaries. | `analyze_quality` exists, but exact duplicates are whole-record equality and summaries are finite binary64 statistics. | Consumers overinterpret duplicate/statistic outputs. | Product and data/domain owner. | PROPOSED — PENDING APPROVAL | NOT GRANTED |
| D-15 | What provenance must be returned and how is it labeled? | Separate server-observed metadata from caller-declared metadata. | Omit provenance for non-scientific input checks. | Existing `Provenance` supports fields but does not authenticate them. | False source/authenticity claim. | Contract/data owner. | NOT DECIDED | NOT GRANTED |
| D-16 | What resource, timeout, retry, pagination and long-task behavior applies? | Decide from selected operation and measured workload; do not add queues/probes speculatively. | Synchronous bounded call; async job if demonstrated necessary. | No service workload or operational contract. | Latency/resource failure or unnecessary infrastructure. | Technical/platform owner. | NOT DECIDED | NOT GRANTED |
| D-17 | What acceptance/review criteria and reviewers apply? | Record test matrix, reviewers and acceptance route before release. | Project’s existing review process, if identified. | ARC-09 request calls for acceptance evidence; API process not confirmed. | Tests mistaken for approval or incomplete release. | ARC-10/project process to identify. | NOT DECIDED | NOT GRANTED |
| D-18 | What is the production frontend consumer? | Confirm repository, stack, owner, base URL and client expectations before integration. | No frontend integration in initial backend slice. | ARC-09 prototype is not a confirmed production app. | Client built against a prototype. | Product/frontend owner to identify. | NOT DECIDED | NOT GRANTED |

Task context identifies ARC-10 co-ownership/review roles but does not by itself resolve or approve these decisions. This register does not assign named authority or fill approvals.

## 7. Proposed implementation sequence after decisions

This sequence is conditional; it is not an authorization to start implementation.

1. **Select operation and target:** document the consumer, use case, production repository and accountable contract owner.
2. **Resolve data boundary:** choose the validator API, trusted schema/version mechanism, provenance behavior, row-index basis, empty input behavior, privacy/retention and limits.
3. **Approve contract and architecture:** record request/response/errors, route/method/version, authentication/CORS/configuration, runtime, and acceptance criteria.
4. **Implement only the approved operation:** transport adapter calls one engine API, does not mutate input, and returns explicit mechanical-only results.
5. **Test the contract:** engine mapping, malformed/empty/oversized inputs, row-index mapping, error distinction, no sensitive value leakage, no network by default, and documented provenance behavior.
6. **Integrate client only if selected:** confirm ARC-09 production repo and map distinct Loading/Success/Empty/Error states without synthetic fallback as live data.
7. **Review and release:** record actual commands/results, security review, contract review, and project approval separately.

## 8. Remaining blockers

Before implementation: first use case/consumer, production target, contract owner, validator/schema choice, exact DTO/error semantics, data handling/security, resource limits, framework/runtime, and required review path.

Before any scientific-data operation: authoritative field meanings, units, provenance and source terms/access/retention policy appropriate to the source. Structural validation cannot resolve them.

Before ARC-09 integration: confirmed production frontend repository/stack, product-selected workflow, and approved backend contract. No production client is established by the prototype.

## 9. Approval statement

This package offers a recommendation for consideration. It does not grant or record approval. No API, architecture, scientific definition, data permission, security rule, deployment, or implementation scope is authorized by this document. A decision-maker must record approval through the project’s established process before gated work begins.
