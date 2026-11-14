# ARC-10 Provenance Representation Proposal v0.1

**Version:** v0.1
**Status:** **PROPOSED — APPROVED IN PRINCIPLE, FINAL REPRESENTATION PENDING**
**API contract drafting:** APPROVED
**Final API contract:** PENDING
**Production implementation:** BLOCKED

The Project Owner decision of 13 November 2026 permits caller-declared provenance to be considered in principle, subject to explicit unverified labeling and separation from server-observed facts. This does not approve the exact wire representation proposed here. This document is a documentation-only proposal, not a canonical governance record, authentication design, final contract, or implementation authorization.

## 1. Purpose

Propose a representation for provenance concepts associated with `POST /api/v1/dataset-validations`. The design must preserve the distinction between:

1. **Caller-declared provenance:** information supplied by the caller, treated as **UNVERIFIED CALLER-SUPPLIED INFORMATION**.
2. **Server-observed request metadata:** facts observed by the service, such as request receipt time, labeled **OBSERVED BY SERVER**.
3. **Authenticated source evidence:** **NOT PROVIDED BY THIS API CONTRACT**.

No caller field authenticates the caller or dataset. No provenance claim is independently verified by the structural validation operation.

## 2. VERIFIED DOMAIN BEHAVIOR

The following fields and behavior were checked in the separate ARC-08 source checkout. They are domain fields, not automatically approved API properties.

| Type / field | Actual domain type and requiredness | Verified validation/meaning |
|---|---|---|
| `Dataset.provenance` | Required `Provenance` | Construction rejects values that are not `Provenance`. This verifies object structure only, not truth or authenticity. |
| `Dataset.records` | `Sequence[Record]` | Each record must be a mapping with string keys. |
| `Dataset.metadata` | `Mapping[str, object]`, optional with empty mapping default | Top-level mapping is copied and exposed read-only; no deep-copy guarantee is provided for nested objects. |
| `Provenance.dataset_id` | Required `str` | Must be non-empty text. It is an identifier declaration, not authentication or proof of ownership/origin. |
| `Provenance.source` | Required `DataSource` | Must be a `DataSource` instance. It does not authenticate the represented source. |
| `Provenance.retrieved_at` | Required `datetime` | Must be timezone-aware (`tzinfo` and `utcoffset()` present). It represents the provenance value supplied to the domain object; ARC-08 does not establish that the timestamp is true. |
| `Provenance.data_format` | Required `DataFormat` | Must be an enum instance; passing a string such as `"json"` directly is rejected. |
| `Provenance.dataset_version` | Optional `str \| None`, default `None` | If present, must be non-empty text. |
| `Provenance.transformations` | `tuple[str, ...]`, default empty tuple | Each item must be a non-empty string; construction stores a tuple. |
| `Provenance.metadata` | `Mapping[str, object]`, optional with empty mapping default | Must be a mapping; copied at top level and exposed read-only, not deeply frozen. |
| `DataSource.identifier` | Required `str` | Must be non-empty text. It is descriptive identity, not proof of source authenticity. |
| `DataSource.description` | Optional `str \| None` | If present, must be non-empty text. |
| `DataSource.url` | Optional `str \| None` | If present, must be non-empty text. A URL does not authenticate the source. |
| `DataSource.version` | Optional `str \| None` | If present, must be non-empty text. |
| `DataSource.metadata` | `Mapping[str, object]`, optional with empty mapping default | Must be a mapping; top-level copied and read-only, not deeply frozen. |
| `DataFormat.JSON` | Enum value `"json"` | Supported domain member. Wire encoding is not formally approved. |
| `DataFormat.CSV` | Enum value `"csv"` | Supported domain member. Wire encoding is not formally approved. |

Evidence: ARC-08 `src/quantum_space_agi/data/models.py`, `provenance.py`, and `sources.py`; focused tests in `tests/data/test_models.py`, `test_provenance.py`, and `test_sources.py`. These files are in the separate ARC-08 checkout and were not modified.

## 3. Trust Boundary

