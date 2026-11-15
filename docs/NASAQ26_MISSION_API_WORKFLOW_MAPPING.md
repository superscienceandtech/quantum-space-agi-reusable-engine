DRAFT — NOT APPROVED

# NASAQ26 Mission Planning & Simulation API: Workflow Mapping

**Status:** Evidence-backed technical mapping; not a contract, implementation authorization, or deployment approval.  
**Evidence snapshot:** local `develop` at `6a44af34a649a1138cf577b3b16dbaf436c8a203`. ARC-10 v0.2 drafts inspected from the cached `origin/arc/10-api-integration` ref at `61d8c520b84cb7f28e0c7ba61863649bafe8c61c`. No remote fetch was performed.

## Status vocabulary

- **VERIFIED** — observed in current source or tests.
- **PROPOSED** — candidate interface/design only; not approved.
- **UNVERIFIED** — evidence not found or not exercised by the listed tests.
- **BLOCKED** — requires an owner/authority decision before production use.
- **NOT IN SCOPE** — explicitly unsupported by the inspected local educational workflow.

The current local Mission Demo is an implementation, but it is not an ARC-10-approved production API. All field/route recommendations in this package remain **PROPOSED**.

## End-to-end workflow

### 1. Mission configuration

- **Existing implementation — VERIFIED:** `MissionDemoConfiguration`, `SpacecraftConfiguration`, `OrbitDestinationProfile`, and immutable `ORBIT_DESTINATION_PROFILES` are in [`configuration.py`](../src/quantum_space_agi/mission_demo/configuration.py). The local `MissionRequestDTO` in [`dto.py`](../src/quantum_space_agi/mission_demo/dto.py) accepts only `destination_profile_id` and `selected_payload_ids`.
- **Input:** one of three catalog IDs (`synthetic-leo-400-km`, `synthetic-leo-800-km`, `synthetic-earth-orbit-2000-km`) plus one or more ARC-08 payload IDs (`imager`, `spectrometer`, `relay`). Profile data supplies altitude, duration, timestep, classification, and assumptions.
- **Output:** a validated configuration holding a synthetic profile and a payload-only `educational-payload-carrier-v1` spacecraft label.
- **Dependencies:** ARC-08 scenario/payload catalog is reused for payload validation; no external provider or NASA dataset is called.
- **Validation/errors — VERIFIED:** unknown profile/payload, missing or empty payload list, duplicates, non-string identifiers, and extra request keys are rejected. The Pydantic DTO is strict and forbids extra fields; configuration classes raise `ValidationError`.
- **Test evidence:** [`test_service.py`](../tests/mission_demo/test_service.py), [`test_api.py`](../tests/mission_demo/test_api.py), including synthetic catalog and invalid-input cases.
- **Limitations/missing capabilities:** no arbitrary orbital elements, initial state, spacecraft mass, propulsion, fuel, capacity, physical power, mission objective, or real destination. The named profiles are idealized initial conditions, not target destinations or transfers.
- **Production status:** the local shape is useful evidence only. Exact profile catalog, configuration semantics, and bounds require contract approval (**BLOCKED**).

### 2. Input validation

- **Existing implementation — VERIFIED:** `MissionRequestDTO` validates the request. `POST /api/v1/missions/validate` in [`api.py`](../src/quantum_space_agi/mission_demo/api.py) builds a mission summary and does not execute ARC-05 or ARC-08.
- **Input/output:** the same two-key mission request returns `{"valid": true, "mission": ...}` with canonical sorted payload IDs and profile/spacecraft identifiers.
- **Dependencies:** FastAPI request parsing, Pydantic DTO validation, local profile and payload catalogs.
- **Validation/errors — VERIFIED locally:** malformed JSON maps to `400 malformed_json`; unsupported media type to `415 unsupported_media_type`; schema/domain request validation to `422 validation_error` with field details. These are local demo semantics, not an approved production status map.
- **Test evidence:** [`test_api.py`](../tests/mission_demo/test_api.py) verifies the validation endpoint does not call `run`, valid response canonicalization, invalid fields, malformed JSON, and unsupported media type.
- **Limitations/missing capabilities:** validation checks configured profile/payload IDs, not scientific validity, simulator convergence, resource-policy approval, or mission feasibility. It has no production schema version or authorization policy.
- **Production status:** endpoint and error mapping remain **PROPOSED**, not approved.

### 3. ARC-05 trajectory simulation

