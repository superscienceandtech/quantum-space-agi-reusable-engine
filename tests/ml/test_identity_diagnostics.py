from copy import deepcopy

import pytest

from quantum_space_agi.ml.identity_diagnostics import (
    audit_partition_assignments,
    diagnose_identity_groups,
)


def row(planet: str, host: str, reference: str) -> dict[str, str]:
    return {"pl_name": planet, "hostname": host, "pl_refname": reference}


def test_reports_multiple_planets_around_one_host_and_group_sizes() -> None:
    report = diagnose_identity_groups(
        [row("p1", "h1", "r1"), row("p2", "h1", "r2"), row("p3", "h2", "r3")]
    )

    assert report.row_count == 3
    assert [(group.hostname, group.row_indices) for group in report.host_groups] == [
        ("h1", (0, 1)),
        ("h2", (2,)),
    ]
    assert report.distinct_host_count == 2
    assert report.host_group_sizes == (2, 1)
    assert report.hosts_with_multiple_rows == ("h1",)
    assert report.largest_host_group_rows == 2
    assert [len(component.row_indices) for component in report.components] == [2, 1]
    assert report.component_sizes == (2, 1)
    assert len(report.singleton_components) == 1
    assert report.largest_component_rows == 2


def test_reports_repeated_references_and_exact_identity_tuples() -> None:
    repeated = row("p1", "h1", "r1")
    report = diagnose_identity_groups(
        [repeated, row("p2", "h2", "r1"), repeated.copy()]
    )

    refs = report.identity_fields[2].repeated_values
    assert [(item.value, item.row_indices) for item in refs] == [("r1", (0, 1, 2))]
    assert report.repeated_identity_tuples[0].identity == ("p1", "h1", "r1")
    assert report.repeated_identity_tuples[0].row_indices == (0, 2)


def test_host_reference_graph_produces_multiple_deterministic_components() -> None:
    rows = [
        row("p1", "h1", "r1"),
        row("p2", "h1", "r2"),
        row("p3", "h2", "r2"),
        row("p4", "h3", "r3"),
    ]

    report = diagnose_identity_groups(rows)

    assert [component.row_indices for component in report.components] == [
        (0, 1, 2),
        (3,),
    ]
    assert report.components[0].hostnames == ("h1", "h2")
    assert report.components[0].references == ("r1", "r2")
    assert [component.component_index for component in report.components] == [0, 1]


def test_reports_majority_component_without_claiming_balanced_feasibility() -> None:
    rows = [row(f"p{i}", "shared-host", f"r{i}") for i in range(5)]
    rows.append(row("other", "other-host", "other-ref"))

    feasibility = diagnose_identity_groups(rows, requested_partitions=2).feasibility

    assert feasibility is not None
    assert feasibility.components_structurally_feasible
    assert feasibility.largest_component_rows == 5
    assert feasibility.largest_component_is_majority
    assert "largest connected component contains a strict majority of rows" in (
        feasibility.warnings
    )


def test_missing_and_malformed_grouping_identities_are_reported() -> None:
    rows = [
        {"pl_name": "p1", "hostname": None, "pl_refname": "r1"},
        {"pl_name": "p2", "pl_refname": " "},
        {"pl_name": "p3", "hostname": 7, "pl_refname": "r3"},
    ]
    report = diagnose_identity_groups(rows, requested_partitions=2)

    host_diagnostics = report.identity_fields[1]
    reference_diagnostics = report.identity_fields[2]
    assert host_diagnostics.missing_row_indices == (0, 1)
    assert host_diagnostics.invalid_type_row_indices == (2,)
    assert reference_diagnostics.missing_row_indices == (1,)
    assert report.feasibility is not None
    assert not report.feasibility.host_structurally_feasible
    assert not report.feasibility.components_structurally_feasible
    assert report.feasibility.missing_host_rows == (0, 1, 2)
    assert report.feasibility.missing_reference_rows == (1,)


def test_repeated_planet_names_are_diagnostic_and_not_deduplicated() -> None:
    rows = [row("same-planet", "h1", "r1"), row("same-planet", "h2", "r2")]
    report = diagnose_identity_groups(rows)

    assert report.row_count == 2
    assert report.identity_fields[0].repeated_values[0].row_indices == (0, 1)
    assert len(report.components) == 2


def test_leakage_audit_reports_host_reference_planet_and_component_crossings() -> None:
    rows = [
        row("p1", "h1", "r1"),
        row("p1", "h2", "r1"),
        row("p3", "h3", "r3"),
    ]

    audit = audit_partition_assignments(rows, ("train", "test", "train"))

    assert audit.host_overlaps == ()
    assert audit.reference_overlaps[0].value == "r1"
    assert audit.reference_overlaps[0].row_indices == (0, 1)
    assert audit.planet_name_overlaps[0].value == "p1"
    assert audit.component_overlaps[0].row_indices == (0, 1)
    assert audit.has_cross_partition_leakage


def test_clean_partitions_have_no_host_or_reference_overlap() -> None:
    rows = [row("p1", "h1", "r1"), row("p2", "h1", "r2"), row("p3", "h2", "r3")]

    audit = audit_partition_assignments(rows, ("train", "train", "test"))

    assert audit.host_overlaps == ()
    assert audit.reference_overlaps == ()
    assert audit.planet_name_overlaps == ()
    assert audit.component_overlaps == ()
    assert not audit.has_cross_partition_leakage


def test_partition_audit_reports_component_crossing_even_without_host_crossing() -> (
    None
):
    rows = [row("p1", "h1", "shared-ref"), row("p2", "h2", "shared-ref")]

    audit = audit_partition_assignments(rows, ("train", "test"))

    assert audit.host_overlaps == ()
    assert audit.reference_overlaps[0].value == "shared-ref"
    assert audit.component_overlaps[0].row_indices == (0, 1)


def test_diagnostics_are_deterministic_and_do_not_mutate_inputs() -> None:
    rows = [row("p2", "h2", "r2"), row("p1", "h1", "r1")]
    original = deepcopy(rows)

    first = diagnose_identity_groups(rows, requested_partitions=2)
    second = diagnose_identity_groups(rows, requested_partitions=2)

    assert first == second
    assert rows == original
    assert [component.row_indices for component in first.components] == [(0,), (1,)]


@pytest.mark.parametrize("assignments", [("train",), ("train", ""), ("train", True)])
def test_partition_audit_rejects_malformed_assignment_contract(
    assignments: tuple[object, ...],
) -> None:
    rows = [row("p1", "h1", "r1"), row("p2", "h2", "r2")]

    with pytest.raises((TypeError, ValueError)):
        audit_partition_assignments(rows, assignments)  # type: ignore[arg-type]