### A. Caller-declared provenance

The caller may supply claims describing dataset identity, source, retrieval time, format, and any explicitly supported optional metadata. Their trust classification is:

> **UNVERIFIED CALLER-SUPPLIED INFORMATION**

The API may validate the declaration's structure. Structural validity is not verification of its truth.

### B. Server-observed request metadata

The service may observe a request receipt timestamp. Its trust classification is:

> **OBSERVED BY SERVER**

This records when the service received a request. It says nothing about when the dataset was retrieved.

### C. Authenticated source evidence

> **NOT PROVIDED BY THIS API CONTRACT**

No authentication, attestation, signature checking, or source verification mechanism is designed here.

## 4. `retrieved_at` Semantics

`retrieved_at` means the caller-declared dataset retrieval timestamp. The API server:

- MUST NOT replace it with request receipt time.
- MUST NOT silently rewrite it.
- MUST NOT present request receipt time as dataset retrieval time.
- Does not independently establish that the caller's timestamp is correct.

An invalid or false caller declaration remains unverified even if it passes structural timestamp parsing. A future timestamp parser/DTO may reject malformed syntax, but that does not authenticate a syntactically valid timestamp.

## 5. Request Receipt Time

The concept `request_received_at` is a distinct server observation. The name is illustrative and remains a proposed wire name.

**Recommendation — PROPOSED, PENDING FINAL CONTRACT REVIEW:** keep receipt time internal to the request-processing context for the initial operation. Do not add it to the public success response unless an approved use case demonstrates a client need and privacy/operational review accepts the exposure. If later exposed, place it in a separate `server_observation` object, label it as observed by the API, and never map it into `Provenance.retrieved_at`.

Internal observation does not prescribe logging, retention, or persistence. Those policies are deferred and not specified here.

## 6. Proposed Wire Representation

The clearest conceptual shape separates caller declarations from server observations. All property names below are **PROPOSED API FIELDS**; they are not final wire names. Domain names are included where they correspond directly to verified ARC-08 fields.

### Proposed request concept

```json
{
  "provenance": {
    "caller_declared": {
      "dataset_id": "synthetic-dataset-001",
      "source": {
        "identifier": "synthetic-source",
        "description": "Synthetic source for documentation",
        "url": "https://source.example.invalid/catalog",
        "version": "example-version"
      },
      "retrieved_at": "2026-11-13T10:00:00Z",
      "data_format": "json"
    }
  }
}
```

This is conceptual and non-executable. `caller_declared` is a proposed wrapper that makes the trust boundary visible; `dataset_id`, `source.identifier`, `retrieved_at`, and `data_format` are candidate API names aligned to domain concepts. `source.description`, `source.url`, and `source.version` are optional candidates supported by `DataSource`. The timestamp syntax and enum serialization are proposals only. No real source, dataset, schema, or approved value is represented.

The API request must not accept a caller-supplied `server_observation` as if it were server-generated. Unknown or caller-supplied server-observation fields should not be trusted; exact request handling remains for final DTO review.

### Proposed server observation concept, only if later approved for exposure

```json
{
  "server_observation": {
    "request_received_at": "<server-observed timestamp; wire format pending>"
  }
}
```

This object is illustrative only. Recommendation is internal-only for v0.1, not response-visible. If response exposure is later approved, use a separate object and explicit server-observed semantics.

## 7. Dataset Identity

`Provenance.dataset_id` is an existing required domain field. The candidate API field `dataset_id` would carry the caller's declared dataset identity. It:

- Does not authenticate the caller or dataset.
- Does not prove ownership or control of the dataset.
- Does not prove NASA origin or source authenticity.
- Does not establish a globally unique identity guarantee; no such guarantee is established by the inspected model.

No new authentication identity field is proposed.

## 8. Source Representation

Verified `DataSource` fields are `identifier` (required), and optional `description`, `url`, `version`, and `metadata`. A corresponding source object is a **PROPOSED API representation**, not a direct public exposure of the domain dataclass.

