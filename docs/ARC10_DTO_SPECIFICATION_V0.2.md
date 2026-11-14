# ARC-10 DTO Specification v0.2

DRAFT — NOT APPROVED
NON-CANONICAL WORKING DOCUMENT

- Version: 0.2
- Reconstructed working draft prepared from the four original tracked ARC-10 planning reports.
- This document does not claim to replace, recover, reproduce, or formally approve any earlier v0.1 artifact.
- It is not the final approved API contract or a canonical governance record.
- Proposed behavior is distinguished from implemented behavior.
- No production implementation or deployment is authorized by this document.

## 1. Purpose and scope

This document records conservative transport DTO concepts for capabilities discussed by the original ARC-10 reports. Dataset validation is an engineering candidate, not a selected product use case or approved MVP. No DTO is implemented or approved here.

The scope is the potential transport/domain boundary. It does not select a production repository, validator, schema catalog contents, API route, HTTP statuses, authentication, retention, or scientific policy.

## 2. Evidence labels

- SOURCE-SUPPORTED: stated or directly described in one of the four original tracked reports.
- PROPOSED — PENDING APPROVAL: illustrative or recommended only, not an adopted contract.
- UNRESOLVED / BLOCKED: the reports do not establish the decision.
- IMPLEMENTATION STATUS: NOT VERIFIED: these planning reports do not provide implementation or test execution evidence.

## 3. Domain and transport boundary

SOURCE-SUPPORTED: the reports describe ARC-08 as a separate reusable Python library with Dataset, Provenance, declarative schemas, validation, and quality capabilities; these are not HTTP APIs. References: Repository & API Readiness Report §§5–6, 8, 10; Endpoint Requirements §§2–3.

PROPOSED — PENDING APPROVAL: define transport DTOs separately from Python domain objects and map explicitly through an application/service boundary. Do not expose internal engine objects directly. References: Backend/API Architecture Proposal §§3–5, 9; Implementation Plan §§4, 8.

UNRESOLVED / BLOCKED: which domain validator the service would call, what provenance it requires, and how its report maps to a wire response.

## 4. Proposed request DTO concepts

The Endpoint Requirements report §6.1 gives an illustrative dataset-validation request with schema identity/version and records. The example is a placeholder, not a final request schema.

| Candidate member | Evidence and possible meaning | Type / requiredness / nullability |
|---|---|---|
| schema_id | PROPOSED — PENDING APPROVAL. Illustrative schema selector. Source: Endpoint Requirements §6.1. | UNRESOLVED. No approved wire type, grammar, requiredness, or null behavior. |
| schema_version | PROPOSED — PENDING APPROVAL. Illustrative version selector. Source: Endpoint Requirements §6.1. | UNRESOLVED. No approved wire type, grammar, requiredness, or null behavior. |
| records | PROPOSED — PENDING APPROVAL. Described conceptually as a JSON array of record objects. Sources: Endpoint Requirements §§5, 6.1. | UNRESOLVED. Exact JSON mapping, requiredness, null handling, unknown-field policy, and limits are not approved. |
| provenance | UNRESOLVED / BLOCKED. Reports identify provenance as a decision area, but the illustrative request says not to invent identity or provenance. Sources: Endpoint Requirements §§6.1, 10, 13; Readiness Report §§10–11. | No member, type, requiredness, or null rule is specified. |

Do not add defaults, schema IDs, definitions, record constraints, or provenance members without evidence and approval.

## 5. Proposed response DTO concepts

The Endpoint Requirements report §7.1 illustrates a validation response. This shape is PROPOSED — PENDING APPROVAL; the source explicitly leaves public names, index base, codes, and semantics unresolved.

| Candidate member | Evidence | Status / unresolved details |
|---|---|---|
| schema_id, schema_version | Illustrative response concepts; Endpoint Requirements §7.1. | Wire names, types, and catalog relationship unapproved. |
| record_count, valid_count | Illustrative integer placeholders; Endpoint Requirements §7.1. | Requiredness and response contract unapproved. |
| invalid_records | Illustrative collection containing record_index and issues; Endpoint Requirements §7.1. | Collection and serialization rules unapproved. |
| record_index | Illustrative integer placeholder; Endpoint Requirements §7.1. | Index base is explicitly unresolved. |
| issues.field | Illustrative string-or-null placeholder; Endpoint Requirements §7.1. | Nullability and field-reference rules unapproved. |
| issues.code | Illustrative stable-code placeholder; Endpoint Requirements §§7.1–8. | No public code registry is defined. |
| issues.message | Illustrative client-safe text; Endpoint Requirements §§7.1–8. | Exact content and stability rules unapproved. |
| scientific_eligibility | Example marker NOT_ASSESSED; Endpoint Requirements §7.1. | PROPOSED only; whether it belongs in a response is undecided. |

