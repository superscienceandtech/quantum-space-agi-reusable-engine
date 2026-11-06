# Qiskit Simulator Experiment (Nov 11–12)

## Scope and setup

This is a local, ideal statevector simulation using Qiskit's `StatevectorSampler`. It does not access a QPU, model hardware noise, or establish quantum advantage. The public optimization solver/benchmark interfaces are unchanged. Qiskit is an optional extra so the generic classical package remains dependency-free:

```bash
python3 -m pip install -e '.[qiskit-experiment]'
PYTHONPATH=src python3 examples/qiskit_qaoa_experiment.py
```

The experiment runs the same three small synthetic QUBO cases already used by the classical QUBO example. The first two have feasible assignments; the third has contradictory resource/minimum-selection requirements. Every sampled assignment is checked against the original `OptimizationProblem` constraints. An infeasible exact input is never described as feasible, and its feasible objective is `null`.

## Circuit and search configuration

Each QUBO variable, including integer-slack bits, maps to one qubit. The QUBO polynomial is converted using `x_i = (1 - Z_i)/2` into `H = constant + Σ h_i Z_i + Σ J_ij Z_i Z_j`. The circuit prepares `|+>` on all qubits, applies one cost unitary `exp(-i γ (H - constant)/s)`, applies `Rx(2β)` to every qubit, and measures all qubits. The scale `s` is the maximum absolute nonconstant Ising coefficient; it only rescales the phase angles.

Qiskit count strings are reversed into the QUBO model's stable variable order before energy calculation and decoding. The parameter search is a deterministic `7 × 7` grid: `γ ∈ {2πk/7}` and `β ∈ {πk/7}`, `k=0..6`; the pair with the smallest sampled mean QUBO energy is selected. Each pair uses 512 shots and sampler seed `20261112`.

The report includes the selected angles, grid, seed, per-pair and total shots, sampled QUBO energy, selected-distribution mean energy, decoded decision variables, original constraint results/violations, and wall-clock time. Runtime covers circuit creation, statevector sampling and collection across the full grid; it excludes QUBO setup and both exact classical references. It is an experimental measurement, not a fair runtime contest with the tiny exhaustive baselines.

## Comparisons

For each case, the sampled result is compared with (1) exhaustive enumeration over every QUBO bitstring, including slack bits, and (2) `EnumerativeSolver` over the original decision domains. The report records exact QUBO energy/bitstring/count and exact solver status/solution/objective/candidate count. A finite-shot heuristic can miss the optimum; a mismatch is reported rather than hidden. For an infeasible case, any sampled decoded assignment is reported as infeasible with no feasible objective, and agreement is checked against the exact infeasible status.

The sampler is the built-in ideal statevector reference implementation documented by Qiskit. Its probabilities are sampled with a fixed seed and shot count. Neither this ideal simulator nor the small synthetic fixtures are evidence for hardware performance or quantum advantage.

## Observed run

Environment: WSL, Python 3.14.4, Qiskit 2.6.1. The run used seed `20261112`, 49 grid points, and 512 shots per point (25,088 shots per case). Runtime is one observed wall-clock run and is recorded for reproducibility only.

| Case | Simulator decoded status | Simulator objective | Simulator QUBO energy | Exact QUBO minimum | `EnumerativeSolver` | Simulator runtime |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| feasible | feasible | 10.0 | -10.0 | -10.0, 256 bitstrings | optimal, 10.0, 8 candidates | 0.493 s |
| resource-constrained | feasible | 7.0 | -7.0 | -7.0, 256 bitstrings | optimal, 7.0, 8 candidates | 0.470 s |
| infeasible | infeasible; `minimum_selected` violation 1.0 | null | 7.0 | 7.0, 256 bitstrings | infeasible, 8 candidates | 0.505 s |

In the two feasible fixtures, this seeded sample matched the exact decision assignment. In the infeasible fixture, both exact references report infeasible and the sampled assignment also fails the original `minimum_selected` constraint. These outcomes describe only this tiny simulator run.

## Verification

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 examples/synthetic_optimization.py
PYTHONPATH=src python3 examples/qiskit_qaoa_experiment.py
```