| Candidate wire field | Existing domain field | Status / constraint |
|---|---|---|
| `source.identifier` | `DataSource.identifier` | PROPOSED mapping; caller declaration only; no authenticity implication. |
| `source.description` | `DataSource.description` | PROPOSED optional mapping; if included, ARC-08 requires non-empty text. |
| `source.url` | `DataSource.url` | PROPOSED optional mapping; a URL is not evidence of authenticity or authorization. |
| `source.version` | `DataSource.version` | PROPOSED optional mapping; if included, ARC-08 requires non-empty text. |
| `source.metadata` | `DataSource.metadata` | Domain supports an optional mapping, but arbitrary caller metadata is not recommended for the initial wire shape until purpose, privacy, and size behavior are reviewed. |

No additional source fields are inferred. How `source` maps to the required domain `DataSource` remains an adapter responsibility and is not implemented.

## 9. Data Format Representation

The existing `DataFormat` enum supports only `JSON = "json"` and `CSV = "csv"`. It is the required domain type for `Provenance.data_format`.

**PROPOSED — PENDING FINAL CONTRACT APPROVAL:** serialize a supported enum value using its lowercase string value (`"json"` or `"csv"`) to fit a JSON representation. An adapter would map an accepted wire value to the corresponding enum member. This is not yet a formal wire rule. No other format is supported by this proposal, and no unsupported-format behavior/status code is assigned here.

## 10. Timestamp Representation

ARC-08 requires `Provenance.retrieved_at` to be a timezone-aware Python `datetime`; a naive datetime is rejected. JSON has no native datetime type.

**PROPOSED:** use an ISO 8601-style timestamp string with an explicit UTC offset for caller-declared `retrieved_at`; if an API observation is later exposed, apply a reviewed serialization rule separately to `request_received_at`. The exact grammar, fractional-second precision, normalization policy, accepted offsets, and UTC rendering remain pending final contract approval. Parsing must preserve the semantic distinction between the two timestamps and must never rewrite one from the other.

## 11. Unverified Trust Semantics and Representation Options

Three options were reviewed:

| Option | Advantages | Disadvantages / trust risk | Contract complexity | ARC-08 fit | Status |
|---|---|---|---|---|---|
| A. Simple caller provenance object; trust meaning in documentation | Smallest shape; maps naturally to `Provenance` concepts. | When copied out of context, claims can be mistaken for verified facts; trust boundary is less visible. | Low | High conceptual fit; still needs adapter and timestamp/format mapping. | Considered; not recommended as the only signal. |
| B. Caller object plus explicit trust metadata, e.g. `trust_status: "unverified_caller_declared"` | Makes the unverified status machine-visible. | Adds a status property that could be mistaken for an authentication enum or later extended with misleading states; no enum is approved. | Medium | No direct ARC-08 field; adapter would add/handle metadata outside domain provenance. | PROPOSED alternative; requires review. |
| C. Caller-declaration section plus separate server-observation section | Separates who supplied a value from what the service observed; receipt time cannot be confused with dataset retrieval time by structure alone. | More verbose; receipt-time exposure can add privacy/operational questions if made public. | Medium | Caller section maps conceptually to `Provenance`; server observation remains outside it. | **Recommended PROPOSED option, pending final contract review.** |

**Recommendation:** use Option C's structural separation, with caller declarations explicitly labeled unverified in the contract and server observations kept internal-only initially. Do not add a trust enum for v0.1. If a future API needs a machine-readable trust property, treat `unverified_caller_declared` as a proposal requiring review; it must never imply a verified/authenticated alternative exists.

## 12. Server Observation Exposure

Receipt-time choices:

- **Response-visible:** improves transparency for a client but adds response fields and exposes a server observation. Not required by the supplied decision; requires contract, privacy, and operations review.
- **Internal-only:** keeps the first public response simpler and avoids implying the caller's retrieval time was checked. **Recommended for the initial draft**, pending final review. This does not authorize logging or retention.
- **Optional response metadata:** flexible but makes response shape conditional and may complicate clients. Not recommended until there is a concrete use case.

