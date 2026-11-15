# ARC-10 Evidence Consistency Review

## Scope and status

Repository: `/mnt/e/nasa26/nasaq26-develop-worktree`
Branch: `develop`
HEAD: `6a44af34a649a1138cf577b3b16dbaf436c8a203`

Current review status: B — PARTIALLY VERIFIED

This review compares six ARC-10 reports to the actual source code, tests, and execution evidence in the local worktree. It does not implement production code, add endpoints, or propose a new contract. It is a read-only evidence reconciliation and governance check.

## Evidence reviewed

1. `docs/ARC10_AUTHORITATIVE_SOURCE_DISCOVERY.md`
2. `docs/ARC10_SIX_ARTIFACT_IMPLEMENTATION_VERIFICATION.md`
3. `docs/ARC10_MISSION_INTEGRATION_VERIFICATION.md`
4. `docs/ARC10_SYNTHETIC_EXECUTION_EVIDENCE.md`
5. `docs/ARC10_GAP_AND_DECISION_REGISTER.md`
6. `docs/ARC10_PROJECT_OWNER_APPROVAL_REQUEST.md`

Additional code reviewed:
- `src/quantum_space_agi/mission_demo/api.py`
- `src/quantum_space_agi/mission_demo/dto.py`
- `src/quantum_space_agi/mission_demo/service.py`
- `src/quantum_space_agi/simulation/workflow.py`
- `tests/mission_demo/test_api.py`
- `tests/ml/test_synthetic_experiment_runner.py`

## High-confidence findings

### 1) The local implementation is materially verified, but only as a local educational demo

The Mission API exists and runs locally in the worktree:
- `src/quantum_space_agi/mission_demo/api.py` defines: `GET /health`, `GET /api/v1/missions/destinations`, `POST /api/v1/missions/validate`, `POST /api/v1/missions/run`, and a dashboard static mount.
- `tests/mission_demo/test_api.py` exercises those routes and confirms the expected 200/400/404/415/422/500 behaviors.
- `src/quantum_space_agi/mission_demo/service.py` composes ARC-05 and ARC-08 outputs into a single synthetic response.

This support is real and reproducible. However, the same source explicitly says the app is a local educational demo and not a production service.

### 2) The evidence supports implementation status, not production approval

The six-artifact reports correctly distinguish between:
- implementation verified against source,
- draft contract status,
- and production approval status.

The source code and tests support the first category. They do not establish the second or third category.

### 3) The remaining gaps are governance and contract issues, not coding-only issues

The main open items are not hidden defects in the local demo. They are unresolved decisions such as:
- canonical repository/branch ownership (`MAPI-02`),
- contract owner and version control (`MAPI-07`, `MAPI-15`),
- security/privacy/deployment approval (`MAPI-08`, `MAPI-09`, `MAPI-13`),
- domain review for ARC-05/ARC-08 boundary (`MAPI-04`, `MAPI-05`),
- missing ARC-10 v0.3/v0.4 documentation.

### 4) Synthetic execution is clearly labeled and not presented as scientific validation

The test file `tests/ml/test_synthetic_experiment_runner.py` asserts that:
- `diagnostics["selection"]["scientific_eligibility_status"] == "NOT_ASSESSED"`
- `bundle.scientific_acceptance_status == "PENDING_REVIEW"`
- `bundle.acquisition_readiness_status is AcquisitionReadinessStatus.NOT_READY`

That matches the governance requirement: synthetic execution is an evidence mechanism, not scientific validation.

## Contradictions and unsupported claims checked

| Check | Result | Evidence |
|---|---|---|
| Mission API is a production contract | Not supported | `src/quantum_space_agi/mission_demo/api.py` and `docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md` both label the app as a synthetic local demo, not a production API |
| `scientific_eligibility` is inferred from structural validation | Not supported | `tests/ml/test_synthetic_experiment_runner.py` explicitly asserts `NOT_ASSESSED` and `PENDING_REVIEW` |
| Dataset Validation API is folded into Mission API | Not supported | `docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md:51-59` states Dataset Validation is separate |
| Local demo is a formal production approval | Unsupported | No formal approval records or canonical contract owner were identified |
| Route/HTTP semantics are fully consistent | Partially supported; one mismatch remains | `api.py` handles 404/405, but `GET /api/v1/missions/run` currently resolves as `404` because the static dashboard mount handles the path before a route-method mismatch is raised |
| Unified result contains full ARC-05 collision metadata | Not supported | `src/quantum_space_agi/simulation/workflow.py` emits `collision_radius_m` and `collision_method`, but `src/quantum_space_agi/mission_demo/service.py` does not include those keys in the public response |

## Verified vs not verified

### Verified against source
- route definitions and JSON error envelopes in `api.py`
- strict DTO validation in `dto.py`
- ARC-05 + ARC-08 orchestration in `service.py`
- route behavior in `tests/mission_demo/test_api.py`
- synthetic-only status in `tests/ml/test_synthetic_experiment_runner.py`

### Not verified as formal approval
- canonical repo/branch owner
- production contract authority
- security/privacy approval
- deployment authorization
- domain approval for scientific and mission labeling
- existence of ARC-10 v0.3/v0.4 docs

## Conclusion

The evidence supports a careful status of B — PARTIALLY VERIFIED.

The implementation is real, tested, and locally reproducible. The project is not ready for formal ARC-10 approval because the authoritative production contract, ownership model, approval chain, and deployment/security boundaries remain unresolved.

No implementation or branch changes were made in this review pass.
