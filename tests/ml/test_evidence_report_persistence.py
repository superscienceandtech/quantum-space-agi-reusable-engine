"""Synthetic tests for durable offline evidence-report persistence."""

from __future__ import annotations

import hashlib
import json
from html import escape
from pathlib import Path

import pytest

from quantum_space_agi.ml.dataset_ingestion import REQUIRED_COLUMNS
from quantum_space_agi.ml.evidence_report import (
    EVIDENCE_REPORT_SCHEMA_VERSION,
    serialize_offline_evidence_report,
)
from quantum_space_agi.ml.evidence_report_persistence import (
    EvidenceReportPersistenceError,
    persist_evidence_report,
    verify_evidence_report,
)
from quantum_space_agi.ml.group_splitter import SplitConfiguration, split_by_host
from quantum_space_agi.ml.identity_diagnostics import diagnose_ingested_identities
from quantum_space_agi.ml.snapshot_artifact import (
    SnapshotArtifactError,
    write_snapshot_artifact,
)
from quantum_space_agi.ml.verified_ingestion import ingest_verified_snapshot

SOURCE_BYTES = b"synthetic source snapshot"
SOURCE_SHA256 = hashlib.sha256(SOURCE_BYTES).hexdigest()


def _report_bytes(source_sha256: str = SOURCE_SHA256) -> bytes:
    report = {
        "accepted_source_row_indices": [],
        "approval_status": {
            "acquisition_authorization": "NOT_ESTABLISHED_BY_THIS_REPORT",
            "scientific": "NOT_ESTABLISHED_BY_THIS_REPORT",
        },
        "exclusion_ledger": [],
        "identity_diagnostics": None,
        "ingestion": {
            "manifest_version": "arc08-offline-ingestion-manifest/1",
            "validation_scope": "MECHANICAL_VALIDATION_ONLY",
            "validation_status": "VALIDATED",
            "serialization": "TABLEDATA",
            "detected_fields": [],
            "extracted_row_count": 0,
            "mechanically_accepted_row_count": 0,
            "excluded_row_count": 0,
            "validation_policy_version": "synthetic-policy/1",
            "votable_validator_version": "synthetic-validator/1",
            "parser_version": "synthetic-parser/1",
            "raw_response_sha256": source_sha256,
            "raw_response_byte_count": len(SOURCE_BYTES),
            "validation_report": {
                "record_count": 0,
                "valid_record_indices": [],
                "excluded_source_row_indices": [],
            },
        },
        "limitations": [],
        "schema_version": EVIDENCE_REPORT_SCHEMA_VERSION,
        "snapshot": {
            "artifact_name": "synthetic-source.vot",
            "sha256": source_sha256,
            "byte_length": len(SOURCE_BYTES),
            "caller_supplied_provenance": {
                "source_identifier": None,
                "tap_endpoint": None,
                "adql_query": None,
                "query_parameters": {},
                "acquisition_timestamp": None,
                "job_identifier": None,
                "http_response_metadata": {},
            },
        },
        "split_assignments": {
            "assignment_status": "NOT_CREATED_OR_SUPPLIED",
            "assignments": None,
        },
        "split_feasibility": None,
    }
    return json.dumps(
        report,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _report_with_row_ledger() -> bytes:
    report = json.loads(_report_bytes())
    report["accepted_source_row_indices"] = [0]
    report["exclusion_ledger"] = [
        {
            "source_row_index": 1,
            "findings": [
                {
                    "field": "pl_rade",
                    "reason_code": "null_value",
                    "original_value": None,
                    "value_omitted": False,
                }
            ],
        }
    ]
    report["ingestion"].update(
        extracted_row_count=2,
        mechanically_accepted_row_count=1,
        excluded_row_count=1,
        validation_report={
            "record_count": 2,
            "valid_record_indices": [0],
            "excluded_source_row_indices": [1],
        },
    )
    return json.dumps(
        report,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _report_with_split(tmp_path: Path) -> bytes:
    field_types = {
        "pl_rade": 'datatype="double" unit="Rearth"',
        "pl_bmasse": 'datatype="double" unit="Mearth"',
        "pl_name": 'datatype="char" arraysize="*"',
        "hostname": 'datatype="char" arraysize="*"',
        "pl_refname": 'datatype="char" arraysize="*"',
    }
    rows = [
        (1, 2, "p1", "h1", "shared-ref"),
        (2, 3, "p2", "h2", "shared-ref"),
        (3, 4, "p3", "h3", "ref-3"),
    ]
    fields = "".join(
        f'<FIELD name="{name}" {field_types[name]}/>' for name in REQUIRED_COLUMNS
    )
    table_rows = "".join(
        "<TR>"
        + "".join(f"<TD>{escape(str(value), quote=False)}</TD>" for value in row)
        + "</TR>"
        for row in rows
    )
    payload = (
        '<VOTABLE xmlns="http://www.ivoa.net/xml/VOTable/v1.3">'
        '<RESOURCE type="results"><INFO name="QUERY_STATUS" value="OK"/>'
        f"<TABLE>{fields}<DATA><TABLEDATA>{table_rows}</TABLEDATA></DATA></TABLE>"
        "</RESOURCE></VOTABLE>"
    ).encode()
    artifact = tmp_path / "split-source.vot"
    write_snapshot_artifact(payload, artifact)
    pipeline = ingest_verified_snapshot(artifact)
    diagnostics = diagnose_ingested_identities(
        pipeline.ingestion, requested_partitions=3
    )
    split = split_by_host(
        pipeline.ingestion.accepted_records,
        SplitConfiguration((0.5, 0.25, 0.25), 17),
    )
    return serialize_offline_evidence_report(
        pipeline, identity_diagnostics=diagnostics, split_result=split
    )


def test_persist_and_verify_preserves_exact_bytes_and_integrity(
    tmp_path: Path,
) -> None:
    report_bytes = _report_bytes()
    result = persist_evidence_report(
        report_bytes,
        tmp_path / "report.json",
        expected_source_snapshot_sha256=SOURCE_SHA256,
    )

    verified = verify_evidence_report(
        result.artifact.artifact_path,
        expected_source_snapshot_sha256=SOURCE_SHA256,
    )

    assert result.source_snapshot_sha256 == SOURCE_SHA256
    assert result.report_sha256 == hashlib.sha256(report_bytes).hexdigest()
    assert result.byte_length == len(report_bytes)
    assert verified.report_bytes == report_bytes
    assert verified.report_sha256 == hashlib.sha256(report_bytes).hexdigest()
    assert verified.byte_length == len(report_bytes)


def test_source_snapshot_checksum_mismatch_is_rejected_before_write(
    tmp_path: Path,
) -> None:
    with pytest.raises(EvidenceReportPersistenceError, match="does not match"):
        persist_evidence_report(
            _report_bytes(),
            tmp_path / "mismatch.json",
            expected_source_snapshot_sha256="0" * 64,
        )
    assert not (tmp_path / "mismatch.json").exists()


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (b"\xff", "UTF-8 JSON"),
        (b"{broken", "UTF-8 JSON"),
        (
            b'{"schema_version":"arc08-offline-evidence-report/1","snapshot":{"sha256":"'
            + SOURCE_SHA256.encode()
            + b'","byte_length":25}}',
            "incomplete",
        ),
        (
            b'{"schema_version":"wrong","snapshot":{"sha256":"'
            + b"0" * 64
            + b'","byte_length":0}}',
            "unsupported",
        ),
        (
            b'{"schema_version":"arc08-offline-evidence-report/1","schema_version":"arc08-offline-evidence-report/1","snapshot":{"sha256":"'
            + SOURCE_SHA256.encode()
            + b'","byte_length":0}}',
            "UTF-8 JSON",
        ),
        (_report_bytes("X" * 64), "lowercase SHA-256"),
    ],
)
def test_invalid_or_unsupported_report_payloads_are_rejected(
    tmp_path: Path, payload: bytes, message: str
) -> None:
    with pytest.raises(EvidenceReportPersistenceError, match=message):
        persist_evidence_report(
            payload,
            tmp_path / "invalid.json",
            expected_source_snapshot_sha256=SOURCE_SHA256,
        )


