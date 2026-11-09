from __future__ import annotations

import math
from typing import Any

import numpy as np
from numpy.typing import NDArray


def _validated_state(state: Any) -> NDArray[np.float64]:
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


def _validated_mu(mu: Any) -> float:
    if isinstance(mu, (bool, np.bool_, str, bytes, bytearray)):
        raise ValueError("Gravitational parameter must be numeric")
    try:
        mu_value = float(mu)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Gravitational parameter must be numeric") from exc
    if not math.isfinite(mu_value) or mu_value <= 0:
        raise ValueError("Gravitational parameter must be finite and positive")
    return mu_value


def specific_orbital_energy(state: Any, mu: Any) -> float:
    y = _validated_state(state)
    mu_value = _validated_mu(mu)
    radius = float(np.linalg.norm(y[:3]))
    speed = float(np.linalg.norm(y[3:]))
    if radius <= 0 or not math.isfinite(radius) or not math.isfinite(speed):
        raise ValueError("State produces an invalid orbital radius or speed")
    return 0.5 * speed * speed - mu_value / radius


def specific_angular_momentum(
    state: Any,
) -> tuple[NDArray[np.float64], float]:
    y = _validated_state(state)
    angular_momentum = np.cross(y[:3], y[3:]).astype(np.float64)
    if not np.all(np.isfinite(angular_momentum)):
        raise ValueError("Angular momentum contains non-finite values")
    return angular_momentum, float(np.linalg.norm(angular_momentum))


def eccentricity_vector(state: Any, mu: Any) -> tuple[NDArray[np.float64], float]:
    y = _validated_state(state)
    mu_value = _validated_mu(mu)
    position = y[:3]
    velocity = y[3:]
    radius = float(np.linalg.norm(position))
    if radius <= 0:
        raise ValueError("Position radius must be positive")
    _, angular_momentum_magnitude = specific_angular_momentum(y)
    del angular_momentum_magnitude
    angular_momentum = np.cross(position, velocity)
    vector = np.cross(velocity, angular_momentum) / mu_value - position / radius
    if not np.all(np.isfinite(vector)):
        raise ValueError("Eccentricity vector contains non-finite values")
    return vector.astype(np.float64), float(np.linalg.norm(vector))


def diagnose_trajectory(times_s: Any, states: Any, mu: Any) -> dict[str, Any]:
    times = np.asarray(times_s, dtype=np.float64)
    trajectory = np.asarray(states, dtype=np.float64)
    mu_value = _validated_mu(mu)
    if times.ndim != 1 or trajectory.shape != (times.size, 6):
        raise ValueError(
            "Trajectory must contain matching six-component states and times"
        )
    if not np.all(np.isfinite(times)) or not np.all(np.isfinite(trajectory)):
        raise ValueError("Trajectory contains non-finite values")
    if times.size == 0 or np.any(np.diff(times) < 0.0):
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
    radii = np.linalg.norm(trajectory[:, :3], axis=1).astype(np.float64)
    speeds = np.linalg.norm(trajectory[:, 3:], axis=1).astype(np.float64)
    energy_drift = energies - energies[0]
    angular_drift = angular_momentum - angular_momentum[0]

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
