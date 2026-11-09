# ARC-05 Scientific Simulation

## Status and Scope

ARC-05 provides seven canonical scientific notebooks and a tested Python
simulation package for an educational two-body orbital model. It models one
spacecraft in an Earth-centered inertial frame using Newtonian point-mass
gravity and fixed-step classical RK4 propagation.

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

The notebooks remain independently executable in numerical order, and the
package implementation is available under `quantum_space_agi.simulation`.
Package tests compare selected RK4 and propagation behavior against notebook
implementations. The notebooks remain the scientific walkthrough; this package
is the reusable Python interface.

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
requires strictly increasing finite endpoint times, and rejects non-finite
interpolated results. This is an educational estimate, not an exact physical
event time or a state-space interpolation of the orbital solution. The
trajectory's final array state remains the final propagated integration sample;
the interpolated state is reported separately in `collision_state`.

Detection is sample-based: an event between samples is only approximated, and
radial-linear interpolation is not a continuous trajectory root solver. Event
time and state accuracy depend on timestep and trajectory geometry; a crossing
that occurs entirely between samples may not be detected. Collision detection
does not guarantee discovery of every possible boundary crossing.

## Numerical Accuracy and Limitations

The baseline uses float64 fixed-step classical RK4. Accuracy depends on timestep,
duration, state scale, and trajectory geometry. The implementation checks for
invalid types, non-finite values, singular states, derivative-stage shape, and
overflow-like non-finite outputs.

The timestep must advance the float64 simulation clock across the requested
duration. A timestep smaller than the representable spacing at the duration is
rejected instead of entering a time-grid loop that cannot complete. Very large
sample counts can still require substantial computation and memory; there is no
configured sample-count limit or pre-allocation resource estimate. For example,
one day at a 1-microsecond timestep implies about 86.4 billion steps. The final
Float64 time and six-component state arrays alone would require about 4.84
terabytes in decimal units, excluding the Python lists and per-sample objects
used during propagation. Do not start workloads of this scale without an
approved resource policy. No universal runtime or accuracy guarantee is
implied. Highly eccentric trajectories can require substantially finer steps
near periapsis than a circular-orbit case.

The RK4 integrator validates each intermediate state before passing it to the
next derivative evaluation, validates each derivative output, and rejects a
non-finite final state. Gravity and diagnostic calculations similarly check
their derived values and report detected numerical failures as `ValueError`.
Their local NumPy calculations are guarded so caller `ignore`, `warn`, or
`raise` settings do not change these checked failure outcomes; underflow may
still round a negligible float64 contribution to zero. A caller-supplied
derivative's own NumPy operations retain their caller-selected warning and
exception behavior. Workflow diagnostics run after propagation: if diagnostics
fail, `run_simulation` raises and returns no partial result.

## ARC-05 Resource-Safety Policy Proposal (Decision Required)

This section is an analysis proposal only. It does not impose a sample limit,
memory budget, warning, or runtime behavior change.

### Current implementation and estimate

`SimulationConfig` has finite positive duration and timestep but no resource
limit. For a collision-free run, the nominal sample count is
`N = ceil(duration_s / timestep_s) + 1`; an early detected collision can reduce
it. The six-component state dimension is fixed by the current contract and is
not configurable.

Propagation appends each time and a copied six-value state to Python lists,
then builds `times_s` and `states` NumPy arrays. It does not estimate `N` or
allocation size before entering the step loop. Its existing float64
representability/progress guards catch a timestep that cannot advance the
clock, not an impractically large but advancing grid. Diagnostics run after
propagation and retain seven float64 arrays of length `N`: energy, angular
momentum magnitude, eccentricity magnitude, radius, speed, energy drift, and
angular-momentum drift.

For float64, the retained trajectory arrays require:

```text
trajectory_bytes = N * (1 + 6) * 8 = 56N
diagnostic_result_bytes = N * 7 * 8 = 56N
retained_result_bytes = 112N
```

