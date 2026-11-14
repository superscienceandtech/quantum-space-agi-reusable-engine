"""Synthetic fixtures for split integrity and identity overlap diagnostics."""

from __future__ import annotations

import json
from copy import deepcopy

import pytest

from quantum_space_agi.ml.leakage_diagnostics import (
    ExperimentManifestLinkage,
    LeakageDiagnosticsError,
    diagnose_split_integrity,
    serialize_leakage_diagnostics,
)
from quantum_space_agi.ml.synthetic_baseline import run_synthetic_baseline


def diagnostic_row(
    row_id: str,
    *,
    host: object | None = None,
    planet: object | None = None,
    reference: object | None = None,
    component: object | None = None,
    feature: object = 1.0,
    target: object = 2.0,
) -> dict[str, object]:
    index = int(row_id[-1])
    return {
        "synthetic_row_id": row_id,
        "pl_name": planet if planet is not None else f"SYNTHETIC planet {row_id}",
        "hostname": host if host is not None else f"SYNTHETIC host {row_id}",
        "pl_refname": reference if reference is not None else f"SYNTHETIC ref {row_id}",
        "component_id": component
        if component is not None
        else f"SYNTHETIC component {row_id}",
        "pl_rade": feature,
        "pl_bmasse": target + index / 10 if type(target) in (int, float) else target,
        "synthetic": True,
    }


def diagnose(
    rows: list[dict[str, object]],
    train: tuple[str, ...] = ("row-0", "row-1"),
    test: tuple[str, ...] = ("row-2", "row-3"),
    predictions: tuple[str, ...] | None = None,
    experiment_id: str = "arc08-synthetic-leakage-test-v1",
    **kwargs: object,
):
    return diagnose_split_integrity(
        rows,
        row_id_field="synthetic_row_id",
        train_row_ids=train,
        test_row_ids=test,
        prediction_row_ids=test if predictions is None else predictions,
        experiment_id=experiment_id,
        fixture_id="synthetic-identity-fixture/1",
        split_method="explicit synthetic row assignment",
        seed=41,
        **kwargs,
    )


def disjoint_rows() -> list[dict[str, object]]:
    return [diagnostic_row(f"row-{index}") for index in range(4)]


def test_controlled_no_overlap_fixture_passes_structural_checks() -> None:
    rows = disjoint_rows()
    rows[2]["hostname"] = "SYNTHETIC host row-0 "
    report = diagnose(rows)

    assert report.split_integrity.status == "PASS"
    assert report.prediction_alignment.status == "PASS"
    assert report.split_integrity.row_id_overlap == ()
    assert report.identity_overlaps == ()
    assert report.identity_overlap_status == "NO_EXACT_OVERLAP_OBSERVED"
    hostname_coverage = next(
        item for item in report.identity_coverage if item.field == "hostname"
    )
    assert hostname_coverage.distinct_value_count == 4
    assert report.graph_component_overlaps == ()
    assert report.graph_component_audit_status == "NO_EXACT_OVERLAP_OBSERVED"
    assert report.determinism_status == "NOT_CHECKED"
    assert report.scientific_policy_status == "PENDING_REVIEW"
    assert any("not proof of independence" in item for item in report.limitations)


@pytest.mark.parametrize(
    ("field", "identity_value"),
    (
        ("hostname", "SHARED HOST"),
        ("pl_refname", "SHARED REFERENCE"),
        ("pl_name", "SHARED PLANET"),
        ("component_id", "SHARED COMPONENT"),
    ),
)
def test_reports_each_identity_overlap_without_normalizing_values(
    field: str, identity_value: str
) -> None:
    rows = disjoint_rows()
    rows[0][field] = identity_value
    rows[2][field] = identity_value

    report = diagnose(rows)

    matches = [item for item in report.identity_overlaps if item.field == field]
    assert len(matches) == 1
    assert matches[0].value == identity_value
    assert matches[0].train_row_ids == ("row-0",)
    assert matches[0].test_row_ids == ("row-2",)
    assert report.identity_overlap_status == "OVERLAP_REPORTED"
    assert report.split_integrity.status == "PASS"
    assert report.scientific_policy_status == "PENDING_REVIEW"


