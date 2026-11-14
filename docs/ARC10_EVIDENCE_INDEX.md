# ARC-10 Evidence Index

**Checked:** 2026-11-13. **Scope:** Read-only inspection of the ARC-10 worktree and locally available Git refs. No live GitHub state was checked.

## 1. Current status

| Item | Status | Evidence boundary |
|---|---|---|
| Canonical ARC-10 Decision & Approval Register | NOT LOCATED | Not found in the inspected worktree, tracked tree/history, or available local refs. This is not an organization-wide or live GitHub search. |
| Local decision package | NON-CANONICAL WORKING MIRROR — NOT AN APPROVED REGISTER | `docs/ARC10_API_CONTRACT_AND_DECISION_PACKAGE.md` is a proposal for decision; its approval fields are NOT GRANTED. The recovery report explicitly labels it WORKING MIRROR — NOT CANONICAL. |
| D-01–D-16 numbering discrepancy | OPEN | Supplied Work Order context calls D-05 the framework decision; the local mirror assigns framework/runtime to D-04 and endpoints/method/versioning to D-05. No authoritative numbering reference was located. |
| Production implementation gate | BLOCKED | `docs/ARC10_IMPLEMENTATION_AUTHORIZATION_GATE.md`, §1, says IMPLEMENTATION_GATE: BLOCKED. |
| Final Project Owner evidence acceptance | ACCEPTED WITH DOCUMENTED LIMITATIONS | Recorded in `docs/ARC10_PROJECT_OWNER_EVIDENCE_ACCEPTANCE.md`; acceptance covers the evidence package only, not API architecture, contract, or implementation authorization. |

No canonical register custodian or authority responsible for designating its location was identified in repository evidence. `docs/ARC10_PROJECT_DECISION_REQUEST.md` requests project decisions and has an unfilled response template; it does not designate a register maintainer. The task-provided context says Project Owner Yousuf acknowledged the prior report and requested follow-up; that context does not establish a canonical register location or custodian in the inspected repository.

## 2. Canonical-register investigation

### Search scope

Inspected current ARC-10 worktree documentation, including the recovery report, decision package, project decision request, implementation authorization gate, use-case comparison, contract-neutral design, service-boundary test strategy, and the four original planning reports. Inspected available local branches and remote-tracking refs with `git branch -avv` and `git for-each-ref`, searched Markdown in those refs with `git grep`, and checked reachable path history with `git log --all --name-only`.

Relevant refs include `arc/10-api-integration` and cached `origin/arc/10-api-integration` at 69c8e711b9e8f3af5c39428e23828ade9e55da2a, cached `origin/main` at 9d65c9547e9c3c59f65c3b81265c7152c8385859, and cached `origin/arc/09-visualization` at 878cb81b69430cdf6c25c419edba587629537768. The refs are local snapshots and may be stale. No fetch or external request was made.

### Register candidates and findings

| Material | Classification | Evidence and limitation |
|---|---|---|
| ARC-10 Decision & Approval Register / canonical location | NOT LOCATED IN INSPECTED MATERIAL | No matching ARC-10 register path or explicit canonical-location designation was found in the inspected worktree, available refs, or reachable path history. The only register-like path found in reachable history was `docs/ARC09_DECISION_REGISTER.md`, which is ARC-09 and is not ARC-10 authority. |
| `docs/ARC10_API_CONTRACT_AND_DECISION_PACKAGE.md`, §6, “Formal decision register” | CANDIDATE — NOT VERIFIED AS CANONICAL | The file header calls it a proposal for decision; its text says no approval is granted and each approval field is NOT GRANTED. It contains D-01–D-18 proposals/statuses, not evidence of canonical designation. The recovery report labels this file NON-CANONICAL WORKING MIRROR — NOT AN APPROVED REGISTER. |
| `docs/ARC10_IMPLEMENTATION_AUTHORIZATION_GATE.md`, §§1–2 | VERIFIED as an assessment, not a register | It calls itself an evidence assessment, states the implementation gate is BLOCKED, and says no completed formal approval was found. It does not designate a register custodian. |
| `docs/ARC10_PROJECT_DECISION_REQUEST.md`, decision request and response template | VERIFIED as a request, not a register | It asks for decisions and contains NOT DECIDED / NOT GRANTED response fields. No completed response or register-maintenance designation is present. |
| `docs/ARC10_WORK_ORDER_V2_REGISTER_RECOVERY_AND_READINESS.md`, §§2–3 and §9 | VERIFIED as a recovery report, not canonical authority | It records CANONICAL_REGISTER: NOT LOCATED, labels the local package WORKING MIRROR — NOT CANONICAL, and records the D-04/D-05 discrepancy as unresolved. |

**Authority result:** No person or role is explicitly assigned in the inspected repository evidence to maintain or designate the canonical ARC-10 register. The project decision authority needed to resolve product/architecture decisions is not the same as a documented register custodian. Ask the Project Owner or established project governance process to identify the canonical source, its owner, revision, and numbering authority; do not assume that the requester is its custodian.

## 3. D-04 / D-05 discrepancy — OPEN

