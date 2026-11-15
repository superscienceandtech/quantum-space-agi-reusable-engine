# ARC-10 Controlled Contract Reconstruction Proposal

Repository: `/mnt/e/nasa26/nasaq26-develop-worktree`
Branch: `develop`
Full HEAD: `6a44af34a649a1138cf577b3b16dbaf436c8a203`
Current status: `B — PARTIALLY VERIFIED`
Baseline: `LOCAL_SYNTHETIC_DEMO_BASELINE — NOT PRODUCTION APPROVED`

## Purpose

This document is a proposal-only mechanism to address the missing ARC-10 v0.3/v0.4 artifacts without inventing a canonical version or implying production approval. It is a governance aid, not an implementation mandate.

## Decision context

Project Owner decision D-03 states:

- Prepare a controlled reconstruction proposal using existing evidence.
- Do not invent missing documents.
- Do not designate a canonical contract version from absent artifacts.

## Proposal scope

The reconstruction proposal shall be limited to evidence-backed documentation work only. It must:

- identify the current verified local demo contract surface
- distinguish verified behavior from undocumented assumptions
- record unresolved contract gaps and governance requirements
- define a controlled path to a future formal version baseline after written owner approval

## Evidence baseline for reconstruction

Use the following as inputs only:

- `docs/ARC10_AUTHORITATIVE_SOURCE_DISCOVERY.md`
- `docs/ARC10_SIX_ARTIFACT_IMPLEMENTATION_VERIFICATION.md`
- `docs/ARC10_MISSION_INTEGRATION_VERIFICATION.md`
- `docs/ARC10_SYNTHETIC_EXECUTION_EVIDENCE.md`
- `docs/ARC10_GAP_AND_DECISION_REGISTER.md`
- `docs/ARC10_PROJECT_OWNER_APPROVAL_REQUEST.md`
- `src/quantum_space_agi/mission_demo/api.py`
- `src/quantum_space_agi/mission_demo/dto.py`
- `src/quantum_space_agi/mission_demo/service.py`
- `src/quantum_space_agi/simulation/workflow.py`
- `tests/mission_demo/test_api.py`
- `tests/ml/test_synthetic_experiment_runner.py`

## Reconstruction rules

1. No invented contract version numbers beyond the evidence-reviewed baseline.
2. No claim that missing v0.3/v0.4 documents were recovered or approved.
3. No fabrication of endpoint schema, DTO fields, or response semantics not present in the local verified demo.
4. No change to implementation, API behavior, or service logic.
5. No production deployment or scientific claim without separate authority.
6. Any future version baseline must be approved by the Project Owner before it is treated as controlling.

## Proposed structure for a formal reconstruction package

When authorized by Project Owner decision, the reconstruction package should include:

- contract scope and boundary
- endpoint and method inventory for the verified local demo
- DTO and response schema summary
- known gaps and unresolved decisions
- collision metadata decision record
- method semantics record (404 vs 405)
- scientific and synthetic boundary statement
- evidence references and review status
- explicit list of approval gates still required

## Current disposition

This proposal remains `PROPOSAL ONLY` and `NOT PRODUCTION APPROVED`.

It is suitable only for governance review and controlled documentation preparation. It does not authorize implementation, deployment, or contract adoption.
