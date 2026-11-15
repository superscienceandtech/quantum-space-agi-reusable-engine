# ARC-10 Contract Baseline Preparation Plan

Repository: `/mnt/e/nasa26/nasaq26-develop-worktree`
Branch: `develop`
Full HEAD: `6a44af34a649a1138cf577b3b16dbaf436c8a203`
Current status: `B — PARTIALLY VERIFIED`
Baseline: `LOCAL_SYNTHETIC_DEMO_BASELINE — NOT PRODUCTION APPROVED`

This plan defines the permitted work after governance decisions are approved. It does not authorize implementation, deployment, or contract changes before approval.

## Scope allowed after formal Project Owner decisions

1. Contract scope definition
   - define the canonical Mission API boundary
   - keep Mission Planning & Simulation API separate from Dataset Validation API
   - avoid implying scientific eligibility from structural validation

2. Versioning and contract governance
   - select the controlling ARC-10 version baseline
   - resolve or document the missing v0.3/v0.4 artifacts
   - name the contract owner, reviewer roles, and decision authority

3. Endpoint and method inventory review
   - confirm the operational route set
   - decide the official HTTP semantics for unsupported methods and route mismatches
   - document the exact error contract for the final baseline

4. DTO and error schema review
   - review request payload and response contract fields
   - decide the collision metadata inclusion policy
   - confirm schema-level requirements and validation behavior

5. Scientific boundary review
   - maintain synthetic execution as synthetic only
   - preserve scientific-eligibility decisions as separate, explicit review outcomes
   - do not conflate simulation success with scientific validation

6. Security, privacy, deployment review
   - authorize boundary conditions, authentication, and deployment model
   - confirm privacy handling and data classification requirements
   - define release and rollback criteria before any deployment claim

7. Test evidence and acceptance criteria
   - confirm the local synthetic demo tests remain the baseline evidence for the local behavior
   - maintain a separate acceptance gate for production readiness
   - document acceptance criteria and owner responsibilities before implementation moves beyond local demo baseline

## Explicit non-authorization

This plan does not authorize:

- endpoint implementation changes
- DTO changes
- service or frontend code modifications
- ARC-05, ARC-08, or ARC-09 source changes
- deployment or production integration
- branch switching, merge, commit, push, reset, or destructive cleanup

## Required decisions before work proceeds

- D-01: canonical repository/branch authority
- D-02: contract owner and approval authority
- D-03: version baseline and missing v0.3/v0.4 disposition
- D-04: collision metadata inclusion
- D-05: 404 vs 405 documentation and behavior rule
- D-06: production boundary and approval gate

## Recommended evidence basis

- `docs/ARC10_AUTHORITATIVE_SOURCE_DISCOVERY.md`
- `docs/ARC10_SIX_ARTIFACT_IMPLEMENTATION_VERIFICATION.md`
- `docs/ARC10_MISSION_INTEGRATION_VERIFICATION.md`
- `docs/ARC10_SYNTHETIC_EXECUTION_EVIDENCE.md`
- `docs/ARC10_GAP_AND_DECISION_REGISTER.md`
- `docs/ARC10_PROJECT_OWNER_APPROVAL_REQUEST.md`
- `docs/ARC10_FAST_FINAL_DECISION_SHEET.md`

This plan becomes active only when the six Project Owner decisions are explicitly recorded and the baseline is no longer `LOCAL_SYNTHETIC_DEMO_BASELINE — NOT PRODUCTION APPROVED`.
