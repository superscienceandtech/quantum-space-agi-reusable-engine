DRAFT — NOT APPROVED

# NASAQ26 Mission API Interface Compatibility Review

**Status:** Technical compatibility assessment; all proposed wire mappings are non-binding.  
**Evidence snapshot:** local `develop` `6a44af34a649a1138cf577b3b16dbaf436c8a203`; cached ARC-10 v0.2 source ref `origin/arc/10-api-integration` `61d8c520b84cb7f28e0c7ba61863649bafe8c61c`.

## Evidence labels

**VERIFIED** = source/test evidence in the stated checkout. **PROPOSED** = candidate only. **UNVERIFIED** = no current evidence. **BLOCKED** = decision/approval required. **NOT IN SCOPE** = unavailable in current implementation.

The four ARC-10 review files—`ARC10_V02_TECHNICAL_REVIEW.md`, `ARC10_API_COMPATIBILITY_MATRIX.md`, `ARC10_OWNER_DECISION_REGISTER.md`, and `ARC10_IMPLEMENTATION_READINESS.md`—were read from the integration worktree. Their matrix/readiness descriptions reference earlier integration HEAD `0aea3314693418f5a9d525a5b93c4a4470a62eb2`; the integration worktree currently observed is `d7ac272af842445733c89074de310d706aed537c`, while this document reviews current `develop` at `6a44af34...`. Consequently, assertions in earlier reviews that there is no mission API/client describe their earlier snapshot. The current local demo exists, but remains separate from an approved production API.

## ARC-05 scientific interface

### Verified input and execution

[`SimulationConfig`](../src/quantum_space_agi/simulation/models.py) is a frozen Pydantic model with `extra="forbid"`, strict typing, and non-finite values disallowed. Its inputs are:

| Field | Verified meaning |
|---|---|
| `initial_position_m` | Three real finite position components in metres. |
| `initial_velocity_mps` | Three real finite velocity components in metres/second. |
| `gravitational_parameter_m3_s2` | Positive finite value; defaults to `EARTH_MU_M3_S2` (`3.986004418e14`). |
| `simulation_duration_s`, `time_step_s` | Positive finite duration and timestep in seconds. |
| `integrator`, `reference_frame` | Fixed literals `RK4` and `ECI`; the model does not expose a choice of algorithm/frame. |
| `collision_radius_m` | Positive finite collision threshold radius in metres. |

[`run_simulation`](../src/quantum_space_agi/simulation/workflow.py) requires a `SimulationConfig` and rejects any nonzero `initial_time_s`. It calls [`propagate_two_body`](../src/quantum_space_agi/simulation/propagation.py), which uses the existing fixed-step classical RK4 integrator and Earth point-mass two-body derivative. The workflow does not accept a destination ID, orbital elements, spacecraft properties, target ephemeris, thrust profile, or objective function.

The local adapter derives initial conditions for its synthetic profile catalog: radius = Earth reference radius + profile altitude; initial position is ECI +X; prograde initial velocity is ECI +Y with circular speed `sqrt(mu/radius)`. This is a local educational assumption in [`MissionDemoService.run`](../src/quantum_space_agi/mission_demo/service.py), not behavior inherent in `SimulationConfig`.

### Verified output, time, collision, and diagnostics

The workflow returns:

- `times_s`: NumPy float64 time samples, beginning at zero.
- `states`: NumPy float64 rows with six components in position XYZ, velocity XYZ order.
- `collision_index`, `collision_radius_m`, `collision_time_s`, `collision_state`, and `collision_method`.
- `diagnostics`: arrays for specific energy (`m²/s²`), specific angular-momentum magnitude (`m²/s`), eccentricity magnitude (dimensionless), radius (`m`), speed (`m/s`), energy drift (`m²/s²`), angular-momentum drift (`m²/s`), and maximum absolute drift scalars.
- `model`: ECI frame, RK4 integrator, Earth point-mass Newtonian two-body dynamics, and units for time, position, and velocity.

Propagation uses the configured nominal timestep and shortens the final step when required to reach the requested duration. Collision indices are zero-based sampled-state indices. Collision helpers report `exact_sample` or `linear_radius_interpolation`. Interpolation is linear interpolation of radius and state over a bracketed step; for an interpolated event the reported collision time/state may precede the sampled state at `collision_index`. It is not a continuous root-finding solution. Relevant test evidence in [`test_arc05_integration.py`](../tests/simulation/test_arc05_integration.py) includes the package workflow contract, analytical orbit comparisons, conservation/drift checks, collision sample/interpolation cases, and invalid input tests.

### Serialization and scientific limitations

