from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from quantum_space_agi.errors import ValidationError
from quantum_space_agi.ml import EducationalMissionConfiguration

SCENARIO_ID = "resource-selection-demo-v1"


class StringSubclass(str):
    pass


def test_accepts_valid_configuration_and_normalizes_payload_ids() -> None:
    configuration = EducationalMissionConfiguration(
        SCENARIO_ID, ["spectrometer", "imager"]
    )

    assert configuration.scenario_id == SCENARIO_ID
    assert configuration.selected_payload_ids == ("imager", "spectrometer")


@pytest.mark.parametrize("payload_id", ["imager", "spectrometer", "relay"])
def test_accepts_each_v1_payload(payload_id: str) -> None:
    configuration = EducationalMissionConfiguration(SCENARIO_ID, [payload_id])

    assert configuration.selected_payload_ids == (payload_id,)


def test_rejects_unknown_scenario() -> None:
    with pytest.raises(ValidationError, match="scenario_id"):
        EducationalMissionConfiguration("unknown-scenario", ["imager"])


def test_rejects_unknown_payload_id() -> None:
    with pytest.raises(ValidationError, match="payload"):
        EducationalMissionConfiguration(SCENARIO_ID, ["unknown-payload"])


def test_rejects_duplicate_payload_ids() -> None:
    with pytest.raises(ValidationError, match="duplicate"):
        EducationalMissionConfiguration(SCENARIO_ID, ["relay", "relay"])


def test_rejects_empty_payload_selection() -> None:
    with pytest.raises(ValidationError, match="non-empty"):
        EducationalMissionConfiguration(SCENARIO_ID, [])


@pytest.mark.parametrize(
    "scenario_id",
    [None, 1, True, [SCENARIO_ID], StringSubclass(SCENARIO_ID)],
)
def test_rejects_non_string_scenario_id(scenario_id: object) -> None:
    with pytest.raises(ValidationError, match="scenario_id must be a string"):
        EducationalMissionConfiguration(
            scenario_id,
            ["imager"],  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "payload_ids",
    [
        None,
        "imager",
        ("imager",),
        {"imager"},
        {"payload": "imager"},
        (payload_id for payload_id in ["imager"]),
    ],
)
def test_rejects_non_list_payload_container(payload_ids: object) -> None:
    with pytest.raises(ValidationError, match="list of strings"):
        EducationalMissionConfiguration(
            SCENARIO_ID,
            payload_ids,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "payload_id",
    [None, 1, True, ["imager"], StringSubclass("imager")],
)
def test_rejects_non_string_payload_identifier(payload_id: object) -> None:
    with pytest.raises(ValidationError, match="strings"):
        EducationalMissionConfiguration(
            SCENARIO_ID,
            [payload_id],  # type: ignore[list-item]
        )


def test_reordered_inputs_produce_equivalent_configurations() -> None:
    first = EducationalMissionConfiguration(SCENARIO_ID, ["relay", "imager"])
    second = EducationalMissionConfiguration(SCENARIO_ID, ["imager", "relay"])

    assert first == second
    assert first.selected_payload_ids == ("imager", "relay")


def test_configuration_is_immutable() -> None:
    configuration = EducationalMissionConfiguration(SCENARIO_ID, ["imager"])

    with pytest.raises(FrozenInstanceError):
        configuration.scenario_id = "another-scenario"  # type: ignore[misc]
    with pytest.raises(AttributeError):
        configuration.selected_payload_ids.append("relay")  # type: ignore[attr-defined]


def test_validation_does_not_mutate_or_retain_caller_list() -> None:
    payload_ids = ["relay", "imager"]

    configuration = EducationalMissionConfiguration(SCENARIO_ID, payload_ids)
    payload_ids.reverse()
    payload_ids.append("spectrometer")

    assert payload_ids == ["imager", "relay", "spectrometer"]
    assert configuration.selected_payload_ids == ("imager", "relay")
