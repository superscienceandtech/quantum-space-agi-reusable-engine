import math

import numpy as np
import pytest

from quantum_space_agi.scientific.errors import (
    ScientificError,
    ScientificErrorCode,
)
from quantum_space_agi.scientific import matrix


def test_create_matrix_returns_float64_copy():
    source = [[1, 2], [3, 4]]
    result = matrix.create_matrix(source)

    assert result.dtype == np.float64
    np.testing.assert_array_equal(result, [[1, 2], [3, 4]])

    result[0, 0] = 99
    assert source[0][0] == 1


@pytest.mark.parametrize(
    "values",
    [
        [],
        [1, 2, 3],
        [[1, 2], [3]],
        [[1, 2], []],
        [[1], [2, 3]],
    ],
)
def test_create_matrix_rejects_invalid_shapes(values):
    with pytest.raises(ScientificError) as exc_info:
        matrix.create_matrix(values)

    assert exc_info.value.code is ScientificErrorCode.INVALID_SHAPE


@pytest.mark.parametrize(
    "values",
    [
        [[True, False]],
        [[1 + 2j, 3 + 4j]],
        [["invalid", 2]],
    ],
)
def test_create_matrix_rejects_invalid_types(values):
    with pytest.raises(ScientificError):
        matrix.create_matrix(values)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_create_matrix_rejects_non_finite_values(value):
    with pytest.raises(ScientificError) as exc_info:
        matrix.create_matrix([[1, value]])

    assert exc_info.value.code is ScientificErrorCode.NON_FINITE_VALUE


def test_add():
    result = matrix.add([[1, 2], [3, 4]], [[5, 6], [7, 8]])

    np.testing.assert_array_equal(result, [[6, 8], [10, 12]])


def test_subtract():
    result = matrix.subtract([[5, 6], [7, 8]], [[1, 2], [3, 4]])

    np.testing.assert_array_equal(result, [[4, 4], [4, 4]])


def test_add_rejects_different_shapes():
    with pytest.raises(ScientificError) as exc_info:
        matrix.add([[1, 2]], [[1], [2]])

    assert exc_info.value.code is ScientificErrorCode.INVALID_SHAPE


def test_subtract_rejects_different_shapes():
    with pytest.raises(ScientificError) as exc_info:
        matrix.subtract([[1, 2]], [[1], [2]])

    assert exc_info.value.code is ScientificErrorCode.INVALID_SHAPE


def test_multiply():
    result = matrix.multiply(
        [[1, 2, 3], [4, 5, 6]],
        [[7, 8], [9, 10], [11, 12]],
    )

    np.testing.assert_array_equal(result, [[58, 64], [139, 154]])


def test_multiply_rejects_incompatible_shapes():
    with pytest.raises(ScientificError) as exc_info:
        matrix.multiply([[1, 2]], [[1, 2]])

    assert exc_info.value.code is ScientificErrorCode.INVALID_SHAPE


def test_transpose():
    result = matrix.transpose([[1, 2, 3], [4, 5, 6]])

    np.testing.assert_array_equal(result, [[1, 4], [2, 5], [3, 6]])


def test_transpose_returns_independent_copy():
    source = np.array([[1, 2], [3, 4]], dtype=np.float64)
    result = matrix.transpose(source)

    result[0, 0] = 99

    assert source[0, 0] == 1


def test_determinant():
    result = matrix.determinant([[4, 6], [3, 8]])

    assert result == pytest.approx(14.0)


def test_determinant_rejects_non_square_matrix():
    with pytest.raises(ScientificError) as exc_info:
        matrix.determinant([[1, 2, 3], [4, 5, 6]])

    assert exc_info.value.code is ScientificErrorCode.INVALID_SHAPE


def test_inverse():
    result = matrix.inverse([[4, 7], [2, 6]])

    expected = np.array([[0.6, -0.7], [-0.2, 0.4]])

    np.testing.assert_allclose(result, expected, atol=1e-12, rtol=1e-9)


def test_inverse_identity_property():
    source = np.array([[4, 7], [2, 6]], dtype=np.float64)

    result = matrix.multiply(source, matrix.inverse(source))

    np.testing.assert_allclose(
        result,
        np.eye(2),
        atol=1e-12,
        rtol=1e-9,
    )


def test_inverse_rejects_singular_matrix():
    with pytest.raises(ScientificError) as exc_info:
        matrix.inverse([[1, 2], [2, 4]])

    assert exc_info.value.code is ScientificErrorCode.SINGULAR_MATRIX


def test_inverse_rejects_ill_conditioned_matrix():
    with pytest.raises(ScientificError) as exc_info:
        matrix.inverse(
            [[1, 0], [0, 1e-14]],
            max_condition_number=1e12,
        )

    assert exc_info.value.code is ScientificErrorCode.UNCERTAIN_RESULT


