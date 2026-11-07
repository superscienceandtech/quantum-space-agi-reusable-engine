# ARC-05 Scientific Simulation

## Status and Scope

ARC-05 is a notebook-first educational two-body orbital simulation foundation.
It deliberately models one spacecraft in an Earth-centered inertial frame using
Newtonian point-mass gravity and fixed-step classical RK4 propagation.

The following are outside the baseline:

- attitude and rotational dynamics;
- spacecraft mass and propellant evolution;
- thrust and control laws;
- atmospheric drag, geopotential perturbations, third-body gravity, and solar
  radiation pressure;
- collision response, terrain modeling, atmospheric entry, and descent;
- mission-domain serialization and backend integration.

Those features require separate ARC or shared-domain decisions and are not
invented here.

## Notebook Execution Order

Execute the notebooks in numerical order:

1. `01_simulation_configuration.ipynb`
   - Defines strict configuration validation and SI/ECI conventions.
2. `02_orbital_state.ipynb`
   - Defines the six-component translational state representation.
3. `03_two_body_dynamics.ipynb`
   - Defines the Newtonian Earth point-mass derivative.
4. `04_rk4_integrator.ipynb`
   - Defines generic fixed-step classical fourth-order Runge-Kutta.
5. `05_orbital_propagation.ipynb`
   - Combines the derivative and integrator into trajectory propagation.
6. `06_simulation_diagnostics.ipynb`
   - Reports invariants, drift, eccentricity, radius, and speed.
7. `07_orbital_validation.ipynb`
   - Defines reproducible circular, elliptical, collision, convergence, and
     invalid-input checks.

The notebooks are independently executable today. Later package integration
should preserve this order while replacing only duplicated notebook
implementations with shared approved modules.

## Scientific Assumptions and Equations

The state is ordered as:

```text
[x, y, z, vx, vy, vz]
```

where position is in metres, velocity in metres per second, and time in seconds.
The coordinate frame is Earth-Centered Inertial (ECI). WGS 84 supplies reference
constants for Earth but does not define the inertial coordinate frame.

The governing equations are:

```text
dr/dt = v
dv/dt = -(mu / ||r||^3) r
```

The educational baseline currently uses:

- Earth gravitational parameter: `3.986004418e14 m^3/s^2`;
- spherical reference collision radius: `6378137.0 m`, based on the WGS 84
  semi-major axis.

These values are explicitly represented in the notebooks and must not be
interpreted as mission-specific constants or safety limits.

## Data Contracts

### Simulation Configuration

`SimulationConfig` is a strict, frozen Pydantic model. It accepts SI values and
only:

- ECI as `reference_frame`;
- RK4 as `integrator`;
- positive finite scalar durations, timesteps, gravitational parameter, and
  collision radius;
- finite three-component position and velocity tuples.

Unknown fields and mutation are rejected.

### Orbital State

`OrbitalState` is a strict, frozen Pydantic model containing:

- `position_m`: three-component finite tuple in metres;
- `velocity_mps`: three-component finite tuple in metres/second;
- `time_s`: finite, non-negative seconds.

`to_array()` returns Float64 shape `(6,)`.
`from_array(state_vector, time_s)` accepts only a real numeric one-dimensional
six-component vector and returns the corresponding orbital state.

### Dynamics and Integrator

`two_body_derivative(state, mu)` returns Float64 shape `(6,)`.
`rk4_step(...)` returns one Float64 state of the same shape as its input and
does not mutate the input. All derivative stages and the output must be finite
and correctly shaped.

### Propagation Trajectory

The propagation interface returns:

```text
{
    "times_s": ndarray, shape (N,),
    "states": ndarray, shape (N, 6),
    "collision_index": integer index or None,
    "collision_radius_m": configured finite positive radius,
    "collision_time_s": sampled or interpolated event time, or None,
    "collision_state": Float64 shape (6,), or None,
    "collision_method": exact_sample or linear_radius_interpolation
}
```

The state columns are `[x, y, z, vx, vy, vz]`; time and position units are
seconds and metres. Propagation uses nominal fixed steps, shortening the final
step so the final recorded time equals the configured duration.

## Diagnostics

The diagnostics interface reports arrays for:

- specific orbital energy in `m^2/s^2`;
- specific angular momentum magnitude in `m^2/s`;
- eccentricity magnitude (dimensionless);
- radius in metres;
- speed in metres/second;
- absolute energy and angular-momentum drift from the initial state.

