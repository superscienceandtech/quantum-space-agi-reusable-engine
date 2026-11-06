import math

import pytest

from quantum_space_agi.scientific.errors import ScientificError, ScientificErrorCode
from quantum_space_agi.scientific.validation import (
    validate_finite,
    validate_matrix,
    validate_vector,
)


def test_validate_finite_accepts_normal_values() -> None:
    assert validate_finite(12.5) == 12.5


@pytest.mark.parametrize("value", [True, False, "1.0", None, 1 + 2j])
def test_validate_finite_rejects_invalid_types_consistently(value: object) -> None:
    with pytest.raises(ScientificError) as exc_info:
        validate_finite(value)

    assert exc_info.value.code is ScientificErrorCode.INVALID_STATE


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_validate_finite_rejects_non_finite_values(value: float) -> None:
    with pytest.raises(ScientificError) as exc_info:
        validate_finite(value, field="position")

    assert exc_info.value.code is ScientificErrorCode.NON_FINITE_VALUE
    assert exc_info.value.field == "position"


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ((1.0, 2.0), (1.0, 2.0)),
        ((1.0, 2.0, 3.0), (1.0, 2.0, 3.0)),
    ],
)
def test_validate_vector_accepts_supported_dimensions(
    values: tuple[float, ...],
    expected: tuple[float, ...],
) -> None:
    assert validate_vector(values) == expected


@pytest.mark.parametrize("values", [(), (1.0,), (1.0, 2.0, 3.0, 4.0)])
def test_validate_vector_rejects_invalid_dimensions(
    values: tuple[float, ...],
) -> None:
    with pytest.raises(ScientificError) as exc_info:
        validate_vector(values)

    assert exc_info.value.code is ScientificErrorCode.INVALID_DIMENSION


def test_validate_vector_rejects_non_finite_component() -> None:
    with pytest.raises(ScientificError) as exc_info:
        validate_vector((1.0, math.inf))

    assert exc_info.value.code is ScientificErrorCode.NON_FINITE_VALUE


def test_validate_matrix_accepts_rectangular_matrix() -> None:
    assert validate_matrix(((1, 2, 3), (4, 5, 6))) == (
        (1.0, 2.0, 3.0),
        (4.0, 5.0, 6.0),
    )


@pytest.mark.parametrize(
    "values",
    [
        (),
        ((1.0, 2.0), (3.0,)),
        ((1.0, 2.0), ()),
    ],
)
def test_validate_matrix_rejects_invalid_shapes(
    values: tuple[tuple[float, ...], ...],
) -> None:
    with pytest.raises(ScientificError) as exc_info:
        validate_matrix(values)

    assert exc_info.value.code is ScientificErrorCode.INVALID_SHAPE
