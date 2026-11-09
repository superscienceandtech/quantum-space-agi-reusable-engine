# Quantum Space AGI Reusable Engine

The Quantum Space AGI Reusable Engine is a Python research and educational
framework for reusable scientific and simulation components. It provides a
foundation for reproducible numerical software while keeping individual models,
interfaces, and validation work explicit.

This repository is organized around numbered ARC workstreams. The README
documents implementation that is present in the repository; later or separate
ARC branches are not represented as completed project features here.

## Project vision

The project aims to develop reusable, reviewable building blocks for an
educational mission-design and space-systems game. The intended progression is
to combine scientific utilities, numerical models, simulation workflows,
visualization, optimization, AI/ML, and deployment components without obscuring
their assumptions or software boundaries.

The current objectives are:

- Use explicit units, coordinate frames, state representations, and model
  contracts.
- Preserve deterministic, reproducible numerical behavior.
- Keep canonical notebooks and reusable package implementations scientifically
  traceable.
- Validate numerical behavior with focused tests and reproducible execution.
- Separate domain models and integrations so that future capabilities are
  introduced only with documentation and tests.

## Current architecture

| Area | Responsibility |
| --- | --- |
| `src/quantum_space_agi/` | Python package root and versioned reusable modules |
| `src/quantum_space_agi/simulation/` | ARC-05 configuration, state, dynamics, RK4, propagation, diagnostics, collision, and workflow code |
| `notebooks/arc05_simulation/` | Canonical executable ARC-05 scientific notebooks |
| `tests/simulation/` | ARC-05 notebook and package integration tests |
| `docs/` | Design contracts, assumptions, and module documentation |

### ARC-04 Scientific Computing

ARC-04 is a separate scientific-computing workstream. Its feature branch
contains a notebook-first foundation for structured scientific errors,
validation, precision comparisons, vectors, matrices, units, and executable
tests.

The ARC-04 implementation is not part of the current ARC-05 base branch and
must not be inferred from the presence of a different worktree or branch.
Coordinate-frame work is limited to the separate ARC-04 notebook-based scope;
Earth-fixed/inertial conversions are not implemented by the ARC-05 package.
ARC-05 uses the complete two-body state and ECI conventions documented in this
repository without silently importing unpublished ARC-04 behavior.

### ARC-05 Simulation

ARC-05 is implemented on the `arc/05-simulation` workstream. It includes:

- Earth point-mass two-body orbital dynamics;
- an Earth-centered inertial (ECI) reference frame;
- metre, second, and metre-per-second SI state units;
- fixed-step classical Runge-Kutta fourth-order integration;
- orbital propagation over a configured duration;
- trajectory and orbital diagnostics;
- sampled and interpolated collision detection.

The public implementation is available under
`quantum_space_agi.simulation`. Other planned modules and future ARC
implementations are not claimed as complete unless their source, tests, and
documentation are present in the active repository branch.

## Installation

Python 3.11 or newer is required, as declared in `pyproject.toml`.

Create and activate a virtual environment, then install the package and its
runtime dependencies in editable mode:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
```

For development and notebook execution, install the declared extras:

```powershell
python -m pip install -e ".[dev,notebooks]"
```

Runtime dependencies are NumPy, Pydantic, and nbformat. Development extras add
pytest, nbclient, and ipykernel; notebook extras add JupyterLab and Matplotlib.

## Minimal simulation example

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

The returned mapping contains sampled Float64 times and six-component states,
trajectory diagnostics, model metadata, and collision fields. The state order is
`[x, y, z, vx, vy, vz]`; positions are metres and velocities are metres per
second.

## Testing

Install development dependencies and run the complete pytest suite from the
repository root:

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

For a concise run:

```powershell
python -m pytest -q
```

The tests discover notebook and package integration coverage under `tests/`.
Do not treat warnings or missing optional dependencies as evidence of a passing
check unless the pytest result explicitly reports success.

## ARC-05 documentation and notebooks

Detailed contracts, equations, assumptions, and limitations are documented in
[docs/arc05_simulation.md](docs/arc05_simulation.md).

The canonical ARC-05 notebooks are:

1. [01 Simulation Configuration](notebooks/arc05_simulation/01_simulation_configuration.ipynb)
2. [02 Orbital State](notebooks/arc05_simulation/02_orbital_state.ipynb)
3. [03 Two-Body Dynamics](notebooks/arc05_simulation/03_two_body_dynamics.ipynb)
4. [04 RK4 Integrator](notebooks/arc05_simulation/04_rk4_integrator.ipynb)
5. [05 Orbital Propagation](notebooks/arc05_simulation/05_orbital_propagation.ipynb)
6. [06 Simulation Diagnostics](notebooks/arc05_simulation/06_simulation_diagnostics.ipynb)
7. [07 Orbital Validation](notebooks/arc05_simulation/07_orbital_validation.ipynb)

## Scientific assumptions and limitations

ARC-05 currently uses:

- Earth-centered inertial coordinates;
- SI positions, velocities, and time;
- Newtonian point-mass Earth gravity;
- Float64 state arrays;
- fixed-step classical RK4;
- a spherical Earth reference radius for collision detection;
- linear radius interpolation as an approximation between collision-bracket
  samples.

The following capabilities are not included:

- atmospheric drag;
- J2 or other geopotential perturbations;
- thrust and control;
- third-body gravity;
- solar radiation pressure;
- adaptive timestep selection;
- attitude or rotational dynamics;
- collision response, terrain, entry, or descent modeling;
- high-precision orbit determination.

Normal propagation completion, collision detection, and numerical failure are
separate outcomes. A collision radius is a simulation convention, not a
validated mission-specific safety boundary.

Future development must introduce additional physical models only with explicit
equations, model identifiers, assumptions, convergence or scientific validation
tests, and documentation. It must not silently change the Earth two-body
baseline or replace fixed-step RK4 without justification.

## Contribution and development workflow

Contributions should be made on dedicated feature branches from the relevant
ARC base branch. Preserve unrelated work and existing local changes, and keep
ARC-04 and ARC-05 changes separated.

Recommended workflow:

1. Create or use a dedicated feature branch.
2. Make the smallest change that addresses the documented scope.
3. Update directly related documentation and tests.
4. Install development dependencies with the declared extras.
5. Run focused tests first, then the complete pytest suite.
6. Review package discovery, public imports, and working-tree changes.
7. Commit only related source, documentation, notebook, and test files.

Use descriptive branches and commits, preserve scientific assumptions in
documentation, and do not present notebook output or a package behavior as
validated unless the relevant executable tests confirm it.
