"""Synthetic tests for deterministic offline evidence-report serialization."""

from __future__ import annotations

import json
from dataclasses import replace
from html import escape
from pathlib import Path

import pytest

from quantum_space_agi.ml.dataset_ingestion import (
    REQUIRED_COLUMNS,
)
from quantum_space_agi.ml.evidence_report import (
    EVIDENCE_REPORT_SCHEMA_VERSION,
    OfflineEvidenceReportError,
    serialize_offline_evidence_report,
)
from quantum_space_agi.ml.identity_diagnostics import diagnose_ingested_identities
from quantum_space_agi.ml.snapshot_artifact import write_snapshot_artifact
from quantum_space_agi.ml.verified_ingestion import (
    VerifiedSnapshotIngestionResult,
    ingest_verified_snapshot,
)

_FIELD_TYPES = {
    "pl_rade": 'datatype="double" unit="Rearth"',
    "pl_bmasse": 'datatype="double" unit="Mearth"',
    "pl_name": 'datatype="char" arraysize="*"',
    "hostname": 'datatype="char" arraysize="*"',
    "pl_refname": 'datatype="char" arraysize="*"',
}


def _row(
    planet: str,
    host: str,
    reference: str,
    *,
    radius: object = 1.5,
    mass: object = 2.5,
) -> dict[str, object]:
    return {
        "pl_rade": radius,
        "pl_bmasse": mass,
        "pl_name": planet,
        "hostname": host,
        "pl_refname": reference,
    }


def _votable(rows: list[dict[str, object]]) -> bytes:
    fields = "".join(
        f'<FIELD name="{name}" {_FIELD_TYPES[name]}/>' for name in REQUIRED_COLUMNS
    )
    table_rows = "".join(
        "<TR>"
        + "".join(
            "<TD/>"
            if row[name] is None
            else f"<TD>{escape(str(row[name]), quote=False)}</TD>"
            for name in REQUIRED_COLUMNS
        )
        + "</TR>"
        for row in rows
    )
    document = (
        '<VOTABLE xmlns="http://www.ivoa.net/xml/VOTable/v1.3">'
        '<RESOURCE type="results"><INFO name="QUERY_STATUS" value="OK"/>'
        f"<TABLE>{fields}<DATA><TABLEDATA>{table_rows}</TABLEDATA></DATA></TABLE>"
        "</RESOURCE></VOTABLE>"
    )
    return document.encode("utf-8")


def _pipeline(tmp_path: Path) -> VerifiedSnapshotIngestionResult:
    payload = _votable(
        [
            _row("planet-a", "host-a", "ref-a"),
            _row("excluded", "host-x", "ref-x", radius=0, mass=None),
            _row("planet-b", "host-b", "ref-b"),
            _row("planet-b", "host-c", "ref-c"),
        ]
    )
    artifact_path = tmp_path / "synthetic.vot"
    write_snapshot_artifact(payload, artifact_path)
    return ingest_verified_snapshot(artifact_path)


def _identity(pipeline: VerifiedSnapshotIngestionResult):
    return diagnose_ingested_identities(pipeline.ingestion, requested_partitions=3)


def test_serializes_verified_snapshot_and_diagnostics_deterministically(
    tmp_path: Path,
) -> None:
    pipeline = _pipeline(tmp_path)
    diagnostics = _identity(pipeline)

    first = serialize_offline_evidence_report(
        pipeline, identity_diagnostics=diagnostics
    )
    second = serialize_offline_evidence_report(
        pipeline, identity_diagnostics=diagnostics
    )
    report = json.loads(first)

    assert first == second
    assert first.startswith(b"{") and not first.startswith(b"\xef\xbb\xbf")
    assert report["schema_version"] == EVIDENCE_REPORT_SCHEMA_VERSION
    assert report["snapshot"]["sha256"] == pipeline.verification.actual_sha256
    assert report["snapshot"]["byte_length"] == pipeline.verification.actual_byte_length
    assert report["snapshot"]["caller_supplied_provenance"]["source_identifier"] is None
    assert report["ingestion"]["validation_scope"] == "MECHANICAL_VALIDATION_ONLY"
    assert report["approval_status"]["scientific"] == "NOT_ESTABLISHED_BY_THIS_REPORT"


def test_report_preserves_ledger_and_original_identity_row_mapping(
    tmp_path: Path,
) -> None:
    pipeline = _pipeline(tmp_path)
    diagnostics = _identity(pipeline)
    report = json.loads(
        serialize_offline_evidence_report(pipeline, identity_diagnostics=diagnostics)
    )

    assert report["accepted_source_row_indices"] == [0, 2, 3]
    assert report["exclusion_ledger"] == [
        {
            "source_row_index": 1,
            "findings": [
                {
                    "field": "pl_bmasse",
                    "reason_code": "null_value",
                    "original_value": None,
                    "value_omitted": False,
                },
                {
                    "field": "pl_rade",
                    "reason_code": "non_positive",
                    "original_value": 0.0,
                    "value_omitted": False,
                },
            ],
        }
    ]
    assert report["identity_diagnostics"]["source_row_indices"] == [0, 2, 3]
    assert report["identity_diagnostics"]["repeated_identity_tuples"] == []
    repeated_names = report["identity_diagnostics"]["repeated_identity_values"]
    assert repeated_names == [
        {"field": "pl_name", "value": "planet-b", "source_row_indices": [2, 3]}
    ]


