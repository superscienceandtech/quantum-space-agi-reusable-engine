DRAFT — NOT APPROVED

# NASAQ26 Mission Planning & Simulation API
## Candidate Contract Proposal v0.1

**Status:** Candidate only. This is not a canonical contract, implementation authorization, security approval, or deployment approval.  
**Product direction:** Project Owner selected Option C: keep Mission Planning & Simulation separate from Dataset Validation, with Mission API as Priority 1. This is product direction only.  
**Evidence snapshot:** `develop` `6a44af34a649a1138cf577b3b16dbaf436c8a203`; local mission-demo implementation and tests.

## 1. Scope and boundary

This proposal describes a candidate transport boundary for a synthetic educational mission workflow:

`Mission Configuration → Input Validation → ARC-05 Simulation → ARC-08 Educational Resource Evaluation → Unified Result → ARC-09 Presentation`

It does not add or modify application code. It does not replace ARC-10 Dataset Validation v0.2. The current local demo routes and DTOs are evidence, not approval. Each route, method, field, response status, and operational behavior below is **PROPOSED — PENDING REVIEW**.

### Operation separation

| Candidate operation | Candidate method/route | Boundary |
|---|---|---|
| Read supported synthetic profile catalog | `GET /api/v1/missions/destinations` | Mission-specific catalog; not a NASA destination service. |
| Validate mission configuration | `POST /api/v1/missions/validate` | Validate request shape/profile/payload identifiers only; do not run simulation/evaluation. |
| Run educational mission workflow | `POST /api/v1/missions/run` | Compose ARC-05 and ARC-08 and return a unified result. |
| Process health | `GET /health` | Exists only in the local demo. Whether it belongs in an approved API and what readiness it proves are operational decisions. |

These are candidates based on current local routes in [`api.py`](../src/quantum_space_agi/mission_demo/api.py); they are not approved production routes. Dataset Validation has no route in the current `develop` source and is not included here.

## 2. Candidate request DTO

### Mission configuration

Current local request evidence in [`MissionRequestDTO`](../src/quantum_space_agi/mission_demo/dto.py):

```json
{
  "destination_profile_id": "synthetic-leo-400-km",
  "selected_payload_ids": ["imager", "relay"]
}
```

Candidate member mapping:

| Field | Candidate wire type | Candidate constraints | Evidence/status |
|---|---|---|---|
| `destination_profile_id` | string | Required; identifier must resolve in the approved synthetic profile catalog. | Local DTO enforces a current profile ID. **PROPOSED** for a future contract; catalog authority/version are unapproved. |
| `selected_payload_ids` | array of strings | Required; non-empty; unique; identifiers must be supported by the selected ARC-08 scenario. | Local DTO/configuration enforce these properties and canonical sorting. **PROPOSED**; public catalog and scenario selection are undecided. |

Candidate strictness is to reject unknown fields and malformed/non-JSON input rather than silently ignore values. Exact type coercion, case sensitivity, whitespace policy, maximum request size, and catalog evolution are **UNRESOLVED / BLOCKED**.

This request does not accept raw state vectors, orbital elements, simulation duration/timestep, arbitrary `mu`, spacecraft engineering properties, mission objectives, NASA data references, or caller-provided scientific provenance. The local demo derives fixed simulation inputs from its synthetic profile. Adding any such field would require new domain behavior and separate technical review.

No separate `scenario_id` is proposed in this first candidate: the current service selects `resource-selection-demo-v1` internally. Whether a future caller may choose among scenarios is **UNRESOLVED** and must not be inferred.

## 3. Candidate response DTO

The candidate unified success response is based on actual local output in [`MissionDemoService.run`](../src/quantum_space_agi/mission_demo/service.py) and [`MissionRunResponseDTO`](../src/quantum_space_agi/mission_demo/dto.py), with an explicit compatibility decision needed for engine collision metadata.

