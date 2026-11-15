# NASAQ26 Mission Planning & Simulation API
## Project Owner Decision Proposal

**Status:** Decision proposal only — not an approved contract, implementation plan, or authorization.  
**Prepared:** 2026-11-15  
**Evidence snapshot:** `develop` at `6a44af34a649a1138cf577b3b16dbaf436c8a203`; ARC-10 review material in the integration worktree describes an earlier review snapshot and remains non-canonical.

## 1. Decision requested

Choose the API product direction:

- **A — Dataset Validation first:** keep the current ARC-10 v0.2 use case as the first API operation. This can support a dataset-validation consumer, but it does not deliver the mission workflow.
- **B — Mission API first:** prioritize a separate Mission Planning & Simulation API and defer Dataset Validation.
- **C — Both, separately (recommended):** maintain Dataset Validation and Mission Planning & Simulation as distinct operations with independently specified and approved contracts. They may share a service deployment only if maintainers approve that boundary; neither operation should reuse or silently expand the other's DTOs.

**Recommendation: Option C.** Dataset Validation and the NASA challenge mission workflow have different inputs, domain behavior, output semantics, and consumers. Separate contracts preserve the existing v0.2 draft's scope while allowing a distinct mission contract to cover ARC-05, ARC-08, and ARC-09. If delivery capacity requires sequencing, prioritize the mission operation for the challenge dashboard and keep Dataset Validation explicitly separate and deferred or independently scheduled.

No option is approved by this proposal. Selecting an option does not approve routes, DTOs, deployment, or implementation.

## 2. Evidence reviewed and freshness

Reviewed the four requested ARC-10 records:

- [ARC10_V02_TECHNICAL_REVIEW.md](../../nasaq26-integration-worktree/docs/ARC10_V02_TECHNICAL_REVIEW.md)
- [ARC10_API_COMPATIBILITY_MATRIX.md](../../nasaq26-integration-worktree/docs/ARC10_API_COMPATIBILITY_MATRIX.md)
- [ARC10_OWNER_DECISION_REGISTER.md](../../nasaq26-integration-worktree/docs/ARC10_OWNER_DECISION_REGISTER.md)
- [ARC10_IMPLEMENTATION_READINESS.md](../../nasaq26-integration-worktree/docs/ARC10_IMPLEMENTATION_READINESS.md)

Also inspected current `develop` source and tests for ARC-05, ARC-08, the local mission demo, and the ARC-09 dashboard. The review records identify their earlier integration snapshot as `0aea331...`; the current integration worktree HEAD observed during this review is `d7ac272...`, while the current `develop` checkout is `6a44af34...`. Therefore, claims in those earlier records that no mission API/client exists describe their reviewed snapshot, not the current `develop` checkout. The current mission demo is still local and educational; its existence does not make it an approved ARC-10 contract or production service.

Current implementation evidence includes [simulation/models.py](../src/quantum_space_agi/simulation/models.py), [simulation/workflow.py](../src/quantum_space_agi/simulation/workflow.py), [mission_configuration.py](../src/quantum_space_agi/ml/mission_configuration.py), [mission_evaluator.py](../src/quantum_space_agi/ml/mission_evaluator.py), [mission_demo/service.py](../src/quantum_space_agi/mission_demo/service.py), [mission_demo/dto.py](../src/quantum_space_agi/mission_demo/dto.py), [mission_demo/api.py](../src/quantum_space_agi/mission_demo/api.py), and the [ARC-09 mission client](../arc09-ui-prototype/mission-demo.js). The local educational scope and limitations are documented in [NASAQ26_LOCAL_EDUCATIONAL_DEMO.md](./NASAQ26_LOCAL_EDUCATIONAL_DEMO.md). Focused test evidence is in [test_arc05_integration.py](../tests/simulation/test_arc05_integration.py), [test_mission_evaluator.py](../tests/ml/test_mission_evaluator.py), [test_service.py](../tests/mission_demo/test_service.py), and [test_api.py](../tests/mission_demo/test_api.py).