- **Existing implementation — VERIFIED:** [`SimulationConfig`](../src/quantum_space_agi/simulation/models.py) and [`run_simulation`](../src/quantum_space_agi/simulation/workflow.py), backed by [`propagate_two_body`](../src/quantum_space_agi/simulation/propagation.py) and [`diagnose_trajectory`](../src/quantum_space_agi/simulation/diagnostics.py).
- **Input structure:** strict finite three-component `initial_position_m` and `initial_velocity_mps`; positive `simulation_duration_s`, `time_step_s`, and `collision_radius_m`; optional positive gravitational parameter (default `EARTH_MU_M3_S2`); integrator literal `RK4`; frame literal `ECI`.
- **Local adapter mapping — VERIFIED:** `MissionDemoService.run` derives `r = EARTH_REFERENCE_RADIUS_M + altitude_m`, `v = sqrt(EARTH_MU_M3_S2 / r)`, uses `[r,0,0]` and `[0,v,0]`, Earth `mu`, the profile duration/timestep, and Earth reference radius as collision threshold. It calls the existing simulator; it does not change the simulation algorithm.
- **Output structure:** float64 NumPy `times_s`, `states` (each state has six values: position XYZ in metres then velocity XYZ in metres/second), collision index/radius/time/state/method, diagnostics, and model metadata. Time starts at zero; `run_simulation` rejects nonzero `initial_time_s`. Propagation uses the configured nominal timestep and shortens the final step when needed to land at the requested duration.
- **Dependencies:** NumPy, Pydantic configuration, existing ARC-05 propagation and diagnostic functions.
- **Validation/errors — VERIFIED:** non-finite, non-real, malformed vectors and non-positive physical parameters are rejected. Propagation also validates duration/timestep and collision inputs; a collision may be an exact sample or use linear interpolation of radius over a bracketing step. The reported collision index refers to a sampled state (zero-based); for interpolated events the event time/state may precede the corresponding sampled state.
- **Test evidence:** [`test_arc05_integration.py`](../tests/simulation/test_arc05_integration.py) includes the package workflow contract, analytical orbit comparisons, invariants/drift, collision cases, and validation tests. The focused run for this review passed 1 test with 131 deselected.
- **Limitations/missing capabilities:** fixed-step classical RK4; Earth point-mass Newtonian two-body model; no atmosphere, perturbations, thrust, launch, transfer, rendezvous, target ephemeris, propulsion, fuel, uncertainty, or validated operational mission feasibility. No public workload/sample cap is defined by the domain interface.
- **Production status:** numerical function is **VERIFIED**; mission/API interpretation and operating bounds remain **BLOCKED** pending technical and contract review.

### 4. ARC-08 educational resource evaluation

- **Existing implementation — VERIFIED:** [`EducationalMissionConfiguration`](../src/quantum_space_agi/ml/mission_configuration.py), [`SCENARIO_CATALOG`](../src/quantum_space_agi/ml/mission_scenarios.py), and `evaluate_educational_mission` / `serialize_educational_mission_result` in [`mission_evaluator.py`](../src/quantum_space_agi/ml/mission_evaluator.py).
- **Input structure:** scenario ID `resource-selection-demo-v1` and a non-empty list of unique known payload IDs; IDs are normalized to sorted order.
- **Calculation/output:** sums each payload's `budget_units`, `mass_units`, and `power_units`, counts `payload_slots`, reports constraint violations against the catalog limits, and returns `feasible`, evaluator/scenario versions, and a score only when feasible. The serializer returns canonical UTF-8 JSON bytes.
- **Dependencies:** immutable in-repository educational scenario/payload catalog; no physical spacecraft model or external data.
- **Validation/errors — VERIFIED:** unknown scenario/payload, duplicate IDs, wrong types, and empty payload list are rejected. Over-limit totals produce ordered violations and no educational score.
- **Composition — VERIFIED locally:** `MissionDemoService` calls ARC-08 after ARC-05 and always includes the educational result if both finish; a resource violation does not gate or modify trajectory output.
- **Test evidence:** [`test_mission_evaluator.py`](../tests/ml/test_mission_evaluator.py), [`test_service.py`](../tests/mission_demo/test_service.py), and [`test_api.py`](../tests/mission_demo/test_api.py). ARC-08 plus mission-demo service/API/dashboard tests passed 67 tests in this review.
- **Limitations/missing capabilities:** all totals are abstract educational units, even fields named `mass_units` or `power_units`; they are not kg, watts, cost, fuel, or measured resource values. `feasible` means only within the demo scenario constraints, not spacecraft or mission feasibility. Policy approval is explicitly pending.
- **Production status:** evaluation behavior is **VERIFIED**; public result semantics and policy authority are **BLOCKED** pending ARC-08/domain and contract approval.

### 5. Unified mission result and JSON serialization

