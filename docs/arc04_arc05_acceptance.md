# ARC-04 / ARC-05 Acceptance Record

**Verification date:** 2026-11-14
**Checkout:** branch `arc/05-simulation`, HEAD `a7a440972a3dd469c0e954be78ce4474586cdaa5`
**Acceptance recommendation:** **CONDITIONAL — neither ARC is declared complete.**

This record separates verified results from checks unavailable in the current
environment and proposed work that requires an owner decision.

## Acceptance summary

| Area | Status | Evidence or remaining work |
|---|---|---|
| ARC-04 scientific utilities | Conditional | 12 scientific tests passed; coordinate frames, proper rotations, unit dimensions/scales, validation, and transform round trips are covered. Python 3.11 execution is unavailable. |
| ARC-05 simulation | Conditional | 291 simulation tests passed; circular and Kepler-ellipse references, rotated 3D cases, convergence, long-run drift, collision interpolation, invalid inputs, and workflow behavior are covered. Resource admission remains unbounded pending policy approval. |
| Full test suite | Verified on available interpreter | 303 passed, 0 failed, 0 skipped on CPython 3.14.1. |
| Jupyter notebooks | Verified by kernel execution | All 13 notebooks passed nbformat validation and `nbconvert` execution on CPython 3.14.1. Executed copies were written to the system temp directory. |
| VS Code interactive UI | Unverified | VS Code and Python/Jupyter extensions are installed and VS Code processes exist, but this agent session has no UI-control runtime. `nbconvert` is not UI verification. Follow the manual steps below. |
| Python 3.11 | Unverified; interpreter unavailable | `py -0p` lists only CPython 3.14.1. No Python runtime, install manager, or Python 3.11 environment was installed. |
| Package and dependencies | Verified on CPython 3.14.1 | Public imports, wheel imports, and `pip check` passed. The wheel contains 12 package files and declares Python `>=3.11`, NumPy `>=2.0,<3.0`, Pydantic `>=2.0,<3.0`, and nbformat `>=5.10,<6.0`. |
| Wheel build | Verified | `pip wheel --no-deps --no-build-isolation --wheel-dir $env:TEMP .` produced `quantum_space_agi_reusable_engine-0.1.0-py3-none-any.whl`. |
| Diff hygiene | Verified | `git diff --check` passed. No commit, push, reset, clean, or deletion was performed. |

## Python 3.11 procedure and result

The host's legacy `py -0p` launcher reports only:

```text
Python 3.14 interpreter (Windows installation)
```

