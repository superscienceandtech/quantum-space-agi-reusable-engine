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

Workstream ownership: Amran owns ARC-04 and ARC-05. Yousuf is the team leader.

## Current architecture

| Area | Responsibility |
| --- | --- |
| `src/quantum_space_agi/` | Python package root and versioned reusable modules |
| `src/quantum_space_agi/scientific/` | ARC-04 structured errors, units, coordinate frames, and rigid transforms |
| `src/quantum_space_agi/simulation/` | ARC-05 configuration, state, dynamics, RK4, propagation, diagnostics, collision, and workflow code |
| `notebooks/arc04_scientific/` | Canonical executable ARC-04 scientific notebooks |
| `notebooks/arc05_simulation/` | Canonical executable ARC-05 scientific notebooks |
| `tests/scientific/` | ARC-04 scientific validation tests |
| `tests/simulation/` | ARC-05 notebook and package integration tests |
| `docs/` | Design contracts, assumptions, and module documentation |

### ARC-04 Scientific Computing

ARC-04 remains a distinct scientific-computing workstream. This repository
contains its structured error types, unit definitions, Cartesian coordinate
frames, rigid transformations, executable notebooks, and validation tests.
The general coordinate-frame utilities do not implement Earth-fixed/inertial
conversions. ARC-05 uses the two-body state and ECI conventions documented here
without silently depending on ARC-04 behavior.

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
The canonical Windows project environment is `.venv`; Python 3.11 compatibility
has not been verified.

### Isolated Python 3.11 verification

