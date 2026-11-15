# ARC-10 Contract Versioning and Provenance

Repository: `/mnt/e/nasa26/nasaq26-develop-worktree`
Branch: `develop`
Full HEAD: `6a44af34a649a1138cf577b3b16dbaf436c8a203`
Current status: `B — PARTIALLY VERIFIED`
Baseline: `LOCAL_SYNTHETIC_DEMO_BASELINE — NOT PRODUCTION APPROVED`

## 1. Purpose

This document captures versioning and provenance requirements for the ARC-10 review package. It does not create a production contract or authorize implementation.

## 2. Available contract artifacts

The following reviewed artifacts are available in the current worktree:

- `docs/ARC10_AUTHORITATIVE_SOURCE_DISCOVERY.md`
- `docs/ARC10_SIX_ARTIFACT_IMPLEMENTATION_VERIFICATION.md`
- `docs/ARC10_MISSION_INTEGRATION_VERIFICATION.md`
- `docs/ARC10_SYNTHETIC_EXECUTION_EVIDENCE.md`
- `docs/ARC10_GAP_AND_DECISION_REGISTER.md`
- `docs/ARC10_PROJECT_OWNER_APPROVAL_REQUEST.md`
- `docs/ARC10_FAST_FINAL_DECISION_SHEET.md`
- `docs/ARC10_PROJECT_OWNER_DECISION_FORM.md`
- `docs/ARC10_GOVERNANCE_DECISION_REGISTER.md`
- `docs/ARC10_CONTROLLED_CONTRACT_RECONSTRUCTION_PROPOSAL.md`
- `src/quantum_space_agi/mission_demo/api.py`
- `src/quantum_space_agi/mission_demo/dto.py`
- `src/quantum_space_agi/mission_demo/service.py`

These files demonstrate the current verified local baseline and the governance decision history, but they are not themselves production-approved contract artifacts.

## 3. Missing v0.3/v0.4 artifacts

D-03 is explicitly approved as:

- Controlled reconstruction proposal is authorized.
- Missing documents must not be invented.
- A canonical contract version is not designated from absent artifacts.

The current review therefore treats the documented missing v0.3/v0.4 artifacts as an unresolved versioning gap rather than a recovered baseline.

## 4. Controlled reconstruction methodology

The reconstruction proposal is limited to evidence-backed documentation work only. It must:

- collect source and test evidence from the current local baseline
- distinguish verified behavior from assumed or missing behavior
- record all unresolved items as gaps requiring explicit Project Owner direction
- preserve the current local demo as a separate baseline from any future trusted production contract

## 5. Evidence provenance requirements

Any future contract version must be traceable to concrete evidence files and source objects. Provenance must include:

- source file path
- relevant commit or branch reference
- test or review evidence source
- status classification: verified, partially verified, documentation only, missing, or blocked
- owner and review status

No undocumented behavior may be treated as an approved contract claim.

## 6. Version status definitions

| Status | Meaning |
|---|---|
| `DRAFT` | Local evolutionary or proposal material without explicit approval |
| `REVIEW_PREPARATION` | Controlled review package created for governance inspection |
| `APPROVED` | Project Owner has explicitly approved the baseline or contract package |
| `BLOCKED` | Missing evidence, missing approvals, or unresolved governance issue |
| `MISSING` | Expected artifact is absent from the current repository or review record |

These definitions are documentation-only and do not imply any production contract approval.

## 7. Review and approval requirements

A formal contract version baseline may only be adopted after:

- Project Owner identifies the controlling repository and branch authority
- the contract owner is formally assigned
- the version baseline is expressly named
- missing artifacts are either recovered or explicitly declared absent
- approval gates for security, privacy, deployment, scientific/domain review, and acceptance are separately satisfied

## 8. No fabricated historical versions

This package does not create, infer, or endorse missing v0.3/v0.4 contract versions. It records the absence of evidence and preserves the current local baseline as the only verified baseline available in the reviewed worktree.

## 9. Current disposition

Current disposition:

`CONTROLLED RECONSTRUCTION PROPOSAL AUTHORIZED — NO CANONICAL VERSION ADOPTED — PRODUCTION NOT APPROVED`
