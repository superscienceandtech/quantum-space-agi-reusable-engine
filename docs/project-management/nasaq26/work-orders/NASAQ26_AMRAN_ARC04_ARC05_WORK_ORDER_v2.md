# Work Order Draft v2 — Amran — ARC-04 / ARC-05 Execution Evidence

**Dispatch state:** SENT.  
**Assignment state:** PROPOSED; acknowledgement not recorded.  
**Responsible scope:** ARC-04 and ARC-05 execution/evidence, as proposed in the Project Owner responsibility model.  
**Purpose:** Collect and report current work evidence separately for each ARC. This request does not claim that work or checks have passed.

## Deliverables

Submit one ARC-04 report and one ARC-05 report. Each report must include:

1. **Repository and branch identity:** canonical repository URL/name, checkout path, branch, HEAD commit, upstream and intended PR base, check date/time/timezone, and whether each reference is the active checkout or a local remote-tracking snapshot.
2. **Exact changed-file scope:** modified, staged, untracked, added, deleted, and generated paths. Identify file ownership when known; call out shared or unrelated files without attributing them to yourself unless verified. Do not stage, clean, or overwrite files to produce this inventory.
3. **Diff summary:** exact base commit and per-file change summary, rationale, additions/deletions where available, linked diff or PR, and any unreviewable path or omitted content.
4. **Existing test evidence:** exact commands, raw or linked logs, exit status, timestamp/timezone, OS, runtime and relevant dependencies, environment/kernel, working directory, tested commit/tree, and separate PASS/FAIL/SKIPPED/NOT RUN outcomes. Do not infer success from plans, caches, prior messages, or source presence. If a check was not run, say `NOT RUN`; this order does not require rerunning it.
5. **Existing notebook evidence:** notebook paths and hashes; execution record/command, kernel/environment and time; outputs/errors and validation results; whether saved outputs are from that run or pre-existing. If no execution evidence exists, state `NOT AVAILABLE` / `NOT RUN`. Do not execute notebooks with restricted/real NASA inputs without applicable authorization; do not alter frozen scientific notebooks or outputs.
6. **SHA256 manifest evidence:** manifest path, tool/method and version, generation time, covered paths, and comparison result. Distinguish a newly computed integrity list from a trusted custody/source manifest. Hashes alone do not prove authorship or approval.
7. **PR recommendation:** PR URL/number if one exists, target/base branch and commit, observed PR state/time, conflicts, checks/reviews and recommendation: `READY_FOR_REVIEW`, `CHANGES_REQUIRED`, `BLOCKED`, or `NO_PR`. If unavailable, say so. Do not create/submit a PR, stage, commit, or push for this report.
8. **Blockers and handover:** each blocker’s evidence, responsible owner if known, dependency/decision, impact, next action, and what remains unverified. Separate ARC-04 from ARC-05.

## Acceptance criteria

- ARC-04 and ARC-05 are separately attributable and tied to exact repository revisions and bases.
- The complete changed/untracked path lists are present; no assertion of clean scope without supporting evidence.
- Actual test/notebook outcomes have logs and environment details; missing checks are explicitly `NOT RUN` or `NOT AVAILABLE`.
- PR state and recommendation are based on observable evidence and time checked, not branch existence.
- Every manifest states its coverage and limitations.
- No result, approval, scientific claim, or completion is inferred from artifacts, previous messages, branch refs, or synthetic data.
- Routine inspection/reporting is within the proposed role; gated data access, scope changes, or release decisions are referred to the appropriate authority.

## Protected work and context

The active checkout observed in the prior local audit is `quantum-space-agi-reusable-engine`, branch `arc/03-data-engineering`, HEAD `8b8f21f`. Preserve these three existing modifications exactly and do not stage, clean, or overwrite them:

- `src/quantum_space_agi/data/__init__.py`
- `src/quantum_space_agi/data/loader.py`
- `tests/test_data_loader.py`

The local `origin/main` snapshot at `401bba6` contains ARC-04 documentation/notebook material and ARC-05 simulation docs/notebooks. The local `origin/arc/04-scientific-computing` and `origin/arc/05-simulation` refs seen earlier pointed at the initial commit; remote-tracking refs were not refreshed for this package. Treat these as historical local snapshot facts, not current remote or delivery status. No current test result is asserted.

**Governance:** This is an evidence request, not scientific/data approval. No restricted or NASA data access, experimentation, frozen-evidence change, or release is authorized by this work order.