Drift is numerical drift for this integrator and timestep, not evidence that the
underlying exact point-mass model conserves or fails to conserve the quantity.

## Collision Radius Interpretation

The current collision radius is a configurable spherical comparison threshold.
The value in the example is the WGS 84 semi-major axis used as an educational
Earth-scale boundary.

It is not:

- terrain elevation;
- a geoid surface;
- an atmospheric boundary;
- a mission abort limit;
- an impact probability model.

The configured radius is used as supplied. It is reported in propagation results
and is never silently substituted or rescaled.

Collision detection first checks the initial state, then stops at the first
integration sample whose radius is at or below the configured threshold. If the
radius equals the threshold at either end of the detecting segment, that sample
time/state is labeled `exact_sample`. Otherwise, the event time and state are
linearly interpolated by radial position between the surrounding RK4 samples.
The interpolation helper rejects intervals that do not bracket the threshold,
so invalid non-crossing intervals cannot be converted into false collision events.
This is an educational estimate, not an exact physical event time or a
state-space interpolation of the orbital solution. The trajectory's final array
state remains the final propagated integration sample; the interpolated state is
reported separately in `collision_state`.

## Numerical Accuracy and Limitations

The baseline uses float64 fixed-step classical RK4. Accuracy depends on timestep,
duration, state scale, and trajectory geometry. The implementation checks for
invalid types, non-finite values, singular states, derivative-stage shape, and
overflow-like non-finite outputs.

Notebook 04 provides an analytic exponential reference for RK4 convergence.
Notebook 07 provides circular and analytical elliptical references, including
periapsis, apoapsis, semi-major axis, eccentricity, specific orbital energy,
specific angular momentum, Keplerian period, and numerical return-position
checks. It also reports absolute and relative energy/angular-momentum drift over
multiple timesteps and durations. Elliptical and circular values are measured
from the displayed notebook run; they are not universal accuracy guarantees.

The provided tolerances are local to those experiments; they are not universal
aerospace tolerances. Tests use fixed input values and do not claim certified
mission accuracy.

## Automated Tests

No active dependency manifest (`pyproject.toml`, `setup.py`, `setup.cfg`, or
equivalent) was found at the repository root during implementation. Therefore,
Python and package constraints must not be inferred or finalized from stale
egg-info metadata. This documentation reports verified runtime compatibility
only; project-wide dependency requirements need team-owner approval.

The verified target environment for the final run was Python 3.12.3. Python
3.14 is not established as the project target by this repository evidence.
No dependency was installed or changed by the ARC-05 work.

Run the ARC-05 tests:

```powershell
python -m pytest tests/simulation/test_arc05_notebooks.py -v
```

Run the complete available suite:

```powershell
python -m pytest -v
```

Tests execute each notebook independently, compile notebook code in order within
that notebook, and therefore do not rely on notebook execution-order state.
The notebook execution outputs and displayed checks remain reproducible
evidence; pytest is the automated interface-level regression suite.

## Integration Readiness

### ARC-04 Scientific Computing

ARC-05 should reuse only approved shared scientific APIs after their public
contracts are confirmed. No dependency on unconfirmed ARC-04 modules is
assumed. The notebook-first implementations use NumPy float64 and explicit
validation patterns to remain compatible with scientific precision, units,
vector, and matrix conventions owned by ARC-04.

Shared units, quantities, tolerances, and constants must continue to be owned
by the appropriate shared layer rather than duplicated independently.

### ARC-06 Mission Experience

ARC-06 should consume immutable configuration and trajectory data rather than
reimplementing propagation logic. Mission configuration, scenario selection,
resource constraints, visualization, and UI behavior remain ARC-06
responsibilities. The final serialized data shape requires approval before it
becomes a shared API.

### ARC-10 Backend and Deployment

ARC-10 should expose a stable, team-approved service contract and operate with
reproducible inputs and outputs. It must not reinterpret or silently change
units, frame, collision threshold, physical constants, tolerance policy, or
trajectory ordering.

### Team Decisions Remaining

The following shared decisions require technical-lead or domain-owner approval:

- authoritative final Earth constant and collision-radius source values;
- shared configuration and trajectory serialization contracts;
- package-location and public import names for reusable Python modules;
- integration ownership for notebook conversion versus package extraction;
- mission resource constraints and non-two-body model requirements.
