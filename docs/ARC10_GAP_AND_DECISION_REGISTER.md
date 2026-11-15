# ARC-10 Gap and Decision Register

**Verification snapshot:** 2026-11-15T07:38:04Z (2026-11-15 13:38 +06:00)
**Source verified:** `/mnt/e/nasa26/nasaq26-develop-worktree`, `develop`, HEAD `6a44af34a649a1138cf577b3b16dbaf436c8a203`
**Purpose:** Record verification-specific gaps and the decisions required to move from partial verification to approval.
**Relation to existing registers:** This report does **not** modify or replace `ARC10_DECISION_APPROVAL_REGISTER.md` or `NASAQ26_MISSION_API_OWNER_DECISION_REGISTER.md`. It references their IDs where they apply and records only what the verification evidence supports.

## 1. Status definitions

| Status | Meaning |
|---|---|
| `RESOLVED FOR LOCAL VERIFICATION` | The local implementation behavior is verified; production approval is still separate. |
| `OPEN — OWNER DECISION REQUIRED` | A named authority must decide; no such decision exists. |
| `OPEN — DOCUMENT GAP` | A required document/version is missing. |
| `OPEN — TECHNICAL GAP` | A verified behavior differs from the documented or desired behavior. |
| `BLOCKED` | Production work must not proceed until closure evidence exists. |
| `FORMALLY APPROVED` | Written approval by an authorized decision maker. **None of the items below has this status.** |

## 2. Executive gap summary

| Area | Status | Effect |
|---|---|---|
| Local implementation of six artifacts | **RESOLVED FOR LOCAL VERIFICATION** | All six artifacts are implemented and evidenced against `develop`. |
| Repository/branch authority | **BLOCKED** | No canonical production target (`MAPI-02`, D-01). |
| Contract ownership and approval | **BLOCKED** | No binding contract or approver (`MAPI-07`, `MAPI-15`, D-04, D-06–D-08). |
| ARC-10 v0.3/v0.4 | **OPEN — DOCUMENT GAP** | Required versions not found anywhere searched. |
| Security/privacy | **BLOCKED** | No auth/CORS/secrets/privacy decision (`MAPI-08`, `MAPI-09`, D-10, D-11). |
| Deployment/operations | **BLOCKED** | Local loopback demo is not a deployment (`MAPI-13`, D-11, D-13). |
| Scientific/domain review | **BLOCKED** | No ARC-05/ARC-08 mapping approval (`MAPI-04`, `MAPI-05`, D-09). |
| Test/release acceptance | **BLOCKED** | Local tests are not production acceptance (`MAPI-12`, D-15). |
| Collision metadata | **OPEN — TECHNICAL GAP** | Radius/method omitted from unified result. |
| Error documentation accuracy | **OPEN — TECHNICAL GAP** | GET on POST-only routes returns 404, docs imply 405. |

**Overall: B — PARTIALLY VERIFIED. Production approval: BLOCKED.**

## 3. Gap register

