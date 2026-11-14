from pathlib import Path
import sys
from types import ModuleType

import nbformat
import numpy as np
import pytest

from quantum_space_agi.scientific import (
    CoordinateFrame,
    ScientificError,
    Unit,
    active_rotation_matrix_z,
    compose_transforms,
    create_transform,
    inverse_transform,
    transform_point,
)

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_DIR = ROOT / "notebooks" / "arc04_scientific"


def execute_implementation_cell(notebook_name, monkeypatch):
    notebook = nbformat.read(NOTEBOOK_DIR / notebook_name, as_version=4)
    monkeypatch.chdir(NOTEBOOK_DIR)
    module_name = f"arc04_test_{notebook_name[:2]}"
    module = ModuleType(module_name)
    namespace = module.__dict__
    sys.modules[module_name] = module
    code_cell = next(cell for cell in notebook.cells if cell.cell_type == "code")
    try:
        exec(compile(code_cell.source, f"{notebook_name}:implementation-cell", "exec"), namespace)
    finally:
        del sys.modules[module_name]
    return namespace


@pytest.mark.parametrize(
    "point",
    [
        [True, 0.0, 0.0],
        np.array([True, 0.0, 0.0], dtype=object),
    ],
)
def test_transform_point_rejects_boolean_components(point):
    transform = create_transform("source", "target")

    with pytest.raises(ScientificError):
        transform_point(transform, point)


def test_rotation_matrix_rejects_mixed_boolean_components():
    rotation = [
        [True, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]

    with pytest.raises(ScientificError):
        create_transform("source", "target", rotation=rotation)


@pytest.mark.parametrize("scale", [float("inf"), float("nan"), True])
def test_unit_rejects_non_finite_or_boolean_scale(scale):
    with pytest.raises(ScientificError):
        Unit("test", "test unit", scale, (1, 0, 0, 0, 0, 0, 0))


@pytest.mark.parametrize(
    "dimensions",
    [
        (1, 0.5, 0, 0, 0, 0, 0),
        (1, True, 0, 0, 0, 0, 0),
        (1, 0, 0, 0, 0, 0),
    ],
)
def test_unit_rejects_invalid_dimension_exponents(dimensions):
    with pytest.raises(ScientificError):
        Unit("test", "test unit", 1.0, dimensions)


def test_active_rotation_and_unit_scaled_transform_round_trip():
    rotation = active_rotation_matrix_z(np.pi / 2.0)
    assert np.allclose(rotation @ [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], atol=1e-15)
    assert np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-15)
    assert np.linalg.det(rotation) == pytest.approx(1.0)

    length_dimensions = (1, 0, 0, 0, 0, 0, 0)
    source = CoordinateFrame(
        "source",
        unit=Unit("km", "kilometre", 1000.0, length_dimensions),
    )
    target = CoordinateFrame(
        "target",
        unit=Unit("m", "metre", 1.0, length_dimensions),
    )
    transform = create_transform(
        source,
        target,
        rotation=rotation,
        translation=[10.0, 20.0, 30.0],
    )
    point = np.array([1.0, 2.0, 3.0])
    transformed = transform_point(transform, point)
    restored = transform_point(inverse_transform(transform), transformed)

    assert np.allclose(transformed, [-1990.0, 1020.0, 3030.0], atol=1e-12)
    assert np.allclose(restored, point, atol=1e-12)
    identity = compose_transforms(inverse_transform(transform), transform)
    assert np.allclose(transform_point(identity, point), point, atol=1e-12)


def test_coordinate_frame_notebook_uses_validated_implementation(monkeypatch):
    namespace = execute_implementation_cell("01_coordinate_frames.ipynb", monkeypatch)

    assert namespace["sys"].path[0] == str(ROOT / "src")
    transform = namespace["create_transform"]("source", "target")
    with pytest.raises(namespace["ScientificError"]):
        namespace["transform_point"](transform, [True, 0.0, 0.0])


def test_units_notebook_uses_validated_implementation(monkeypatch):
    namespace = execute_implementation_cell("03_units.ipynb", monkeypatch)

    assert namespace["sys"].path[0] == str(ROOT / "src")
    with pytest.raises(namespace["ScientificError"]):
        namespace["Unit"]("test", "test unit", float("inf"), (1, 0, 0, 0, 0, 0, 0))
