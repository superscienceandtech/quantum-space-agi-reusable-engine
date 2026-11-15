# ARC-10 Formal Contract Baseline Review

Repository: `/mnt/e/nasa26/nasaq26-develop-worktree`
Branch: `develop`
Full HEAD: `6a44af34a649a1138cf577b3b16dbaf436c8a203`
Current status: `B — PARTIALLY VERIFIED`
Baseline: `LOCAL_SYNTHETIC_DEMO_BASELINE — NOT PRODUCTION APPROVED`
Status: `FORMAL REVIEW PREPARATION COMPLETE — PRODUCTION NOT APPROVED`

## 1. Purpose and authorization boundary

This document is a review-preparation package only. It is authorized by D-06 for review preparation without implementation, external integration, or deployment.

This package does not authorize:

- production contract approval
- production endpoint or DTO implementation
- backend or frontend integration changes
- external API integration
- NASA data acquisition or reuse
- security/privacy/scientific/domain/deployment acceptance

## 2. Current verified baseline

The current verified baseline remains the local synthetic demo baseline, as recorded in the Project Owner decision register.

Verified evidence available in the current worktree:

- `src/quantum_space_agi/mission_demo/api.py`
- `src/quantum_space_agi/mission_demo/dto.py`
- `src/quantum_space_agi/mission_demo/service.py`
- `src/quantum_space_agi/ml/synthetic_experiment_runner.py`
- `tests/mission_demo/test_api.py`
- `tests/ml/test_synthetic_experiment_runner.py`
- `docs/ARC10_PROJECT_OWNER_DECISION_FORM.md`
- `docs/ARC10_GOVERNANCE_DECISION_REGISTER.md`

## 3. Proposed contract scope

The proposed review baseline is intentionally limited to the local mission demo contract surface and its evidence-backed orchestration flow:

Mission Configuration
→ Validation
→ ARC-05 Simulation
→ ARC-08 Resource Evaluation
→ Unified Mission Result
→ ARC-09 Dashboard

This scope remains separate from any production dataset-validation or scientific approval path.

## 4. Endpoint and HTTP method inventory

The following routes are verified in source and are the basis for the review package:

| Method | Path | Status | Evidence |
|---|---|---|---|
| GET | `/health` | Verified | `src/quantum_space_agi/mission_demo/api.py` |
| GET | `/api/v1/missions/destinations` | Verified | `src/quantum_space_agi/mission_demo/api.py` |
| POST | `/api/v1/missions/validate` | Verified | `src/quantum_space_agi/mission_demo/api.py` |
| POST | `/api/v1/missions/run` | Verified | `src/quantum_space_agi/mission_demo/api.py` |
| GET | `/` and static dashboard mount | Verified | `src/quantum_space_agi/mission_demo/api.py` |

Current local method semantics:

- D-05 is approved as `404 Not Found` for unsupported methods on current local POST-only demo routes.
- This decision applies to the current demo only and does not generalize to production APIs.
- Actual local evidence includes `404` for unsupported GET access to POST-only routes and `405` for unsupported method cases such as `POST /health` or `PUT /api/v1/missions/run` handled at the framework boundary.

## 5. Request and response DTO inventory

The verified DTOs in `src/quantum_space_agi/mission_demo/dto.py` are:

- `MissionRequestDTO`
- `MissionSummaryDTO`
- `MissionValidationDTO`
- `DestinationProfileDTO`
- `DestinationListDTO`
- `ApiErrorFieldDTO`
- `ApiErrorDetailDTO`
- `ApiErrorDTO`
- `ResourceTotalsDTO`
- `ResourceViolationDTO`
- `EducationalResourceResultDTO`
- `ResourceEvaluationDTO`
- `SimulationModelDTO`
- `TrajectoryDiagnosticsDTO`
- `TrajectoryDTO`
- `MissionRunResponseDTO`

These DTOs are strict, JSON-only, and locally verified. Their public contract is limited to the local synthetic demo and is not an approved production contract.

## 6. Error and validation behavior

The validated local API behavior includes:

