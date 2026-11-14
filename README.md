# Quantum Space AGI Reusable Engine

This repository contains reusable foundations for scientific data processing,
numerical simulation, and educational space-mission design. It is not a complete
NASA Space Apps game, a flight system, or a source of authoritative scientific
data.

## Current components

| Area | Responsibility |
| --- | --- |
| `src/quantum_space_agi/core/` | General numerical, validation, and result primitives |
| `src/quantum_space_agi/data/` | ARC-03 ingestion, provenance, schema validation, quality, export, and data adapters |
| `src/quantum_space_agi/scientific/` | ARC-04 scientific utilities and coordinate/frame support |
| `src/quantum_space_agi/simulation/` | ARC-05 Earth point-mass two-body dynamics, RK4 propagation, and diagnostics |
| `src/quantum_space_agi/ml/` | ARC-08 dataset, reproducibility, and educational evaluator utilities |
| `notebooks/` | Executable scientific and simulation learning material |
| `tests/` | Focused package and integration tests |
| `arc09-ui-prototype/` | Dashboard with synthetic overview panels and a local ARC-05/ARC-08 mission run |

These reusable components include a local educational mission demo. The demo
connects synthetic configuration inputs to ARC-05 and ARC-08 and displays their
results in the ARC-09 dashboard; it is not a complete mission-planning game or
production API.

## Scope and limitations

ARC-03 provides source/provenance models, local JSON/CSV ingestion, declarative
schema validation, quality analysis, safe export, and provider-neutral adapter
contracts. It does not provide general NASA API access, automatic type coercion,
or scientific validation. A bounded, read-only NASA Exoplanet Archive TAP
adapter exists in the codebase; its presence does not authorize a data request,
retention, redistribution, or publication. See
[`docs/EXOPLANET_ARCHIVE_ADAPTER.md`](docs/EXOPLANET_ARCHIVE_ADAPTER.md).

`Dataset` exposes top-level records and metadata as read-only mappings, but
nested dictionaries and lists are not deep-copied or frozen. CSV headers are
inferred from record keys; an empty dataset exports an empty CSV, and CSV cannot
retain provenance or dataset metadata. Use JSON when traceability is needed.
Explicit CSV headers are not currently supported.

ARC-05 uses Earth-centered inertial coordinates, SI position/velocity/time,
Newtonian point-mass Earth gravity, Float64 state arrays, and fixed-step RK4.
The model excludes atmospheric drag, geopotential perturbations, thrust,
third-body gravity, solar radiation pressure, attitude dynamics, and adaptive
timesteps. Collision detection uses a spherical reference radius and an
interpolation approximation. ARC-05 does not implement Earth-fixed/inertial
coordinate conversion. Collision radius is a simulation convention, not a
mission-specific safety boundary; normal completion, collision, and numerical
failure are separate outcomes. Results are educational, not scientifically
validated mission predictions.

ARC-08 includes reusable dataset and ML utilities, plus a fictional
payload/resource evaluator. The evaluator's budget, mass, power, and slot totals
are abstract educational units, not physical spacecraft properties or fuel
estimates. Its presence does not authorize a training or prediction claim.
The local mission demo uses synthetic Earth-orbit profiles with the ARC-05
two-body simulator, then reports ARC-08's actual educational evaluator output
with resource-policy approval explicitly pending. ARC-09's remaining overview
panels are illustrative synthetic samples; only the mission result section is
backed by live local calculations. See
[`docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md`](docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md)
for API routes, assumptions, and limitations.

## Installation

Python 3.11 or newer is required. Create and activate a virtual environment,
then install the package with development and notebook dependencies:

```shell
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,quality,notebooks]"
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

To run the local mission dashboard, install its optional API dependencies and
start the loopback-only server:

```shell
python -m pip install -e ".[api]"
python -m quantum_space_agi.mission_demo.server
```

Open `http://127.0.0.1:8765/`. Windows PowerShell users can use the same commands
after activating the virtual environment. The API and startup details are in
[`docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md`](docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md).

## Minimal ARC-05 simulation example

```python
from quantum_space_agi.simulation import SimulationConfig, run_simulation

config = SimulationConfig(
    initial_position_m=(7_000_000.0, 0.0, 0.0),
    initial_velocity_mps=(0.0, 7_500.0, 0.0),
    simulation_duration_s=600.0,
    time_step_s=10.0,
    collision_radius_m=6_378_137.0,
)
result = run_simulation(config)
print(result["times_s"].shape)
print(result["states"].shape)
print(result["collision_time_s"])
```

The state order is `[x, y, z, vx, vy, vz]`; positions are metres and velocities
are metres per second. See
[`docs/arc05_simulation.md`](docs/arc05_simulation.md) for model details.

## Tests and quality checks

```shell
python -m pytest
ruff check .
ruff format --check .
mypy
python -m build
```

Notebook tests may require local socket access to start a kernel. Report
environment restrictions separately from assertion failures; do not claim a
clean full-suite result unless the test command reports success.

## Development workflow

Use short-lived branches and preserve unrelated work. Until maintainers specify
otherwise, repository guidance names `develop` as the default pull-request
target. Keep ARC workstreams focused, document model assumptions and units, and
include deterministic tests. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

MIT is the recorded license direction, but no `LICENSE` file is present. Do not
assume reuse under MIT terms until the license is formally added; see
[`docs/governance/license-options.md`](docs/governance/license-options.md).
# NASAQ26 Local Educational Demo

The integrated local-only mission demonstration and its route/input/output description are documented in [`docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md`](docs/NASAQ26_LOCAL_EDUCATIONAL_DEMO.md). It uses synthetic Earth-orbit profiles, the existing ARC-05 educational simulator, and ARC-08 educational resource output. Resource policy approval remains pending; the evaluator's abstract units do not indicate mission eligibility. The local service is not an ARC-10 production API and makes no scientific validation claim.

Start from the repository root with:

```bash
PYTHONPATH=src python -m quantum_space_agi.mission_demo.server
```

Open `http://127.0.0.1:8765/`.