**VERIFIED compatibility constraint:** simulator arrays are NumPy arrays and cannot be passed directly as standard JSON arrays. The local service explicitly converts arrays using `.tolist()`; its Pydantic DTO uses finite-number types. Any future transport contract must define output precision, shapes, ordering, nullability, non-finite handling, and response size.

**NOT IN SCOPE / NOT SUPPORTED:** transfer design/optimization, rendezvous, launch windows, target ephemerides, orbital perturbations, atmosphere, thrust/propulsion, fuel use, vehicle properties, uncertainty propagation, operational constraints, NASA data, or validated operational mission feasibility. The implementation is an educational two-body orbital propagation, not an operational mission-planning system. Existing tests demonstrate code behavior and selected numerical comparisons; they do not establish mission fitness or scientific certification.

### ARC-05 API compatibility

| Boundary | Status | Evidence/gap |
|---|---|---|
| Simulator input to local mission profile | **VERIFIED locally** | Adapter constructs `SimulationConfig` from a fixed synthetic profile and existing constants. |
| User-supplied arbitrary `SimulationConfig` DTO | **NOT IN SCOPE** | Mission API request does not accept raw state vectors or simulator parameters. No direct mapping should be invented. |
| NumPy-to-JSON mapping | **VERIFIED locally; PROPOSED for future contract** | `.tolist()` conversion in `service.py`; finite response validation in `dto.py`. No production serialization contract approved. |
| Collision details | **PARTIAL** | Engine returns method and threshold; local `MissionDemoService` drops `collision_radius_m` and `collision_method`, and `TrajectoryDTO` does not expose them. Candidate contract must decide whether to add them. |
| Workload/resource limits | **BLOCKED** | Profiles currently bound local demo workload by fixed catalog entries; no production request-size, step-count, timeout, cancellation, or concurrency policy is approved. |

## ARC-08 educational resource evaluator

[`EducationalMissionConfiguration`](../src/quantum_space_agi/ml/mission_configuration.py) accepts a supported `scenario_id` and non-empty list of unique string payload IDs; it stores sorted immutable IDs. [`mission_scenarios.py`](../src/quantum_space_agi/ml/mission_scenarios.py) currently defines one scenario, `resource-selection-demo-v1`, with `imager`, `spectrometer`, and `relay`, and a fixed immutable educational catalog.

[`evaluate_educational_mission`](../src/quantum_space_agi/ml/mission_evaluator.py):

1. Sums per-payload `budget_units`, `mass_units`, `power_units`, and payload count (`payload_slots`).
2. Compares totals to scenario limits and emits ordered violations for totals exceeding limits.
3. Sets `feasible` to the absence of violations.
4. Emits the sum of educational value points only if feasible; otherwise `educational_score` is `None`.
5. Includes evaluator and scenario version identifiers. `serialize_educational_mission_result` emits canonical compact UTF-8 JSON.

**Semantic limit:** all resource totals and limits are abstract educational units. The names `mass_units` and `power_units` do not make them kilograms or watts. The result is neither physical resource accounting nor spacecraft/mission feasibility. The current local wrapper labels policy approval `pending`, says it is informational, and does not let it gate simulation. [`test_mission_evaluator.py`](../tests/ml/test_mission_evaluator.py) verifies calculations, boundaries, infeasible results, immutability, deterministic ordering, and serialization. Mission tests verify the resource result does not gate the trajectory.

## ARC-09 dashboard compatibility

### Verified client and views

The current static dashboard uses [`mission-demo.js`](../arc09-ui-prototype/mission-demo.js) and [`app.js`](../arc09-ui-prototype/app.js):

- On load, GETs `/api/v1/missions/destinations`; an empty list or failed request displays an error.
- Submits `destination_profile_id` and `selected_payload_ids` to `/api/v1/missions/validate`; then sends the same body to `/api/v1/missions/run`.
- Uses same-origin relative URLs and JSON; no configurable backend base URL, authentication, timeout, cancellation, retry, or persistence is implemented.
- Requires trajectory time/state arrays of matching length, at least two states, six finite numbers per state. It draws the ECI X/Y projection and supplies a numeric trajectory table.
- Shows ARC-08 evaluator version, scenario, abstract totals, violations, warning, and pending policy status.
- Publishes loading, empty, ready, and error states. It clears old results while a request runs or after an error.
- Renders a latest-run report only; explicitly states cross-mission comparison/history is unavailable. Physical spacecraft properties are unavailable.

The overview charts/cards in [`index.html`](../arc09-ui-prototype/index.html) and `data.js` are synthetic illustrative samples, not live mission output. Results are held in browser memory and disappear on reload.

