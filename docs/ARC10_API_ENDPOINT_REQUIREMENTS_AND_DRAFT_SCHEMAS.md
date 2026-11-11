# ARC-10 API Endpoint Requirements and Draft Response Schemas

**Status:** Contract-design preparation. All endpoint identifiers and schemas below are **ILLUSTRATIVE — NOT APPROVED**. No production API contract, first endpoint, or implementation authorization is established by this document.

## 1. Executive Summary

The refreshed ARC-10 branch contains only the repository initialization commit and README.md. The inspected ARC-08 branch provides reusable Python libraries, but no general HTTP backend. The ARC-09 prototype and backend-contract request are available only in locally inspected origin/main. The request leaves endpoints and schemas to an authoritative backend contract.

Several capabilities can be discussed as candidates, especially dataset validation and a dashboard summary, but evidence does not establish a single correct first operation. Dataset validation is a technical candidate, **not an approved MVP**. The ARC-09 dashboard summary is **PROPOSED / PENDING APPROVAL**.

## 2. Sources Inspected and Evidence Boundaries

- Current ARC-08 source/tests: checkout at de48b077571fe44b1fc8b7ab8fad6ba60016f029.
- ARC-09 UI prototype, docs/ARC09_BACKEND_DATA_CONTRACT_REQUEST.md, ARC-05 simulation docs/source, and optimization modules: locally available origin/main only. Not integrated into refreshed ARC-10.
- The ARC-09 request asks for definitions, types/nullability, units, provenance, timestamps, pagination/filtering, validation, errors, authentication, CORS, and operational behavior. It defines no paths/methods/schemas.
- Prototype values/labels are not production data or approved API fields.

## 3. API Capability Inventory

| Capability | Evidence / engine support | Consumer / sensitivity | Complexity | Initial MVP suitability | Approval |
|---|---|---|---|---|---|
| Health/status | No HTTP health endpoint found; liveness semantics undefined. | Operational consumer unknown; dependency readiness may mislead. | Low if process-only. | Candidate for discussion. | Not approved. |
| Dashboard summary | Synthetic cards exist only in ARC-09 prototype; no authoritative metric source/aggregation. | Proposed ARC-09 consumer; unit, freshness, source and provenance matter. | Medium–High. | Candidate pending metric definitions. | Not approved. |
| Dataset discovery/metadata | Current data package has Dataset, DataSource, Provenance; no persistent catalog API found. | Consumer unknown; source and reuse constraints matter. | Medium. | Defer until catalog use case exists. | Not approved. |
| Dataset validation/quality | Current checkout has DataSchema, validate_dataset(), analyze_quality(); mechanical checks only. | Potential tooling consumer; submitted records may be sensitive or large. | Medium. | Strong engineering candidate, not selected. | Not approved. |
| Scientific data/provenance | Data/provenance models and external TAP adapter exist on ARC-08. | Exposed science requires source, units, semantics and access decisions. | High. | Defer. | Not approved. |
| ML readiness/evaluation | Current ML readiness, preparation, diagnostics and evaluation APIs exist. | Consumer unknown; must not imply scientific acceptance. | High. | Defer. | Not approved. |
| Simulation execution/results | ARC-05 implementation exists only in origin/main; no API contract. | SI/ECI, assumptions, array serialization and compute limits matter. | High. | Defer. | Not approved. |
| Optimization execution/results | Interfaces/solver exist only in origin/main; no product workload defined. | Compute cost and bounds material. | High. | Defer. | Not approved. |
| Mission/experiment management | No supporting workflow or persistence requirement found. | Unknown. | High. | Do not invent workflows. | Not approved. |

## 4. Candidate First-Use-Case Discussion

| Candidate | Readiness evidence | Main blockers | Status |
|---|---|---|---|
| Process health | Technically small and low scientific sensitivity. | No verified consumer or definition of healthy. | Candidate only. |
| Dataset validation/quality | Reusable validation/quality functions exist in current ARC-08 checkout. | No accepted client schema, privacy/retention policy, or request limits. | Candidate only; technical feasibility is not product priority. |
| Dashboard summary | ARC-09 request calls it a proposed P0 slice conditional on approval. | Metrics, source, aggregation, units, nullability, freshness and provenance unresolved. | Proposed / pending approval. |
| Simulation | ARC-05 implementation is in origin/main. | Not in current branch; serialization, use case, workload bounds and domain review unresolved. | Defer. |

No winner is selected.

## 5. Endpoint Requirements Catalogue

All paths and methods are placeholders only.

