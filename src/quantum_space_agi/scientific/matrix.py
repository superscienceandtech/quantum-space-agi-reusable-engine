"""Float64 matrix operations with validation and numerical diagnostics."""

from __future__ import annotations

from numbers import Real
from typing import Any, Sequence

import numpy as np
from numpy.typing import NDArray

from .errors import ScientificError, ScientificErrorCode
from .validation import validate_finite, validate_matrix


Matrix = NDArray[np.float64]
MatrixInput = Sequence[Sequence[Real]] | NDArray[np.generic]

DEFAULT_MAX_CONDITION_NUMBER = 1e12


def create_matrix(values: MatrixInput, *, field: str = "matrix") -> Matrix:
    """Create a finite, rectangular Float64 matrix copy."""
    try:
        array = np.asarray(values)
    except (TypeError, ValueError) as exc:
        raise ScientificError(
            ScientificErrorCode.INVALID_SHAPE,
            "Matrix must be a rectangular numeric array.",
            field=field,
            expected="2D rectangular real matrix",
            received=type(values).__name__,
        ) from exc

    if array.ndim != 2:
        raise ScientificError(
            ScientificErrorCode.INVALID_SHAPE,
            "Matrix must have exactly two dimensions.",
            field=field,
            expected="2D matrix",
            received=array.shape,
        )

    if np.iscomplexobj(array):
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Matrix components must be real numbers.",
            field=field,
            expected="real numeric components",
            received="complex components",
        )

    if array.dtype.kind == "b":
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Boolean matrix components are not supported.",
            field=field,
            expected="real numeric components",
            received="boolean components",
        )

    try:
        with np.errstate(over="ignore", invalid="ignore"):
            converted = array.astype(np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Matrix components must be real numeric values.",
            field=field,
            expected="Float64-compatible real components",
            received=array.dtype.name,
        ) from exc

    validated = validate_matrix(converted.tolist(), field=field)
    return np.array(validated, dtype=np.float64, copy=True)


def _ensure_finite_result(values: NDArray[np.float64], *, operation: str) -> Matrix:
    if not np.all(np.isfinite(values)):
        raise ScientificError(
            ScientificErrorCode.NON_FINITE_VALUE,
            f"{operation} produced a non-finite result.",
            field=operation,
            expected="finite Float64 matrix",
            received=values.tolist(),
        )
    return np.array(values, dtype=np.float64, copy=True)


def _ensure_same_shape(left: Matrix, right: Matrix, *, operation: str) -> None:
    if left.shape != right.shape:
        raise ScientificError(
            ScientificErrorCode.INVALID_SHAPE,
            f"{operation} requires matrices with identical shapes.",
            field=operation,
            expected=left.shape,
            received=right.shape,
        )


def _ensure_square(matrix: Matrix, *, operation: str) -> None:
    if matrix.shape[0] != matrix.shape[1]:
        raise ScientificError(
            ScientificErrorCode.INVALID_SHAPE,
            f"{operation} requires a square matrix.",
            field=operation,
            expected="square matrix",
            received=matrix.shape,
        )


def _validate_condition_limit(max_condition_number: Real) -> float:
    limit = validate_finite(
        max_condition_number,
        field="max_condition_number",
    )
    if limit <= 1.0:
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Maximum condition number must be greater than one.",
            field="max_condition_number",
            expected="finite number greater than 1",
            received=limit,
        )
    return limit


def _check_condition(
    matrix: Matrix,
    *,
    operation: str,
    max_condition_number: Real,
) -> float:
    limit = _validate_condition_limit(max_condition_number)

    try:
        singular_values = np.linalg.svd(matrix, compute_uv=False)
    except np.linalg.LinAlgError as exc:
        raise ScientificError(
            ScientificErrorCode.SINGULAR_MATRIX,
            f"{operation} could not evaluate matrix rank.",
            field=operation,
        ) from exc

    largest = float(singular_values[0])
    smallest = float(singular_values[-1])

    rank_tolerance = (
        max(matrix.shape)
        * np.finfo(np.float64).eps
        * largest
    )

    if smallest <= rank_tolerance:
        raise ScientificError(
            ScientificErrorCode.SINGULAR_MATRIX,
            f"{operation} requires a numerically full-rank matrix.",
            field=operation,
            expected=f"smallest singular value > {rank_tolerance}",
            received=smallest,
            diagnostic={
                "singular_values": singular_values.tolist(),
                "rank_tolerance": rank_tolerance,
            },
        )

    condition_number = largest / smallest

    if condition_number > limit:
        raise ScientificError(
            ScientificErrorCode.UNCERTAIN_RESULT,
            f"{operation} rejected an ill-conditioned matrix.",
            field=operation,
            expected=f"condition number <= {limit}",
            received=condition_number,
            diagnostic={
                "condition_number": condition_number,
                "maximum_condition_number": limit,
                "singular_values": singular_values.tolist(),
            },
        )

    return condition_number


def add(left: MatrixInput, right: MatrixInput) -> Matrix:
    """Add matrices with identical shapes."""
    left_matrix = create_matrix(left, field="left")
    right_matrix = create_matrix(right, field="right")
    _ensure_same_shape(left_matrix, right_matrix, operation="add")

    with np.errstate(over="ignore", invalid="ignore"):
        result = left_matrix + right_matrix

    return _ensure_finite_result(result, operation="add")