| ID | Gap | Severity | Verified evidence | Impact | Required closure | Responsible authority | Related IDs | Status |
|---|---|---|---|---|---|---|---|---|
| **GAP-01** | No canonical production repository, branch, or integration target for the Mission API. | Critical | `NASAQ26_MISSION_API_OWNER_DECISION_REGISTER.md:22`; multiple worktrees exist; `origin/arc/10-api-integration` is docs-only; `develop` is 47 ahead of `origin/develop`. | Any production change has no authoritative target; duplicate services or wrong-branch integration risk. | Written Project Owner/maintainer decision naming repository, branch, integration target, and permitted change boundary. | Project Owner / maintainers | `MAPI-02`, D-01 | **BLOCKED** |
| **GAP-02** | No Mission API contract owner, canonical contract location, version, or final approver. | Critical | `MAPI-07` and `MAPI-15` are `OPEN / BLOCKED`; candidate v0.1 is untracked and marked draft. | Routes, DTOs, result shape, errors, and versioning cannot become binding. | Name owner, canonical location, versioning/change process, and recorded approval. | Project Owner to designate | `MAPI-07`, `MAPI-15`, D-04, D-06–D-08 | **BLOCKED** |
| **GAP-03** | ARC-10 documentation v0.3 and v0.4 are missing. | High | Searched all five worktrees, `/mnt/e/nasa26`, `/mnt/c/Users/HP/Downloads`, and all local refs plus cached remote-tracking refs (no network fetch); only v0.1/v0.2 found. | Cannot compare, preserve, or reconcile the required versions; cannot claim conformance to them. | Locate and provide v0.3/v0.4, or record an authorized decision that they do not exist and define the controlling version. | ARC-10 document owner / Project Owner | — | **OPEN — DOCUMENT GAP** |
| **GAP-04** | No approved security architecture: authentication, authorization, CORS, secrets, network boundary, threat model. | Critical | `server.py:7` binds loopback only; no auth/CORS code in `mission_demo`; `MAPI-08` open. | The local demo cannot be exposed or treated as a production service. | Named security authority and approved controls for the chosen deployment. | Security/platform authority | `MAPI-08`, D-10, D-11 | **BLOCKED** |
| **GAP-05** | No privacy/data-rights, logging/redaction, retention, or deletion policy. | Critical | Synthetic-only local demo; no production logging/retention policy; `MAPI-09` open. | Unknown consequences if inputs/logs later contain controlled data. | Approved data classification, redaction, retention/deletion, and permitted-use record. | Privacy/data-rights authority | `MAPI-09` | **BLOCKED** |
| **GAP-06** | No production deployment/operations model: runtime, network, monitoring, runbook, rollback, release. | Critical | Loopback Uvicorn demo only; `MAPI-13` open; no deployment docs. | A demo process is not a supported service. | Named operations owner and approved deployment/operations plan. | Platform/operations authority | `MAPI-13`, D-11, D-13 | **BLOCKED** |
| **GAP-07** | No authorized ARC-05/ARC-08 domain review of mapping, units, frames, collision semantics, feasibility, score, and policy wording. | High | Local source/tests verified, but no reviewer authority; `MAPI-04`/`MAPI-05` open. | Transport could overstate scientific meaning even if structurally valid. | Named reviewers and written acceptance of the field-level mapping and labels. | Project Owner to designate ARC-05/08 reviewers | `MAPI-04`, `MAPI-05`, D-09 | **BLOCKED** |
| **GAP-08** | No authorized ARC-09 client integration target, accessibility review, or production field mapping approval. | High | Prototype + browser tests exist; `MAPI-06` open. | A prototype is not an approved production client. | Named frontend authority, target confirmation, and reviewed client mapping. | Project Owner / frontend authority | `MAPI-06`, D-02 | **BLOCKED** |
| **GAP-09** | No approved test strategy or release acceptance authority. | High | 46 local API/UI tests, 67 ARC-08 tests, 291 simulation tests pass; `MAPI-12`/D-15 open. | Local green tests do not prove transport, security, performance, or scientific suitability. | Approved acceptance matrix, environment, thresholds, and recorded result. | Test/release acceptance authority | `MAPI-12`, D-15 | **BLOCKED** |
| **GAP-10** | Unified result omits `collision_radius_m` and `collision_method`. | Medium | ARC-05 returns both (`workflow.py:50,53`); service omits both (`service.py:95-105`); candidate proposal flags it (`NASAQ26_MISSION_API_CONTRACT_PROPOSAL_V0.1.md:76`). | Consumers cannot tell which threshold/method produced a collision result; data loss across the boundary. | Contract/domain decision to expose, transform, or explicitly exclude them, with tests. | Contract owner + ARC-05 reviewer | `MAPI-04`, `MAPI-15` | **OPEN — TECHNICAL GAP** |
| **GAP-11** | Documented method behavior is imprecise: GET on POST-only mission routes returns 404, not 405. | Low | Real server: `GET /api/v1/missions/run` → 404; `POST /health` and `PUT /api/v1/missions/run` → 405; `NASAQ26_LOCAL_EDUCATIONAL_DEMO.md:116` broadly says 405. | Client error handling may misclassify a wrong-method call. Local-only impact. | Correct the doc or implement consistent 405 behavior, then add a test. | Contract owner / API owner | `MAPI-11`, `MAPI-15` | **OPEN — TECHNICAL GAP** |
| **GAP-12** | Implementation is not represented on `origin/develop`; `develop` is 47 commits ahead with uncommitted changes. | High | `git status`: ahead 47; 4 modified + 22 untracked; `origin/develop` is the initial commit. | Verification is reproducible only in this worktree; reviewers cannot fetch the verified implementation. | Maintainer decision to publish/reconcile the branch, or provide a preserved artifact/ref. | Maintainers | `MAPI-02`, D-01 | **OPEN — OWNER DECISION REQUIRED** |
| **GAP-13** | Dataset Validation API boundary is not implemented in this source. | High if Dataset Validation is in ARC-10 scope | No dataset route/DTO in `src/quantum_space_agi/mission_demo`; local doc `:59` says it is separate; `MAPI-14` open. | Risk of conflating Mission API verification with Dataset Validation deliverable. | Independent Dataset API owner, contract, and verification track. | Project Owner to designate | `MAPI-14` | **BLOCKED** (separate track) |
| **GAP-14** | `scientific_eligibility` could be incorrectly inferred from structural validation. | Medium | Not present in Mission API; only unrelated ARC-08 diagnostics use `scientific_eligibility_status`/`NOT_ASSESSED`. | Misleading scientific claim. | Maintain explicit boundary and wording; do not add the field without domain approval. | ARC-08/domain authority | `MAPI-05`, D-09 | **OPEN — OWNER DECISION REQUIRED** |
| **GAP-15** | No partial-failure, timeout, cancellation, retry, idempotency, or result-bound contract. | High | Service runs ARC-05 then ARC-08 synchronously; exceptions become generic 500; `MAPI-16` open. | Unbounded or misleading behavior under load/failure. | Recorded all-or-error/partial policy, measured limits, and acceptance tests. | Contract + operations authority | `MAPI-16`, D-12 | **BLOCKED** |
| **GAP-16** | No provenance/version/timestamp/uncertainty policy for the unified result. | Medium | Response has component versions (`evaluator_version`) and model metadata, but no run timestamp, request ID, overall contract version, or uncertainty. | Results are harder to audit or compare; consumers may assume more than is warranted. | Field-level provenance/version decision, or explicit exclusion. | Contract + domain authority | D-09 | **OPEN — OWNER DECISION REQUIRED** |
| **GAP-17** | No request/response size, array-bound, or trajectory-sample limit. | Medium | Local demo accepts payload lists constrained only by the fixed catalog; trajectory length follows fixed profiles. | Risk if profiles or catalogs expand; production bounds undefined. | Approved numeric limits and enforcement tests. | Contract + operations authority | D-12, `MAPI-16` | **OPEN — OWNER DECISION REQUIRED** |
| **GAP-18** | No human usability, accessibility certification, or cross-browser acceptance. | Low/Medium | 18 browser-backed tests passed in Chrome; no human acceptance, no multi-browser matrix. | Prototype may still have usability/accessibility gaps. | Human review and agreed browser/accessibility matrix. | ARC-09 authority | `MAPI-06`, D-15 | **OPEN — OWNER DECISION REQUIRED** |
| **GAP-19** | Ambient editable install can resolve the wrong checkout. | Low | Ambient import resolved ARC-03 checkout; fresh venv assertion passed. Documented procedure covers it. | A tester could verify the wrong source. | Keep and enforce the documented fresh-venv import assertion. | Maintainers/developers | — | **RESOLVED FOR LOCAL VERIFICATION** (documented control) |
| **GAP-20** | Collision path is not exercised by the synthetic nominal run. | Low | Actual LEO 400 km run has null collision fields; collision behavior is covered by ARC-05 tests but not this API execution. | API collision serialization is less evidenced than nominal output. | Add/execute an API-level collision scenario or record why it is out of scope. | Test owner | D-15 | **OPEN — TECHNICAL GAP** |

