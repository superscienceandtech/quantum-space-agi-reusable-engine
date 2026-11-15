# ARC-10 Project Owner Decision Form

Repository: `/mnt/e/nasa26/nasaq26-develop-worktree`
Branch: `develop`
Full HEAD: `6a44af34a649a1138cf577b3b16dbaf436c8a203`
Current status: `B — PARTIALLY VERIFIED`
Baseline: `LOCAL_SYNTHETIC_DEMO_BASELINE — NOT PRODUCTION APPROVED`

This form is a decision record only. It does not approve implementation, deployment, or any production contract.

Project Owner decisions captured in this task are explicit and recorded below. D-06 remains pending clarification.

## Decision D-01 — Canonical repository/branch authority for ARC-10

- Exact owner decision: `develop` is the current verification baseline ONLY. It is not the canonical production repository.
- Status: `APPROVED — LIMITED SCOPE`
- Evidence currently available:
  - `docs/ARC10_AUTHORITATIVE_SOURCE_DISCOVERY.md`
  - `docs/ARC10_GAP_AND_DECISION_REGISTER.md`
  - git status confirms the current worktree is the verified local baseline and is not a production approval target
- Technical consequences:
  - the verified worktree remains a local baseline for evidence and review only
  - no canonical production repository or branch is inferred from this decision
- Follow-up action:
  - retain the current worktree as a limited-scope verification baseline until a canonical production target is named
- Approval date: blank (not recorded)
- Authority: Project Owner

## Decision D-02 — Contract owner and approval authority

- Exact owner decision: Project Owner owns final contract approval. Technical contributors prepare drafts and evidence.
- Status: `APPROVED`
- Evidence currently available:
  - `docs/ARC10_PROJECT_OWNER_APPROVAL_REQUEST.md`
  - `docs/ARC10_GAP_AND_DECISION_REGISTER.md`
- Technical consequences:
  - all contract drafts remain non-binding until Project Owner approval
  - contributor work remains evidence and proposal material, not authority
- Follow-up action:
  - direct all contract drafting and evidence collection to the current local baseline without assuming approval
- Approval date: blank (not recorded)
- Authority: Project Owner

## Decision D-03 — Contract versioning baseline and missing ARC-10 v0.3/v0.4 artifacts

- Exact owner decision: Prepare a controlled reconstruction proposal using existing evidence. Do not invent missing documents or designate a canonical contract version.
- Status: `APPROVED — PROPOSAL ONLY`
- Evidence currently available:
  - `docs/ARC10_GAP_AND_DECISION_REGISTER.md`
  - `docs/ARC10_PROJECT_OWNER_APPROVAL_REQUEST.md`
  - v0.3/v0.4 artifacts are absent from reviewed workspaces and refs
- Technical consequences:
  - no canonical contract version is adopted from missing artifacts
  - version resolution remains a proposal and governance task, not implementation
- Follow-up action:
  - create `docs/ARC10_CONTROLLED_CONTRACT_RECONSTRUCTION_PROPOSAL.md` and use it as the baseline proposal only
- Approval date: blank (not recorded)
- Authority: Project Owner

## Decision D-04 — Collision metadata in the public Mission API contract

- Exact owner decision: Exclude collision metadata from the public Mission API response for now. Future inclusion requires explicit contract review and Project Owner approval.
- Status: `APPROVED — CURRENT SCOPE ONLY`
- Evidence currently available:
  - `src/quantum_space_agi/simulation/workflow.py` emits collision metadata
  - `src/quantum_space_agi/mission_demo/service.py` omits it from the public summary
  - `docs/ARC10_GAP_AND_DECISION_REGISTER.md` records the gap
- Technical consequences:
  - current local baseline remains intentionally limited to the current public contract surface
  - any future inclusion requires a separate contract review
- Follow-up action:
  - keep the omission documented as the approved current-scope decision
- Approval date: blank (not recorded)
- Authority: Project Owner

## Decision D-05 — Unsupported methods on POST-only routes: 404 or 405

- Exact owner decision: Use `404 Not Found` for unsupported methods on the current POST-only local demo routes. Update documentation only. Do not change implementation or generalize this decision to production APIs.
- Status: `APPROVED — LOCAL DEMO ONLY`
- Evidence currently available:
  - current local demo behavior and documentation are consistent with this decision for the local scope
  - `src/quantum_space_agi/mission_demo/api.py` and `tests/mission_demo/test_api.py` show the current local behavior
- Technical consequences:
  - the local demo rule is fixed and documented only
  - the decision is intentionally scoped to the current demo and not production
- Follow-up action:
  - update local demo documentation to match the decision without changing implementation or production assumptions
- Approval date: blank (not recorded)
- Authority: Project Owner

## Decision D-06 — Formal production boundary and required governance approvals

- Exact owner decision: `Other` was selected, but no explicit production authorization was supplied. Time is limited, but this does not mean production approval.
- Status: `PENDING — CLARIFICATION REQUIRED`
- Evidence currently available:
  - `docs/ARC10_GAP_AND_DECISION_REGISTER.md`
  - `docs/ARC10_PROJECT_OWNER_APPROVAL_REQUEST.md`
  - local synthetic demo remains verified but not production approved
- Technical consequences:
  - production contract baseline remains blocked until explicit clarification
  - security, privacy, scientific/domain, deployment, and acceptance approvals remain separately required
- Follow-up action:
  - ask the owner: "Do you authorize preparation of a formal production-contract baseline review ONLY, without implementation, external integration, or deployment, while security, privacy, scientific/domain, deployment, and acceptance approvals remain separately required?"
- Approval date: blank (not recorded)
- Authority: Project Owner

## Summary

D-01 to D-05 are recorded as explicit Project Owner decisions and remain within the current local-demo scope. D-06 remains pending clarification. The current verified baseline remains `LOCAL_SYNTHETIC_DEMO_BASELINE — NOT PRODUCTION APPROVED`.
