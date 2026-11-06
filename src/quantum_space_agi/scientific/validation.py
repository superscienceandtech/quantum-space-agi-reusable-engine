from __future__ import annotations

import math
from numbers import Real
from typing import Sequence

from .errors import ScientificError, ScientificErrorCode


def validate_finite(value: Real, *, field: str = "value") -> float:
    """Convert a real scalar to float and reject non-finite values."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Value must be a real number.",
            field=field,
            expected="finite real number",
            received=type(value).__name__,
        )

    result = float(value)
    if not math.isfinite(result):
        raise ScientificError(
            ScientificErrorCode.NON_FINITE_VALUE,
            "Value must be finite.",
            field=field,
            expected="a finite number",
            received=result,
        )
    return result


def validate_vector(
    values: Sequence[Real],
    *,
    allowed_dimensions: Sequence[int] = (2, 3),
    field: str = "vector",
) -> tuple[float, ...]:
    """Validate a 2D or 3D vector and return it as a float tuple."""
    if isinstance(values, (str, bytes)):
        raise ScientificError(
            ScientificErrorCode.INVALID_DIMENSION,
            "Vector values must be a one-dimensional numeric sequence.",
            field=field,
            expected="numeric sequence",
            received=type(values).__name__,
        )

    try:
        length = len(values)
    except TypeError as exc:
        raise ScientificError(
            ScientificErrorCode.INVALID_DIMENSION,
            "Vector values must have a measurable dimension.",
            field=field,
            expected="sequence with finite length",
            received=type(values).__name__,
        ) from exc

    allowed = tuple(allowed_dimensions)
    if length not in allowed:
        raise ScientificError(
            ScientificErrorCode.INVALID_DIMENSION,
            "Vector dimension is not supported.",
            field=field,
            expected=f"one of {allowed}",
            received=length,
        )

    return tuple(
        validate_finite(value, field=f"{field}[{index}]")
        for index, value in enumerate(values)
    )


def validate_matrix(
    values: Sequence[Sequence[Real]],
    *,
    field: str = "matrix",
) -> tuple[tuple[float, ...], ...]:
    """Validate a non-empty rectangular matrix and return a float tuple."""
    if isinstance(values, (str, bytes)):
        raise ScientificError(
            ScientificErrorCode.INVALID_SHAPE,
            "Matrix values must be a sequence of rows.",
            field=field,
            expected="rectangular sequence of sequences",
            received=type(values).__name__,
        )

    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ScientificError(
            ScientificErrorCode.INVALID_SHAPE,
            "Matrix values must be an iterable sequence of rows.",
            field=field,
            expected="rectangular sequence of sequences",
            received=type(values).__name__,
        ) from exc

    if not rows:
        raise ScientificError(
            ScientificErrorCode.INVALID_SHAPE,
            "Matrix must contain at least one row.",
            field=field,
            expected="at least 1 row",
            received=0,
        )

    widths: list[int] = []
    validated_rows: list[tuple[float, ...]] = []
    for row_index, row in enumerate(rows):
        if isinstance(row, (str, bytes)):
            raise ScientificError(
                ScientificErrorCode.INVALID_SHAPE,
                "Matrix rows must be numeric sequences.",
                field=f"{field}[{row_index}]",
                expected="numeric row sequence",
                received=type(row).__name__,
            )
        try:
            row_values = tuple(row)
        except TypeError as exc:
            raise ScientificError(
                ScientificErrorCode.INVALID_SHAPE,
                "Matrix row must be iterable.",
                field=f"{field}[{row_index}]",
                expected="numeric row sequence",
                received=type(row).__name__,
            ) from exc
        widths.append(len(row_values))
        validated_rows.append(
            tuple(
                validate_finite(value, field=f"{field}[{row_index}][{column_index}]")
                for column_index, value in enumerate(row_values)
            )
        )

    if not widths[0] or len(set(widths)) != 1:
        raise ScientificError(
            ScientificErrorCode.INVALID_SHAPE,
            "Matrix must be rectangular with no empty or unequal rows.",
            field=field,
            expected=f"all rows have {widths[0]} columns",
            received=widths,
        )

    return tuple(validated_rows)