The estimate excludes scalar metadata and any collision-state vector. It
assumes a full collision-free trajectory; an early collision may shorten it.
During propagation, list entries add substantial transient storage. For an
illustrative CPython/NumPy estimate, assume an 8-byte list pointer, a 24-byte
Python float, and a 112-byte one-dimensional ndarray object header (in addition
to its 48-byte six-float payload). That gives about `32N` bytes for the time
list and `168N` bytes for the state list. While constructing the final state
matrix, `vstack` and the subsequent `astype(float64)` copy can temporarily hold
two more `48N` state payloads; the time array adds `8N`. A rough propagation
peak is therefore about `304N` bytes before list over-allocation, allocator
fragmentation, object/runtime overhead, or implementation-specific temporary
allocations.

Diagnostics add temporary Python lists and conversion arrays while creating
each invariant series, plus NumPy temporaries for vectorized radius/speed
calculations. A rough lower-order allowance during this phase is `40N` bytes
for one temporary scalar list plus its float64 array, on top of the `112N`
retained arrays; vectorization and allocator behavior can increase peak use.
These are transparent planning estimates, not memory guarantees. Python
object sizes, list capacity, NumPy headers/temporaries, platform word size,
allocator behavior, and whether an early collision occurs are implementation
and platform dependent. They must not be used as an exact admission check.

| Duration | Timestep | Nominal samples | Trajectory arrays `56N` | Retained with diagnostics `112N` |
|---|---:|---:|---:|---:|
| 1 day | 1 s | 86,401 | 4.84 MB | 9.68 MB |
| 1 day | 1 ms | 86,400,001 | 4.84 GB | 9.68 GB |
| 1 day | 1 μs | 86,400,000,001 | 4.84 TB | 9.68 TB |

Units in the table are decimal (1 MB = 10^6 bytes, 1 GB = 10^9 bytes, 1 TB =
10^12 bytes). For the 1 μs case, the rough `304N` propagation peak is about
26.3 TB before additional overhead. No such workload was executed.

The public `propagate_two_body` API does not expose a caller-supplied budget;
`run_simulation` invokes it and then diagnostics. Neither layer rejects a
workload based on estimated samples or memory before allocation/iteration.
There is no configured maximum sample count and no preflight warning.

### Policy options (not selected)

| Option | Compatibility and usability | Safety and testability | Ownership implications |
|---|---|---|---|
| Maximum sample-count limit | Simple but rejects long/fine simulations regardless of actual memory; a universal threshold may break existing valid callers. | Predictable upper bound on iterations; easy to test at limit and limit + 1, but does not directly bound bytes if state/results grow. | Requires Yousuf's approval of a global scientific/API policy and integration-owner review of affected workloads. |
| Estimated-memory budget | More directly related to resource risk, but estimates vary by Python/NumPy version and transient allocations; may surprise callers near budget. | Can reject before propagation if conservative estimate and collision-independent upper bound are defined; requires tests around arithmetic and estimate margin. | Requires agreement on budget source, margin, and how platform variation is handled. |
| Configurable limit in `SimulationConfig` | Explicit per-run control, but changes the public schema and serialized/config contracts; strict validation means downstream config producers must adapt. | Enables caller-specific tests and limits, but a missing/default value can still leave unsafe behavior. | Requires Yousuf's API/schema approval and approval from every configuration/integration owner. |
| Warning-only preflight | Least disruptive to successful calls; warnings may be ignored or unavailable to UI/service callers. | Can signal large estimates but does not prevent memory exhaustion; warnings are testable but platform/resource-context dependent. | Requires agreement on warning channel, threshold/budget policy, and whether library warnings are acceptable to callers. |
| Hard rejection before propagation | Stronger protection, but changes which inputs succeed and exposes a new failure point; can use existing `ValueError` unless owners approve otherwise. | Directly testable and protects against known unsafe estimates; requires bounded, conservative estimate and no reliance on a collision happening early. | Requires Yousuf and integration owners to approve default threshold and compatibility impact. |
| Caller-controlled limits with no universal default | Avoids an unapproved global cap; adds a call-level API or wrapper contract if the engine itself is to enforce it. | Lets resource-aware callers reject before invocation, but offers no protection when callers omit the check; tests belong at the caller boundary. | Requires caller/integration owners to define the contract; changing ARC-05 public APIs still requires Yousuf's approval. |

### Decisions and approval requested

