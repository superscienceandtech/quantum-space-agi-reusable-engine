import math

import numpy as np
import pytest

from quantum_space_agi.scientific.errors import ScientificError, ScientificErrorCode
from quantum_space_agi.scientific.vector import (
    add,
    create_vector,
    cross,
    distance,
    dot,
    magnitude,
    normalize,
    scale,
    subtract,
)


def test_create_vector_accepts_2d_and_3d_values() -> None:
    vector_2d = create_vector((1, 2))
    vector_3d = create_vector([1.0, 2.0, 3.0])

    assert vector_2d.dtype == np.dtype(np.float64)
    assert vector_3d.dtype == np.dtype(np.float64)
    np.testing.assert_array_equal(vector_2d, np.array([1.0, 2.0]))
    np.testing.assert_array_equal(vector_3d, np.array([1.0, 2.0, 3.0]))


def test_create_vector_copies_mutable_input() -> None:
    source = [1.0, 2.0]
    vector = create_vector(source)
    source[0] = 99.0

    np.testing.assert_array_equal(vector, np.array([1.0, 2.0]))


@pytest.mark.parametrize(
    "values",
    [(), (1.0,), (1.0, 2.0, 3.0, 4.0), ((1.0, 2.0),)],
)
def test_create_vector_rejects_invalid_dimensions(
    values: tuple[object, ...],
) -> None:
    with pytest.raises(ScientificError) as exc_info:
        create_vector(values)

    assert exc_info.value.code is ScientificErrorCode.INVALID_DIMENSION


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_create_vector_rejects_non_finite_values(value: float) -> None:
    with pytest.raises(ScientificError) as exc_info:
        create_vector((1.0, value))

    assert exc_info.value.code is ScientificErrorCode.NON_FINITE_VALUE


def test_create_vector_rejects_complex_values() -> None:
    with pytest.raises(ScientificError) as exc_info:
        create_vector((1.0 + 1.0j, 2.0))

    assert exc_info.value.code is ScientificErrorCode.INVALID_DIMENSION


@pytest.mark.parametrize("values", [(True, False), np.array([True, False])])
def test_create_vector_rejects_boolean_values(values) -> None:
    with pytest.raises(ScientificError) as exc_info:
        create_vector(values)

    assert exc_info.value.code is ScientificErrorCode.INVALID_STATE


def test_2d_vector_addition_and_subtraction() -> None:
    np.testing.assert_array_equal(add((1, 2), (3, 4)), np.array([4.0, 6.0]))
    np.testing.assert_array_equal(
        subtract((1, 2), (3, 4)),
        np.array([-2.0, -2.0]),
    )


def test_3d_vector_addition_and_subtraction() -> None:
    np.testing.assert_array_equal(
        add((1, 2, 3), (4, 5, 6)),
        np.array([5.0, 7.0, 9.0]),
    )
    np.testing.assert_array_equal(
        subtract((4, 5, 6), (1, 2, 3)),
        np.array([3.0, 3.0, 3.0]),
    )


def test_scalar_multiplication() -> None:
    np.testing.assert_array_equal(
        scale((1, -2, 3), 2.5),
        np.array([2.5, -5.0, 7.5]),
    )


def test_scalar_multiplication_rejects_non_finite_scalar() -> None:
    with pytest.raises(ScientificError) as exc_info:
        scale((1, 2, 3), math.inf)

    assert exc_info.value.code is ScientificErrorCode.NON_FINITE_VALUE


@pytest.mark.parametrize("scalar", [True, "2", None, 1 + 2j])
def test_scalar_multiplication_rejects_invalid_scalar(scalar) -> None:
    with pytest.raises(ScientificError) as exc_info:
        scale((1, 2, 3), scalar)

    assert exc_info.value.code is ScientificErrorCode.INVALID_STATE


def test_dot_product() -> None:
    assert dot((1, 2, 3), (4, 5, 6)) == pytest.approx(32.0)


def test_cross_product_follows_right_hand_rule() -> None:
    np.testing.assert_allclose(
        cross((1, 0, 0), (0, 1, 0)),
        np.array([0.0, 0.0, 1.0]),
    )


def test_cross_product_is_perpendicular_to_inputs() -> None:
    left = (1.0, 2.0, 3.0)
    right = (4.0, 5.0, 6.0)
    result = cross(left, right)

    assert dot(left, result) == pytest.approx(0.0)
    assert dot(right, result) == pytest.approx(0.0)


def test_cross_product_rejects_2d_vectors() -> None:
    with pytest.raises(ScientificError) as exc_info:
        cross((1, 0), (0, 1))

    assert exc_info.value.code is ScientificErrorCode.INVALID_DIMENSION


def test_magnitude() -> None:
    assert magnitude((3, 4)) == pytest.approx(5.0)
    assert magnitude((3e150, 4e150)) == pytest.approx(5e150)


def test_normalize() -> None:
    result = normalize((3, 4))
    np.testing.assert_allclose(result, np.array([0.6, 0.8]))
    assert magnitude(result) == pytest.approx(1.0)


def test_normalize_rejects_zero_vector() -> None:
    with pytest.raises(ScientificError) as exc_info:
        normalize((0, 0, 0))

    assert exc_info.value.code is ScientificErrorCode.INVALID_STATE


def test_distance() -> None:
    assert distance((0, 0), (3, 4)) == pytest.approx(5.0)
    assert distance((1, 2, 3), (1, 2, 3)) == 0.0


@pytest.mark.parametrize(
    "operation",
    [
        lambda: add((1e308, 1e308), (1e308, 1e308)),
        lambda: subtract((-1e308, -1e308), (1e308, 1e308)),
        lambda: scale((1e308, 1e308), 2.0),
        lambda: dot((1e308, 1e308), (1e308, 1e308)),
        lambda: cross((1e308, 1e308, 0.0), (1e308, 1e308, 0.0)),
    ],
)
def test_vector_operations_reject_overflow_results(operation) -> None:
    with pytest.raises(ScientificError) as exc_info:
        operation()

    assert exc_info.value.code is ScientificErrorCode.NON_FINITE_VALUE


def test_distance_rejects_overflowing_difference() -> None:
    with pytest.raises(ScientificError) as exc_info:
        distance((-1e308, 0.0), (1e308, 0.0))

    assert exc_info.value.code is ScientificErrorCode.NON_FINITE_VALUE


def test_magnitude_supports_small_and_large_finite_vectors() -> None:
    assert magnitude((1e-300, 1e-300)) == pytest.approx(1.4142135623730951e-300)
    assert magnitude((3e300, 4e300)) == pytest.approx(5e300)


def test_normalize_supports_small_finite_vector() -> None:
    result = normalize((1e-300, 1e-300))
    np.testing.assert_allclose(
        result,
        np.array([1 / math.sqrt(2), 1 / math.sqrt(2)]),
    )


@pytest.mark.parametrize("operation", [add, subtract, dot, distance])
def test_matching_dimension_is_required(operation) -> None:
    with pytest.raises(ScientificError) as exc_info:
        operation((1, 2), (1, 2, 3))

    assert exc_info.value.code is ScientificErrorCode.INVALID_DIMENSION


def test_vector_operations_do_not_mutate_input_arrays() -> None:
    left = np.array([1.0, 2.0, 3.0])
    right = np.array([4.0, 5.0, 6.0])
    left_before = left.copy()
    right_before = right.copy()

    add(left, right)
    subtract(left, right)
    scale(left, 2.0)
    dot(left, right)
    cross(left, right)
    normalize(left)
    distance(left, right)

    np.testing.assert_array_equal(left, left_before)
    np.testing.assert_array_equal(right, right_before)
