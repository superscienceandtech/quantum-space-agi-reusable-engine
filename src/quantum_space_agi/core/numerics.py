"""Scalar floating-point comparison utilities."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real

from quantum_space_agi.core.validation import validate_non_negative_real
from quantum_space_agi.errors import ValidationError


@dataclass(frozen=True, slots=True)
class Tolerance:
    """Finite, non-negative relative and absolute comparison tolerances.

    Defaults match :func:`math.isclose`: relative tolerance ``1e-9`` and zero
    absolute tolerance.
    """

    rel_tol: float = 1e-9
    abs_tol: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "rel_tol", validate_non_negative_real(self.rel_tol, name="rel_tol")
        )
        object.__setattr__(
            self, "abs_tol", validate_non_negative_real(self.abs_tol, name="abs_tol")
        )


def is_close(a: float, b: float, *, tolerance: Tolerance | None = None) -> bool:
    """Compare two scalar values using :func:`math.isclose` semantics.

    Values are close when their absolute difference is no greater than the
    larger of the relative tolerance times the larger magnitude and the
    absolute tolerance. The absolute tolerance therefore governs comparisons
    near zero. NaN is never close, including to itself; equal signed infinities
    are close, while unequal infinities are not.

    Args:
        a: First real scalar.
        b: Second real scalar.
        tolerance: Relative and absolute tolerance; defaults to
            ``rel_tol=1e-9`` and ``abs_tol=0.0``.

    Raises:
        ValidationError: If either value is not a real, non-boolean scalar.
    """
    first = _as_float(a, name="a")
    second = _as_float(b, name="b")
    selected_tolerance = Tolerance() if tolerance is None else tolerance
    if not isinstance(selected_tolerance, Tolerance):
        raise ValidationError("tolerance must be a Tolerance")
    return math.isclose(
        first,
        second,
        rel_tol=selected_tolerance.rel_tol,
        abs_tol=selected_tolerance.abs_tol,
    )


def _as_float(value: object, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValidationError(f"{name} must be a real number")
    try:
        return float(value)
    except OverflowError as exc:
        raise ValidationError(f"{name} must be representable as a float") from exc