- **Existing implementation — VERIFIED:** `MissionDemoService.run` in [`service.py`](../src/quantum_space_agi/mission_demo/service.py) composes the mission summary, ARC-08 evaluation, and ARC-05 output. `MissionRunResponseDTO` and nested DTOs in [`dto.py`](../src/quantum_space_agi/mission_demo/dto.py) validate the local response.
- **Serialization:** NumPy trajectory and diagnostic arrays are converted with `.tolist()`; ARC-08's canonical JSON bytes are decoded and parsed; the Pydantic response DTO rejects non-finite numeric values through `FiniteFloat`.
- **Output structure:** top-level `classification`, `limitations`, `mission`, `resource_evaluation`, and `trajectory`; trajectory includes time/state arrays, state ordering, collision index/time/state, diagnostics, and model/unit metadata. The service result intentionally does **not** copy ARC-05's `collision_radius_m` or `collision_method` into the local API DTO, although those exist in the simulator result. This is a known information-mapping gap, not evidence that the simulator lacks those fields.
- **Errors — VERIFIED locally:** unexpected exceptions are logged server-side and returned as generic `500 mission_run_failed`; internal exception text is not exposed. A response containing non-finite simulation values is rejected.
- **Test evidence:** [`test_service.py`](../tests/mission_demo/test_service.py) checks JSON serialization and component composition; [`test_api.py`](../tests/mission_demo/test_api.py) checks ARC-05/08 response fields, generic failures, and non-finite output rejection.
- **Missing capabilities/decisions:** no production provenance/version envelope, correlation ID, partial-result semantics, result persistence, response-size contract, or policy on including collision method/threshold. If either component errors, the current endpoint returns a generic failure rather than a partial result.
- **Production status:** local unified output is **VERIFIED**; transport DTO and serialization contract are **PROPOSED / BLOCKED**.

### 6. ARC-09 dashboard presentation

- **Existing implementation — VERIFIED:** static HTML/CSS/JavaScript in [`index.html`](../arc09-ui-prototype/index.html), [`mission-demo.js`](../arc09-ui-prototype/mission-demo.js), [`app.js`](../arc09-ui-prototype/app.js), and `mission-demo.css`.
- **Client request:** loads `GET /api/v1/missions/destinations`, then sends the same JSON request to `POST /api/v1/missions/validate` followed by `POST /api/v1/missions/run`. Calls use same-origin relative URLs; no configurable backend base URL or authentication header exists.
- **Presentation:** plots returned ECI X/Y position projection as SVG, provides a numeric state table and drift diagnostics, displays ARC-08 abstract totals/violations/policy-pending warning, and shows selected payload/profile information.
- **States/errors — VERIFIED:** adapter publishes loading, empty, ready, and error states; disables the run button during loading/run; clears the previous result on a new run or error; shows destination-loading failure and request errors. It flattens field details into a user-facing message. No timeout, cancellation, retry policy, or request correlation is implemented.
- **Other views:** spacecraft view states physical properties are unavailable. Resource view labels abstract units and pending policy status. Simulation view displays latest returned trajectory. Report view summarizes the latest run and clearly says cross-mission comparison/history is unavailable. These results live in browser memory only.
- **Tests:** [`test_dashboard.py`](../tests/mission_demo/test_dashboard.py) statically checks form/client endpoints, state publication, view hosts, scientific/policy labels and unavailable capabilities; [`test_api.py`](../tests/mission_demo/test_api.py) verifies local API/dashboard serving. No browser automation or production frontend build was run for this readiness review.
- **Limitations/gaps:** overview cards/charts are illustrative synthetic samples, not run results. The client assumes exact local response field names. It does not show collision method/radius, persistence, history, true mission comparison, physical spacecraft properties, or NASA data. The local adapter's frontend/backend behavior is not a cross-repository production contract.
- **Production status:** local integration is **VERIFIED** by source/tests; target frontend authority, API compatibility, and production readiness remain **UNVERIFIED / BLOCKED**.

## Dataset Validation separation

The current `develop` source has structural validation domain functions but no Dataset Validation HTTP route or dataset-validation transport DTO. ARC-10 v0.2 proposes only a separate dataset-validation candidate using illustrative `schema_id`, `schema_version`, and `records`; those fields are not an approved API or implemented interface. The draft files were read from the cached `origin/arc/10-api-integration` ref at `61d8c520b84cb7f28e0c7ba61863649bafe8c61c`, not from the current `develop` tree.

Do not pass mission configuration through Dataset Validation DTOs. Mission validation establishes only that mission-demo identifiers are accepted; it does not validate scientific data or imply scientific eligibility. Structural schema validity is not scientific or operational eligibility.

The exact independent validation interfaces and their incompatible semantics are documented in [NASAQ26_MISSION_API_INTERFACE_COMPATIBILITY.md](./NASAQ26_MISSION_API_INTERFACE_COMPATIBILITY.md).

## Overall workflow verdict

**Local educational flow: VERIFIED. Production Mission API contract: NOT APPROVED. Production implementation/deployment: BLOCKED pending authorities and explicit authorization.** Owner-selected Option C establishes separate API direction and priority only; it does not approve any field, route, HTTP status, security policy, data access, or deployment.