def test_existing_graph_component_diagnostic_reports_shared_hosts() -> None:
    rows = disjoint_rows()
    rows[0]["hostname"] = rows[2]["hostname"] = "shared graph host"

    report = diagnose(rows)

    assert report.graph_component_audit_status == "OVERLAP_REPORTED"
    assert report.graph_component_overlaps[0].row_ids == ("row-0", "row-2")
    assert report.graph_component_overlaps[0].partition_labels == ("test", "train")


def test_missing_and_invalid_identity_values_are_reported_separately() -> None:
    rows = disjoint_rows()
    del rows[0]["hostname"]
    rows[1]["pl_name"] = None
    rows[2]["pl_refname"] = 19
    rows[3]["component_id"] = "   "

    report = diagnose(rows)
    coverage = {item.field: item for item in report.identity_coverage}

    assert coverage["hostname"].missing_row_indices == (0,)
    assert coverage["pl_name"].missing_row_indices == (1,)
    assert coverage["pl_refname"].invalid_type_row_indices == (2,)
    assert coverage["component_id"].missing_row_indices == (3,)


def test_split_checks_report_crossing_ids_missing_ids_and_duplicates() -> None:
    rows = disjoint_rows()
    del rows[0]["synthetic_row_id"]
    rows[1]["synthetic_row_id"] = "row-1"
    rows[2]["synthetic_row_id"] = "row-1"

    report = diagnose(
        rows,
        train=("row-1", "row-1", "unrecognized"),
        test=("row-1", "row-3"),
        predictions=("row-3",),
    )

    assert report.split_integrity.status == "FAIL"
    assert report.split_integrity.missing_source_row_indices == (0,)
    assert report.split_integrity.duplicate_source_row_ids == ("row-1",)
    assert report.split_integrity.duplicate_train_row_ids == ("row-1",)
    assert report.split_integrity.row_id_overlap == ("row-1",)
    assert report.split_integrity.unknown_split_row_ids == ("unrecognized",)
    assert report.prediction_alignment.status == "FAIL"


def test_split_checks_report_an_unassigned_source_row() -> None:
    report = diagnose(
        disjoint_rows(),
        train=("row-0",),
        test=("row-2", "row-3"),
        predictions=("row-2", "row-3"),
    )

    assert report.split_integrity.status == "FAIL"
    assert report.split_integrity.unassigned_source_row_indices == (1,)


def test_manifest_linkage_must_name_the_diagnostic_experiment() -> None:
    baseline = run_synthetic_baseline()
    linkage = ExperimentManifestLinkage(
        "different-synthetic-experiment",
        baseline.configuration_sha256,
        baseline.manifest_sha256,
        "arc08-experiment-manifest/1",
    )

    with pytest.raises(LeakageDiagnosticsError, match="experiment id"):
        diagnose(disjoint_rows(), manifest_linkage=linkage)


@pytest.mark.parametrize(
    ("prediction_ids", "missing", "unexpected", "duplicates"),
    (
        (("row-2",), ("row-3",), (), ()),
        (("row-2", "row-3", "row-0"), (), ("row-0",), ()),
        (("row-2", "row-2", "row-3"), (), (), ("row-2",)),
    ),
)
def test_prediction_alignment_detects_missing_extra_and_duplicate_predictions(
    prediction_ids: tuple[str, ...],
    missing: tuple[str, ...],
    unexpected: tuple[str, ...],
    duplicates: tuple[str, ...],
) -> None:
    report = diagnose(disjoint_rows(), predictions=prediction_ids)

    assert report.prediction_alignment.status == "FAIL"
    assert report.prediction_alignment.missing_prediction_row_ids == missing
    assert report.prediction_alignment.unexpected_prediction_row_ids == unexpected
    assert report.prediction_alignment.duplicate_prediction_row_ids == duplicates