Focused tests were run using the checkout-specific virtual environment. Exact commands, run from `/mnt/e/nasa26/nasaq26-develop-worktree`:

```bash
/home/yousuf/.copilot/session-state/f342f789-70aa-4c5d-8252-c96168f9f1ba/files/nasaq26-develop-worktree-venv/bin/python -m pytest -q tests/simulation/test_arc05_integration.py -k package_workflow_contract
/home/yousuf/.copilot/session-state/f342f789-70aa-4c5d-8252-c96168f9f1ba/files/nasaq26-develop-worktree-venv/bin/python -m pytest -q tests/ml/test_mission_evaluator.py tests/mission_demo/test_service.py tests/mission_demo/test_api.py
```

Results: **1 passed, 131 deselected** for ARC-05; **62 passed** for ARC-08 and the local mission demo. These tests verify domain and local-demo behavior, not production readiness or an approved contract.

## 3. Verified component capabilities and boundaries

| Component | Verified interface and behavior | Boundary / implication |
|---|---|---|
| **ARC-05 simulation** | `SimulationConfig` accepts strict three-component `initial_position_m` and `initial_velocity_mps`, positive duration, timestep, collision radius, optional gravitational parameter, and fixed `RK4` / `ECI` literals. `run_simulation(config, initial_time_s=0.0)` returns NumPy `times_s` and `states`, collision data, diagnostics, and model metadata. The current workflow requires a zero start time and models Earth point-mass Newtonian two-body dynamics. | It does not accept a destination ID, orbital elements, spacecraft properties, transfer, thrust, fuel, or mission objective. Its NumPy output is not directly JSON serializable. |
| **ARC-08 educational evaluator** | `EducationalMissionConfiguration(scenario_id, selected_payload_ids)` validates the current `resource-selection-demo-v1` scenario and payload IDs `imager`, `spectrometer`, and `relay`. `evaluate_educational_mission` returns feasibility for that educational scenario, violations, abstract totals, evaluator/scenario versions, and an optional educational score. A canonical JSON-byte serializer is provided. | Budget, mass, power, and slot values are abstract educational units, not physical quantities. Evaluator feasibility is not mission feasibility and must not gate or alter ARC-05 simulation. |
| **ARC-09 mission dashboard** | Current `develop` includes a mission form, calls the local API, displays ARC-05 trajectory/diagnostics and ARC-08 results, and surfaces loading, success, and error states. The latest result is held in browser memory. | Dashboard overview charts/cards remain synthetic samples. Cross-mission comparison/history, persistence, real NASA data, and physical spacecraft configuration are not available. |
| **Dataset Validation** | ARC-10 v0.2 is a dataset-validation candidate. ARC-03 has two distinct structural validation interfaces with different inputs, result fields, record-index bases, and empty/unexpected-field semantics. | v0.2 does not define the complete mission workflow. A validator must be selected and mapped before Dataset Validation can be contracted; `scientific_eligibility` cannot be inferred from structural validation. |

### Current local-demo mapping (verified, not proposed as production approval)

The current local demo's request is:

```json
{
  "destination_profile_id": "synthetic-leo-400-km",
  "selected_payload_ids": ["imager", "relay"]
}
```

Its strict request DTO rejects extra fields, requires a known synthetic profile and a non-empty, unique list of known payload IDs, and returns payload IDs in canonical sorted order. The server derives an idealized circular ECI initial state from the selected synthetic altitude and fixed Earth constants, then invokes ARC-05. It invokes ARC-08 after ARC-05 and returns both outputs; ARC-08 infeasibility does not prevent the trajectory result.

The local server exposes `GET /health`, `GET /api/v1/missions/destinations`, `POST /api/v1/missions/validate`, and `POST /api/v1/missions/run`. These routes are implemented for the loopback-only educational demo. They are **not approved production routes**.

The local run DTO includes:

