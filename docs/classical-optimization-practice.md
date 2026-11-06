# Classical Optimization Practice (Nov 5–6)

## Purpose and scope

These examples exercise the generic `Objective`, `Constraint`, `OptimizationProblem`, and `Solver` contracts using the existing `EnumerativeSolver` as a transparent reference baseline. They are tiny synthetic option-selection fixtures, not mission requirements, scientific models, or challenge-specific solutions. No QUBO/QAOA, external solver, or quantum comparison is included.

## Deterministic input

All three cases use the same three binary variables and objective:

| Variable | Objective value | Budget use | Capacity use |
| --- | ---: | ---: | ---: |
| `alpha` | 6 | 3 | 2 |
| `beta` | 4 | 2 | 1 |
| `gamma` | 3 | 2 | 1 |

Each variable domain is `(0, 1)`. The objective is to maximize `6*alpha + 4*beta + 3*gamma`. Cases alter only their constraints:

- `feasible`: budget `<= 5`, capacity `<= 3`.
- `resource_constrained`: budget `<= 4`, capacity `<= 2`.
- `infeasible`: budget `<= 4`, capacity `<= 3`, and selected count `>= 3`.

The infeasible solver result intentionally has no chosen solution and therefore no `constraint_checks`. The JSON includes a separately labelled all-selected diagnostic witness so the resource violations are visible; those checks are not presented as solver output.

## Solver and benchmark configuration

- Solver: `EnumerativeSolver`; comparison tolerance comes from the problem (default `1e-12`).
- Enumeration order: variable names sorted lexically, then values in declared order.
- Repetitions: 5 per case in the example.
- Random seed: not applicable; no randomness is used.
- Timing: `time.perf_counter()` around each `solver.solve(problem)` call.
- Aggregation: every sample plus arithmetic mean, median, and minimum. Median is computed from `BenchmarkReport.elapsed_seconds` in the example; the public benchmark helper contract is unchanged.
- Output: JSON with sorted keys, input/configuration, status, objective, constraint diagnostics, candidate counts, objective-call counts, and timings.

The candidate count is eight per solve because there are three binary variables. Objective evaluation count is separately instrumented in the example and can be lower when constraints reject candidates. Runtime for these tiny problems is only recorded for repeatability; it is not meaningful evidence of a performance advantage.

## Scaling evaluation

In addition to the three correctness scenarios, the script runs a deterministic scaling series with 3, 6, 9, and 12 binary variables. Each size uses generated objective/resource coefficients, one resource-capacity constraint, and the same exhaustive solver. Expected candidate counts are `8`, `64`, `512`, and `4096` per solve (`2^n`). Objective evaluations are counted separately because infeasible candidates are rejected before the objective runs. The series shows search-space growth; it does not compare algorithms or establish a runtime advantage.

## Run

From the repository root:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 examples/synthetic_optimization.py
```
