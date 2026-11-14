"""Dimensioned unit definitions used by scientific coordinate frames."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .errors import ScientificError, ScientificErrorCode


@dataclass(frozen=True, slots=True)
class Unit:
    """A scalar unit with a symbol, scale factor, and physical dimensions."""

    symbol: str
    name: str
    scale: float
    dimensions: tuple[int, int, int, int, int, int, int]

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str) or not self.symbol.strip():
            raise ScientificError(
                ScientificErrorCode.INVALID_STATE,
                "Unit symbol must be a non-empty string.",
                field="symbol",
                expected="unit symbol",
                received=self.symbol,
            )
        if not isinstance(self.name, str) or not self.name.strip():
            raise ScientificError(
                ScientificErrorCode.INVALID_STATE,
                "Unit name must be a non-empty string.",
                field="name",
                expected="unit name",
                received=self.name,
            )
        if not isinstance(self.scale, (int, float)) or not (float(self.scale) > 0.0):
            raise ScientificError(
                ScientificErrorCode.INVALID_STATE,
                "Unit scale must be a positive finite real number.",
                field="scale",
                expected="positive finite real scale",
                received=self.scale,
            )
        if len(self.dimensions) != 7:
            raise ScientificError(
                ScientificErrorCode.INVALID_SHAPE,
                "Dimensions must contain seven exponents.",
                field="dimensions",
                expected="7 values",
                received=len(self.dimensions),
            )
        object.__setattr__(self, "symbol", self.symbol.strip())
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "scale", float(self.scale))
        object.__setattr__(self, "dimensions", tuple(int(v) for v in self.dimensions))

    def __str__(self) -> str:
        return self.symbol


_LENGTH_DIMENSIONS: Final = (1, 0, 0, 0, 0, 0, 0)
_TIME_DIMENSIONS: Final = (0, 1, 0, 0, 0, 0, 0)
_VELOCITY_DIMENSIONS: Final = (1, -1, 0, 0, 0, 0, 0)

_UNIT_TABLE: dict[str, Unit] = {
    "m": Unit("m", "metre", 1.0, _LENGTH_DIMENSIONS),
    "meter": Unit("m", "metre", 1.0, _LENGTH_DIMENSIONS),
    "metre": Unit("m", "metre", 1.0, _LENGTH_DIMENSIONS),
    "km": Unit("km", "kilometre", 1000.0, _LENGTH_DIMENSIONS),
    "kilometer": Unit("km", "kilometre", 1000.0, _LENGTH_DIMENSIONS),
    "kilometre": Unit("km", "kilometre", 1000.0, _LENGTH_DIMENSIONS),
    "mm": Unit("mm", "millimetre", 1.0e-3, _LENGTH_DIMENSIONS),
    "s": Unit("s", "second", 1.0, _TIME_DIMENSIONS),
    "sec": Unit("s", "second", 1.0, _TIME_DIMENSIONS),
    "second": Unit("s", "second", 1.0, _TIME_DIMENSIONS),
    "m/s": Unit("m/s", "metres per second", 1.0, _VELOCITY_DIMENSIONS),
    "mps": Unit("m/s", "metres per second", 1.0, _VELOCITY_DIMENSIONS),
    "m/s": Unit("m/s", "metres per second", 1.0, _VELOCITY_DIMENSIONS),
    "km/s": Unit("km/s", "kilometres per second", 1000.0, _VELOCITY_DIMENSIONS),
    "kmps": Unit("km/s", "kilometres per second", 1000.0, _VELOCITY_DIMENSIONS),
}

for _unit in list(_UNIT_TABLE.values()):
    _UNIT_TABLE.setdefault(_unit.symbol.lower(), _unit)
    _UNIT_TABLE.setdefault(_unit.name.lower(), _unit)


def get_unit(symbol: str) -> Unit:
    """Lookup a registered scientific unit by symbol or name."""

    if not isinstance(symbol, str):
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Unit identifier must be a string.",
            field="symbol",
            expected="unit symbol or name",
            received=type(symbol).__name__,
        )
    key = symbol.strip().lower()
    if key not in _UNIT_TABLE:
        raise ScientificError(
            ScientificErrorCode.INVALID_STATE,
            "Unsupported unit.",
            field="symbol",
            expected="known scientific unit",
            received=symbol,
        )
    return _UNIT_TABLE[key]


__all__ = ["Unit", "get_unit"]