def test_existing_destination_requires_explicit_overwrite(tmp_path: Path) -> None:
    destination = tmp_path / "no-overwrite.json"
    persist_evidence_report(
        _report_bytes(), destination, expected_source_snapshot_sha256=SOURCE_SHA256
    )

    with pytest.raises(SnapshotArtifactError, match="already exists"):
        persist_evidence_report(
            _report_bytes(), destination, expected_source_snapshot_sha256=SOURCE_SHA256
        )


def test_explicit_overwrite_updates_pair_and_is_deterministic(tmp_path: Path) -> None:
    destination = tmp_path / "overwrite.json"
    first_bytes = _report_bytes()
    first = persist_evidence_report(
        first_bytes, destination, expected_source_snapshot_sha256=SOURCE_SHA256
    )
    first_sidecar = first.artifact.manifest_path.read_bytes()
    replacement_bytes = _report_bytes("a" * 64)
    replacement_source = "a" * 64

    with pytest.raises(EvidenceReportPersistenceError, match="does not match"):
        persist_evidence_report(
            replacement_bytes,
            destination,
            expected_source_snapshot_sha256=SOURCE_SHA256,
            overwrite=True,
        )
    assert first.artifact.artifact_path.read_bytes() == first_bytes
    assert first.artifact.manifest_path.read_bytes() == first_sidecar

    second = persist_evidence_report(
        replacement_bytes,
        destination,
        expected_source_snapshot_sha256=replacement_source,
        overwrite=True,
    )
    second_sidecar = second.artifact.manifest_path.read_bytes()
    assert (
        verify_evidence_report(
            destination, expected_source_snapshot_sha256=replacement_source
        ).report_bytes
        == replacement_bytes
    )
    assert second.report_sha256 == hashlib.sha256(replacement_bytes).hexdigest()

    third = persist_evidence_report(
        replacement_bytes,
        destination,
        expected_source_snapshot_sha256=replacement_source,
        overwrite=True,
    )
    assert third.artifact.manifest_path.read_bytes() == second_sidecar
    assert not tuple(tmp_path.glob(".arc08-backup-*"))
    assert not tuple(tmp_path.glob(".arc08-artifact-*"))


