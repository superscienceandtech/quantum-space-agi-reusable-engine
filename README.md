# Quantum Space AGI Reusable Engine

Reusable, challenge-independent components for the Quantum Space AGI project.
This repository currently contains a small classical optimization foundation;
it is not a complete mission-design solution or an official NASA specification.

## Current scope

- Generic objective and constraint interfaces.
- Validated finite-domain problem and result data structures.
- A deterministic exhaustive classical baseline for small problems.
- A repeatable wall-clock benchmark helper and synthetic example.

The QUBO encoding and local QAOA simulator are optional experimental examples,
not production solver capabilities. Challenge-specific mission logic remains
outside this reusable-engine baseline.

## Classical optimization practice

Install the package in editable mode, then run the deterministic feasible,
resource-constrained, and infeasible examples:

```powershell
python -m pip install -e .
python examples/synthetic_optimization.py
```

The script prints JSON for the three correctness scenarios and a separate
3/6/9/12-variable scaling series. Output includes inputs, solver settings,
status, objective, constraint checks, candidate/objective-evaluation counts,
and five timing samples with mean, median, and minimum. Timing is recorded for
reproducibility; these tiny examples do not establish a performance advantage. See
[docs/classical-optimization-practice.md](docs/classical-optimization-practice.md)
for benchmark methodology and expected case outcomes.

The QUBO example also reports a seeded classical simulated-annealing heuristic
against exact QUBO enumeration. It is a classical heuristic comparison, not a
quantum-hardware run or a quantum-advantage claim.

Algorithm research has a seeded CPU dSB baseline and a project-specific
feasibility-guided dSB pilot; see [docs/algorithm-research.md](docs/algorithm-research.md).
They are experimental candidates, not production capabilities or proven novel algorithms.

## Algorithm generalization benchmark

A generated benchmark compares exact small-instance references, simulated
annealing, discrete simulated bifurcation, and feasibility-guided dSB across
sparse/dense Max-Cut and knapsack families. See
[docs/generalization-benchmark.md](docs/generalization-benchmark.md) for the
matched-budget protocol, public Kipu and Stanford Gset G1/G2 Max-Cut comparisons,
held-out parameter sensitivity, reproduction commands, and interpretation
limits.
## Run verification

```powershell
python -m unittest discover -s tests -v
```

The local conventions, assumptions, and integration decisions to align with
Yousuf and Sonjoy are documented in [docs/algorithm-conventions.md](docs/algorithm-conventions.md).

The Nov 9–10 QUBO encoding assumptions and classical comparison procedure are
documented in [docs/qubo-experiment.md](docs/qubo-experiment.md). A separate
Nov 11–12 local Qiskit simulator experiment is described in
[docs/qiskit-experiment.md](docs/qiskit-experiment.md); it uses an optional
dependency, makes no hardware or quantum-advantage claim, and leaves the
classical baseline intact. The consolidated Nov 13 results and limits are in
[docs/final-benchmark.md](docs/final-benchmark.md).
