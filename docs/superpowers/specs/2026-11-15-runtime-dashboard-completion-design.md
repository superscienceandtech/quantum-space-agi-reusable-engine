# Runtime and Dashboard Completion Design

## Goal

Make the `develop` worktree's local mission application install and start
without a manually supplied `PYTHONPATH`, and turn the existing four proposed
mission views into useful views of actual local API results.

The application remains an educational prototype. Reuse the current ARC-05
simulator, ARC-08 evaluator, mission API, and ARC-09 visual shell. Do not invent
physical spacecraft values, mission eligibility, NASA data, or capabilities
the API does not provide.

## Python package and runtime

- Keep the existing `src/quantum_space_agi` package and setuptools build
  backend. Make discovery explicit for `quantum_space_agi*` under `src`, with
  namespace-package discovery disabled so only actual package directories are
  included.
- Document one virtual environment per checkout/worktree and install the
  editable project with that environment's Python (`python -m pip install -e
  ".[api]"`). This avoids a stale editable mapping from a neighboring checkout
  or a `pip`/`python` interpreter mismatch.
- Verify the imported package file resolves inside the current worktree, then
  run the server with the documented module command and without setting
  `PYTHONPATH`.
- Preserve all existing `quantum_space_agi` subpackages and optional dependency
  groups. Do not rename the distribution or add a runtime bootstrap that
  manipulates `sys.path`.

## Dashboard state and views

- Move the existing live mission form from the overview page into Mission
  Builder. Keep validation, loading, error, and successful-run messages
  visible there. Keep overview widgets only as explicitly labeled synthetic
  samples.
- Keep the latest successful `/api/v1/missions/run` response in browser memory
  and share it with the other views. Do not persist it across reloads. Starting
  another run or encountering an error clears the prior result so a stale run
  cannot be mistaken for the current one. Until a successful run exists, each
  data-dependent page shows a clear empty state.
- Spacecraft Configuration shows only the returned spacecraft profile ID and
  selected payload IDs. Label mass, dimensions, propulsion, fuel, capacity,
  power, and other physical vehicle properties unavailable.
- Resource Dashboard renders the actual ARC-08 evaluator version, scenario,
  abstract-unit totals, violations, and warning. Mark policy approval pending;
  describe feasibility only as the result of that educational scenario.
- Simulation & Results renders actual ARC-05 model metadata, trajectory
  projection and tabular states, and returned diagnostics with their declared
  units and limitations.
- Mission Comparison & Report renders a report for the latest actual run. The
  API has no history or comparison endpoint, so cross-mission comparison is
  explicitly labeled unavailable rather than simulated from sample data.
- Retain the existing visual system and accessible navigation. Do not change
  unrelated ARC-09 illustrative charts or archived materials.

## Data flow and errors

1. Mission Builder loads supported destinations from the existing API.
2. The user selects a destination and at least one supported payload.
3. The client validates, then runs the existing mission endpoint.
4. On success, the unmodified API response becomes the in-memory latest run
   and all views render their relevant fields from it.
5. On loading, empty, or error state, all result views update consistently;
   errors remain visible in Mission Builder and no sample values are used as
   live output.

No API endpoints or DTOs are added. If a desired value is absent from the API
response, render an explicit unavailable label rather than estimating it.

## Verification

- In a clean worktree-local virtual environment, install the project editable,
  assert `quantum_space_agi.__file__` is under that worktree, and start the
  server using the documented module command without `PYTHONPATH`.
- Test the dashboard's page structure, data labels, empty/loading/error
  transitions, and rendering from actual response-shaped data.
- Run mission/API regression tests and the non-notebook pytest suite.
- Perform a browser smoke test: configure a destination, select a payload, run
  the mission, and verify trajectory and ARC-08 data appear in their views;
  also verify loading and API failure states.

## Acceptance criteria

1. Editable installation and normal server startup resolve
   `quantum_space_agi` from the current `develop` worktree, without manual
   `PYTHONPATH`.
2. The four mission views consume only the latest actual local API response or
   show an explicit empty/unavailable state.
3. Physical spacecraft properties and cross-mission comparison are not
   fabricated.
4. Existing ARC packages, visual design, and team contributions remain intact.
5. Automated and browser verification results are reported accurately. No
   push or force-push is performed.
