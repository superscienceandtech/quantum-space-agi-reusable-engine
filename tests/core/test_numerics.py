import math

import pytest

from quantum_space_agi.core import Tolerance, is_close
from quantum_space_agi.errors import ValidationError


def test_is_close_accepts_exactly_equal_values() -> None:
    assert is_close(1.25, 1.25)


def test_is_close_accepts_values_within_absolute_tolerance() -> None:
    assert is_close(0.0, 0.005, tolerance=Tolerance(abs_tol=0.01, rel_tol=0.0))


def test_is_close_rejects_values_outside_absolute_tolerance() -> None:
    assert not is_close(0.0, 0.02, tolerance=Tolerance(abs_tol=0.01, rel_tol=0.0))


def test_is_close_uses_relative_tolerance_for_nonzero_values() -> None:
    assert is_close(100.0, 100.5, tolerance=Tolerance(rel_tol=0.01, abs_tol=0.0))


def test_is_close_rejects_difference_outside_relative_tolerance() -> None:
    assert not is_close(100.0, 102.0, tolerance=Tolerance(rel_tol=0.01, abs_tol=0.0))


def test_is_close_compares_zero_using_absolute_tolerance() -> None:
    assert not is_close(0.0, 1e-10)
    assert is_close(0.0, 1e-10, tolerance=Tolerance(abs_tol=1e-10))


def test_is_close_follows_standard_nan_and_infinity_semantics() -> None:
    assert not is_close(math.nan, math.nan)
    assert is_close(math.inf, math.inf)
    assert is_close(-math.inf, -math.inf)
    assert not is_close(math.inf, -math.inf)
    assert not is_close(math.inf, 1.0)


@pytest.mark.parametrize(
    ("rel_tol", "abs_tol"),
    [
        (-1.0, 0.0),
        (0.0, -1.0),
        (math.nan, 0.0),
        (0.0, math.inf),
        (True, 0.0),
    ],
)
def test_tolerance_rejects_invalid_values(rel_tol: float, abs_tol: float) -> None:
    with pytest.raises(ValidationError):
        Tolerance(rel_tol=rel_tol, abs_tol=abs_tol)


def test_tolerance_is_immutable() -> None:
    tolerance = Tolerance(abs_tol=0.1)

    with pytest.raises(AttributeError):
        tolerance.abs_tol = 0.2  # type: ignore[misc]


def test_tolerance_documents_math_isclose_parameter_order() -> None:
    tolerance = Tolerance()

    assert tolerance.rel_tol == 1e-9
    assert tolerance.abs_tol == 0.0
