# Data Directory Guide

This repository uses filesystem directories to keep source inputs, derived outputs, examples, and metadata separate. Generic local CSV/JSON ingestion, structured schema validation, dataset quality analysis, and deterministic scalar preprocessing are implemented. A bounded, read-only NASA Exoplanet Archive TAP JSON adapter is documented in [EXOPLANET_ARCHIVE_ADAPTER.md](../docs/EXOPLANET_ARCHIVE_ADAPTER.md); it returns data in memory and does not retain raw response files.

## Directory responsibilities

| Path | Use |
| --- | --- |
| `data/raw/` | Original external or internally supplied files. Preserve bytes; do not edit in place. Usually ignored by Git. |
| `data/processed/` | Outputs created by an explicit future transformation. Never replace the corresponding raw input. Usually ignored by Git. |
| `data/samples/` | Small, synthetic fixtures safe to review and track in Git. Current sample files are named `sample_dataset.csv` and `sample_dataset.json`. |
| `data/metadata/sources/` | Dataset-level source, status, format, version, and attribution details. |
| `data/metadata/provenance/` | Artifact-level input/checksum and transformation history. |
| `config/data_config.json` | Shared non-secret relative paths, supported formats, and default text encoding. |

## Adding a raw dataset

Place an unmodified source file in `data/raw/`, using a stable, descriptive filename. Before it is consumed, create a source record in `data/metadata/sources/` based on `docs/source_metadata_template.json` and a provenance record in `data/metadata/provenance/` based on `docs/provenance_template.json`. Use the same `dataset_id` in related records. Record the actual source identifier, retrieval/collection time when known, license or terms status, file format, dataset version, and a computed checksum. Do not guess at attribution or put secrets in metadata.

Raw and processed data directories are ignored by default to prevent accidental commits of large or restricted datasets. The sample files and metadata remain tracked. If the team approves tracking a specific real dataset, change ignore policy deliberately and document its license and size.

## Processed datasets and metadata linkage

Future processing should write a new file under `data/processed/`; it must not overwrite the input. Its provenance record should identify the input artifact(s), checksums, transformations, schema/dataset version, and producing code revision. The current provenance template is a starting structure and does not calculate checksums automatically.

## Sample data

`sample_dataset.csv` and `sample_dataset.json` each contain one identical generic illustrative record. `record_id` begins with `EXAMPLE`, and `notes` marks it synthetic. Values are placeholders with no scientific meaning, external source, NASA mission association, or validation claim. Use these files as fixtures for CSV/JSON ingestion and validation tests.

## Configuration

`config/data_config.json` uses repository-relative paths, so it does not depend on a developer's machine. Its fields are:

- `data_root`: top-level data directory.
- `raw_dir`, `processed_dir`, `samples_dir`, `metadata_dir`: locations for each data category.
- `supported_formats`: local text formats (`csv`, `json`) supported by the generic readers.
- `default_encoding`: default text encoding for future readers (`utf-8`).

The generic data-directory configuration does not define a global size limit; a suitable local-file limit depends on deployment and loader behavior. The Exoplanet Archive TAP adapter independently rejects response bodies larger than 10 MiB. Put machine-specific overrides in an untracked `config/data_config.local.json`; never put credentials in either config file.

## Not implemented yet

The local loader reads one explicitly supplied file, and the validators check records against explicit schemas. Deterministic scalar preprocessing is available separately; it does not perform learned transformations. There is no directory discovery API, general checksum generator, or storage service. The Exoplanet Archive adapter computes a response checksum but does not retain response bytes. No task-specific ML pipeline exists. See the [loader guide](../docs/DATA_LOADER.md), [validation guide](../docs/DATA_VALIDATION.md), and [Exoplanet Archive adapter guide](../docs/EXOPLANET_ARCHIVE_ADAPTER.md) for API and limits. Structural validation and successful parsing do not establish scientific validity.
