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

## Run the synthetic example

Install the package in editable mode, then run:

```powershell
python -m pip install -e .
python examples/synthetic_optimization.py
```

Expected result: a feasible optimum with objective value `14.0` after `16`
candidates are enumerated. Runtime varies by machine.

## Run verification

```powershell
python -m unittest discover -s tests -v
```

The local conventions, assumptions, and integration decisions to align with
Yousuf and Sonjoy are documented in [docs/algorithm-conventions.md](docs/algorithm-conventions.md).
