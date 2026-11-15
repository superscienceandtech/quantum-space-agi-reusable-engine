# ARC-10 Project Owner Decisions Required

Repository: `/mnt/e/nasa26/nasaq26-develop-worktree`
Branch: `develop`
Full HEAD: `6a44af34a649a1138cf577b3b16dbaf436c8a203`
Current status: `B — PARTIALLY VERIFIED`
Baseline: `LOCAL_SYNTHETIC_DEMO_BASELINE — NOT PRODUCTION APPROVED`

Explicit Project Owner decisions are recorded for D-01 through D-05. D-06 remains open and requires a single explicit yes/no clarification before a formal production-contract baseline review can be authorized.

## D-01 — Canonical repository/branch authority for ARC-10

Status: `APPROVED — LIMITED SCOPE`
Exact decision: `develop` is the current verification baseline ONLY. It is not the canonical production repository.

## D-02 — Contract owner and approval authority

Status: `APPROVED`
Exact decision: Project Owner owns final contract approval. Technical contributors prepare drafts and evidence.

## D-03 — Contract versioning baseline and missing ARC-10 v0.3/v0.4 artifacts

Status: `APPROVED — PROPOSAL ONLY`
Exact decision: Prepare a controlled reconstruction proposal using existing evidence. Do not invent missing documents or designate a canonical contract version.

## D-04 — Collision metadata in the public Mission API contract

Status: `APPROVED — CURRENT SCOPE ONLY`
Exact decision: Exclude collision metadata from the public Mission API response for now. Future inclusion requires explicit contract review and Project Owner approval.

## D-05 — Unsupported methods on POST-only routes: 404 vs 405

Status: `APPROVED — LOCAL DEMO ONLY`
Exact decision: Use `404 Not Found` for unsupported methods on the current POST-only local demo routes. Update documentation only. Do not change implementation or generalize this decision to production APIs.

## D-06 — Formal production boundary and required approvals

Status: `PENDING — CLARIFICATION REQUIRED`
Question to the Project Owner:

"Do you authorize preparation of a formal production-contract baseline review ONLY, without implementation, external integration, or deployment, while security, privacy, scientific/domain, deployment, and acceptance approvals remain separately required?"

Allowed answers:
- `YES — review preparation only`
- `NO — keep production work blocked`

## Current status

D-01 through D-05 are resolved at the current local-demo scope. D-06 remains pending. No production approval is recorded, and no production implementation or deployment authorization is implied by this file.
