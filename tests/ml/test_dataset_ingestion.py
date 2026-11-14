import json
from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
from html import escape

import pytest

from quantum_space_agi.ml.dataset_ingestion import (
    REQUIRED_COLUMNS,
    DatasetIngestionError,
    DatasetIngestionResult,
    IngestionMetadata,
    ingest_votable_payload,
    serialize_ingestion_manifest,
)
from quantum_space_agi.ml.dataset_validation import (
    DatasetValidationReport,
    ExcludedRow,
    ValidationFinding,
)
from quantum_space_agi.ml.identity_diagnostics import diagnose_ingested_identities

EXTRA_COLUMN = "pl_bmasselim"
FIELD_SCHEMA = {
    "pl_rade": ('datatype="double" unit="Rearth"',),
    "pl_bmasse": ('datatype="double" unit="Mearth"',),
    "pl_name": ('datatype="char" arraysize="*"',),
    "hostname": ('datatype="char" arraysize="*"',),
    "pl_refname": ('datatype="char" arraysize="*"',),
    EXTRA_COLUMN: ('datatype="int"',),
}


def votable(
    rows: list[dict[str, object]],
    *,
    columns: tuple[str, ...] = (*REQUIRED_COLUMNS, EXTRA_COLUMN),
    status: str = "OK",
    serialization: str = "TABLEDATA",
) -> bytes:
    fields = "".join(
        f'<FIELD name="{name}" {FIELD_SCHEMA[name][0]} />' for name in columns
    )
    if serialization == "TABLEDATA":
        table_rows = "".join(
            "<TR>"
            + "".join(
                "<TD/>"
                if row.get(name) is None
                else f"<TD>{escape(str(row.get(name)), quote=False)}</TD>"
                for name in columns
            )
            + "</TR>"
            for row in rows
        )
        data = f"<DATA><TABLEDATA>{table_rows}</TABLEDATA></DATA>"
    else:
        data = '<DATA><BINARY><STREAM encoding="base64">AA==</STREAM></BINARY></DATA>'
    document = (
        '<VOTABLE xmlns="http://www.ivoa.net/xml/VOTable/v1.3">'
        '<RESOURCE type="results">'
        f'<INFO name="QUERY_STATUS" value="{status}"/>'
        f"<TABLE>{fields}{data}</TABLE>"
        "</RESOURCE></VOTABLE>"
    )
    return document.encode("utf-8")


def valid_row(
    name: str, *, radius: object = 1.5, mass: object = 2.5
) -> dict[str, object]:
    return {
        "pl_rade": radius,
        "pl_bmasse": mass,
        "pl_name": name,
        "hostname": f"host-{name}",
        "pl_refname": f"reference-{name}",
        EXTRA_COLUMN: -1,
    }


def test_ingests_valid_tabledata_and_preserves_extra_source_columns() -> None:
    payload = votable([valid_row("planet-1")])

    result = ingest_votable_payload(payload)

    assert result.manifest.validation_status == "OK"
    assert result.manifest.serialization == "TABLEDATA"
    assert result.accepted_records[0]["pl_name"] == "planet-1"
    assert result.accepted_records[0][EXTRA_COLUMN] == -1
    assert result.manifest.detected_fields[-1].name == EXTRA_COLUMN


def test_sha256_matches_independent_digest_and_size_matches_raw_bytes() -> None:
    payload = votable([valid_row("planet-1")])

    manifest = ingest_votable_payload(payload).manifest

    assert manifest.raw_response_sha256 == sha256(payload).hexdigest()
    assert manifest.raw_response_byte_count == len(payload)


def test_required_columns_are_reported_and_missing_columns_fail_actionably() -> None:
    result = ingest_votable_payload(votable([valid_row("planet-1")]))
    assert set(REQUIRED_COLUMNS).issubset(
        {field.name for field in result.manifest.detected_fields}
    )

    columns = tuple(name for name in REQUIRED_COLUMNS if name != "pl_refname")
    with pytest.raises(DatasetIngestionError) as exc_info:
        ingest_votable_payload(votable([valid_row("planet-1")], columns=columns))

    assert exc_info.value.code == "missing_required_columns"
    assert "pl_refname" in str(exc_info.value)


