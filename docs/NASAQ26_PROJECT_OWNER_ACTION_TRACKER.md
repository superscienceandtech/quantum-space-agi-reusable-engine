# NASAQ26 Project Owner Action Tracker

**Purpose:** Track coordination responses, required evidence, and approval
gates for ARC-09 visualization readiness and ARC-10 API contract approval.

**Evidence basis:** Existing Project Owner reports and repository ownership /
approval records inspected 2026-11-15. No messages were sent for this tracker.
No deadline, response, approval, or decision authority is inferred. Update
the response and approval columns only when a response is received through
the authorized project process and its record can be linked.

## Current status

- Local mission dashboard HEAD recorded in the status report:
  `6a44af34a649a1138cf577b3b16dbaf436c8a203` on local `develop`.
- The dashboard/API is a synthetic educational local demo, not an approved
  ARC-10 production contract.
- `docs/ARC10_DECISION_APPROVAL_REGISTER.md` says no decisions are approved
  and production API implementation / ARC-09 production integration remain
  blocked.
- The recorded local branch is 47 commits ahead of `origin/develop`.
  `develop` and `origin/main` are diverged; the prior merge simulation found
  nine conflicts. Do not select or assume an integration base.
- The prior audit reported 915 tests passed and 4 subtests passed. The audit
  did not rerun browser or accessibility verification.
- Detailed snapshots and caveats are in
  `docs/NASAQ26_PROJECT_OWNER_STATUS_REPORT.md`.

## Ownership and approval boundaries

- The Project Owner's coordination request assigns **Hridi** to ARC-09
  visualization and **Rafi** to ARC-10 API-contract coordination. These are
  task-level assignments, not evidence that either person has approval
  authority.
- `docs/ARC10_DECISION_APPROVAL_REGISTER.md` identifies **Sonjoy and Rafi** as
  ARC-10 co-owners/preparers for coordination, while explicitly noting that
  decision-specific approval authority remains to be confirmed.
- `docs/ARC09_OWNER_HANDOVER_SUMMARY.md` identifies Project Owner Yousuf and
  ARC-09 reviewer Rafi for the notebook evidence package. It states the
  reviewer assignment does not establish approval authority for production
  integration and that review completion/outcome remain unconfirmed.
- `docs/ARC09_DECISION_REGISTER.md` likewise records Rafi's reviewer
  assignment for the ARC-09 notebook evidence package, not approval of the
  mission dashboard or production API.
- Approval authority for production frontend/backend targets, contract
  source, scientific mappings, security/environment policy, and release is
  not established by the records reviewed. Record the authorized approver
  separately for each decision.

## Hridi — ARC-09 visualization response tracking

| ID | Action / deliverable | Required response or evidence | Dependency | Status | Response received | Approval / decision record |
|---|---|---|---|---|---|---|
| H-01 | Confirm availability and authorized repository/branch for ARC-09 review | Written availability; confirmed repository, branch, access, and permitted PR target | Project Owner/maintainer confirms canonical frontend target and branch | OPEN — not recorded | Not recorded | Not applicable until a decision is required |
| H-02 | Review current dashboard and report its intended scope and prototype boundaries | Review notes identifying production target (if any), synthetic panels, local-demo connection, and proposed reusable elements | Read access to the authorized target; distinguish prototype from production | NOT VERIFIED | Not recorded | Product/maintainer acceptance not recorded |
| H-03 | Review visualization practice projects for reuse suitability | Evidence-based disposition of chart-practice SVG patterns and Three.js practice; do not treat either as an approved production component | H-01; accessibility/performance review of any candidate reuse | NOT VERIFIED | Not recorded | Reuse approval not recorded |
| H-04 | Verify visualization accessibility and responsive behavior | Browser/viewports tested; keyboard/focus, zoom/reflow, reduced motion, contrast, semantics, screen-reader alternatives, issues and results | Authorized target and representative data; agreed acceptance criteria | NOT VERIFIED — source inspection is not browser verification | Not recorded | Accessibility reviewer and acceptance record not identified |
| H-05 | Verify request lifecycle and display behavior | Evidence for loading, success, empty, validation/error, stale-result clearing, and live-vs-synthetic labeling | Approved response and error semantics for production; local checks may be reported separately | NOT VERIFIED in current coordination record | Not recorded | Product acceptance not recorded |
| H-06 | Prepare contract-neutral compatibility notes / adapter test approach | Proposed UI needs and mapping questions without inventing endpoint, DTO, URL, or backend behavior | Can proceed as requirements work; production mapping depends on ARC-10 artifacts | OPEN — preparation only | Not recorded | No production integration approval |
| H-07 | Produce ARC-09 compatibility handoff | Target branch, exact source commit(s), changed files, contract version, tests, known limitations, and reproducible verification | H-01 and approved ARC-10 contract; integration base confirmation | BLOCKED for production handoff | Not recorded | Project Owner/maintainer target approval not recorded |
| H-08 | Confirm ARC-09 review outcome and acceptance criteria | Written review outcome, criteria applied, reviewer availability, and record of acceptance or requested changes | Confirm whether notebook evidence review is separate from dashboard review | OPEN — prior notebook reviewer assignment is not completed evidence | Not recorded | No completed review/acceptance recorded |

## Rafi — ARC-10 contract response tracking

The six artifact rows track **drafting/evidence**, not approval. Rafi may
prepare material labeled DRAFT / NOT CANONICAL; implementation may not depend
on it until the authorized approval process records acceptance.

