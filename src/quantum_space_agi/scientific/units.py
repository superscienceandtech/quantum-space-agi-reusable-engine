"""SI-based units and physical quantities."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import ScientificError, ScientificErrorCode
from .validation import validate_finite


# SI base-dimension order: length, mass, time, current,
# temperature, amount of substance, luminous intensity.
Dimensions = tuple[int, int, int, int, int, int, int]


@dataclass(frozen=True, slots=True)
class Unit:
    """A unit represented by its SI conversion scale and dimensions."""

    symbol: str
    scale_to_si: float
    dimensions: Dimensions

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str) or not self.symbol.strip():
            raise ScientificError(
                ScientificErrorCode.INVALID_STATE,
                "Unit symbol must be a non-empty string.",
                field="symbol",
                received=self.symbol,
            )

        scale = validate_finite(self.scale_to_si, field="scale_to_si")
        if scale <= 0:
            raise ScientificError(
                ScientificErrorCode.INVALID_STATE,
                "Unit scale must be greater than zero.",
                field="scale_to_si",
                expected="positive finite number",
                received=scale,
            )

        if (
            not isinstance(self.dimensions, tuple)
            or len(self.dimensions) != 7
            or any(type(value) is not int for value in self.dimensions)
        ):
            raise ScientificError(
                ScientificErrorCode.INVALID_STATE,
                "Unit dimensions must be a seven-element integer tuple.",
                field="dimensions",
                expected="seven integer exponents",
                received=self.dimensions,
            )

        object.__setattr__(self, "scale_to_si", scale)


@dataclass(frozen=True, slots=True)
class Quantity:
    """A finite numerical value associated with a physical unit."""

    value: float
    unit: Unit

    def __post_init__(self) -> None:
        if not isinstance(self.unit, Unit):
            raise ScientificError(
                ScientificErrorCode.INVALID_STATE,
                "Quantity must contain a Unit instance.",
                field="unit",
                expected="Unit",
                received=type(self.unit).__name__,
            )

        object.__setattr__(
            self,
            "value",
            validate_finite(self.value, field="value"),
        )


# Seven SI base dimensions: L, M, T, I, Θ, N, J.
_LENGTH = (1, 0, 0, 0, 0, 0, 0)
_MASS = (0, 1, 0, 0, 0, 0, 0)
_TIME = (0, 0, 1, 0, 0, 0, 0)
_VELOCITY = (1, 0, -1, 0, 0, 0, 0)
_ACCELERATION = (1, 0, -2, 0, 0, 0, 0)
_FORCE = (1, 1, -2, 0, 0, 0, 0)
_ENERGY = (2, 1, -2, 0, 0, 0, 0)


UNIT_REGISTRY: dict[str, Unit] = {
    "m": Unit("m", 1.0, _LENGTH),
    "km": Unit("km", 1000.0, _LENGTH),
    "cm": Unit("cm", 0.01, _LENGTH),
    "s": Unit("s", 1.0, _TIME),
    "min": Unit("min", 60.0, _TIME),
    "h": Unit("h", 3600.0, _TIME),
    "kg": Unit("kg", 1.0, _MASS),
    "g": Unit("g", 0.001, _MASS),
    "m/s": Unit("m/s", 1.0, _VELOCITY),
    "km/h": Unit("km/h", 1000.0 / 3600.0, _VELOCITY),
    "m/s^2": Unit("m/s^2", 1.0, _ACCELERATION),
    "N": Unit("N", 1.0, _FORCE),
    "J": Unit("J", 1.0, _ENERGY),
}


def get_unit(unit: str | Unit) -> Unit:
    """Resolve a registered unit symbol or return a Unit instance."""
    if isinstance(unit, Unit):
        return unit

    if not isinstance(unit, str) or unit not in UNIT_REGISTRY:
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Unknown or invalid unit.",
            field="unit",
            expected=tuple(UNIT_REGISTRY),
            received=unit,
        )

    return UNIT_REGISTRY[unit]


def is_compatible(unit_a: str | Unit, unit_b: str | Unit) -> bool:
    """Return whether two units represent the same physical dimensions."""
    first = get_unit(unit_a)
    second = get_unit(unit_b)
    return first.dimensions == second.dimensions


def convert(quantity: Quantity, target_unit: str | Unit) -> Quantity:
    """Convert a quantity to another unit with compatible dimensions."""
    if not isinstance(quantity, Quantity):
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Input must be a Quantity instance.",
            field="quantity",
            expected="Quantity",
            received=type(quantity).__name__,
        )

    target = get_unit(target_unit)

    if not is_compatible(quantity.unit, target):
        raise ScientificError(
            ScientificErrorCode.UNIT_MISMATCH,
            "Cannot convert between physically incompatible units.",
            field="target_unit",
            expected=quantity.unit.dimensions,
            received=target.dimensions,
        )

    converted_value = (
        quantity.value * quantity.unit.scale_to_si / target.scale_to_si
    )

    return Quantity(converted_value, target)