Regardless of placement, `request_received_at` describes only the server's request receipt. Security/operations are deferred, so no logging, retention, precision, or access policy is defined here.

## 13. Domain Mapping

No mapping below is implemented. “Transformation” describes the conceptual adapter operation only.

| API concept/field | ARC-08 domain field | Trust classification | Conceptual transformation | Status |
|---|---|---|---|---|
| `caller_declared.dataset_id` | `Provenance.dataset_id` | Caller-declared, unverified | Preserve text; domain requires non-empty text. | Domain field VERIFIED; API field PROPOSED |
| `caller_declared.source.identifier` | `Provenance.source.identifier` via `DataSource` | Caller-declared, unverified | Construct a `DataSource` only after reviewed wire validation; non-empty identifier required by domain. | Domain field VERIFIED; API mapping PROPOSED |
| Optional source description/url/version | Corresponding optional `DataSource` fields | Caller-declared, unverified | Preserve only if included and approved; no identity/authentication inference. | Domain fields VERIFIED; API mapping PROPOSED |
| `caller_declared.retrieved_at` | `Provenance.retrieved_at` | Caller-declared, unverified | Parse reviewed timezone-aware timestamp syntax; do not replace or rewrite with receipt time. | Domain field/rule VERIFIED; wire syntax PROPOSED/PENDING |
| `caller_declared.data_format` | `Provenance.data_format` | Caller-declared, unverified | Map only a reviewed representation of `DataFormat.JSON` or `.CSV` to enum; exact encoding pending. | Domain values VERIFIED; wire mapping PROPOSED/PENDING |
| Optional dataset version, transformations, provenance metadata | `Provenance.dataset_version`, `.transformations`, `.metadata` | Caller-declared if accepted | Optional mapping only after field policy is reviewed; no arbitrary metadata assumptions. | Domain fields VERIFIED; wire inclusion PENDING |
| Server request receipt time | No corresponding `Provenance` field | Observed by server | Capture separately if required; keep outside caller provenance and initially internal-only by recommendation. | Concept VERIFIED as future service observation; API exposure PENDING |
| Trust/authentication result | No corresponding authenticated field | Not provided | No transformation; this API defines no source authentication. | NOT PROVIDED |

## 14. Provenance Completeness Recommendation

The ARC-08 `Dataset` constructor requires a `Provenance` object. `Provenance` in turn requires `dataset_id`, `source`, timezone-aware `retrieved_at`, and `data_format`.

**Recommendation — PROPOSED, PENDING FINAL API CONTRACT APPROVAL:** if the ARC-10 service selects the Dataset-based schema validator, require truthful caller declarations corresponding to all four required domain components, represented as unverified. This aligns with the existing constructor and avoids fabricating missing values. This is not an approved API requiredness rule. If the service chooses a different validator/input boundary, these domain requirements may not apply; that choice requires an explicit contract decision.

Optional domain fields (`dataset_version`, `transformations`, metadata, and optional `DataSource` fields) should not be required by this proposal. Including arbitrary metadata in the initial public request is not recommended until its purpose and privacy/size handling are reviewed.

## 15. Missing or Invalid Provenance

The table distinguishes domain checks from future request handling. No HTTP status is assigned here beyond the already authorized generic malformed-request behavior; exact provenance error mapping belongs in the separate error/HTTP mapping deliverable.

