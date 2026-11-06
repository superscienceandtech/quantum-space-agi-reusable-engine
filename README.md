# Quantum Space AGI Reusable Engine

Reusable, challenge-independent components for the Quantum Space AGI project.
This repository currently contains a small classical optimization foundation;
it is not a complete mission-design solution or an official NASA specification.

## Current scope

- Generic objective and constraint interfaces.
- Validated finite-domain problem and result data structures.
- A deterministic exhaustive classical baseline for small problems.
- A repeatable wall-clock benchmark helper and synthetic example.

QUBO/QAOA and challenge-specific mission logic are deferred until the classical
baseline is reviewed and the team interfaces are agreed.

## Classical optimization practice

Install the package in editable mode, then run the deterministic feasible,
resource-constrained, and infeasible examples:

```powershell
python -m pip install -e .
python examples/synthetic_optimization.py
```

The script prints JSON containing each case's input, solver settings, status,
objective, constraint checks, candidate/objective-evaluation counts, and five
timing samples with mean and minimum. Timing is recorded for reproducibility;
these tiny examples do not establish a performance advantage. See
[docs/classical-optimization-practice.md](docs/classical-optimization-practice.md)
for benchmark methodology and expected case outcomes.

## Run verification

```powershell
python -m unittest discover -s tests -v
```

The local conventions, assumptions, and integration decisions to align with
Yousuf and Sonjoy are documented in [docs/algorithm-conventions.md](docs/algorithm-conventions.md).
