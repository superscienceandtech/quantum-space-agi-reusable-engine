# ARC-10 Static Schema Catalog Design v0.1

**Status:** **PROPOSED — INTERNAL DESIGN**
**Schema content and identifiers:** **NOT YET APPROVED**
**Catalog design direction:** APPROVED WITH CONDITIONS under REQ-ARC10-03
**Final API contract:** PENDING
**Production implementation:** BLOCKED

This is a documentation-only design. It is not a canonical governance record, final API contract, approval to implement production functionality, or approval of any actual schema ID or schema version. No schema entries or definitions are created here.

## A. Purpose and Scope

ARC-10's drafted first operation, `POST /api/v1/dataset-validations`, needs a deterministic way to resolve a caller-selected schema without allowing callers to define the rules applied to their own records. A static, read-only allowlist is intended to provide that selection boundary: each request names a schema ID and version, and the service resolves exactly that reviewed entry before invoking the selected structural validator.

The design covers catalog lookup, entry metadata, lifecycle/review concepts, mapping to ARC-08 `DataSchema`, and proposed checks. It does not select actual schemas, define their scientific content, implement a registry, or approve an HTTP error envelope/status for unknown schemas.

Outside scope: arbitrary caller-defined schemas, scientific eligibility or physical constraints, NASA data access, authentication, data-rights authorization, deployment, persistence beyond the catalog's eventual static representation, and changes to ARC-03 or ARC-08.

## B. Decision and Approval Context

REQ-ARC10-03 is **APPROVE WITH CONDITIONS**. The supplied Project Owner decision authorizes preparation of a static, read-only schema allowlist design subject to these constraints:

1. Schema IDs and versions must be explicitly reviewed.
2. Released schema versions are immutable.
3. Ownership and review responsibilities must be documented.
4. Unknown schema IDs and versions are explicitly rejected.
5. Arbitrary caller-defined schemas are unsupported in the initial release.
6. No actual schema ID or schema content is approved by that decision.

These approved design constraints must be distinguished from the following:

- **Proposed technical recommendations:** data structures, ID/version naming principles, lifecycle states, load/lookup behavior, and testing strategy in this document.
- **Unresolved schema-content decisions:** actual identifiers, versions, fields, Python type mappings, requiredness, nullability, and any domain-specific semantics.
- **Final approval requirements:** approval authority, catalog custodian, reviewers, release process, canonical catalog location, and final API error mapping.

No recommendation below upgrades an item to approved. Request-local REQ identifiers do not alter or resolve D-01–D-16 or the open D-04/D-05 discrepancy.

## C. Verified ARC-08 Schema Capabilities

The following facts were verified against the separate ARC-08 checkout at `arc/08-ai-ml`, HEAD `de48b077571fe44b1fc8b7ab8fad6ba60016f029`. These domain facts are not the proposed catalog design.

| ARC-08 type/function | Verified behavior |
|---|---|
| `DataSchema` | Frozen dataclass in `src/quantum_space_agi/data/schemas.py` with `identifier: str`, `version: str`, and `fields: tuple[FieldSchema, ...]`. It requires non-empty identifier/version, stores fields as a tuple, requires `FieldSchema` entries, and rejects duplicate field names. |
| `FieldSchema` | Frozen dataclass with `name: str`, `value_type: type[object]`, `required: bool = True`, and `allow_none: bool = False`. Field name must be non-empty, `value_type` must be a Python type, and flags must be booleans. |
| `validate_dataset(dataset, schema)` | Checks only declared field presence, nullability, and exact Python type (`type(value) is field.value_type`). Missing required, forbidden null, and wrong type are reported as issues (`missing`, `null`, `type`). Missing optional fields are allowed. No coercion or row dropping is performed. Undeclared input keys are not checked or rejected by this function. |
| `SchemaValidationReport` | Frozen report with `schema_id`, `schema_version`, `record_count`, `valid_count`, and tuple `invalid_records`. Its `is_valid` property is derived from whether `invalid_records` is empty. |
| `InvalidRecord` / `ValidationIssue` | Invalid record contains a zero-based `record_index` and tuple of issues. Each issue contains `field`, `code`, and `message`. |
| Empty dataset | The schema-based validator returns `record_count=0`, `valid_count=0`, no invalid records, and `is_valid=True`. This is domain behavior. The ARC-10 API drafting direction separately assigns HTTP 422 to empty `records`; it does not change ARC-08. |
| Dataset/provenance dependency | `validate_dataset` requires a `Dataset`, whose constructor requires `Provenance`. The catalog alone does not resolve the API's provenance-to-domain mapping. |

