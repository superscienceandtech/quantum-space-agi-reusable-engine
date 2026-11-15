# NASAQ26 Multi-ARC Audit and Authorized Remediation Design

**Status: DRAFT — FOR PROJECT OWNER REVIEW**

## Purpose

Produce an evidence-backed audit of the accessible NASAQ26 repositories and
worktrees, covering ARC-01 through ARC-11, and remediate verified defects only
within the Project Owner's stated authorization. The audit must report the
state actually present in each worktree rather than treating documents or
branch names as proof of implementation.

## Confirmed constraints

- Preserve all existing modified and untracked files.
- Do not delete, reset, clean, or overwrite user work.
- Do not commit, push, merge, rewrite history, or deploy.
- Do not expose credentials, tokens, private data, or sensitive report content.
- Do not acquire restricted NASA data or claim synthetic results as NASA data.
- Keep Dataset Validation and Mission Planning APIs separate.
- Treat ARC-10 v0.2 as draft/non-canonical; preserve the unresolved D-04/D-05
  discrepancy and all other governance blockers.
- Do not implement unapproved production contracts or change official
  governance decisions.
- Screen-reader/WCAG, scientific, security, and test claims require direct
  verification and explicit limitations.
- The local Mission Builder non-JSON error fallback is authorized for
  investigation and implementation; that authorization does not create or
  approve a backend endpoint.

## Repository evidence model

The initial inventory found five linked worktrees:

| Worktree | Branch | HEAD | Initial condition |
|---|---|---|---|
| `/mnt/e/nasa26/quantum-space-agi-reusable-engine` | `arc/03-data-engineering` | `8b8f21fc3ff42286cd6e4894ad25616c9df87354` | Modified data loader/module and test files |
| `/mnt/e/nasa26/nasaq26-develop-worktree` | `develop` | `6a44af34a649a1138cf577b3b16dbaf436c8a203` | Modified ARC-09 files plus existing untracked reports/test |
| `/mnt/e/nasa26/nasaq26-docs-worktree` | `docs/arc09-arc10-governance-sync` | `874d3e89f371a1762f735a3955b096c5d3307a31` | Modified governance reports plus untracked reports |
| `/mnt/e/nasa26/nasaq26-integration-worktree` | `integration/nasaq26-branch-reconciliation` | `d7ac272af842445733c89074de310d706aed537c` | Untracked ARC-10 reports and plan |
| `/mnt/e/nasa26/nasaq26-local-mission-demo-worktree` | `feat/nasaq26-local-mission-demo` | `dd79bc27523e845a7ae8e8c6164b5fcc3513f2eb` | Untracked local mission-demo source and tests |

These are separate evidence snapshots, not a clean canonical tree. The
repository contributing guide names `develop` as the default pull-request
target, but does not establish a single authoritative working copy. Audit
claims will identify the worktree and commit they describe. No snapshot will
be merged into another as part of this work.

## Audit structure

The audit will use one common evidence template for every ARC:

- implementation state and exact evidence paths/symbols;
- behavior verified and behavior absent or unverified;
- relevant tests and actual command results;
- dependencies and technical limitations;
- security, scientific, accessibility, and data-provenance risks where
  applicable;
- documentation, ownership, approval, and governance gaps;
- severity, confidence, and a bounded recommended next action.

Findings will distinguish `VERIFIED`, `IMPLEMENTED`, `TESTED`, `DRAFT`,
`PROPOSED`, `BLOCKED`, `NOT TESTED`, and `REQUIRES APPROVAL`. Existing
uncommitted and untracked work will be identified as pre-existing or
task-produced; uncertain attribution will be stated rather than inferred.

The work is divided into these review streams:

1. Repository/worktree baseline, instructions, branches, and project-wide
   integration state.
2. ARC-01 through ARC-04: foundation, memory, artifacts/data provenance, and
   biomedical/scientific model evidence.
3. ARC-05 through ARC-08: simulation, quantum, robotics, cybersecurity, and
   resource/dataset evaluation evidence.
4. ARC-09: dashboard, charts, accessibility, responsive behavior, local demo
   behavior, and owner-approved local error handling.
5. ARC-10 and ARC-11: DTO/contracts/governance and curriculum/knowledge-graph
   evidence.
6. Cross-worktree synthesis, prioritized risks, tests, and handover.

Each stream must cite the exact worktree and source/test evidence. A reported
capability in a document without corresponding current code/test evidence is
not considered verified.

## Remediation boundaries

After review, implement verified, authorized code fixes on a worktree selected
from the evidence without discarding existing user work. If two snapshots
contain conflicting versions of the affected implementation, stop and request
Project Owner direction before editing either version. The specifically
authorized Mission Builder fix is limited to presenting a non-empty,
actionable error for non-JSON/non-OK local responses, preserving disabled
controls, and verifying error semantics. No endpoint, backend, contract, or
production behavior will be added.

Other verified defects may be fixed only when the change is clearly within the
provided authorization, has focused regression coverage, and does not require
an unapproved interface, scientific assumption, ownership decision, or
governance change. Otherwise document the blocker and recommended decision.

## Verification

Use the test and quality commands defined by the applicable checkout. At
minimum, run focused ARC-09 and mission-demo tests and the full project suite
where practical. Run static analysis, build, API contract tests, and security
checks only when the available repository/tooling supports them and the scope
is clear. Record exact commands, checkout/commit, environment, counts, and
failures/skips. Do not repair unrelated baseline failures as part of this
review.

For ARC-09, repeat available browser checks and use axe or equivalent tooling
only if present. Execute a screen-reader review only if a supported screen
reader is available. Do not claim WCAG conformance without sufficient
evidence.

## Deliverables and final state

The final handover will contain:

- repository/worktree/branch/HEAD/status inventory;
- ARC-01 through ARC-11 status matrix;
- exact source/test evidence for verified behavior;
- implemented changes and worktree locations;
- exact test/static/security/accessibility results and unavailable checks;
- prioritized defect/risk register;
- ARC-10 decisions, drafts, blockers, and approval boundaries;
- NASA data provenance and scientific limitations;
- handover/acceptance state and a numbered next-action list.

No contributor acceptance, Project Owner closure, contract approval,
production readiness, or deployment authorization will be inferred.

**Final status must be one of:** A — Ready for Project Owner Closure Review;
B — Conditionally Ready; C — Not Ready; or D — Blocked. The status will follow
the evidence and open approvals, not test results alone.

## Self-review

- Scope covers the requested ARC-01–ARC-11 audit without combining separate
  API contracts or changing governance.
- The local Mission Builder defect is bounded to frontend error presentation;
  backend/API creation is explicitly excluded.
- The five worktrees and existing dirty states are treated as separate
  evidence; no canonical snapshot is invented.
- Conflicting implementation snapshots trigger an owner decision rather than
  an assumed merge or overwrite.
- The design requires exact verification evidence and records unavailable
  screen-reader/axe tooling without claiming compliance.
- No commit or external action is included.
