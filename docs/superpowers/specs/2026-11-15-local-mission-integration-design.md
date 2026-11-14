# Local Mission Integration Design

## Goal

Deliver a local educational workflow in the existing integration worktree:

Mission Configuration -> Input Validation -> ARC-05 Orbit Simulation ->
ARC-08 Resource Evaluation -> Unified Mission Result -> ARC-09 Dashboard.

Reuse the current domain implementations and dashboard contribution. Do not
rebuild completed ARC modules or treat the prototype as a production flight
system.

## Architecture

- Add FastAPI and Uvicorn as an optional API dependency group. Keep scientific
  and resource-evaluation modules independent of the web framework.
- Place request/response DTOs, mission orchestration, HTTP transport, and static
  dashboard serving at the mission-demo/API boundary. Retain the current
  synthetic destination and payload validation behavior.
- Keep Dataset Validation API separate; do not expose or repurpose its routes
  for mission requests.
- Bind the local application to loopback and serve the dashboard and API from
  one origin. No external NASA data or network service is required.

## Mission API

Use the versioned `/api/v1` namespace:

- `GET /health`: local application health.
- `GET /api/v1/missions/destinations`: supported synthetic profiles and their
  assumptions.
- `POST /api/v1/missions/validate`: validate the mission request without
  running either evaluator.
- `POST /api/v1/missions/run`: validate, run the ARC-05 simulator, run the
  existing ARC-08 educational evaluator, and return a unified result.

The mission request contains a supported `destination_profile_id` and a
non-empty list of unique `selected_payload_ids`. Reject unknown fields and
unsupported profile/payload identifiers. The unified result contains mission
identity, synthetic classification and assumptions, ARC-05 trajectory and
diagnostics with units/model provenance, and ARC-08's actual scenario output.
Convert NumPy values to JSON-safe arrays/scalars and reject non-finite JSON.

ARC-08 results describe only the existing fictional educational scenario.
Expose that resource-policy approval is pending; do not use its `feasible`
field as mission eligibility or gate/alter the ARC-05 simulation. Resource
totals remain abstract units; do not invent fuel or other physical quantities.
No NASA data provenance or validated prediction is claimed.

Use one explicit error envelope for invalid requests and failed mission runs.
Validation errors should identify the rejected fields; unexpected failures
must not expose tracebacks or internal details. Keep status codes consistent
across validation, media-type, missing-route, and execution failures.

## Dashboard

Preserve the ARC-09 visual design and wire the mission form to the versioned
API. Load destination choices from the API, validate before a run, and render
only actual response data as mission results. Show loading, validation,
empty/ready, and backend error states. Plot the returned ECI X/Y trajectory
and offer the numeric trajectory table. Explain SI units, synthetic inputs,
the ARC-05 model limits, and ARC-08's unapproved abstract-unit boundary.
Existing illustrative widgets may remain only with their current synthetic
sample labels.

## Integration and verification

Preserve pre-existing tracked and untracked work. Inspect each remote branch
before merging, avoid duplicate history, and incorporate the verified ARC-05
commit `c9258d187e09ee83e5205364894b42e975c3e5da` if it is not already in the
integration history. Reuse ARC-03/08/09 work already present and only take
relevant ARC-10 contributions after reviewing their actual contents.

Add deterministic DTO, route, mission orchestration, serialization, and
dashboard behavior tests. Verify relevant ARC-04/05 and ARC-08 suites, the
dashboard build/check, local end-to-end smoke behavior, and the full
non-notebook pytest suite where feasible. Report exact commands and results.

Follow `CONTRIBUTING.md`: do not work directly on `main`; prepare the reviewed
integration for the designated PR target (`develop`) and do not claim remote
integration without an authorized merge.

## Acceptance criteria

1. A local user can select a synthetic orbit profile and payloads, validate
   them, run the mission, and view actual ARC-05 and ARC-08 outputs in the
   dashboard.
2. The API returns JSON-safe, versioned responses and explicit errors.
3. Resource policy status and scientific assumptions are visible and are not
   presented as approved physical feasibility.
4. Existing unrelated work and dashboard design are preserved.
5. Test, build, Git, and remote-main status are reported from observed results.