Evidence: `src/quantum_space_agi/data/schemas.py`, `models.py`, and `provenance.py`; relevant existing tests: `tests/data/test_schemas.py`, `test_models.py`, and `test_provenance.py`. No tests were run for this documentation task.

Limitations relevant to an API catalog: `DataSchema` represents basic Python-type/presence/nullability rules. It is not a general JSON Schema document or a domain-specific scientific rule engine. Its `value_type` is a Python type and requires an explicit transport-to-Python mapping. The current model does not carry display descriptions, review approvals, lifecycle state, compatibility notes, or ownership metadata.

## D. Catalog Architecture (Proposed)

**PROPOSED:** use a static, server-controlled catalog keyed by the exact pair `(schema_id, schema_version)`. It should be immutable to request handlers after the reviewed catalog snapshot is loaded. A request supplies identifiers only; it cannot add, replace, mutate, or register catalog entries.

Conceptual lookup flow:

1. Receive `schema_id` and `schema_version` from the request DTO.
2. Perform exact lookup of the pair in the loaded allowlist.
3. Confirm that the exact entry is in the approved/released state for the serving catalog snapshot.
4. Return that entry's reviewed definition or reject the request explicitly.
5. Never select “latest”, nearest, default, or compatible version implicitly.

A deterministic in-memory lookup after startup is the preferred technical shape because it avoids request-time catalog mutation and makes the selected pair explicit. Whether entries are packaged as source data or loaded from an approved artifact at startup is unresolved until the implementation target, packaging, and deployment boundary are known. No filesystem scanning, mutable administrative endpoint, runtime registration, or network fetch is proposed.

## E. Proposed Catalog Entry Metadata

The following is a conceptual entry model, not an approved DTO, persisted format, or schema definition. No values are assigned. “Required/optional/unresolved” applies to the proposed metadata design only.

| Proposed field | Purpose | Proposed presence | Status / unresolved point |
|---|---|---|---|
| `schema_id` | Stable key identifying a schema family. | Required for an entry. | PROPOSED; naming grammar and actual IDs require review. |
| `schema_version` | Identifies one immutable definition within the schema family. | Required for an entry. | PROPOSED; exact version syntax and values require review. |
| `display_name` | Human-readable catalog label. | Optional. | PROPOSED; no name assigned. |
| `description` | States the schema's intended structural scope and known exclusions. | Optional, but recommended before release. | PROPOSED; wording requires schema owner/reviewer. |
| `schema_definition_reference` | Links the entry to the exact reviewed definition or source artifact. | Required for traceable release in principle. | PROPOSED; reference format, storage, and canonical location unresolved. It must not be an unverified path that changes after release. |
| `lifecycle_status` | Indicates draft/review/release/deprecation state. | Required for governance tracking; serving behavior must accept only released entries. | PROPOSED lifecycle in Section I; exact enum and transitions unapproved. |
| `compatibility_notes` | Explains changes, compatibility expectations, and replacement versions. | Optional for early drafts; required when a version changes/deprecates another. | PROPOSED; compatibility policy pending. |
| `review_status` | Records whether required review evidence is complete. | Required before release. | PROPOSED; criteria and authoritative evidence location unresolved. |
| `owner_role` | Identifies the accountable schema stewardship role. | Required before release; role assignment unresolved. | PROPOSED role field; do not populate with an unassigned person. |
| `reviewer_role` | Identifies required review role(s), including domain review when schema semantics warrant it. | Required before release; assignment unresolved. | PROPOSED role field; names and authority not established. |
| `release_date` | Records when an approved version was released. | Optional until release; required after release if the governance process adopts it. | PROPOSED; date format and authority source pending. |
| `approval_reference` | Points to recorded approval evidence for the exact schema/version. | Required before release. | PROPOSED; canonical decision/evidence system and reference format unresolved. |
| `definition_checksum` | Detects accidental changes to the released definition. | Optional technical safeguard; recommended if a stable canonical byte representation is established. | PROPOSED only; checksum does not prove approval, authenticity, or scientific correctness. Canonical serialization and retention are unresolved. |

