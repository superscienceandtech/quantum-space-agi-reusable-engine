from __future__ import annotations

import math

import numpy as np

from .integrator import rk4_step


def _stable_position_radius(position):
    with np.errstate(over="ignore", invalid="ignore", under="ignore", divide="ignore"):
        radius = np.hypot(np.hypot(abs(position[0]), abs(position[1])), abs(position[2]))
    radius = float(radius)
    if not math.isfinite(radius):
        raise ValueError("Collision bracket contains a non-finite radius")
    return radius


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
    try:
        array = np.asarray(state, dtype=np.float64)
    except (TypeError, ValueError, OverflowError, FloatingPointError) as exc:
        raise ValueError("State must be numeric") from exc
    if array.shape != (6,) or not np.all(np.isfinite(array)):
        raise ValueError("State must be a finite six-component vector")
    return array


def _propagation_derivative(time_s, state, mu):
    del time_s
    from .dynamics import two_body_derivative

    return two_body_derivative(state, mu)


def interpolate_collision_event(
    previous_time_s,
    previous_state,
    next_time_s,
    next_state,
    collision_radius_m,
):
    previous = _numeric_state(previous_state)
    next_y = _numeric_state(next_state)
    previous_radius = _stable_position_radius(previous[:3])
    next_radius = _stable_position_radius(next_y[:3])
    if not math.isfinite(previous_radius) or not math.isfinite(next_radius):
        raise ValueError("Collision bracket contains a non-finite radius")
    if isinstance(previous_time_s, (bool, np.bool_, str, bytes, bytearray)) or isinstance(
        next_time_s, (bool, np.bool_, str, bytes, bytearray)
    ):
        raise ValueError("Collision bracket times must be finite numeric scalars")
    try:
        previous_time = float(previous_time_s)
        next_time = float(next_time_s)
        threshold = float(collision_radius_m)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Collision bracket times and threshold must be numeric") from exc
    if (
        not math.isfinite(previous_time)
        or not math.isfinite(next_time)
        or next_time <= previous_time
    ):
        raise ValueError("Collision bracket times must be finite and strictly increasing")
    if isinstance(collision_radius_m, (bool, np.bool_, str, bytes, bytearray)):
        raise ValueError("Collision threshold must be finite and positive")
    if not math.isfinite(threshold) or threshold <= 0:
        raise ValueError("Collision threshold must be finite and positive")

    if previous_radius == threshold:
        return previous_time, previous.copy(), "exact_sample"
    if next_radius == threshold:
        return next_time, next_y.copy(), "exact_sample"
    if previous_radius == next_radius:
        raise ValueError(
            "Invalid collision interval: endpoint radii are degenerate and do not bracket the threshold"
        )
    if not (min(previous_radius, next_radius) <= threshold <= max(previous_radius, next_radius)):
        raise ValueError("Invalid collision interval: threshold is not bracketed by endpoint radii")

    radius_difference = next_radius - previous_radius
    alpha = (threshold - previous_radius) / radius_difference
    if not math.isfinite(alpha):
        raise ValueError("Invalid collision interval: interpolation fraction is non-finite")
    if alpha < 0.0 or alpha > 1.0:
        raise ValueError("Invalid collision interval: interpolation fraction is outside [0, 1]")

    event_time = (1.0 - alpha) * previous_time + alpha * next_time
    if not math.isfinite(event_time):
        raise ValueError("Interpolated collision time is non-finite")
    with np.errstate(over="ignore", invalid="ignore", under="ignore"):
        event_state = (1.0 - alpha) * previous + alpha * next_y
    if not np.all(np.isfinite(event_state)):
        raise ValueError("Interpolated collision state is non-finite")
    return event_time, event_state.astype(np.float64), "linear_radius_interpolation"


def linear_radius_collision_event(
    previous_time_s,
    previous_state,
    next_time_s,
    next_state,
    collision_radius_m,
):
    """Backward-compatible alias for the linear-radius collision interpolation helper."""

    return interpolate_collision_event(
        previous_time_s,
        previous_state,
        next_time_s,
        next_state,
        collision_radius_m,
    )


def propagate_two_body(
    initial_state,
    mu,
    duration_s,
    time_step_s,
    collision_radius_m,
):
    """Propagate the unchanged Earth point-mass model with fixed-step classical RK4."""

    y0 = _numeric_state(initial_state)
    for name, value in (
        ("mu", mu),
        ("duration", duration_s),
        ("timestep", time_step_s),
        ("collision radius", collision_radius_m),
    ):
        if isinstance(value, (bool, np.bool_, str, bytes, bytearray)):
            raise ValueError(f"{name} must be numeric")
    try:
        mu_value = float(mu)
        duration = float(duration_s)
        timestep = float(time_step_s)
        collision_radius = float(collision_radius_m)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Propagation parameters must be numeric") from exc
    if not math.isfinite(mu_value) or mu_value <= 0:
        raise ValueError("Gravitational parameter must be finite and positive")
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Simulation duration must be finite and positive")
    if not math.isfinite(timestep) or timestep <= 0:
        raise ValueError("Timestep must be finite and positive")
    if not math.isfinite(collision_radius) or collision_radius <= 0:
        raise ValueError("Collision radius must be finite and positive")
    if duration > timestep and timestep < math.ulp(duration):
        raise ValueError("Timestep is too small to represent the simulation time grid")

    initial_radius = _stable_position_radius(y0[:3])
    if not math.isfinite(initial_radius) or initial_radius <= 0:
        raise ValueError("Initial position radius must be finite and positive")

    times = [0.0]
    states = [y0.copy()]
    collision_index = None
    collision_time_s = None
    collision_state = None
    collision_method = None

    current_time = 0.0
    y = y0.copy()
    initial_velocity_zero = bool(np.all(y0[3:] == 0.0))
    if initial_radius < collision_radius or (initial_radius == collision_radius and initial_velocity_zero):
        collision_index = 0
        collision_time_s = 0.0
        collision_state = y.copy()
        collision_method = "exact_sample"

    while current_time < duration and collision_index is None:
        step = min(timestep, duration - current_time)
        next_time = current_time + step
        if next_time <= current_time:
            raise ValueError("Timestep cannot advance the simulation time")
        previous_time = current_time
        previous_state = y.copy()
        previous_radius = _stable_position_radius(previous_state[:3])
        y = rk4_step(
            y,
            current_time,
            step,
            _propagation_derivative,
            mu_value,
        )
        current_time = next_time
        if abs(current_time - duration) <= 1e-12 * max(1.0, duration):
            current_time = duration
        times.append(current_time)
        states.append(y.copy())
        current_radius = _stable_position_radius(y[:3])
        if current_radius <= collision_radius and previous_radius > collision_radius:
            collision_index = len(states) - 1
            (
                collision_time_s,
                collision_state,
                collision_method,
            ) = interpolate_collision_event(
                previous_time,
                previous_state,
                current_time,
                y,
                collision_radius,
            )

    return {
        "times_s": np.asarray(times, dtype=np.float64),
        "states": np.vstack(states).astype(np.float64),
        "collision_index": collision_index,
        "collision_radius_m": collision_radius,
        "collision_time_s": collision_time_s,
        "collision_state": None if collision_state is None else collision_state.astype(np.float64),
        "collision_method": collision_method,
    }