def test_missing_optional_sections_are_explicit_and_not_assignments(
    tmp_path: Path,
) -> None:
    report = json.loads(serialize_offline_evidence_report(_pipeline(tmp_path)))

    assert report["identity_diagnostics"] is None
    assert report["split_feasibility"] is None
    assert report["split_assignments"] == {
        "assignment_status": "NOT_CREATED_OR_SUPPLIED",
        "assignments": None,
    }


@pytest.mark.parametrize("mismatch", ["checksum", "byte_length"])
def test_snapshot_integrity_mismatches_are_rejected(
    tmp_path: Path, mismatch: str
) -> None:
    pipeline = _pipeline(tmp_path)
    if mismatch == "checksum":
        verification = replace(pipeline.verification, actual_sha256="0" * 64)
        manifest = replace(pipeline.ingestion.manifest, raw_response_sha256="0" * 64)
    else:
        wrong_length = pipeline.verification.actual_byte_length + 1
        verification = replace(pipeline.verification, actual_byte_length=wrong_length)
        manifest = replace(
            pipeline.ingestion.manifest, raw_response_byte_count=wrong_length
        )
    ingestion = replace(pipeline.ingestion, manifest=manifest)
    inconsistent_pipeline = VerifiedSnapshotIngestionResult(verification, ingestion)

    with pytest.raises(OfflineEvidenceReportError, match="checksum or byte length"):
        serialize_offline_evidence_report(inconsistent_pipeline)


def test_identity_source_mapping_must_match_ingestion_rows(
    tmp_path: Path,
) -> None:
    pipeline = _pipeline(tmp_path)
    diagnostics = _identity(pipeline)
    mismatched = replace(diagnostics, source_row_indices=(3, 2, 0))

    with pytest.raises(OfflineEvidenceReportError, match="does not match"):
        serialize_offline_evidence_report(pipeline, identity_diagnostics=mismatched)


def test_duplicate_identity_source_mapping_is_rejected_at_construction(
    tmp_path: Path,
) -> None:
    diagnostics = _identity(_pipeline(tmp_path))

    with pytest.raises(ValueError, match="must be unique"):
        replace(diagnostics, source_row_indices=(0, 2, 2))


def test_feasibility_is_distinct_from_assignments_and_inputs_are_unchanged(
    tmp_path: Path,
) -> None:
    pipeline = _pipeline(tmp_path)
    diagnostics = _identity(pipeline)
    before = (pipeline.verification, pipeline.ingestion, diagnostics)

    report = json.loads(
        serialize_offline_evidence_report(pipeline, identity_diagnostics=diagnostics)
    )

    assert report["split_feasibility"]["host_structurally_feasible"] is True
    assert report["split_feasibility"]["is_assignment"] is False
    assert report["split_assignments"]["assignment_status"] == (
        "NOT_CREATED_OR_SUPPLIED"
    )
    assert (pipeline.verification, pipeline.ingestion, diagnostics) == before


def test_inconsistent_feasibility_counts_are_rejected(tmp_path: Path) -> None:
    pipeline = _pipeline(tmp_path)
    diagnostics = _identity(pipeline)
    feasibility = diagnostics.report.feasibility
    assert feasibility is not None
    forged_feasibility = replace(
        feasibility,
        component_count=feasibility.component_count - 1,
        components_structurally_feasible=False,
    )
    forged_report = replace(diagnostics.report, feasibility=forged_feasibility)
    forged_diagnostics = replace(diagnostics, report=forged_report)

    with pytest.raises(OfflineEvidenceReportError, match="does not match its counts"):
        serialize_offline_evidence_report(
            pipeline, identity_diagnostics=forged_diagnostics
        )


def test_malformed_report_inputs_raise_clear_errors(tmp_path: Path) -> None:
    with pytest.raises(
        OfflineEvidenceReportError, match="VerifiedSnapshotIngestionResult"
    ):
        serialize_offline_evidence_report(object())  # type: ignore[arg-type]

    pipeline = _pipeline(tmp_path)
    diagnostics = _identity(pipeline)
    out_of_range = replace(diagnostics, source_row_indices=(0, 2, 999))
    with pytest.raises(
        OfflineEvidenceReportError, match="invalid or contains duplicates"
    ):
        serialize_offline_evidence_report(pipeline, identity_diagnostics=out_of_range)