No actual `schema_id`, `schema_version`, field list, owner, reviewer, release date, approval reference, or checksum is populated or approved in this design.

## F. Schema Definition Mapping

A reviewed catalog entry could map its structural definition to ARC-08 `DataSchema` as follows:

| Catalog definition concept | ARC-08 domain mapping | Status/limitation |
|---|---|---|
| Schema identifier | `DataSchema.identifier` | Direct conceptual mapping. Actual value not approved. |
| Schema version | `DataSchema.version` | Direct conceptual mapping. Exact version policy not approved. |
| Field name | `FieldSchema.name` | Direct mapping for a reviewed field. No fields are defined here. |
| Expected type | `FieldSchema.value_type` (Python type) | Requires a reviewed mapping from wire/definition type to Python type. No universal mapping is established here. |
| Requiredness | `FieldSchema.required` | Direct mapping for basic presence rules. |
| Nullability | `FieldSchema.allow_none` | Direct mapping for explicit `None` behavior. |
| Display name, description, lifecycle, review/owner data, compatibility, release/approval references | No corresponding fields in `DataSchema` | Catalog governance metadata must remain separate from the domain schema unless future approved model changes are made outside this scope. |
| Scientific units, limits, eligibility, or physical rules | Not represented by these basic `FieldSchema` fields | Requires separate authoritative domain/scientific decisions; must not be silently added as structural rules. |

The existing ARC-08 model appears sufficient for simple structural schemas expressible as field name, Python type, requiredness, and nullability. It is not sufficient by itself for a richer external schema language or scientific semantics. Any translation beyond these direct concepts is unresolved and must be explicitly designed and reviewed. This proposal does not modify ARC-08.

## G. Schema ID and Version Policy (Proposed)

All policy in this section is a recommendation, not an approved naming/versioning standard.

- **Identifier principles:** use stable, human-auditable identifiers scoped to a documented schema family; avoid identifiers whose meaning changes over time. Grammar, case sensitivity, namespace, and length remain pending. Do not publish illustrative examples as real IDs.
- **Version format:** use an opaque exact-match version string in the catalog and request. A constrained numeric `MAJOR.MINOR[.PATCH]` format may be considered for readability, but is **PROPOSED**, not selected; do not assume semantic compatibility from the string alone. No concrete version is assigned.
- **Exact-match lookup:** resolve only the exact `(schema_id, schema_version)` pair. No aliasing, version ranges, “latest”, implicit default, or fallback.
- **Unknown ID/version:** explicitly reject. Distinguish unknown ID from known ID with unknown version in internal diagnostics if useful; public status/code remains subject to final error mapping.
- **Released immutability:** never edit the definition or meaning of a released pair in place. Corrections or rule changes require review and a new version; prior released versions remain available only according to an approved support/deprecation policy.
- **Compatibility:** do not infer that a version is backward-compatible. Compatibility notes and any compatibility guarantee require review and approval.
- **Deprecation/retirement:** a future policy may mark versions deprecated before retirement and define support windows. Unknown/retired behavior must remain explicit and must not silently select a replacement. Exact behavior and timelines remain unresolved.

