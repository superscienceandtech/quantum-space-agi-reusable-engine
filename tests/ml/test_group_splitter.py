from copy import deepcopy

import pytest

from quantum_space_agi.ml.group_splitter import (
    ORDERING_STRATEGY,
    PARTITIONS,
    GroupSplitError,
    SplitConfiguration,
    split_by_host,
)


def config(seed: int = 17) -> SplitConfiguration:
    return SplitConfiguration((0.6, 0.2, 0.2), seed)


def rows_for_hosts(hosts: list[str]) -> list[dict[str, str]]:
    return [
        {
            "pl_name": f"planet-{index}",
            "hostname": host,
            "pl_refname": f"reference-{index}",
        }
        for index, host in enumerate(hosts)
    ]


def test_creates_three_host_disjoint_non_empty_partitions() -> None:
    rows = rows_for_hosts([f"host-{index}" for index in range(12)])

    result = split_by_host(rows, config())

    assert tuple(partition.name for partition in result.partitions) == PARTITIONS
    assert all(partition.row_count > 0 for partition in result.partitions)
    assert len(result.row_assignments) == len(rows)
    assert {assignment.partition for assignment in result.host_assignments} == set(
        PARTITIONS
    )
    assert result.leakage_audit.host_overlaps == ()


def test_multiple_rows_for_one_host_are_kept_in_one_partition() -> None:
    rows = rows_for_hosts(["shared", "shared", "host-b", "host-c", "host-d"])

    result = split_by_host(rows, config())

    assert result.row_assignments[0] == result.row_assignments[1]
    assert (
        next(
            assignment
            for assignment in result.host_assignments
            if assignment.hostname == "shared"
        ).row_count
        == 2
    )
    assert result.leakage_audit.host_overlaps == ()


def test_identical_input_and_seed_produce_identical_result() -> None:
    rows = rows_for_hosts([f"host-{index}" for index in range(15)])

    assert split_by_host(rows, config(42)) == split_by_host(rows, config(42))


def test_different_seed_can_produce_a_different_permitted_allocation() -> None:
    rows = rows_for_hosts([f"host-{index}" for index in range(12)])

    first = split_by_host(rows, SplitConfiguration((1 / 3, 1 / 3, 1 / 3), 1))
    second = split_by_host(rows, SplitConfiguration((1 / 3, 1 / 3, 1 / 3), 2))

    assert first.host_assignments != second.host_assignments
    assert first.leakage_audit.host_overlaps == second.leakage_audit.host_overlaps == ()


def test_references_and_components_are_reported_without_forcing_reallocation() -> None:
    rows = [
        {"pl_name": "p1", "hostname": "h1", "pl_refname": "shared-ref"},
        {"pl_name": "p2", "hostname": "h2", "pl_refname": "shared-ref"},
        {"pl_name": "p3", "hostname": "h3", "pl_refname": "ref-3"},
    ]

    result = split_by_host(rows, SplitConfiguration((1 / 3, 1 / 3, 1 / 3), 8))

    assert result.leakage_audit.host_overlaps == ()
    assert result.leakage_audit.reference_overlaps[0].value == "shared-ref"
    assert result.leakage_audit.component_overlaps[0].row_indices == (0, 1)
    assert len({item.partition for item in result.host_assignments}) == 3


def test_invalid_partition_configurations_are_rejected() -> None:
    with pytest.raises(GroupSplitError, match="sum to 1.0") as exc_info:
        SplitConfiguration((0.5, 0.25, 0.1), 1)
    assert exc_info.value.code == "invalid_configuration"
    with pytest.raises(GroupSplitError, match="built-in floats") as exc_info:
        SplitConfiguration((0.5, 0.25, True), 1)  # type: ignore[arg-type]
    assert exc_info.value.code == "invalid_configuration"
    with pytest.raises(GroupSplitError, match="built-in integer"):
        SplitConfiguration((0.5, 0.25, 0.25), True)  # type: ignore[arg-type]


def test_too_few_host_groups_fails_without_row_level_fallback() -> None:
    rows = rows_for_hosts(["host-a", "host-a", "host-b"])

    with pytest.raises(GroupSplitError) as exc_info:
        split_by_host(rows, config())

    assert exc_info.value.code == "insufficient_groups"
    assert "three distinct" in str(exc_info.value)


@pytest.mark.parametrize(
    "rows",
    [
        rows_for_hosts(["host-a", "host-b", "host-c"])[:2]
        + [{"pl_name": "p3", "pl_refname": "r3"}],
        rows_for_hosts(["host-a", "host-b", "host-c"])[:2]
        + [{"pl_name": "p3", "hostname": "  ", "pl_refname": "r3"}],
    ],
)
def test_missing_or_blank_group_key_fails_with_row_indices(
    rows: list[dict[str, str]],
) -> None:
    with pytest.raises(GroupSplitError) as exc_info:
        split_by_host(rows, config())

    assert exc_info.value.code == "missing_group_key"
    assert exc_info.value.row_indices == (2,)


def test_indivisible_large_host_group_can_make_row_ratios_imperfect() -> None:
    rows = rows_for_hosts(["large-host"] * 8 + ["small-host-a", "small-host-b"])

    result = split_by_host(rows, SplitConfiguration((0.7, 0.15, 0.15), 4))

    assert tuple(partition.row_count for partition in result.partitions) == (8, 1, 1)
    assert tuple(partition.host_group_count for partition in result.partitions) == (
        1,
        1,
        1,
    )
    assert result.row_assignments[:8] == ("train",) * 8


def test_input_records_are_not_mutated() -> None:
    rows = rows_for_hosts([f"host-{index}" for index in range(5)])
    original = deepcopy(rows)

    split_by_host(rows, config())

    assert rows == original


def test_reproducibility_metadata_is_explicit() -> None:
    result = split_by_host(
        rows_for_hosts([f"host-{index}" for index in range(6)]), config(9)
    )

    assert result.configuration == config(9)
    assert result.grouping_field == "hostname"
    assert result.ordering_strategy == ORDERING_STRATEGY
    assert len(result.host_assignments) == 6
    assert sum(partition.row_count for partition in result.partitions) == 6
    assert sum(partition.host_group_count for partition in result.partitions) == 6
    assert len(result.row_assignments) == 6


def test_splitter_rejects_non_mapping_input() -> None:
    with pytest.raises(GroupSplitError) as exc_info:
        split_by_host(["not a row"] * 3, config())  # type: ignore[list-item]

    assert exc_info.value.code == "invalid_rows"
