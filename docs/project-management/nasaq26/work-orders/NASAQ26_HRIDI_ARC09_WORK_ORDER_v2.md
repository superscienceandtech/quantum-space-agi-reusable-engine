# Work Order Draft v2 — Hridi — ARC-09 Visualization and Handover

**Dispatch state:** SENT.  
**Assignment state:** PROPOSED; acknowledgement not recorded.  
**Responsible scope:** ARC-09 visualization, prototype handover, verification, and frontend preparation, as proposed in the Project Owner responsibility model.  
**Purpose:** Return independently useful prototype and readiness evidence. This work order does not approve a production stack or integration.

## Deliverables

1. **Original prototype handover:** authoritative repository/path, branch/commit, source and documentation inventory, run instructions, design/assets, known limitations, source owner/custodian if known, and any competing copies. Identify the evidence revision and date checked. Keep the isolated prototype distinct from the production frontend.
2. **Visualization inventory and count reconciliation:** enumerate the six visualizations referenced by the current request, if six exist. For each, provide display name, component/source path, data/fixture source, documentation, and verification state. The inspected local `origin/main` documentation describes four visualizations: line, grouped bar, scatter, and conceptual relationship graph. Identify evidence for any additional two or state that only four are supported by the inspected snapshot. Do not count six proposed navigation destinations as charts.
3. **Accessibility and responsive verification:** for each check report `PASS`, `FAIL`, `NOT TESTED`, or `NOT APPLICABLE`, with evidence/reference and limitation. Include OS/device, browser/version, viewport dimensions, reproduction steps and screenshots/logs where available; keyboard/focus, zoom/contrast/overflow, and assistive-technology/screen-reader results. Separate source inspection from browser/runtime and assistive-technology checks. Do not claim accessibility compliance from source review alone.
4. **Production frontend repository and branch:** canonical URL, repository owner, checkout, branch/commit/base, date/time/timezone checked, and evidence that this is the designated production frontend. State explicitly if unconfirmed or only a local snapshot.
5. **Approved framework evidence:** framework/runtime/build tool and versions, authority/decision-maker, decision record/date and canonical location. If no approval evidence exists, report `UNCONFIRMED`; do not infer it from prototype HTML/CSS/JS.
6. **Backend contract request state:** canonical request path/revision and evidence of dispatch/response if sent. If only a draft exists, report `PREPARED / NOT SENT` or the status supported by evidence. Link an authoritative approved contract if one exists; do not invent endpoint/schema/metric semantics.
7. **Production integration dependency map:** for each item mark `EVIDENCED`, `PENDING`, or `NOT IDENTIFIED` and provide source: approved use case; backend/API owner and repository; canonical contract/version and DTO/error conventions; scientific metric meanings, units, uncertainty and provenance; authentication/authorization; CORS/environment/secrets; payload/compute/time/rate limits; persistence/background behavior; frontend repository/framework; test/accessibility acceptance; architecture/security review; implementation authorization; release authorization.
8. **Proposed next implementation task:** recommend a bounded task with purpose, exact expected output/files, acceptance criteria, dependencies, risk, and reviewer. It may be isolated prototype work or other already-authorized preparation. Any production implementation remains gated. Keep synthetic fixtures explicitly labeled and physically/logically separate from NASA research or production data.

## Acceptance criteria

- Each deliverable is independently traceable to a source revision/path, evidence date and owner/custody claim where known.
- Prototype handover, visualization inventory and verification evidence can be submitted even if production API/framework decisions remain unresolved.
- The four-versus-six discrepancy is reconciled against evidence; no additional visualization is presumed.
- Each accessibility check has a disposition and evidence or an explicit not-tested reason.
- Production repository/framework and contract status are evidenced or marked unconfirmed; a request draft is not dispatch evidence.
- Synthetic values remain synthetic and are not presented or mapped as NASA/production observations.
- The proposed next task has its own scope and reviewer and does not imply architecture approval or production authorization.

## Evidence context and boundaries

The prior local `origin/main` snapshot at `401bba6` contains `arc09-ui-prototype/`, its handoff/checklist/static audit/manual verification report, and `docs/ARC09_BACKEND_DATA_CONTRACT_REQUEST.md`. Documentation identifies four visualizations. The manual verification report records supplied manual results but says it was not rerun while preparing that report; screen-reader checks and production API integration are not established. Refs were not refreshed for this package, so report current state from an authorized checkout rather than assuming the snapshot is current.

The handover, chart inventory, existing verification evidence, framework/repository discovery, and contract-request status are independent evidence tasks. Unresolved backend contracts block production integration and data mapping; they do not block collection of these existing records.

**Governance:** Synthetic demonstration data must remain separate from real NASA research data. No external approval is inferred. Production implementation requires the appropriate product, API, architecture, security, scientific/data, and implementation/release decisions recorded by their actual authorities.
