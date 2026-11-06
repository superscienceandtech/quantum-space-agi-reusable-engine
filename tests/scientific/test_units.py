import pytest

from quantum_space_agi.scientific.errors import (
    ScientificError,
    ScientificErrorCode,
)
from quantum_space_agi.scientific.units import (
    Quantity,
    Unit,
    convert,
    get_unit,
    is_compatible,
)


def test_get_registered_unit():
    assert get_unit("km").symbol == "km"
    assert get_unit("m").scale_to_si == 1.0


def test_convert_kilometers_to_meters():
    result = convert(Quantity(5, get_unit("km")), "m")
    assert result.value == pytest.approx(5000)
    assert result.unit.symbol == "m"


def test_convert_kilometers_per_hour_to_meters_per_second():
    result = convert(Quantity(36, get_unit("km/h")), "m/s")
    assert result.value == pytest.approx(10)


def test_convert_hours_to_seconds():
    result = convert(Quantity(2, get_unit("h")), "s")
    assert result.value == pytest.approx(7200)


def test_compatible_units():
    assert is_compatible("km", "m")
    assert is_compatible("h", "s")
    assert is_compatible("km/h", "m/s")


def test_incompatible_units():
    assert not is_compatible("km", "s")
    assert not is_compatible("kg", "N")


def test_conversion_rejects_incompatible_units():
    with pytest.raises(ScientificError) as exc:
        convert(Quantity(5, get_unit("km")), "s")

    assert exc.value.code == ScientificErrorCode.UNIT_MISMATCH


def test_unknown_unit_is_rejected():
    with pytest.raises(ScientificError):
        get_unit("lightyear")


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), True])
def test_quantity_rejects_invalid_values(value):
    with pytest.raises(ScientificError):
        Quantity(value, get_unit("m"))


def test_unit_is_immutable():
    unit = get_unit("m")

    with pytest.raises(AttributeError):
        unit.symbol = "km"


def test_quantity_is_immutable():
    quantity = Quantity(10, get_unit("m"))

    with pytest.raises(AttributeError):
        quantity.value = 20


def test_custom_unit():
    custom = Unit("millimeter", 0.001, (1, 0, 0, 0, 0, 0, 0))
    result = convert(Quantity(1000, custom), "m")

    assert result.value == pytest.approx(1)