The supplied Work Order context refers to D-05 as the framework decision. The local non-canonical mirror at `docs/ARC10_API_CONTRACT_AND_DECISION_PACKAGE.md`, §6, labels D-04 as backend architecture/framework/runtime and D-05 as endpoint paths, methods, and versioning. The Work Order file itself was not located in the inspected worktree or tracked ARC-10 HEAD, so its numbering could not be tied to a repository revision. No renumbering, editing, or reconciliation is performed here. An authoritative register or explicit project decision is required.

## 4. Recovery report and checksum verification

The following SHA256 values were recalculated directly from each file's current bytes and match the values supplied for verification.

| Path | Bytes | SHA256 | Current Git status |
|---|---:|---|---|
| `docs/ARC10_WORK_ORDER_V2_REGISTER_RECOVERY_AND_READINESS.md` | 21,865 | `0e48922ce9c290d031ee73b55a18e3e47e577b173c4454a19d8b753475cf409e` | Untracked; not ignored |

## 5. Four original planning reports

All four paths are tracked in commit `69c8e711b9e8f3af5c39428e23828ade9e55da2a`, subject `docs(arc-10): add API integration planning reports`. Independent `git show --name-only` inspection found exactly these four files in that commit. Their content is planning/proposal material, not formal approval evidence.

| Path | Bytes | SHA256 | Purpose and evidence status |
|---|---:|---|---|
| `docs/ARC10_REPOSITORY_API_READINESS_REPORT.md` | 13,998 | `495a4fd181d1c3cefee5fe0ab0783b8b1220f913dbc9dea3e2c4045282d06940` | Repository/API readiness audit; records verified baseline facts and unresolved gates. It explicitly does not approve architecture, contract, science, or implementation. |
| `docs/ARC10_BACKEND_API_ARCHITECTURE_PROPOSAL.md` | 14,083 | `2d3da096c91c76ebf84e35c0a175652a16a604eae73d89e290df48c8b93a94d4` | Architecture proposal; compares framework options but selects none and does not authorize implementation. |
| `docs/ARC10_API_ENDPOINT_REQUIREMENTS_AND_DRAFT_SCHEMAS.md` | 14,920 | `2f25f3e2489f9d2af87da94bd6b4a88384f296ca397b34121015f2a83b6cb661` | Endpoint/schema preparation; identifies examples as illustrative and not approved. |
| `docs/ARC10_IMPLEMENTATION_PLAN_AND_TEST_STRATEGY.md` | 15,462 | `283c7b8bbacb7c54707e4215a073d5125a16429ad8ee781a0c90e9d0b9c54fbf` | Implementation plan and test strategy; gates implementation on target, use-case, architecture, and contract decisions. |

A commit establishes repository history and file inclusion only; it does not establish Project Owner approval, review, or publication to an authoritative register.

## 6. Working mirror and supporting references

- **NON-CANONICAL WORKING MIRROR — NOT AN APPROVED REGISTER:** `docs/ARC10_API_CONTRACT_AND_DECISION_PACKAGE.md`, especially §6. It contains D-01–D-18 questions and proposals; its approval column is NOT GRANTED. Do not treat its D numbering/statuses as canonical.
- `docs/ARC10_IMPLEMENTATION_AUTHORIZATION_GATE.md` is a supporting readiness assessment and states BLOCKED; it is not an approval record.
- `docs/ARC10_WORK_ORDER_V2_REGISTER_RECOVERY_AND_READINESS.md` is the recovery report; it records the prior search boundary and open discrepancy.

## 7. Evidence classifications

### Verified repository facts

- The ARC-10 worktree is on `arc/10-api-integration`, HEAD `69c8e711b9e8f3af5c39428e23828ade9e55da2a` at this inspection. The recovery report and six other ARC-10 working documents are untracked; no staged or tracked modifications were reported.
- The original four reports are tracked in the identified commit; the recalculated checksums above match the requested prior checksums.
- The local decision package describes itself as a proposal and records NOT GRANTED approvals. The authorization gate explicitly reports BLOCKED.
- No ARC-10 register-designation authority was found in the searched material.

### Unresolved decisions and dependencies

Canonical register location, custodian, authoritative D numbering, completed decisions, production backend target, first approved use case/consumer, contract owner, API contract, architecture/framework, security/data-handling rules, acceptance, and implementation authorization remain unresolved or blocked in the inspected repository evidence.

### Proposed recommendations

Mechanical schema validation as a candidate use case, layered architecture, framework options, endpoint/schema examples, and operational/privacy controls are proposals in the planning materials. None is promoted to a decision by this index.

### Formal approvals still required

No formal production API approval or implementation authorization was found. The Project Owner evidence-package acceptance is recorded in `docs/ARC10_PROJECT_OWNER_EVIDENCE_ACCEPTANCE.md` and does not constitute API approval. The decision request refers to project/product, engineering, architecture, contract, security/platform, and scientific/data authorities as roles to identify; it does not name an approved register custodian. Document author, technical reviewer, contract owner, decision-maker, and approval authority remain separate roles.

## 8. Investigation limitations

This index reflects only the current ARC-10 worktree, tracked content and history reachable from locally available branches/refs, and task-provided context noted above. No live GitHub state, external organization storage, private messages, or unpushed work was searched. Cached `origin/*` refs may be stale. The search therefore supports NOT LOCATED IN INSPECTED MATERIAL, not a claim that no canonical register exists anywhere.

No production API implementation, NASA access, or dataset activity was performed. The D-04/D-05 discrepancy remains open, and the implementation gate remains BLOCKED.
