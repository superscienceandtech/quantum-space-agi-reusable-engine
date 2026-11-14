"""Offline orchestration from verified snapshot bytes to VOTable ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from quantum_space_agi.ml.dataset_ingestion import (
    DatasetIngestionResult,
    ingest_votable_payload,
)
from quantum_space_agi.ml.snapshot_artifact import (
    SnapshotArtifactVerification,
    verify_snapshot_artifact,
)


@dataclass(frozen=True, slots=True)
class VerifiedSnapshotIngestionResult:
    """Artifact integrity verification linked to the resulting offline ingest."""

    verification: SnapshotArtifactVerification
    ingestion: DatasetIngestionResult

    def __post_init__(self) -> None:
        if type(self.verification) is not SnapshotArtifactVerification:
            raise TypeError("verification must be SnapshotArtifactVerification")
        if type(self.ingestion) is not DatasetIngestionResult:
            raise TypeError("ingestion must be DatasetIngestionResult")
        if self.verification.verified_bytes is None:
            raise ValueError("verification must retain the verified bytes")
        if (
            self.ingestion.manifest.raw_response_byte_count
            != self.verification.actual_byte_length
            or self.ingestion.manifest.raw_response_sha256
            != self.verification.actual_sha256
            or self.ingestion.manifest.caller_metadata
            != self.verification.manifest.caller_metadata
        ):
            raise ValueError("ingestion manifest does not match verified artifact")


def ingest_verified_snapshot(
    artifact_path: str | Path,
    manifest_path: str | Path | None = None,
) -> VerifiedSnapshotIngestionResult:
    """Verify a stored artifact before passing the same bytes to offline ingest.

    Snapshot verification errors propagate without invoking ingestion. Caller
    metadata recorded in the verified sidecar is forwarded unchanged to the
    existing ingestion API; no acquisition context is synthesized.
    """
    verification = verify_snapshot_artifact(
        artifact_path, manifest_path, include_bytes=True
    )
    verified_bytes = verification.verified_bytes
    if verified_bytes is None:  # Defensive guard for a broken verifier contract.
        raise RuntimeError("snapshot verifier did not return verified bytes")
    ingestion = ingest_votable_payload(
        verified_bytes, metadata=verification.manifest.caller_metadata
    )
    return VerifiedSnapshotIngestionResult(verification, ingestion)