At the 2026-11-14 environment audit, `py -0p` listed only Python 3.14.1.
Python 3.11 was not installed, so this verification has not been run. Current
Python 3.11 security releases are source-only; the last traditional Windows
installer was 3.11.9. For a current 3.11 runtime, the supported path is the
[Python install manager](https://docs.python.org/3/using/windows.html#python-install-manager).
Installing the manager and its runtime changes the current user's Python
environment, so obtain authorization before doing either. After authorization,
install the manager from the [official Python downloads page](https://www.python.org/downloads/windows/)
or Microsoft Store, then run `pymanager install 3.11` to install the latest
available 3.11 security runtime (currently 3.11.18). `pymanager` avoids a
possible command conflict with the legacy `py.exe` launcher on this host. Do
not enable PATH changes if they are not wanted. Then run the following from
the repository root in PowerShell. It creates a separate `.venv311` and does
not replace `.venv`:

```powershell
pymanager exec -V:3.11 --version
pymanager exec -V:3.11 -m venv .venv311
.\.venv311\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv311\Scripts\python.exe -m pip install -e ".[dev,notebooks]"
.\.venv311\Scripts\python.exe -m pytest -q
.\.venv311\Scripts\python.exe -m pip check
.\.venv311\Scripts\python.exe -c "import quantum_space_agi.scientific, quantum_space_agi.simulation; print('imports ok')"
```

Build and import the wheel in that same isolated interpreter after the tests:

```powershell
$wheelOutput = Join-Path $env:TEMP 'arc04-arc05-wheel-py311'
New-Item -ItemType Directory -Force -Path $wheelOutput | Out-Null
.\.venv311\Scripts\python.exe -m pip wheel --no-deps --no-build-isolation --wheel-dir $wheelOutput .
$wheel = Get-ChildItem $wheelOutput -Filter 'quantum_space_agi_reusable_engine-*.whl' | Select-Object -First 1
.\.venv311\Scripts\python.exe -m pip install --no-deps --force-reinstall $wheel.FullName
.\.venv311\Scripts\python.exe -c "import quantum_space_agi.scientific, quantum_space_agi.simulation; print('wheel imports ok')"
.\.venv311\Scripts\python.exe -m pip check
```

These are instructions only; no Python install manager, Python runtime, or
Python 3.11 environment was installed or created during the current
verification. Python 3.11.9 is available from its [official release page](https://www.python.org/downloads/release/python-3119/)
if a historical binary is specifically needed, but it predates subsequent 3.11
security-only updates.

Create the Windows project environment, then install the package and its
runtime dependencies in editable mode:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv\Scripts\python.exe -m pip install -e .
```

For development and notebook execution, install the declared extras:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,notebooks]"
.\.venv\Scripts\python.exe -m ipykernel install --user --name quantum-space-agi --display-name "Python (.venv)"
```

Runtime dependencies are NumPy, Pydantic, and nbformat. Development extras add
pytest, nbclient, and ipykernel; notebook extras add JupyterLab, Matplotlib, and
nbconvert. For WSL, activate the existing project environment and register its
kernel separately from Windows:

```bash
source venv/bin/activate
python -m pip install -e '.[dev,notebooks]'
python -m ipykernel install --user --name quantum-space-agi --display-name 'Python (.venv)'
```

Windows and WSL have separate kernel registries. In VS Code, select
`quantum-space-agi` / `Python (.venv)` for notebooks in the Windows workspace;
in a WSL workspace select that WSL environment's kernel. To verify the selected
interpreter in either UI, run `import sys; print(sys.executable); print(sys.version)`
in a notebook cell before **Run All**. These steps document how to check the UI;
they are not evidence that VS Code UI execution has been performed.

For manual VS Code UI verification, open this repository, open each notebook
under `notebooks/arc04_scientific/` and `notebooks/arc05_simulation/`, select the
intended Python 3.11 environment with **Select Kernel**, and run a temporary
cell containing the `sys.executable` and `sys.version` check above. Confirm it
reports Python 3.11 and `.venv311`, then choose **Run All** and confirm every
cell completes without an error. The temporary check cell and any execution
outputs need not be saved to the canonical notebooks. Record the VS Code and
Jupyter extension versions and the result for each notebook. Do not treat
`nbconvert` execution as VS Code UI verification.

To execute all ARC-04 and ARC-05 notebooks with the registered Windows project
kernel, from the repository root in PowerShell:

```powershell
$notebookOutput = Join-Path $env:TEMP 'arc04-arc05-executed'
New-Item -ItemType Directory -Force -Path $notebookOutput | Out-Null
Get-ChildItem notebooks\arc04_scientific,notebooks\arc05_simulation -Filter *.ipynb -File |
    ForEach-Object {
        .\.venv\Scripts\python.exe -m jupyter nbconvert --to notebook --execute `
            --ExecutePreprocessor.kernel_name=quantum-space-agi `
            --ExecutePreprocessor.timeout=600 --output-dir $notebookOutput $_.FullName
        if ($LASTEXITCODE -ne 0) { throw "Notebook execution failed: $($_.FullName)" }
    }
```

The command writes executed copies under the temporary directory and does not
overwrite the source notebooks.

From the repository root in a WSL shell, activate the WSL project environment
first, then execute with its separately registered kernel:

```bash
set -e
notebook_output="$(mktemp -d)"
for notebook in notebooks/arc04_scientific/*.ipynb notebooks/arc05_simulation/*.ipynb; do
    python -m jupyter nbconvert --to notebook --execute \
        --ExecutePreprocessor.kernel_name=quantum-space-agi \
        --ExecutePreprocessor.timeout=600 --output-dir "$notebook_output" "$notebook"
done
printf 'Executed copies: %s\n' "$notebook_output"
```

This command also writes executed copies outside the repository source tree.

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
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
```

For a concise run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The tests discover notebook and package integration coverage under `tests/`.
Do not treat warnings or missing optional dependencies as evidence of a passing
check unless the pytest result explicitly reports success.

## ARC-04 scientific notebooks

The ARC-04 scientific package is demonstrated by:

1. [00 Package API](notebooks/arc04_scientific/00_package_api.ipynb)
2. [01 Coordinate Frames](notebooks/arc04_scientific/01_coordinate_frames.ipynb)
3. [02 Errors](notebooks/arc04_scientific/02_errors.ipynb)
4. [03 Units](notebooks/arc04_scientific/03_units.ipynb)

## ARC-05 documentation and notebooks

Detailed contracts, equations, assumptions, and limitations are documented in
[docs/arc05_simulation.md](docs/arc05_simulation.md).

The supporting [00 Simulation Package Overview](notebooks/arc05_simulation/00_simulation_package_overview.ipynb)
introduces the package, and [08 Workflow](notebooks/arc05_simulation/08_workflow.ipynb)
demonstrates the end-to-end interface using the public simulation workflow. The
seven canonical scientific notebooks are:

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
