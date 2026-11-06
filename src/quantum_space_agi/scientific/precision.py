from __future__ import annotations

import math
from numbers import Real
from typing import Final

from .errors import ScientificError, ScientificErrorCode


DEFAULT_ABSOLUTE_TOLERANCE: Final[float] = 1e-12
DEFAULT_RELATIVE_TOLERANCE: Final[float] = 1e-9


class ComparisonTolerance:
    """Configurable absolute and relative numerical comparison tolerances.

    These values are provisional ARC-04 defaults, not universal scientific
    standards. Domain-specific models may require different tolerances.
    """

    def __init__(
        self,
        *,
        atol: Real = DEFAULT_ABSOLUTE_TOLERANCE,
        rtol: Real = DEFAULT_RELATIVE_TOLERANCE,
    ) -> None:
        self.atol = _validate_tolerance(atol, field="atol")
        self.rtol = _validate_tolerance(rtol, field="rtol")

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(atol={self.atol!r}, "
            f"rtol={self.rtol!r})"
        )


def _validate_tolerance(value: Real, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Tolerance must be a real number.",
            field=field,
            expected="finite non-negative real number",
            received=type(value).__name__,
        )

    tolerance = float(value)
    if not math.isfinite(tolerance):
        raise ScientificError(
            ScientificErrorCode.NON_FINITE_VALUE,
            "Tolerance must be finite.",
            field=field,
            expected="finite non-negative tolerance",
            received=tolerance,
        )
    if tolerance < 0.0:
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Tolerance must not be negative.",
            field=field,
            expected="a non-negative tolerance",
            received=tolerance,
        )
    return tolerance


def _validate_comparison_input(value: Real, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Comparison input must be a real number.",
            field=field,
            expected="finite real number",
            received=type(value).__name__,
        )

    numeric_value = float(value)
    if not math.isfinite(numeric_value):
        raise ScientificError(
            ScientificErrorCode.NON_FINITE_VALUE,
            "Comparison input must be finite.",
            field=field,
            expected="a finite number",
            received=numeric_value,
        )
    return numeric_value


def is_close(
    actual: Real,
    expected: Real,
    *,
    tolerance: ComparisonTolerance | None = None,
    atol: Real | None = None,
    rtol: Real | None = None,
) -> bool:
    """Compare finite real values with combined absolute/relative tolerance."""
    actual_value = _validate_comparison_input(actual, field="actual")
    expected_value = _validate_comparison_input(expected, field="expected")

    if tolerance is not None:
        if atol is not None or rtol is not None:
            raise ScientificError(
                ScientificErrorCode.INVALID_STATE,
                "Use either tolerance or explicit atol/rtol values, not both.",
                field="tolerance",
                expected="one tolerance configuration style",
                received={
                    "tolerance_provided": True,
                    "atol_provided": atol is not None,
                    "rtol_provided": rtol is not None,
                },
            )
        configured_atol = tolerance.atol
        configured_rtol = tolerance.rtol
    else:
        configured_atol = (
            DEFAULT_ABSOLUTE_TOLERANCE if atol is None else _validate_tolerance(atol, field="atol")
        )
        configured_rtol = (
            DEFAULT_RELATIVE_TOLERANCE if rtol is None else _validate_tolerance(rtol, field="rtol")
        )

    threshold = configured_atol + configured_rtol * max(
        abs(actual_value),
        abs(expected_value),
    )
    difference = abs(actual_value - expected_value)
    if not math.isfinite(threshold) or not math.isfinite(difference):
        return False
    return difference <= threshold
