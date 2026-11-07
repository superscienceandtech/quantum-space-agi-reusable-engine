# Data Architecture

**Status:** Initial architecture, updated after the ARC-03 Day 3 loader implementation. Components identified as future remain unimplemented.

## Purpose and scope

The data layer ingests tabular or nested data, retains original inputs, and supports explicit structural validation while tracing outputs to their sources. It fits the planned Python/FastAPI/Pydantic/NumPy/SciPy modular monolith. The ARC-03 loader parses CSV and JSON and associates optional metadata; a separate validator checks records against caller-supplied schemas. Scientific validation and preprocessing remain future work.

## Requirements and assumptions

### Confirmed by the project brief

- CSV and JSON are the initial supported input formats.
- Preserve source data and provenance; do not silently alter units or types.
- NASA open datasets may be a future compatibility target, but no particular dataset is selected or confirmed available.
- Future simulation and ML modules should be able to consume prepared data.
- Keep the system a modular monolith and avoid unnecessary dependencies.
- Do not train a model until there is suitable data and a measurable task.

### Recommendations (not yet team-approved requirements)

- Give every imported dataset a stable dataset identifier and record its format, schema/version, source, timestamps, and integrity checksum.
- Treat raw input as immutable. Store derived/cleaned data separately and record the transformation and software version that produced it.
- Validate structure, types, nullability, duplicate policy, and units before downstream use; report failures rather than coercing silently.
- Keep dataset-specific schemas and configuration close to the data contracts, not inside API handlers.
- Start with repository-local sample fixtures and filesystem storage; select production storage only when deployment and data-volume needs are known.

## Logical architecture

```text
external file/source
        |
        v
raw/ (retained original) ---- source metadata + provenance
        |
        v
implemented loader -> implemented structural validation -> future preprocessing
                                              |              |
                                              v              v
                                        reject/report   processed/
                                                            |
                                            simulation / API / ML consumers
```

The diagram shows the current module boundaries and future preprocessing step.

| Component | Responsibility | Current design |
| --- | --- | --- |
| Raw data storage | Keep received files byte-for-byte for audit and reprocessing. | Future `data/raw/`; read-only after ingestion. Exclude large/private data from Git as appropriate. |
| Processed data storage | Hold explicitly transformed outputs without replacing raw files. | Future `data/processed/`; associate each output with provenance. |
| Sample data | Small, clearly synthetic fixtures for examples and future development. | Future `data/samples/`; label synthetic/example values in filenames and metadata. |
| Data schemas | Define fields, types, nullability, and simple constraints. | Explicit lightweight JSON-compatible schema at `schemas/`; version/migration policy remains future work. |
| Source metadata | Describe where/how a dataset was obtained and its license/access details. | Use `source_metadata_template.json`. Never put credentials in metadata. |
| Provenance metadata | Record file identity, transformations, timestamps, and parent inputs. | Use `provenance_template.json`; link processed outputs to source checksums. |
| Data configuration | Hold non-secret dataset paths/options and supported-format defaults. | `config/data_config.json`; environment-specific secrets belong in secret management. |
| Loader interface | Read CSV/JSON into a consistent record-list result while retaining source details. | Implemented in `src/quantum_space_agi/data/loader.py`; format-specific parsers are behind `load_dataset`. |
| Validation interface | Check structure, declared types, missing values, basic constraints, and optional duplicates. | Implemented separately in `src/quantum_space_agi/data/validator.py`; returns structured issues without changing records. Scientific and unit validation remain future work. |
| ML integration | Consume versioned processed data and return model/evaluation artifacts linked to inputs. | Future module boundary; must not own or mutate raw data. |

## Suggested future layout

```text
docs/                 data and ML design documents
data/raw/             immutable input files (normally not committed)
data/processed/       derived datasets (normally not committed)
data/samples/         small synthetic examples/fixtures
data/metadata/sources/     source records for datasets
data/metadata/provenance/  artifact and transformation records
config/data_config.json    non-secret data paths and defaults
schemas/              explicit data contracts
src/<package>/data/   loader, validation, preprocessing interfaces and implementations
```

The paths above are the initial repository layout. Generic loading and explicit-schema structural validation exist; scientific validation, schema migration, and processing code remain future work. Confirm repository packaging, storage, and ignore rules with the team as those components are implemented.

## Ingestion and quality contract

1. Identify the source file and capture source metadata before parsing.
2. Parse CSV/JSON without changing original bytes; the ARC-03 loader rejects malformed input with a useful error.
3. Apply a declared schema version. Preserve source field names or document mappings.
4. Apply an explicit schema for structural and basic data-quality checks. Report missing values, configured duplicates, type mismatches, and declared range violations without modifying source data. Unit and scientific rules must be domain-specific and explicit.
5. Write accepted/processed output separately and capture every transformation in provenance.
6. Make downstream consumers state which schema and processed-data version they accept.

Nulls must remain distinguishable from zero, empty string, and sentinel values. Duplicate detection should use a declared key or documented full-row policy; do not assume all repeated observations are errors. Numeric values with units should carry units in schema/metadata or use explicit unit-bearing fields. Conversions require a recorded source unit, target unit, and conversion step.

## NASA data compatibility

Design for future external datasets by allowing source URLs/identifiers, access and retrieval timestamps, license/terms references, citation, units, coordinate/time conventions, and source-specific identifiers to be recorded. These are compatibility considerations, not evidence that a NASA source has been chosen, retrieved, endorsed, or scientifically validated. Dataset-specific documentation and terms must be reviewed when a source is selected.

## Open decisions for implementation

- Which storage backend and retention/access controls fit deployment?
- What are the first real datasets, owners, license terms, schemas, keys, and units?
- Which processed artifacts should be versioned in Git versus external storage?
- Which module owns schema definitions and compatibility/version migration?