| Path | Candidate type/meaning | Evidence and open contract decision |
|---|---|---|
| `classification` | String explicitly classifying the run as synthetic educational output. | Local value exists; exact enum/string stability needs approval. |
| `limitations` | Array of profile/model assumption strings. | Local profile supplies assumptions; decide whether this free-text field is stable API or informational. |
| `mission.destination_profile_id` | String catalog identifier. | Local field exists. |
| `mission.destination_display_name` | String display label. | Local field exists; display labels are not identifiers. |
| `mission.spacecraft_profile_id` | String payload-carrier label. | Local field exists; not a physical spacecraft model. |
| `mission.selected_payload_ids` | Array of sorted string identifiers. | Local field exists; sorting/canonicalization must be documented. |
| `resource_evaluation.status` | Candidate evaluation state. | Local literal `"evaluated"` when it completes. Failure/partial-result states are not implemented. |
| `resource_evaluation.policy_approval_status` | Candidate pending/approval label. | Local value is `"pending"`; no policy authority or approval is established. |
| `resource_evaluation.policy_authority`, `warning` | Text disclaiming policy/physical interpretation. | Local demo fields exist; stable wording/version policy unresolved. |
| `resource_evaluation.result` | Scenario, evaluator version, sorted payload IDs, boolean educational `feasible`, violations, abstract totals, optional score. | Actual ARC-08 serialized result; names/semantics must preserve abstract units and not imply mission feasibility. |
| `trajectory.times_s` | JSON array of finite numbers in seconds, starting at zero. | Converts NumPy float64 samples to JSON arrays. Precision and size limit unresolved. |
| `trajectory.states` | Array of six-number rows, `[x_m,y_m,z_m,vx_mps,vy_mps,vz_mps]`. | Local `state_order` declares this sequence; units are metres and metres/second. |
| `trajectory.diagnostics` | Finite-number arrays/scalars for energy, angular momentum, eccentricity, radius, speed, and drifts. | Local DTO enumerates fields and units in names; exact compatibility/version rules unresolved. |
| `trajectory.model` | Frame `ECI`, integrator `RK4`, dynamics name, seconds/metres/metres-per-second. | Actual local metadata; not evidence of a validated operational prediction. |
| `trajectory.collision_index`, `collision_time_s`, `collision_state` | Nullable collision details. | Present in local DTO. Null/absence semantics and indexing need approval. |
| `trajectory.collision_radius_m`, `collision_method` | Candidate fields to preserve simulator threshold and event method. | ARC-05 returns both, but local service/DTO currently omit them. **PROPOSED addition; explicit approval and compatibility tests required.** |

Candidate shape sketch (illustrative, not a valid or guaranteed response fixture):

```text
{
  classification,
  limitations,
  mission: { destination_profile_id, destination_display_name,
             spacecraft_profile_id, selected_payload_ids },
  resource_evaluation: {
    status, policy_approval_status, policy_authority, warning,
    result: { selected_payload_ids, evaluator_version, scenario_id, feasible,
              violations, resource_totals, educational_score }
  },
  trajectory: {
    times_s, states, state_order, collision details, diagnostics, model
  }
}
```

No ARC-08 field may be labeled as kilograms, watts, physical budget, fuel, or mission feasibility. No NASA data provenance may be implied. Component provenance/version, uncertainty, numerical error estimates, model certification, and run timestamps are not currently present in the local result; adding them is **UNVERIFIED / BLOCKED**, not assumed.

## 4. Validation and result behavior proposal

Proposed request validation, pending contract approval:

1. Require JSON object and appropriate JSON media type for mission POSTs.
2. Reject unknown top-level fields.
3. Require a supported synthetic profile and a non-empty list of unique supported payload identifiers.
4. Canonicalize payload identifier order as the local implementation does, if approved.
5. Treat validation as input validation only; do not imply scientific validation or resource-policy approval.
6. For `/missions/run`, construct the existing simulator/evaluator domain inputs only through the reviewed application mapping.
7. Keep ARC-08's `feasible` field scoped to its educational scenario. A violation is a successful evaluation result, not automatically a failed HTTP request.
8. Do not silently return a partial success if either component fails. Partial-result policy is unresolved; default candidate is to report a failed operation without representing it as a complete unified result.

The local service runs ARC-05 first and ARC-08 second. That sequence is verified local behavior, not a scientific dependency. The future contract owner must decide whether to retain it and approve what happens when either stage raises.

## 5. Candidate error envelope and HTTP mapping