def subtract(left: MatrixInput, right: MatrixInput) -> Matrix:
    """Subtract matrices with identical shapes."""
    left_matrix = create_matrix(left, field="left")
    right_matrix = create_matrix(right, field="right")
    _ensure_same_shape(left_matrix, right_matrix, operation="subtract")

    with np.errstate(over="ignore", invalid="ignore"):
        result = left_matrix - right_matrix

    return _ensure_finite_result(result, operation="subtract")


def multiply(left: MatrixInput, right: MatrixInput) -> Matrix:
    """Perform standard matrix multiplication (not element-wise multiplication)."""
    left_matrix = create_matrix(left, field="left")
    right_matrix = create_matrix(right, field="right")

    if left_matrix.shape[1] != right_matrix.shape[0]:
        raise ScientificError(
            ScientificErrorCode.INVALID_SHAPE,
            "Matrix multiplication requires matching inner dimensions.",
            field="multiply",
            expected=f"left columns = {right_matrix.shape[0]}",
            received=left_matrix.shape,
        )

    with np.errstate(over="ignore", invalid="ignore"):
        result = left_matrix @ right_matrix

    return _ensure_finite_result(result, operation="multiply")


def transpose(values: MatrixInput) -> Matrix:
    """Return a transposed matrix copy."""
    matrix = create_matrix(values)

    return np.array(matrix.T, dtype=np.float64, copy=True)


def determinant(values: MatrixInput) -> float:
    """Calculate the determinant of a square matrix."""
    matrix = create_matrix(values)
    _ensure_square(matrix, operation="determinant")

    try:
        with np.errstate(over="ignore", invalid="ignore"):
            result = float(np.linalg.det(matrix))
    except np.linalg.LinAlgError as exc:
        raise ScientificError(
            ScientificErrorCode.SINGULAR_MATRIX,
            "Determinant calculation failed.",
            field="determinant",
        ) from exc

    if not np.isfinite(result):
        raise ScientificError(
            ScientificErrorCode.NON_FINITE_VALUE,
            "Determinant produced a non-finite result.",
            field="determinant",
            received=result,
        )

    return result


def inverse(
    values: MatrixInput,
    *,
    max_condition_number: Real = DEFAULT_MAX_CONDITION_NUMBER,
) -> Matrix:
    """Calculate the inverse of a well-conditioned square matrix."""
    matrix = create_matrix(values)
    _ensure_square(matrix, operation="inverse")

    _check_condition(
        matrix,
        operation="inverse",
        max_condition_number=max_condition_number,
    )

    try:
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            result = np.linalg.inv(matrix)
    except np.linalg.LinAlgError as exc:
        raise ScientificError(
            ScientificErrorCode.SINGULAR_MATRIX,
            "Cannot invert a singular matrix.",
            field="inverse",
        ) from exc

    return _ensure_finite_result(result, operation="inverse")


def solve(
    coefficients: MatrixInput,
    right_hand_side: Sequence[Real] | NDArray[np.generic],
    *,
    max_condition_number: Real = DEFAULT_MAX_CONDITION_NUMBER,
) -> NDArray[np.float64]:
    """Solve a square linear system Ax = b."""
    matrix = create_matrix(coefficients, field="coefficients")

    _ensure_square(matrix, operation="solve")

    try:
        rhs_array = np.asarray(right_hand_side)
    except (TypeError, ValueError) as exc:
        raise ScientificError(
            ScientificErrorCode.INVALID_SHAPE,
            "Right-hand side must be a numeric vector.",
            field="right_hand_side",
        ) from exc

    if rhs_array.ndim != 1 or rhs_array.size != matrix.shape[0]:
        raise ScientificError(
            ScientificErrorCode.INVALID_SHAPE,
            "Right-hand side must be a vector matching matrix rows.",
            field="right_hand_side",
            expected=(matrix.shape[0],),
            received=rhs_array.shape,
        )

    if np.iscomplexobj(rhs_array) or rhs_array.dtype.kind == "b":
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Right-hand side must contain real numeric values.",
            field="right_hand_side",
        )

    try:
        with np.errstate(over="ignore", invalid="ignore"):
            rhs = rhs_array.astype(np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Right-hand side must contain real numeric values.",
            field="right_hand_side",
        ) from exc

    rhs = np.array(
        [validate_finite(value, field=f"right_hand_side[{index}]")
         for index, value in enumerate(rhs)],
        dtype=np.float64,
    )

    _check_condition(
        matrix,
        operation="solve",
        max_condition_number=max_condition_number,
    )

    try:
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            result = np.linalg.solve(matrix, rhs)
    except np.linalg.LinAlgError as exc:
        raise ScientificError(
            ScientificErrorCode.SINGULAR_MATRIX,
            "Linear system could not be solved.",
            field="solve",
        ) from exc

    if not np.all(np.isfinite(result)):
        raise ScientificError(
            ScientificErrorCode.NON_FINITE_VALUE,
            "Linear system produced a non-finite result.",
            field="solve",
            received=result.tolist(),
        )

    return np.array(result, dtype=np.float64, copy=True)
