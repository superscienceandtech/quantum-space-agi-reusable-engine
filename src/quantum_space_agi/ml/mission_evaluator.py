"""Deterministic evaluator for the ARC-08 educational mission exercise."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

from quantum_space_agi.ml.mission_configuration import EducationalMissionConfiguration
from quantum_space_agi.ml.mission_scenarios import SCENARIO_CATALOG

EVALUATOR_VERSION = "educational-mission-evaluator/0.1.0"
ViolationCode = Literal["budget", "mass", "power", "slots"]


@dataclass(frozen=True, slots=True)
class ConstraintViolation:
    code: ViolationCode
    observed_total: int
    limit: int

    def __post_init__(self) -> None:
        if type(self.code) is not str:
            raise TypeError("code must be a string")
        if self.code not in ("budget", "mass", "power", "slots"):
            raise ValueError("code must identify a supported constraint")
        if type(self.observed_total) is not int:
            raise TypeError("observed_total must be an integer")
        if type(self.limit) is not int:
            raise TypeError("limit must be an integer")
        if self.limit < 0 or self.observed_total <= self.limit:
            raise ValueError("a violation total must exceed a non-negative limit")


@dataclass(frozen=True, slots=True)
class ResourceTotals:
    budget_units: int
    mass_units: int
    power_units: int
    payload_slots: int

    def __post_init__(self) -> None:
        for field_name in (
            "budget_units",
            "mass_units",
            "power_units",
            "payload_slots",
        ):
            value = getattr(self, field_name)
            if type(value) is not int:
                raise TypeError(f"{field_name} must be an integer")
            if value < 0:
                raise ValueError(f"{field_name} must be non-negative")


@dataclass(frozen=True, slots=True)
class EducationalMissionResult:
    selected_payload_ids: tuple[str, ...]
    evaluator_version: str
    scenario_id: str
    feasible: bool
    violations: tuple[ConstraintViolation, ...]
    resource_totals: ResourceTotals
    educational_score: int | None

    def __post_init__(self) -> None:
        _validate_result_contract(self)


def evaluate_educational_mission(
    configuration: EducationalMissionConfiguration,
) -> EducationalMissionResult:
    """Evaluate one validated configuration against its immutable scenario."""
    if type(configuration) is not EducationalMissionConfiguration:
        raise TypeError("configuration must be an EducationalMissionConfiguration")
    validated_configuration = _validate_configuration_instance(configuration)
    totals, violations, feasible, educational_score = _calculate_outcome(
        validated_configuration
    )
    return EducationalMissionResult(
        selected_payload_ids=validated_configuration.selected_payload_ids,
        evaluator_version=EVALUATOR_VERSION,
        scenario_id=validated_configuration.scenario_id,
        feasible=feasible,
        violations=violations,
        resource_totals=totals,
        educational_score=educational_score,
    )


def serialize_educational_mission_result(
    result: EducationalMissionResult,
) -> bytes:
    """Serialize a result to compact canonical UTF-8 JSON bytes."""
    if type(result) is not EducationalMissionResult:
        raise TypeError("result must be an EducationalMissionResult")
    _validate_result_contract(result)

    payload = {
        "selected_payload_ids": list(result.selected_payload_ids),
        "evaluator_version": result.evaluator_version,
        "scenario_id": result.scenario_id,
        "feasible": result.feasible,
        "violations": [
            {
                "code": violation.code,
                "observed_total": violation.observed_total,
                "limit": violation.limit,
            }
            for violation in result.violations
        ],
        "resource_totals": {
            "budget_units": result.resource_totals.budget_units,
            "mass_units": result.resource_totals.mass_units,
            "power_units": result.resource_totals.power_units,
            "payload_slots": result.resource_totals.payload_slots,
        },
        "educational_score": result.educational_score,
    }
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=False,
    )
    return serialized.encode("utf-8", errors="strict")


def _validate_result_contract(result: EducationalMissionResult) -> None:
    if type(result.selected_payload_ids) is not tuple or any(
        type(payload_id) is not str for payload_id in result.selected_payload_ids
    ):
        raise TypeError("result does not match the selected_payload_ids contract")
    if tuple(sorted(result.selected_payload_ids)) != result.selected_payload_ids:
        raise ValueError("result does not match canonical payload ordering")
    if type(result.evaluator_version) is not str or type(result.scenario_id) is not str:
        raise TypeError("result does not match the evaluator/scenario identifier types")
    if result.evaluator_version != EVALUATOR_VERSION:
        raise ValueError("result does not match the current evaluator version")
    if type(result.feasible) is not bool:
        raise TypeError("result does not match the feasible field type")
    if type(result.violations) is not tuple or any(
        type(violation) is not ConstraintViolation
        or type(violation.code) is not str
        or violation.code not in ("budget", "mass", "power", "slots")
        or type(violation.observed_total) is not int
        or type(violation.limit) is not int
        for violation in result.violations
    ):
        raise TypeError("result does not match the violations structure")
    if type(result.resource_totals) is not ResourceTotals or any(
        type(value) is not int
        for value in (
            result.resource_totals.budget_units,
            result.resource_totals.mass_units,
            result.resource_totals.power_units,
            result.resource_totals.payload_slots,
        )
    ):
        raise TypeError("result does not match the resource_totals structure")
    if (
        result.educational_score is not None
        and type(result.educational_score) is not int
    ):
        raise TypeError("result does not match the educational_score type")

    try:
        result.evaluator_version.encode("utf-8", errors="strict")
        result.scenario_id.encode("utf-8", errors="strict")
        for payload_id in result.selected_payload_ids:
            payload_id.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise ValueError("result strings must be valid UTF-8 text") from exc

    try:
        configuration = EducationalMissionConfiguration(
            result.scenario_id, list(result.selected_payload_ids)
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "result does not match a supported mission configuration"
        ) from exc
    if configuration.selected_payload_ids != result.selected_payload_ids:
        raise ValueError("result does not match canonical payload ordering")

    expected_totals, expected_violations, expected_feasible, expected_score = (
        _calculate_outcome(configuration)
    )
    if (
        result.resource_totals != expected_totals
        or result.violations != expected_violations
        or result.feasible != expected_feasible
        or result.educational_score != expected_score
    ):
        raise ValueError("result does not match the evaluated mission outcome")


def _validate_configuration_instance(
    configuration: EducationalMissionConfiguration,
) -> EducationalMissionConfiguration:
    if (
        type(configuration.scenario_id) is not str
        or type(configuration.selected_payload_ids) is not tuple
        or any(
            type(payload_id) is not str
            for payload_id in configuration.selected_payload_ids
        )
    ):
        raise TypeError("configuration does not match its validated field types")
    try:
        validated = EducationalMissionConfiguration(
            configuration.scenario_id, list(configuration.selected_payload_ids)
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("configuration is invalid") from exc
    if validated.selected_payload_ids != configuration.selected_payload_ids:
        raise ValueError("configuration payload IDs are not in canonical order")
    return validated


def _calculate_outcome(
    configuration: EducationalMissionConfiguration,
) -> tuple[ResourceTotals, tuple[ConstraintViolation, ...], bool, int | None]:
    scenario = SCENARIO_CATALOG[configuration.scenario_id]
    payloads = tuple(
        scenario.payloads[payload_id]
        for payload_id in configuration.selected_payload_ids
    )
    totals = ResourceTotals(
        budget_units=sum(payload.budget_units for payload in payloads),
        mass_units=sum(payload.mass_units for payload in payloads),
        power_units=sum(payload.power_units for payload in payloads),
        payload_slots=len(payloads),
    )
    limits = scenario.limits
    checks: tuple[tuple[ViolationCode, int, int], ...] = (
        ("budget", totals.budget_units, limits.budget_units),
        ("mass", totals.mass_units, limits.mass_units),
        ("power", totals.power_units, limits.power_units),
        ("slots", totals.payload_slots, limits.payload_slots),
    )
    violations = tuple(
        ConstraintViolation(code, observed_total, limit)
        for code, observed_total, limit in checks
        if observed_total > limit
    )
    feasible = not violations
    score = (
        sum(payload.educational_value_points for payload in payloads)
        if feasible
        else None
    )
    return totals, violations, feasible, score
