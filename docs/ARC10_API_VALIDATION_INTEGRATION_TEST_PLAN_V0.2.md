# ARC-10 API Validation Integration Test Plan v0.2

DRAFT — NOT APPROVED
NON-CANONICAL WORKING DOCUMENT

- Version: 0.2
- Reconstructed working draft prepared from the four original tracked ARC-10 planning reports.
- This document does not claim to replace, recover, reproduce, or formally approve any earlier v0.1 artifact.
- It is not the final approved API contract or a canonical governance record.
- Proposed tests are distinguished from existing test evidence.
- No production implementation or deployment is authorized by this document.

## 1. Purpose, scope, and status

This is a planning-only outline for a possible mechanical dataset-validation API. The original reports identify validation as a technical candidate, not a selected or approved first use case. No API test suite is evidenced by these reports.

IMPLEMENTATION STATUS: NOT VERIFIED by this plan. Test execution status: NOT VERIFIED; no test result is claimed. The original reports describe test and acceptance matrices as proposed, not executed evidence.

## 2. Evidence labels and test boundaries

- SOURCE-SUPPORTED: capability or requirement stated in an original report.
- PROPOSED — PENDING APPROVAL: test idea or assertion not yet authorized as API behavior.
- UNRESOLVED / BLOCKED: final assertion depends on a missing contract, schema, policy, or authority.
- API layer: transport request/response behavior.
- Service layer: orchestration, schema resolution, engine mapping.
- Domain layer: engine behavior; domain tests are not HTTP tests.

The architecture proposal recommends separating transport, DTOs, application services, and engine logic. This is a proposal, not an implemented boundary. Source: Architecture Proposal §§3–5, 9.

## 3. Test scope and exclusions

Candidate scope is mechanical validation of caller-supplied records against a selected schema. The original route example is the placeholder POST /example-dataset-validation in Endpoint Requirements §5; it is not approved. Test naming or URL must wait for an approved route.

PROPOSED exclusions: NASA/archive access, scientific eligibility, physical correctness, model behavior, production deployment, and production authentication/authorization. Reports must not imply that a schema finding is scientific validation. Sources: Readiness Report §§8, 10; Endpoint Requirements §§7–8, 12.

Synthetic fixtures are a conservative test-design recommendation, not a source-established authorization. The original reports identify ARC-09 prototype values as synthetic/conceptual and not production data. Sources: Readiness Report §7; Endpoint Requirements §§2, 9. Do not present synthetic cases as NASA observations.

## 4. Test layers

| Layer | Candidate responsibilities | Readiness |
|---|---|---|
| DTO / request parsing | Candidate required/optional/null/type and malformed-body cases. | PROPOSED; exact DTO and transport rules unresolved. |
| Service / application | Candidate schema selection and explicit mapping to one engine capability. | PROPOSED; validator and catalog decisions unresolved. |
| Domain integration | Verify mapping without changing selected engine semantics. | PROPOSED; domain capability exists in source evidence, but API adapter is not approved. |
| HTTP integration | Verify approved route, method, statuses, and serialization. | BLOCKED until target, route, contract, and error mapping are approved. |
| Contract / compatibility | Verify fields, types, schema versions, and compatibility. | BLOCKED until authoritative versioned contract exists. |
| Security / operational | Verify approved limits, privacy/data handling, access controls, runtime behavior. | BLOCKED until requirements and authority are established. |

## 5. Proposed test groups and traceability