@pytest.mark.parametrize("failure_call", [1, 2], ids=["artifact", "sidecar"])
def test_initial_publication_failures_leave_no_completed_pair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_call: int,
) -> None:
    import quantum_space_agi.ml.snapshot_artifact as snapshot_artifact

    original_link = snapshot_artifact.os.link
    calls = 0

    def controlled_link(source: str | Path, target: str | Path) -> None:
        nonlocal calls
        calls += 1
        if calls == failure_call:
            raise OSError("controlled publication failure")
        original_link(source, target)

    monkeypatch.setattr(snapshot_artifact.os, "link", controlled_link)
    destination = tmp_path / "failed-write.json"
    with pytest.raises(SnapshotArtifactError):
        persist_evidence_report(
            _report_bytes(), destination, expected_source_snapshot_sha256=SOURCE_SHA256
        )

    assert not destination.exists()
    assert not Path(f"{destination}.manifest.json").exists()
    assert not tuple(tmp_path.glob(".arc08-artifact-*"))


@pytest.mark.parametrize("failure_call", [1, 2], ids=["artifact", "sidecar"])
def test_overwrite_publication_failures_restore_valid_prior_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_call: int,
) -> None:
    import quantum_space_agi.ml.snapshot_artifact as snapshot_artifact

    destination = tmp_path / "rollback.json"
    old_bytes = _report_bytes()
    persist_evidence_report(
        old_bytes, destination, expected_source_snapshot_sha256=SOURCE_SHA256
    )
    old_manifest = Path(f"{destination}.manifest.json").read_bytes()
    original_replace = snapshot_artifact.os.replace
    calls = 0

    def controlled_replace(source: str | Path, target: str | Path) -> None:
        nonlocal calls
        calls += 1
        if calls == failure_call:
            raise OSError("controlled publication failure")
        original_replace(source, target)

    monkeypatch.setattr(snapshot_artifact.os, "replace", controlled_replace)
    with pytest.raises(SnapshotArtifactError, match="previous pair was restored"):
        persist_evidence_report(
            _report_bytes("b" * 64),
            destination,
            expected_source_snapshot_sha256="b" * 64,
            overwrite=True,
        )

    restored = verify_evidence_report(
        destination, expected_source_snapshot_sha256=SOURCE_SHA256
    )
    assert restored.report_bytes == old_bytes
    assert Path(f"{destination}.manifest.json").read_bytes() == old_manifest


