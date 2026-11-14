# ARC-10 Use-Case Comparison and Recommendation

**Status:** Internal proposal only. This comparison does not select an approved product scope, architecture, API, or implementation target. It does not authorize production work.

**Evidence basis:** ARC-08 source inspected in the separate `quantum-space-agi-reusable-engine` checkout at `arc/08-ai-ml` / `de48b077571fe44b1fc8b7ab8fad6ba60016f029`; ARC-09 documents inspected from the locally available `origin/main` reference. Those references are snapshots, not evidence of current co-owner work or production deployment.

## 1. Decision in brief

Three possible first use cases were compared: mechanical dataset validation/quality checks, an ARC-09 dashboard summary, and process health/status. The strongest repository-backed engineering candidate is a **narrow mechanical dataset schema-validation operation**, with optional quality summaries deferred until their output and privacy rules are selected. ARC-08 already has tested schema and quality functions. This says nothing about product priority or scientific value.

**Recommendation: PROPOSED — PENDING PROJECT APPROVAL.** Select a bounded schema-validation operation only if a project decision-maker confirms a consumer and accepts its data-handling contract. Do not expose scientific eligibility, NASA-specific interpretation, or a dashboard metric under this proposal.

No candidate is approved. If the project has no user need for submitted-dataset validation, repository capability alone is not sufficient reason to build a service; the use-case decision remains open.

## 2. Evidence and candidate comparison

| Dimension | Mechanical validation / quality check | ARC-09 Dashboard Summary | Process health/status |
|---|---|---|---|
| User/system value | Could give a caller deterministic feedback about conformance to an explicitly selected schema. Whether a caller needs this service is unknown. | Could populate one approved dashboard summary. ARC-09 describes this as a proposed P0 slice conditional on product/backend approval. | Could let an operator distinguish a responding process from an unavailable process; no operational consumer or semantics are documented. |
| Existing engine capability | **Verified:** `src/quantum_space_agi/data/schemas.py::validate_dataset(dataset, schema)` checks declared field presence, nullability, and exact Python types; returns `SchemaValidationReport` and does not coerce/drop rows. **Verified:** `src/quantum_space_agi/data/quality.py::analyze_quality(dataset, validation_report=...)` reports missing counts, exact whole-record duplicates, validation row indexes, and finite numeric summaries. **Alternative legacy API:** `src/quantum_space_agi/data/validator.py::validate_dataset` (publicly re-exported as `validate_records`) accepts a sequence/mapping plus a schema mapping and returns `ValidationReport`; its row indexes are one-based and its report has a run timestamp. | No authoritative summary source, metrics, aggregation, unit, or freshness meaning was found in the ARC-09 request. Prototype `arc09-ui-prototype/data.js` is synthetic/conceptual. | `src/quantum_space_agi/config.py` supports explicit settings construction and log-level configuration; searches did not identify an application lifecycle or health-state API. No HTTP process-health route exists in inspected evidence. |
| Required input | Proposed: JSON record array plus identifier for a server-controlled schema/version. Exact accepted sizes, types, schema registry and empty-input behavior require approval. Existing `data.schemas.validate_dataset` requires `Dataset` and `DataSchema`; `Dataset` requires `Provenance`. The legacy record validator accepts records and a mapping schema without a `Dataset`, but its schema/report contract differs. This adapter choice is unresolved. | An authoritative metrics source, definitions, identifiers/context, units, freshness and provenance are required; none is established by the prototype. | Runtime/process lifecycle and the definition of liveness/readiness must be selected. Dependency checks must not be implied unless specified. |
| Expected output | Proposed: mechanical valid/invalid summary and field-level structural issues. Never “scientifically eligible.” Whether to return quality summaries is unresolved; quality statistics can be binary64 approximations and duplicate detection is exact whole-record equality, not entity identity. | Only approved metric labels, values, units, freshness and provenance could be returned. No response contract is available. | At most a narrowly defined process response. A liveness response must not imply scientific, data-source, or downstream dependency readiness. Exact status fields are not defined. |
| Scientific semantics required | Low only if restricted to structural checks against a trusted schema. Schema selection and field semantics still require an owner; structural validity does not establish scientific correctness. | High if values are scientific/simulation-derived: metric meanings, units, uncertainty, provenance and freshness are all required. | Low for process liveness only; higher if “ready” includes data providers or scientific services. Those meanings are unspecified. |
| NASA data-rights implications | None can be assumed. Caller-submitted data may not be NASA data; if archive-derived input is allowed, source/access/retention/reuse obligations must be established. No persistence or reuse permission is implied. | Unknown until the summary source is identified. Do not proxy or republish NASA data without applicable source terms and authorization. | No direct data-rights implication for process-only liveness; dependency/source probes would change that assessment and require decisions. |
| Security/privacy | Potentially sensitive arbitrary records. Request-size/record limits, access controls, retention, log redaction, error-value disclosure, and deletion behavior require decisions. The legacy validator omits actual values by default, but a service must preserve that property deliberately. | May disclose mission or scientific data and operational context. Authentication, authorization, field-level access, caching, and retention are unresolved. | Exposes operational state and possibly dependency topology. Public/internal access and response detail require a security decision. |
| Computational/resource needs | Linear in record count and schema fields for structural validation; exact duplicate/quality work also traverses records and values. Enforce bounded request/record/depth/cost limits; do not select numeric limits without approval. | Depends on data source and aggregation; query, cache, freshness, and compute behavior unknown. | Process-only response can be small; dependency probes, if any, introduce latency and failure coupling. |
| Testability | Strong for deterministic mechanical behavior using the existing ARC-03 synthetic tests; API contract tests still require approved wire semantics. Existing legacy report includes current time, so byte-identical report output is not established. | Cannot produce meaningful contract tests without authoritative metric examples/source; synthetic UI data cannot serve as production fixtures. | Straightforward only after liveness/readiness and failure semantics are defined. No runtime exists to test in this repository. |
| ARC-09 dependency | None inherent. ARC-09 integration should not be assumed. | Direct dependency on ARC-09 product scope and confirmed production frontend, neither established by the prototype. | No direct UI dependency; an operator/monitor consumer must be identified. |
| Unknowns / approvals | Consumer and use case; schema ownership/registry; which validator API; input/provenance model; output mapping; limits; privacy/retention; error semantics; hosting and security. | Approved metrics, backend source, product scope, production frontend, contract owner, units/provenance/freshness, access policy. | Operational owner, health definition, deployment/runtime, probe behavior, security exposure, consumer. |
| Engineering complexity estimate | **Medium estimate** if fixed trusted schemas and a bounded request are approved; adapter/transport/privacy and stable contract remain work. Quality summaries increase scope. | **Medium–High estimate** because authoritative data and aggregation contracts are absent. | **Low estimate** for process-only liveness after runtime selection; **Medium+** if dependency readiness is included. Estimates are not schedules or approvals. |

