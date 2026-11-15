# ARC-10 Project Owner Approval Request

**To:** Project Owner / authorized maintainers
**From:** Independent ARC-10 read-only verification
**Date:** 2026-11-15
**Subject:** Request for authority, contract, and release decisions after local six-artifact verification
**Current status:** **B — PARTIALLY VERIFIED**
**Requested outcome:** Written decisions that either authorize a controlled next step or confirm that ARC-10 remains blocked.

> **This document is a request, not an approval.** No decision below is approved by this document, by the local demo, by passing tests, or by the existence of an implementation.

## 1. Purpose

The six ARC-10 artifacts have been verified against the only complete Mission API implementation accessible in the workspace:

- Repository: `/mnt/e/nasa26/nasaq26-develop-worktree`
- Branch/HEAD: `develop` / `6a44af34a649a1138cf577b3b16dbaf436c8a203`
- Implementation: local educational Mission API, ARC-09 prototype, ARC-05/ARC-08 integration, tests, and dashboard.

The verification establishes that the local implementation works. It does **not** establish that the implementation is the canonical production API, that the contract is approved, or that production deployment is authorized.

The Project Owner is asked to make the decisions in §5 so the project can move from partial verification to a controlled approved state, or to record that work remains blocked.

## 2. What has been verified

| # | Artifact | Evidence | Status |
|---:|---|---|---|
| 1 | Endpoints, methods, routes | `api.py`; real `GET /health`, `GET /destinations`, `POST /validate`, `POST /run`, `GET /` | **VERIFIED AGAINST IMPLEMENTATION** (local) |
| 2 | Request/response DTOs | `dto.py`; strict extra-forbid DTOs; rejection tests | **VERIFIED AGAINST IMPLEMENTATION** (local) |
| 3 | Unified Mission Result | Actual 8,783-byte response; ARC-05 + ARC-08 composition; finite values | **VERIFIED AGAINST IMPLEMENTATION** (local) |
| 4 | Validation/error formats | Real 400/404/405/415/422 responses; generic 500 path tested | **VERIFIED AGAINST IMPLEMENTATION** (local; one doc mismatch) |
| 5 | Local setup/base URL/health | Fresh venv, documented command, loopback `127.0.0.1:8765`, health 200 | **VERIFIED AGAINST IMPLEMENTATION** (local) |
| 6 | Synthetic examples | Real LEO 400 km run; reproducible byte-identical response | **VERIFIED AGAINST IMPLEMENTATION** (local) |

Test results:

- `tests/mission_demo`: **46 passed**
- ARC-08 configuration/evaluator: **67 passed**
- `tests/simulation`: **291 passed**
- Browser-backed ARC-09 subset with Google Chrome: **18 passed, 0 skipped**

Full evidence is in the five companion reports listed in §7.

## 3. What has not been approved

| Area | Current state | Consequence |
|---|---|---|
| Canonical repository/branch | **OPEN / BLOCKED** (`MAPI-02`) | No authoritative production target. |
| Contract owner/approver/version | **OPEN / BLOCKED** (`MAPI-07`, `MAPI-15`) | Routes, DTOs, result, errors, and versioning are not binding. |
| ARC-10 v0.3/v0.4 | **NOT FOUND** | Cannot compare or claim conformance. |
| Security/privacy | **BLOCKED** (`MAPI-08`, `MAPI-09`) | No auth, CORS, secrets, retention, or data-rights approval. |
| Deployment/operations | **BLOCKED** (`MAPI-13`) | Loopback demo is not a production service. |
| ARC-05/ARC-08 domain review | **BLOCKED** (`MAPI-04`, `MAPI-05`) | Scientific meaning, units, collision semantics, and feasibility labels are unreviewed. |
| ARC-09 client authority | **BLOCKED** (`MAPI-06`) | Prototype is not an approved production client. |
| Test/release acceptance | **BLOCKED** (`MAPI-12`) | Local green tests are not production acceptance. |
| Dataset Validation API | **SEPARATE / BLOCKED** (`MAPI-14`) | Not implemented in this Mission API source. |

**No artifact is `FORMALLY APPROVED`.**

## 4. Why a decision is needed now