The local error DTO shape is:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The mission request did not pass validation.",
    "details": [
      {"field": "selected_payload_ids", "message": "A field-level explanation."}
    ]
  }
}
```

Reusing this envelope is **PROPOSED**, not approved. Stable code vocabulary, localization, message stability, request/correlation identifier, detail redaction, and domain-vs-transport classification remain open.

| Candidate condition | Candidate status/code | Status |
|---|---|---|
| Malformed JSON | `400 malformed_json` | Mirrors local demo; production choice pending. |
| Unsupported request media type | `415 unsupported_media_type` | Mirrors local demo; production choice pending. |
| Invalid/missing/unknown mission fields | `422 validation_error` with `details` | Mirrors local demo; field semantics pending. |
| Unknown route/method | `404 not_found` / `405 method_not_allowed` | Mirrors local demo; standardization pending. |
| ARC-05/ARC-08 execution or output validation failure | `500 mission_run_failed` with generic public message | Local generic behavior; production error taxonomy and incident policy pending. |
| Educational evaluator reports constraint violation | Candidate successful evaluation response with `feasible:false` and violations | Supported domain behavior; must not be confused with a transport/server error. |

These mappings do not determine authorization, rate-limit, timeout, cancellation, overload, dependency, or partial-result responses. Those cases are **BLOCKED** for decision.

## 6. JSON serialization and versioning

- **PROPOSED:** keep transport DTOs separate from ARC-05/08 domain objects; map fields explicitly in an application service.
- **VERIFIED locally:** NumPy arrays become lists with `.tolist()`; ARC-08 result uses its canonical JSON serializer; Pydantic response DTO rejects non-finite floats.
- **PROPOSED:** retain a major version in the URL (the local demo uses `/api/v1/...`) for a first candidate. The version path is not a production commitment; compatibility, deprecation, additive-field, and breaking-change rules require contract-owner approval.
- **UNRESOLVED:** numeric precision policy, exact array length/schema, collision field inclusion, maximum serialized response size, handling of non-finite values, and provenance/version identity for ARC-05.
- **NOT IN SCOPE:** serializing Python/NumPy implementation objects directly or allowing framework defaults to define the public contract.

## 7. Idempotency and execution semantics

The current local `POST /missions/run` has no persistence or external side effect; it recomputes from catalog inputs and deterministic component code. It has no idempotency-key support and no stored run ID.

**PROPOSED:** initially treat a run as a read-only computation with no persistence guarantee. Do not promise byte-identical results across software versions or deployments. A client retry may repeat computation and consume resources. If persistence, asynchronous execution, billing, external access, or other side effects are later added, define a request idempotency mechanism and lifecycle before implementation.

Execution time, maximum steps/result size, cancellation, retry policy, concurrency, and overload behavior are **UNVERIFIED / BLOCKED**.

## 8. Authentication, authorization, privacy, and operations

The current server in [`server.py`](../src/quantum_space_agi/mission_demo/server.py) binds to `127.0.0.1`; this is a local educational boundary, not a production security design. No production authentication, authorization, CORS, secrets, data retention, or deployment controls are established.

Questions requiring named authority and written decision:

- Who may call the service, and from which network boundary?
- Is authentication required for any non-loopback environment? What principal, credential lifecycle, and authorization scope apply?
- What CORS origins, if any, are permitted?
- Can requests/results contain sensitive or NASA-controlled information? What logging, redaction, retention, and deletion rules apply?
- What request/result size, duration, concurrency, and rate limits are supported by measured workloads?
- Who owns alerts, incident response, service health/readiness semantics, and release/deployment?

No mechanism is selected in this proposal. **BLOCKED** from non-loopback production deployment until security, privacy/data-rights, platform, and operations authorities are identified and approve applicable controls.

## 9. Observability proposal

**PROPOSED for review:** record a server-generated correlation identifier; operation outcome and duration; safe component stage/error code; application, ARC-08 evaluator, and simulation/model version metadata when verifiably available. Do not log full request payloads, sensitive values, or internal exception text in client responses. Keep exception detail in access-controlled server logs according to an approved policy.

The local API currently logs unexpected exceptions through `logger.exception` and returns a generic `mission_run_failed` response, but has no verified correlation ID, metrics contract, retention policy, or production alerting. Sampling, retention, access, and telemetry content require authority decisions.

## 10. Dataset Validation is a separate contract

Dataset Validation remains a distinct operation under the Project Owner's Option C direction. It must not reuse `MissionRequestDTO`, `MissionRunResponseDTO`, or mission routes. ARC-10 v0.2's illustrative `schema_id`, `schema_version`, and `records` request is not canonical or approved; its response concepts and `scientific_eligibility` marker are not accepted here.

Before that API can be specified, an authorized reviewer must choose exactly one underlying validator and decide schema catalog, provenance construction, empty-input, extra-field, index-base, error-code, and scientific-interpretation behavior. Structural validation must not imply scientific eligibility. See [`NASAQ26_MISSION_API_INTERFACE_COMPATIBILITY.md`](./NASAQ26_MISSION_API_INTERFACE_COMPATIBILITY.md).

## 11. Approval boundary

This candidate v0.1 does not close ARC-10 D-01 through D-16 or reconcile the D-04/D-05 numbering discrepancy. Its `MAPI-*` decision IDs are kept in a separate register and are not mappings to ARC-10 D-numbers.

**Contract status: NOT APPROVED. Implementation status: BLOCKED.** The Project Owner's confirmed Option C selects separate API direction and priority only. A designated contract owner and final approver, ARC-05/08 reviewers, ARC-09 authority, security/privacy/operations authorities, test acceptance authority, target repository/branch, and explicit implementation authorization remain required.
