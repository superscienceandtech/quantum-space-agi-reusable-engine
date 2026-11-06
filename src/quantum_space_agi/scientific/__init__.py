"""Foundation utilities for scientific computing."""

from .errors import ScientificError, ScientificErrorCode
from .precision import ComparisonTolerance, is_close
from .validation import (
    validate_finite,
    validate_matrix,
    validate_vector,
)
from .vector import (
    add,
    create_vector,
    cross,
    distance,
    dot,
    magnitude,
    normalize,
    scale,
    subtract,
)

__all__ = [
    "ComparisonTolerance",
    "ScientificError",
    "ScientificErrorCode",
    "is_close",
    "validate_finite",
    "validate_matrix",
    "validate_vector",
    "add",
    "create_vector",
    "cross",
    "distance",
    "dot",
    "magnitude",
    "normalize",
    "scale",
    "subtract",
]
