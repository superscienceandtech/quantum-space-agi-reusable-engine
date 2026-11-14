"""Shared structured scientific exception types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ScientificErrorCode(str, Enum):
    """Domain-specific validation error categories for scientific utilities."""

    INVALID_STATE = "INVALID_STATE"
    INVALID_SHAPE = "INVALID_SHAPE"
    NON_FINITE_VALUE = "NON_FINITE_VALUE"
    UNIT_MISMATCH = "UNIT_MISMATCH"
    FRAME_MISMATCH = "FRAME_MISMATCH"


@dataclass(frozen=True, slots=True)
class ScientificError(ValueError):
    """ValueError carrying structured metadata for scientific validation failures."""

    code: ScientificErrorCode
    message: str
    field: str | None = None
    expected: Any = None
    received: Any = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, ScientificErrorCode):
            object.__setattr__(self, "code", ScientificErrorCode(self.code))

    def __str__(self) -> str:
        detail = f"{self.message}"
        if self.field is not None:
            detail += f" (field={self.field})"
        if self.expected is not None:
            detail += f" expected={self.expected!r}"
        if self.received is not None:
            detail += f" received={self.received!r}"
        return detail
