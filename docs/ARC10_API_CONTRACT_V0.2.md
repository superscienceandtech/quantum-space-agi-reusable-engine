# ARC-10 API Contract v0.2

DRAFT — NOT APPROVED
NON-CANONICAL WORKING DOCUMENT

- Version: 0.2
- Reconstructed working draft prepared from the four original tracked ARC-10 planning reports.
- This document does not claim to replace, recover, reproduce, or formally approve any earlier v0.1 artifact.
- It is not the final approved API contract or a canonical governance record.
- Proposed behavior is distinguished from implemented behavior.
- No production implementation or deployment is authorized by this document.

## 1. Scope and status

This document conservatively records API concepts raised in the original ARC-10 planning reports. Dataset validation is a technical candidate, not a selected product operation or approved MVP. No endpoint or contract is approved here.

The NASA Exoplanet Archive TAP adapter described in the readiness report is an external data-provider adapter, not the project's frontend-facing backend API. Source: Repository & API Readiness Report §§6, 8.

## 2. Evidence labels

- SOURCE-SUPPORTED: stated in an original tracked report.
- PROPOSED — PENDING APPROVAL: an illustrative or recommended behavior, not adopted.
- UNRESOLVED / BLOCKED: sources do not establish the decision.
- IMPLEMENTATION STATUS: NOT VERIFIED: this draft is not implementation evidence.

## 3. Operation candidates

All routes and methods below are placeholders from Endpoint Requirements §5, not approved operations.

| Placeholder | Candidate purpose | Status |
|---|---|---|
| POST /example-dataset-validation | Potential mechanical schema-validation operation. | PROPOSED — PENDING APPROVAL; not an approved path, method, use case, or MVP. |
| GET /example-health | Optional process-status operation. | PROPOSED — PENDING APPROVAL; health semantics and consumer undefined. |
| GET /example-dashboard-summary | Potential dashboard metrics. | PROPOSED — PENDING APPROVAL; authoritative metrics and sources absent. |

No /api/v1 route or production endpoint is established by the four source reports. No candidate is selected. Sources: Endpoint Requirements §§1, 4–5; Implementation Plan §§1, 5.

## 4. Candidate dataset-validation request and response

### Request

Endpoint Requirements §6.1 gives an illustrative request concept with schema identity/version and records. It leaves transport rules unresolved.

- schema identity/version: PROPOSED selector concepts; no actual IDs, versions, grammar, or catalog are approved.
- records: PROPOSED as a JSON array of record objects; exact type mapping, requiredness, nullability, unknown-field behavior, and limits are unresolved.
- provenance: UNRESOLVED. The original reports do not define a wire representation; §6.1 says not to invent identity or provenance.

### Response

Endpoint Requirements §7.1 illustrates schema identity/version, record and valid counts, invalid record indices and issues, and a scientific_eligibility marker. This is illustrative only.

Exact fields, index basis, issue codes, message stability, marker inclusion, and serialization rules are UNRESOLVED. The source notes structural validity is not scientific eligibility. Do not treat a validation report as scientific approval or eligibility.

## 5. Request and validation behavior

| Case | Source evidence | Contract status |
|---|---|---|
| Malformed request | Request-validation cases are proposed in Endpoint Requirements §11; no final classification or status is specified. | UNRESOLVED / BLOCKED |
| Empty input | Endpoint Requirements §§5, 11 say empty behavior must be separately defined. | UNRESOLVED / BLOCKED |
| Structurally invalid records | Validation is a candidate supported by engine capability, but API output/classification are not settled. Sources: Endpoint Requirements §§3–4; Readiness Report §6. | PROPOSED — PENDING APPROVAL |
| Unsupported schema | Schema identity/version is illustrative; no actual catalog or lookup behavior approved. | UNRESOLVED / BLOCKED |
| Unexpected fields / type coercion | Exact request mapping is not defined. | UNRESOLVED / BLOCKED |
| Quality analysis | A separate engine capability is noted, but its inclusion is not selected. | UNRESOLVED / BLOCKED |

Do not silently change domain behavior or describe mechanical validation as scientific correctness. Sources: Architecture Proposal §§3, 8–9; Endpoint Requirements §§3, 7.

## 6. Errors and HTTP mapping

Endpoint Requirements §5 lists possible HTTP status categories as PROPOSED alternatives, and §8 provides an illustrative error envelope. Neither is approved.

