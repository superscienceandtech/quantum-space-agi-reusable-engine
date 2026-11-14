"""Deterministic, offline identity, grouping, and leakage diagnostics.

Identity strings are compared exactly. This module does not normalize, resolve
aliases, deduplicate records, create partitions, or determine scientific fitness.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeAlias

from quantum_space_agi.ml.dataset_ingestion import DatasetIngestionResult

Row: TypeAlias = Mapping[str, object]
IDENTITY_FIELDS = ("pl_name", "hostname", "pl_refname")


@dataclass(frozen=True, slots=True)
class RepeatedIdentityValue:
    """One exact identity string found on multiple rows."""

    value: str
    row_indices: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class RepeatedIdentityTuple:
    """One exact (planet, host, reference) tuple found on multiple rows."""

    identity: tuple[str, str, str]
    row_indices: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class IdentityFieldDiagnostics:
    """Missing, malformed, and repeated-value summary for an identity field."""

    field: str
    missing_row_indices: tuple[int, ...]
    invalid_type_row_indices: tuple[int, ...]
    repeated_values: tuple[RepeatedIdentityValue, ...]


@dataclass(frozen=True, slots=True)
class HostGroup:
    """Rows associated with one exact, non-blank hostname value."""

    hostname: str
    row_indices: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class ConnectedComponent:
    """Rows connected through exact host/reference identity associations."""

    component_index: int
    row_indices: tuple[int, ...]
    hostnames: tuple[str, ...]
    references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GroupingFeasibility:
    """Structural group-count assessment, not a proposed split assignment."""

    requested_partitions: int
    host_group_count: int
    host_structurally_feasible: bool
    component_count: int
    components_structurally_feasible: bool
    largest_component_rows: int
    largest_component_is_majority: bool
    missing_host_rows: tuple[int, ...]
    missing_reference_rows: tuple[int, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IdentityGroupingReport:
    """Identity audit, exact host groups, and host-reference components."""

    row_count: int
    identity_fields: tuple[IdentityFieldDiagnostics, ...]
    repeated_identity_tuples: tuple[RepeatedIdentityTuple, ...]
    host_groups: tuple[HostGroup, ...]
    components: tuple[ConnectedComponent, ...]
    feasibility: GroupingFeasibility | None

    @property
    def distinct_host_count(self) -> int:
        """Number of exact, usable hostname values."""
        return len(self.host_groups)

    @property
    def host_group_sizes(self) -> tuple[int, ...]:
        """Host group sizes in deterministic hostname order."""
        return tuple(len(group.row_indices) for group in self.host_groups)

    @property
    def hosts_with_multiple_rows(self) -> tuple[str, ...]:
        """Exact hostnames represented by more than one row."""
        return tuple(
            group.hostname for group in self.host_groups if len(group.row_indices) > 1
        )

    @property
    def largest_host_group_rows(self) -> int:
        """Largest number of rows associated with one exact hostname."""
        return max(self.host_group_sizes, default=0)

    @property
    def component_sizes(self) -> tuple[int, ...]:
        """Component sizes in deterministic component-index order."""
        return tuple(len(component.row_indices) for component in self.components)

    @property
    def singleton_components(self) -> tuple[ConnectedComponent, ...]:
        """Components containing exactly one source row."""
        return tuple(
            component
            for component in self.components
            if len(component.row_indices) == 1
        )

    @property
    def largest_component_rows(self) -> int:
        """Largest number of rows in one host-reference component."""
        return max(self.component_sizes, default=0)


@dataclass(frozen=True, slots=True)
class IngestedIdentityDiagnostics:
    """Identity diagnostics for mechanically accepted rows plus source mapping.

    Indices inside ``report`` refer to positions in the accepted-record sequence.
    ``source_row_indices`` maps each such position back to its original VOTable
    row. Mechanical acceptance is not scientific eligibility.
    """

    source_row_indices: tuple[int, ...]
    report: IdentityGroupingReport

    def __post_init__(self) -> None:
        if type(self.source_row_indices) is not tuple or any(
            type(index) is not int or index < 0 for index in self.source_row_indices
        ):
            raise ValueError("source_row_indices must be a tuple of non-negative ints")
        if len(set(self.source_row_indices)) != len(self.source_row_indices):
            raise ValueError("source_row_indices must be unique")
        if type(self.report) is not IdentityGroupingReport:
            raise TypeError("report must be an IdentityGroupingReport")
        if self.report.row_count != len(self.source_row_indices):
            raise ValueError("source row mapping length must match report row count")

    def source_indices_for(self, local_indices: Sequence[int]) -> tuple[int, ...]:
        """Map report-local indices back to original VOTable row positions."""
        if isinstance(local_indices, (str, bytes)) or not isinstance(
            local_indices, Sequence
        ):
            raise TypeError("local_indices must be a sequence of integers")
        indices = tuple(local_indices)
        if any(
            type(index) is not int or not 0 <= index < len(self.source_row_indices)
            for index in indices
        ):
            raise ValueError("local index is outside the accepted-record mapping")
        return tuple(self.source_row_indices[index] for index in indices)


@dataclass(frozen=True, slots=True)
class PartitionIdentityOverlap:
    """One exact identity value assigned to multiple proposed partitions."""

    field: str
    value: str
    partition_labels: tuple[str, ...]
    row_indices: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class ComponentPartitionOverlap:
    """One host-reference component assigned across multiple partitions."""

    component_index: int
    partition_labels: tuple[str, ...]
    row_indices: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class LeakageAuditReport:
    """Cross-partition identity findings; no assignments are repaired."""

    host_overlaps: tuple[PartitionIdentityOverlap, ...]
    reference_overlaps: tuple[PartitionIdentityOverlap, ...]
    planet_name_overlaps: tuple[PartitionIdentityOverlap, ...]
    component_overlaps: tuple[ComponentPartitionOverlap, ...]
    rows_missing_host: tuple[int, ...]
    rows_missing_reference: tuple[int, ...]

    @property
    def has_cross_partition_leakage(self) -> bool:
        """Whether any audited host, reference, planet, or component crosses."""
        return bool(
            self.host_overlaps
            or self.reference_overlaps
            or self.planet_name_overlaps
            or self.component_overlaps
        )


def diagnose_identity_groups(
    rows: Sequence[Row], *, requested_partitions: int | None = None
) -> IdentityGroupingReport:
    """Report exact identity repetition and host/reference grouping structure.

    A connected component joins rows sharing an exact usable hostname or
    reference. Each row with neither key becomes its own isolated component and
    is also reported as missing grouping metadata. Components are deterministic
    and indexed by their smallest source row index.
    """
    normalized_rows = _validate_rows(rows)
    if requested_partitions is not None and (
        type(requested_partitions) is not int or requested_partitions < 2
    ):
        raise ValueError("requested_partitions must be an integer of at least 2")

    field_reports = tuple(
        _field_diagnostics(normalized_rows, field) for field in IDENTITY_FIELDS
    )
    repeated_tuples = _repeated_tuples(normalized_rows)
    host_groups = _host_groups(normalized_rows)
    components = _connected_components(normalized_rows)
    feasibility = (
        _feasibility(
            normalized_rows,
            host_groups,
            components,
            requested_partitions,
        )
        if requested_partitions is not None
        else None
    )
    return IdentityGroupingReport(
        row_count=len(normalized_rows),
        identity_fields=field_reports,
        repeated_identity_tuples=repeated_tuples,
        host_groups=host_groups,
        components=components,
        feasibility=feasibility,
    )


def diagnose_ingested_identities(
    ingestion: DatasetIngestionResult,
    *,
    requested_partitions: int | None = None,
) -> IngestedIdentityDiagnostics:
    """Diagnose mechanically accepted ingestion rows without losing source IDs.

    Excluded rows and their reasons remain in ``ingestion.exclusion_ledger``.
    This function does not decide scientific eligibility or create partitions.
    """
    if type(ingestion) is not DatasetIngestionResult:
        raise TypeError("ingestion must be a DatasetIngestionResult")
    report = diagnose_identity_groups(
        ingestion.accepted_records,
        requested_partitions=requested_partitions,
    )
    return IngestedIdentityDiagnostics(
        source_row_indices=ingestion.accepted_source_row_indices,
        report=report,
    )


def audit_partition_assignments(
    rows: Sequence[Row], assignments: Sequence[str]
) -> LeakageAuditReport:
    """Audit proposed partition labels for exact identity/component overlap.

    ``assignments[i]`` labels ``rows[i]``. Labels must be non-empty built-in
    strings and there must be exactly one label per row. The function reports
    overlaps; it never changes an assignment or creates a split.
    """
    normalized_rows = _validate_rows(rows)
    if isinstance(assignments, (str, bytes)) or not isinstance(assignments, Sequence):
        raise TypeError("assignments must be a sequence of partition labels")
    labels = tuple(assignments)
    if len(labels) != len(normalized_rows):
        raise ValueError("assignments length must match the number of rows")
    if any(type(label) is not str or not label for label in labels):
        raise TypeError("partition labels must be non-empty built-in strings")

    overlaps = {
        field: _partition_overlaps(normalized_rows, labels, field)
        for field in IDENTITY_FIELDS
    }
    components = _connected_components(normalized_rows)
    component_overlaps = tuple(
        ComponentPartitionOverlap(
            component_index=component.component_index,
            partition_labels=tuple(
                sorted({labels[index] for index in component.row_indices})
            ),
            row_indices=component.row_indices,
        )
        for component in components
        if len({labels[index] for index in component.row_indices}) > 1
    )
    return LeakageAuditReport(
        host_overlaps=overlaps["hostname"],
        reference_overlaps=overlaps["pl_refname"],
        planet_name_overlaps=overlaps["pl_name"],
        component_overlaps=component_overlaps,
        rows_missing_host=_unusable_identity_indices(normalized_rows, "hostname"),
        rows_missing_reference=_unusable_identity_indices(
            normalized_rows, "pl_refname"
        ),
    )


def _validate_rows(rows: Sequence[Row]) -> tuple[Row, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise TypeError("rows must be a sequence of row mappings")
    normalized = tuple(rows)
    if any(not isinstance(row, Mapping) for row in normalized):
        raise TypeError("each row must be a mapping")
    if any(any(type(key) is not str for key in row) for row in normalized):
        raise TypeError("row keys must be strings")
    return normalized


def _identity_value(row: Row, field: str) -> str | None:
    value = row.get(field)
    if type(value) is not str or not value.strip():
        return None
    return value


def _field_diagnostics(rows: tuple[Row, ...], field: str) -> IdentityFieldDiagnostics:
    missing: list[int] = []
    invalid_type: list[int] = []
    values: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        if field not in row or row[field] is None:
            missing.append(index)
            continue
        value = row[field]
        if type(value) is not str:
            invalid_type.append(index)
            continue
        if not value.strip():
            missing.append(index)
            continue
        values.setdefault(value, []).append(index)
    repeated = tuple(
        RepeatedIdentityValue(value, tuple(indices))
        for value, indices in sorted(values.items())
        if len(indices) > 1
    )
    return IdentityFieldDiagnostics(
        field, tuple(missing), tuple(invalid_type), repeated
    )


def _repeated_tuples(rows: tuple[Row, ...]) -> tuple[RepeatedIdentityTuple, ...]:
    tuples: dict[tuple[str, str, str], list[int]] = {}
    for index, row in enumerate(rows):
        planet = _identity_value(row, "pl_name")
        host = _identity_value(row, "hostname")
        reference = _identity_value(row, "pl_refname")
        if planet is not None and host is not None and reference is not None:
            tuples.setdefault((planet, host, reference), []).append(index)
    return tuple(
        RepeatedIdentityTuple(identity, tuple(indices))
        for identity, indices in sorted(tuples.items())
        if len(indices) > 1
    )


def _host_groups(rows: tuple[Row, ...]) -> tuple[HostGroup, ...]:
    grouped: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        host = _identity_value(row, "hostname")
        if host is not None:
            grouped.setdefault(host, []).append(index)
    return tuple(
        HostGroup(host, tuple(indices)) for host, indices in sorted(grouped.items())
    )


def _connected_components(rows: tuple[Row, ...]) -> tuple[ConnectedComponent, ...]:
    parent = list(range(len(rows)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[max(left_root, right_root)] = min(left_root, right_root)

    first_row_for_node: dict[tuple[str, str], int] = {}
    for index, row in enumerate(rows):
        for field, node_type in (("hostname", "host"), ("pl_refname", "reference")):
            value = _identity_value(row, field)
            if value is None:
                continue
            node = (node_type, value)
            if node in first_row_for_node:
                union(index, first_row_for_node[node])
            else:
                first_row_for_node[node] = index

    rows_by_root: dict[int, list[int]] = {}
    for index in range(len(rows)):
        rows_by_root.setdefault(find(index), []).append(index)

    components: list[ConnectedComponent] = []
    for row_indices in sorted(rows_by_root.values(), key=lambda values: values[0]):
        hosts = sorted(
            {
                host
                for index in row_indices
                if (host := _identity_value(rows[index], "hostname")) is not None
            }
        )
        references = sorted(
            {
                reference
                for index in row_indices
                if (reference := _identity_value(rows[index], "pl_refname")) is not None
            }
        )
        components.append(
            ConnectedComponent(
                len(components), tuple(row_indices), tuple(hosts), tuple(references)
            )
        )
    return tuple(components)


def _feasibility(
    rows: tuple[Row, ...],
    host_groups: tuple[HostGroup, ...],
    components: tuple[ConnectedComponent, ...],
    requested_partitions: int,
) -> GroupingFeasibility:
    missing_hosts = _unusable_identity_indices(rows, "hostname")
    missing_references = _unusable_identity_indices(rows, "pl_refname")
    largest_component = max(
        (len(component.row_indices) for component in components), default=0
    )
    warnings: list[str] = []
    if len(host_groups) < requested_partitions:
        warnings.append("fewer distinct hosts than requested partitions")
    if missing_hosts:
        warnings.append("missing or invalid hostname prevents complete host grouping")
    if len(components) < requested_partitions:
        warnings.append("fewer connected components than requested partitions")
    if missing_hosts or missing_references:
        warnings.append(
            "missing or invalid graph key prevents complete component grouping"
        )
    if rows and largest_component * 2 > len(rows):
        warnings.append(
            "largest connected component contains a strict majority of rows"
        )
    return GroupingFeasibility(
        requested_partitions=requested_partitions,
        host_group_count=len(host_groups),
        host_structurally_feasible=(
            len(host_groups) >= requested_partitions and not missing_hosts
        ),
        component_count=len(components),
        components_structurally_feasible=(
            len(components) >= requested_partitions
            and not missing_hosts
            and not missing_references
        ),
        largest_component_rows=largest_component,
        largest_component_is_majority=bool(rows and largest_component * 2 > len(rows)),
        missing_host_rows=missing_hosts,
        missing_reference_rows=missing_references,
        warnings=tuple(warnings),
    )


def _unusable_identity_indices(rows: tuple[Row, ...], field: str) -> tuple[int, ...]:
    return tuple(
        index for index, row in enumerate(rows) if _identity_value(row, field) is None
    )


def _partition_overlaps(
    rows: tuple[Row, ...], assignments: tuple[str, ...], field: str
) -> tuple[PartitionIdentityOverlap, ...]:
    assigned: dict[str, list[tuple[int, str]]] = {}
    for index, row in enumerate(rows):
        identity = _identity_value(row, field)
        if identity is not None:
            assigned.setdefault(identity, []).append((index, assignments[index]))
    return tuple(
        PartitionIdentityOverlap(
            field=field,
            value=value,
            partition_labels=tuple(sorted({label for _, label in values})),
            row_indices=tuple(index for index, _ in values),
        )
        for value, values in sorted(assigned.items())
        if len({label for _, label in values}) > 1
    )