The reports describe the current SchemaValidationReport conceptually as including schema identity, counts, invalid indices, and issues; they do not authorize public serialization. References: Readiness Report §6; Endpoint Requirements §7.1.

## 6. Validation and serialization considerations

- PROPOSED — PENDING APPROVAL: keep transport parsing and approved type/nullability checks at the DTO boundary, then map explicitly to an engine input. Source: Architecture Proposal §§5, 9.
- SOURCE-SUPPORTED: scientific serialization would require decisions about units, frames where applicable, timestamps, precision, nullability, uncertainty, provenance, arrays, and non-finite values. Sources: Readiness Report §10; Endpoint Requirements §10.
- UNRESOLVED / BLOCKED: exact field types, coercion, extra-field handling, numeric constraints, resource limits, timestamp format, and array representation.
- PROPOSED — PENDING APPROVAL: avoid echoing input values or leaking sensitive payloads. Sources: Endpoint Requirements §8; Architecture Proposal §10.

## 7. Error and provenance representation

The error envelope in Endpoint Requirements §8 is ILLUSTRATIVE — NOT APPROVED. Its code, message, request identifier, details, and mappings remain undecided. This DTO draft assigns no HTTP status codes.

The original reports do not define an accepted provenance wire structure. Caller-supplied metadata must not be inferred to authenticate a source or authorize data use.

## 8. D-01 through D-16 references

The four original tracked reports contain no D-01 through D-16 register or status assignments. Each reference remains unresolved in this reconstructed draft; no topic mapping or approval is inferred.

| Reference | Status in this draft |
|---|---|
| D-01 | UNRESOLVED — SOURCE EVIDENCE INSUFFICIENT |
| D-02 | UNRESOLVED — SOURCE EVIDENCE INSUFFICIENT |
| D-03 | UNRESOLVED — SOURCE EVIDENCE INSUFFICIENT |
| D-04 | UNRESOLVED — SOURCE EVIDENCE INSUFFICIENT |
| D-05 | UNRESOLVED — SOURCE EVIDENCE INSUFFICIENT |
| D-06 | UNRESOLVED — SOURCE EVIDENCE INSUFFICIENT |
| D-07 | UNRESOLVED — SOURCE EVIDENCE INSUFFICIENT |
| D-08 | UNRESOLVED — SOURCE EVIDENCE INSUFFICIENT |
| D-09 | UNRESOLVED — SOURCE EVIDENCE INSUFFICIENT |
| D-10 | UNRESOLVED — SOURCE EVIDENCE INSUFFICIENT |
| D-11 | UNRESOLVED — SOURCE EVIDENCE INSUFFICIENT |
| D-12 | UNRESOLVED — SOURCE EVIDENCE INSUFFICIENT |
| D-13 | UNRESOLVED — SOURCE EVIDENCE INSUFFICIENT |
| D-14 | UNRESOLVED — SOURCE EVIDENCE INSUFFICIENT |
| D-15 | UNRESOLVED — SOURCE EVIDENCE INSUFFICIENT |
| D-16 | UNRESOLVED — SOURCE EVIDENCE INSUFFICIENT |

D-04/D-05 numbering discrepancy: OPEN and not reconciled here. This status is carried forward from the task context; the four primary source reports do not document or resolve it. The four primary source reports do not establish the canonical register, numbering, or resolution. This note preserves the discrepancy without assigning either reference a meaning.

## 9. Implementation status and blockers

IMPLEMENTATION STATUS: NOT VERIFIED by these reconstructed drafts. The original reports describe a planning/audit snapshot with no general-purpose backend or API implementation; see Readiness Report §§8, 12 and Implementation Plan §§1–3. No tests are claimed as executed.

Adoption requires a confirmed target and owner, authoritative contract process, selected use case and validator, schema definitions, wire-field decisions, error behavior, security/privacy rules, resource limits, and acceptance criteria. Sources: Readiness Report §§14–16; Implementation Plan §§3, 12–13.

## 10. Source traceability

Primary sources for this reconstruction:

1. docs/ARC10_REPOSITORY_API_READINESS_REPORT.md — §§5–6, 8, 10–12, 14–17.
2. docs/ARC10_BACKEND_API_ARCHITECTURE_PROPOSAL.md — §§3–5, 7–10, 17–19.
3. docs/ARC10_API_ENDPOINT_REQUIREMENTS_AND_DRAFT_SCHEMAS.md — §§3–8, 10–15.
4. docs/ARC10_IMPLEMENTATION_PLAN_AND_TEST_STRATEGY.md — §§3–4, 8, 11–13.

Section references identify source locations, not approvals.