## 3. Verified ARC-08 capability details

| Source | Actual interface/behavior | Existing test evidence | Limitation for API use |
|---|---|---|---|
| `src/quantum_space_agi/data/schemas.py` | `FieldSchema(name, value_type, required, allow_none)` and versioned `DataSchema(identifier, version, fields)` are frozen structures. `validate_dataset(Dataset, DataSchema)` returns `SchemaValidationReport(schema_id, schema_version, record_count, valid_count, invalid_records)`. Each `InvalidRecord.record_index` is zero-based and carries `ValidationIssue(field, code, message)`. Exact type checks reject `bool` where `int` is required. It does not coerce/drop/mutate records; it checks only declared structural conditions. | `tests/data/test_schemas.py` covers valid rows/version; missing fields; null and wrong types; boolean-vs-integer; multiple issues and no mutation; optional/nullable; invalid/duplicate schema fields. | Requires an ARC-03 `Dataset` and `DataSchema`; `Dataset` in turn requires provenance. It establishes neither scientific validity nor a wire format. |
| `src/quantum_space_agi/data/quality.py` | `analyze_quality(Dataset, validation_report=None)` returns `DataQualityReport` with missing counts, exact duplicate groups, invalid indexes, and per-field finite numeric count/min/max/mean. Empty/None/blank text counts as missing; bool is excluded from numeric statistics; means are binary64 approximations. | `tests/data/test_quality.py` covers empty datasets, missing, exact duplicates independent of key order, validation-index linkage, finite stats/bool exclusion, large/mixed means, and non-mutation. | “Duplicate” means exactly equal complete records, not duplicate planet/mission identities. Numeric summaries are descriptive mechanics, not endorsed metrics or scientific conclusions. |
| `src/quantum_space_agi/data/models.py` and `src/quantum_space_agi/data/provenance.py` | `Dataset` requires a `Provenance`, copies top-level record mappings, and exposes top-level structures read-only; nested lists/dicts are not deep-frozen. `Provenance` requires dataset id, declared `DataSource`, timezone-aware retrieval timestamp and format; metadata/transforms are optional. | `tests/data/test_models.py`, `tests/data/test_provenance.py`, and ingestion tests cover these declared contracts. | Declared provenance is not authenticated. A service must not synthesize source/retrieval facts or use caller metadata as proof of authority. |
| `src/quantum_space_agi/data/validator.py` and public `validate_records` export | Record-oriented `validate_dataset(dataset, schema, include_actual_values=False)` accepts a `DatasetLoadResult`, `{records: ...}` mapping, or record sequence with a schema mapping. It returns `ValidationReport`; indexes are one-based, and actual values are omitted by default. Empty records are reported invalid. The report includes a validation timestamp. | `tests/data/test_public_api.py` verifies the public import. No dedicated legacy-validator test module was found in the inspected `tests/data/` tree; the exported API has less direct test coverage than the schema-based validator. | There are two functions named `validate_dataset` with different input/output/index conventions. API code must import a fully qualified function and document one index basis. A caller-controlled schema must not become an unreviewed policy mechanism. |
| `src/quantum_space_agi/config.py` | Explicit settings/environment parsing covers application log level; it is not a process health monitor. | Configuration tests cover settings behavior. | No liveness/readiness data or HTTP behavior is exposed. |
| `pyproject.toml` | Python >=3.11; runtime dependency list is empty; pytest/Ruff/mypy are optional development extras. | Package tests exist. | No HTTP framework or runtime contract is selected. |