### Actual local response compatibility

The current local response DTOs in [`dto.py`](../src/quantum_space_agi/mission_demo/dto.py) provide `classification`, `limitations`, `mission`, `resource_evaluation`, and `trajectory`. The frontend consumes those exact property names. The local wrapper converts NumPy arrays and maps ARC-08 canonical JSON into DTOs. The response includes collision index/time/state, but does not include simulator collision method/radius. This is a specific data loss across the service-to-DTO mapping.

The API error body is `{error: {code, message, details: [{field, message}]}}`; the frontend flattens detail messages and does not expose internal stack traces. This behavior is local-only and not a production standard.

### Compatibility gaps

1. **Contract authority:** frontend and local backend share code/history but no approved production contract; they cannot establish future clients' guarantees.
2. **Config scope:** the request chooses only a synthetic profile and payload IDs; it cannot represent a real target, arbitrary orbit state, spacecraft, objective, or simulation controls.
3. **Trajectory loss:** collision method and collision threshold returned by ARC-05 are omitted by the service/API DTO; frontend cannot present them.
4. **No comparison service:** no API for mission history, saved runs, comparison, or generated report beyond a latest-run summary.
5. **Unavailable craft fields:** no mass, dimensions, propulsion, fuel, capacity, or physical power are present.
6. **No backend selection/operations:** relative same-origin base, no auth, no timeout/cancellation/retry/correlation policy; loopback server has no production controls.
7. **Testing boundary:** [`test_dashboard.py`](../tests/mission_demo/test_dashboard.py) checks HTML/JavaScript text and structure, not a browser session or JavaScript runtime. No production frontend build system is configured by the inspected project manifests.

`tests/mission_demo/test_api.py` and `test_dashboard.py` are useful local compatibility evidence; they do not approve the current DTOs as the production contract.

## Dataset Validation separation

The current `develop` tree has **no Dataset Validation HTTP route or dataset-validation API DTO**. The cached ARC-10 v0.2 contract and DTO files (`ARC10_API_CONTRACT_V0.2.md`, `ARC10_DTO_SPECIFICATION_V0.2.md`) are **DRAFT — NOT APPROVED / NON-CANONICAL** and use illustrative `schema_id`, `schema_version`, and `records` concepts. No route, schema catalog, provenance wire shape, or error map is approved.

Two domain validators must remain distinct:

| Function | Input/result | Semantics material to a future contract |
|---|---|---|
| `quantum_space_agi.data.schemas.validate_dataset(Dataset, DataSchema)` | Returns `SchemaValidationReport` with `schema_id`, `schema_version`, counts, and invalid records. | Zero-based indices; checks declared fields/types without coercion; does not reject undeclared keys; empty record sequence yields no invalid records and therefore `is_valid == true`. Requires `Dataset` with `Provenance`. |
| `quantum_space_agi.data.validator.validate_dataset(dataset, schema)` | Accepts `DatasetLoadResult`, mapping, or sequence plus declarative mapping schema; returns a different `ValidationReport`. | One-based issue indices; supports `allow_unexpected_fields`; empty dataset produces `empty_dataset`; has errors/warnings and timestamp; actual values omitted from issue reports by default. |

Evidence: [`schemas.py`](../src/quantum_space_agi/data/schemas.py), [`data/models.py`](../src/quantum_space_agi/data/models.py), [`provenance.py`](../src/quantum_space_agi/data/provenance.py), [`validator.py`](../src/quantum_space_agi/data/validator.py), [`test_schemas.py`](../tests/data/test_schemas.py), and [`test_data_validation.py`](../tests/test_data_validation.py).

Mission input validation is a separate task: it verifies known mission profile/payload IDs and request shape. Structural dataset validation does not establish scientific eligibility, mission feasibility, or NASA provenance. If Dataset Validation is implemented later, it needs independent operation scope, DTOs, selected validator, schema/provenance model, error semantics, tests, and approval. Do not reuse the mission DTO or route.

## Compatibility conclusion

- **VERIFIED:** a local synthetic Mission Demo composes ARC-05, ARC-08, and the ARC-09 dashboard.
- **PROPOSED:** a separate Mission Planning & Simulation API contract, derived from evidence but not copied mechanically from local DTOs.
- **BLOCKED:** production API implementation/deployment until named authorities approve operation scope, DTO mapping, security, operations, testing, and target repository.
- **NOT IN SCOPE:** converting synthetic or abstract fields into NASA data, physical resource units, or operational mission claims.

The four ARC-10 draft documents and their D-04/D-05 numbering discrepancy are not changed or reconciled by this compatibility review.
