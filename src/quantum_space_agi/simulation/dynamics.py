from __future__ import annotations

import math
from typing import Any

import numpy as np
from numpy.typing import NDArray


def _numeric_state(state: Any) -> NDArray[np.float64]:
    if isinstance(state, (str, bytes, bytearray, bool, np.bool_)):
        raise ValueError("State must be numeric")
    try:
        components = list(state)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("State must be numeric") from exc
    for component in components:
        if isinstance(
            component,
            (
                bool,
                np.bool_,
                str,
                bytes,
                bytearray,
                complex,
                np.complexfloating,
                list,
                tuple,
                np.ndarray,
            ),
        ):
            raise ValueError("State must contain only real numeric values")
    array = np.asarray(state, dtype=np.float64)
    if array.shape != (6,) or not np.all(np.isfinite(array)):
        raise ValueError("State must be a finite six-component vector")
    return array


def two_body_derivative(state: Any, mu: Any) -> NDArray[np.float64]:
    """Newtonian point-mass Earth derivative: dr/dt=v, dv/dt=-mu*r/|r|^3."""

    y = _numeric_state(state)
    if isinstance(mu, (bool, np.bool_, str, bytes, bytearray)):
        raise ValueError("Gravitational parameter must be numeric")
    try:
        mu_value = float(mu)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Gravitational parameter must be numeric") from exc
    if not math.isfinite(mu_value) or mu_value <= 0:
        raise ValueError("Gravitational parameter must be finite and positive")

    radius = float(np.hypot(np.hypot(abs(y[0]), abs(y[1])), abs(y[2])))
    if not math.isfinite(radius) or radius <= 0:
        raise ValueError("Position radius must be finite and positive")
    acceleration_scale = (mu_value / radius) / radius
    if not math.isfinite(acceleration_scale):
        raise ValueError("Acceleration magnitude is non-finite")
    if acceleration_scale == 0.0:
        raise ValueError("Acceleration magnitude underflows float64")

    acceleration = -acceleration_scale * (y[:3] / radius)
    derivative = np.concatenate((y[3:], acceleration)).astype(np.float64)
    if not np.all(np.isfinite(derivative)):
        raise ValueError("Derivative contains non-finite values")
    return derivative