No tests were executed for this proposal; test references above identify existing source tests, not results of a new run.

## 4. Recommended candidate and scope boundary

**PROPOSED — PENDING PROJECT APPROVAL:** A first operation could validate caller-supplied records against a server-owned, named/versioned structural schema, returning counts and field-level issues. Keep quality aggregation out of the initial slice unless a consumer requests it and accepts what its exact-duplicate and numeric summaries mean.

Reasons:

1. It is the only candidate with directly relevant, already-tested engine functions in the inspected ARC-08 source.
2. A structural-only operation can explicitly avoid deriving scientific eligibility or interpreting archive fields.
3. It can be tested locally without using NASA data, once API semantics and bounded resource limits are approved.
4. It does not depend on the ARC-09 prototype or assume it is the production frontend.

Limits: the service consumer, schema source, provenance model, privacy/retention controls, validator selection, and response semantics remain unresolved. The existing API is not itself a ready-made HTTP endpoint. A process-only health endpoint may ultimately be simpler if the team needs operations monitoring; no consumer or requirement currently establishes that need. No candidate should be implemented solely because it is technically available.

## 5. ARC-09 implications

The ARC-09 contract request (`docs/ARC09_BACKEND_DATA_CONTRACT_REQUEST.md` in the inspected `origin/main` reference) makes dashboard summary P0 conditional, identifies distinct Loading/Success/Empty/Error states, and asks for an authoritative backend contract. It supplies no endpoint, method, production schema, field names, units, or data source. The prototype handoff (`arc09-ui-prototype/PROTOTYPE_HANDOFF.md` in that reference) says the UI is isolated HTML/CSS/JS, its content is synthetic/conceptual, and it has no production API, persistence, or authentication. Thus:

- No production frontend repository/stack is confirmed.
- Validation-service request parameters and response fields cannot be inferred from prototype cards or sample data.
- If a later ARC-09 feature consumes validation, ARC-09 must specify how records/schema are chosen, how validation issues are shown, and what “empty” means; a technical error must remain distinct from a valid invalid-record report.
- Loading/Success/Empty/Error, freshness/provenance display, retry messaging, and client configuration need product/backend agreement. Do not show synthetic fallback data as live.
- No change to Hridi’s UI or frontend integration is in this proposal.

## 6. Decision status

| Topic | Current status |
|---|---|
| Candidate use cases | Identified from project materials; none approved. |
| Dataset structural validation as first slice | **PROPOSED — PENDING PROJECT APPROVAL**. |
| Dashboard summary and process health | Alternatives; not selected. |
| Backend target, framework, endpoint, request/response schema | Not decided. |
| Scientific/API/data access policy | Not decided. |
| Implementation authorization | Not established by this recommendation. |

See `docs/ARC10_API_CONTRACT_AND_DECISION_PACKAGE.md` for proposed wire concepts and the formal decision register.
