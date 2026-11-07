# Quantum Space AGI Reusable Engine

A reusable engineering foundation for future space-mission design and other
scientific computing projects.

## Purpose

This project is intended to grow a collection of reusable, tested components for:

- scientific data processing and computing;
- space-mission simulation interfaces;
- classical optimization and optional quantum optimization experiments;
- AI and machine-learning utilities;
- visualization and API integration; and
- testing, packaging, and deployment.

The repository includes ARC-00 governance, the ARC-01 Python package
foundation, ARC-02 core utilities, and ARC-03 data engineering components.

## Scope and non-goals

The engine is intended to provide general-purpose infrastructure that can be
reused across projects. It is not, at this stage, a complete NASA Space Apps
Challenge solution, a mission-ready flight system, or a source of authoritative
scientific data. Future scientific calculations and simulations must document
their assumptions, inputs, limitations, and validation; no accuracy or quantum
advantage is implied by the project's name or goals.

The ARC-03 data package provides source and provenance models, JSON/CSV and
local-file ingestion, declarative schema validation, basic quality analysis,
safe JSON/CSV export, and a provider-neutral adapter contract. A focused,
read-only NASA Exoplanet Archive TAP adapter retrieves bounded JSON responses
into a provenance-linked `Dataset`; it does not retain raw response files.
There is no general NASA API client, automatic type coercion, or scientific
validation. Callers remain responsible for accurate source metadata and
domain-appropriate schemas. See
[`docs/EXOPLANET_ARCHIVE_ADAPTER.md`](docs/EXOPLANET_ARCHIVE_ADAPTER.md).

`Dataset` copies and exposes its top-level record and metadata mappings as
read-only, but nested dictionaries and lists are not deep-copied or frozen.
Mutating a nested value can therefore change the dataset; consumers such as
quality analysis and JSON export inspect these values without mutating them.

CSV export infers headers from record keys. An empty dataset has no keys from
which to infer a header, so its CSV output is an empty file. CSV also cannot
preserve provenance or dataset metadata; use JSON export when that traceability
is needed. An explicit schema/header option may be considered in a future
version, but is not currently provided.

Quantum computing, task-specific AI/ML, visualization, and other external API
integrations remain future capabilities. They are not core dependencies and
should only be introduced with a concrete use case and tests.

## Project status

Work is organized into ARC roadmap branches. See [CONTRIBUTING.md](CONTRIBUTING.md)
for branch, review, and development conventions. The package is an early
foundation; domain-specific scientific validation and optimization
capabilities remain future work.

## Development

Install the package and development tools in an isolated environment:

```shell
python -m pip install -e ".[test,quality]"
```

Run the available checks from the repository root:

```shell
python -m pytest
ruff check .
ruff format --check .
mypy
python -m build
```

Contributions should explain their purpose, include appropriate tests when
code is introduced, and document user-visible behavior. See
[CONTRIBUTING.md](CONTRIBUTING.md) and the [pull request template](.github/PULL_REQUEST_TEMPLATE.md).

## License

MIT is the project's selected license direction, but no `LICENSE` file has
been added. Until a license is formally added, do not assume the repository is
available for reuse under MIT terms. See
[the license decision record](docs/governance/license-options.md).