| Case | Existing domain concern | Conceptual API treatment | Final mapping status |
|---|---|---|---|
| Missing top-level provenance | `Dataset` requires a `Provenance` instance. | If the selected API path requires the Dataset-based validator, treat absent provenance as malformed/incomplete request rather than fabricate it. | Requiredness and exact error body/status pending contract review. |
| Missing required component (`dataset_id`, `source`, `retrieved_at`, `data_format`) | `Provenance` constructor requires each component. | Reject before domain construction if the selected mapping requires all four. | API classification and exact response mapping pending. |
| Naive or malformed timestamp | Domain rejects a naive `datetime`; transport parser syntax is not defined by ARC-08. | Do not substitute request receipt time. Reject a value that cannot produce an allowed timezone-aware datetime. | Parser/format and API error mapping pending. |
| Invalid source representation | Domain requires a `DataSource`; source identifier must be non-empty; optional descriptive text if provided must also be non-empty. | Reject malformed source structure; do not infer/authenticate source from URL or identifier. | API validation details/status pending. |
| Invalid/unsupported format | Domain requires a `DataFormat` enum instance; only JSON and CSV members exist. | Reject unrecognized format rather than silently coerce or add a format. | Exact wire values and HTTP/error mapping pending. |
| Empty dataset identity | Domain rejects empty/whitespace `dataset_id`. | Treat as invalid declared provenance if that value is required for the chosen path. | API error classification/status pending. |

These are structural mappings only. The eventual DTO layer must keep record-level schema findings separate from request/provenance parsing failures under the approved contract.

## 16. Provenance Is Not Authentication

- Provenance is not authentication.
- A caller-declared source does not authenticate the caller.
- A caller-declared dataset identity does not authenticate the dataset or prove ownership.
- A URL does not authenticate a source.
- `retrieved_at` does not prove that retrieval occurred at that time.
- Server receipt time proves only that the service observed receipt of a request at that time.

No authentication mechanism is designed or authorized by this proposal.

## 17. Provenance Is Not Scientific Validity

Valid provenance structure does not establish scientific correctness, scientific eligibility, physical validity, NASA authenticity, or authenticity of scientific provenance. This API remains mechanical structural validation only.

## 18. Provenance Is Not Data-Rights Authorization

Provenance fields do not establish ownership, licensing rights, data-use authorization, NASA data rights, or publication rights. No data-rights decision is made here.

## 19. Security Boundary

Security requirements are **DEFERRED**. This proposal does not define authentication, authorization, CORS, encryption policy, retention, logging policy, or secrets management. These concerns intersect with provenance because caller-declared source information, URLs, timestamps, metadata, and server receipt observations may be sensitive or misleading if disclosed or retained without an approved policy. No handling policy is inferred here.

## 20. Synthetic Examples

All values below are synthetic and are not NASA data, real personal data, approved schema values, or executable API examples. The illustrative field names are proposals pending review.

### A. Complete caller-declared provenance

```json
{
  "provenance": {
    "caller_declared": {
      "dataset_id": "synthetic-dataset-001",
      "source": {
        "identifier": "synthetic-source",
        "description": "Synthetic source for documentation",
        "url": "https://source.example.invalid/catalog",
        "version": "example-version"
      },
      "retrieved_at": "2026-11-13T10:00:00Z",
      "data_format": "json"
    }
  }
}
```

The timestamp syntax and format encoding are proposals, not final rules. All claims remain unverified.

### B. Caller declaration plus separate server observation

```json
{
  "caller_declared": {
    "dataset_id": "synthetic-dataset-002",
    "retrieved_at": "2026-11-13T09:45:00Z"
  },
  "server_observation": {
    "request_received_at": "2026-11-13T10:00:00Z"
  }
}
```

This illustrates semantic separation only; recommendation is to keep server observation internal for the initial response. The two times must not be substituted for one another.

### C. Missing `retrieved_at`

```json
{
  "provenance": {
    "caller_declared": {
      "dataset_id": "synthetic-dataset-003",
      "source": {"identifier": "synthetic-source"},
      "data_format": "json"
    }
  }
}
```

If the Dataset-based domain path is selected and all required components are required by the approved API contract, this is incomplete. Exact API error mapping is pending.

### D. Invalid timestamp

```json
{
  "provenance": {
    "caller_declared": {
      "dataset_id": "synthetic-dataset-004",
      "source": {"identifier": "synthetic-source"},
      "retrieved_at": "not-a-timestamp",
      "data_format": "json"
    }
  }
}
```

This synthetic value is illustrative of a parse failure; no final parser grammar/status is assigned.

### E. Unknown/unsupported format