def test_inverse_accepts_well_conditioned_matrix():
    result = matrix.inverse(
        [[1, 0], [0, 2]],
        max_condition_number=1e12,
    )

    np.testing.assert_allclose(result, [[1, 0], [0, 0.5]])


def test_inverse_rejects_non_square_matrix():
    with pytest.raises(ScientificError) as exc_info:
        matrix.inverse([[1, 2, 3], [4, 5, 6]])

    assert exc_info.value.code is ScientificErrorCode.INVALID_SHAPE


def test_solve():
    result = matrix.solve(
        [[3, 1], [1, 2]],
        [9, 8],
    )

    np.testing.assert_allclose(result, [2, 3])


def test_solve_solution_satisfies_original_equation():
    coefficients = np.array([[3, 1], [1, 2]], dtype=np.float64)
    rhs = np.array([9, 8], dtype=np.float64)

    result = matrix.solve(coefficients, rhs)

    np.testing.assert_allclose(
        coefficients @ result,
        rhs,
        atol=1e-12,
        rtol=1e-9,
    )


def test_solve_rejects_singular_matrix():
    with pytest.raises(ScientificError) as exc_info:
        matrix.solve([[1, 2], [2, 4]], [3, 6])

    assert exc_info.value.code is ScientificErrorCode.SINGULAR_MATRIX


def test_solve_rejects_ill_conditioned_matrix():
    with pytest.raises(ScientificError) as exc_info:
        matrix.solve(
            [[1, 0], [0, 1e-14]],
            [1, 1],
            max_condition_number=1e12,
        )

    assert exc_info.value.code is ScientificErrorCode.UNCERTAIN_RESULT


def test_solve_rejects_wrong_rhs_shape():
    with pytest.raises(ScientificError) as exc_info:
        matrix.solve([[1, 2], [3, 4]], [1, 2, 3])

    assert exc_info.value.code is ScientificErrorCode.INVALID_SHAPE


@pytest.mark.parametrize(
    "rhs",
    [
        [True, False],
        [1 + 2j, 3 + 4j],
        ["invalid", 2],
    ],
)
def test_solve_rejects_invalid_rhs_types(rhs):
    with pytest.raises(ScientificError):
        matrix.solve([[2, 0], [0, 2]], rhs)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_solve_rejects_non_finite_rhs(value):
    with pytest.raises(ScientificError) as exc_info:
        matrix.solve([[2, 0], [0, 2]], [1, value])

    assert exc_info.value.code is ScientificErrorCode.NON_FINITE_VALUE


def test_solve_rejects_non_square_matrix():
    with pytest.raises(ScientificError) as exc_info:
        matrix.solve([[1, 2, 3], [4, 5, 6]], [1, 2])

    assert exc_info.value.code is ScientificErrorCode.INVALID_SHAPE


@pytest.mark.parametrize("limit", [1.0, 0.0, -1.0, math.inf, math.nan, True])
def test_condition_limit_rejects_invalid_values(limit):
    with pytest.raises(ScientificError):
        matrix.inverse([[1, 0], [0, 2]], max_condition_number=limit)


def test_add_detects_overflow():
    with pytest.raises(ScientificError) as exc_info:
        matrix.add(
            [[np.finfo(np.float64).max]],
            [[np.finfo(np.float64).max]],
        )

    assert exc_info.value.code is ScientificErrorCode.NON_FINITE_VALUE


def test_multiply_detects_overflow():
    with pytest.raises(ScientificError) as exc_info:
        matrix.multiply(
            [[np.finfo(np.float64).max]],
            [[2]],
        )

    assert exc_info.value.code is ScientificErrorCode.NON_FINITE_VALUE


def test_inverse_detects_non_finite_result():
    with pytest.raises(ScientificError) as exc_info:
        matrix.inverse([[1e-310, 0], [0, 1e-310]])

    assert exc_info.value.code in (
        ScientificErrorCode.UNCERTAIN_RESULT,
        ScientificErrorCode.NON_FINITE_VALUE,
    )


def test_input_matrices_remain_unchanged():
    left = np.array([[1, 2], [3, 4]], dtype=np.float64)
    right = np.array([[5, 6], [7, 8]], dtype=np.float64)

    left_before = left.copy()
    right_before = right.copy()

    matrix.add(left, right)
    matrix.subtract(left, right)
    matrix.multiply(left, right)
    matrix.transpose(left)
    matrix.determinant(left)
    matrix.inverse(left)
    matrix.solve(left, [1, 2])

    np.testing.assert_array_equal(left, left_before)
    np.testing.assert_array_equal(right, right_before)
