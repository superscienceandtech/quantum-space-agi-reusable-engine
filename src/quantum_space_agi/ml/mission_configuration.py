"""Validated immutable configuration for the educational mission exercise."""

from __future__ import annotations

from dataclasses import dataclass

from quantum_space_agi.errors import ValidationError
from quantum_space_agi.ml.mission_scenarios import SCENARIO_PAYLOAD_IDS


@dataclass(frozen=True, slots=True, init=False)
class EducationalMissionConfiguration:
    """A validated mission choice with payload IDs stored in canonical order.

    The constructor accepts the JSON-compatible list contract and stores an
    immutable tuple so the configuration cannot be changed after validation.
    """

    scenario_id: str
    selected_payload_ids: tuple[str, ...]

    def __init__(self, scenario_id: str, selected_payload_ids: list[str]) -> None:
        if type(scenario_id) is not str:
            raise ValidationError("scenario_id must be a string")
        if scenario_id not in SCENARIO_PAYLOAD_IDS:
            raise ValidationError("scenario_id is not a supported scenario")
        if not isinstance(selected_payload_ids, list):
            raise ValidationError("selected_payload_ids must be a list of strings")
        if not selected_payload_ids:
            raise ValidationError("selected_payload_ids must be non-empty")
        if any(type(payload_id) is not str for payload_id in selected_payload_ids):
            raise ValidationError("selected_payload_ids must contain only strings")

        normalized_payload_ids = tuple(sorted(selected_payload_ids))
        if len(set(normalized_payload_ids)) != len(normalized_payload_ids):
            raise ValidationError("selected_payload_ids must not contain duplicates")

        known_payload_ids = SCENARIO_PAYLOAD_IDS[scenario_id]
        if any(
            payload_id not in known_payload_ids for payload_id in normalized_payload_ids
        ):
            raise ValidationError("selected_payload_ids contains an unknown payload")

        object.__setattr__(self, "scenario_id", scenario_id)
        object.__setattr__(self, "selected_payload_ids", normalized_payload_ids)