def test_duplicate_required_column_is_rejected() -> None:
    columns = (*REQUIRED_COLUMNS, "pl_rade")
    with pytest.raises(DatasetIngestionError) as exc_info:
        ingest_votable_payload(votable([valid_row("planet-1")], columns=columns))

    assert exc_info.value.code == "duplicate_columns"


def test_malformed_votable_is_rejected() -> None:
    with pytest.raises(DatasetIngestionError) as exc_info:
        ingest_votable_payload(b"<VOTABLE><broken>")

    assert exc_info.value.code == "malformed_votable"


def test_non_ok_query_status_is_rejected() -> None:
    with pytest.raises(DatasetIngestionError) as exc_info:
        ingest_votable_payload(votable([valid_row("p")], status="OVERFLOW"))

    assert exc_info.value.code == "query_status_not_ok"


def test_non_tabledata_serialization_fails_explicitly() -> None:
    with pytest.raises(DatasetIngestionError) as exc_info:
        ingest_votable_payload(votable([], serialization="BINARY"))

    assert exc_info.value.code == "unsupported_serialization"


def test_accepted_rows_keep_source_order_and_counts_reconcile() -> None:
    rows = [
        valid_row("first"),
        valid_row("excluded", radius=0, mass=None),
        valid_row("third"),
    ]
    result = ingest_votable_payload(votable(rows))

    assert result.manifest.extracted_row_count == 3
    assert result.manifest.accepted_row_count == 2
    assert result.manifest.excluded_row_count == 1
    assert result.accepted_source_row_indices == (0, 2)
    assert [record["pl_name"] for record in result.accepted_records] == [
        "first",
        "third",
    ]
    assert result.exclusion_ledger[0].row_index == 1
    assert result.exclusion_ledger[0].findings[0].field == "pl_bmasse"
    assert {finding.field for finding in result.exclusion_ledger[0].findings} >= {
        "pl_rade",
        "pl_bmasse",
    }


def test_multiple_findings_on_one_row_are_retained() -> None:
    row = valid_row("bad", radius=-1, mass=None)
    payload = votable([row])

    result = ingest_votable_payload(payload)

    findings = result.exclusion_ledger[0].findings
    assert [(finding.field, finding.reason_code) for finding in findings] == [
        ("pl_bmasse", "null_value"),
        ("pl_rade", "non_positive"),
    ]


def test_manifest_serialization_is_deterministic_compact_utf8_and_preserves_nulls() -> (
    None
):
    metadata = IngestionMetadata(
        source_identifier="NASA Exoplanet Archive",
        tap_endpoint="https://example.invalid/tap",
        adql_query="SELECT ...",
        query_parameters=(("format", "votable"), ("limit", 5)),
        acquisition_timestamp=datetime(2026, 11, 9, tzinfo=UTC),
        job_identifier="job-123",
        http_response_metadata=(("Content-Type", "application/x-votable+xml"),),
    )
    result = ingest_votable_payload(votable([valid_row("é")]), metadata=metadata)

    first = serialize_ingestion_manifest(result.manifest)
    second = serialize_ingestion_manifest(result.manifest)
    decoded = json.loads(first)
    assert first == second
    assert first.startswith(b"{") and not first.startswith(b"\xef\xbb\xbf")
    assert b"\\u00e9" not in first
    assert decoded["caller_supplied"]["source_identifier"] == "NASA Exoplanet Archive"
    assert decoded["caller_supplied"]["acquisition_timestamp"].endswith("+00:00")


def test_identical_inputs_produce_equal_results() -> None:
    payload = votable([valid_row("planet-1")])

    assert ingest_votable_payload(payload) == ingest_votable_payload(payload)


def test_optional_metadata_is_explicitly_unavailable_without_fabrication() -> None:
    result = ingest_votable_payload(votable([valid_row("planet-1")]))
    document = json.loads(serialize_ingestion_manifest(result.manifest))

    assert result.manifest.caller_metadata.acquisition_timestamp is None
    assert result.manifest.caller_metadata.source_identifier is None
    assert document["caller_supplied"]["acquisition_timestamp"] is None
    assert document["caller_supplied"]["source_identifier"] is None


