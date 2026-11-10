from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from quantum_space_agi.errors import ValidationError
from quantum_space_agi.ml import (
    ConstraintViolation,
    EducationalMissionConfiguration,
    ResourceTotals,
    evaluate_educational_mission,
    serialize_educational_mission_result,
)
from quantum_space_agi.ml.mission_scenarios import (
    RESOURCE_SELECTION_SCENARIO_ID,
    SCENARIO_CATALOG,
)


def configuration(*payload_ids: str) -> EducationalMissionConfiguration:
    return EducationalMissionConfiguration(
        RESOURCE_SELECTION_SCENARIO_ID, list(payload_ids)
    )


def test_spectrometer_and_relay_are_feasible_with_score_eleven() -> None:
    result = evaluate_educational_mission(configuration("spectrometer", "relay"))

    assert result.feasible is True
    assert result.educational_score == 11
    assert result.violations == ()
    assert result.selected_payload_ids == ("relay", "spectrometer")


@pytest.mark.parametrize(
    ("payload_id", "score", "budget", "mass", "power"),
    [
        ("imager", 5, 3, 2, 2),
        ("spectrometer", 8, 5, 3, 3),
        ("relay", 3, 2, 1, 1),
    ],
)
def test_each_individual_payload_is_feasible(
    payload_id: str,
    score: int,
    budget: int,
    mass: int,
    power: int,
) -> None:
    result = evaluate_educational_mission(configuration(payload_id))

    assert result.feasible is True
    assert result.educational_score == score
    assert result.resource_totals.budget_units == budget
    assert result.resource_totals.mass_units == mass
    assert result.resource_totals.power_units == power
    assert result.resource_totals.payload_slots == 1


def test_imager_and_relay_are_feasible() -> None:
    result = evaluate_educational_mission(configuration("imager", "relay"))

    assert result.feasible is True
    assert result.educational_score == 8
    assert result.resource_totals.budget_units == 5
    assert result.resource_totals.mass_units == 3
    assert result.resource_totals.power_units == 3
    assert result.resource_totals.payload_slots == 2


def test_exact_budget_mass_power_and_slot_limits_are_feasible() -> None:
    result = evaluate_educational_mission(configuration("spectrometer", "relay"))

    assert result.resource_totals.budget_units == 7
    assert result.resource_totals.mass_units == 4
    assert result.resource_totals.power_units == 4
    assert result.resource_totals.payload_slots == 2
    assert result.feasible is True
    assert result.violations == ()


@pytest.mark.parametrize(
    ("payload_ids", "expected_codes"),
    [
        (("imager", "spectrometer"), ("budget", "mass", "power")),
        (("imager", "relay", "spectrometer"), ("budget", "mass", "power", "slots")),
    ],
)
def test_resource_constraints_emit_expected_violations_in_order(
    payload_ids: tuple[str, ...], expected_codes: tuple[str, ...]
) -> None:
    result = evaluate_educational_mission(configuration(*payload_ids))

    assert tuple(violation.code for violation in result.violations) == expected_codes
    assert result.feasible is False
    assert result.educational_score is None


def test_each_violation_type_is_reported_with_its_observed_total_and_limit() -> None:
    resource_overages = evaluate_educational_mission(
        configuration("imager", "spectrometer")
    )
    all_overages = evaluate_educational_mission(
        configuration("imager", "relay", "spectrometer")
    )

    assert [
        (violation.code, violation.observed_total, violation.limit)
        for violation in resource_overages.violations
    ] == [("budget", 8, 7), ("mass", 5, 4), ("power", 5, 4)]
    assert [
        (violation.code, violation.observed_total, violation.limit)
        for violation in all_overages.violations
    ] == [
        ("budget", 10, 7),
        ("mass", 6, 4),
        ("power", 6, 4),
        ("slots", 3, 2),
    ]


def test_infeasible_result_has_no_educational_score() -> None:
    result = evaluate_educational_mission(
        configuration("imager", "relay", "spectrometer")
    )

    assert result.educational_score is None