| Group | Candidate cases | Source traceability | Status |
|---|---|---|---|
| Request parsing | Valid shape; malformed JSON/top-level body; missing candidate members; wrong types; explicit null; unexpected members. | Endpoint Requirements §§5–6, 11; Implementation Plan §8. | PROPOSED; final DTO rules needed. |
| Schema selection | Exact supported pair; unknown ID/version; invalid identity syntax; no silent substitution. | Endpoint Requirements §§5–6, 13; Implementation Plan §§3, 5. | BLOCKED; no actual IDs, catalog, syntax, or lookup contract. |
| Structural validation | Conforming records; missing required fields; nullability; wrong types; multiple findings; preserve row positions. | Readiness Report §6; Endpoint Requirements §§3–5, 7, 11; Implementation Plan §§5, 8. | Domain capability is source-supported; API mapping remains proposed. |
| Empty input | Distinguish empty collection from malformed request and valid empty domain result. | Endpoint Requirements §§5, 11; Implementation Plan §§5, 8. | BLOCKED; reports require a decision but do not define behavior. |
| Report mapping | Map identity, counts, invalid indexes/issues; test message/code stability only when defined. | Endpoint Requirements §7.1; Readiness Report §6. | PROPOSED; index basis, codes, fields, and serialization unresolved. |
| Error mapping | Distinguish request errors, findings, unsupported schema, access, resource, upstream, and internal failures. | Endpoint Requirements §§8, 11; Architecture Proposal §9. | BLOCKED; status categories and envelope illustrative only. |
| Provenance | Test a later-approved caller-declaration mapping without treating it as authentication. | Readiness Report §§6, 10–11; Endpoint Requirements §§10, 13. | BLOCKED; wire fields, trust semantics, requiredness, and disclosure unresolved. |
| No mutation / serialization | Check no unexpected input change; verify representation after contract is defined. | Architecture Proposal §§5, 9; Implementation Plan §§4, 8. | PROPOSED; boundary and serialization contract undefined. |
| Quality analysis | If selected, ensure quality summaries remain distinct from structural validity. | Readiness Report §6; Endpoint Requirements §§3–4; Implementation Plan §5, Option B. | BLOCKED for inclusion; no approved operation includes it. |
| Security and privacy | Redaction, no secret/path/trace leakage, access boundaries, data handling. | Architecture Proposal §10; Endpoint Requirements §§8, 12; Implementation Plan §§3, 8, 10–12. | BLOCKED pending policy and authority. |
| Resource and reliability | Oversized payloads, depth, compute, timeout/cancellation/retry and long tasks. | Architecture Proposal §§10–11, 17; Endpoint Requirements §§10–12; Implementation Plan §§3, 8–9. | BLOCKED pending workload evidence and approved limits. |
| Frontend states | Loading, Success, Empty, Error; no synthetic fallback displayed as live. | Endpoint Requirements §9; Implementation Plan §§5, 8. | Conditional on confirmed production frontend and API contract. |

## 6. HTTP and status assertions

Endpoint Requirements §5 lists possible status categories as proposed alternatives; §8 gives an illustrative error envelope. Neither is approved.

This plan assigns no status codes to individual tests. HTTP assertions are BLOCKED until route/method, malformed/empty behavior, unsupported-schema behavior, error envelope, security behavior, and resource limits are approved in an authoritative contract.

## 7. D-01 through D-16 and numbering

The four original tracked reports contain no D-01 through D-16 register or status assignments. Every D reference remains unresolved here because primary-source evidence is insufficient. No topic mapping or approval is inferred.

D-04/D-05 numbering discrepancy: OPEN and not reconciled. This status is carried forward from the task context; the four primary source reports do not document or resolve it. No test asserts a numbering interpretation or treats this plan as a canonical register.

## 8. Prerequisites and acceptance criteria

Before API integration tests can be executable acceptance tests, the project needs:

- Confirmed implementation repository, owner, branch, and integration boundary.
- Selected use case/consumer and authoritative contract owner/location.
- Approved route/method, request/response DTO, schema identities and definitions.
- Selected engine capability and reviewed mapping.
- Defined empty/malformed/unsupported-schema/error behavior.
- Approved privacy, security, data-handling, resource, and operational constraints.
- Acceptance/review authority and measurable criteria.

Traceability: Readiness Report §§14–16; Implementation Plan §§3, 11–13. This summary does not claim any gate is approved.

## 9. Test data and execution status

PROPOSED: use synthetic records and test-only schema definitions for future isolated tests until actual schema identities and permissions are established. Do not invent production schema IDs or definitions.

The original reports provide no API implementation, API test files, or executed API test results at their inspection snapshots. No tests were executed for this document. Any ARC-08 tests referenced later must be described as domain tests, not HTTP/API acceptance evidence. Sources: Readiness Report §12; Implementation Plan §§2, 8.

## 10. Source traceability

Primary sources:

1. docs/ARC10_REPOSITORY_API_READINESS_REPORT.md — §§6, 8, 10–12, 14–17.
2. docs/ARC10_BACKEND_API_ARCHITECTURE_PROPOSAL.md — §§3–5, 8–11, 17–19.
3. docs/ARC10_API_ENDPOINT_REQUIREMENTS_AND_DRAFT_SCHEMAS.md — §§3–8, 10–15.
4. docs/ARC10_IMPLEMENTATION_PLAN_AND_TEST_STRATEGY.md — §§3–6, 8–13.

All test cases are proposed unless explicitly described as a source-supported domain capability. A test plan is not test evidence or approval.
