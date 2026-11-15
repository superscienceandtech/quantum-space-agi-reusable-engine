# ARC-09 Contract-Independent Readiness Checklist

**Status basis:** 2026-11-15 audit of local repository evidence. The local
educational mission demo is not the authoritative ARC-10 production contract.
“Owner” below means the role assigned in the Project Owner's task; it does not
assert additional decision authority. Project Owner / maintainer approval is
required where noted.

| # | Readiness item | Required evidence | Responsible owner | Dependency | Acceptance criteria | Current status |
|---:|---|---|---|---|---|---|
| 1 | API endpoint and HTTP method mapping | Approved, versioned route table/OpenAPI; each operation has method, path, purpose, auth, and consumer | Rafi (ARC-10); Hridi (client mapping) | Product scope and named canonical API owner | Every frontend operation maps to one approved operation; no guessed route or method | **BLOCKED** — local `/api/v1` routes are demo-only |
| 2 | Request DTO mapping | Approved request schema with field names, types, required/null rules, constraints, and unknown-field behavior | Rafi; domain reviewer for scientific terms | Artifact 1 and approved mission use case | Client payload validates against the approved schema; invalid inputs map consistently | **BLOCKED** — local `MissionRequestDTO` is not production authority |
| 3 | Response DTO mapping | Approved response schemas, field semantics, nullability, units, and version compatibility rules | Rafi; ARC-05/ARC-08 domain reviewers; Hridi | Artifacts 1–2 and model-owner review | Client parses valid responses and rejects/handles absent, null, malformed, or incompatible fields per contract | **BLOCKED** |
| 4 | Unified mission result structure | Approved top-level result DTO and versioned example defining mission, simulation, resources, status, provenance, and limitations | Rafi; ARC-05/ARC-08 owners; Project Owner approval | Approved product scope and component response schemas | A single result can be rendered without inventing fields or merging incompatible assumptions | **BLOCKED** — only the local demo's unified response is defined |
| 5 | ARC-05 simulation output mapping | ARC-05 owner-approved output definition, coordinate frame, model/integrator metadata, units, diagnostics, and limitations | ARC-05 owner; Rafi; Hridi | ARC-05 model provenance plus artifact 3 | Every displayed field traces to a defined simulator output with its declared units and educational/operational boundary | **BLOCKED** for production — local ARC-05 output is documented, but no production contract mapping is approved |
| 6 | ARC-08 resource evaluation mapping | ARC-08 owner-approved evaluator/version, scenario semantics, abstract vs physical units, violations, warnings, and approval state | ARC-08 owner; Rafi; Hridi | ARC-08 policy approval and artifact 3 | Dashboard labels educational feasibility and units exactly; no unsupported fuel/physical estimates or silent policy approval | **BLOCKED** for production — local educational output exists; policy is pending |
| 7 | Validation and error response mapping | Approved status codes, stable error codes/body, field paths, malformed input, valid-empty behavior, and redaction rules | Rafi; backend owner; Hridi | Artifacts 1–3 and service error policy | UI distinguishes validation, empty, unavailable, and server failures using the approved mapping | **BLOCKED** — local demo error shape is not canonical |
| 8 | Backend base URL and local startup configuration | Per-environment startup/configuration instructions, ownership, binding, port/base URL, and health check | Rafi; repository maintainer | Named backend repo/branch and deployment target | Local setup is reproducible with no hard-coded production endpoint; environment target and health check are explicit | **READY** for current local demo only (`127.0.0.1:8765` documented); production URL remains unconfirmed |
| 9 | Adapter/interface design | Boundary showing UI view models separate from transport DTOs, error translation, and version negotiation/compatibility | Hridi and Rafi; maintainer review | Approved contract before production adapter binding | Views depend on one narrow adapter; mapping is testable and no production DTO is inferred from prototype code | **NOT VERIFIED** — local API client exists, but no production adapter/interface decision is approved |
| 10 | Loading, success, empty, and error states | State transition matrix, API failure evidence, stale-result behavior, and browser/runtime observations | Hridi | Contract response/error semantics and local service availability | Every state is distinguishable and accessible; failures do not show stale or synthetic values as live results | **NOT VERIFIED** in this audit — earlier browser evidence is inherited, not rerun |
| 11 | Integration test strategy | Unit, API/contract, adapter, view-render, regression, and end-to-end test plan with fixtures and result records | Hridi and Rafi; QA owner to be confirmed | Approved contract, synthetic examples, test target | CI/local commands and expected outcomes are defined; contract conformance and regressions are separately measured | **READY** for local non-notebook regression baseline; production contract tests remain blocked |
| 12 | Accessibility and responsive visualization verification | Keyboard-only navigation, focus order, semantics, zoom/reflow, reduced motion, contrast, screen-reader alternatives, and viewport/browser evidence | Hridi; accessibility reviewer to be confirmed | Approved production target and representative data | Findings and tested browser/viewports are recorded; no critical keyboard or reflow barriers remain | **NOT VERIFIED** — source-level affordances do not prove browser behavior |
| 13 | Synthetic example request/response validation | Approved contract-marked synthetic request plus complete response fixture, schema validation, and provenance/limitation labels | Rafi; Hridi; ARC-05/08 reviewers | Artifacts 1–7 and approved synthetic scenario | Example validates against the approved schema and displays only declared synthetic/model-derived data | **NOT VERIFIED** — local request example and response assertions exist, but no canonical full contract example |
| 14 | ARC-09 compatibility handoff | Handoff packet with repository/branch, exact available commits, changed files, adapter assumptions, checks, known gaps, and contract version | Hridi; Project Owner/maintainer approves target | Artifacts 1–13 and confirmed integration base | Receiver can reproduce the compatible integration without importing unapproved demo assumptions or overwriting another worktree | **NOT VERIFIED** — draft prepared; remote `develop` does not contain the local dashboard commits |

## Evidence references

- `docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md` documents the local API, startup
  at `http://127.0.0.1:8765/`, synthetic request, response description,
  error behavior, and explicit non-production boundary.
- `src/quantum_space_agi/mission_demo/api.py` and `dto.py` implement that
  local demo.
- `tests/mission_demo/` contains local API/service tests.
- `docs/ARC09_BACKEND_DATA_CONTRACT_REQUEST.md` asks for authoritative data
  contracts and says endpoint details must come from backend authority.
- `docs/ARC10_DECISION_APPROVAL_REGISTER.md` says no decision is approved and
  production API/client work remains blocked.
- The test suite newly run for this audit is recorded in
  `docs/NASAQ26_PROJECT_OWNER_STATUS_REPORT.md`; no browser check was run in
  this audit.

## Stop condition

Do not implement a production client, backend route, or production DTO from
the local educational demo. Resume production mapping only after an
authoritative, versioned contract and the required owner approvals are
recorded.
