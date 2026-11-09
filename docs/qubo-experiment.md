# QUBO Encoding Experiment (Nov 9–10)

## Scope

The ARC-07 experiment converts the three tiny synthetic binary cases into QUBO energy functions. It then enumerates every encoded bitstring with ordinary Python and compares the minimum-energy decoded assignment with the exact `EnumerativeSolver` result. This is classical exhaustive enumeration over a QUBO encoding: no Qiskit, quantum simulator, or hardware is used, and no quantum advantage is claimed. Qiskit remains a separate Nov 11–12 experiment.

The generic `OptimizationProblem` holds Python callables, so their algebra cannot be recovered automatically. `LinearConstraintSpec` supplies explicit coefficients for this small adapter. The example uses the same coefficient maps to build the callables and the QUBO specs, so both solvers receive the same synthetic objective and constraints.

## Mathematical encoding

Assume decision bits `x_i ∈ {0,1}`, an integer linear objective `f(x) = Σ c_i x_i`, and linear constraints with integer coefficients, integer bounds, and zero tolerance. The selected examples satisfy these assumptions. Continuous variables, nonlinear/black-box expressions, fractional coefficients or bounds, and nonzero tolerances are not encoded.

For minimization, the objective energy is `f(x)`. For maximization it is `-f(x)`, since QUBO energy is minimized. Additive constants may be omitted because they do not change the minimizing assignment.

For `Σ a_i x_i ≤ b`, add nonnegative binary-encoded slack `s = Σ 2^k s_k` and penalize:

`P(x,s) = (Σ a_i x_i + s - b)^2`.

For `Σ a_i x_i ≥ b`, use:

`P(x,s) = (Σ a_i x_i - s - b)^2`.

Equality constraints use `(Σ a_i x_i - b)^2` with no slack. For a `≤` constraint, the maximum needed slack is `b - Σ min(0,a_i)`; for `≥`, it is `Σ max(0,a_i) - b`. When that bound is positive, `bit_length(max_slack)` bits represent every integer slack from zero through that maximum. A feasible binary assignment therefore has an exact zero-residual slack representation. A violation cannot be cancelled by nonnegative slack in the relevant direction.

The full energy is:

`E(x,s) = objective_energy(x) + λ Σ_j P_j(x,s)`.

Expanding each square gives a quadratic polynomial. Because bits obey `z² = z`, all diagonal-square terms reduce to linear QUBO terms; cross terms use coefficient `2 a_i a_j`.

### Penalty choice

For the example objective coefficients `(6,4,3)`, its entire binary objective range is `R = Σ|c_i| = 13`. Every constraint residual is integer-valued, so a violated equality penalty has residual magnitude at least one and costs at least `λ`. Choosing `λ = R + 1 = 14` makes one violated constraint cost more than the maximum possible objective improvement across any two assignments. Thus, when at least one feasible assignment exists, a minimum-energy state must decode to a feasible objective optimum. This guarantee depends on the stated integer and exact-tolerance assumptions; it is not a universal penalty rule for arbitrary real-valued models.

For an infeasible input, no penalty can create a genuinely feasible decision assignment. The experiment reports the exact baseline as `infeasible`, checks the decoded bitstring against the original constraints, and marks it infeasible if any constraint fails. It never reports its decoded objective as a feasible solution.

## Reported experiments

For each of the existing `feasible`, `resource_constrained`, and `infeasible` inputs, the JSON output records:

- QUBO variable order, minimum-energy bitstring, energy, slack values, penalty, and number of bitstrings evaluated.
- Decoded decision bits and feasibility under the original constraint callables.
- Exact baseline status, solution/objective if feasible, and decision-candidate count.
- Whether feasibility agrees and whether the feasible assignment matches exactly.

The number of QUBO bitstrings includes slack bits and can exceed the original decision-candidate count. The example enumerates all QUBO bitstrings deterministically and is intended only for these small cases.

## Heuristic evaluation

The JSON example also runs a classical single-bit Metropolis simulated-annealing
heuristic over each encoded QUBO. It uses 20 fixed seeds, four restarts per seed,
64 sweeps per restart, and a geometric temperature schedule from 10.0 to 0.05.
For each seed it records the best visited QUBO energy, whether the original
decision constraints are satisfied, proposal/acceptance counts, and paired runtime
measurements for the heuristic and exact enumeration.
The aggregate success rate is compared with the exact minimum QUBO energy; the
decoded best state is independently checked against the original model.

This is an ordinary classical heuristic baseline. It is not simulated quantum
annealing, a quantum-inspired algorithm, or evidence of quantum advantage. The
small fixed-seed study is for method comparison and reproducibility only.

A separate research pilot implements a CPU discrete simulated-bifurcation
baseline and a feasibility-guided dSB candidate. Its scope, equations,
comparison procedure, and limitations are documented in
[docs/algorithm-research.md](algorithm-research.md).

## Run

From the repository root:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 examples/synthetic_optimization.py
```
