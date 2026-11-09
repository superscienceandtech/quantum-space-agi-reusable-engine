"""Foundation utilities loaded from canonical ARC-04 notebooks."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import nbformat

_NOTEBOOK_DIR = Path(__file__).resolve().parent
_NOTEBOOK_ORDER = (
    "errors",
    "precision",
    "validation",
    "vector",
    "matrix",
    "units",
)
_LOADED_MODULES: dict[str, types.ModuleType] = {}


def _execute_notebook_module(module_name: str) -> types.ModuleType:
    notebook_path = _NOTEBOOK_DIR / f"{module_name}.ipynb"
    full_name = f"{__name__}.{module_name}"
    previous_module = sys.modules.get(full_name)
    package_module = sys.modules[__name__]
    had_attribute = hasattr(package_module, module_name)
    previous_attribute = getattr(package_module, module_name, None)

    if not notebook_path.is_file():
        raise ImportError(f"Missing ARC-04 notebook module: {notebook_path}")

    with notebook_path.open("r", encoding="utf-8") as file:
        notebook = nbformat.read(file, as_version=4)  # type: ignore[no-untyped-call]

    module = types.ModuleType(full_name)
    module.__file__ = str(notebook_path)
    module.__package__ = __name__
    module.__loader__ = None
    module.__spec__ = importlib.util.spec_from_loader(full_name, loader=None)
    sys.modules[full_name] = module

    try:
        for index, cell in enumerate(notebook.cells):
            if cell.cell_type != "code":
                continue
            source = "".join(cell.source)
            if not source.strip():
                continue
            code = compile(source, f"{notebook_path}:cell-{index + 1}", "exec")
            exec(code, module.__dict__)
    except Exception as exc:
        if previous_module is None:
            sys.modules.pop(full_name, None)
        else:
            sys.modules[full_name] = previous_module
        if had_attribute:
            setattr(package_module, module_name, previous_attribute)
        elif hasattr(package_module, module_name):
            delattr(package_module, module_name)
        raise ImportError(
            f"Failed to execute ARC-04 notebook module {module_name}"
        ) from exc

    return module


def load_notebook_modules() -> dict[str, types.ModuleType]:
    """Load every ARC-04 notebook module in deterministic dependency order."""
    if _LOADED_MODULES:
        return dict(_LOADED_MODULES)

    previous_modules = {
        module_name: sys.modules.get(f"{__name__}.{module_name}")
        for module_name in _NOTEBOOK_ORDER
    }
    previous_attributes = {
        module_name: getattr(sys.modules[__name__], module_name, None)
        for module_name in _NOTEBOOK_ORDER
    }
    previous_loaded = dict(_LOADED_MODULES)

    try:
        for module_name in _NOTEBOOK_ORDER:
            full_name = f"{__name__}.{module_name}"
            module = sys.modules.get(full_name)
            if module is None:
                module = _execute_notebook_module(module_name)
            setattr(sys.modules[__name__], module_name, module)
            _LOADED_MODULES[module_name] = module
        return dict(_LOADED_MODULES)
    except Exception:
        _LOADED_MODULES.clear()
        _LOADED_MODULES.update(previous_loaded)
        for module_name in _NOTEBOOK_ORDER:
            full_name = f"{__name__}.{module_name}"
            previous_module = previous_modules[module_name]
            if previous_module is None:
                sys.modules.pop(full_name, None)
            else:
                sys.modules[full_name] = previous_module

            if (
                module_name in previous_attributes
                and previous_attributes[module_name] is not None
            ):
                setattr(
                    sys.modules[__name__], module_name, previous_attributes[module_name]
                )
            elif hasattr(sys.modules[__name__], module_name):
                delattr(sys.modules[__name__], module_name)
        raise


_modules = load_notebook_modules()
errors = _modules["errors"]
precision = _modules["precision"]
validation = _modules["validation"]
vector = _modules["vector"]
matrix = _modules["matrix"]
units = _modules["units"]

ScientificError = errors.ScientificError
ScientificErrorCode = errors.ScientificErrorCode
ComparisonTolerance = precision.ComparisonTolerance
is_close = precision.is_close
validate_finite = validation.validate_finite
validate_matrix = validation.validate_matrix
validate_vector = validation.validate_vector
add = vector.add
create_vector = vector.create_vector
cross = vector.cross
distance = vector.distance
dot = vector.dot
magnitude = vector.magnitude
normalize = vector.normalize
scale = vector.scale
subtract = vector.subtract

__all__ = [
    "errors",
    "precision",
    "validation",
    "vector",
    "matrix",
    "units",
    "ComparisonTolerance",
    "ScientificError",
    "ScientificErrorCode",
    "is_close",
    "validate_finite",
    "validate_matrix",
    "validate_vector",
    "add",
    "create_vector",
    "cross",
    "distance",
    "dot",
    "magnitude",
    "normalize",
    "scale",
    "subtract",
]
