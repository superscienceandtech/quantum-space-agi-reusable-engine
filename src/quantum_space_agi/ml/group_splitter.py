"""Deterministic host-grouped train/validation/test allocation."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeAlias, cast

from quantum_space_agi.ml.identity_diagnostics import (
    LeakageAuditReport,
    Row,
    audit_partition_assignments,
)

PARTITIONS = ("train", "validation", "test")
HOST_FIELD = "hostname"
ORDERING_STRATEGY = "sha256-seeded-host-order-v1"
_Proportions: TypeAlias = tuple[float, float, float]


class GroupSplitError(ValueError):
    """Machine-readable failure to create a host-disjoint group allocation."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        row_indices: tuple[int, ...] = (),
    ) -> None:
        self.code = code
        self.row_indices = row_indices
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class SplitConfiguration:
    """Explicit row-proportion targets and seed for exactly three partitions."""

    proportions: _Proportions
    seed: int

    def __post_init__(self) -> None:
        if type(self.proportions) is not tuple or len(self.proportions) != 3:
            raise GroupSplitError(
                "invalid_configuration", "proportions must be a three-item tuple"
            )
        if any(type(value) is not float for value in self.proportions):
            raise GroupSplitError(
                "invalid_configuration", "proportions must contain built-in floats"
            )
        if any(not math.isfinite(value) or value <= 0 for value in self.proportions):
            raise GroupSplitError(
                "invalid_configuration",
                "proportions must be finite and greater than zero",
            )
        if not math.isclose(math.fsum(self.proportions), 1.0, rel_tol=0, abs_tol=1e-12):
            raise GroupSplitError(
                "invalid_configuration", "proportions must sum to 1.0"
            )
        if type(self.seed) is not int:
            raise GroupSplitError(
                "invalid_configuration", "seed must be a built-in integer"
            )


@dataclass(frozen=True, slots=True)
class HostPartitionAssignment:
    """Partition assigned to one exact hostname group."""

    hostname: str
    partition: str
    row_count: int


@dataclass(frozen=True, slots=True)
class PartitionSummary:
    """Assigned rows and host groups for one named partition."""

    name: str
    row_count: int
    host_group_count: int


@dataclass(frozen=True, slots=True)
class GroupSplitResult:
    """Reproducible row assignments and post-allocation leakage diagnostics."""

    configuration: SplitConfiguration
    grouping_field: str
    ordering_strategy: str
    host_assignments: tuple[HostPartitionAssignment, ...]
    row_assignments: tuple[str, ...]
    partitions: tuple[PartitionSummary, ...]
    leakage_audit: LeakageAuditReport


def split_by_host(
    rows: Sequence[Row], configuration: SplitConfiguration
) -> GroupSplitResult:
    """Allocate complete exact-host groups across train/validation/test.

    Proportions are explicit target row shares, not scientific recommendations.
    Groups are processed in deterministic seed-derived order (large groups first)
    and assigned greedily to minimize the incremental normalized squared error
    from those target row counts. Whole groups remain intact; actual proportions
    may differ because host groups are indivisible. There is no row-level fallback.

    Callers are expected to run the Phase 4.1 mechanical feature/target checks
    first. This function independently validates the host grouping key and uses
    Phase 4.2 diagnostics after allocation. It does not establish scientific
    eligibility or validate a proposed evaluation protocol.
    """
    if not isinstance(configuration, SplitConfiguration):
        raise GroupSplitError(
            "invalid_configuration", "configuration must be SplitConfiguration"
        )
    normalized_rows = _validate_rows(rows)
    host_rows: dict[str, list[int]] = {}
    missing_indices: list[int] = []
    for row_index, record in enumerate(normalized_rows):
        hostname = record.get(HOST_FIELD)
        if type(hostname) is not str or not hostname.strip():
            missing_indices.append(row_index)
            continue
        host_rows.setdefault(hostname, []).append(row_index)

    if missing_indices:
        raise GroupSplitError(
            "missing_group_key",
            "every row must have a non-empty built-in hostname string",
            row_indices=tuple(missing_indices),
        )
    if len(host_rows) < len(PARTITIONS):
        raise GroupSplitError(
            "insufficient_groups",
            "at least three distinct exact hostnames are required",
        )

    # SHA-256 ordering avoids process-global RNG state and Python-version-specific
    # shuffle behavior. A stable host-string tie-break handles digest collisions.
    ordered_hosts = sorted(
        host_rows,
        key=lambda host: (_seeded_order_key(configuration.seed, host), host),
    )
    ordered_hosts.sort(key=lambda host: -len(host_rows[host]))

    target_rows = tuple(
        len(normalized_rows) * share for share in configuration.proportions
    )
    current_rows = [0, 0, 0]
    host_partition: dict[str, str] = {}
    for host_index, hostname in enumerate(ordered_hosts):
        if host_index < len(PARTITIONS):
            partition_index = host_index
        else:
            partition_index = min(
                range(len(PARTITIONS)),
                key=lambda index: (
                    _normalized_squared_error_delta(
                        current_rows[index],
                        len(host_rows[hostname]),
                        target_rows[index],
                    ),
                    index,
                ),
            )
        partition = PARTITIONS[partition_index]
        host_partition[hostname] = partition
        current_rows[partition_index] += len(host_rows[hostname])

    row_assignments = tuple(
        host_partition[cast(str, record[HOST_FIELD])] for record in normalized_rows
    )
    leakage_audit = audit_partition_assignments(normalized_rows, row_assignments)
    if leakage_audit.host_overlaps:
        raise GroupSplitError(
            "host_constraint_violation",
            "generated assignment violates exact-host disjointness",
        )

    host_assignments = tuple(
        HostPartitionAssignment(host, host_partition[host], len(host_rows[host]))
        for host in sorted(host_rows)
    )
    summaries = tuple(
        PartitionSummary(
            name=partition,
            row_count=current_rows[index],
            host_group_count=sum(
                assigned_partition == partition
                for assigned_partition in host_partition.values()
            ),
        )
        for index, partition in enumerate(PARTITIONS)
    )
    return GroupSplitResult(
        configuration=configuration,
        grouping_field=HOST_FIELD,
        ordering_strategy=ORDERING_STRATEGY,
        host_assignments=host_assignments,
        row_assignments=row_assignments,
        partitions=summaries,
        leakage_audit=leakage_audit,
    )


def _validate_rows(rows: Sequence[Row]) -> tuple[Row, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise GroupSplitError("invalid_rows", "rows must be a sequence of mappings")
    normalized = tuple(rows)
    if any(not isinstance(row, Mapping) for row in normalized):
        raise GroupSplitError("invalid_rows", "each row must be a mapping")
    if any(any(type(key) is not str for key in row) for row in normalized):
        raise GroupSplitError("invalid_rows", "row keys must be strings")
    return normalized


def _seeded_order_key(seed: int, hostname: str) -> bytes:
    seed_bytes = str(seed).encode("ascii")
    host_bytes = hostname.encode("utf-8", errors="surrogatepass")
    return hashlib.sha256(seed_bytes + b"\0" + host_bytes).digest()


def _normalized_squared_error_delta(
    current: int, addition: int, target: float
) -> float:
    before = (current - target) / target
    after = (current + addition - target) / target
    return after * after - before * before