| ID | Required artifact / action | Required response or evidence | Dependency | Status | Response received | Approval / decision record |
|---|---|---|---|---|---|---|
| R-01 | API endpoints, HTTP methods, and routes | Versioned operation list/OpenAPI: method, path, purpose, consumer, auth, and canonical source | Approved product use case; named backend and contract owner | BLOCKED — current routes are local-demo only | Not recorded | No approval recorded |
| R-02 | Request and response DTOs | Versioned schemas with field types, required/optional/null semantics, constraints, unknown-field policy, and compatibility rules | R-01; domain review for scientific fields | BLOCKED | Not recorded | No approval recorded |
| R-03 | Unified mission result structure | Approved response envelope composing mission, ARC-05, ARC-08, status, provenance, units, and limitations; include a validated example | R-01/R-02; ARC-05 and ARC-08 owner input | BLOCKED | Not recorded | No approval recorded |
| R-04 | Validation and error formats | HTTP statuses, stable error codes/body, field-level errors, valid-empty behavior, redaction, and upstream/internal failure semantics | R-01/R-02 and security/platform input where required | BLOCKED | Not recorded | No approval recorded |
| R-05 | Local backend setup and base URL | Canonical backend repository/branch, per-environment configuration, local startup, health check, and separation of local/test/production URLs | Named service owner and environment/security decisions | PARTIAL — local demo setup exists; production target/URL not established | Not recorded | No production setup approval |
| R-06 | Verified synthetic request/response examples | Complete example pair tied to contract version, schema validation evidence, synthetic/model-derived labels, units, provenance, and limitations | R-01 through R-05; ARC-05/ARC-08 domain review | PARTIAL — local demo request/response documentation and assertions exist; not a canonical contract example | Not recorded | No approval recorded |
| R-07 | Contract ownership and canonical source | Named contract owner, source-of-record location, versioning/change review, and decision authority | Project Owner / maintainer confirmation | BLOCKED — ownership and canonical source not confirmed | Not recorded | No approval recorded |
| R-08 | Production integration target and scope | Confirmed backend/frontend repository and branch, first approved use case, and explicit in/out of scope | Project Owner and maintainers | BLOCKED | Not recorded | No approval recorded |

## Project Owner decisions requiring explicit record

These are decision requests, not presumed approvals:

| ID | Decision required | Evidence needed to close | Current status |
|---|---|---|---|
| P-01 | Confirm canonical frontend and backend repositories/branches and the authorized integration base | Written decision with exact remote refs and owners; recheck current Git state before integration | OPEN — not recorded |
| P-02 | Select the initial API use case and its consumer/scope | Written product decision including exclusions | OPEN — ARC-10 register says no use case is selected |
| P-03 | Designate contract owner, source of record, versioning, and change-review process | Written authority assignment and canonical location | OPEN |
| P-04 | Identify decision-specific approvers for API/schema, scientific semantics, security/environment, and acceptance | Named approver(s), scope, and how approval is recorded | OPEN |
| P-05 | Approve or reject the production contract after review | Approved versioned contract and recorded decision; no draft is sufficient | BLOCKED until contract is submitted |
| P-06 | Authorize production implementation separately from contract drafting | Explicit scope, target repository/branch, and implementation authorization | NOT GRANTED in inspected records |
| P-07 | Confirm ARC-09 reviewer availability and acceptance process for the relevant work | Written availability, scope distinction, criteria, and final record | OPEN — existing Rafi assignment concerns notebook evidence review |
| P-08 | Decide history reconciliation/integration path | Maintainer-confirmed base and conflict-resolution strategy; rerun tests after reconciliation | BLOCKED — diverged history and nine simulated conflicts |

## Blockers and status vocabulary

**Blockers**

1. No authoritative, formally approved ARC-10 production contract was found.
2. The canonical backend/frontend targets and integration base are not
   confirmed; local `develop` is not present on remote `develop`.
3. Production approval authority is not assigned per decision in the inspected
   approval records.
4. ARC-09 browser/accessibility verification and the review outcome are not
   recorded as completed in the current evidence.
5. Main/develop reconciliation is unsafe to assume: histories have diverged
   and nine merge conflicts were previously simulated.

**Status meanings**

- **READY:** the specified evidence exists and is verified for the stated
  scope only. Local-demo readiness must not be interpreted as production
  approval.
- **BLOCKED:** work depends on a missing decision, contract, target, or
  approval.
- **NOT VERIFIED:** evidence has not been checked or a required test/review
  result has not been recorded.
- **OPEN:** a response or decision is requested but no response is recorded.
- **PARTIAL:** some local/demo evidence exists, but acceptance criteria are
  not met for production.

Do not change a row to approved/complete based on an unrecorded conversation.
Record response date, responder, decision authority, contract/version or
commit, evidence link, and any conditions when they are actually supplied.
Do not invent a due date; add one only when the Project Owner sets it.

## Recommended next three actions

1. **Project Owner / maintainers:** confirm canonical frontend/backend
   targets, integration base, first use case, contract owner, and
   decision-specific approvers.
2. **Rafi with ARC-10 coordination:** prepare the six artifacts as explicitly
   DRAFT / NOT CANONICAL; request ARC-05/ARC-08 domain input for scientific
   semantics and provide contract-versioned synthetic examples for review.
3. **Hridi:** continue contract-independent visualization/accessibility
   review in an authorized branch and return evidence; defer production
   adapter binding until contract approval and integration-base confirmation.
