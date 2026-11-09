# Final Benchmark Summary (Nov 13)

## Scope

This document summarizes challenge-independent synthetic examples for the ARC-06/ARC-07 optimization work. These are internal engineering experiments, not official NASA requirements, mission analysis, scientific findings, or production solver claims. The examples do not establish quantum advantage.

## Three different evaluation methods

1. **Exact classical decision enumeration:** `EnumerativeSolver` visits every assignment in the original finite domains and checks the original constraints. Each three-bit case has 8 candidates. The deterministic scaling fixtures use 3, 6, 9, and 12 binary variables, so candidate counts grow as `2^n`: 8, 64, 512, and 4,096. The benchmark helper repeats solves 5 times and reports each `time.perf_counter()` sample plus mean, median, and minimum. These small sizes demonstrate search-space growth and correctness, not a performance advantage.
2. **Exact classical enumeration of a QUBO encoding:** ordinary Python enumerates all encoded bitstrings, including slack bits. This is also classical exhaustive search, not a quantum method. For each three-variable fixture the encoded model has 8 bits and 256 bitstrings. The minimum is decoded and checked against the original constraints, and compared with `EnumerativeSolver`.
3. **Qiskit QAOA circuit simulation:** `StatevectorSampler` locally simulates an ideal full statevector circuit, then samples a finite number of shots. It does not model device noise or run on a QPU. The `p=1` circuit prepares `|+>`, applies one QUBO cost layer and one transverse-field mixer, then measures. A classical grid search selects the parameter pair by sampled mean energy. This is a simulator experiment, not evidence of hardware performance.

## Inputs and QUBO assumptions

The same synthetic fixtures maximize `6*alpha + 4*beta + 3*gamma` over binary decision variables. The cases are:

| Case | Constraints |
| --- | --- |
| `feasible` | budget `<= 5`, capacity `<= 3` |
| `resource_constrained` | budget `<= 4`, capacity `<= 2` |
| `infeasible` | budget `<= 4`, capacity `<= 3`, selected count `>= 3` |

The QUBO adapter accepts the explicit integer-linear model used by these examples; it does not recover algebra from arbitrary objective/constraint callables. Assumptions are binary decisions, integer objective coefficients, integer linear constraint coefficients/bounds, and zero tolerance. `<=` and `>=` constraints use binary-encoded integer slack; equality constraints use a squared residual without slack. These assumptions do not cover continuous or nonlinear constraints, fractional values, or nonzero tolerances.

For objective coefficients `(6,4,3)`, the full binary objective range is `R = Σ|c_i| = 13`. Integer residuals have a minimum nonzero magnitude of 1, so the chosen penalty is `λ = R + 1 = 14`. Under these assumptions, any violated constraint adds at least 14, more than the maximum objective-range improvement of 13. This is a bounded-example argument, not a universal penalty prescription. An infeasible original problem remains infeasible when decoded; its objective is reported as `null`.

## Qiskit configuration and observed results

Environment used: WSL, Python `3.14.4`, Qiskit `2.6.1`. Qiskit is optional (`qiskit-experiment` extra in `pyproject.toml`); the base package dependency list remains empty. The run used seed `20261112`, a `7 × 7` grid with `γ = 2πk/7` and `β = πk/7` for `k=0..6`, and 512 shots per parameter pair (25,088 shots per case). QUBO coefficients were converted with `x_i=(1-Z_i)/2`; the nonconstant Ising coefficients were scaled by their maximum absolute value for the phase angles. The selected sample is the lowest-energy observed bitstring from the parameter pair with the lowest sampled mean QUBO energy.

| Case | QAOA simulator sample | Exact QUBO enumeration | `EnumerativeSolver` | One-run simulator time |
| --- | --- | --- | --- | ---: |
| `feasible` | bitstring `11000000`, feasible, objective `10.0`, energy `-10.0`; selected `γ=3.5904`, `β=1.3464` | minimum `-10.0`, 256 bitstrings | optimal, objective `10.0`, 8 candidates | `0.493 s` |
| `resource_constrained` | bitstring `01100000`, feasible, objective `7.0`, energy `-7.0`; selected `γ=0.8976`, `β=2.6928` | minimum `-7.0`, 256 bitstrings | optimal, objective `7.0`, 8 candidates | `0.470 s` |
| `infeasible` | bitstring `01100010`, infeasible (`minimum_selected` violation `1.0`), objective `null`, energy `7.0`; selected `γ=0.8976`, `β=2.6928` | minimum `7.0`, 256 bitstrings | infeasible, no solution/objective, 8 candidates | `0.505 s` |

The listed runtime is one observed wall-clock measurement per simulator case; it includes circuit construction, statevector simulation, shot sampling, and result collection over the full parameter grid. It excludes model construction and both exact classical references. It is not a repeated runtime comparison and must not be compared as a speed claim against the tiny exhaustive cases. The QAOA results matched the exact assignment in the two feasible fixtures in this run. In the infeasible fixture, both exact references and the sampled decoded assignment are infeasible.

## Reproduction

Install the optional extra in a virtual environment, then from the repository root run:

```bash
python3 -m pip install -e '.[qiskit-experiment]'
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 examples/synthetic_optimization.py
PYTHONPATH=src python3 examples/qiskit_qaoa_experiment.py
```

Detailed classical benchmark methodology, mathematical encoding assumptions, and simulator configuration are in [classical-optimization-practice.md](classical-optimization-practice.md), [qubo-experiment.md](qubo-experiment.md), and [qiskit-experiment.md](qiskit-experiment.md).