Continuing without decisions would risk:

1. Treating a local educational demo as a production contract.
2. Building against a non-canonical branch (`develop` is 47 commits ahead of `origin/develop`).
3. Claiming scientific or mission validity that the implementation does not support.
4. Exposing a service with no approved security or operational boundary.
5. Losing the verified state because it is uncommitted/untracked.
6. Conflating the Mission API with the separate Dataset Validation API.
7. Inferring `scientific_eligibility` from structural validation, which the implementation does not do.

## 5. Decisions requested

### DEC-01 — Approve or reject the read-only verification basis

**Question:** May `develop@6a44af3` be recorded as the read-only operational verification source while formal authority remains unresolved?

**Options:**

- **A. Yes — verification only.** Record that this source was used for read-only verification, not as a production target or contract approval.
- **B. No — wait for a canonical-source decision.** Verification remains incomplete.
- **C. Other (specify).**

**Recommendation:** **A**, with explicit wording that it does not confer production authority.

**Impact if A:** The six-artifact verification can be cited as local evidence.
**Impact if B:** Status remains **B — PARTIALLY VERIFIED** with no accepted operational source.

---

### DEC-02 — Name the canonical repository, branch, and integration target

**Question:** Which repository, branch, and integration target own the Mission API contract and eventual implementation?

**Required in the answer:**

- Repository URL/name.
- Branch name.
- Integration target for changes.
- Permitted change boundary.
- Whether `develop@6a44af3` is to be preserved, merged, rebased, or discarded.
- Named maintainer confirmation.

**Options:**

- **A. `develop` in `quantum-space-agi-reusable-engine`** (operational source today; 47 commits ahead of `origin/develop`).
- **B. A dedicated release/integration branch** (name it).
- **C. A different repository** (name it).
- **D. Defer; keep blocked.**

**Recommendation:** No recommendation without owner context. If A is chosen, also decide how to reconcile `origin/develop` and preserve the verified state.

**Related gaps:** `GAP-01`, `GAP-12`; `MAPI-02`, D-01.

---

### DEC-03 — Name the contract owner, canonical contract, and approval process

**Question:** Who owns the Mission API contract, where is the canonical version, and who may approve it?

**Required in the answer:**

- Accountable contract owner.
- Canonical document path/location.
- Contract version to be used.
- Reviewers and final approver.
- Versioning and change-control process.
- Whether the current candidate v0.1 is an input only or a baseline.

**Options:**

- **A. Designate an owner/approver and canonical location now.**
- **B. Keep the candidate as input and start a new versioned contract process.**
- **C. Defer; keep blocked.**

**Recommendation:** **A** or **B**, with a named final approver. Do not treat the untracked candidate v0.1 as approved.

**Related gaps:** `GAP-02`; `MAPI-07`, `MAPI-15`, D-04, D-06–D-08.

---

### DEC-04 — Resolve the missing ARC-10 v0.3/v0.4 documents

**Question:** Where are ARC-10 documentation v0.3 and v0.4, or what is the controlling version if they do not exist?

**Verified fact:** Neither version exists in any searched worktree, `/mnt/e/nasa26`, `/mnt/c/Users/HP/Downloads`, or local/cached remote-tracking git ref. Only v0.1/v0.2 were found; no network fetch was performed.

**Options:**

- **A. Provide the v0.3/v0.4 documents** (paths/refs).
- **B. Record that they do not exist** and designate v0.1/v0.2 or a new version as controlling.
- **C. Defer; keep blocked.**

**Recommendation:** **A** first; otherwise **B** with a written record. Do not silently promote v0.2.

**Related gap:** `GAP-03`.

---

### DEC-05 — Confirm scope: educational local demo vs production API

**Question:** Is the approved scope (a) the local educational demo, (b) a production Mission API, or (c) both as separate deliverables?

**Options:**

- **A. Local educational demo only.** Keep synthetic labels, loopback binding, and no production claims.
- **B. Production Mission API.** Require security, deployment, domain, and acceptance approvals before implementation/release.
- **C. Both, with separate contracts and release gates.**

**Recommendation:** **A** for the current implementation; **C** if production is intended, with the demo explicitly non-production.