@pytest.mark.parametrize(
    "payload_ids",
    [[], ["unknown-payload"]],
)
def test_invalid_configuration_is_rejected_before_evaluation(
    payload_ids: list[str],
) -> None:
    with pytest.raises(ValidationError):
        EducationalMissionConfiguration(RESOURCE_SELECTION_SCENARIO_ID, payload_ids)


def test_result_identifies_evaluator_version_and_scenario() -> None:
    result = evaluate_educational_mission(configuration("relay"))

    assert result.evaluator_version == "educational-mission-evaluator/0.1.0"
    assert result.scenario_id == RESOURCE_SELECTION_SCENARIO_ID


def test_repeated_and_reordered_evaluations_are_deterministic() -> None:
    first_configuration = configuration("spectrometer", "relay")
    reordered_configuration = configuration("relay", "spectrometer")

    first = evaluate_educational_mission(first_configuration)
    repeated = evaluate_educational_mission(first_configuration)
    reordered = evaluate_educational_mission(reordered_configuration)

    assert first == repeated == reordered


def test_evaluation_does_not_mutate_configuration_or_catalog() -> None:
    mission = configuration("relay", "imager")
    catalog_before = dict(SCENARIO_CATALOG)
    payload_catalog_before = dict(
        SCENARIO_CATALOG[RESOURCE_SELECTION_SCENARIO_ID].payloads
    )

    evaluate_educational_mission(mission)

    assert mission.selected_payload_ids == ("imager", "relay")
    assert dict(SCENARIO_CATALOG) == catalog_before
    assert (
        dict(SCENARIO_CATALOG[RESOURCE_SELECTION_SCENARIO_ID].payloads)
        == payload_catalog_before
    )
    with pytest.raises(TypeError):
        SCENARIO_CATALOG["new-scenario"] = SCENARIO_CATALOG[
            RESOURCE_SELECTION_SCENARIO_ID
        ]  # type: ignore[index]
    with pytest.raises(TypeError):
        SCENARIO_CATALOG[RESOURCE_SELECTION_SCENARIO_ID].payloads["new-payload"] = next(
            iter(payload_catalog_before.values())
        )  # type: ignore[index]


def test_result_and_nested_values_are_immutable() -> None:
    result = evaluate_educational_mission(configuration("imager", "spectrometer"))

    with pytest.raises(FrozenInstanceError):
        result.feasible = True  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.resource_totals.budget_units = 0  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.violations[0].limit = 0  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        SCENARIO_CATALOG[RESOURCE_SELECTION_SCENARIO_ID].payloads[
            "imager"
        ].budget_units = 0  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        SCENARIO_CATALOG[RESOURCE_SELECTION_SCENARIO_ID].limits.budget_units = 0  # type: ignore[misc]
    with pytest.raises(AttributeError):
        result.selected_payload_ids.append("relay")  # type: ignore[attr-defined]


def test_result_serializes_to_canonical_compact_utf8_json() -> None:
    result = evaluate_educational_mission(configuration("spectrometer", "relay"))

    assert serialize_educational_mission_result(result) == (
        b'{"selected_payload_ids":["relay","spectrometer"],'
        b'"evaluator_version":"educational-mission-evaluator/0.1.0",'
        b'"scenario_id":"resource-selection-demo-v1","feasible":true,'
        b'"violations":[],"resource_totals":{"budget_units":7,'
        b'"mass_units":4,"power_units":4,"payload_slots":2},'
        b'"educational_score":11}'
    )


def test_infeasible_result_serializes_score_as_json_null() -> None:
    result = evaluate_educational_mission(
        configuration("imager", "relay", "spectrometer")
    )

    assert b'"educational_score":null' in serialize_educational_mission_result(result)


@pytest.mark.parametrize("unsupported_score", [True, 1.5])
def test_result_serializer_rejects_unsupported_numeric_values(
    unsupported_score: object,
) -> None:
    malformed_result = evaluate_educational_mission(configuration("relay"))
    object.__setattr__(malformed_result, "educational_score", unsupported_score)

    with pytest.raises(TypeError, match="educational_score"):
        serialize_educational_mission_result(malformed_result)