No policy is selected here. Yousuf, as architecture owner, should first decide
whether ARC-05 needs an engine-enforced guard or whether resource admission
belongs to callers. If an engine guard is desired, approve its semantics:
sample count versus estimated bytes, default behavior, failure type/message,
and whether any public configuration/API field is allowed. Relevant ARC-06,
ARC-10, and other integration owners should then confirm that the policy fits
their expected workloads and error handling. Until those decisions are made,
ARC-05 should retain the current behavior and document that large grids are
unbounded.

Notebook 04 provides an analytic exponential reference for RK4 convergence.
Notebook 07 provides circular and elliptical orbital references. Package
integration tests independently solve Kepler's equation for elliptical
reference states and compare position, velocity, energy, angular momentum, and
eccentricity against propagation.

In the package tests, a planar ellipse with semi-major axis 10,000 km and
eccentricity 0.25 at 128 steps/orbit had a measured one-period maximum sampled
error of about 50.18 m and 0.04814 m/s. A 3D rotation using ascending node 40°,
inclination 55°, and periapsis argument 30° produced equivalent measured
one-period errors. For the same rotated ellipse over 10 periods at 128
steps/orbit, measured maxima were 1,851.27 m and 1.6806 m/s; relative energy and
angular-momentum drift were 2.64e-6 and 7.95e-7. Over 50 periods at that
resolution, maxima were 39,907.60 m and 35.0513 m/s, with relative energy and
angular-momentum drift of 1.27e-5 and 3.98e-6. Refining the 50-period run from
64 to 128 steps/orbit reduced each tested state and invariant error. These
results are evidence only for the stated model, initial conditions, and
resolutions; they are not universal accuracy or stability guarantees.

The collision tests include an independently calculated radial fall from rest
and check that event-time error decreases with timestep refinement. The
simulation's collision detector remains sample-based; the radial interpolation
is not a continuous root solver.

The provided tolerances are local to those experiments; they are not universal
aerospace tolerances. Tests use fixed input values and do not claim certified
mission accuracy.

## Automated Tests

The active dependency and Python-version manifest is `pyproject.toml`. It
declares Python `>=3.11`, runtime constraints for NumPy, Pydantic, and nbformat,
and optional development and notebook dependencies. These declarations do not
prove compatibility for every matching interpreter and package version.

In the current worktree, `python -m pytest tests/simulation -q` and
`python -m pytest -q` each passed all 270 tests on Python 3.14.1. Pytest reported
one third-party AnyIO deprecation warning. No dependency was installed or
changed for these runs.

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
assumed. The notebooks and Python package use NumPy float64 and explicit
validation patterns; they do not import or claim integration with the separate
ARC-04 workstream.

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
- final architecture approval for package location and public import names;
- whether the canonical notebooks and Python package remain parallel reference
  implementations or are consolidated later;
- mission resource constraints and non-two-body model requirements.

## Package Integration Interface

The importable API is provided under
`quantum_space_agi.simulation` and is an implementation-facing mirror of the
validated notebook contracts:

```python
from quantum_space_agi.simulation import (
    OrbitalState,
    SimulationConfig,
    run_simulation,
)
```

The workflow contract is:

```python
config = SimulationConfig(
    initial_position_m=(7_000_000.0, 0.0, 0.0),
    initial_velocity_mps=(0.0, 7_500.0, 0.0),
    simulation_duration_s=600.0,
    time_step_s=10.0,
    collision_radius_m=6_378_137.0,
)
result = run_simulation(config)
```

The result is deterministic for identical inputs and immutable configuration.
It contains:

- `times_s`: Float64 sample times in seconds.
- `states`: Float64 shape `(N, 6)` states ordered as
  `[x, y, z, vx, vy, vz]` in metres and metres per second.
- `collision_*`: initial or sampled collision information; `None` means no
  detected collision before trajectory termination.
- `diagnostics`: trajectory-level invariants and drift arrays.
- `model`: explicit frame, integrator, model, and unit metadata.

`run_simulation` terminates normally at the configured duration or at the first
collision sample. It raises `ValueError` for invalid scalar, state, derivative,
or numerical output conditions. Numerical failure, collision detection, and
normal propagation completion are distinct outcomes and must not be inferred
from one another.

The package implementation does not add drag, J2, thrust, third-body gravity,
adaptive stepping, attitude dynamics, or collision response. Any future model
extension requires a separate model identifier, equation documentation, and
scientific tests.