**Impact:** Determines whether security/deployment work is required now or deferred.

---

### DEC-06 — Designate ARC-05, ARC-08, and ARC-09 reviewers

**Question:** Who reviews and accepts the domain and client mappings?

**Required designations:**

| Area | What must be reviewed | Related IDs |
|---|---|---|
| ARC-05 | `SimulationConfig` mapping, ECI/RK4, state order, units, collision semantics, diagnostics | `MAPI-04` |
| ARC-08 | Scenario/payload catalog, abstract units, feasibility, score, policy limitations | `MAPI-05` |
| ARC-09 | Client target, field consumption, loading/error/empty states, accessibility | `MAPI-06` |

**Options:**

- **A. Name reviewers and scope now.**
- **B. Defer; keep blocked.**

**Recommendation:** **A.** Local tests and source are not a substitute for named review authority.

**Related gaps:** `GAP-07`, `GAP-08`.

---

### DEC-07 — Decide collision metadata exposure

**Question:** Should the unified result expose `collision_radius_m` and `collision_method`?

**Verified fact:** ARC-05 returns both (`workflow.py:50,53`), but the service omits them (`service.py:95-105`). The candidate proposal flags this as an open omission.

**Options:**

- **A. Expose both.**
- **B. Expose radius only.**
- **C. Explicitly exclude both** with a documented rationale.
- **D. Defer.**

**Recommendation:** **A** if collision semantics are in scope; otherwise **C** with a recorded reason.

**Related gap:** `GAP-10`.

---

### DEC-08 — Decide wrong-method behavior and correct the documentation

**Question:** Should `GET` on the POST-only mission routes return `404` (current behavior) or `405`?

**Verified fact:**

- `POST /health` → `405`
- `PUT /api/v1/missions/run` → `405`
- `GET /api/v1/missions/run` → **`404`** because the static mount handles it
- Local demo doc broadly says unsupported methods return `405`

**Options:**

- **A. Keep 404 and correct the documentation.**
- **B. Implement consistent 405 behavior and add tests.**
- **C. Defer.**

**Recommendation:** Choose one explicitly and test it. Do not leave the doc/behavior mismatch.

**Related gap:** `GAP-11`.

---

### DEC-09 — Decide security, privacy, and deployment posture

**Question:** What deployment boundary and security model apply, and who approves them?

**Options:**

- **A. Developer-only loopback tool.** Record no production security/deployment obligation; keep the demo local.
- **B. Internal service.** Require authn/authz, CORS, secrets, logging/redaction, retention, and network boundary.
- **C. Public service.** Require the full security/privacy/deployment review.
- **D. Defer; keep blocked.**

**Recommendation:** **A** for the current demo; **B/C** only with named security, privacy, and operations authorities.

**Related gaps:** `GAP-04`, `GAP-05`, `GAP-06`; `MAPI-08`, `MAPI-09`, `MAPI-13`.

---

### DEC-10 — Approve the acceptance matrix and authority

**Question:** Who accepts the test strategy and release evidence, and against which matrix?

**Minimum matrix questions:**

- API/transport tests.
- ARC-05/ARC-08 integration tests.
- ARC-09 browser/state tests.
- Security/resource-limit tests.
- Scientific/domain review.
- Performance/timeout behavior.
- Acceptance environment and thresholds.

**Options:**

- **A. Approve a named matrix and acceptance authority.**
- **B. Accept local verification only, explicitly not production acceptance.**
- **C. Defer; keep blocked.**

**Recommendation:** **B** now; **A** before production.

**Related gap:** `GAP-09`; `MAPI-12`, D-15.

---

### DEC-11 — Preserve the verified implementation

**Question:** How should the verified `develop@6a44af3` state be preserved so reviewers can reproduce it?

**Options:**

- **A. Commit/push after review** (requires explicit authorization; not done).
- **B. Tag or archive a reproducible ref/artifact.**
- **C. Leave local only** (verification remains worktree-specific).

**Recommendation:** **B** or **A** after review. The repository currently has 4 modified and 22 untracked files, and `origin/develop` does not contain the implementation.

**Related gap:** `GAP-12`.

---