## H. Unknown and Unsupported Schema Behavior

The following behavior is required by the Project Owner's conditional catalog decision and contract-drafting direction:

- Unknown schema ID: explicit rejection; no silent fallback.
- Known ID with unknown/unsupported version: explicit rejection; do not select another version.
- Caller-supplied schema definition: not accepted in the initial release.
- Dynamic caller registration: unsupported.
- Automatic schema inference: not proposed.

The exact HTTP status, error code, and final error body remain subject to the API error/HTTP mapping deliverable and final contract review. This design does not assign them.

## I. Catalog Governance and Review Lifecycle (Proposed)

The following lifecycle is a proposal only; no roles or authorities have been formally assigned by this document.

`DRAFT → UNDER_REVIEW → APPROVED_FOR_RELEASE → RELEASED → DEPRECATED → RETIRED`

Possible role responsibilities, pending assignment:

- **Proposer:** prepares a definition, intended scope, field rationale, and change description.
- **Technical schema reviewer:** checks internal consistency, type mapping, required/null behavior, and compatibility notes.
- **Domain/scientific reviewer:** reviews scientific semantics only when present; no such authority is identified here.
- **Catalog custodian:** maintains the static allowlist and verifies metadata/approval references; role is not assigned.
- **Release approver:** records authorization to release the exact immutable ID/version; authority is not identified.

Proposed controls:

1. A candidate starts as DRAFT and is not resolvable by production requests.
2. Review records identify the exact definition/version reviewed and unresolved comments.
3. Release requires recorded approval evidence, documented owner/reviewer responsibilities, and a stable definition reference.
4. Released bytes/meaning are immutable; any change follows review as a new version.
5. A change proposal records its predecessor and compatibility/deprecation consequences, without changing the predecessor.
6. Deprecation/retirement requires an explicit policy and must never trigger silent version substitution.

Approval references must point to the project-designated source of record once identified. The canonical governance register and designating authority remain unresolved; this document cannot designate them.

## J. API Integration Behavior (Conceptual)

1. Receive the dataset-validation request.
2. Read the proposed `schema_id` and `schema_version` fields; final DTO details remain subject to contract review.
3. Resolve the exact pair from the approved static, read-only catalog.
4. Reject unknown/unreleased pairs explicitly, without fallback.
5. Map the reviewed definition to ARC-08 `DataSchema` only for concepts the domain model supports.
6. Invoke the selected existing structural validation capability if the final target/provenance/validator decisions permit it.
7. Map the resulting `SchemaValidationReport` to the API response under the final contract.

This is not implemented. API target, catalog placement, provenance mapping, error response, and final contract are unresolved. No route or wire field is made final here.

## K. Security and Trust Boundaries

A server-controlled static allowlist limits the rules a caller can select to definitions reviewed and released by the project. Rejecting arbitrary caller schemas prevents requesters from redefining the validation rules applied to their own records. Exact lookup also reduces accidental rule substitution.

Catalog approval metadata does not authenticate a dataset or caller. A schema match and successful structural report do not prove scientific validity, NASA authenticity, source authenticity, physical plausibility, ownership, or data-rights authorization. Security/authentication and operational policies remain deferred; no access control, logging, retention, or deployment policy is designed here.

## L. Testing and Acceptance Criteria (Proposed)

These are planned tests, not implemented or executed tests.

### Unit tests

- Exact known `(schema_id, schema_version)` returns that entry only.
- Unknown ID is rejected.
- Known ID with unknown version is rejected.
- No fallback to default/latest/nearest version occurs.
- Released entry data cannot be mutated through the catalog lookup interface.
- Duplicate `(schema_id, schema_version)` entries are rejected when constructing/validating a catalog snapshot.
- Repeated exact lookup is deterministic.
- Request input cannot register or replace a catalog entry.
- Caller-defined schema payload is rejected at the service boundary.
- Catalog definition maps only supported field name/type/required/nullability concepts into `DataSchema`.
- Domain schema findings preserve missing/null/type issue behavior and zero-based indices.
- Empty `Dataset` keeps verified ARC-08 behavior: zero counts, no invalid rows, `is_valid=True`.