The four reports do not settle:

- Which request failures map to 400 versus 422.
- How valid-empty input differs from failure.
- Unsupported-schema status.
- Authentication/authorization behavior.
- Resource-limit rejection.
- Upstream or unexpected internal failures.
- Error codes, envelope, details, or request identifier.

All mappings remain UNRESOLVED / BLOCKED. Do not copy illustrative status categories into binding contract guarantees.

## 7. Versioning and compatibility

The reports identify versioning and compatibility as decisions but do not define URL/header versioning, guarantees, deprecation, or migration rules. Sources: Readiness Report §§11, 15; Endpoint Requirements §§5, 13–14; Implementation Plan §§3, 11–12.

Status: UNRESOLVED / BLOCKED. No /v1 path is approved by these four source reports.

## 8. Provenance, scientific semantics, and schemas

- SOURCE-SUPPORTED: exposing scientific values requires explicit units, frames where relevant, precision, nullability, provenance, timestamps, uncertainty, and measured/simulated/estimated/predicted/assumed meaning. Sources: Readiness Report §10; Endpoint Requirements §10.
- PROPOSED — PENDING APPROVAL: keep transport mapping explicit and separate from engine models. Source: Architecture Proposal §§5, 9.
- UNRESOLVED / BLOCKED: provenance fields, authenticity claims, catalog ownership, schema IDs/content, scientific definitions, and data-use/retention rules. Sources: Readiness Report §§11, 14–15; Endpoint Requirements §§6, 10, 12–14.

No schema ID, schema definition, scientific eligibility rule, source authenticity, or NASA authorization is established here.

## 9. Synchronous operation and resource boundary

The architecture proposal suggests bounded synchronous requests only if a selected operation fits a request lifecycle, and recommends measuring workload before considering background work. This is PROPOSED, not approved operating policy. Source: Architecture Proposal §11.

Payload, record, depth, array, time, cancellation, retry, concurrency, pagination, and long-running behavior remain UNRESOLVED. Sources: Architecture Proposal §§10–11, 17; Endpoint Requirements §§10–12; Implementation Plan §§3, 8–9.

No queue, database, cache, persistence, or external provider call is required or approved by this draft.

## 10. Security and operations

Authentication, authorization, CORS, secrets, logging/redaction, retention, deployment, and release policy are UNRESOLVED / BLOCKED. The architecture report provides proposals only and does not select these choices. Sources: Architecture Proposal §§10, 17–19; Endpoint Requirements §12; Implementation Plan §§3, 12.

The ARC-09 prototype is described as a synthetic/conceptual visual reference, not a production client or data source. Do not present its sample values as live or scientific data. Sources: Readiness Report §7; Endpoint Requirements §§2, 9.

## 11. D-01 through D-16 references

The four original tracked reports contain no D-01 through D-16 register or status assignments. This draft therefore records no mapping or decision:

D-01 through D-16: each UNRESOLVED — SOURCE EVIDENCE INSUFFICIENT.

D-04/D-05 numbering discrepancy: OPEN and not reconciled. This status is carried forward from the task context; the four primary source reports do not document or resolve it. The four primary sources do not define a canonical mapping or resolve the discrepancy. No reinterpretation or renumbering is made.

## 12. Implementation status and approval boundary

IMPLEMENTATION STATUS: NOT VERIFIED by this reconstructed draft. The original reports describe no general HTTP backend or approved API contract at their inspection snapshots. Sources: Readiness Report §§8, 11–12, 17; Architecture Proposal §§18–19; Endpoint Requirements §§14–15; Implementation Plan §§1–3, 6, 12–13.

This document authorizes no implementation, deployment, client integration, data access, or production exposure. Planning and technical proposals are not approvals.

## 13. Source traceability

Primary sources:

1. docs/ARC10_REPOSITORY_API_READINESS_REPORT.md — §§5–12, 14–17.
2. docs/ARC10_BACKEND_API_ARCHITECTURE_PROPOSAL.md — §§3–5, 8–12, 17–19.
3. docs/ARC10_API_ENDPOINT_REQUIREMENTS_AND_DRAFT_SCHEMAS.md — §§3–8, 10–15.
4. docs/ARC10_IMPLEMENTATION_PLAN_AND_TEST_STRATEGY.md — §§3–6, 8–13.

References identify source locations only; they do not confer approval.
