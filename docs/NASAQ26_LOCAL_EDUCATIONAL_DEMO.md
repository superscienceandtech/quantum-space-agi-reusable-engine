# NASAQ26 Local Educational Mission Demo

This local-only demonstration connects synthetic mission-profile inputs to the existing ARC-05 Earth two-body simulator and the existing ARC-08 educational payload evaluator. It is not the ARC-10 production API contract.

## Run locally

Create a separate virtual environment for this checkout or worktree. Editable
install metadata is tied to the source directory, so do not reuse an environment
from a neighboring checkout.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[api]"
.venv/bin/python -c "from pathlib import Path; import quantum_space_agi; expected = (Path.cwd() / 'src/quantum_space_agi/__init__.py').resolve(); actual = Path(quantum_space_agi.__file__).resolve(); assert actual == expected, f'{actual} is not {expected}'; print(actual)"
.venv/bin/python -m quantum_space_agi.mission_demo.server
```

On Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[api]"
.venv\Scripts\python.exe -c "from pathlib import Path; import quantum_space_agi; expected=(Path.cwd() / 'src/quantum_space_agi/__init__.py').resolve(); actual=Path(quantum_space_agi.__file__).resolve(); assert actual == expected, f'{actual} is not {expected}'; print(actual)"
.venv\Scripts\python.exe -m quantum_space_agi.mission_demo.server
```

Open `http://127.0.0.1:8765/`. The server binds only to loopback and serves the ARC-09 dashboard alongside the versioned local API. Stop it with Ctrl+C.
The import check, package installation, and server launch all use the same
environment-specific Python executable. The import path must point to this
checkout's `src/quantum_space_agi`, not another worktree.

For a WSL checkout under `/mnt/<drive>`, keep the environment on the Linux
filesystem to avoid mounted-drive symlink and package-install performance
problems. Give each checkout its own environment path:

```bash
mkdir -p "$HOME/.venvs"
python3 -m venv "$HOME/.venvs/nasaq26-develop-worktree"
"$HOME/.venvs/nasaq26-develop-worktree/bin/python" -m pip install -e ".[api]"
"$HOME/.venvs/nasaq26-develop-worktree/bin/python" -c "from pathlib import Path; import quantum_space_agi; expected = (Path.cwd() / 'src/quantum_space_agi/__init__.py').resolve(); actual = Path(quantum_space_agi.__file__).resolve(); assert actual == expected, f'{actual} is not {expected}'; print(actual)"
"$HOME/.venvs/nasaq26-develop-worktree/bin/python" -m quantum_space_agi.mission_demo.server
```

Use a different path for each checkout and run these commands from that
checkout's repository root.

Python 3.11 or later is declared in `pyproject.toml`. This environment's active interpreter should be checked before treating Python 3.11 runtime compatibility as verified.

## Clerk configuration

The dashboard fails closed when Clerk is not configured: mission operations stay
disabled and synthetic profiles are not requested. The public auth configuration
route reports `enabled: true` only when `CLERK_PUBLISHABLE_KEY`,
`CLERK_FRONTEND_API_URL`, and `CLERK_ALLOWED_ORIGINS` are all set.

For local use, configure a Clerk application and set its values in the shell
before starting the server. Use the exact local dashboard origin for
`CLERK_ALLOWED_ORIGINS`:

```bash
export CLERK_PUBLISHABLE_KEY="pk_test_<your-clerk-publishable-key>"
export CLERK_FRONTEND_API_URL="https://<your-clerk-frontend-api-origin>"
export CLERK_ALLOWED_ORIGINS="http://127.0.0.1:8765"
# Optional; set only when the Clerk session token uses an audience.
# export CLERK_AUDIENCE="<configured-audience>"
.venv/bin/python -m quantum_space_agi.mission_demo.server
```

The example values are placeholders, not credentials. The app does not load a
`.env` file automatically; set variables in the process environment or a
secrets manager. `CLERK_SECRET_KEY` is not used or read by this integration.
For staging, use the exact HTTPS service origin and configure live
values in the provider's secure environment settings; see
[`NASAQ26_BACKEND_STAGING_DEPLOYMENT_PLAN.md`](./NASAQ26_BACKEND_STAGING_DEPLOYMENT_PLAN.md).

This dashboard is static HTML and vanilla JavaScript, not a React application;
it uses ClerkJS rather than `ClerkProvider`. The browser fetches the public auth
configuration, loads Clerk UI v1 and ClerkJS v6 from the configured Frontend
API, and obtains a session token in memory for each mission API request. These
are CDN-loaded versions, not installed npm dependencies. FastAPI verifies that
token against Clerk's public JWKS before serving the profile, validation, or run
routes.

## Versioned local API

Dataset Validation is a separate capability and is not exposed or routed through
these Dashboard Mission APIs.

