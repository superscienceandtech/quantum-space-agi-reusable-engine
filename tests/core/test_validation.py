import math

import pytest

from quantum_space_agi.core import (
    validate_finite_real,
    validate_non_empty_text,
    validate_non_negative_real,
    validate_positive_real,
)
from quantum_space_agi.errors import ValidationError


@pytest.mark.parametrize("text", ["space", "  space mission  "])
def test_validate_non_empty_text_returns_original_text(text: str) -> None:
    assert validate_non_empty_text(text) == text


@pytest.mark.parametrize("text", ["", " ", "\t\n"])
def test_validate_non_empty_text_rejects_empty_or_whitespace(text: str) -> None:
    with pytest.raises(ValidationError, match="must not be empty"):
        validate_non_empty_text(text, name="label")


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_validate_finite_real_rejects_non_finite_values(value: float) -> None:
    with pytest.raises(ValidationError, match="must be finite"):
        validate_finite_real(value, name="measurement")


@pytest.mark.parametrize(("value", "expected"), [(2, 2.0), (2.5, 2.5), (0, 0.0)])
def test_validate_finite_real_accepts_finite_values(
    value: int | float, expected: float
) -> None:
    assert validate_finite_real(value) == expected


@pytest.mark.parametrize("value", [0.1, 1, 2.5])
def test_validate_positive_real_accepts_positive_values(value: int | float) -> None:
    assert validate_positive_real(value) == float(value)


@pytest.mark.parametrize("value", [0, -0.1, -2])
def test_validate_positive_real_rejects_zero_and_negative_values(
    value: int | float,
) -> None:
    with pytest.raises(ValidationError, match="must be positive"):
        validate_positive_real(value, name="duration")


@pytest.mark.parametrize("value", [0, 0.1, 2])
def test_validate_non_negative_real_accepts_zero_and_positive_values(
    value: int | float,
) -> None:
    assert validate_non_negative_real(value) == float(value)


@pytest.mark.parametrize("value", [-0.1, -2])
def test_validate_non_negative_real_rejects_negative_values(
    value: int | float,
) -> None:
    with pytest.raises(ValidationError, match="must be non-negative"):
        validate_non_negative_real(value, name="count")


@pytest.mark.parametrize("value", [None, True, "1.5", 1j, object()])
def test_validate_finite_real_rejects_wrong_types(value: object) -> None:
    with pytest.raises(ValidationError, match="must be a real number"):
        validate_finite_real(value)


@pytest.mark.parametrize("value", [None, 1, object()])
def test_validate_non_empty_text_rejects_wrong_types(value: object) -> None:
    with pytest.raises(ValidationError, match="must be a string"):
        validate_non_empty_text(value)


def test_validation_error_includes_argument_name_and_value_condition() -> None:
    with pytest.raises(ValidationError, match="mass must be finite"):
        validate_finite_real(math.inf, name="mass")
