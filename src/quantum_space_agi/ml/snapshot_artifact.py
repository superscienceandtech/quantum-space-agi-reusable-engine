"""Offline persistence and integrity checks for caller-supplied byte artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import cast

from quantum_space_agi.errors import ValidationError
from quantum_space_agi.ml.dataset_ingestion import IngestionMetadata

SNAPSHOT_ARTIFACT_FORMAT_VERSION = "arc08-snapshot-artifact/1"
SNAPSHOT_MANIFEST_FORMAT_VERSION = "arc08-snapshot-manifest/1"
_HASH_CHUNK_BYTES = 1024 * 1024


class SnapshotArtifactError(ValidationError):
    """Invalid artifact input, filesystem operation, or integrity mismatch."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        original_error: OSError | None = None,
        rollback_error: OSError | None = None,
        recoverable_paths: tuple[Path, ...] = (),
    ) -> None:
        self.code = code
        self.original_error = original_error
        self.rollback_error = rollback_error
        self.recoverable_paths = recoverable_paths
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class SnapshotArtifactManifest:
    """Integrity values calculated from bytes and metadata supplied by caller."""

    format_version: str
    artifact_name: str
    byte_length: int
    sha256: str
    caller_metadata: IngestionMetadata

    def __post_init__(self) -> None:
        if (
            type(self.format_version) is not str
            or self.format_version != SNAPSHOT_ARTIFACT_FORMAT_VERSION
        ):
            raise SnapshotArtifactError(
                "invalid_manifest", "unsupported format_version"
            )
        if (
            type(self.artifact_name) is not str
            or not self.artifact_name
            or self.artifact_name in {".", ".."}
            or "/" in self.artifact_name
            or "\\" in self.artifact_name
        ):
            raise SnapshotArtifactError("invalid_manifest", "invalid artifact_name")
        if type(self.byte_length) is not int or self.byte_length < 0:
            raise SnapshotArtifactError("invalid_manifest", "invalid byte_length")
        if (
            type(self.sha256) is not str
            or len(self.sha256) != 64
            or any(character not in "0123456789abcdef" for character in self.sha256)
        ):
            raise SnapshotArtifactError("invalid_manifest", "invalid SHA-256")
        if type(self.caller_metadata) is not IngestionMetadata:
            raise SnapshotArtifactError(
                "invalid_manifest", "caller_metadata must be IngestionMetadata"
            )


@dataclass(frozen=True, slots=True)
class SnapshotArtifactWriteResult:
    """Paths and manifest for one successfully published artifact pair."""

    artifact_path: Path
    manifest_path: Path
    manifest: SnapshotArtifactManifest


@dataclass(frozen=True, slots=True)
class SnapshotArtifactVerification:
    """Successful independent verification of stored artifact bytes."""

    artifact_path: Path
    manifest_path: Path
    manifest: SnapshotArtifactManifest
    actual_byte_length: int
    actual_sha256: str
    verified_bytes: bytes | None = None


