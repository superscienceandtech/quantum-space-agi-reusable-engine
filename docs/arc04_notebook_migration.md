# ARC-04 Notebook Migration

## Architecture

ARC-04 implementation source is canonical under
`src/quantum_space_agi/scientific/*.ipynb`. The implementation is not
maintained in generated or independently maintained `.py` files.

The runtime loader in `src/quantum_space_agi/scientific/__init__.py` reads
notebooks with `nbformat`, executes their code cells, and registers synthetic
Python modules in `sys.modules`. It loads modules in this deterministic order:

1. `errors`
2. `precision`
3. `validation`
4. `vector`
5. `matrix`
6. `units`

The loader preserves normal package imports:

```python
import quantum_space_agi.scientific as scientific
import quantum_space_agi.scientific.vector as vector

vector.create_vector((1.0, 2.0))
```

Notebook modules execute only when absent from the dependency registry.
Repeated imports reuse the module already registered in `sys.modules` and the
`_LOADED_MODULES` cache. If a notebook or dependency fails, loading rolls back
newly loaded modules, attributes, and cache entries; ordinary `Exception`
failures are wrapped as `ImportError` while process-control exceptions are not
converted into ordinary import failures.

## Dependencies and kernel

`nbformat` is a runtime dependency because the loader imports it. `nbclient`,
`pytest`, and `ipykernel` are development/test dependencies. Install the
complete notebook environment with:

```powershell
python -m pip install -e ".[dev,notebooks]"
```

The notebook package data pattern is:

```toml
[tool.setuptools.package-data]
quantum_space_agi = ["scientific/*.ipynb"]
```

Executable test notebooks are maintained under `tests/scientific/`.

## Testing actual scientific cases

The repository performs two independent kinds of notebook validation:

1. `test_notebook_executes` validates JSON/`nbformat` structure and executes
   each implementation and test notebook through `NotebookClient` with
   `allow_errors=False`.
2. `test_scientific_notebook_case` reads the test definitions from each test
   notebook, expands `pytest.mark.parametrize` decorators (including stacked
   decorators), and creates one pytest case for every expanded value.

The expanded scientific notebook suite currently contains **142 cases**:

| Notebook | Verified cases |
|---|---:|
| `test_matrix.ipynb` | 50 |
| `test_precision.ipynb` | 17 |
| `test_units.ipynb` | 15 |
| `test_validation.ipynb` | 19 |
| `test_vector.ipynb` | 41 |

Run the complete suite with:

```powershell
python -m pytest
```

The 11 notebook execution tests plus 142 expanded scientific cases produce
153 pytest results, rather than treating notebook execution itself as 142
independent passing cases.

## Necessary Python files

The following Python files are bootstrap, package metadata, or test infrastructure:

- `src/quantum_space_agi/scientific/__init__.py`: notebook runtime loader.
- `tests/test_notebooks.py`: notebook validation, notebook execution, and
  expansion of parametrized scientific cases.
- `tests/conftest.py` or other small bootstrap files, if later needed, are
  acceptable when they do not implement scientific algorithms.

Scientific implementation and test algorithms remain canonical in `.ipynb`
files. No generated `.py` implementation artifact is created or maintained.

## File mapping

| Original ARC-04 file | Canonical notebook | Notebook cell module |
|---|---|---|
| `src/quantum_space_agi/scientific/errors.py` | `src/quantum_space_agi/scientific/errors.ipynb` | `errors` |
| `src/quantum_space_agi/scientific/precision.py` | `src/quantum_space_agi/scientific/precision.ipynb` | `precision` |
| `src/quantum_space_agi/scientific/validation.py` | `src/quantum_space_agi/scientific/validation.ipynb` | `validation` |
| `src/quantum_space_agi/scientific/vector.py` | `src/quantum_space_agi/scientific/vector.ipynb` | `vector` |
| `src/quantum_space_agi/scientific/matrix.py` | `src/quantum_space_agi/scientific/matrix.ipynb` | `matrix` |
| `src/quantum_space_agi/scientific/units.py` | `src/quantum_space_agi/scientific/units.ipynb` | `units` |
| `tests/scientific/test_precision.py` | `tests/scientific/test_precision.ipynb` | runner cell |
| `tests/scientific/test_validation.py` | `tests/scientific/test_validation.ipynb` | runner cell |
| `tests/scientific/test_vector.py` | `tests/scientific/test_vector.ipynb` | runner cell |
| `tests/scientific/test_matrix.py` | `tests/scientific/test_matrix.ipynb` | runner cell |
| `tests/scientific/test_units.py` | `tests/scientific/test_units.ipynb` | runner cell |