| Placeholder | Purpose / consumer | Inputs and validation | Output / empty/failure behavior | Operational/provenance requirements |
|---|---|---|---|---|
| GET /example-health | Optional process-status consumer. | No body; dependency checks only if approved. | Define process-live vs dependency-ready; do not imply overall scientific/system readiness. | No external probes unless required. Version/timestamp semantics TBD. |
| POST /example-dataset-validation | Potential mechanical validation service. | Schema identity/version and records illustrative; body size, count, nesting and types TBD. | Report counts/issues; define empty input separately. Never call it scientific eligibility. | Privacy, retention, logging and provenance rules required. Uses current schema/validation APIs. |
| GET /example-dashboard-summary | Proposed metric-card summary. | Query identifiers/date ranges only if approved. | Define valid-empty separately from error; metric labels/values TBD. | Each metric needs source, unit, aggregation window, freshness and provenance. |
| Simulation/optimization placeholders | Future use cases only. | No request schema justified. | No response shape justified. | Need approved engine integration, workload budgets, async policy and domain review. |

Potential status categories, all **PROPOSED**: success 200; invalid input 400 or 422; not found 404; authentication/authorization 401/403 only if selected; oversized input 413; agreed resource rejection 429 or another contract status; upstream failure 502/503; unexpected internal failure 500. The contract owner must choose consistent semantics.

## 6. Illustrative Request Schemas

### 6.1 Dataset validation

**ILLUSTRATIVE — NOT APPROVED.** Concepts are informed by current DataSchema, but transport rules are TBD.

    {
      "schema_id": "TBD",
      "schema_version": "TBD",
      "records": "TBD: JSON array of record objects"
    }

Define whether clients may select schemas, record size/count limits, nested value types, unknown fields, and whether submitted data is retained. Do not invent identity or provenance.

### 6.2 Dashboard summary

No request shape is justified. Scope may be global, context-specific, time-filtered, or otherwise; **TBD**.

## 7. Illustrative Response Schemas

### 7.1 Dataset validation

**ILLUSTRATIVE — NOT APPROVED.** This is a transport mapping concept, not a recommendation to expose the internal report object directly.

    {
      "schema_id": "TBD",
      "schema_version": "TBD",
      "record_count": "TBD: integer",
      "valid_count": "TBD: integer",
      "invalid_records": [
        {
          "record_index": "TBD: integer; indexing convention",
          "issues": [
            {
              "field": "TBD: string or null",
              "code": "TBD: stable machine-readable code",
              "message": "TBD: client-safe text"
            }
          ]
        }
      ],
      "scientific_eligibility": "NOT_ASSESSED"
    }

The current SchemaValidationReport has schema ID/version, counts, invalid record indices and issues. Public names, index base, stable codes and an explicit eligibility marker require approval. Structural validity is not scientific eligibility.

### 7.2 Dashboard summary

**ILLUSTRATIVE — NOT APPROVED.** No metric value is drawn from prototype sample values.

    {
      "as_of": "TBD: timestamp format and timezone",
      "metrics": [
        {
          "id": "TBD",
          "label": "TBD",
          "value": "TBD: numeric, string, or null",
          "unit": "TBD",
          "status": "TBD",
          "source": "TBD",
          "freshness": "TBD"
        }
      ]
    }

Each metric needs a definition, type/nullability, source, aggregation window, unit or explicit unitless definition, precision, freshness and provenance.

### 7.3 Health

**ILLUSTRATIVE — NOT APPROVED.**

    {
      "status": "TBD: liveness/readiness meaning",
      "service_version": "TBD",
      "timestamp": "TBD: format and timezone"
    }

## 8. Error Contract Proposal

**ILLUSTRATIVE — NOT APPROVED:**

    {
      "error": {
        "code": "TBD: stable code",
        "message": "TBD: client-safe message",
        "request_id": "TBD: correlation identifier",
        "details": "TBD: optional structured field errors"
      }
    }

Decide how transport validation, domain failure, not found, valid-empty, access failure, upstream errors, resource rejection, and unexpected errors differ. Do not expose traces, credentials, local paths, raw upstream bodies or sensitive payloads. Mapping from core.Result and exceptions to HTTP statuses is undefined.

## 9. ARC-09 Dashboard-to-API Requirements Mapping

The prototype in origin/main presents metric cards, resource cards, recent activity, line/grouped-bar/scatter charts and a conceptual relationship graph. Its values and relationships are synthetic/conceptual, not production data or an approved model.