## 4. Decision register

The following decisions are required. None is approved. "Recommendation" is the verifier's evidence-based recommendation, not an authorization.

| ID | Decision | Options | Recommendation | Required authority | Blocks | Status |
|---|---|---|---|---|---|---|
| **DEC-01** | May `develop@6a44af3` be used as the read-only operational verification source while authority is unresolved? | (a) Yes, read-only only; (b) No, wait for owner decision. | **(a)**, explicitly limited to verification, not approval or production. | Project Owner/maintainers | Further verification | **RECOMMENDED; NOT FORMALLY APPROVED** |
| **DEC-02** | Should the local demo be promoted to the binding production contract? | (a) No, keep as educational demo; (b) Yes, with review and changes. | **(a)**. It is labelled synthetic and lacks security/deployment/scientific review. | Contract owner + Project Owner | Contract status | **RECOMMENDED; NOT FORMALLY APPROVED** |
| **DEC-03** | What is the controlling ARC-10 documentation version if v0.3/v0.4 do not exist? | (a) Locate v0.3/v0.4; (b) formally designate v0.1/v0.2 or a new version as controlling; (c) stop. | **(a)** first; if impossible, **(b)** with an explicit record. Do not silently treat v0.2 as final. | ARC-10 document owner | Contract authoring | **OPEN** |
| **DEC-04** | What are the canonical repository, branch, and integration target? | Candidate: `develop`; alternatives: a dedicated release branch or new repo. | No recommendation without owner input; `develop` is operational only. | Project Owner/maintainers | `GAP-01`, `GAP-12` | **BLOCKED** |
| **DEC-05** | Who owns and approves the contract, and what is the versioning/change process? | Named individual/role; canonical doc location; semver or other policy. | Name a single accountable owner and a recorded approval path. | Project Owner | `GAP-02` | **BLOCKED** |
| **DEC-06** | Should `collision_radius_m` and `collision_method` be exposed in the unified result? | (a) Expose both; (b) expose radius only; (c) explicitly exclude with rationale. | **(a)** if collision semantics are part of the contract; otherwise **(c)** with a documented rationale. | Contract owner + ARC-05 reviewer | `GAP-10` | **OPEN** |
| **DEC-07** | Should GET on POST-only mission routes return 404 or 405? | (a) 404 as implemented; (b) 405 consistently; (c) leave and correct docs. | Choose one and test it; document the choice. | Contract owner/API owner | `GAP-11` | **OPEN** |
| **DEC-08** | Is Dataset Validation part of ARC-10 delivery or a separate track? | (a) Separate with independent owner/contract; (b) combined. | **(a)**, consistent with Option C and the owner register. | Project Owner | `GAP-13` | **DIRECTION CONFIRMED (separate); exact ownership OPEN** |
| **DEC-09** | What security/deployment boundary applies? | Loopback developer tool; internal service; public service; other. | No recommendation without security authority. | Security/platform authority | `GAP-04`–`GAP-06` | **BLOCKED** |
| **DEC-10** | What acceptance matrix and authority apply? | Unit/API/integration/UI/security/performance/scientific; named acceptance authority. | Approve a matrix that separates local verification from production acceptance. | Test/release authority | `GAP-09` | **BLOCKED** |
| **DEC-11** | How should the verified `develop` state be preserved/published? | (a) Commit/push after review; (b) tag/archive; (c) leave local. | Preserve a reproducible ref or artifact before relying on the verification. | Maintainers | `GAP-12` | **OPEN** |
| **DEC-12** | What are the partial-failure, timeout, cancellation, retry, idempotency, and size limits? | All-or-error vs partial; bounded synchronous vs async; per-request limits. | Define explicit bounds and failure semantics before production. | Contract + operations authority | `GAP-15`, `GAP-17` | **BLOCKED** |
| **DEC-13** | How should scientific eligibility be represented or excluded? | (a) Exclude from Mission API; (b) add only after domain review. | **(a)** now; do not infer eligibility from validation. | ARC-08/domain authority | `GAP-14` | **RECOMMENDED; NOT FORMALLY APPROVED** |
| **DEC-14** | Should provenance, contract version, run timestamp, request ID, and uncertainty be exposed? | Expose a defined subset; or explicitly exclude. | Define a minimal provenance/version set before production. | Contract + domain authority | `GAP-16` | **OPEN** |

