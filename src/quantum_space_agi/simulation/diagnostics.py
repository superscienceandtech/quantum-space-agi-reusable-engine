from __future__ import annotations

import math

import numpy as np


def _contains_boolean(value):
    if isinstance(value, (bool, np.bool_)):
        return True
    if isinstance(value, np.ndarray):
        return value.dtype.kind == "b"
    if isinstance(value, (list, tuple)):
        return any(_contains_boolean(component) for component in value)
    return False


def _validated_real_array(value, name):
    if _contains_boolean(value):
        raise ValueError(f"{name} must contain only real numeric values")
    try:
        raw = np.asarray(value)
    except (TypeError, ValueError, OverflowError, FloatingPointError) as exc:
        raise ValueError(f"{name} must contain only real numeric values") from exc
    if raw.dtype.kind not in "iuf":
        raise ValueError(f"{name} must contain only real numeric values")
    try:
        array = np.asarray(raw, dtype=np.float64)
    except (TypeError, ValueError, OverflowError, FloatingPointError) as exc:
        raise ValueError(f"{name} must contain only real numeric values") from exc
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    return array


def _validated_state(state):
    array = _validated_real_array(state, "State")
    if array.shape != (6,):
        raise ValueError("State must be a finite six-component vector")
    return array


def _validated_mu(mu):
    if isinstance(mu, (bool, np.bool_, str, bytes, bytearray)):
        raise ValueError("Gravitational parameter must be numeric")
    try:
        mu_value = float(mu)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Gravitational parameter must be numeric") from exc
    if not math.isfinite(mu_value) or mu_value <= 0:
        raise ValueError("Gravitational parameter must be finite and positive")
    return mu_value


def _stable_norm(vector):
    with np.errstate(over="ignore", invalid="ignore", under="ignore", divide="ignore"):
        norm = np.hypot(np.hypot(abs(vector[0]), abs(vector[1])), abs(vector[2]))
    value = float(norm)
    if not math.isfinite(value):
        raise ValueError("Vector norm is non-finite")
    return value


def specific_orbital_energy(state, mu):
    y = _validated_state(state)
    mu_value = _validated_mu(mu)
    radius = _stable_norm(y[:3])
    speed = _stable_norm(y[3:])
    if radius <= 0 or not math.isfinite(radius) or not math.isfinite(speed):
        raise ValueError("State produces an invalid orbital radius or speed")
    with np.errstate(over="ignore", invalid="ignore", under="ignore", divide="ignore"):
        energy = 0.5 * speed * speed - mu_value / radius
    if not math.isfinite(float(energy)):
        raise ValueError("Specific orbital energy is non-finite")
    return float(energy)


def specific_angular_momentum(state):
    y = _validated_state(state)
    with np.errstate(over="ignore", invalid="ignore", under="ignore"):
        angular_momentum = np.cross(y[:3], y[3:]).astype(np.float64)
    if not np.all(np.isfinite(angular_momentum)):
        raise ValueError("Angular momentum contains non-finite values")
    magnitude = _stable_norm(angular_momentum)
    if not math.isfinite(magnitude):
        raise ValueError("Angular momentum magnitude is non-finite")
    return angular_momentum, magnitude


def eccentricity_vector(state, mu):
    y = _validated_state(state)
    mu_value = _validated_mu(mu)
    position = y[:3]
    velocity = y[3:]
    radius = _stable_norm(position)
    if radius <= 0 or not math.isfinite(radius):
        raise ValueError("Position radius must be finite and positive")
    angular_momentum, _ = specific_angular_momentum(y)
    with np.errstate(over="ignore", invalid="ignore", under="ignore", divide="ignore"):
        vector = np.cross(velocity, angular_momentum) / mu_value - position / radius
    if not np.all(np.isfinite(vector)):
        raise ValueError("Eccentricity vector contains non-finite values")
    magnitude = _stable_norm(vector)
    if not math.isfinite(magnitude):
        raise ValueError("Eccentricity magnitude is non-finite")
    return vector.astype(np.float64), magnitude


def diagnose_trajectory(times_s, states, mu):
    times = _validated_real_array(times_s, "Times")
    trajectory = _validated_real_array(states, "Trajectory")
    mu_value = _validated_mu(mu)
    if times.ndim != 1 or trajectory.shape != (times.size, 6):
        raise ValueError("Trajectory must contain matching six-component states and times")
    with np.errstate(over="ignore", invalid="ignore", under="ignore"):
        time_deltas = np.diff(times)
    if not np.all(np.isfinite(time_deltas)):
        raise ValueError("Times must have finite differences")
    if times.size == 0 or np.any(time_deltas < 0.0):
        raise ValueError("Times must be non-empty and monotonically ordered")

    energies = np.asarray(
        [specific_orbital_energy(state, mu_value) for state in trajectory],
        dtype=np.float64,
    )
    angular_momentum = np.asarray(
        [specific_angular_momentum(state)[1] for state in trajectory],
        dtype=np.float64,
    )
    eccentricities = np.asarray(
        [eccentricity_vector(state, mu_value)[1] for state in trajectory],
        dtype=np.float64,
    )
    with np.errstate(over="ignore", invalid="ignore", under="ignore", divide="ignore"):
        radii = np.hypot(
            np.hypot(np.abs(trajectory[:, 0]), np.abs(trajectory[:, 1])),
            np.abs(trajectory[:, 2]),
        ).astype(np.float64)
        speeds = np.hypot(
            np.hypot(np.abs(trajectory[:, 3]), np.abs(trajectory[:, 4])),
            np.abs(trajectory[:, 5]),
        ).astype(np.float64)
    with np.errstate(over="ignore", invalid="ignore", under="ignore"):
        energy_drift = energies - energies[0]
        angular_drift = angular_momentum - angular_momentum[0]
    if not all(
        np.all(np.isfinite(values))
        for values in (radii, speeds, energy_drift, angular_drift)
    ):
        raise ValueError("Trajectory diagnostics contain non-finite results")

    return {
        "specific_energy_m2_s2": energies,
        "specific_angular_momentum_m2_s": angular_momentum,
        "eccentricity_magnitude": eccentricities,
        "radius_m": radii,
        "speed_m_s": speeds,
        "energy_drift_m2_s2": energy_drift,
        "angular_momentum_drift_m2_s": angular_drift,
        "max_abs_energy_drift_m2_s2": float(np.max(np.abs(energy_drift))),
        "max_abs_angular_momentum_drift_m2_s": float(np.max(np.abs(angular_drift))),
    }
