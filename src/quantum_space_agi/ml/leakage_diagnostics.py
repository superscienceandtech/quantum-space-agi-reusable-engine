"""Offline split-integrity and exact-identity overlap diagnostics.

The API inspects caller-supplied rows and assignments. It does not create a
split, resolve identities, determine scientific validity, or infer semantic
target leakage.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeAlias

from quantum_space_agi.ml.identity_diagnostics import (
    ComponentPartitionOverlap,
    IdentityGroupingReport,
    audit_partition_assignments,
    diagnose_identity_groups,
)

Row: TypeAlias = Mapping[str, object]
_IDENTITY_FIELDS = ("pl_name", "hostname", "pl_refname", "component_id")
_SHA256_CHARS = frozenset("0123456789abcdef")


class LeakageDiagnosticsError(ValueError):
    """Malformed diagnostic input or unsupported serialization value."""


@dataclass(frozen=True, slots=True)
class ExperimentManifestLinkage:
    """Caller-supplied links to existing configuration and manifest bytes.

    This validates declaration shape only; callers should source values from
    the experiment manifest APIs. The link is not artifact authentication.
    """

    experiment_id: str
    configuration_sha256: str
    manifest_sha256: str
    manifest_schema_version: str

    def __post_init__(self) -> None:
        if type(self.experiment_id) is not str or not self.experiment_id.strip():
            raise LeakageDiagnosticsError("experiment_id must be non-empty text")
        for name in ("configuration_sha256", "manifest_sha256"):
            value = getattr(self, name)
            if (
                type(value) is not str
                or len(value) != 64
                or any(character not in _SHA256_CHARS for character in value)
            ):
                raise LeakageDiagnosticsError(f"{name} must be lowercase SHA-256")
        if (
            type(self.manifest_schema_version) is not str
            or not self.manifest_schema_version.strip()
        ):
            raise LeakageDiagnosticsError("manifest schema version must be non-empty")


@dataclass(frozen=True, slots=True)
class IdentityFieldCoverage:
    """Coverage of one exact identity field across source row positions."""

    field: str
    observed_row_count: int
    missing_row_indices: tuple[int, ...]
    invalid_type_row_indices: tuple[int, ...]
    distinct_value_count: int


@dataclass(frozen=True, slots=True)
class IdentityOverlap:
    """One exact string value observed in both declared partitions."""

    field: str
    value: str
    train_row_ids: tuple[str, ...]
    test_row_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GraphComponentOverlap:
    """Existing host-reference graph component crossing partition labels."""

    component_index: int
    partition_labels: tuple[str, ...]
    row_indices: tuple[int, ...]
    row_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DuplicateRecordGroup:
    """Rows with identical canonical record contents under the declared key."""

    row_indices: tuple[int, ...]
    row_ids: tuple[str, ...]
    partition_labels: tuple[str, ...]
    comparison: str


@dataclass(frozen=True, slots=True)
class FeatureTargetPairOverlap:
    """Exact scalar feature/target pair repeated across train and test."""

    feature_value: object
    target_value: object
    train_row_ids: tuple[str, ...]
    test_row_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SplitIntegrityDiagnostics:
    """Accounting checks for source rows and the requested train/test IDs."""

    status: str
    source_row_count: int
    train_row_count: int
    test_row_count: int
    train_row_ids: tuple[str, ...]
    test_row_ids: tuple[str, ...]
    row_id_overlap: tuple[str, ...]
    missing_source_row_indices: tuple[int, ...]
    invalid_source_row_indices: tuple[int, ...]
    duplicate_source_row_ids: tuple[str, ...]
    duplicate_train_row_ids: tuple[str, ...]
    duplicate_test_row_ids: tuple[str, ...]
    unknown_split_row_ids: tuple[str, ...]
    unassigned_source_row_indices: tuple[int, ...]
    multiply_assigned_source_row_indices: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class PredictionAlignmentDiagnostics:
    """One-to-one relationship between declared test rows and predictions."""

    status: str
    prediction_row_count: int
    prediction_row_ids: tuple[str, ...]
    missing_prediction_row_ids: tuple[str, ...]
    unexpected_prediction_row_ids: tuple[str, ...]
    duplicate_prediction_row_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LeakageDiagnosticReport:
    """Immutable structural and identity report; no scientific approval implied."""

    schema_version: str
    experiment_id: str
    fixture_id: str
    split_method: str
    seed: int | None
    determinism_status: str
    split_integrity: SplitIntegrityDiagnostics
    prediction_alignment: PredictionAlignmentDiagnostics
    identity_coverage: tuple[IdentityFieldCoverage, ...]
    identity_overlap_status: str
    identity_overlaps: tuple[IdentityOverlap, ...]
    graph_component_audit_status: str
    graph_component_overlaps: tuple[GraphComponentOverlap, ...]
    duplicate_record_groups: tuple[DuplicateRecordGroup, ...]
    cross_partition_payload_duplicates: tuple[DuplicateRecordGroup, ...]
    feature_target_pair_overlaps: tuple[FeatureTargetPairOverlap, ...]
    uncomparable_record_indices: tuple[int, ...]
    warnings: tuple[str, ...]
    limitations: tuple[str, ...]
    scientific_policy_status: str
    manifest_linkage: ExperimentManifestLinkage | None


def diagnose_split_integrity(
    rows: Sequence[Row],
    *,
    row_id_field: str,
    train_row_ids: Sequence[str],
    test_row_ids: Sequence[str],
    prediction_row_ids: Sequence[str],
    experiment_id: str,
    fixture_id: str,
    split_method: str,
    seed: int | None = None,
    feature_field: str = "pl_rade",
    target_field: str = "pl_bmasse",
    identity_fields: tuple[str, ...] = _IDENTITY_FIELDS,
    repeat_train_row_ids: Sequence[str] | None = None,
    repeat_test_row_ids: Sequence[str] | None = None,
    repeat_seed: int | None = None,
    manifest_linkage: ExperimentManifestLinkage | None = None,
) -> LeakageDiagnosticReport:
    """Check split accounting, prediction membership, overlap and duplicates.

    Inputs are compared exactly as supplied. Identity text is not trimmed,
    case-folded, alias-resolved, or deduplicated. Overlap is an observation, not
    a declaration that a split is scientifically invalid or independent.
    """
    normalized_rows = _rows(rows)
    for name, value in (
        ("row_id_field", row_id_field),
        ("experiment_id", experiment_id),
        ("fixture_id", fixture_id),
        ("split_method", split_method),
        ("feature_field", feature_field),
        ("target_field", target_field),
    ):
        _required_text(name, value)
    if type(identity_fields) is not tuple or any(
        type(field) is not str or not field for field in identity_fields
    ):
        raise LeakageDiagnosticsError("identity_fields must be a tuple of strings")
    if len(set(identity_fields)) != len(identity_fields):
        raise LeakageDiagnosticsError("identity_fields must be unique")
    if seed is not None and (type(seed) is not int or seed < 0):
        raise LeakageDiagnosticsError("seed must be a non-negative integer or None")
    if manifest_linkage is not None:
        if type(manifest_linkage) is not ExperimentManifestLinkage:
            raise LeakageDiagnosticsError("manifest_linkage has an invalid type")
        if manifest_linkage.experiment_id != experiment_id:
            raise LeakageDiagnosticsError(
                "manifest linkage experiment id does not match diagnostic report"
            )

    train_ids = _string_sequence("train_row_ids", train_row_ids)
    test_ids = _string_sequence("test_row_ids", test_row_ids)
    prediction_ids = _string_sequence("prediction_row_ids", prediction_row_ids)
    split = _split_checks(normalized_rows, row_id_field, train_ids, test_ids)
    predictions = _prediction_checks(test_ids, prediction_ids)
    coverage = _identity_coverage(normalized_rows, identity_fields)
    overlaps = _identity_overlaps(
        normalized_rows, row_id_field, identity_fields, train_ids, test_ids
    )

    graph_status = "NOT_ASSESSED_INVALID_SPLIT_MEMBERSHIP"
    graph_overlaps: tuple[GraphComponentOverlap, ...] = ()
    if split.status == "PASS":
        labels = tuple(
            "train" if _row_value(row, row_id_field) in set(train_ids) else "test"
            for row in normalized_rows
        )
        identity_report = diagnose_identity_groups(normalized_rows)
        audit = audit_partition_assignments(normalized_rows, labels)
        graph_status = (
            "OVERLAP_REPORTED"
            if audit.component_overlaps
            else "NO_EXACT_OVERLAP_OBSERVED"
        )
        graph_overlaps = _graph_overlaps(
            audit.component_overlaps, identity_report, normalized_rows, row_id_field
        )

    duplicates, payload_duplicates, uncomparable = _duplicate_groups(
        normalized_rows,
        row_id_field,
        train_ids,
        test_ids,
    )
    feature_target_overlaps = _feature_target_overlaps(
        normalized_rows,
        row_id_field,
        feature_field,
        target_field,
        train_ids,
        test_ids,
    )
    determinism_status = _determinism_status(
        train_ids,
        test_ids,
        seed,
        repeat_train_row_ids,
        repeat_test_row_ids,
        repeat_seed,
    )
    warnings: list[str] = []
    if overlaps or graph_overlaps:
        warnings.append("Exact identity or graph-component overlap was observed.")
    if any(
        item.missing_row_indices or item.invalid_type_row_indices for item in coverage
    ):
        warnings.append("Some identity values are missing or have invalid types.")
    if duplicates or payload_duplicates:
        warnings.append(
            "Duplicate record content warrants inspection; no rows were removed."
        )
    if feature_target_overlaps:
        warnings.append("Identical feature/target pairs cross train and test.")
    if split.status != "PASS":
        warnings.append(
            "Split membership does not account for source rows exactly once."
        )
    if predictions.status != "PASS":
        warnings.append("Prediction IDs do not match the declared test IDs one-to-one.")
    if uncomparable:
        warnings.append("Some records could not be compared as JSON-like values.")
    if determinism_status == "NOT_CHECKED":
        warnings.append(
            "Determinism requires an independently repeated assignment input."
        )

    return LeakageDiagnosticReport(
        schema_version="arc08-leakage-diagnostics/1",
        experiment_id=experiment_id,
        fixture_id=fixture_id,
        split_method=split_method,
        seed=seed,
        determinism_status=determinism_status,
        split_integrity=split,
        prediction_alignment=predictions,
        identity_coverage=coverage,
        identity_overlap_status=(
            "OVERLAP_REPORTED" if overlaps else "NO_EXACT_OVERLAP_OBSERVED"
        ),
        identity_overlaps=overlaps,
        graph_component_audit_status=graph_status,
        graph_component_overlaps=graph_overlaps,
        duplicate_record_groups=duplicates,
        cross_partition_payload_duplicates=payload_duplicates,
        feature_target_pair_overlaps=feature_target_overlaps,
        uncomparable_record_indices=uncomparable,
        warnings=tuple(warnings),
        limitations=(
            "Identity overlap is not proof of scientific dependence; "
            "no observed overlap is not proof of independence.",
            "Exact string checks do not resolve aliases, renamed objects, "
            "or semantic identity.",
            "Structural duplicate checks cannot detect every related measurement "
            "or semantic target leakage.",
            "A row-level assignment is not a host/reference/component-disjoint "
            "policy unless separately demonstrated.",
            "This diagnostic does not decide cohort eligibility or scientific "
            "validity.",
        ),
        scientific_policy_status="PENDING_REVIEW",
        manifest_linkage=manifest_linkage,
    )


def serialize_leakage_diagnostics(report: LeakageDiagnosticReport) -> bytes:
    """Serialize a diagnostic report as deterministic compact UTF-8 JSON."""
    if type(report) is not LeakageDiagnosticReport:
        raise LeakageDiagnosticsError("report must be LeakageDiagnosticReport")
    try:
        return json.dumps(
            _report_document(report),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, OverflowError) as exc:
        raise LeakageDiagnosticsError(
            "diagnostic report is not JSON serializable"
        ) from exc


def _required_text(name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise LeakageDiagnosticsError(f"{name} must be a non-empty string")


def _rows(rows: Sequence[Row]) -> tuple[Row, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise LeakageDiagnosticsError("rows must be a sequence of mappings")
    normalized = tuple(rows)
    if any(not isinstance(row, Mapping) for row in normalized):
        raise LeakageDiagnosticsError("each row must be a mapping")
    if any(any(type(key) is not str for key in row) for row in normalized):
        raise LeakageDiagnosticsError("row keys must be built-in strings")
    return normalized


def _string_sequence(name: str, values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise LeakageDiagnosticsError(f"{name} must be a sequence of strings")
    normalized = tuple(values)
    if any(type(value) is not str or not value for value in normalized):
        raise LeakageDiagnosticsError(f"{name} values must be non-empty strings")
    return normalized


def _row_value(row: Row, field: str) -> str | None:
    value = row.get(field)
    return value if type(value) is str and value.strip() else None


def _split_checks(
    rows: tuple[Row, ...],
    row_id_field: str,
    train_ids: tuple[str, ...],
    test_ids: tuple[str, ...],
) -> SplitIntegrityDiagnostics:
    source_values: list[str] = []
    missing_indices: list[int] = []
    invalid_indices: list[int] = []
    for index, row in enumerate(rows):
        row_id = row.get(row_id_field)
        if row_id_field not in row or row_id is None:
            missing_indices.append(index)
        elif type(row_id) is not str:
            invalid_indices.append(index)
        elif not row_id.strip():
            missing_indices.append(index)
        else:
            source_values.append(row_id)

    source_counts = Counter(source_values)
    train_counts = Counter(train_ids)
    test_counts = Counter(test_ids)
    source_set = set(source_counts)
    train_set = set(train_counts)
    test_set = set(test_counts)
    duplicate_source = tuple(
        sorted(key for key, count in source_counts.items() if count > 1)
    )
    duplicate_train = tuple(
        sorted(key for key, count in train_counts.items() if count > 1)
    )
    duplicate_test = tuple(
        sorted(key for key, count in test_counts.items() if count > 1)
    )
    unknown_ids = tuple(sorted((train_set | test_set) - source_set))
    assignments = train_counts + test_counts
    unassigned_rows: list[int] = []
    multiply_assigned_rows: list[int] = []
    for index, row in enumerate(rows):
        row_id = _row_value(row, row_id_field)
        if row_id is not None:
            assignment_count = assignments[row_id]
            if assignment_count == 0:
                unassigned_rows.append(index)
            elif assignment_count > 1:
                multiply_assigned_rows.append(index)
    unassigned = tuple(unassigned_rows)
    multiply_assigned = tuple(multiply_assigned_rows)
    overlap = tuple(sorted(train_set & test_set))
    passed = (
        not any(
            (
                missing_indices,
                invalid_indices,
                duplicate_source,
                duplicate_train,
                duplicate_test,
                unknown_ids,
                unassigned,
                multiply_assigned,
                overlap,
            )
        )
        and source_set == train_set | test_set
    )
    return SplitIntegrityDiagnostics(
        status="PASS" if passed else "FAIL",
        source_row_count=len(rows),
        train_row_count=len(train_ids),
        test_row_count=len(test_ids),
        train_row_ids=train_ids,
        test_row_ids=test_ids,
        row_id_overlap=overlap,
        missing_source_row_indices=tuple(missing_indices),
        invalid_source_row_indices=tuple(invalid_indices),
        duplicate_source_row_ids=duplicate_source,
        duplicate_train_row_ids=duplicate_train,
        duplicate_test_row_ids=duplicate_test,
        unknown_split_row_ids=unknown_ids,
        unassigned_source_row_indices=unassigned,
        multiply_assigned_source_row_indices=multiply_assigned,
    )


def _prediction_checks(
    test_ids: tuple[str, ...], prediction_ids: tuple[str, ...]
) -> PredictionAlignmentDiagnostics:
    expected = set(test_ids)
    actual = Counter(prediction_ids)
    missing = tuple(sorted(expected - set(actual)))
    unexpected = tuple(sorted(set(actual) - expected))
    duplicated = tuple(sorted(key for key, count in actual.items() if count > 1))
    status = "PASS" if not (missing or unexpected or duplicated) else "FAIL"
    return PredictionAlignmentDiagnostics(
        status=status,
        prediction_row_count=len(prediction_ids),
        prediction_row_ids=prediction_ids,
        missing_prediction_row_ids=missing,
        unexpected_prediction_row_ids=unexpected,
        duplicate_prediction_row_ids=duplicated,
    )


def _identity_coverage(
    rows: tuple[Row, ...], fields: tuple[str, ...]
) -> tuple[IdentityFieldCoverage, ...]:
    results: list[IdentityFieldCoverage] = []
    for field in fields:
        missing: list[int] = []
        invalid: list[int] = []
        values: set[str] = set()
        for index, row in enumerate(rows):
            value = row.get(field)
            if field not in row or value is None:
                missing.append(index)
            elif type(value) is not str:
                invalid.append(index)
            elif not value.strip():
                missing.append(index)
            else:
                values.add(value)
        results.append(
            IdentityFieldCoverage(
                field=field,
                observed_row_count=len(rows) - len(missing) - len(invalid),
                missing_row_indices=tuple(missing),
                invalid_type_row_indices=tuple(invalid),
                distinct_value_count=len(values),
            )
        )
    return tuple(results)


def _identity_overlaps(
    rows: tuple[Row, ...],
    row_id_field: str,
    fields: tuple[str, ...],
    train_ids: tuple[str, ...],
    test_ids: tuple[str, ...],
) -> tuple[IdentityOverlap, ...]:
    train_set = set(train_ids)
    test_set = set(test_ids)
    results: list[IdentityOverlap] = []
    for field in fields:
        memberships: dict[str, dict[str, list[str]]] = defaultdict(
            lambda: {"train": [], "test": []}
        )
        for row in rows:
            row_id = _row_value(row, row_id_field)
            identity = _row_value(row, field)
            if row_id is None or identity is None:
                continue
            if row_id in train_set:
                memberships[identity]["train"].append(row_id)
            if row_id in test_set:
                memberships[identity]["test"].append(row_id)
        for value, assigned in sorted(memberships.items()):
            if assigned["train"] and assigned["test"]:
                results.append(
                    IdentityOverlap(
                        field,
                        value,
                        tuple(assigned["train"]),
                        tuple(assigned["test"]),
                    )
                )
    return tuple(results)


def _graph_overlaps(
    overlaps: tuple[ComponentPartitionOverlap, ...],
    report: IdentityGroupingReport,
    rows: tuple[Row, ...],
    row_id_field: str,
) -> tuple[GraphComponentOverlap, ...]:
    components = {item.component_index: item for item in report.components}
    return tuple(
        GraphComponentOverlap(
            item.component_index,
            item.partition_labels,
            item.row_indices,
            tuple(
                value
                for index in item.row_indices
                if (value := _row_value(rows[index], row_id_field)) is not None
            ),
        )
        for item in overlaps
        if item.component_index in components
    )


def _freeze_json_value(value: object) -> object:
    """Produce a type-tagged exact comparison key for JSON-like row values."""
    if value is None:
        return ("null",)
    if type(value) is bool:
        return ("bool", value)
    if type(value) is int:
        return ("int", value)
    if type(value) is float:
        if math.isnan(value):
            return ("float", "nan")
        if math.isinf(value):
            return ("float", "inf" if value > 0 else "-inf")
        return ("float", value.hex())
    if type(value) is str:
        return ("str", value)
    if type(value) is list:
        return ("list", tuple(_freeze_json_value(item) for item in value))
    if isinstance(value, Mapping) and all(type(key) is str for key in value):
        return (
            "dict",
            tuple((key, _freeze_json_value(value[key])) for key in sorted(value)),
        )
    raise TypeError(type(value).__name__)


def _duplicate_groups(
    rows: tuple[Row, ...],
    row_id_field: str,
    train_ids: tuple[str, ...],
    test_ids: tuple[str, ...],
) -> tuple[
    tuple[DuplicateRecordGroup, ...], tuple[DuplicateRecordGroup, ...], tuple[int, ...]
]:
    full_records: dict[object, list[int]] = defaultdict(list)
    payload_records: dict[object, list[int]] = defaultdict(list)
    uncomparable: list[int] = []
    for index, row in enumerate(rows):
        try:
            full_records[_freeze_json_value(dict(row))].append(index)
            payload_records[
                _freeze_json_value(
                    {key: value for key, value in row.items() if key != row_id_field}
                )
            ].append(index)
        except TypeError:
            uncomparable.append(index)
    train_set = set(train_ids)
    test_set = set(test_ids)

    def make_groups(
        grouped: dict[object, list[int]], comparison: str
    ) -> tuple[DuplicateRecordGroup, ...]:
        result = []
        for indices in grouped.values():
            if len(indices) < 2:
                continue
            row_ids = tuple(
                value
                for index in indices
                if (value := _row_value(rows[index], row_id_field)) is not None
            )
            labels = tuple(
                label
                for label, partition in (("train", train_set), ("test", test_set))
                if any(row_id in partition for row_id in row_ids)
            )
            result.append(
                DuplicateRecordGroup(tuple(indices), row_ids, labels, comparison)
            )
        return tuple(sorted(result, key=lambda item: item.row_indices))

    exact = make_groups(full_records, "all fields, including row identifier")
    payload = tuple(
        item
        for item in make_groups(payload_records, "all fields except row identifier")
        if "train" in item.partition_labels and "test" in item.partition_labels
    )
    return exact, payload, tuple(uncomparable)


def _feature_target_overlaps(
    rows: tuple[Row, ...],
    row_id_field: str,
    feature_field: str,
    target_field: str,
    train_ids: tuple[str, ...],
    test_ids: tuple[str, ...],
) -> tuple[FeatureTargetPairOverlap, ...]:
    values: dict[object, dict[str, list[str]]] = defaultdict(
        lambda: {"train": [], "test": []}
    )
    pair_values: dict[object, tuple[object, object]] = {}
    train_set = set(train_ids)
    test_set = set(test_ids)
    for row in rows:
        row_id = _row_value(row, row_id_field)
        feature = row.get(feature_field)
        target = row.get(target_field)
        if (
            row_id is None
            or type(feature) not in (str, int, float, bool)
            or type(target) not in (str, int, float, bool)
            or (type(feature) is float and not math.isfinite(feature))
            or (type(target) is float and not math.isfinite(target))
        ):
            continue
        key = (_freeze_json_value(feature), _freeze_json_value(target))
        pair_values[key] = (feature, target)
        if row_id in train_set:
            values[key]["train"].append(row_id)
        if row_id in test_set:
            values[key]["test"].append(row_id)
    return tuple(
        FeatureTargetPairOverlap(
            pair_values[key][0],
            pair_values[key][1],
            tuple(assigned["train"]),
            tuple(assigned["test"]),
        )
        for key, assigned in sorted(values.items(), key=lambda item: repr(item[0]))
        if assigned["train"] and assigned["test"]
    )


def _determinism_status(
    train_ids: tuple[str, ...],
    test_ids: tuple[str, ...],
    seed: int | None,
    repeat_train: Sequence[str] | None,
    repeat_test: Sequence[str] | None,
    repeat_seed: int | None,
) -> str:
    if repeat_train is None and repeat_test is None and repeat_seed is None:
        return "NOT_CHECKED"
    if repeat_train is None or repeat_test is None:
        raise LeakageDiagnosticsError("both repeated train and test IDs are required")
    repeated_train = _string_sequence("repeat_train_row_ids", repeat_train)
    repeated_test = _string_sequence("repeat_test_row_ids", repeat_test)
    return (
        "PASS"
        if seed == repeat_seed
        and train_ids == repeated_train
        and test_ids == repeated_test
        else "FAIL"
    )


def _report_document(report: LeakageDiagnosticReport) -> dict[str, object]:
    manifest_linkage: dict[str, object] | None = None
    if report.manifest_linkage is not None:
        link = report.manifest_linkage
        manifest_linkage = {
            "experiment_id": link.experiment_id,
            "configuration_sha256": link.configuration_sha256,
            "manifest_sha256": link.manifest_sha256,
            "manifest_schema_version": link.manifest_schema_version,
            "integrity_note": (
                "caller-declared linkage; artifact bytes are not authenticated here"
            ),
        }
    return {
        "schema_version": report.schema_version,
        "experiment_id": report.experiment_id,
        "fixture_id": report.fixture_id,
        "split_method": report.split_method,
        "seed": report.seed,
        "determinism_status": report.determinism_status,
        "scientific_policy_status": report.scientific_policy_status,
        "split_integrity": {
            "status": report.split_integrity.status,
            "source_row_count": report.split_integrity.source_row_count,
            "train_row_count": report.split_integrity.train_row_count,
            "test_row_count": report.split_integrity.test_row_count,
            "train_row_ids": list(report.split_integrity.train_row_ids),
            "test_row_ids": list(report.split_integrity.test_row_ids),
            "row_id_overlap": list(report.split_integrity.row_id_overlap),
            "missing_source_row_indices": list(
                report.split_integrity.missing_source_row_indices
            ),
            "invalid_source_row_indices": list(
                report.split_integrity.invalid_source_row_indices
            ),
            "duplicate_source_row_ids": list(
                report.split_integrity.duplicate_source_row_ids
            ),
            "duplicate_train_row_ids": list(
                report.split_integrity.duplicate_train_row_ids
            ),
            "duplicate_test_row_ids": list(
                report.split_integrity.duplicate_test_row_ids
            ),
            "unknown_split_row_ids": list(report.split_integrity.unknown_split_row_ids),
            "unassigned_source_row_indices": list(
                report.split_integrity.unassigned_source_row_indices
            ),
            "multiply_assigned_source_row_indices": list(
                report.split_integrity.multiply_assigned_source_row_indices
            ),
        },
        "prediction_alignment": {
            "status": report.prediction_alignment.status,
            "prediction_row_count": report.prediction_alignment.prediction_row_count,
            "prediction_row_ids": list(report.prediction_alignment.prediction_row_ids),
            "missing_prediction_row_ids": list(
                report.prediction_alignment.missing_prediction_row_ids
            ),
            "unexpected_prediction_row_ids": list(
                report.prediction_alignment.unexpected_prediction_row_ids
            ),
            "duplicate_prediction_row_ids": list(
                report.prediction_alignment.duplicate_prediction_row_ids
            ),
        },
        "identity_coverage": [
            {
                "field": item.field,
                "observed_row_count": item.observed_row_count,
                "missing_row_indices": list(item.missing_row_indices),
                "invalid_type_row_indices": list(item.invalid_type_row_indices),
                "distinct_value_count": item.distinct_value_count,
            }
            for item in report.identity_coverage
        ],
        "identity_overlap_status": report.identity_overlap_status,
        "identity_overlaps": [
            {
                "field": item.field,
                "value": item.value,
                "train_row_count": len(item.train_row_ids),
                "test_row_count": len(item.test_row_ids),
                "train_row_ids": list(item.train_row_ids),
                "test_row_ids": list(item.test_row_ids),
            }
            for item in report.identity_overlaps
        ],
        "graph_component_audit_status": report.graph_component_audit_status,
        "graph_component_overlaps": [
            {
                "component_index": item.component_index,
                "partition_labels": list(item.partition_labels),
                "row_indices": list(item.row_indices),
                "row_ids": list(item.row_ids),
            }
            for item in report.graph_component_overlaps
        ],
        "duplicate_record_groups": [
            _duplicate_document(item) for item in report.duplicate_record_groups
        ],
        "cross_partition_payload_duplicates": [
            _duplicate_document(item)
            for item in report.cross_partition_payload_duplicates
        ],
        "feature_target_pair_overlaps": [
            {
                "feature_value": item.feature_value,
                "target_value": item.target_value,
                "train_row_ids": list(item.train_row_ids),
                "test_row_ids": list(item.test_row_ids),
            }
            for item in report.feature_target_pair_overlaps
        ],
        "uncomparable_record_indices": list(report.uncomparable_record_indices),
        "warnings": list(report.warnings),
        "limitations": list(report.limitations),
        "manifest_linkage": manifest_linkage,
    }


def _duplicate_document(group: DuplicateRecordGroup) -> dict[str, object]:
    return {
        "row_indices": list(group.row_indices),
        "row_ids": list(group.row_ids),
        "partition_labels": list(group.partition_labels),
        "comparison": group.comparison,
    }
