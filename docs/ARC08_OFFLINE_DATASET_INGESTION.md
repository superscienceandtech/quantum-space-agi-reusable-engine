# ARC-08 Offline VOTable Ingestion

**Status:** Offline engineering component only. It does not authorize NASA
requests, establish a scientifically approved cohort, or change the ML NO-GO.

## API

`quantum_space_agi.ml.ingest_votable_payload(raw_payload: bytes, *, metadata: IngestionMetadata | None = None)` accepts bytes already acquired by the caller. It performs no network access and does not create an acquisition timestamp. Supplied metadata is optional; absent values remain `null` in the manifest. A source identifier is caller-provided and is not inferred from NASA-like columns.

The API reuses `validate_tap_votable()` for XML safety, TAP query-status and VOTable structure validation. It extracts only inline scalar `TABLEDATA`; `BINARY`, `BINARY2`, and `FITS` responses are rejected because the validator does not decode those formats. The required columns are `pl_rade`, `pl_bmasse`, `pl_name`, `hostname`, and `pl_refname`. Duplicate columns and missing required columns fail explicitly. Other scalar fields are retained in the same order as the source table.

VOTable datatypes are decoded according to their declared scalar type; this is format parsing, not scientific preprocessing. Empty numeric cells become null, declared null sentinels become null, and character values retain their exact parsed text. The Phase 4.1 mechanical checks then report missing, non-numeric, non-finite, non-positive, and missing-identity findings. They do not interpret limit codes, select scientific solutions, normalize identities, deduplicate rows, or make scientific eligibility decisions.

## Result and manifest

`DatasetIngestionResult` contains immutable accepted record mappings, their original zero-based row positions, the Phase 4.1 validation report, and an exclusion ledger. The manifest reconciles extracted, accepted, and excluded counts. It records the exact input byte count and SHA-256, detected field names/types/units/null sentinels, query-status result, serialization, and parser/validator/policy versions. Caller metadata is kept separate from calculated values. `serialize_ingestion_manifest()` returns compact, sorted-key UTF-8 JSON without a BOM; missing metadata is encoded as JSON null.

The input bytes are not retained by the result or written to disk. A checksum does not reconstruct the raw response; callers need a separately approved durable retention plan. The result is not an ARC-03 `Dataset`: the current ARC-03 format enum does not include VOTable, and `Provenance.retrieved_at` is required even when a caller has no verified acquisition time. No retrieval time is invented or mapped silently. Any later ARC-03 conversion requires a verified compatible provenance mapping.

This component validates representation and basic numeric usability only. It does not apply the candidate cohort, interpret `pl_bmasselim`/`pl_radelim`, filter controversy or solution status, resolve identities, split data, fit models, or claim scientific validation or performance.