def test_result_serializer_rejects_strings_that_are_not_valid_utf8() -> None:
    malformed_result = evaluate_educational_mission(configuration("relay"))
    object.__setattr__(malformed_result, "scenario_id", "\ud800")

    with pytest.raises(ValueError, match="valid UTF-8"):
        serialize_educational_mission_result(malformed_result)


def test_reordered_configurations_serialize_to_identical_bytes() -> None:
    first = evaluate_educational_mission(configuration("spectrometer", "relay"))
    second = evaluate_educational_mission(configuration("relay", "spectrometer"))

    assert serialize_educational_mission_result(first) == (
        serialize_educational_mission_result(second)
    )


def test_non_ascii_payload_id_is_not_representable_in_v1() -> None:
    # V1 exposes only fixed ASCII catalog IDs and a fixed ASCII evaluator version.
    with pytest.raises(ValidationError, match="unknown payload"):
        EducationalMissionConfiguration(RESOURCE_SELECTION_SCENARIO_ID, ["imáger"])


def test_result_construction_rejects_mutable_nested_containers() -> None:
    result = evaluate_educational_mission(configuration("relay"))

    with pytest.raises(TypeError, match="selected_payload_ids"):
        replace(result, selected_payload_ids=["relay"])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="violations"):
        replace(result, violations=[])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="budget_units"):
        ResourceTotals(True, 1, 1, 1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="observed_total"):
        ConstraintViolation("budget", [2], 1)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    [
        ("scenario_id", "unknown-scenario"),
        ("evaluator_version", "educational-mission-evaluator/0.0.0"),
        ("selected_payload_ids", ("relay", "relay")),
    ],
)
def test_result_construction_rejects_invalid_identity_contract(
    field_name: str, replacement: object
) -> None:
    result = evaluate_educational_mission(configuration("relay"))

    with pytest.raises((TypeError, ValueError)):
        replace(result, **{field_name: replacement})


@pytest.mark.parametrize(
    ("payload_ids", "replacement"),
    [
        (("relay",), {"feasible": False}),
        (("imager", "spectrometer"), {"feasible": True}),
        (("imager", "spectrometer"), {"violations": ()}),
        (("spectrometer", "relay"), {"educational_score": 10}),
        (("imager", "relay", "spectrometer"), {"educational_score": 0}),
        (
            ("spectrometer", "relay"),
            {"resource_totals": ResourceTotals(6, 4, 4, 2)},
        ),
        (
            ("imager", "relay", "spectrometer"),
            {
                "violations": (
                    ConstraintViolation("slots", 3, 2),
                    ConstraintViolation("budget", 10, 7),
                    ConstraintViolation("mass", 6, 4),
                    ConstraintViolation("power", 6, 4),
                )
            },
        ),
    ],
)
def test_result_construction_rejects_semantic_inconsistencies(
    payload_ids: tuple[str, ...], replacement: dict[str, object]
) -> None:
    result = evaluate_educational_mission(configuration(*payload_ids))

    with pytest.raises(ValueError, match="result does not match"):
        replace(result, **replacement)


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    [
        ("feasible", True),
        ("violations", ()),
        ("educational_score", 0),
        ("resource_totals", ResourceTotals(6, 4, 4, 2)),
        (
            "violations",
            (
                ConstraintViolation("slots", 3, 2),
                ConstraintViolation("budget", 10, 7),
                ConstraintViolation("mass", 6, 4),
                ConstraintViolation("power", 6, 4),
            ),
        ),
    ],
)
def test_serializer_rejects_tampered_result_semantics(
    field_name: str, replacement: object
) -> None:
    result = evaluate_educational_mission(
        configuration("imager", "relay", "spectrometer")
    )
    object.__setattr__(result, field_name, replacement)

    with pytest.raises(ValueError, match="result does not match"):
        serialize_educational_mission_result(result)


def test_rejects_non_configuration_input() -> None:
    with pytest.raises(TypeError, match="EducationalMissionConfiguration"):
        evaluate_educational_mission(object())  # type: ignore[arg-type]