### Integration tests

- Supported catalog pair resolves and invokes the selected schema-based validator once the final service adapter is approved.
- Unknown ID/version returns the final approved explicit error without invoking validation; exact HTTP mapping waits for contract approval.
- Validation findings return the report per approved contract; no coercion or record dropping.
- Empty API `records` returns HTTP 422 per contract-drafting authorization, without changing ARC-08 empty-domain behavior.
- No filesystem/network lookup or runtime catalog mutation occurs if static in-process design is adopted.

### Governance/documentation checks

- No released catalog entry exists without exact schema/version review evidence and assigned governance roles.
- A released entry's definition and meaning are immutable; change proposals use a new version.
- No actual schema IDs/contents are described as approved before an authoritative review record exists.
- Catalog docs distinguish structural validation from scientific approval and source authentication.
- Unknown and retired entries have documented handling with no implicit substitution.

No test results are claimed.

## M. Open Decisions and Dependencies

- Actual first-release schema IDs and versions.
- Actual schema definitions and field-level constraints.
- Field-level scientific semantics, units, limits, and any domain validation requirements.
- Authority that approves schema contents and the evidence format/location for that approval.
- Catalog owner/custodian and reviewer assignments.
- Canonical catalog location and immutable artifact representation.
- Final API error mapping for unknown, unsupported, deprecated, or retired schemas.
- Final request DTO and exact `schema_id`/`schema_version` wire constraints.
- Production implementation target repository, owner, branch, and integration boundary.
- Security and operational approval, including resource limits and deployment requirements.
- Final API contract approval and canonical contract location.
- Canonical governance register designation and D-04/D-05 resolution remain open; this document does not change numbering.

## N. Approval Status

| Item | Status | Qualification |
|---|---|---|
| Static read-only allowlist direction | **APPROVED WITH CONDITIONS** | Catalog design direction only, under REQ-ARC10-03. |
| Actual schema IDs | **NOT APPROVED** | None assigned or represented here. |
| Actual schema content | **NOT APPROVED** | No definitions created or approved. |
| Catalog metadata representation | **PROPOSED** | Conceptual metadata only; wire/storage representation pending. |
| Governance lifecycle | **PROPOSED** | Roles and authority assignments remain unresolved. |
| Final API contract | **PENDING** | Contract v0.1 remains a draft. |
| Production implementation | **BLOCKED** | No implementation authorization or confirmed target. |

## O. Traceability

| Decision/reference | Treatment in this design |
|---|---|
| REQ-ARC10-03 | Static read-only allowlist; reviewed IDs/versions; immutable releases; documented responsibilities; explicit unknown rejection; no caller-defined initial schemas. No actual IDs/content approved. |
| REQ-ARC10-05 | Consistent with provisional internal Modular Monolith/FastAPI/Uvicorn/Python direction; does not select a target or authorize implementation. |
| REQ-ARC10-07 | Catalog lookup supports the drafted `POST /api/v1/dataset-validations`; unknown schema is an explicit error with status pending final mapping. |
| `docs/ARC10_ARCHITECTURE_DECISION_RECORD_V0.1.md` | Internal architecture direction and implementation boundaries. |
| `docs/ARC10_API_CONTRACT_V0.1.md` | Draft endpoint, schema selection, unknown-schema behavior, and approval limits. |
| `docs/ARC10_DTO_SPECIFICATION_V0.1.md` | Proposed request schema ID/version fields and unresolved DTO details. |
| `docs/ARC10_PROVENANCE_REPRESENTATION_PROPOSAL_V0.1.md` | Provenance and trust boundaries; no catalog authentication implication. |

REQ identifiers are request-local, not D-01–D-16 assignments. The local decision package remains non-canonical. D-04/D-05 remains open.
