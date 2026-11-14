"""Strict JSON DTOs for the local educational mission API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, field_validator

from .configuration import ORBIT_DESTINATION_PROFILES, SpacecraftConfiguration


class MissionRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    destination_profile_id: str
    selected_payload_ids: list[str] = Field(min_length=1)

    @field_validator("destination_profile_id")
    @classmethod
    def validate_destination_profile(cls, value: str) -> str:
        if value not in ORBIT_DESTINATION_PROFILES:
            raise ValueError("destination_profile_id is not a supported profile")
        return value

    @field_validator("selected_payload_ids")
    @classmethod
    def validate_payload_ids(cls, value: list[str]) -> list[str]:
        return list(SpacecraftConfiguration(value).selected_payload_ids)


class MissionSummaryDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    destination_profile_id: str
    destination_display_name: str
    spacecraft_profile_id: str
    selected_payload_ids: list[str]


class MissionValidationDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    valid: Literal[True]
    mission: MissionSummaryDTO


class DestinationProfileDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    profile_id: str
    display_name: str
    altitude_m: FiniteFloat
    simulation_duration_s: FiniteFloat
    time_step_s: FiniteFloat
    assumptions: list[str]
    classification: Literal["synthetic educational profile"]


class DestinationListDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    destinations: list[DestinationProfileDTO]


class ApiErrorFieldDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    field: str
    message: str


class ApiErrorDetailDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    code: str
    message: str
    details: list[ApiErrorFieldDTO] = Field(default_factory=list)


class ApiErrorDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    error: ApiErrorDetailDTO


class ResourceTotalsDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    budget_units: int
    mass_units: int
    power_units: int
    payload_slots: int


class ResourceViolationDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    code: Literal["budget", "mass", "power", "slots"]
    observed_total: int
    limit: int


class EducationalResourceResultDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    selected_payload_ids: list[str]
    evaluator_version: str
    scenario_id: str
    feasible: bool
    violations: list[ResourceViolationDTO]
    resource_totals: ResourceTotalsDTO
    educational_score: int | None


class ResourceEvaluationDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    status: Literal["evaluated"]
    policy_approval_status: Literal["pending"]
    policy_authority: str
    warning: str
    result: EducationalResourceResultDTO


class SimulationModelDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    reference_frame: Literal["ECI"]
    integrator: Literal["RK4"]
    dynamics: str
    time_unit: Literal["s"]
    position_unit: Literal["m"]
    velocity_unit: Literal["m/s"]


class TrajectoryDiagnosticsDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    specific_energy_m2_s2: list[FiniteFloat]
    specific_angular_momentum_m2_s: list[FiniteFloat]
    eccentricity_magnitude: list[FiniteFloat]
    radius_m: list[FiniteFloat]
    speed_m_s: list[FiniteFloat]
    energy_drift_m2_s2: list[FiniteFloat]
    angular_momentum_drift_m2_s: list[FiniteFloat]
    max_abs_energy_drift_m2_s2: FiniteFloat
    max_abs_angular_momentum_drift_m2_s: FiniteFloat


class TrajectoryDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    times_s: list[FiniteFloat]
    states: list[list[FiniteFloat]]
    state_order: list[Literal["x_m", "y_m", "z_m", "vx_mps", "vy_mps", "vz_mps"]]
    collision_index: int | None
    collision_time_s: FiniteFloat | None
    collision_state: list[FiniteFloat] | None
    diagnostics: TrajectoryDiagnosticsDTO
    model: SimulationModelDTO


class MissionRunResponseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    classification: Literal["synthetic educational demonstration"]
    limitations: list[str]
    mission: MissionSummaryDTO
    resource_evaluation: ResourceEvaluationDTO
    trajectory: TrajectoryDTO
