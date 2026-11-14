from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

EARTH_MU_M3_S2 = 3.986004418e14
EARTH_REFERENCE_RADIUS_M = 6_378_137.0


class SimulationConfig(BaseModel):
    """Strict frozen input contract for the fixed-step ARC-05 workflow."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, allow_inf_nan=False)

    initial_position_m: tuple[float, float, float]
    initial_velocity_mps: tuple[float, float, float]
    gravitational_parameter_m3_s2: float = Field(default=EARTH_MU_M3_S2, gt=0)
    simulation_duration_s: float = Field(gt=0)
    time_step_s: float = Field(gt=0)
    integrator: Literal["RK4"] = "RK4"
    reference_frame: Literal["ECI"] = "ECI"
    collision_radius_m: float = Field(gt=0)

    @field_validator("initial_position_m", "initial_velocity_mps", mode="before")
    @classmethod
    def validate_vector_inputs(cls, value):
        if isinstance(value, (str, bytes, bytearray)):
            raise ValueError("Position and velocity components must be numeric")
        return value

    @model_validator(mode="after")
    def validate_physical_values(self):
        values = (
            *self.initial_position_m,
            *self.initial_velocity_mps,
            self.gravitational_parameter_m3_s2,
            self.simulation_duration_s,
            self.time_step_s,
            self.collision_radius_m,
        )
        if not all(math.isfinite(float(value)) for value in values):
            raise ValueError("All configuration values must be finite")
        return self


class OrbitalState(BaseModel):
    """Immutable six-component translational state in Earth-centered inertial SI units."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, allow_inf_nan=False)

    position_m: tuple[float, float, float]
    velocity_mps: tuple[float, float, float]
    time_s: float = Field(ge=0)

    def to_array(self) -> np.ndarray:
        return np.asarray((*self.position_m, *self.velocity_mps), dtype=np.float64)

    @classmethod
    def from_array(cls, state_vector, time_s) -> "OrbitalState":
        if isinstance(state_vector, (str, bytes, bytearray, bool, np.bool_)):
            raise ValueError("State vector must be a numeric array")

        try:
            components = list(state_vector)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("State vector must be a numeric array") from exc

        for component in components:
            if isinstance(
                component,
                (bool, np.bool_, str, bytes, bytearray, complex, np.complexfloating),
            ):
                raise ValueError("State vector must contain only real numeric values")
            if isinstance(component, (list, tuple, np.ndarray)):
                raise ValueError("State vector must be one-dimensional")

        try:
            untyped_state = np.asarray(state_vector)
        except (TypeError, ValueError, OverflowError, FloatingPointError) as exc:
            raise ValueError("State vector must be a numeric array") from exc

        if untyped_state.dtype.kind not in "iuf":
            raise ValueError("State vector must contain only real numeric values")

        try:
            state = np.asarray(untyped_state, dtype=np.float64)
        except (TypeError, ValueError, OverflowError, FloatingPointError) as exc:
            raise ValueError("State vector must be float64-compatible") from exc

        if state.shape != (6,):
            raise ValueError("State vector must have exactly six components")
        if not np.all(np.isfinite(state)):
            raise ValueError("State vector must contain only finite values")

        if isinstance(time_s, (bool, np.bool_, str, bytes, bytearray)):
            raise ValueError("Time must be a finite numeric scalar")
        try:
            time_value = float(time_s)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("Time must be a finite numeric scalar") from exc
        if not math.isfinite(time_value) or time_value < 0:
            raise ValueError("Time must be finite and non-negative")

        return cls(
            position_m=tuple(float(x) for x in state[:3]),
            velocity_mps=tuple(float(x) for x in state[3:]),
            time_s=time_value,
        )
