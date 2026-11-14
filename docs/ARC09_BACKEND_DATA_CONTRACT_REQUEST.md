# ARC-09 Backend Data Contract Request

**Project:** Quantum Space AGI — Space Mission Design Game
**Purpose:** Request the decisions and authoritative data contracts needed before ARC-09 frontend integration.

## 1. Project context

ARC-09 is responsible for visualization and frontend data presentation. The current dashboard in `arc09-ui-prototype/` is an isolated visual prototype. Its cards, activity, charts, and relationship graph use synthetic or conceptual examples; they do not define production requirements, backend fields, scientific values, or an approved data model.

This document requests integration requirements. It does not specify endpoints, HTTP methods, request/response schemas, or backend capabilities.

## 2. Initial integration scope

**Proposed P0 slice, pending product and backend approval:** connect one approved dashboard summary to the metric-card area. Confirm which summary content belongs in the initial release before implementation.

The integrated slice should present four distinct states:

- **Loading:** clearly indicate that the approved summary is being requested.
- **Success:** show only values supported by the confirmed contract, with approved labels, units, and provenance context.
- **Empty:** distinguish a valid response with no applicable summary data from an error.
- **Error:** explain that data could not be loaded and use only a team-approved recovery action or message.

The current prototype's state preview is static and makes no backend request. It is a visual reference only.

## 3. Component data requirements and priorities

Priorities below are planning recommendations, not approved product scope. P0 is conditional on the dashboard being selected for the initial release.

| Component | Priority | Contract information needed |
|---|---|---|
| Dashboard metrics | **P0, proposed** | Meaning and label for each metric; value type and nullability; stable mission/context identifiers; units or explicit unitless status; update/freshness meaning; provenance; formatting and validation rules. |
| Resource cards | **P1** | Resource identity and definition; amount type; unit; denominator and meaning for any percentage; limits or reference values if applicable; precision, freshness, provenance, and validation rules. |
| Recent activity | **P1** | Event identifier; title/action semantics; allowed status values; timestamp format and time zone; ordering; actor fields if shown; pagination and filtering rules; nullability and retention. |
| Line chart | **P1** | Series identity; x-axis meaning (step, time, or other); y-field definition; units; ordering; sampling and aggregation; gaps/nulls; precision, uncertainty, timestamps, provenance, and valid ranges. |
| Grouped bar chart | **P2** | Meaning and identity of each category and series; units; comparability; ordering; aggregation; nullability; precision, uncertainty, and validation rules. |
| Scatter chart | **P2** | Definitions and units for both axes; point identity; relationship between paired observations; coordinate conventions if applicable; uncertainty, filtering, missing values, and provenance. |
| Relationship graph | **P2; model-dependent** | Whether this visualization is a product requirement; entity definitions and stable IDs; edge meaning, direction, and cardinality; graph size/pagination; permissions; provenance and validation. The current concepts and links are placeholders, not a confirmed data model. |

For every component that is approved, confirm field definitions, data types, nullability, identifiers, units, validation, and error behavior; confirm timestamps, pagination, and filtering where applicable. No current prototype property name should be treated as a backend field name.

## 4. Backend contract questions

For the proposed dashboard summary and each approved component, please provide or identify:

1. The authoritative contract document and its version/status.
2. Field meanings, data types, optionality/nullability, and stable identifier semantics.
3. Units, formatting guidance, precision, timestamp format/time zone, and freshness semantics.
4. Pagination, sorting, filtering, and empty-result behavior where applicable.
5. Validation constraints and representative valid, empty, null, and invalid examples.
6. Error categories and their client-safe messages or recovery guidance.
7. Provenance and any access-control rules governing the data.

Endpoint URLs, HTTP methods, request structures, and response structures must come from the backend's authoritative documentation; they are intentionally not proposed here.

## 5. Scientific data requirements

For any scientific or simulation-derived information displayed, please confirm:

- Units and coordinate/reference-frame conventions.
- Precision, rounding, significant digits, and uncertainty representation.
- Data provenance and source/version traceability.
- Whether each value is measured, simulated, estimated, or assumed, and how that distinction is encoded.
- Applicable model assumptions and limitations that the UI must disclose.
- Authoritative validation examples, including expected invalid or incomplete cases.

ARC-09 will not infer these properties from labels, sample values, or chart ranges in the prototype.

## 6. Architecture dependencies

Before implementation, confirm:

- Official production frontend repository and working branch.
- Approved frontend framework, language, styling approach, package manager, and supported build/test commands.
- Backend repository/service and the responsible backend contact or role.
- API documentation location and contract ownership/versioning process.
- Authentication/session approach and authorization requirements.
- Environment-specific configuration mechanism and secret-handling rules.
- CORS and local-development expectations.
- Standard error, timeout, cancellation, retry, and logging conventions.

No frontend stack or deployment configuration is assumed by this request.

## 7. Integration acceptance criteria

The first dashboard-summary slice is ready for review when all applicable criteria below are met:

1. The production repository, approved stack, initial dashboard scope, and responsible reviewers are recorded.
2. The backend owner supplies an authoritative, versioned contract and representative examples for the selected summary.
3. Every displayed value maps to a documented field; labels, units, precision, provenance, and freshness follow the approved definitions.
4. Loading, success, valid-empty, and request-error states are distinguishable and do not present synthetic fallback values as live data.
5. Invalid or incomplete responses are handled according to the approved validation and error policy; no missing field is silently assigned a scientific meaning or value.
6. At team-agreed viewport sizes, important content and controls remain accessible, with no unintended clipping or horizontal overflow during each state; status/error information is available to keyboard and assistive-technology users.
7. Reviewers record each test case and its result for successful, empty, error, and invalid or malformed responses, using approved backend contract examples when available. Results distinguish checks performed from checks not run.
8. Backend and frontend reviewers accept the field mapping and user-visible behavior before the slice is expanded.

## 8. Ownership and pending decisions

Roles are intentionally generic. Assign named owners through the team's normal process; no individual responsibility or approval is implied here.

| Question | Responsible role | Decision required | Status |
|---|---|---|---|
| Which repository and branch are the production frontend target? | Product/engineering owner to be assigned | Confirm repository, branch, and initial integration location | Pending |
| Which frontend stack and development conventions are approved? | Frontend/engineering owner to be assigned | Confirm framework, language, package manager, configuration, and checks | Pending |
| Is the dashboard summary in the initial release, and which metrics are in scope? | Product owner to be assigned | Approve the P0 slice and metric definitions | Pending |
| Which backend service owns the summary and other approved data? | Backend owner to be assigned | Identify service, contract source, version, and contact | Pending |
| What are the exact contracts for approved components? | Backend owner to be assigned | Supply fields, types, nullability, IDs, timestamps, pagination/filtering, validation, and errors | Pending |
| What scientific definitions and provenance rules apply? | Scientific/data owner to be assigned | Confirm units, conventions, uncertainty, provenance, value categories, limitations, and examples | Pending |
| What authentication, environment, and CORS rules apply? | Backend/platform owner to be assigned | Document secure configuration and local-development behavior | Pending |
| What review and acceptance evidence is required? | Project reviewer/engineering owner to be assigned | Confirm reviewers and required checks for the first slice | Pending |