## 5. What would change the final status

### B → A (verified with no material gaps)

All of the following would be required:

1. Written canonical repository/branch decision (`MAPI-02`, `GAP-01`).
2. Written contract owner, version, and approval (`MAPI-07`, `MAPI-15`, `GAP-02`).
3. ARC-10 v0.3/v0.4 located or an authorized controlling-version decision (`GAP-03`).
4. Approved security/privacy/deployment model (`GAP-04`–`GAP-06`).
5. Named ARC-05/ARC-08/ARC-09 reviewers and accepted mappings (`GAP-07`, `GAP-08`).
6. Approved acceptance matrix and recorded results (`GAP-09`).
7. Collision/error/method decisions closed with tests (`GAP-10`, `GAP-11`, `GAP-20`).
8. Verified implementation preserved in a reproducible ref (`GAP-12`).
9. Partial-failure/limits/provenance decisions recorded (`GAP-15`–`GAP-17`).

### B → C (partially verified with a critical unresolved defect)

Would apply if a verified six-artifact behavior were found materially wrong or unsafe, for example:

- the local backend did not actually execute ARC-05/ARC-08,
- the API fabricated results,
- non-finite or corrupt data reached clients,
- a security boundary was falsely claimed,
- the unified result contradicted the documented contract in a way that misleads users.

