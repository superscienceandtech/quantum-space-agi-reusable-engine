"""Float64 2D and 3D numeric vector operations.

This module does not provide unit or coordinate-frame metadata. Callers must
coordinate those concerns before combining values through a future quantity
or frame-aware interface. The operations below are numeric only.
"""

from __future__ import annotations

import math
from numbers import Real
from typing import Any, Sequence

import numpy as np
from numpy.typing import NDArray

from .errors import ScientificError, ScientificErrorCode
from .validation import validate_finite, validate_vector


Vector = NDArray[np.float64]
VectorInput = Sequence[Real] | NDArray[np.generic]


def create_vector(values: VectorInput, *, field: str = "vector") -> Vector:
    """Construct a copy of a finite, two- or three-dimensional Float64 vector."""
    try:
        array = np.asarray(values)
    except (TypeError, ValueError) as exc:
        raise ScientificError(
            ScientificErrorCode.INVALID_DIMENSION,
            "Vector values must be a one-dimensional numeric sequence.",
            field=field,
            expected="a 2D or 3D numeric sequence",
            received=type(values).__name__,
        ) from exc

    if array.ndim != 1:
        raise ScientificError(
            ScientificErrorCode.INVALID_DIMENSION,
            "Vector values must be one-dimensional.",
            field=field,
            expected="a 2D or 3D numeric sequence",
            received=array.shape,
        )
    if np.iscomplexobj(array):
        raise ScientificError(
            ScientificErrorCode.INVALID_DIMENSION,
            "Vector components must be real numbers.",
            field=field,
            expected="real numeric components",
            received="complex components",
        )
    if array.dtype.kind in "biu":
        # Boolean values are deliberately sent through validation and rejected
        # as invalid scalar state rather than being converted to 0 or 1.
        if array.dtype.kind == "b":
            validated = validate_vector(array.tolist(), field=field)
        else:
            with np.errstate(over="ignore", invalid="ignore"):
                converted = array.astype(np.float64)
            validated = validate_vector(converted.tolist(), field=field)
    elif array.dtype.kind == "f":
        with np.errstate(over="ignore", invalid="ignore"):
            converted = array.astype(np.float64)
        validated = validate_vector(converted.tolist(), field=field)
    else:
        validated = validate_vector(array.tolist(), field=field)
    return np.array(validated, dtype=np.float64, copy=True)


def _as_vector(values: VectorInput, *, field: str) -> Vector:
    return create_vector(values, field=field)


def _ensure_same_dimension(
    left: Vector,
    right: Vector,
    *,
    operation: str,
) -> None:
    if left.size != right.size:
        raise ScientificError(
            ScientificErrorCode.INVALID_DIMENSION,
            f"{operation} requires vectors with matching dimensions.",
            field=operation,
            expected=left.size,
            received=right.size,
        )


def _ensure_finite_array(values: NDArray[np.float64], *, operation: str) -> Vector:
    if not np.all(np.isfinite(values)):
        raise ScientificError(
            ScientificErrorCode.NON_FINITE_VALUE,
            f"{operation} produced a non-finite result.",
            field=operation,
            expected="all finite Float64 components",
            received=values.tolist(),
        )
    return np.array(values, dtype=np.float64, copy=True)


def _ensure_finite_scalar(value: float, *, operation: str) -> float:
    return validate_finite(float(value), field=operation)


def _validate_scalar(scalar: Real | np.floating[Any], *, field: str = "scalar") -> float:
    if isinstance(scalar, bool) or not isinstance(
        scalar,
        (Real, np.integer, np.floating),
    ):
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Scalar must be a real number.",
            field=field,
            expected="finite real scalar",
            received=type(scalar).__name__,
        )
    return validate_finite(float(scalar), field=field)


def add(left: VectorInput, right: VectorInput) -> Vector:
    """Add two numeric vectors of matching dimensions."""
    left_vector = _as_vector(left, field="left")
    right_vector = _as_vector(right, field="right")
    _ensure_same_dimension(left_vector, right_vector, operation="add")
    with np.errstate(over="ignore", invalid="ignore"):
        result = left_vector + right_vector
    return _ensure_finite_array(result, operation="add")


def subtract(left: VectorInput, right: VectorInput) -> Vector:
    """Subtract two numeric vectors of matching dimensions."""
    left_vector = _as_vector(left, field="left")
    right_vector = _as_vector(right, field="right")
    _ensure_same_dimension(left_vector, right_vector, operation="subtract")
    with np.errstate(over="ignore", invalid="ignore"):
        result = left_vector - right_vector
    return _ensure_finite_array(result, operation="subtract")


def scale(vector_values: VectorInput, scalar: Real | np.floating[Any]) -> Vector:
    """Multiply every component of a numeric vector by a finite real scalar."""
    vector_value = _as_vector(vector_values, field="vector")
    scalar_value = _validate_scalar(scalar)
    with np.errstate(over="ignore", invalid="ignore"):
        result = vector_value * scalar_value
    return _ensure_finite_array(result, operation="scale")


def dot(left: VectorInput, right: VectorInput) -> float:
    """Calculate the dot product of two vectors with matching dimensions."""
    left_vector = _as_vector(left, field="left")
    right_vector = _as_vector(right, field="right")
    _ensure_same_dimension(left_vector, right_vector, operation="dot")
    with np.errstate(over="ignore", invalid="ignore"):
        result = np.dot(left_vector, right_vector)
    return _ensure_finite_scalar(float(result), operation="dot")


def cross(left: VectorInput, right: VectorInput) -> Vector:
    """Calculate the right-hand-rule cross product of two 3D vectors."""
    left_vector = _as_vector(left, field="left")
    right_vector = _as_vector(right, field="right")
    if left_vector.size != 3 or right_vector.size != 3:
        raise ScientificError(
            ScientificErrorCode.INVALID_DIMENSION,
            "Cross product requires exactly three-dimensional vectors.",
            field="cross",
            expected=(3, 3),
            received=(left_vector.size, right_vector.size),
        )
    with np.errstate(over="ignore", invalid="ignore"):
        result = np.cross(left_vector, right_vector)
    return _ensure_finite_array(result, operation="cross")


def magnitude(vector_values: VectorInput) -> float:
    """Calculate vector magnitude with overflow-resistant summation."""
    vector_value = _as_vector(vector_values, field="vector")
    result = math.hypot(*(float(component) for component in vector_value))
    if not math.isfinite(result):
        raise ScientificError(
            ScientificErrorCode.NON_FINITE_VALUE,
            "Magnitude produced a non-finite result.",
            field="magnitude",
            expected="finite magnitude",
            received=result,
        )
    return result


def normalize(vector_values: VectorInput) -> Vector:
    """Return a unit vector in the same direction; reject a zero vector."""
    vector_value = _as_vector(vector_values, field="vector")
    vector_magnitude = magnitude(vector_value)
    if vector_magnitude == 0.0:
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Cannot normalize a zero vector.",
            field="normalize",
            expected="non-zero vector",
            received=vector_magnitude,
        )
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        result = vector_value / vector_magnitude
    return _ensure_finite_array(result, operation="normalize")


def distance(left: VectorInput, right: VectorInput) -> float:
    """Calculate distance between two vectors of matching dimensions."""
    left_vector = _as_vector(left, field="left")
    right_vector = _as_vector(right, field="right")
    _ensure_same_dimension(left_vector, right_vector, operation="distance")
    with np.errstate(over="ignore", invalid="ignore"):
        difference = left_vector - right_vector
    difference = _ensure_finite_array(difference, operation="distance")
    return magnitude(difference)