def test_no_network_call_is_made(monkeypatch: pytest.MonkeyPatch) -> None:
    def reject_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("ingestion must remain offline")

    monkeypatch.setattr("urllib.request.urlopen", reject_network)
    monkeypatch.setattr("http.client.HTTPConnection.request", reject_network)

    assert (
        ingest_votable_payload(
            votable([valid_row("planet-1")])
        ).manifest.accepted_row_count
        == 1
    )


def test_input_bytes_are_not_mutated_or_retained_by_result() -> None:
    payload = bytearray(votable([valid_row("planet-1")]))
    frozen_payload = bytes(payload)

    with pytest.raises(DatasetIngestionError, match="immutable bytes"):
        ingest_votable_payload(payload)  # type: ignore[arg-type]

    result = ingest_votable_payload(frozen_payload)
    assert bytes(payload) == frozen_payload
    assert not hasattr(result, "raw_payload")


def test_ingestion_result_record_mappings_are_immutable() -> None:
    result = ingest_votable_payload(votable([valid_row("planet-1")]))

    with pytest.raises(TypeError):
        result.accepted_records[0]["pl_name"] = "changed"  # type: ignore[index]


def test_ingestion_result_rejects_validation_index_mismatch() -> None:
    rows = [
        valid_row("accepted-0"),
        valid_row("excluded", radius=0),
        valid_row("accepted-2"),
    ]
    result = ingest_votable_payload(votable(rows))
    mismatched_report = DatasetValidationReport(
        policy_version=result.validation_report.policy_version,
        record_count=3,
        valid_record_indices=(1, 2),
        excluded_rows=(
            ExcludedRow(
                0,
                (ValidationFinding("pl_rade", "non_positive", 0, False),),
            ),
        ),
    )

    with pytest.raises(DatasetIngestionError) as exc_info:
        DatasetIngestionResult(
            result.manifest,
            result.accepted_records,
            result.accepted_source_row_indices,
            result.exclusion_ledger,
            mismatched_report,
        )

    assert exc_info.value.code == "validation_mismatch"


def test_ingestion_result_rejects_validation_policy_version_mismatch() -> None:
    result = ingest_votable_payload(votable([valid_row("accepted")]))
    mismatched_report = replace(
        result.validation_report,
        policy_version="different-validation-policy",
    )

    with pytest.raises(DatasetIngestionError) as exc_info:
        DatasetIngestionResult(
            result.manifest,
            result.accepted_records,
            result.accepted_source_row_indices,
            result.exclusion_ledger,
            mismatched_report,
        )

    assert exc_info.value.code == "validation_mismatch"


def test_ingested_identity_diagnostics_preserve_original_row_mapping() -> None:
    rows = [
        valid_row("accepted-0"),
        valid_row("excluded", radius=None),
        valid_row("accepted-2"),
        valid_row("accepted-3"),
    ]
    ingestion = ingest_votable_payload(votable(rows))

    diagnostics = diagnose_ingested_identities(ingestion, requested_partitions=3)

    assert diagnostics.source_row_indices == (0, 2, 3)
    assert diagnostics.report.row_count == 3
    assert diagnostics.source_indices_for((0, 1, 2)) == (0, 2, 3)
    assert diagnostics.report.feasibility is not None
    assert diagnostics.report.feasibility.host_structurally_feasible
    assert ingestion.exclusion_ledger[0].row_index == 1
    assert ingestion.exclusion_ledger[0].findings[0].reason_code == "null_value"


def test_empty_payload_has_specific_error() -> None:
    with pytest.raises(DatasetIngestionError) as exc_info:
        ingest_votable_payload(b"")

    assert exc_info.value.code == "empty_payload"


def test_invalid_metadata_is_rejected_without_credentials() -> None:
    with pytest.raises(DatasetIngestionError) as exc_info:
        IngestionMetadata(http_response_metadata=(("Set-Cookie", "session=secret"),))

    assert exc_info.value.code == "invalid_metadata"
