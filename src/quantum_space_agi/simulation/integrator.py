from __future__ import annotations

import math

import numpy as np


def _numeric_state(state):
    if isinstance(state, (str, bytes, bytearray, bool, np.bool_)):
        raise ValueError("State must be numeric")
    try:
        components = list(state)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("State must be numeric") from exc
    for component in components:
        if isinstance(
            component,
            (bool, np.bool_, str, bytes, bytearray, complex, np.complexfloating, list, tuple, np.ndarray),
        ):
            raise ValueError("State must contain only real numeric values")
    array = np.asarray(state, dtype=np.float64)
    if array.size == 0 or array.ndim != 1 or not np.all(np.isfinite(array)):
        raise ValueError("State must be a finite one-dimensional numeric vector")
    return array


def rk4_step(state, time_s, time_step_s, derivative, *derivative_args):
    """Advance one fixed step with classical fourth-order Runge-Kutta."""

    if isinstance(time_step_s, (bool, np.bool_, str, bytes, bytearray)):
        raise ValueError("Timestep must be numeric")
    if isinstance(time_s, (bool, np.bool_, str, bytes, bytearray)):
        raise ValueError("Time must be numeric")
    try:
        time = float(time_s)
        dt = float(time_step_s)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Time and timestep must be numeric") from exc
    if not math.isfinite(time) or time < 0:
        raise ValueError("Time must be finite and non-negative")
    if not math.isfinite(dt) or dt <= 0:
        raise ValueError("Timestep must be finite and positive")

    y = _numeric_state(state)
    k1 = np.asarray(derivative(time, y, *derivative_args), dtype=np.float64)
    k2 = np.asarray(derivative(time + 0.5 * dt, y + 0.5 * dt * k1, *derivative_args), dtype=np.float64)
    k3 = np.asarray(derivative(time + 0.5 * dt, y + 0.5 * dt * k2, *derivative_args), dtype=np.float64)
    k4 = np.asarray(derivative(time + dt, y + dt * k3, *derivative_args), dtype=np.float64)
    for stage in (k1, k2, k3, k4):
        if stage.shape != y.shape or not np.all(np.isfinite(stage)):
            raise ValueError("RK4 intermediate stage is invalid")

    result = y + dt / 6.0 * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
    if not np.all(np.isfinite(result)):
        raise ValueError("RK4 produced a non-finite state")
    return result.astype(np.float64)
