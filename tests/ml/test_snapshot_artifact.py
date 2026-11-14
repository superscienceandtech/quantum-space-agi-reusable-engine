"""Tests for offline snapshot artifact persistence using synthetic bytes only."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import pytest

from quantum_space_agi.ml.dataset_ingestion import IngestionMetadata
from quantum_space_agi.ml.snapshot_artifact import (
    SnapshotArtifactError,
    deserialize_snapshot_manifest,
    serialize_snapshot_manifest,
    verify_snapshot_artifact,
    write_snapshot_artifact,
)

SYNTHETIC_BYTES = b"synthetic offline fixture\x00\xff"


def test_write_preserves_exact_bytes_and_independently_verifies(
    tmp_path: Path,
) -> None:
    metadata = IngestionMetadata(
        source_identifier="synthetic-fixture",
        adql_query="SELECT 1",
        acquisition_timestamp=datetime(2026, 11, 9, tzinfo=UTC),
    )

    written = write_snapshot_artifact(
        SYNTHETIC_BYTES, tmp_path / "fixture.vot", metadata=metadata
    )
    verified = verify_snapshot_artifact(written.artifact_path)

    assert written.artifact_path.read_bytes() == SYNTHETIC_BYTES
    assert written.manifest.byte_length == len(SYNTHETIC_BYTES)
    assert written.manifest.sha256 == sha256(SYNTHETIC_BYTES).hexdigest()
    assert verified.actual_byte_length == len(SYNTHETIC_BYTES)
    assert verified.actual_sha256 == sha256(SYNTHETIC_BYTES).hexdigest()
    assert verified.manifest.caller_metadata == metadata


def test_empty_payload_is_supported(tmp_path: Path) -> None:
    written = write_snapshot_artifact(b"", tmp_path / "empty.bin")

    verified = verify_snapshot_artifact(written.artifact_path)

    assert verified.actual_byte_length == 0
    assert verified.actual_sha256 == sha256(b"").hexdigest()


def test_manifest_round_trip_and_serialization_are_deterministic(
    tmp_path: Path,
) -> None:
    metadata = IngestionMetadata(
        source_identifier="synthetic-é",
        query_parameters=(("z", 2), ("a", "value")),
    )
    manifest = write_snapshot_artifact(
        SYNTHETIC_BYTES, tmp_path / "roundtrip.bin", metadata=metadata
    ).manifest

    first = serialize_snapshot_manifest(manifest)
    second = serialize_snapshot_manifest(manifest)
    restored = deserialize_snapshot_manifest(first)

    assert first == second
    assert first.startswith(b"{") and not first.startswith(b"\xef\xbb\xbf")
    assert "synthetic-é".encode() in first
    assert restored == manifest


def test_missing_artifact_is_reported(tmp_path: Path) -> None:
    written = write_snapshot_artifact(SYNTHETIC_BYTES, tmp_path / "missing.bin")
    written.artifact_path.unlink()

    with pytest.raises(SnapshotArtifactError) as exc_info:
        verify_snapshot_artifact(written.artifact_path)

    assert exc_info.value.code == "artifact_missing"


def test_missing_manifest_is_reported(tmp_path: Path) -> None:
    written = write_snapshot_artifact(SYNTHETIC_BYTES, tmp_path / "no-manifest.bin")
    written.manifest_path.unlink()

    with pytest.raises(SnapshotArtifactError) as exc_info:
        verify_snapshot_artifact(written.artifact_path)

    assert exc_info.value.code == "manifest_missing"


def test_modified_artifact_is_reported_as_checksum_mismatch(
    tmp_path: Path,
) -> None:
    written = write_snapshot_artifact(SYNTHETIC_BYTES, tmp_path / "changed.bin")
    written.artifact_path.write_bytes(b"x" * written.manifest.byte_length)
    assert len(written.artifact_path.read_bytes()) == written.manifest.byte_length

    with pytest.raises(SnapshotArtifactError) as exc_info:
        verify_snapshot_artifact(written.artifact_path)

    assert exc_info.value.code == "checksum_mismatch"


@pytest.mark.parametrize(
    ("manifest_field", "replacement", "expected_code"),
    [
        ("sha256", "0" * 64, "checksum_mismatch"),
        ("byte_length", len(SYNTHETIC_BYTES) + 1, "byte_length_mismatch"),
    ],
)
def test_manifest_integrity_mismatches_are_reported(
    tmp_path: Path,
    manifest_field: str,
    replacement: object,
    expected_code: str,
) -> None:
    written = write_snapshot_artifact(SYNTHETIC_BYTES, tmp_path / "bad-manifest.bin")
    document = json.loads(written.manifest_path.read_bytes())
    document["artifact"][manifest_field] = replacement
    written.manifest_path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(SnapshotArtifactError) as exc_info:
        verify_snapshot_artifact(written.artifact_path)

    assert exc_info.value.code == expected_code


@pytest.mark.parametrize(
    "document",
    [
        b"{}",
        b"not json",
        json.dumps(
            {
                "manifest_format_version": "arc08-snapshot-manifest/1",
                "artifact": {
                    "format_version": "arc08-snapshot-artifact/1",
                    "name": "x.bin",
                    "byte_length": True,
                    "sha256": "0" * 64,
                },
                "caller_supplied": {},
            }
        ).encode(),
    ],
)
def test_missing_or_malformed_manifest_fields_are_rejected(document: bytes) -> None:
    with pytest.raises(SnapshotArtifactError) as exc_info:
        deserialize_snapshot_manifest(document)

    assert exc_info.value.code == "invalid_manifest"


def test_existing_artifact_or_manifest_requires_explicit_overwrite(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "existing.bin"
    first = write_snapshot_artifact(b"first", destination)

    with pytest.raises(SnapshotArtifactError) as exc_info:
        write_snapshot_artifact(b"second", destination)
    assert exc_info.value.code == "destination_exists"
    assert first.artifact_path.read_bytes() == b"first"

    overwritten = write_snapshot_artifact(b"second", destination, overwrite=True)
    assert overwritten.artifact_path.read_bytes() == b"second"
    assert (
        verify_snapshot_artifact(destination).manifest.sha256
        == sha256(b"second").hexdigest()
    )
    assert not tuple(tmp_path.glob(".arc08-backup-*"))
    assert not tuple(tmp_path.glob(".arc08-artifact-*"))


def test_overwrite_true_on_empty_destination_uses_initial_write_behavior(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "initial-overwrite.bin"

    result = write_snapshot_artifact(b"initial", destination, overwrite=True)

    assert result.artifact_path.read_bytes() == b"initial"
    assert verify_snapshot_artifact(destination).manifest == result.manifest
    assert not tuple(tmp_path.glob(".arc08-backup-*"))
    assert not tuple(tmp_path.glob(".arc08-artifact-*"))


def test_interrupted_temporary_write_publishes_no_artifact_or_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import quantum_space_agi.ml.snapshot_artifact as snapshot_artifact

    original = snapshot_artifact._write_temp_file
    calls = 0

    def fail_on_manifest(directory: Path, contents: bytes) -> Path:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated interrupted manifest write")
        return original(directory, contents)

    monkeypatch.setattr(snapshot_artifact, "_write_temp_file", fail_on_manifest)
    destination = tmp_path / "interrupted.bin"

    with pytest.raises(SnapshotArtifactError) as exc_info:
        write_snapshot_artifact(SYNTHETIC_BYTES, destination)

    assert exc_info.value.code == "filesystem_error"
    assert not destination.exists()
    assert not Path(f"{destination}.manifest.json").exists()
    assert not tuple(tmp_path.glob(".arc08-artifact-*"))


def test_manifest_publication_failure_removes_new_non_overwrite_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import quantum_space_agi.ml.snapshot_artifact as snapshot_artifact

    original_link = snapshot_artifact.os.link
    calls = 0

    def fail_manifest_link(source: str | Path, destination: str | Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated manifest publication failure")
        original_link(source, destination)

    monkeypatch.setattr(snapshot_artifact.os, "link", fail_manifest_link)
    destination = tmp_path / "orphan-prevention.bin"

    with pytest.raises(SnapshotArtifactError) as exc_info:
        write_snapshot_artifact(SYNTHETIC_BYTES, destination)

    assert exc_info.value.code == "filesystem_error"
    assert not destination.exists()
    assert not Path(f"{destination}.manifest.json").exists()
    assert not tuple(tmp_path.glob(".arc08-artifact-*"))


def test_artifact_replacement_failure_restores_old_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import quantum_space_agi.ml.snapshot_artifact as snapshot_artifact

    destination = tmp_path / "overwrite-failure.bin"
    previous = write_snapshot_artifact(b"old bytes", destination)
    original_replace = snapshot_artifact.os.replace
    calls = 0

    def fail_manifest_replace(source: str | Path, target: str | Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("simulated artifact replacement failure")
        original_replace(source, target)

    monkeypatch.setattr(snapshot_artifact.os, "replace", fail_manifest_replace)
    with pytest.raises(SnapshotArtifactError) as exc_info:
        write_snapshot_artifact(b"new bytes", destination, overwrite=True)

    assert exc_info.value.code == "overwrite_failed_rolled_back"
    restored = verify_snapshot_artifact(destination)
    assert restored.manifest == previous.manifest
    assert destination.read_bytes() == b"old bytes"
    assert not tuple(tmp_path.glob(".arc08-backup-*"))


def test_manifest_publication_failure_restores_old_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import quantum_space_agi.ml.snapshot_artifact as snapshot_artifact

    destination = tmp_path / "manifest-overwrite-failure.bin"
    previous = write_snapshot_artifact(b"previous bytes", destination)
    original_replace = snapshot_artifact.os.replace
    calls = 0

    def fail_manifest_replace(source: str | Path, target: str | Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated manifest publication failure")
        original_replace(source, target)

    monkeypatch.setattr(snapshot_artifact.os, "replace", fail_manifest_replace)
    with pytest.raises(SnapshotArtifactError) as exc_info:
        write_snapshot_artifact(b"replacement bytes", destination, overwrite=True)

    assert exc_info.value.code == "overwrite_failed_rolled_back"
    restored = verify_snapshot_artifact(destination)
    assert restored.manifest == previous.manifest
    assert destination.read_bytes() == b"previous bytes"
    assert not tuple(tmp_path.glob(".arc08-backup-*"))


def test_rollback_failure_reports_errors_and_preserves_backup_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import quantum_space_agi.ml.snapshot_artifact as snapshot_artifact

    destination = tmp_path / "rollback-failure.bin"
    previous = write_snapshot_artifact(b"recoverable prior bytes", destination)
    previous_manifest_bytes = previous.manifest_path.read_bytes()
    original_replace = snapshot_artifact.os.replace
    calls = 0

    def fail_publication_and_rollback(source: str | Path, target: str | Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("publication failure")
        if calls == 3:
            raise OSError("rollback failure")
        original_replace(source, target)

    monkeypatch.setattr(snapshot_artifact.os, "replace", fail_publication_and_rollback)
    with pytest.raises(SnapshotArtifactError) as exc_info:
        write_snapshot_artifact(b"new bytes", destination, overwrite=True)

    error = exc_info.value
    assert error.code == "overwrite_rollback_failed"
    assert str(error.original_error) == "publication failure"
    assert str(error.rollback_error) == "rollback failure"
    assert len(error.recoverable_paths) == 2
    assert all(path.exists() for path in error.recoverable_paths)
    artifact_backups = [
        path
        for path in error.recoverable_paths
        if path.read_bytes() == b"recoverable prior bytes"
    ]
    manifest_backups = [
        path
        for path in error.recoverable_paths
        if path.read_bytes() == previous_manifest_bytes
    ]
    assert len(artifact_backups) == 1
    assert len(manifest_backups) == 1
    assert not previous.manifest_path.exists()


@pytest.mark.parametrize("orphan", ["artifact", "manifest"])
def test_ambiguous_existing_pair_is_rejected(tmp_path: Path, orphan: str) -> None:
    destination = tmp_path / f"orphan-{orphan}.bin"
    sidecar = Path(f"{destination}.manifest.json")
    if orphan == "artifact":
        destination.write_bytes(b"orphaned")
    else:
        sidecar.write_bytes(b"orphaned manifest")

    with pytest.raises(SnapshotArtifactError) as exc_info:
        write_snapshot_artifact(b"replacement", destination, overwrite=True)

    assert exc_info.value.code == "ambiguous_existing_pair"
    assert destination.exists() is (orphan == "artifact")
    assert sidecar.exists() is (orphan == "manifest")


@pytest.mark.parametrize("corruption", ["artifact", "manifest"])
def test_corrupt_existing_pair_is_not_overwritten(
    tmp_path: Path, corruption: str
) -> None:
    destination = tmp_path / f"corrupt-{corruption}.bin"
    written = write_snapshot_artifact(b"previous valid bytes", destination)
    if corruption == "artifact":
        destination.write_bytes(b"corrupted artifact data")
    else:
        written.manifest_path.write_bytes(b"malformed manifest")
    old_artifact_bytes = destination.read_bytes()
    old_manifest_bytes = written.manifest_path.read_bytes()

    with pytest.raises(SnapshotArtifactError):
        write_snapshot_artifact(b"replacement bytes", destination, overwrite=True)

    assert destination.read_bytes() == old_artifact_bytes
    assert written.manifest_path.read_bytes() == old_manifest_bytes
    assert not tuple(tmp_path.glob(".arc08-backup-*"))


def test_empty_metadata_is_explicit_and_not_invented(tmp_path: Path) -> None:
    written = write_snapshot_artifact(SYNTHETIC_BYTES, tmp_path / "metadata.bin")
    restored = deserialize_snapshot_manifest(written.manifest_path.read_bytes())

    assert restored.caller_metadata.source_identifier is None
    assert restored.caller_metadata.acquisition_timestamp is None
