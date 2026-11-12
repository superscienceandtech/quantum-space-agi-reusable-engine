# Copy-Ready Distribution Draft — Amran — ARC-04 / ARC-05

**Status:** Draft only. Not sent. No acknowledgement recorded.

## Message

**Subject:** NASAQ_26 — ARC-04 / ARC-05 evidence and status request

Hi Amran,

Yousuf is coordinating project review as Project Owner and AI/ML Technical Lead. This draft work order requests a current evidence report for your proposed ARC-04/05 responsibilities. Please review the attached [ARC-04/05 Work Order v2](NASAQ26_AMRAN_ARC04_ARC05_WORK_ORDER_v2.md) and the six acceptance rows below. Report ARC-04 and ARC-05 separately.

Please reply explicitly with:

1. **Receipt:** “Received” confirms only that you received this work order.
2. **Assignment:** “I accept” or “I cannot accept” the stated ARC-04/05 scope and responsibilities; list any correction or constraint. Receipt alone is not acceptance.
3. **Work commencement:** if accepted, give the date you expect to begin or state that evidence collection is already underway. Assignment acceptance does not itself mean work has begun.

For each ARC, report repository/branch and exact scope; diff/base; existing test and notebook evidence; environment; manifest; PR recommendation; blockers. Include actual logs or links and say `NOT RUN` / `NOT AVAILABLE` where evidence does not exist. This request does not ask you to rerun tests or notebooks. Do not infer test success from prior messages or branch names.

When ready, submit the deliverables with exact evidence links/paths, repository revision, and date checked. Submission is separate from both receipt and assignment acceptance. Yousuf will review each item and record acceptance, changes requested, or an unresolved blocker; submission does not mean project-owner acceptance.

Please preserve these three existing ARC-03 modified files exactly; do not stage, clean, or overwrite them:

- `src/quantum_space_agi/data/__init__.py`
- `src/quantum_space_agi/data/loader.py`
- `tests/test_data_loader.py`

Do not access restricted/real NASA data, change frozen evidence, or take release actions without the applicable authorization. No approval or test result is implied by this request.

Thank you,
Yousuf

## Assigned acceptance-matrix rows — Amran only

The following are the six Amran rows from `NASAQ26_TEAM_DELIVERABLE_ACCEPTANCE_MATRIX_v2.csv`; the complete work-order detail is in the attached v2 document.

| ID | Deliverable | Acceptance criterion | Evidence / blocker note |
|---|---|---|---|
| A1 | Repository and branch identity | Canonical repo/path, active vs snapshot, branch, HEAD/base, owner where evidenced, checked timestamp/timezone. | Add exact path/URL, revision/hash and date when received. Missing evidence is not inferred. |
| A2 | Exact changed-file inventory and diff | All modified/staged/untracked/added/deleted/generated files listed; per-file summary, exact base and ownership/shared-file caveats. | Identify missing logs/files and preserve protected ARC-03 paths. |
| A3 | Test evidence and environment | Actual commands/logs/exit codes, execution time, OS/runtime/dependencies/environment and tested commit; PASS/FAIL/SKIPPED/NOT RUN distinct. | No rerun required by this request; unsupported success claims are not accepted. |
| A4 | Notebook execution evidence | Paths/hashes, execution record, kernel/environment, outputs/errors and saved-output provenance; NOT RUN/NOT AVAILABLE allowed. | Restricted inputs remain authorization-gated; frozen evidence must not be changed. |
| A5 | SHA256 manifest | Manifest/tool/version/time/scope and result; local digest distinguished from trusted custody manifest. | Hashes do not prove authorship or approval. |
| A6 | PR recommendation and blockers | PR/base/current state/checks/reviews observed at time checked; recommendation, blockers, owners/dependencies and next steps; ARC-04/05 separate. | Current PR state must be evidence-based or marked unavailable. |

**Initial matrix state for each row:** assignment `PROPOSED`; dispatch `NOT_SENT`; acknowledgement `NOT_RECEIVED`; deliverable `NOT_STARTED`; verification `NOT_STARTED`; acceptance `NOT_REVIEWED`. These are initial records, not a claim about your response.
