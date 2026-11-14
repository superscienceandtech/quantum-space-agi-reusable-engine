"""Orchestration adapter for ARC-08 education and ARC-05 simulation."""

from __future__ import annotations

import json
from typing import Any

import numpy as np

from quantum_space_agi.ml.mission_configuration import EducationalMissionConfiguration
from quantum_space_agi.ml.mission_evaluator import (
    evaluate_educational_mission,
    serialize_educational_mission_result,
)
from quantum_space_agi.ml.mission_scenarios import RESOURCE_SELECTION_SCENARIO_ID
from quantum_space_agi.simulation import SimulationConfig, run_simulation
from quantum_space_agi.simulation.models import (
    EARTH_MU_M3_S2,
    EARTH_REFERENCE_RADIUS_M,
)

from .configuration import MissionDemoConfiguration, SpacecraftConfiguration

_REQUEST_KEYS = {"destination_profile_id", "selected_payload_ids"}


class MissionDemoService:
    """Run a synthetic profile through existing domain components.

    ARC-08 results describe an educational scenario only. Pending policy
    approval never gates or alters the ARC-05 simulation.
    """

    def run(self, request: dict[str, Any]) -> dict[str, Any]:
        if type(request) is not dict:
            raise ValueError("request must be a JSON object")
        if set(request) != _REQUEST_KEYS:
            raise ValueError(
                "request must contain only destination_profile_id and "
                "selected_payload_ids"
            )
        spacecraft = SpacecraftConfiguration(request["selected_payload_ids"])
        mission = MissionDemoConfiguration(
            request["destination_profile_id"], spacecraft
        )
        profile = mission.destination_profile

        radius_m = EARTH_REFERENCE_RADIUS_M + profile.altitude_m
        circular_speed_mps = (EARTH_MU_M3_S2 / radius_m) ** 0.5
        config = SimulationConfig(
            initial_position_m=(radius_m, 0.0, 0.0),
            initial_velocity_mps=(0.0, circular_speed_mps, 0.0),
            gravitational_parameter_m3_s2=EARTH_MU_M3_S2,
            simulation_duration_s=profile.simulation_duration_s,
            time_step_s=profile.time_step_s,
            reference_frame="ECI",
            collision_radius_m=EARTH_REFERENCE_RADIUS_M,
        )
        simulation = run_simulation(config)

        resource_configuration = EducationalMissionConfiguration(
            RESOURCE_SELECTION_SCENARIO_ID,
            list(spacecraft.selected_payload_ids),
        )
        resource_evaluation: dict[str, Any] = {
            "status": "evaluated",
            "policy_approval_status": "pending",
            "policy_authority": "educational evaluator output only",
            "warning": (
                "Not an approved spacecraft resource policy; totals are abstract "
                "educational units and do not gate simulation."
            ),
            "result": json.loads(
                serialize_educational_mission_result(
                    evaluate_educational_mission(resource_configuration)
                )
            ),
        }

        diagnostics = {
            name: value.tolist() if isinstance(value, np.ndarray) else value
            for name, value in simulation["diagnostics"].items()
        }
        collision_state = simulation["collision_state"]
        return {
            "classification": "synthetic educational demonstration",
            "limitations": list(profile.assumptions),
            "mission": {
                "destination_profile_id": profile.profile_id,
                "destination_display_name": profile.display_name,
                "spacecraft_profile_id": spacecraft.profile_id,
                "selected_payload_ids": list(spacecraft.selected_payload_ids),
            },
            "resource_evaluation": resource_evaluation,
            "trajectory": {
                "times_s": simulation["times_s"].tolist(),
                "states": simulation["states"].tolist(),
                "state_order": ["x_m", "y_m", "z_m", "vx_mps", "vy_mps", "vz_mps"],
                "collision_index": simulation["collision_index"],
                "collision_time_s": simulation["collision_time_s"],
                "collision_state": None
                if collision_state is None
                else collision_state.tolist(),
                "diagnostics": diagnostics,
                "model": simulation["model"],
            },
        }
