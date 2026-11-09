"""Offline verified-snapshot integration tests using synthetic VOTable bytes."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from hashlib import sha256
from pathlib import Path

import pytest

from quantum_space_agi.ml.dataset_ingestion import (
    DatasetIngestionError,
    IngestionMetadata,
    ingest_votable_payload,
)
from quantum_space_agi.ml.snapshot_artifact import (
    SnapshotArtifactError,
    write_snapshot_artifact,
)
from quantum_space_agi.ml.verified_ingestion import ingest_verified_snapshot

SYNTHETIC_VOTABLE = (
    b'<VOTABLE xmlns="http://www.ivoa.net/xml/VOTable/v1.3">'
    b'<RESOURCE type="results"><INFO name="QUERY_STATUS" value="OK"/>'
    b"<TABLE>"
    b'<FIELD name="pl_rade" datatype="double" unit="Rearth"/>'
    b'<FIELD name="pl_bmasse" datatype="double" unit="Mearth"/>'
    b'<FIELD name="pl_name" datatype="char" arraysize="*"/>'
    b'<FIELD name="hostname" datatype="char" arraysize="*"/>'
    b'<FIELD name="pl_refname" datatype="char" arraysize="*"/>'
    b"<DATA><TABLEDATA><TR>"
    b"<TD>1.5</TD><TD>2.5</TD><TD>synthetic-planet</TD>"
    b"<TD>synthetic-host</TD><TD>synthetic-reference</TD>"
    b"</TR></TABLEDATA></DATA></TABLE></RESOURCE></VOTABLE>"
)


def _write_fixture(tmp_path: Path, payload: bytes = SYNTHETIC_VOTABLE) -> Path:
    path = tmp_path / "synthetic.vot"
    write_snapshot_artifact(
        payload,
        path,
        metadata=IngestionMetadata(source_identifier="synthetic-test-fixture"),
    )
    return path


def _forbid_ingestion(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("ingestion must not run before verification succeeds")

    monkeypatch.setattr(
        "quantum_space_agi.ml.verified_ingestion.ingest_votable_payload",
        fail_if_called,
    )


def test_verified_snapshot_is_ingested_from_exact_verified_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact_path = _write_fixture(tmp_path)
    original_ingest = ingest_votable_payload
    received: list[bytes] = []

    def capture_ingestion(raw_bytes: bytes, *, metadata: IngestionMetadata) -> object:
        received.append(raw_bytes)
        return original_ingest(raw_bytes, metadata=metadata)

    monkeypatch.setattr(
        "quantum_space_agi.ml.verified_ingestion.ingest_votable_payload",
        capture_ingestion,
    )

    result = ingest_verified_snapshot(artifact_path)

    assert received == [SYNTHETIC_VOTABLE]
    assert result.verification.verified_bytes == SYNTHETIC_VOTABLE
    assert result.verification.actual_byte_length == len(SYNTHETIC_VOTABLE)
    assert result.verification.actual_sha256 == sha256(SYNTHETIC_VOTABLE).hexdigest()
    assert result.ingestion.manifest.raw_response_byte_count == len(SYNTHETIC_VOTABLE)
    assert (
        result.ingestion.manifest.raw_response_sha256
        == sha256(SYNTHETIC_VOTABLE).hexdigest()
    )
    assert result.ingestion.manifest.caller_metadata.source_identifier == (
        "synthetic-test-fixture"
    )


def test_missing_artifact_prevents_ingestion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact_path = _write_fixture(tmp_path)
    artifact_path.unlink()
    _forbid_ingestion(monkeypatch)

    with pytest.raises(SnapshotArtifactError) as exc_info:
        ingest_verified_snapshot(artifact_path)

    assert exc_info.value.code == "artifact_missing"


@pytest.mark.parametrize("manifest_state", ["missing", "malformed"])
def test_invalid_manifest_prevents_ingestion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    manifest_state: str,
) -> None:
    artifact_path = _write_fixture(tmp_path)
    manifest_path = Path(f"{artifact_path}.manifest.json")
    if manifest_state == "missing":
        manifest_path.unlink()
    else:
        manifest_path.write_bytes(b"not-json")
    _forbid_ingestion(monkeypatch)

    with pytest.raises(SnapshotArtifactError) as exc_info:
        ingest_verified_snapshot(artifact_path)

    assert exc_info.value.code in {"manifest_missing", "invalid_manifest"}


def test_modified_artifact_prevents_ingestion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact_path = _write_fixture(tmp_path)
    artifact_path.write_bytes(b"x" * len(SYNTHETIC_VOTABLE))
    _forbid_ingestion(monkeypatch)

    with pytest.raises(SnapshotArtifactError) as exc_info:
        ingest_verified_snapshot(artifact_path)

    assert exc_info.value.code == "checksum_mismatch"


@pytest.mark.parametrize(
    ("field", "replacement", "error_code"),
    [
        ("sha256", "0" * 64, "checksum_mismatch"),
        ("byte_length", len(SYNTHETIC_VOTABLE) + 1, "byte_length_mismatch"),
    ],
)
def test_checksum_or_length_mismatch_prevents_ingestion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    replacement: object,
    error_code: str,
) -> None:
    artifact_path = _write_fixture(tmp_path)
    manifest_path = Path(f"{artifact_path}.manifest.json")
    document = json.loads(manifest_path.read_bytes())
    document["artifact"][field] = replacement
    manifest_path.write_text(json.dumps(document), encoding="utf-8")
    _forbid_ingestion(monkeypatch)

    with pytest.raises(SnapshotArtifactError) as exc_info:
        ingest_verified_snapshot(artifact_path)

    assert exc_info.value.code == error_code


def test_valid_artifact_with_invalid_votable_returns_ingestion_error(
    tmp_path: Path,
) -> None:
    artifact_path = _write_fixture(tmp_path, b"<VOTABLE><broken>")

    with pytest.raises(DatasetIngestionError) as exc_info:
        ingest_verified_snapshot(artifact_path)

    assert exc_info.value.code == "malformed_votable"


def test_result_is_deterministic_and_immutable(tmp_path: Path) -> None:
    artifact_path = _write_fixture(tmp_path)

    first = ingest_verified_snapshot(artifact_path)
    second = ingest_verified_snapshot(artifact_path)

    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.ingestion = second.ingestion  # type: ignore[misc]


def test_direct_byte_ingestion_api_remains_available() -> None:
    result = ingest_votable_payload(SYNTHETIC_VOTABLE)

    assert result.manifest.raw_response_sha256 == sha256(SYNTHETIC_VOTABLE).hexdigest()
    assert result.manifest.accepted_row_count == 1
