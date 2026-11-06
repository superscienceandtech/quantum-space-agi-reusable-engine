# Contributing

Thank you for helping build a reusable engineering foundation. Contributions
should support general-purpose project infrastructure and avoid adding
challenge-specific behavior before that work is authorized.

## Before starting

1. Check the open issues and pull requests for related work.
2. For a substantial change, open or update an issue to agree on scope before
   implementation.
3. Keep changes focused. Explain trade-offs when a change affects public APIs,
   dependencies, scientific assumptions, or compatibility.
4. Do not add credentials, private data, or other secrets to the repository.

## Branches and pull requests

- Do not work directly on `main` or push directly to it.
- Use a short-lived branch from the repository's designated integration branch.
  Until maintainers specify otherwise, target `develop` for pull requests.
- Use `arc/<number>-<short-name>` for roadmap work (for example,
  `arc/01-foundation`), `feature/<short-name>` for other features,
  `fix/<short-name>` for fixes, and `docs/<short-name>` for documentation.
- Use lowercase words separated by hyphens in branch names.
- Open a pull request with a concise summary, rationale, test evidence, and any
  documentation or dependency impacts. Link the related issue when applicable.
- Do not merge your own change without the project's required review. Do not
  force-push shared branches.

## Development expectations

Install the package and its development tools in an isolated environment:

```shell
python -m pip install -e ".[test,quality]"
```

Run the project checks from the repository root:

```shell
python -m pytest
ruff check .
ruff format --check .
mypy
python -m build
```

When contributing code:

- Prefer small, cohesive changes with type hints and clear public interfaces.
- Use `snake_case` for Python modules, functions, and variables;
  `PascalCase` for classes; and `UPPER_SNAKE_CASE` for constants.
- Keep core runtime dependencies minimal. Put optional scientific, quantum,
  AI/ML, visualization, and API dependencies in feature-specific optional
  groups when justified.
- Validate inputs and surface errors explicitly. Avoid silent fallbacks and
  broad exception handling.
- Add deterministic tests for changed behavior. Tests should not require
  network access or credentials unless that dependency is explicitly part of
  the feature and isolated.
- Document assumptions, units, numerical tolerances, and known limitations
  where relevant. Do not claim scientific accuracy or quantum advantage without
  reproducible evidence.
- Update user and developer documentation when behavior or workflow changes.

## Reviews

Reviewers should focus on correctness, scope, maintainability, tests, security,
dependency impact, and documentation. A change should not be considered ready
until its required checks have been run and their results are reported in the
pull request. Do not claim checks passed if they were not run.

## Conduct

All contributors are expected to follow the project's
[Code of Conduct](CODE_OF_CONDUCT.md). Report concerns privately to the
repository owner or maintainers through a communication channel they have
provided; do not post sensitive details in a public issue.
