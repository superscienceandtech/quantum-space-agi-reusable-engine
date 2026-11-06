# Quantum Space AGI Reusable Engine

## ARC-04 scientific notebooks

ARC-04 scientific implementations are canonical Jupyter notebooks under
`src/quantum_space_agi/scientific/`. The package loader executes them in this
dependency order:

1. `errors.ipynb`
2. `precision.ipynb`
3. `validation.ipynb`
4. `vector.ipynb`
5. `matrix.ipynb`
6. `units.ipynb`

ARC-05 and later modules should use the stable package imports rather than
executing or parsing notebooks themselves:

```python
import quantum_space_agi.scientific as scientific

from quantum_space_agi.scientific import matrix, units, vector
from quantum_space_agi.scientific.errors import ScientificError
```

Executable ARC-04 tests are in `tests/scientific/*.ipynb`.

## Validation and testing

Install development dependencies and execute the notebook-aware suite:

```powershell
python -m pip install -e .[dev,notebooks]
python -m pytest
```