def write_snapshot_artifact(
    raw_bytes: bytes,
    destination: str | Path,
    *,
    metadata: IngestionMetadata | None = None,
    overwrite: bool = False,
) -> SnapshotArtifactWriteResult:
    """Persist exact bytes and a deterministic sidecar manifest, without networking.

    The sidecar path is ``<artifact filename>.manifest.json``. Existing files
    are rejected unless ``overwrite=True``. The manifest is published only
    after the complete artifact file has been written and flushed.
    """
    if type(raw_bytes) is not bytes:
        raise SnapshotArtifactError("invalid_payload", "raw_bytes must be bytes")
    if type(overwrite) is not bool:
        raise SnapshotArtifactError("invalid_option", "overwrite must be a bool")
    if metadata is None:
        caller_metadata = IngestionMetadata()
    elif type(metadata) is IngestionMetadata:
        caller_metadata = metadata
    else:
        raise SnapshotArtifactError(
            "invalid_metadata", "metadata must be IngestionMetadata"
        )

    artifact_path = Path(destination)
    manifest_path = Path(f"{artifact_path}.manifest.json")
    existing_artifact = artifact_path.exists()
    existing_manifest = manifest_path.exists()
    if overwrite and existing_artifact != existing_manifest:
        raise SnapshotArtifactError(
            "ambiguous_existing_pair",
            "overwrite requires both the artifact and its manifest, or neither",
        )
    if overwrite and existing_artifact:
        # Do not replace a pair whose existing integrity cannot be established.
        verify_snapshot_artifact(artifact_path, manifest_path)
    manifest = SnapshotArtifactManifest(
        format_version=SNAPSHOT_ARTIFACT_FORMAT_VERSION,
        artifact_name=artifact_path.name,
        byte_length=len(raw_bytes),
        sha256=hashlib.sha256(raw_bytes).hexdigest(),
        caller_metadata=caller_metadata,
    )
    manifest_bytes = serialize_snapshot_manifest(manifest)

    artifact_temp: Path | None = None
    manifest_temp: Path | None = None
    artifact_published = False
    manifest_published = False
    try:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        if not overwrite and (artifact_path.exists() or manifest_path.exists()):
            raise SnapshotArtifactError(
                "destination_exists", "artifact or manifest already exists"
            )
        artifact_temp = _write_temp_file(artifact_path.parent, raw_bytes)
        manifest_temp = _write_temp_file(artifact_path.parent, manifest_bytes)

        if overwrite and existing_artifact:
            _overwrite_verified_pair(
                artifact_path,
                manifest_path,
                artifact_temp,
                manifest_temp,
            )
            artifact_temp = None
            manifest_temp = None
        elif overwrite:
            # Invalidate an old sidecar before replacing bytes, so an interrupted
            # initial write cannot leave a manifest presented as current.
            os.replace(artifact_temp, artifact_path)
            artifact_temp = None
            artifact_published = True
            os.replace(manifest_temp, manifest_path)
            manifest_temp = None
            manifest_published = True
        else:
            # Hard-link publication is atomic and fails if another writer won the
            # destination race; temporary files are in the same directory.
            os.link(artifact_temp, artifact_path)
            artifact_published = True
            artifact_temp.unlink()
            artifact_temp = None
            try:
                os.link(manifest_temp, manifest_path)
            except FileExistsError as exc:
                artifact_path.unlink(missing_ok=True)
                artifact_published = False
                raise SnapshotArtifactError(
                    "destination_exists", "artifact or manifest already exists"
                ) from exc
            manifest_published = True
            manifest_temp.unlink()
            manifest_temp = None
        return SnapshotArtifactWriteResult(artifact_path, manifest_path, manifest)
    except SnapshotArtifactError:
        if manifest_published:
            manifest_path.unlink(missing_ok=True)
        if artifact_published:
            artifact_path.unlink(missing_ok=True)
        raise
    except OSError as exc:
        if manifest_published:
            manifest_path.unlink(missing_ok=True)
        if artifact_published:
            artifact_path.unlink(missing_ok=True)
        raise SnapshotArtifactError("filesystem_error", str(exc)) from exc
    finally:
        for temporary_path in (artifact_temp, manifest_temp):
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)


def serialize_snapshot_manifest(manifest: SnapshotArtifactManifest) -> bytes:
    """Serialize the manifest as compact deterministic UTF-8 JSON without BOM."""
    if type(manifest) is not SnapshotArtifactManifest:
        raise SnapshotArtifactError("invalid_manifest", "invalid manifest object")
    caller = manifest.caller_metadata
    document = {
        "manifest_format_version": SNAPSHOT_MANIFEST_FORMAT_VERSION,
        "artifact": {
            "format_version": manifest.format_version,
            "name": manifest.artifact_name,
            "byte_length": manifest.byte_length,
            "sha256": manifest.sha256,
        },
        "caller_supplied": {
            "source_identifier": caller.source_identifier,
            "tap_endpoint": caller.tap_endpoint,
            "adql_query": caller.adql_query,
            "query_parameters": {key: value for key, value in caller.query_parameters},
            "acquisition_timestamp": (
                caller.acquisition_timestamp.isoformat()
                if caller.acquisition_timestamp is not None
                else None
            ),
            "job_identifier": caller.job_identifier,
            "http_response_metadata": {
                key: value for key, value in caller.http_response_metadata
            },
        },
    }
    try:
        return json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, OverflowError) as exc:
        raise SnapshotArtifactError(
            "invalid_manifest", "manifest is not serializable"
        ) from exc