None of those was found.

### B → D (not verified)

Would apply if the implementation were inaccessible, unrunnable, or absent. It was accessible, runnable, and evidenced.

### B → E (blocked)

Would apply if the only correct action were to stop. Verification could proceed read-only without inventing authority, so a full stop was not necessary. Production work remains blocked.

## 6. Recommended next actions (in order)

1. Obtain the Project Owner decision on canonical repository/branch and contract ownership (`DEC-04`, `DEC-05`).
2. Locate ARC-10 v0.3/v0.4 or record the controlling-version decision (`DEC-03`).
3. Preserve the verified `develop` state in a reproducible ref (`DEC-11`).
4. Convene ARC-05/ARC-08/ARC-09 domain and client reviews (`GAP-07`, `GAP-08`).
5. Decide collision metadata, GET/405 behavior, and partial-failure/limits (`DEC-06`, `DEC-07`, `DEC-12`).
6. Obtain security/privacy/deployment approval (`DEC-09`).
7. Obtain test/release acceptance (`DEC-10`).
8. Only then change the six artifacts from `DRAFT`/`VERIFIED AGAINST IMPLEMENTATION` to `FORMALLY APPROVED`.

## 7. Final verdict

**B — PARTIALLY VERIFIED.**

- Six artifacts: implemented and verified against the local operational source.
- Authority, contract, security, deployment, domain review, and acceptance: **NOT APPROVED / BLOCKED**.
- Required ARC-10 v0.3/v0.4: **NOT FOUND**.
- No fabricated route, request, response, approval, or evidence was introduced.
