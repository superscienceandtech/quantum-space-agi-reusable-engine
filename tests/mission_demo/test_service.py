from __future__ import annotations

import json
import math

import pytest

from quantum_space_agi.mission_demo.configuration import (
    ORBIT_DESTINATION_PROFILES,
    MissionDemoConfiguration,
    SpacecraftConfiguration,
)
from quantum_space_agi.mission_demo.service import MissionDemoService


def mission_request() -> dict[str, object]:
    return {
        "destination_profile_id": "synthetic-leo-400-km",
        "selected_payload_ids": ["relay", "imager"],
    }


def test_destination_profiles_are_synthetic_supported_orbits() -> None:
    assert set(ORBIT_DESTINATION_PROFILES) == {
        "synthetic-leo-400-km",
        "synthetic-leo-800-km",
        "synthetic-earth-orbit-2000-km",
    }
    assert all(
        profile.classification == "synthetic educational profile"
        for profile in ORBIT_DESTINATION_PROFILES.values()
    )


def test_spacecraft_configuration_validates_supported_payload_selection() -> None:
    spacecraft = SpacecraftConfiguration(["relay", "imager"])
    assert spacecraft.selected_payload_ids == ("imager", "relay")
    with pytest.raises(ValueError):
        SpacecraftConfiguration(["unknown-payload"])


def test_service_maps_mission_to_arc05_and_returns_trajectory() -> None:
    result = MissionDemoService().run(mission_request())

    profile = ORBIT_DESTINATION_PROFILES["synthetic-leo-400-km"]
    initial = result["trajectory"]["states"][0]
    radius_m = 6_378_137.0 + profile.altitude_m
    expected_speed_mps = math.sqrt(3.986004418e14 / radius_m)
    assert initial[0:3] == pytest.approx([radius_m, 0.0, 0.0])
    assert initial[3:6] == pytest.approx([0.0, expected_speed_mps, 0.0])
    assert result["trajectory"]["model"]["reference_frame"] == "ECI"
    assert result["resource_evaluation"]["status"] == "evaluated"
    assert result["resource_evaluation"]["policy_approval_status"] == "pending"


def test_infeasible_arc08_evaluation_does_not_gate_simulation() -> None:
    request = {
        "destination_profile_id": "synthetic-leo-400-km",
        "selected_payload_ids": ["imager", "spectrometer", "relay"],
    }
    result = MissionDemoService().run(request)

    evaluation = result["resource_evaluation"]
    assert evaluation["status"] == "evaluated"
    assert evaluation["policy_approval_status"] == "pending"
    assert evaluation["result"]["feasible"] is False
    assert (
        evaluation["policy_authority"]
        == "educational evaluator output only"
    )
    assert result["trajectory"]["states"]


def test_run_includes_unapproved_arc08_output_by_default() -> None:
    result = MissionDemoService().run(mission_request())
    evaluation = result["resource_evaluation"]

    assert evaluation["status"] == "evaluated"
    assert evaluation["policy_approval_status"] == "pending"
    assert evaluation["result"]["scenario_id"] == "resource-selection-demo-v1"
    assert evaluation["result"]["resource_totals"]["mass_units"] >= 0
    assert result["trajectory"]["states"]
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    "payload_data",
    [
        {},
        {"destination_profile_id": "mars", "selected_payload_ids": ["imager"]},
        {
            "destination_profile_id": "synthetic-leo-400-km",
            "selected_payload_ids": ["imager", "imager"],
        },
        {
            "destination_profile_id": "synthetic-leo-400-km",
            "selected_payload_ids": ["imager"],
            "extra": True,
        },
    ],
)
def test_service_rejects_invalid_mission_request(
    payload_data: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        MissionDemoService().run(payload_data)


def test_configuration_models_reject_unsupported_profile_and_payloads() -> None:
    with pytest.raises(ValueError):
        MissionDemoConfiguration("mars", SpacecraftConfiguration(["imager"]))
