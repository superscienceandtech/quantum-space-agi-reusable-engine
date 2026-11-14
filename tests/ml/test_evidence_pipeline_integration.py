"""Synthetic end-to-end tests for the offline evidence workflow."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from html import escape
from pathlib import Path

import pytest

from quantum_space_agi.ml.dataset_ingestion import (
    DatasetIngestionError,
    IngestionMetadata,
)
from quantum_space_agi.ml.evidence_report import (
    OfflineEvidenceReportError,
    serialize_offline_evidence_report,
)
from quantum_space_agi.ml.evidence_report_persistence import (
    EvidenceReportPersistenceError,
    persist_evidence_report,
    verify_evidence_report,
)
from quantum_space_agi.ml.group_splitter import (
    GroupSplitError,
    SplitConfiguration,
    split_by_host,
)
from quantum_space_agi.ml.identity_diagnostics import diagnose_ingested_identities
from quantum_space_agi.ml.snapshot_artifact import (
    SnapshotArtifactError,
    verify_snapshot_artifact,
    write_snapshot_artifact,
)
from quantum_space_agi.ml.verified_ingestion import ingest_verified_snapshot

_COLUMNS = (
    ("pl_rade", 'datatype="double" unit="Rearth"'),
    ("pl_bmasse", 'datatype="double" unit="Mearth"'),
    ("pl_name", 'datatype="char" arraysize="*"'),
    ("hostname", 'datatype="char" arraysize="*"'),
    ("pl_refname", 'datatype="char" arraysize="*"'),
)
_METADATA = IngestionMetadata(
    source_identifier="synthetic-integration-fixture",
    adql_query="SYNTHETIC FIXTURE ONLY",
)


def _votable(rows: list[tuple[object, ...]]) -> bytes:
    fields = "".join(
        f'<FIELD name="{name}" {attributes}/>' for name, attributes in _COLUMNS
    )
    table_rows = "".join(
        "<TR>"
        + "".join(
            "<TD/>" if value is None else f"<TD>{escape(str(value), quote=False)}</TD>"
            for value in row
        )
        + "</TR>"
        for row in rows
    )
    return (
        '<VOTABLE xmlns="http://www.ivoa.net/xml/VOTable/v1.3">'
        '<RESOURCE type="results"><INFO name="QUERY_STATUS" value="OK"/>'
        f"<TABLE>{fields}<DATA><TABLEDATA>{table_rows}</TABLEDATA></DATA></TABLE>"
        "</RESOURCE></VOTABLE>"
    ).encode()


def _rows(
    host_count: int = 4, *, shared_reference: bool = False
) -> list[tuple[object, ...]]:
    rows: list[tuple[object, ...]] = [
        (1.1, 2.1, "planet-0", "host-0", "ref-0"),
        (0, None, "excluded-planet", "excluded-host", "excluded-ref"),
    ]
    rows.extend(
        (
            1.0 + index,
            2.0 + index,
            f"planet-{index}",
            f"host-{index}",
            "shared-reference" if shared_reference else f"ref-{index}",
        )
        for index in range(1, host_count)
    )
    return rows


def _workflow(
    directory: Path, *, host_count: int = 4, shared_reference: bool = False
) -> dict[str, object]:
    directory.mkdir(parents=True)
    payload = _votable(_rows(host_count, shared_reference=shared_reference))
    artifact_path = directory / "synthetic-source.vot"
    write_snapshot_artifact(payload, artifact_path, metadata=_METADATA)
    direct_verification = verify_snapshot_artifact(artifact_path, include_bytes=True)
    pipeline = ingest_verified_snapshot(artifact_path)
    diagnostics = diagnose_ingested_identities(
        pipeline.ingestion, requested_partitions=3
    )
    feasibility = diagnostics.report.feasibility
    assert feasibility is not None
    split_result = None
    if feasibility.host_structurally_feasible:
        split_result = split_by_host(
            pipeline.ingestion.accepted_records,
            SplitConfiguration((0.5, 0.25, 0.25), 17),
        )
    report_bytes = serialize_offline_evidence_report(
        pipeline,
        identity_diagnostics=diagnostics,
        split_result=split_result,
    )
    report_write = persist_evidence_report(
        report_bytes,
        directory / "evidence-report.json",
        expected_source_snapshot_sha256=direct_verification.actual_sha256,
    )
    verified_report = verify_evidence_report(
        report_write.artifact.artifact_path,
        expected_source_snapshot_sha256=direct_verification.actual_sha256,
    )
    return {
        "payload": payload,
        "artifact_path": artifact_path,
        "direct_verification": direct_verification,
        "pipeline": pipeline,
        "diagnostics": diagnostics,
        "split_result": split_result,
        "report_bytes": report_bytes,
        "report_write": report_write,
        "verified_report": verified_report,
    }


def test_complete_synthetic_workflow_preserves_evidence_and_is_deterministic(
    tmp_path: Path,
) -> None:
    first = _workflow(tmp_path / "first")
    second = _workflow(tmp_path / "second")
    payload = first["payload"]
    pipeline = first["pipeline"]
    diagnostics = first["diagnostics"]
    verified_report = first["verified_report"]
    assert isinstance(payload, bytes)

    source_digest = hashlib.sha256(payload).hexdigest()
    report = json.loads(verified_report.report_bytes)
    assert first["direct_verification"].verified_bytes == payload
    assert first["direct_verification"].actual_byte_length == len(payload)
    assert first["artifact_path"].read_bytes() == payload
    assert pipeline.verification.verified_bytes == payload
    assert pipeline.ingestion.manifest.raw_response_sha256 == source_digest
    assert pipeline.ingestion.manifest.raw_response_byte_count == len(payload)
    assert pipeline.ingestion.accepted_source_row_indices == (0, 2, 3, 4)
    assert tuple(row.row_index for row in pipeline.ingestion.exclusion_ledger) == (1,)
    assert diagnostics.source_row_indices == (0, 2, 3, 4)
    assert diagnostics.report.feasibility.host_structurally_feasible is True
    assert report["accepted_source_row_indices"] == [0, 2, 3, 4]
    assert report["exclusion_ledger"][0]["source_row_index"] == 1
    assert report["exclusion_ledger"][0]["findings"]
    assert report["identity_diagnostics"]["source_row_indices"] == [0, 2, 3, 4]
    assert report["snapshot"]["caller_supplied_provenance"]["source_identifier"] == (
        "synthetic-integration-fixture"
    )
    assert report["ingestion"]["validation_scope"] == "MECHANICAL_VALIDATION_ONLY"
    assert report["split_feasibility"]["is_assignment"] is False
    assert report["split_assignments"]["assignment_status"] == "SUPPLIED_NOT_APPROVED"
    assert all(
        assignment["source_row_index"] in [0, 2, 3, 4]
        for assignment in report["split_assignments"]["assignments"]
    )
    assert report["approval_status"]["scientific"] == "NOT_ESTABLISHED_BY_THIS_REPORT"
    assert first["report_bytes"] == second["report_bytes"]
    assert verified_report.report_bytes == first["report_bytes"]
    assert verified_report.source_snapshot_sha256 == source_digest
    assert (
        verified_report.report_sha256
        == hashlib.sha256(first["report_bytes"]).hexdigest()
    )


def test_infeasible_host_grouping_does_not_create_assignments(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path / "few-hosts", host_count=2)
    diagnostics = workflow["diagnostics"]
    report = json.loads(workflow["verified_report"].report_bytes)

    assert diagnostics.report.feasibility.host_structurally_feasible is False
    assert workflow["split_result"] is None
    assert report["split_feasibility"]["host_structurally_feasible"] is False
    assert report["split_assignments"] == {
        "assignment_status": "NOT_CREATED_OR_SUPPLIED",
        "assignments": None,
    }
    with pytest.raises(GroupSplitError, match="at least three"):
        split_by_host(
            workflow["pipeline"].ingestion.accepted_records,
            SplitConfiguration((0.5, 0.25, 0.25), 17),
        )


def test_host_split_preserves_reference_and_component_overlap_diagnostics(
    tmp_path: Path,
) -> None:
    workflow = _workflow(
        tmp_path / "shared-reference", host_count=3, shared_reference=True
    )
    report = json.loads(workflow["verified_report"].report_bytes)
    leakage = report["split_assignments"]["leakage_audit"]

    assert workflow["split_result"].grouping_field == "hostname"
    assert leakage["host_overlap_count"] == 0
    assert leakage["reference_overlap_count"] == 1
    assert leakage["component_overlap_count"] == 1
    assert leakage["has_cross_partition_leakage"] is True
    assert report["split_assignments"]["assignment_status"] == "SUPPLIED_NOT_APPROVED"
    assert "reference_overlap_count" in leakage
    assert "component_overlap_count" in leakage


@pytest.mark.parametrize(
    ("manifest_field", "replacement", "error_message"),
    [
        ("sha256", "0" * 64, "SHA-256"),
        ("byte_length", len(_votable(_rows())) + 1, "byte length"),
    ],
)
def test_corrupt_snapshot_artifact_and_manifest_mismatch_are_rejected(
    tmp_path: Path,
    manifest_field: str,
    replacement: object,
    error_message: str,
) -> None:
    payload = _votable(_rows())
    artifact = tmp_path / "corrupt.vot"
    write_snapshot_artifact(payload, artifact, metadata=_METADATA)
    artifact.write_bytes(payload + b"corrupt")
    with pytest.raises(SnapshotArtifactError):
        ingest_verified_snapshot(artifact)

    artifact.write_bytes(payload)
    manifest = Path(f"{artifact}.manifest.json")
    document = json.loads(manifest.read_bytes())
    document["artifact"][manifest_field] = replacement
    manifest.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(SnapshotArtifactError, match=error_message):
        ingest_verified_snapshot(artifact)


def test_invalid_votable_and_mechanical_validation_exclusions_are_audited(
    tmp_path: Path,
) -> None:
    invalid_path = tmp_path / "invalid.vot"
    write_snapshot_artifact(b"<VOTABLE><broken>", invalid_path)
    with pytest.raises(DatasetIngestionError, match="malformed"):
        ingest_verified_snapshot(invalid_path)

    all_excluded_path = tmp_path / "all-excluded.vot"
    write_snapshot_artifact(_votable([(0, None, "p", "h", "r")]), all_excluded_path)
    pipeline = ingest_verified_snapshot(all_excluded_path)
    assert pipeline.ingestion.accepted_source_row_indices == ()
    assert pipeline.ingestion.exclusion_ledger[0].row_index == 0
    assert {
        finding.field for finding in pipeline.ingestion.exclusion_ledger[0].findings
    } == {
        "pl_bmasse",
        "pl_rade",
    }


def test_inconsistent_identity_mapping_and_report_link_are_rejected(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path / "identity")
    pipeline = workflow["pipeline"]
    diagnostics = workflow["diagnostics"]
    mismatched = replace(diagnostics, source_row_indices=(2, 0, 3, 4))
    with pytest.raises(OfflineEvidenceReportError, match="does not match"):
        serialize_offline_evidence_report(pipeline, identity_diagnostics=mismatched)

    with pytest.raises(EvidenceReportPersistenceError, match="does not match"):
        persist_evidence_report(
            workflow["report_bytes"],
            tmp_path / "wrong-link.json",
            expected_source_snapshot_sha256="0" * 64,
        )


def test_invalid_report_and_persisted_report_corruption_are_rejected(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path / "report-errors")
    report_path = workflow["report_write"].artifact.artifact_path
    invalid_report = workflow["report_bytes"].replace(
        b'"schema_version":"arc08-offline-evidence-report/1"',
        b'"schema_version":"unsupported/9"',
    )
    with pytest.raises(EvidenceReportPersistenceError, match="unsupported"):
        persist_evidence_report(
            invalid_report,
            tmp_path / "unsupported.json",
            expected_source_snapshot_sha256=workflow[
                "direct_verification"
            ].actual_sha256,
        )

    report_path.write_bytes(b"corrupted persisted report")
    with pytest.raises(SnapshotArtifactError):
        verify_evidence_report(
            report_path,
            expected_source_snapshot_sha256=workflow[
                "direct_verification"
            ].actual_sha256,
        )