def test_corrupt_or_incomplete_pairs_are_rejected(tmp_path: Path) -> None:
    destination = tmp_path / "corrupt.json"
    result = persist_evidence_report(
        _report_bytes(), destination, expected_source_snapshot_sha256=SOURCE_SHA256
    )
    destination.write_bytes(b"changed")

    with pytest.raises(SnapshotArtifactError, match="byte length|SHA-256"):
        verify_evidence_report(
            destination, expected_source_snapshot_sha256=SOURCE_SHA256
        )

    destination.write_bytes(_report_bytes())
    result.artifact.manifest_path.unlink()
    with pytest.raises(SnapshotArtifactError, match="manifest is missing"):
        verify_evidence_report(
            destination, expected_source_snapshot_sha256=SOURCE_SHA256
        )


def test_non_finite_json_constant_and_invalid_expected_checksum_are_rejected(
    tmp_path: Path,
) -> None:
    payload = _report_bytes().replace(b'"byte_length":25', b'"byte_length":NaN')
    with pytest.raises(EvidenceReportPersistenceError, match="UTF-8 JSON"):
        persist_evidence_report(
            payload,
            tmp_path / "nan.json",
            expected_source_snapshot_sha256=SOURCE_SHA256,
        )
    with pytest.raises(EvidenceReportPersistenceError, match="lowercase SHA-256"):
        persist_evidence_report(
            _report_bytes(),
            tmp_path / "bad-hash.json",
            expected_source_snapshot_sha256="Z" * 64,
        )