```json
{
  "provenance": {
    "caller_declared": {
      "dataset_id": "synthetic-dataset-005",
      "source": {"identifier": "synthetic-source"},
      "retrieved_at": "2026-11-13T10:00:00Z",
      "data_format": "parquet"
    }
  }
}
```

`parquet` is an intentionally unsupported illustrative value, not a supported ARC-08 format. The domain enum currently defines JSON and CSV only. API behavior for an unrecognized value remains pending.

### F. Explicitly unverified caller declaration

```json
{
  "provenance": {
    "caller_declared": {
      "dataset_id": "synthetic-dataset-006",
      "source": {"identifier": "synthetic-source"}
    },
    "trust_notice": "UNVERIFIED CALLER-SUPPLIED INFORMATION"
  }
}
```

`trust_notice` is an illustrative proposed property, not an approved field or enum. Documentation may instead make the trust meaning explicit without a machine-readable property.

## 21. Representation Options and Recommendation

Options A–C and their tradeoffs are compared in Section 11. The recommendation is:

> **PROPOSED — PENDING FINAL API CONTRACT APPROVAL**

Prefer a distinct caller-declaration structure and a separate server-observation structure, with the latter internal-only for the first operation. Use documentation to label caller values unverified. Do not add an authentication claim or formal trust enum in v0.1. Require the four caller declarations needed to construct ARC-08 `Provenance` only if the final design selects the Dataset-based validator; this remains a proposal, not an approved API requiredness rule.

## 22. Open Decisions

- Exact wire field names and nesting.
- Trust metadata representation, if any.
- Whether server request receipt time is exposed or remains internal.
- Timestamp serialization grammar, precision, and normalization.
- `DataSource` wire shape and optional metadata policy.
- `DataFormat` wire values and mapping.
- Whether caller provenance is required in the final API and which validator/input boundary is selected.
- Missing/invalid provenance HTTP mapping.
- Final error envelope.
- Authentication and authorization.
- Security/operational requirements, including privacy and retention/logging.
- Canonical contract location and final contract approval authority.
- Production target/integration boundary and authorization.

## 23. Approval Status

| Item | Status | Boundary |
|---|---|---|
| Caller-declared provenance | **APPROVED IN PRINCIPLE** | Only if explicitly marked unverified caller-supplied information. |
| Exact wire representation | **PROPOSED / PENDING** | This proposal is not final. |
| ARC-03 model changes | **NOT AUTHORIZED / NONE** | No changes are requested or made. |
| Authentication | **DEFERRED** | No authentication mechanism designed. |
| Security/operations | **DEFERRED** | Relevant authorities and policies remain unresolved. |
| Final API contract | **PENDING** | Final review/approval remains outstanding. |
| Production implementation | **BLOCKED** | No implementation authorization. |
| Canonical contract location | **PENDING** | Not designated. |

## 24. Decision Traceability

| Request ID | Provenance proposal treatment |
|---|---|
| REQ-ARC10-02 — Provenance policy | Sections 3–5, 8–15 preserve unverified caller declarations and keep `retrieved_at` distinct from server receipt time. |
| REQ-ARC10-04 — Contract ownership/location | Header/status retains unresolved authority and non-canonical boundary; no D-number changes. |
| REQ-ARC10-06 — Security/operations | Section 19 records deferred status without inventing policy. |
| REQ-ARC10-07 — API behavior | This proposal is scoped to the drafted validation operation and does not change its authorized status behavior. |

References: `docs/ARC10_API_CONTRACT_V0.1.md`, `docs/ARC10_DTO_SPECIFICATION_V0.1.md`, and `docs/ARC10_ARCHITECTURE_DECISION_RECORD_V0.1.md`. REQ identifiers are request-local, not D-01–D-16 assignments.

## 25. Next Step

**Next authorized deliverable:** Static Schema Catalog Design.

This remains documentation-only. Do not create or implement catalog schemas, DTOs, authentication, API code, or ARC-03/ARC-08 changes. Final representation, contract approval, security/operations, target selection, and production authorization remain pending or blocked as described above.
