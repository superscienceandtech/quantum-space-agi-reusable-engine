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
| `arc09-ui-prototype/` | Standalone synthetic HTML/CSS/JavaScript/SVG visualization prototype |

These are reusable components and separate prototypes. Their presence does not
establish a complete integrated mission-planning application, backend service,
or production API.

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
ARC-09 is a synthetic static visualization prototype, not connected to these
Python components or a production API.

## Installation

Python 3.11 or newer is required. Create and activate a virtual environment,
then install the package with development and notebook dependencies:

```shell
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,quality,notebooks]"
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

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
