"""Immutable identifier constants for ARC-08 educational scenarios."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

RESOURCE_SELECTION_SCENARIO_ID = "resource-selection-demo-v1"


@dataclass(frozen=True, slots=True)
class PayloadSpec:
    educational_value_points: int
    budget_units: int
    mass_units: int
    power_units: int


@dataclass(frozen=True, slots=True)
class ResourceLimits:
    budget_units: int
    mass_units: int
    power_units: int
    payload_slots: int


@dataclass(frozen=True, slots=True)
class ScenarioCatalog:
    scenario_id: str
    payloads: Mapping[str, PayloadSpec]
    limits: ResourceLimits

    def __post_init__(self) -> None:
        object.__setattr__(self, "payloads", MappingProxyType(dict(self.payloads)))


_RESOURCE_SELECTION_PAYLOADS = MappingProxyType(
    {
        "imager": PayloadSpec(
            educational_value_points=5,
            budget_units=3,
            mass_units=2,
            power_units=2,
        ),
        "spectrometer": PayloadSpec(
            educational_value_points=8, budget_units=5, mass_units=3, power_units=3
        ),
        "relay": PayloadSpec(
            educational_value_points=3,
            budget_units=2,
            mass_units=1,
            power_units=1,
        ),
    }
)

SCENARIO_CATALOG = MappingProxyType(
    {
        RESOURCE_SELECTION_SCENARIO_ID: ScenarioCatalog(
            scenario_id=RESOURCE_SELECTION_SCENARIO_ID,
            payloads=_RESOURCE_SELECTION_PAYLOADS,
            limits=ResourceLimits(
                budget_units=7,
                mass_units=4,
                power_units=4,
                payload_slots=2,
            ),
        )
    }
)

SCENARIO_PAYLOAD_IDS = MappingProxyType(
    {
        scenario_id: frozenset(scenario.payloads)
        for scenario_id, scenario in SCENARIO_CATALOG.items()
    }
)