| UI group | Minimum decisions before integration |
|---|---|
| Metric cards | Meaning/label, type/nullability, units, source, aggregation, freshness, precision and provenance for each selected metric. |
| Resource cards | Resource identity, amount, unit, denominator/percentage meaning, limits/reference values and provenance. |
| Recent activity | Event IDs, status vocabulary, ordering, timestamp/timezone, pagination/filtering and retention. |
| Line chart | X/Y meanings, units, series identity, ordering, sampling/aggregation, missing gaps, uncertainty and provenance. |
| Grouped bar | Category/series definitions, units, comparability, order and aggregation. |
| Scatter | Axis definitions/units, paired-observation meaning, point identity, uncertainty and filtering. |
| Relationship graph | Product need, stable entity/edge IDs, edge meaning/direction/cardinality, scale and permissions. |

The ARC-09 request requires distinct Loading, Success, Empty and Error UI states. Loading is client state; success, valid-empty and failure representations depend on the approved API contract. Synthetic fallback values must not be presented as live.

## 10. Scientific Data and Serialization Requirements

For scientific values, define quantity, unit, coordinate/reference frame, timestamp meaning/timezone, precision, nullability, uncertainty, provenance, source/model version, and whether values are measured, simulated, estimated, predicted, or assumed.

For arrays, define JSON nesting, shape/dimensions, element order, precision, non-finite policy and size limits. ARC-05 results in origin/main include NumPy arrays; no response conversion is defined. Large-result artifact handling is future-only unless justified.

## 11. Proposed Test and Acceptance Matrix

Tests are proposed, not written or executed.

| Area | Cases |
|---|---|
| Request validation | Valid, missing, wrong types, nullability, ranges, unknown schema/ID. |
| Empty/malformed | Valid empty results vs empty inputs; malformed JSON; unexpected fields. |
| Engine mapping | Correct DTO mapping, domain errors, malformed outputs, no mutation/reinterpretation. |
| Numeric serialization | Units/precision, array shape/order, non-finite values, payload limits. |
| Provider failures | Timeouts/upstream mapping only if an approved operation calls a provider. |
| Security/resources | Oversized body, excessive records/dimensions, auth boundaries, secret/log redaction. |
| Provenance | Source, timestamps, units and provenance preserved according to contract. |
| Client states | Loading, Success, Empty, Error; no synthetic fallback as live data. |

## 12. Security and Operational Requirements

Authentication, authorization, CORS, secret management, logging/redaction, request limits, compute budgets, timeouts, cancellation, retries, pagination, filtering, freshness, and long-running operation policy are **TBD / REQUIRES APPROVAL**. The NASA adapter is not authorization to proxy archive access. No database, queue, cache or deployment provider is implied.

## 13. Decision and Approval Register

| Decision | Current evidence/options | Status |
|---|---|---|
| First product/API use case | Health, validation, summary candidates; none selected. | REQUIRES APPROVAL |
| Production repository/branch | ARC-10 fetched branch initialized; target frontend/backend ownership needs confirmation. | TBD |
| Contract owner/location | No approved owner/versioned contract identified. | TBD |
| Endpoint paths and methods | None defined. | REQUIRES APPROVAL |
| Request/response schemas | Illustrations only; fields and semantics TBD. | REQUIRES APPROVAL |
| Units/reference frames | ARC-05 origin/main source uses SI/ECI; exposed use case TBD. | REQUIRES DOMAIN APPROVAL |
| Provenance/uncertainty | Models exist; public requirements undecided. | REQUIRES APPROVAL |
| Errors/statuses | No HTTP convention found. | TBD |
| Authentication/authorization | No implementation or policy found. | REQUIRES APPROVAL |
| Pagination/filter/freshness | Decide per selected operation. | TBD |
| Resource limits/long-running tasks | No API workload profile found. | REQUIRES APPROVAL |
| Simulation/optimization scope | Modules only in origin/main; no API use case approved. | REQUIRES APPROVAL |

Task context identifies Sonjoy/Rafi as co-owners, Amran as reviewer, and Yousuf's technical/contract responsibilities. It does not assign extra per-decision authority.

## 14. Implementation Readiness Assessment

Evidence supports requirements drafting, not implementation. Confirm production target, first use case, contract owner, approved schema/error semantics, relevant scientific definitions, security policy, operational limits and acceptance requirements first. The prototype is not production integration. No endpoint or schema here is approved.

## 15. Recommended Next Actions

1. Confirm target backend/frontend repositories and contract owner.
2. Select the first operation based on product need, not prototype appearance alone.
3. Obtain authoritative fields, types, nullability, IDs, units, provenance, errors and operational requirements.
4. Review scientific mappings with the relevant domain owner.
5. Convert only the approved option into a versioned contract, then plan implementation.
