"""Common result, validation, and numerical utility APIs."""

from quantum_space_agi.core.numerics import Tolerance, is_close
from quantum_space_agi.core.results import ErrorInfo, Result, ResultStatus
from quantum_space_agi.core.validation import (
    validate_finite_real,
    validate_non_empty_text,
    validate_non_negative_real,
    validate_positive_real,
)

__all__ = [
    "ErrorInfo",
    "Result",
    "ResultStatus",
    "Tolerance",
    "is_close",
    "validate_finite_real",
    "validate_non_empty_text",
    "validate_non_negative_real",
    "validate_positive_real",
]
