from __future__ import annotations

import math

import numpy as np

from .diagnostics import diagnose_trajectory
from .models import OrbitalState, SimulationConfig
from .propagation import propagate_two_body


def run_simulation(config: SimulationConfig, initial_time_s: float = 0.0):
    """Run the validated ARC-05 fixed-step Earth two-body workflow."""

    if isinstance(initial_time_s, (bool, np.bool_, str, bytes, bytearray)):
        raise ValueError("Initial time must be a finite numeric scalar")
    try:
        initial_time = float(initial_time_s)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Initial time must be a finite numeric scalar") from exc
    if not math.isfinite(initial_time):
        raise ValueError("Initial time must be a finite numeric scalar")
    if initial_time != 0.0:
        raise ValueError("ARC-05 propagation currently starts at time zero")

    if not isinstance(config, SimulationConfig):
        raise TypeError("config must be a SimulationConfig")

    initial_state = OrbitalState(
        position_m=config.initial_position_m,
        velocity_mps=config.initial_velocity_mps,
        time_s=initial_time,
    )
    trajectory = propagate_two_body(
        initial_state.to_array(),
        config.gravitational_parameter_m3_s2,
        config.simulation_duration_s,
        config.time_step_s,
        config.collision_radius_m,
    )
    diagnostics = diagnose_trajectory(
        trajectory["times_s"],
        trajectory["states"],
        config.gravitational_parameter_m3_s2,
    )
    return {
        "times_s": trajectory["times_s"],
        "states": trajectory["states"],
        "collision_index": trajectory["collision_index"],
        "collision_radius_m": trajectory["collision_radius_m"],
        "collision_time_s": trajectory["collision_time_s"],
        "collision_state": trajectory["collision_state"],
        "collision_method": trajectory["collision_method"],
        "diagnostics": diagnostics,
        "model": {
            "reference_frame": "ECI",
            "integrator": "RK4",
            "dynamics": "Earth point-mass Newtonian two-body",
            "time_unit": "s",
            "position_unit": "m",
            "velocity_unit": "m/s",
        },
    }
