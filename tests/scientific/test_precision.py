import math

import pytest

from quantum_space_agi.scientific.errors import ScientificError, ScientificErrorCode
from quantum_space_agi.scientific.precision import ComparisonTolerance, is_close


def test_is_close_accepts_normal_finite_values() -> None:
    assert is_close(1.0, 1.0 + 1e-10)


def test_is_close_supports_near_zero_comparison() -> None:
    assert is_close(1e-12, 0.0, atol=2e-12, rtol=0.0)
    assert not is_close(1e-8, 0.0, atol=1e-12, rtol=1e-9)


def test_is_close_supports_large_magnitude_comparison() -> None:
    assert is_close(1.0e12, 1.0e12 + 0.5, rtol=1e-9, atol=0.0)
    assert not is_close(1.0e12, 1.000001e12, rtol=1e-12, atol=0.0)


@pytest.mark.parametrize("tolerance", [-1e-12, -1.0])
def test_comparison_tolerance_rejects_negative_values(
    tolerance: float,
) -> None:
    with pytest.raises(ScientificError) as exc_info:
        ComparisonTolerance(atol=tolerance)

    assert exc_info.value.code is ScientificErrorCode.INVALID_STATE


@pytest.mark.parametrize("tolerance", [math.nan, math.inf, -math.inf])
def test_comparison_tolerance_rejects_non_finite_values(
    tolerance: float,
) -> None:
    with pytest.raises(ScientificError) as exc_info:
        ComparisonTolerance(rtol=tolerance)

    assert exc_info.value.code is ScientificErrorCode.NON_FINITE_VALUE


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_is_close_rejects_non_finite_inputs(value: float) -> None:
    with pytest.raises(ScientificError) as exc_info:
        is_close(value, 1.0)

    assert exc_info.value.code is ScientificErrorCode.NON_FINITE_VALUE


@pytest.mark.parametrize("value", ["1.0", True, None])
def test_is_close_rejects_invalid_numerical_inputs(value: object) -> None:
    with pytest.raises(ScientificError):
        is_close(value, 1.0)


def test_is_close_rejects_mixed_tolerance_configuration() -> None:
    tolerance = ComparisonTolerance(atol=1e-8, rtol=1e-6)
    with pytest.raises(ScientificError) as exc_info:
        is_close(1.0, 1.0 + 1e-8, tolerance=tolerance, rtol=1e-9)

    assert exc_info.value.code is ScientificErrorCode.INVALID_STATE


@pytest.mark.parametrize(
    ("actual", "expected", "atol", "rtol"),
    [
        (1e308, -1e308, 0.0, 1e308),
        (1e308, -1e308, 1e308, 2.0),
    ],
)
def test_is_close_does_not_report_overflowing_comparison_as_close(
    actual: float,
    expected: float,
    atol: float,
    rtol: float,
) -> None:
    assert not is_close(actual, expected, atol=atol, rtol=rtol)
