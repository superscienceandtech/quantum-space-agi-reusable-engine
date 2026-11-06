from __future__ import annotations

from enum import Enum
from typing import Any


class ScientificErrorCode(str, Enum):
    INVALID_DIMENSION = "invalid_dimension"
    INVALID_SHAPE = "invalid_shape"
    NON_FINITE_VALUE = "non_finite_value"
    UNIT_MISMATCH = "unit_mismatch"
    FRAME_MISMATCH = "frame_mismatch"
    SINGULAR_MATRIX = "singular_matrix"
    UNCERTAIN_RESULT = "uncertain_result"
    INVALID_STATE = "invalid_state"


class ScientificError(ValueError):
    """Structured error raised at scientific utility boundaries."""

    def __init__(
        self,
        code: ScientificErrorCode,
        message: str,
        *,
        field: str | None = None,
        expected: Any | None = None,
        received: Any | None = None,
        diagnostic: Any | None = None,
    ) -> None:
        self.code = code
        self.field = field
        self.expected = expected
        self.received = received
        self.diagnostic = diagnostic
        super().__init__(message)

    def __str__(self) -> str:
        details: list[str] = []
        if self.field is not None:
            details.append(f"field={self.field}")
        if self.expected is not None:
            details.append(f"expected={self.expected!r}")
        if self.received is not None:
            details.append(f"received={self.received!r}")
        if self.diagnostic is not None:
            details.append(f"diagnostic={self.diagnostic!r}")
        suffix = "; ".join(details)
        return f"{self.code.value}: {super().__str__()}" + (
            f" ({suffix})" if suffix else ""
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code.value,
            "message": super().__str__(),
            "field": self.field,
            "expected": self.expected,
            "received": self.received,
            "diagnostic": self.diagnostic,
        }

