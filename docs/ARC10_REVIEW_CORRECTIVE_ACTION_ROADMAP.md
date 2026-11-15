# ARC-10 Review Corrective Action Roadmap

Repository: `/mnt/e/nasa26/nasaq26-develop-worktree`
Branch: `develop`
Full HEAD: `6a44af34a649a1138cf577b3b16dbaf436c8a203`
Governance status: `REVIEW SUBMISSION WORKFLOW READY — ALL REVIEWS PENDING — PRODUCTION NOT APPROVED`
Baseline: `LOCAL_SYNTHETIC_DEMO_BASELINE — NOT PRODUCTION APPROVED`

## 1. Authentic reviewer findings

No authentic reviewer responses or findings have been received. Therefore, there are no reviewer-derived corrective actions to prioritize or implement. This roadmap does not treat the pre-existing gaps below as reviewer findings.

All proposed actions are planning items only. No corrective action is authorized for implementation by this document.

## 2. Pre-existing gap work — not reviewer corrective actions

The following items are carried forward from the existing ARC-10 gap and review documents. They are separated from actual reviewer findings and are proposals for governance-controlled follow-up.

| Existing gap | Priority | Proposed action | Dependencies | Responsible role | Evidence needed | Verification criteria | Approval required before implementation |
|---|---|---|---|---|---|---|---|
| G-01 canonical production target | Critical | Obtain an explicit canonical repository/branch decision if production work is later proposed; preserve `develop` as verification baseline only | Project Owner decision; production scope request | Project Owner | Written authority decision and target reference | Decision is explicit and recorded without reclassifying the current baseline | Project Owner approval; no implementation until separately authorized |
| G-02 contract ownership | Critical | Assign contract-drafting responsibility and keep final contract approval with Project Owner | Governance assignment | Project Owner | Recorded role assignment and approval path | Named role/authority is documented; no authority inferred from contribution | Project Owner approval |
| G-03 missing v0.3/v0.4 artifacts | High | Continue proposal-only reconstruction from source/history, preserve provenance and uncertainty, do not fabricate historical versions | D-03; source and historical evidence availability | Contract owner to be assigned | Referenced source, tests, historical records, and draft status | Every draft claim traces to evidence; absent facts stay marked unknown | Project Owner review before draft becomes authoritative |
| G-04 collision metadata boundary | Medium | Preserve current exclusion; route any proposed inclusion through separate contract review | D-04; future scope proposal | Contract owner to be assigned | Explicit schema delta and impact analysis if a change is proposed | Current public response remains scoped to recorded decision until approval | Project Owner approval before any contract or code change |
| G-05 local HTTP 404 decision | Medium | Keep documentation and future review scope explicitly local-demo-only | D-05 | Contract owner to be assigned | Route/method evidence and scope label | No production method semantics inferred from local behavior | Project Owner approval for any production rule or implementation |
| G-06 scientific/domain boundary | High | Obtain independent scientific/domain review; keep structural validation separate from scientific eligibility | Reviewer assignment and authentic response | Scientific/domain authority | Completed response, evidence examined, limitations, and decision | No eligibility inferred from structural validation; synthetic execution not scientific validation | Domain authority approval; Project Owner approval remains separate |
| G-07 security approval | Critical | Submit security package through the review workflow and record authentic response | Authorized reviewer assignment | Security authority | Completed response, authority verification, evidence references | Decision meets `ARC10_REVIEW_DECISION_RULES.md`; all critical findings resolved or separately authorized | Security approval; any implementation requires separate authorization |
| G-08 privacy approval | Critical | Submit privacy package and obtain review of data inventory, retention, sharing, and provenance | Authorized reviewer assignment | Privacy authority | Completed response and applicable policy evidence | Decision meets review rules; conditions and limitations preserved | Privacy approval; any implementation requires separate authorization |
| G-09 deployment/operations approval | Critical | Submit operations package; define the future operational evidence boundary without deploying | Authorized reviewer assignment | Platform/operations authority | Completed response, deployment/rollback/runbook evidence | Explicit operations decision; no unresolved blocking items | Operations approval; separate deployment authorization required |
| G-10 acceptance/QA | Critical | Submit QA package and require reproducible evidence for the exact reviewed baseline | Authorized QA reviewer assignment | QA/acceptance authority | Completed response, exact commands/results, accessibility and acceptance evidence | Evidence is reproducible and scope-limited; no claims beyond actual results | QA approval; Project Owner contract approval remains separate |

## 3. Workstream separation

### Documentation corrections

- Candidate work: maintain provenance, scope labels, evidence references, and decision consistency.
- Current status: no reviewer-requested documentation corrections received.
- Any reconstructed contract must remain `DRAFT — RECONSTRUCTED FROM AVAILABLE EVIDENCE` and must not invent ARC-10 v0.3/v0.4 artifacts or a canonical production version.
- Approval dependency: Project Owner review before a draft is treated as authoritative.

### Code corrections

- Authentic reviewer findings: none received.
- Proposed code corrections: none identified from reviewer feedback.
- Status: no code work authorized by this roadmap.
- Approval dependency: a real finding, explicit scope, Project Owner authorization, and applicable independent approvals before implementation.

### Security corrections

- Findings: none received.
- Required next action: obtain authentic independent security review.
- Status: pending; no remediation is prescribed as a reviewer finding.

### Privacy corrections

- Findings: none received.
- Required next action: obtain authentic independent privacy review.
- Status: pending; no remediation is prescribed as a reviewer finding.

### Scientific/domain corrections

- Findings: none received.
- Required next action: obtain authentic domain review while maintaining the rule that structural validation does not establish scientific eligibility and synthetic execution is not scientific validation.
- Status: pending.

### Deployment corrections

- Findings: none received.
- Required next action: obtain authentic platform/operations review.
- Status: pending; no infrastructure or deployment action is authorized.

### QA corrections

- Findings: none received.
- Required next action: obtain authentic acceptance/QA review with exact evidence references.
- Status: pending; no test result is asserted here.

## 4. Governance controls

- Preserve D-01 through D-06 as currently recorded.
- Keep each independent review separate from Project Owner final contract approval.
- Do not mark a gap accepted risk without written authorization from the appropriate authority.
- Do not mark a finding verified without actual closure evidence.
- Keep Mission Planning & Simulation API separate from Dataset Validation API.
- No production implementation, external integration, NASA data acquisition, or deployment is authorized.

## 5. Next action

Use the established submission workflow to obtain authentic written responses from authorized reviewers. Update this roadmap only after evidence is received and verified; keep all current review decisions pending in the meantime.