- `classification`, `limitations`, and a `mission` summary;
- `resource_evaluation` with evaluator result, warning, and explicit pending policy approval;
- `trajectory.times_s`, six-value `states` rows ordered as `[x_m, y_m, z_m, vx_mps, vy_mps, vz_mps]`, collision details, diagnostics, and model/unit metadata.

NumPy arrays are converted to JSON arrays; ARC-08's canonical JSON is parsed into the response; Pydantic DTOs enforce finite numeric output and declared fields. The local API's tested error mapping includes malformed JSON (400), unsupported media type (415), request validation (422), not found (404), and generic mission execution failure (500), with a stable local error envelope. These behaviors are evidence for a candidate mapping only; production HTTP semantics still require approval.

## 4. Candidate mission application architecture

The following is a design candidate, not an instruction to implement:

```text
ARC-09 client
    -> mission transport boundary (approved request/response and error DTOs)
        -> mission application service
            -> validate selected synthetic profile and payload IDs
            -> construct ARC-05 SimulationConfig from explicitly approved inputs
            -> ARC-05 run_simulation
            -> ARC-08 EducationalMissionConfiguration / evaluator
            -> serialize and validate a unified mission result
```

Keep the transport DTOs separate from ARC-05/ARC-08 domain types. Keep Dataset Validation as a distinct operation with its own selected validator, schema/provenance model, DTOs, errors, and tests. The services may be hosted together or separately only after repository, ownership, security, and operations decisions are recorded.

For any future mission contract, the existing local demo is a candidate reference implementation—not an authoritative schema. In particular, its three destination profiles are synthetic circular-orbit initial conditions, not actual target destinations or orbit transfers.

## 5. Candidate DTO mapping and scientific/serialization requirements

| Candidate wire concept | Existing evidence | Required contract decision |
|---|---|---|
| Mission configuration | Local demo uses `destination_profile_id` and `selected_payload_ids`; profiles currently supply altitude, duration, timestep, and assumptions. | Confirm whether production scope permits only catalog profile IDs, or requires another input model. Do not add destination/orbit-element or spacecraft-property fields without corresponding domain behavior. |
| ARC-05 input mapping | Profile altitude is added to Earth reference radius; a circular speed is derived; ECI +X position and prograde +Y velocity, Earth gravitational parameter, RK4, Earth-radius collision threshold, duration, and timestep form `SimulationConfig`. | Approve the exact assumptions, constants/provenance, supported profile catalog, and policy for bounds on duration, timestep, and result size. |
| ARC-05 output | Time samples; six-component state samples; collision metadata; energy/angular-momentum/eccentricity/radius/speed diagnostics; model metadata. | Define array dimensions and ordering, precision, nullability, finite-number rules, units, and response-size policy. Unit metadata currently declares seconds, metres, and metres/second; diagnostics retain their domain meanings and units. |
| ARC-08 output | Scenario/version, sorted payload IDs, `feasible`, violations (`code`, `observed_total`, `limit`), abstract totals, and optional score. | Preserve explicit abstract-unit labeling. Decide whether this result is always returned, and state that educational feasibility does not mean spacecraft or mission feasibility. Do not reinterpret units as kilograms, watts, percentages, or fuel. |
| Unified result | Current local `MissionRunResponseDTO` has mission, resource-evaluation, and trajectory sections, with synthetic classification and limitations. | Approve top-level field names, component versions/provenance, partial-failure semantics, policy status, and whether an ARC-05 result may be returned when ARC-08 fails (or vice versa). |
| Validation and errors | Local demo has strict DTO validation and a tested error envelope; validation endpoint does not execute either component. | Approve stable field errors, HTTP status mapping, malformed/unsupported media handling, unsupported profile/payload behavior, and distinction between request failures, domain findings, and server failures. |

The current local service runs ARC-05 first and ARC-08 second. That sequencing is verified implementation behavior, not a scientific dependency. The future contract owner must decide whether to retain it and how to represent a failure in either component; no successful-looking partial result should conceal a failed component.