def test_repeat_assignment_comparison_reports_determinism_only_when_checked() -> None:
    passing = diagnose(
        disjoint_rows(),
        repeat_train_row_ids=("row-0", "row-1"),
        repeat_test_row_ids=("row-2", "row-3"),
        repeat_seed=41,
    )
    failing = diagnose(
        disjoint_rows(),
        repeat_train_row_ids=("row-1", "row-0"),
        repeat_test_row_ids=("row-2", "row-3"),
        repeat_seed=41,
    )

    assert passing.determinism_status == "PASS"
    assert failing.determinism_status == "FAIL"


def test_duplicate_records_and_cross_partition_payloads_are_reported_not_removed() -> (
    None
):
    first = diagnostic_row("row-0", feature=1.5, target=3.0)
    second = diagnostic_row("row-2", feature=1.5, target=3.0)
    for field in ("pl_name", "hostname", "pl_refname", "component_id"):
        second[field] = first[field]
    second["pl_bmasse"] = first["pl_bmasse"]
    rows = [first, diagnostic_row("row-1"), second, diagnostic_row("row-3")]

    report = diagnose(rows)

    assert len(report.cross_partition_payload_duplicates) == 1
    assert report.cross_partition_payload_duplicates[0].row_ids == ("row-0", "row-2")
    assert report.cross_partition_payload_duplicates[0].comparison.endswith(
        "except row identifier"
    )
    assert report.feature_target_pair_overlaps[0].feature_value == 1.5
    assert report.feature_target_pair_overlaps[0].target_value == first["pl_bmasse"]
    assert report.feature_target_pair_overlaps[0].train_row_ids == ("row-0",)
    assert report.feature_target_pair_overlaps[0].test_row_ids == ("row-2",)
    assert len(rows) == 4


def test_exact_record_duplicates_and_uncomparable_values_are_reported() -> None:
    original = diagnostic_row("row-0")
    rows = [original, original.copy(), diagnostic_row("row-2"), diagnostic_row("row-3")]
    rows[3]["nested"] = {"unsupported": object()}

    report = diagnose(rows)

    assert report.split_integrity.status == "FAIL"
    assert report.duplicate_record_groups[0].row_indices == (0, 1)
    assert report.uncomparable_record_indices == (3,)


def test_report_serialization_is_deterministic_and_manifest_linked() -> None:
    baseline = run_synthetic_baseline(seed=41)
    linkage = ExperimentManifestLinkage(
        experiment_id="arc08-synthetic-mass-radius-smoke-test-v1",
        configuration_sha256=baseline.configuration_sha256,
        manifest_sha256=baseline.manifest_sha256,
        manifest_schema_version="arc08-experiment-manifest/1",
    )
    rows = disjoint_rows()
    first = diagnose(
        rows, experiment_id=linkage.experiment_id, manifest_linkage=linkage
    )
    second = diagnose(
        rows, experiment_id=linkage.experiment_id, manifest_linkage=linkage
    )
    serialized = serialize_leakage_diagnostics(first)
    document = json.loads(serialized)

    assert serialized == serialize_leakage_diagnostics(second)
    assert not serialized.startswith(b"\xef\xbb\xbf")
    assert document["manifest_linkage"]["manifest_sha256"] == baseline.manifest_sha256
    assert "not authenticated" in document["manifest_linkage"]["integrity_note"]
    assert document["scientific_policy_status"] == "PENDING_REVIEW"
    assert all(row["synthetic"] for row in rows)


def test_diagnostics_do_not_mutate_caller_rows() -> None:
    rows = disjoint_rows()
    original = deepcopy(rows)

    diagnose(rows)

    assert rows == original


def test_invalid_manifest_linkage_is_rejected() -> None:
    with pytest.raises(LeakageDiagnosticsError, match="lowercase SHA-256"):
        ExperimentManifestLinkage("synthetic", "not-a-hash", "a" * 64, "manifest/1")