- request body must be JSON on POST endpoints
- `415 Unsupported Media Type` when non-JSON payload is sent to the mission POST endpoints
- `400 Malformed JSON` for invalid JSON payloads
- `422 Validation Error` for invalid field content or invalid values
- `500` with a generic error envelope for unhandled runtime failures
- documented error envelope: `{"error": {"code": ..., "message": ..., "details": [...]}}`

This is implemented in the exception handlers in `src/quantum_space_agi/mission_demo/api.py` and is part of the current local review baseline.

## 7. Unified Mission Result structure

The verified mission result contract is a `MissionRunResponseDTO` with the following logical structure:

- `classification`
- `limitations`
- `mission`
  - `destination_profile_id`
  - `destination_display_name`
  - `spacecraft_profile_id`
  - `selected_payload_ids`
- `resource_evaluation`
  - `status`
  - `policy_approval_status`
  - `policy_authority`
  - `warning`
  - `result`
- `trajectory`
  - `times_s`
  - `states`
  - `state_order`
  - `collision_index`
  - `collision_time_s`
  - `collision_state`
  - `diagnostics`
  - `model`

This structure is implemented in `src/quantum_space_agi/mission_demo/service.py` and the corresponding DTO model in `src/quantum_space_agi/mission_demo/dto.py`.

## 8. ARC-05 / ARC-08 / ARC-09 integration boundaries

### ARC-05 simulation integration

`MissionDemoService.run()` invokes the simulation package and constructs a configuration with:

- `SimulationConfig`
- Earth orbital geometry
- circular orbit approximation
- collision radius and trajectory diagnostics

This is local evidence for the simulation layer, not a production contract or a scientific validation result.

### ARC-08 resource evaluation integration

The service calls the educational mission evaluator and wraps its output in `resource_evaluation` while preserving the explicit warning:

- `policy_approval_status: "pending"`
- `policy_authority: "educational evaluator output only"`
- `warning`: the result is not an approved spacecraft resource policy and does not gate the simulation

This is a required boundary for the local demo.

### ARC-09 dashboard integration

The dashboard is mounted as a static front-end from the local prototype directory. Its integration is a review boundary for local UI display only. It does not create a production API contract or scientific approval path.

## 9. Collision metadata exclusion decision

D-04 is approved as current-scope-only:

- collision metadata is excluded from the public Mission API response for the current review baseline
- any future inclusion requires a separate explicit contract review and Project Owner approval

This is consistent with the local `MissionRunResponseDTO` and service output, which exclude the metadata from the public response while the lower-level simulation may include collision-related calculations internally.

## 10. Dataset Validation API separation

The reviewed evidence does not support a production or contract-level merge between Mission Planning & Simulation API and Dataset Validation API.

The local mission demo remains explicitly synthetic and educational, and the synthetic experiment evidence is not treated as scientific validation. The `scientific_eligibility` field is intentionally not inferred from structural validation and remains a separate approval gate such as `NOT_ASSESSED` or `PENDING_REVIEW` in the synthetic evidence path.

## 11. Known implementation and documentation gaps

The following items remain unresolved for production-orientated approval:

- no canonical production repository/branch authority beyond the local verification baseline
- no formal contract owner beyond the Project Owner approval authority
- missing ARC-10 v0.3/v0.4 artifacts
- collision metadata treatment and exported schema remain a formal decision item
- HTTP method semantics remain local-demo scoped per D-05
- security/privacy/deployment/domain/scientific approvals remain independent requirements
- no production or scientific acceptance claim is supported by the verified local review evidence

## 12. Explicitly unverified production requirements

The following remain unverified and must not be claimed as approved:

- production access control and authentication
- data retention/privacy review and approval
- deployment architecture and rollback requirements
- scientific or operational readiness of mission calculations
- production contract signing or acceptance
- external API integration or compatibility claims
- NASA-data validation claims

## 13. Review outcome

The evidence supports a controlled review-preparation package for the local synthetic demo baseline. It does not support production approval or a production contract baseline. The current status remains:

`FORMAL REVIEW PREPARATION COMPLETE — PRODUCTION NOT APPROVED`