def deserialize_snapshot_manifest(raw_manifest: bytes) -> SnapshotArtifactManifest:
    """Parse and strictly validate a serialized artifact manifest."""
    if type(raw_manifest) is not bytes:
        raise SnapshotArtifactError("invalid_manifest", "manifest must be bytes")
    try:
        document = json.loads(raw_manifest.decode("utf-8"))
        if type(document) is not dict or set(document) != {
            "manifest_format_version",
            "artifact",
            "caller_supplied",
        }:
            raise ValueError("unexpected manifest fields")
        if document["manifest_format_version"] != SNAPSHOT_MANIFEST_FORMAT_VERSION:
            raise ValueError("unsupported manifest format")
        artifact = document["artifact"]
        if type(artifact) is not dict or set(artifact) != {
            "format_version",
            "name",
            "byte_length",
            "sha256",
        }:
            raise ValueError("malformed artifact metadata")
        caller = document["caller_supplied"]
        caller_keys = {
            "source_identifier",
            "tap_endpoint",
            "adql_query",
            "query_parameters",
            "acquisition_timestamp",
            "job_identifier",
            "http_response_metadata",
        }
        if type(caller) is not dict or set(caller) != caller_keys:
            raise ValueError("malformed caller metadata")
        parameters = caller["query_parameters"]
        headers = caller["http_response_metadata"]
        timestamp = caller["acquisition_timestamp"]
        if type(parameters) is not dict or type(headers) is not dict:
            raise ValueError("malformed caller metadata mappings")
        parsed_timestamp = (
            datetime.fromisoformat(timestamp) if timestamp is not None else None
        )
        metadata = IngestionMetadata(
            source_identifier=caller["source_identifier"],
            tap_endpoint=caller["tap_endpoint"],
            adql_query=caller["adql_query"],
            query_parameters=tuple(
                (key, cast(str | int | float | bool | None, value))
                for key, value in parameters.items()
            ),
            acquisition_timestamp=parsed_timestamp,
            job_identifier=caller["job_identifier"],
            http_response_metadata=tuple(headers.items()),
        )
        return SnapshotArtifactManifest(
            format_version=artifact["format_version"],
            artifact_name=artifact["name"],
            byte_length=artifact["byte_length"],
            sha256=artifact["sha256"],
            caller_metadata=metadata,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
        OverflowError,
    ) as exc:
        raise SnapshotArtifactError(
            "invalid_manifest", "malformed snapshot manifest"
        ) from exc


def verify_snapshot_artifact(
    artifact_path: str | Path,
    manifest_path: str | Path | None = None,
    *,
    include_bytes: bool = False,
) -> SnapshotArtifactVerification:
    """Verify stored length and SHA-256; optionally return those exact bytes.

    ``include_bytes=True`` lets an offline consumer use the same byte sequence
    that was hashed, avoiding a verify-then-reread race.
    """
    if type(include_bytes) is not bool:
        raise SnapshotArtifactError("invalid_option", "include_bytes must be a bool")
    artifact = Path(artifact_path)
    sidecar = (
        Path(manifest_path)
        if manifest_path is not None
        else Path(f"{artifact}.manifest.json")
    )
    try:
        manifest_bytes = sidecar.read_bytes()
    except FileNotFoundError as exc:
        raise SnapshotArtifactError(
            "manifest_missing", "snapshot manifest is missing"
        ) from exc
    except OSError as exc:
        raise SnapshotArtifactError("filesystem_error", str(exc)) from exc
    manifest = deserialize_snapshot_manifest(manifest_bytes)
    if manifest.artifact_name != artifact.name:
        raise SnapshotArtifactError(
            "artifact_name_mismatch", "manifest names a different artifact"
        )

    digest = hashlib.sha256()
    actual_length = 0
    chunks: list[bytes] | None = [] if include_bytes else None
    try:
        with artifact.open("rb") as stream:
            while chunk := stream.read(_HASH_CHUNK_BYTES):
                actual_length += len(chunk)
                digest.update(chunk)
                if chunks is not None:
                    chunks.append(chunk)
    except FileNotFoundError as exc:
        raise SnapshotArtifactError(
            "artifact_missing", "snapshot artifact is missing"
        ) from exc
    except OSError as exc:
        raise SnapshotArtifactError("filesystem_error", str(exc)) from exc
    actual_sha256 = digest.hexdigest()
    if actual_length != manifest.byte_length:
        raise SnapshotArtifactError(
            "byte_length_mismatch", "artifact byte length differs from manifest"
        )
    if actual_sha256 != manifest.sha256:
        raise SnapshotArtifactError(
            "checksum_mismatch", "artifact SHA-256 differs from manifest"
        )
    return SnapshotArtifactVerification(
        artifact,
        sidecar,
        manifest,
        actual_length,
        actual_sha256,
        b"".join(chunks) if chunks is not None else None,
    )


