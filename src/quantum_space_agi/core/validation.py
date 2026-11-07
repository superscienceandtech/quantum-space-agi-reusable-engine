"""Reusable validation for common scalar input constraints."""

from __future__ import annotations

import math
from numbers import Real

from quantum_space_agi.errors import ValidationError


def validate_non_empty_text(value: object, *, name: str = "value") -> str:
    """Return text that contains non-whitespace characters."""
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be a string")
    if not value.strip():
        raise ValidationError(f"{name} must not be empty")
    return value


def validate_finite_real(value: object, *, name: str = "value") -> float:
    """Return a finite real number as ``float``.

    Booleans and values that cannot be represented as a finite float are rejected.
    """
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValidationError(f"{name} must be a real number")

    try:
        converted = float(value)
    except OverflowError as exc:
        raise ValidationError(f"{name} must be finite") from exc
    if not math.isfinite(converted):
        raise ValidationError(f"{name} must be finite")
    return converted


def validate_positive_real(value: object, *, name: str = "value") -> float:
    """Return a finite real number greater than zero."""
    converted = validate_finite_real(value, name=name)
    if converted <= 0.0:
        raise ValidationError(f"{name} must be positive")
    return converted


def validate_non_negative_real(value: object, *, name: str = "value") -> float:
    """Return a finite real number greater than or equal to zero."""
    converted = validate_finite_real(value, name=name)
    if converted < 0.0:
        raise ValidationError(f"{name} must be non-negative")
    return converted