### DEC-12 — Decide partial-failure, limits, provenance, and Dataset Validation boundaries

**Questions:**

1. On ARC-05 or ARC-08 failure, should the API return all-or-error, or a partial result with explicit status? (`MAPI-16`, D-12)
2. What timeout, cancellation, retry, idempotency, request-size, and trajectory-sample limits apply?
3. Should the result expose contract version, run timestamp, request ID, and uncertainty? (D-09)
4. Confirm Dataset Validation remains a separate API with its own owner/contract. (`MAPI-14`)

**Options:**

- **A. Record explicit decisions now.**
- **B. Defer production decisions; keep the demo's current behavior.**
- **C. Keep blocked.**

**Recommendation:** **B** for the demo; **A** before production. Do not infer `scientific_eligibility` from structural validation.

**Related gaps:** `GAP-13`, `GAP-14`, `GAP-15`, `GAP-16`, `GAP-17`.

## 6. Approval record template

To be completed only by an authorized decision maker. A checked box without a name, date, and scope is not approval.

| Decision | Approved / Rejected / Deferred | Scope and conditions | Authorized name/role | Date | Evidence reference |
|---|---|---|---|---|---|
| DEC-01 Read-only verification basis |  |  |  |  |  |
| DEC-02 Canonical repo/branch |  |  |  |  |  |
| DEC-03 Contract owner/version/process |  |  |  |  |  |
| DEC-04 ARC-10 v0.3/v0.4 controlling version |  |  |  |  |  |
| DEC-05 Scope: demo vs production |  |  |  |  |  |
| DEC-06 ARC-05/08/09 reviewers |  |  |  |  |  |
| DEC-07 Collision metadata |  |  |  |  |  |
| DEC-08 Wrong-method behavior |  |  |  |  |  |
| DEC-09 Security/privacy/deployment |  |  |  |  |  |
| DEC-10 Acceptance matrix/authority |  |  |  |  |  |
| DEC-11 Preservation/publication |  |  |  |  |  |
| DEC-12 Limits/provenance/Dataset boundary |  |  |  |  |  |

**Overall decision:**

- [ ] Approve a controlled next step within the stated scope.
- [ ] Reject / keep blocked.
- [ ] Defer pending additional evidence (specify).

**Authorized signature:** ______________________
**Name/role:** ______________________
**Date:** ______________________
**Comments/conditions:** ______________________________________________

## 7. Evidence index

| Report | Purpose |
|---|---|
| `ARC10_AUTHORITATIVE_SOURCE_DISCOVERY.md` | Environment, worktrees, branch/ref relationships, source-of-truth matrix, missing v0.3/v0.4. |
| `ARC10_SIX_ARTIFACT_IMPLEMENTATION_VERIFICATION.md` | Artifact-by-artifact verification against source and tests. |
| `ARC10_MISSION_INTEGRATION_VERIFICATION.md` | ARC-05/ARC-08/ARC-09 boundary analysis and cross-boundary invariants. |
| `ARC10_SYNTHETIC_EXECUTION_EVIDENCE.md` | Actual HTTP requests/responses, hashes, headers, errors, server logs. |
| `ARC10_GAP_AND_DECISION_REGISTER.md` | Gap register, decision register, status-change criteria. |
| `ARC10_PROJECT_OWNER_APPROVAL_REQUEST.md` | This request. |

Raw evidence: `/tmp/opencode/arc10_evidence/` (local, ephemeral). The reports summarize the raw evidence so the findings remain reviewable if the temp directory is removed.

## 8. What happens if no decision is made

Without a decision:

- The status remains **B — PARTIALLY VERIFIED**.
- The local implementation remains usable for read-only demonstration.
- No production claim, deployment, security certification, scientific approval, or release authorization is made.
- No route, request, response, approval, or evidence will be fabricated to fill the gap.
- No commit, push, merge, or implementation change will be made.

## 9. Requested response

Please provide written answers to **DEC-01 through DEC-12** using §6, or schedule a review to decide them. The minimum decisions needed to move beyond partial verification are **DEC-02, DEC-03, DEC-04, DEC-05, and DEC-10**; security and domain decisions are required before any non-local use.