## 6. Options, tradeoffs, and recommendation

| Option | Benefits | Risks / limitations | Assessment |
|---|---|---|---|
| **A. Dataset Validation first** | Keeps the existing v0.2 direction and can serve a validation-specific consumer. | Does not support mission configuration, simulation, resource evaluation, or ARC-09 mission results; validator choice and schema/provenance remain unresolved. | Appropriate only if dataset validation is the immediate approved product goal. |
| **B. Mission API first** | Aligns directly with the NASA challenge dashboard and permits focused ARC-05/08/09 contract decisions. | Can sideline a separate validation need; may be misconstrued as replacing v0.2 unless its status and separation are explicit. | Viable sequencing choice if mission delivery is the priority, but should not redefine v0.2. |
| **C. Both, distinct operations/contracts** | Preserves v0.2 scope while providing a mission-specific contract; prevents conflating records, validation, resources, and trajectories. Enables separate tests and approval evidence. | More contract and maintenance work; shared deployment would still need explicit ownership, security, and operational boundaries. | **Recommended.** It best represents the actual domain boundaries and avoids implying that dataset validation is mission execution. |

## 7. Decisions and approval authorities required

Before any production contract or implementation work is authorized, the Project Owner and designated maintainers should record:

1. **Product scope and priority:** choose A, B, or C; identify the first consumer and success criteria for each selected operation.
2. **Contract authority:** name the canonical contract owner, final approver(s), technical reviewers for ARC-05/08, and approval evidence/location. Drafting responsibility alone is not final approval.
3. **Implementation boundary:** select repository, maintainers, branch, runtime, local/non-production or production scope, and whether services may share a deployment.
4. **Mission input model:** approve whether the synthetic profile/payload-only model is sufficient; define any new input only if supported by reviewed domain behavior.
5. **Component composition:** approve order, output completeness, behavior on partial failure, and the exact non-gating relationship between educational resource evaluation and simulation.
6. **Units and provenance:** approve trajectory field order/units/model labels, evaluator abstract-unit presentation, synthetic-data labeling, and component/scenario version provenance.
7. **Dataset Validation specifics (if retained):** select exactly one validation interface and approve schema catalog, provenance construction, empty-input, undeclared-field, index-base, and issue-code behavior.
8. **HTTP/security/operations:** approve routes/methods, version policy, error semantics, authentication/authorization boundary, CORS, logging/redaction, retention, request/result limits, timeout/concurrency policy, and deployment controls. The current demo is loopback-only and has no production authentication or deployment controls.
9. **ARC-09 behavior:** approve which data is live versus illustrative, loading/empty/error mappings, and whether history or cross-mission comparison is in scope. Those capabilities are not provided by the current local API.
10. **Data authority:** explicitly approve any future NASA data use and provenance separately. No NASA data is used or claimed by this local demo.
11. **Implementation authorization:** record a separate explicit authorization after contract, technical, security, and operations reviews. This proposal is not that authorization.

## 8. Remaining blockers and verdict

- ARC-10 v0.2 remains **DRAFT — NOT APPROVED** and **NON-CANONICAL**; this proposal does not revise it.
- The production Mission API has no approved contract, route, DTO, deployment target, or final contract approver.
- Dataset Validation still lacks a selected validator and approved schema/provenance semantics.
- The local mission demo is verified as a synthetic integration but lacks production security/operations controls and must not be presented as NASA data or validated mission design.
- Physical spacecraft properties, fuel, transfer trajectories, mission feasibility, persistence, and cross-mission comparison are unavailable in the inspected workflow.

**Verdict: READY FOR PROJECT OWNER DECISION; BLOCKED for production contract approval and implementation.** Option C is recommended. The next gate is a recorded scope choice plus named contract/technical/security approvers; only then should a separate mission contract be drafted for approval. No production implementation or deployment is authorized here.