def test_exponent_overflow_is_rejected_as_non_finite(tmp_path: Path) -> None:
    payload = _report_bytes().replace(b'"byte_length":25', b'"byte_length":1e999')
    with pytest.raises(EvidenceReportPersistenceError, match="non-finite"):
        persist_evidence_report(
            payload,
            tmp_path / "overflow.json",
            expected_source_snapshot_sha256=SOURCE_SHA256,
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "non_boolean_feasibility_flag",
        "negative_count",
        "missing_feasibility_field",
        "empty_leakage_audit",
        "incomplete_configuration",
        "boolean_seed",
        "contradictory_host_count",
        "contradictory_feasibility_flag",
        "missing_identity_field_summary",
        "overlapping_host_groups",
        "contradictory_missing_host_rows",
        "host_assignment_overlap",
        "boolean_identity_source_index",
    ],
)
def test_nested_split_metadata_mutations_are_rejected_on_write_and_verify(
    tmp_path: Path, mutation: str
) -> None:
    report = json.loads(_report_with_split(tmp_path / "source"))
    feasibility = report["split_feasibility"]
    assignment = report["split_assignments"]
    if mutation == "non_boolean_feasibility_flag":
        feasibility["host_structurally_feasible"] = "true"
    elif mutation == "negative_count":
        feasibility["component_count"] = -1
    elif mutation == "missing_feasibility_field":
        del feasibility["largest_component_rows"]
    elif mutation == "empty_leakage_audit":
        assignment["leakage_audit"] = {}
    elif mutation == "incomplete_configuration":
        del assignment["configuration"]["proportions"]
    elif mutation == "boolean_seed":
        assignment["configuration"]["seed"] = True
    elif mutation == "contradictory_host_count":
        feasibility["host_group_count"] += 1
    elif mutation == "contradictory_feasibility_flag":
        feasibility["host_structurally_feasible"] = False
    elif mutation == "missing_identity_field_summary":
        report["identity_diagnostics"]["identity_fields"].pop()
    elif mutation == "overlapping_host_groups":
        host_groups = report["identity_diagnostics"]["host_groups"]
        host_groups[1]["source_row_indices"].append(
            host_groups[0]["source_row_indices"][0]
        )
    elif mutation == "contradictory_missing_host_rows":
        feasibility["missing_host_source_row_indices"] = [0]
    elif mutation == "host_assignment_overlap":
        split_assignments = assignment["assignments"]
        split_assignments[1]["partition"] = split_assignments[0]["partition"]
        assignment["leakage_audit"].update(
            host_overlap_count=1,
            component_overlap_count=1,
            has_cross_partition_leakage=True,
        )
    else:
        report["identity_diagnostics"]["source_row_indices"][0] = False

    malformed = json.dumps(
        report,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    source_sha256 = report["snapshot"]["sha256"]
    with pytest.raises(EvidenceReportPersistenceError):
        persist_evidence_report(
            malformed,
            tmp_path / f"rejected-{mutation}.json",
            expected_source_snapshot_sha256=source_sha256,
        )

    # Recompute a valid artifact sidecar for the malformed report bytes so this
    # assertion exercises semantic verification rather than checksum failure.
    malformed_artifact = tmp_path / f"verify-{mutation}.json"
    write_snapshot_artifact(malformed, malformed_artifact)
    with pytest.raises(EvidenceReportPersistenceError):
        verify_evidence_report(
            malformed_artifact, expected_source_snapshot_sha256=source_sha256
        )


def test_incomplete_nested_ingestion_section_is_rejected(tmp_path: Path) -> None:
    report = json.loads(_report_bytes())
    report["ingestion"] = {"extracted_row_count": 0}
    payload = json.dumps(report, separators=(",", ":"), sort_keys=True).encode()

    with pytest.raises(EvidenceReportPersistenceError, match="incomplete or malformed"):
        persist_evidence_report(
            payload,
            tmp_path / "incomplete.json",
            expected_source_snapshot_sha256=SOURCE_SHA256,
        )


def test_negative_accepted_source_row_index_is_rejected(tmp_path: Path) -> None:
    report = json.loads(_report_bytes())
    report["ingestion"].update(
        extracted_row_count=1,
        mechanically_accepted_row_count=1,
        raw_response_byte_count=len(SOURCE_BYTES),
        validation_report={
            "record_count": 1,
            "valid_record_indices": [-1],
            "excluded_source_row_indices": [],
        },
    )
    report["accepted_source_row_indices"] = [-1]
    payload = json.dumps(report, separators=(",", ":"), sort_keys=True).encode()

    with pytest.raises(EvidenceReportPersistenceError, match="valid_record_indices"):
        persist_evidence_report(
            payload,
            tmp_path / "negative-index.json",
            expected_source_snapshot_sha256=SOURCE_SHA256,
        )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("valid_record_indices", [True]),
        ("excluded_source_row_indices", [True]),
        ("valid_record_indices", [-1]),
        ("excluded_source_row_indices", [2]),
    ],
    ids=("bool-valid", "bool-excluded", "negative", "out-of-range"),
)
def test_nested_validation_row_indices_require_in_range_exact_integers(
    tmp_path: Path, field: str, replacement: list[object]
) -> None:
    report = json.loads(_report_with_row_ledger())
    report["ingestion"]["validation_report"][field] = replacement
    payload = json.dumps(
        report,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    with pytest.raises(EvidenceReportPersistenceError, match="source-row indices"):
        persist_evidence_report(
            payload,
            tmp_path / f"invalid-{field}.json",
            expected_source_snapshot_sha256=SOURCE_SHA256,
        )


def test_nested_validation_row_indices_accept_consistent_integers(
    tmp_path: Path,
) -> None:
    report_bytes = _report_with_row_ledger()
    written = persist_evidence_report(
        report_bytes,
        tmp_path / "valid-row-ledger.json",
        expected_source_snapshot_sha256=SOURCE_SHA256,
    )

    verified = verify_evidence_report(
        written.artifact.artifact_path,
        expected_source_snapshot_sha256=SOURCE_SHA256,
    )

    report = json.loads(verified.report_bytes)
    assert report["ingestion"]["validation_report"]["valid_record_indices"] == [0]
    assert report["ingestion"]["validation_report"]["excluded_source_row_indices"] == [
        1
    ]
