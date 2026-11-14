"""Synthetic orbit profiles and minimal payload-only spacecraft selection."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from quantum_space_agi.errors import ValidationError
from quantum_space_agi.ml.mission_configuration import EducationalMissionConfiguration
from quantum_space_agi.ml.mission_scenarios import RESOURCE_SELECTION_SCENARIO_ID

EDUCATIONAL_SPACECRAFT_PROFILE_ID = "educational-payload-carrier-v1"


@dataclass(frozen=True, slots=True)
class OrbitDestinationProfile:
    """Idealized synthetic circular Earth-orbit initial-condition profile."""

    profile_id: str
    display_name: str
    altitude_m: float
    simulation_duration_s: float
    time_step_s: float
    assumptions: tuple[str, ...]
    classification: Literal["synthetic educational profile"] = (
        "synthetic educational profile"
    )

    def __post_init__(self) -> None:
        for name in ("profile_id", "display_name"):
            value = getattr(self, name)
            if type(value) is not str or not value.strip():
                raise ValidationError(f"{name} must be non-empty text")
        for name in ("altitude_m", "simulation_duration_s", "time_step_s"):
            value = getattr(self, name)
            if (
                type(value) not in (int, float)
                or not math.isfinite(value)
                or value <= 0
            ):
                raise ValidationError(f"{name} must be finite and positive")
        if self.time_step_s > self.simulation_duration_s:
            raise ValidationError("time_step_s must not exceed simulation_duration_s")
        if self.classification != "synthetic educational profile":
            raise ValidationError(
                "classification must label synthetic educational data"
            )
        if type(self.assumptions) is not tuple or not self.assumptions:
            raise ValidationError("assumptions must be a non-empty tuple")
        if any(type(item) is not str or not item.strip() for item in self.assumptions):
            raise ValidationError("assumptions must contain non-empty strings")


_ASSUMPTIONS = (
    "Synthetic profile; not a real NASA mission target.",
    "Altitude is above the simulator's Earth reference radius.",
    "Ideal circular-orbit initial condition; no transfer is modeled.",
    "Initial position is ECI +X and velocity is prograde ECI +Y.",
    "Uses the educational Earth point-mass two-body model.",
    "No atmosphere, thrust, propulsion, spacecraft mass, or mission success is",
    "modeled.",
)

ORBIT_DESTINATION_PROFILES: Mapping[str, OrbitDestinationProfile] = MappingProxyType(
    {
        profile.profile_id: profile
        for profile in (
            OrbitDestinationProfile(
                "synthetic-leo-400-km",
                "Synthetic LEO profile A",
                400_000.0,
                3_600.0,
                120.0,
                _ASSUMPTIONS,
            ),
            OrbitDestinationProfile(
                "synthetic-leo-800-km",
                "Synthetic LEO profile B",
                800_000.0,
                3_600.0,
                120.0,
                _ASSUMPTIONS,
            ),
            OrbitDestinationProfile(
                "synthetic-earth-orbit-2000-km",
                "Synthetic Earth-orbit profile C",
                2_000_000.0,
                3_600.0,
                120.0,
                _ASSUMPTIONS,
            ),
        )
    }
)


@dataclass(frozen=True, slots=True, init=False)
class SpacecraftConfiguration:
    """A payload selection label; it contains no physical spacecraft properties."""

    profile_id: str
    selected_payload_ids: tuple[str, ...]

    def __init__(self, selected_payload_ids: list[str]) -> None:
        if not isinstance(selected_payload_ids, list) or not selected_payload_ids:
            raise ValidationError(
                "selected_payload_ids must be a non-empty list of strings"
            )
        if any(
            type(item) is not str or not item.strip() for item in selected_payload_ids
        ):
            raise ValidationError("selected_payload_ids must contain non-empty strings")
        ordered = tuple(sorted(selected_payload_ids))
        if len(set(ordered)) != len(ordered):
            raise ValidationError("selected_payload_ids must not contain duplicates")
        # Reuse ARC-08's actual supported scenario/payload validation even when
        # optional resource evaluation is disabled.
        EducationalMissionConfiguration(RESOURCE_SELECTION_SCENARIO_ID, list(ordered))
        object.__setattr__(self, "profile_id", EDUCATIONAL_SPACECRAFT_PROFILE_ID)
        object.__setattr__(self, "selected_payload_ids", ordered)


@dataclass(frozen=True, slots=True, init=False)
class MissionDemoConfiguration:
    destination_profile_id: str
    spacecraft: SpacecraftConfiguration

    def __init__(
        self, destination_profile_id: str, spacecraft: SpacecraftConfiguration
    ) -> None:
        if (
            type(destination_profile_id) is not str
            or destination_profile_id not in ORBIT_DESTINATION_PROFILES
        ):
            raise ValidationError(
                "destination_profile_id is not a supported synthetic profile"
            )
        if type(spacecraft) is not SpacecraftConfiguration:
            raise ValidationError("spacecraft must be a SpacecraftConfiguration")
        object.__setattr__(self, "destination_profile_id", destination_profile_id)
        object.__setattr__(self, "spacecraft", spacecraft)

    @property
    def destination_profile(self) -> OrbitDestinationProfile:
        return ORBIT_DESTINATION_PROFILES[self.destination_profile_id]