The latest Python 3.11 security updates are source-only; the last traditional
Windows binary installer was Python 3.11.9. To verify the current security
runtime, first obtain authorization to install the Python install manager,
which changes the current user's Python tooling. Install it from the official
[Python downloads page](https://www.python.org/downloads/windows/) or Microsoft
Store, then use `pymanager install 3.11` to install the current 3.11 runtime.
The `pymanager` command avoids ambiguity with the legacy `py.exe` launcher.
Do not enable PATH changes unless wanted. Then follow the isolated `.venv311` test and
wheel commands in the [README](../README.md#isolated-python-311-verification).
No such installation was attempted in this run.

## Notebook verification

Notebook JSON validity and Jupyter-kernel execution both passed for the four
ARC-04 notebooks and nine ARC-05 notebooks. Jupyter emitted a Windows Proactor
event-loop warning and used a selector thread for ZeroMQ; there were no cell
execution errors. Pytest notebook tests use Python `exec` and are not kernel or
UI tests.

VS Code UI verification remains unperformed. The VS Code CLI extension probe
listed the Python and Jupyter extensions, but VS Code reported that it could
not create a log directory. No editor interaction was performed. Manual
verification:

1. Open the repository folder in VS Code and open each `.ipynb` under
   `notebooks/arc04_scientific/` and `notebooks/arc05_simulation/`.
2. Use **Select Kernel** to select the authorized `.venv311` Python 3.11
   interpreter.
3. Run a temporary cell containing `import sys; print(sys.executable);
   print(sys.version)` and verify both the interpreter path and Python 3.11.
4. Choose **Run All** and confirm every cell completes without an error.
5. Record VS Code/Jupyter extension versions and the result for each notebook.
   Do not save temporary verification cells or execution outputs over the
   canonical notebooks unless their source is intentionally being updated.

## ARC-05 resource policy

The current API accepts finite positive duration and timestep but has no
sample-count cap, preflight estimate, or memory budget. Propagation accumulates
Python lists before building NumPy arrays; diagnostics retain additional
per-sample arrays. Large but advancing time grids can therefore consume
substantial resources. Existing numerical progress checks do not bound work.

The proposed opt-in `max_samples` guard is documented in
[arc05_resource_policy_proposal.md](arc05_resource_policy_proposal.md). It
preserves existing calls with a `None` default, adds no arbitrary default cap,
and defines tests for preflight, boundary counts, legacy calls, workflow
propagation, collision behavior, and invalid limits. The proposal notes that a
sample count is not a hard byte-level memory guarantee. No policy, API change,
runtime guard, or policy-specific test has been implemented; owner approval is
required.

## Scientific and integration evidence

ARC-05 declares an Earth point-mass two-body model in SI units, ECI state order
`[x, y, z, vx, vy, vz]`, Float64, and fixed-step RK4. Tests compare circular
and elliptical propagation with analytical or independent Kepler references,
measure timestep convergence and invariant drift, exercise rotated 3D orbits,
and validate collision estimates against an independent radial-fall reference.
These tests support the stated model and tested input ranges; they are not
mission certification or universal accuracy guarantees.

ARC-04 and ARC-05 public imports work together in the installed package. The
architecture intentionally keeps ARC-05 ECI/orbital conventions independent
of ARC-04's general Cartesian frame utilities; no unapproved cross-ARC frame
conversion dependency is claimed. `run_simulation` completed a smoke workflow
with 11 time samples and a `(11, 6)` state array through the configured 20 s
final time.

## Dated verification history

- **2026-11-14, Windows CPython 3.14.1:** 303 tests passed (12 ARC-04 and 291
  ARC-05). Jupyter kernel execution passed for all 13 notebooks. Dependency
  checks, public imports, wheel imports, and wheel build passed.
- **Earlier WSL CPython 3.12.3 report:** 284 tests passed; the date was not
  recorded. This predates current notebook and regression-test changes and is
  retained as historical evidence only, not as current acceptance evidence.
- **Python 3.11:** not run; runtime unavailable and installation was not
  authorized/performed.
- **VS Code UI:** not run; interactive UI control was unavailable in this
  session.

The current pytest run reported an AnyIO deprecation warning and a pytest cache
write warning. Neither affected the 303 passing tests. The notebook run emitted
the Windows Proactor/ZeroMQ compatibility warning noted above.

## Submission manifest

Candidate ARC-04/ARC-05 files present as changes in this checkout:

- `README.md`, `pyproject.toml`, `docs/arc05_simulation.md`;
- `docs/arc04_arc05_acceptance.md` and
  `docs/arc05_resource_policy_proposal.md`;
- all notebooks under `notebooks/arc04_scientific/` and
  `notebooks/arc05_simulation/`;
- `src/quantum_space_agi/scientific/coordinate_frames.py`,
  `src/quantum_space_agi/scientific/units.py`, and
  `src/quantum_space_agi/simulation/propagation.py`;
- `tests/scientific/test_arc04_validation.py`,
  `tests/simulation/test_arc05_integration.py`, and
  `tests/simulation/test_arc05_notebooks.py`.

Other pre-existing untracked ARC-08/planning documents remain outside this
ARC-04/ARC-05 manifest. The local untracked `venv/` and CLI-generated
`debug.log` are environment/diagnostic artifacts and are excluded from formal
submission. They were left untouched under the no-delete instruction. No
files were staged or committed.

## Recommendation and blockers

**Recommendation: conditional submission readiness; do not mark ARC-04 or
ARC-05 complete yet.** The applicable tests and packaging checks pass on
CPython 3.14.1. Before formal acceptance, run the suite and wheel import under
Python 3.11 after authorization, complete the manual VS Code UI notebook run,
and obtain the owner decision on the ARC-05 resource-policy proposal or
explicitly accept the documented unbounded behavior for this submission.