def _write_temp_file(directory: Path, contents: bytes) -> Path:
    descriptor, name = tempfile.mkstemp(prefix=".arc08-artifact-", dir=directory)
    path = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            if stream.write(contents) != len(contents):
                raise OSError("incomplete temporary file write")
            stream.flush()
            os.fsync(stream.fileno())
        return path
    except OSError:
        path.unlink(missing_ok=True)
        raise


def _overwrite_verified_pair(
    artifact_path: Path,
    manifest_path: Path,
    artifact_temp: Path,
    manifest_temp: Path,
) -> None:
    """Replace a verified pair, restoring hard-link backups on ordinary errors."""
    artifact_backup = _create_backup_link(artifact_path)
    try:
        manifest_backup = _create_backup_link(manifest_path)
    except OSError:
        artifact_backup.unlink(missing_ok=True)
        raise

    manifest_invalidated = False
    try:
        # The previous pair is already verified and backed up. Removing its
        # sidecar before replacing the data prevents stale metadata from matching
        # a different artifact during the multi-file publication window.
        manifest_path.unlink()
        manifest_invalidated = True
        os.replace(artifact_temp, artifact_path)
        os.replace(manifest_temp, manifest_path)
    except OSError as publication_error:
        if not manifest_invalidated:
            artifact_backup.unlink(missing_ok=True)
            manifest_backup.unlink(missing_ok=True)
            raise SnapshotArtifactError(
                "filesystem_error",
                f"overwrite publication failed before changes: {publication_error}",
                original_error=publication_error,
            ) from publication_error

        try:
            # Keep the manifest absent until the original artifact is restored.
            manifest_path.unlink(missing_ok=True)
            os.replace(artifact_backup, artifact_path)
            os.replace(manifest_backup, manifest_path)
        except OSError as rollback_error:
            recoverable_paths = tuple(
                path for path in (artifact_backup, manifest_backup) if path.exists()
            )
            raise SnapshotArtifactError(
                "overwrite_rollback_failed",
                "overwrite publication failed: "
                f"{publication_error}; rollback failed: {rollback_error}; "
                "recoverable backups: "
                + (", ".join(str(path) for path in recoverable_paths) or "none"),
                original_error=publication_error,
                rollback_error=rollback_error,
                recoverable_paths=recoverable_paths,
            ) from rollback_error
        # If artifact publication failed before replacing the original file,
        # POSIX rename may leave the backup hard link in place when source and
        # destination are the same inode. The canonical artifact and manifest
        # have now both been restored, so remove any remaining backup links.
        try:
            artifact_backup.unlink(missing_ok=True)
            manifest_backup.unlink(missing_ok=True)
        except OSError as cleanup_error:
            recoverable_paths = tuple(
                path for path in (artifact_backup, manifest_backup) if path.exists()
            )
            raise SnapshotArtifactError(
                "overwrite_rollback_cleanup_failed",
                "the previous pair was restored, but backup cleanup failed: "
                f"{cleanup_error}; recoverable backups: "
                + (", ".join(str(path) for path in recoverable_paths) or "none"),
                original_error=publication_error,
                rollback_error=cleanup_error,
                recoverable_paths=recoverable_paths,
            ) from cleanup_error
        raise SnapshotArtifactError(
            "overwrite_failed_rolled_back",
            f"overwrite publication failed and the previous pair was restored: "
            f"{publication_error}",
            original_error=publication_error,
        ) from publication_error

    # The replacement is now a complete, verifiable pair. Backup cleanup is
    # post-publication housekeeping, not a two-file atomicity guarantee.
    try:
        artifact_backup.unlink()
        manifest_backup.unlink()
    except OSError as cleanup_error:
        leftovers = tuple(
            path for path in (artifact_backup, manifest_backup) if path.exists()
        )
        raise SnapshotArtifactError(
            "backup_cleanup_failed",
            f"replacement pair was published but backup cleanup failed: "
            f"{cleanup_error}; remaining backups: "
            + (", ".join(str(path) for path in leftovers) or "none"),
            original_error=cleanup_error,
            recoverable_paths=leftovers,
        ) from cleanup_error


def _create_backup_link(source: Path) -> Path:
    """Create a unique same-directory hard link for rollback recovery."""
    descriptor, name = tempfile.mkstemp(prefix=".arc08-backup-", dir=source.parent)
    os.close(descriptor)
    backup = Path(name)
    try:
        backup.unlink()
        os.link(source, backup)
        return backup
    except OSError:
        backup.unlink(missing_ok=True)
        raise
