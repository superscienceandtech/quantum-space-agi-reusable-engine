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
    half_step_time = time + 0.5 * dt
    end_time = time + dt
    if not math.isfinite(half_step_time) or not math.isfinite(end_time):
        raise ValueError("RK4 intermediate time is non-finite")

    def evaluate_stage(stage_time, stage_state):
        if not np.all(np.isfinite(stage_state)):
            raise ValueError("RK4 intermediate state is non-finite")
        try:
            stage = np.asarray(
                derivative(stage_time, stage_state.copy(), *derivative_args),
                dtype=np.float64,
            )
        except (TypeError, ValueError, OverflowError, FloatingPointError) as exc:
            raise ValueError("RK4 intermediate stage is invalid") from exc
        if stage.shape != y.shape or not np.all(np.isfinite(stage)):
            raise ValueError("RK4 intermediate stage is invalid")
        return stage

    def intermediate_state(stage, scale):
        with np.errstate(over="ignore", invalid="ignore", under="ignore"):
            stage_state = y + scale * stage
        if not np.all(np.isfinite(stage_state)):
            raise ValueError("RK4 intermediate state is non-finite")
        return stage_state

    k1 = evaluate_stage(time, y)
    k2 = evaluate_stage(half_step_time, intermediate_state(k1, 0.5 * dt))
    k3 = evaluate_stage(half_step_time, intermediate_state(k2, 0.5 * dt))
    k4 = evaluate_stage(end_time, intermediate_state(k3, dt))

    with np.errstate(over="ignore", invalid="ignore", under="ignore"):
        result = y + dt / 6.0 * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
    if not np.all(np.isfinite(result)):
        raise ValueError("RK4 produced a non-finite state")
    return result.astype(np.float64)
