# Quantum Space AGI Reusable Engine

Reusable Python foundations for scientific computing, data engineering,
simulation, optimization, machine-learning readiness, and visualization.
This repository is an engineering project, not a complete mission-design
solution or an official NASA specification.

## Current modules

- **ARC-03 — Data engineering:** validated datasets, provenance, local
  ingestion/export, schemas, quality checks, and a provider-neutral adapter
  contract. See [data architecture](docs/DATA_ARCHITECTURE.md) and
  [data validation](docs/DATA_VALIDATION.md).
- **ARC-04 — Scientific computing:** canonical Jupyter notebooks for numerical
  precision, validation, vectors, matrices, and units. See
  [scientific foundation](docs/scientific/arc04_foundation.md) and
  [notebook migration](docs/arc04_notebook_migration.md).
- **ARC-05 — Simulation:** an educational two-body orbital propagation
  workflow using fixed-step RK4. Its assumptions and limits are in
  [the simulation notes](docs/arc05_simulation.md).
- **ARC-06 — Classical optimization:** generic objective/constraint interfaces,
  finite-domain models, `EnumerativeSolver`, and repeatable synthetic
  benchmarks. See [classical optimization practice](docs/classical-optimization-practice.md).
- **ARC-07 — Quantum toolkit experiments:** optional QUBO encoding, classical
  heuristics, and a local Qiskit statevector QAOA example. These are
  experimental examples, not production solvers, hardware runs, or evidence
  of quantum advantage. See [the QUBO experiment](docs/qubo-experiment.md),
  [the Qiskit simulator experiment](docs/qiskit-experiment.md), and
  [consolidated benchmark notes](docs/final-benchmark.md).
- **ARC-08 — AI/ML readiness:** preprocessing utilities and a bounded,
  provenance-linked NASA Exoplanet Archive TAP adapter. The adapter is a data
  integration example, not an official NASA requirement or a general NASA API
  client. See [adapter documentation](docs/EXOPLANET_ARCHIVE_ADAPTER.md) and
  [ML readiness notes](docs/ARC08_ML_READINESS_DECISION.md).
- **ARC-09 — Visualization:** standalone UI and chart prototypes with handoff
  notes; they are not a production dashboard or integrated backend. See
  [prototype handoff](arc09-ui-prototype/PROTOTYPE_HANDOFF.md).

## Scope and limits

The modules are reusable starting points. They do not establish mission
readiness, scientific validity for a specific mission, or official NASA
requirements. Each scientific or optimization example documents its own
inputs, assumptions, validation, and limitations. The finite enumerative
solver is exponential and intended only for small problems. QUBO/QAOA examples
remain optional experiments; the base package does not require Qiskit.

The ARC-03 `Dataset` keeps its top-level record and metadata mappings
read-only, but nested dictionaries and lists are not deep-frozen. CSV export
infers headers from record keys; empty datasets produce an empty CSV, and CSV
cannot preserve provenance metadata. Use JSON export when that metadata is
needed.

## Install and verify

Use Python 3.11 or newer. Install test and quality tools in an isolated
environment:

```shell
python -m pip install -e ".[test,quality]"
```

Run the repository checks from the root:

```shell
python -m pytest
ruff check .
ruff format --check .
mypy
python -m build
```

Notebook authoring tools are optional:

```shell
python -m pip install -e ".[notebooks]"
```

The Qiskit simulator example is optional:

```shell
python -m pip install -e ".[qiskit-experiment]"
PYTHONPATH=src python examples/qiskit_qaoa_experiment.py
```

For the deterministic classical examples, run:

```shell
PYTHONPATH=src python examples/synthetic_optimization.py
```

## Contribution and licensing

Contributions should explain their purpose, include appropriate tests, and
document user-visible behavior. See [CONTRIBUTING.md](CONTRIBUTING.md) and
the [pull request template](.github/PULL_REQUEST_TEMPLATE.md).

MIT is recorded as the intended license direction, but there is no `LICENSE`
file yet. Do not assume reuse rights until a license is formally added; see
[the license decision record](docs/governance/license-options.md).