| Method and route | Purpose | Success response |
| --- | --- | --- |
| `GET /health` | Local process health | `{"status":"ok"}` |
| `GET /api/v1/missions/destinations` | Read synthetic orbit profiles | `{"destinations":[{"profile_id","display_name","altitude_m","simulation_duration_s","time_step_s","assumptions","classification"}]}` |
| `POST /api/v1/missions/validate` | Validate only; does not execute ARC-05 or ARC-08 | `{"valid":true,"mission":{"destination_profile_id","destination_display_name","spacecraft_profile_id","selected_payload_ids"}}` |
| `POST /api/v1/missions/run` | Validate, run ARC-05, run ARC-08, return the unified result | Mission, resource evaluation, and trajectory fields described below |

Mission POSTs require `Content-Type: application/json`.

`POST /api/v1/missions/validate` and `POST /api/v1/missions/run` accept:

```json
{
  "destination_profile_id": "synthetic-leo-400-km",
  "selected_payload_ids": ["imager", "relay"]
}
```

Supported synthetic orbit profiles are `synthetic-leo-400-km`, `synthetic-leo-800-km`, and `synthetic-earth-orbit-2000-km`. Payload identifiers are validated against ARC-08's existing `resource-selection-demo-v1` scenario. The list must be non-empty, contain unique known IDs, and no unknown fields are accepted. Validation returns a canonical mission summary with payload IDs in sorted order and does not run either evaluator. The spacecraft profile records payload selection only; it defines no vehicle mass, capacity, propulsion, or fuel.

The dashboard validates the configuration before running. A successful run response contains:

- `classification` and `limitations` labels.
- `mission` profile and payload identifiers.
- `resource_evaluation`, produced by ARC-08 after ARC-05 completes.
- `trajectory.times_s` and `trajectory.states`; each state row is `[x_m, y_m, z_m, vx_mps, vy_mps, vz_mps]` in ECI SI units.
- `trajectory.state_order`, collision index/time/state, diagnostics, and model metadata. Diagnostic arrays and trajectory data are JSON arrays; the response DTO rejects non-finite numeric values.

The Mission Builder reports sign-in, profile loading, empty-profile, and loading
failure states separately. The Run button stays disabled until the authenticated
profile response is valid, a listed profile is selected, and at least one
supported payload is selected. On submission, the API validates the request
before starting the simulation. The run route is not separately preflighted:
its availability is confirmed by the actual run request, and failures are
shown without fabricating a result.

## Dashboard result views

The browser keeps the latest successful mission response in memory only. A new
run or an API error clears the previous result; reloading the page returns the
result views to their empty state.

- Spacecraft Configuration shows the returned spacecraft profile ID and
  selected payload IDs. Mass, dimensions, propulsion, fuel, capacity, and power
  are unavailable because the API does not model those properties.
- Resource Dashboard shows ARC-08's evaluator version, scenario, abstract-unit
  totals, violations, warning, and policy-approval status. Scenario feasibility
  is not mission feasibility; policy approval remains pending.
- Simulation & Results shows ARC-05 model metadata, the ECI X/Y trajectory
  projection, numeric state table, and returned drift diagnostics.
- Mission Comparison & Report summarizes the latest run. Cross-mission
  comparison and mission history are unavailable because the local API exposes
  neither capability.

Errors have the shape:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The mission request did not pass validation.",
    "details": [{"field": "selected_payload_ids", "message": "..." }]
  }
}
```

`details` is an empty array when no field-level detail applies. Invalid JSON
returns `400 malformed_json`; unsupported content type returns
`415 unsupported_media_type`; schema/domain validation returns
`422 validation_error`; unknown routes return `404 not_found`; unsupported
methods return `405 method_not_allowed`; unexpected execution or invalid
non-finite output returns `500 mission_run_failed` without exception details.
The API remains a local educational demo, not a production or ARC-10 service.

## ARC-08 resource-evaluation boundary

The existing ARC-08 evaluator runs after the ARC-05 simulation and its result is always returned. Its `feasible` field applies only to the evaluator's educational scenario; policy approval remains pending and this output does not approve a spacecraft resource policy, gate, or alter the orbit simulation. Budget/mass/power/slot values are abstract educational units, not physical quantities. Do not label the result as mission feasibility.

## Synthetic orbit assumptions and limitations

- Each profile specifies altitude above `EARTH_REFERENCE_RADIUS_M`; initial position is `[radius, 0, 0]` and velocity is `[0, sqrt(mu/radius), 0]`.
- Initial state is an idealized circular orbit in ECI using the existing ARC-05 Earth gravitational parameter, fixed-step RK4 integrator, two-body model, and profile duration/timestep.
- This is an initial orbit simulation, not an orbit transfer, destination rendezvous, launch plan, or spacecraft trajectory design.
- Provenance is the repository's educational ARC-05 Earth two-body/RK4 implementation and the ARC-08 `resource-selection-demo-v1` evaluator scenario. The local profile inputs are synthetic; no NASA data is fetched or claimed.
- No atmosphere, perturbations, thrust, spacecraft mass, fuel estimate, NASA data, or scientifically validated mission prediction is included.
- The trajectory chart is an ECI X/Y projection; the table is the accessible numeric alternative.
- The server has no production authentication, CORS policy, deployment controls, or ARC-10 route status. Keep it on loopback for this educational prototype.
