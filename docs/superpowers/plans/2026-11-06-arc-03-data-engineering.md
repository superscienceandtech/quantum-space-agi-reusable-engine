# ARC-03 Data Engineering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dependency-free data engineering layer for source metadata, JSON/CSV ingestion, schema validation, provenance, quality analysis, export, and future generic data adapters.

**Architecture:** Keep `quantum_space_agi.data` separate from the existing core utilities and expose only deliberate data APIs. Use standard-library models and readers, preserve CSV cells as strings, retain invalid records in reports rather than dropping or coercing them, preserve provenance in a versioned JSON envelope, and keep CSV output conventional and tabular.

**Tech Stack:** Python >=3.11, standard library at runtime, existing `ValidationError`, pytest, Ruff, mypy, setuptools.

**Spec:** User-provided ARC-03 implementation authorization and requirements in this session; no separate design document exists.

## Global Constraints

- Python standard library only for runtime utilities.
- Do not add NumPy, SciPy, Qiskit, PyTorch or other runtime dependencies.
- Preserve ARC-00, ARC-01 and ARC-02.
- Reuse existing Result, ErrorInfo and ValidationError where appropriate.
- Use type hints.
- Write clear docstrings.
- Keep deterministic behavior.
- Support offline testing.
- Avoid duplicate validation logic.
- Avoid unnecessary dependencies.
- Do not put NASA-specific assumptions in generic core models.
- Do not mix raw data with transformed data.
- Preserve original source information.
- Do not silently discard invalid records.
- CSV ingestion preserves every cell as a string.
- JSON parsing rejects non-standard NaN and infinity constants.
- Schema `int` fields do not accept booleans despite Python's `bool` subclassing `int`.
- Do not start ARC-04, commit, push, or run Python 3.11–3.13 tests.

## Review Focus

- Malformed or partially decoded JSON/CSV must produce a clear data error with the original parse/decode exception chained; it must not return partial data.
- External JSON without a package envelope must require caller-supplied dataset/source provenance; the loader must never invent a provider or source version.
- CSV fields that are blank, absent, or quoted must not be inferred into numbers, nulls, or booleans during ingestion.
- Invalid schema records must remain available and be identified by stable zero-based record index.
- Export to an existing path without overwrite authorization must leave the original file unchanged, including when a write fails.

---

### Task 1: Source, provenance, and dataset contracts

**Files:**
- Create: `src/quantum_space_agi/data/errors.py`
- Create: `src/quantum_space_agi/data/sources.py`
- Create: `src/quantum_space_agi/data/provenance.py`
- Create: `src/quantum_space_agi/data/models.py`
- Test: `tests/data/test_sources.py`
- Test: `tests/data/test_provenance.py`
- Test: `tests/data/test_models.py`

**Interfaces:**
- Consumes: `quantum_space_agi.errors.QuantumSpaceError` and `ValidationError`.
- Produces: `DataEngineeringError`, `DataFormatError`, `DataSourceError`, `DataExportError`; `DataSource(identifier, description=None, url=None, version=None, metadata=...)`; `DataSourceRegistry.register(source)`, `.get(identifier)`, `.sources`; `DataFormat.JSON` / `.CSV`; `Provenance(dataset_id, source, retrieved_at, data_format, dataset_version=None, transformations=(), metadata=...)`; `Dataset(provenance, records, metadata=...)`.

- [ ] **Step 1: Write tests first.** Cover source identity and optional fields, registry registration/lookup/duplicate and missing identifiers, timezone-aware provenance, and dataset record/metadata retention. Add errors for malformed identifiers and invalid timestamps.
- [ ] **Step 2: Run the tests and verify the missing-contract failure.**

Run: `python3 -m pytest -q tests/data/test_sources.py tests/data/test_provenance.py tests/data/test_models.py`

Expected: collection fails because the `quantum_space_agi.data` modules do not exist.

- [ ] **Step 3: Implement only these contracts.** Use frozen/slotted dataclasses where safe; copy caller metadata into per-instance dictionaries; reject empty identifiers, duplicate registry keys, naive timestamps, and invalid formats; do not generate source descriptions, URLs, or versions.
- [ ] **Step 4: Re-run the focused tests.**

Run: `python3 -m pytest -q tests/data/test_sources.py tests/data/test_provenance.py tests/data/test_models.py`

Expected: all tests in these files pass; registry state is instance-local and deterministic.

### Task 2: JSON, CSV, and local-file ingestion

**Files:**
- Create: `src/quantum_space_agi/data/ingestion.py`
- Test: `tests/data/test_ingestion.py`

**Interfaces:**
- Consumes: `Dataset`, `DataFormat`, `Provenance`, and data exceptions from Task 1.
- Produces: `load_json(text, *, provenance=None)`, `load_csv(text, *, provenance)`, and `load_file(path, *, data_format, provenance=None, encoding="utf-8")`.
- JSON envelope: `{"format_version": 1, "provenance": ..., "records": [...], "metadata": {...}}`. Plain JSON must be a list of object records and requires explicit provenance. CSV always yields string values and requires explicit provenance.

- [ ] **Step 1: Write tests first.** Cover valid JSON list/envelope, valid CSV, UTF-8 and an alternate encoding through a local file, malformed JSON/CSV, duplicate/empty CSV headers, inconsistent CSV row widths, non-standard JSON NaN/infinity, unsupported JSON shapes/versions, missing provenance, empty files, and preservation of row count and original values.
- [ ] **Step 2: Run focused tests and verify the expected missing-module failure.**

Run: `python3 -m pytest -q tests/data/test_ingestion.py`

Expected: collection fails because `ingestion.py` does not exist.

- [ ] **Step 3: Implement readers.** Parse JSON without coercion beyond JSON's native values; reject non-standard NaN/infinity constants, non-object rows, and unsupported envelope versions. Use `csv.reader` with explicit encoding and `newline=""`; require a non-empty unique header and equal row widths, then build mappings without type inference. Convert known parse, decode, and I/O errors to data-specific exceptions with `raise ... from exc`; never catch broadly or return partial rows.
- [ ] **Step 4: Re-run ingestion tests.**

Run: `python3 -m pytest -q tests/data/test_ingestion.py`

Expected: malformed input raises clear chained exceptions and CSV values remain strings.

### Task 3: Schema and validation reports

**Files:**
- Create: `src/quantum_space_agi/data/schemas.py`
- Test: `tests/data/test_schemas.py`

**Interfaces:**
- Consumes: `Dataset` and existing `ValidationError`.
- Produces: `FieldSchema(name, value_type, required=True, allow_none=False)`, `DataSchema(identifier, version, fields)`, per-field `ValidationIssue`, `InvalidRecord(record_index, issues)`, `SchemaValidationReport(schema_id, schema_version, record_count, valid_count, invalid_records, is_valid)`, and `validate_dataset(dataset, schema)`.

- [ ] **Step 1: Write tests first.** Cover valid rows, missing required keys, `None`, optional fields, wrong types including `bool` for an `int` field, schema id/version retention, multiple issues in one row, and stable zero-based indices.
- [ ] **Step 2: Run focused tests and observe the expected missing-module failure.**

Run: `python3 -m pytest -q tests/data/test_schemas.py`

Expected: collection fails because `schemas.py` does not exist.

- [ ] **Step 3: Implement validation without conversion or mutation.** Validate declared fields only; missing required values and disallowed null values are issues. Match declared built-in types exactly for JSON values (notably, booleans are not integers). Keep every input row in the original `Dataset`, and report every invalid row and issue.
- [ ] **Step 4: Re-run schema tests.**

Run: `python3 -m pytest -q tests/data/test_schemas.py`

Expected: all reports identify invalid rows and the dataset records are unchanged.

### Task 4: Data quality summaries

**Files:**
- Create: `src/quantum_space_agi/data/quality.py`
- Test: `tests/data/test_quality.py`

**Interfaces:**
- Consumes: `Dataset` and optional `SchemaValidationReport`.
- Produces: `FieldStatistics`, `DuplicateGroup`, `DataQualityReport`, and `analyze_quality(dataset, *, validation_report=None)`.
- Missing means absent key, `None`, or blank/whitespace text. Duplicate means exact record equality independent of mapping key order. Numeric statistics include finite `int`/`float` values but exclude booleans.

- [ ] **Step 1: Write tests first.** Cover empty and populated datasets, missing counts, repeated exact rows, different key order, invalid-record indices, numeric min/max/mean/count, booleans, and non-finite numeric values.
- [ ] **Step 2: Run focused tests and observe the expected missing-module failure.**

Run: `python3 -m pytest -q tests/data/test_quality.py`

Expected: collection fails because `quality.py` does not exist.

- [ ] **Step 3: Implement deterministic analysis.** Do not modify the dataset or remove duplicates/invalid records. Use stable ordering in reports and explicit numeric filtering.
- [ ] **Step 4: Re-run quality tests.**

Run: `python3 -m pytest -q tests/data/test_quality.py`

Expected: report values and ordering are deterministic; source records are unchanged.

### Task 5: JSON and CSV export

**Files:**
- Create: `src/quantum_space_agi/data/export.py`
- Test: `tests/data/test_export.py`

**Interfaces:**
- Consumes: `Dataset`, `DataFormat`, `DataExportError`, and `load_json` / `load_csv`.
- Produces: `export_json(dataset, path, *, overwrite=False, encoding="utf-8")` and `export_csv(dataset, path, *, overwrite=False, encoding="utf-8")`.
- JSON writes the version-1 envelope and preserves provenance/metadata. CSV writes ordinary rows with deterministic field ordering; cells are text and provenance/metadata are not embedded. Existing files are preserved unless `overwrite=True`.

- [ ] **Step 1: Write tests first.** Cover JSON dataset round-trip, CSV string-record round-trip, deterministic headers, unsupported nested CSV values, overwrite refusal, explicit overwrite, and cleanup when export fails.
- [ ] **Step 2: Run focused tests and observe the expected missing-module failure.**

Run: `python3 -m pytest -q tests/data/test_export.py`

Expected: collection fails because `export.py` does not exist.

- [ ] **Step 3: Implement serialization and safe writes.** Write to a temporary file in the target directory; atomically replace only when overwrite is authorized; otherwise create the final target exclusively so a race cannot clobber an existing file. Always clean temporary files and chain expected I/O/serialization errors.
- [ ] **Step 4: Re-run export tests.**

Run: `python3 -m pytest -q tests/data/test_export.py`

Expected: JSON preserves provenance, CSV semantics are documented, and existing targets remain unchanged without explicit overwrite.

### Task 6: Generic future adapter contract

**Files:**
- Create: `src/quantum_space_agi/data/adapters/base.py`
- Create: `src/quantum_space_agi/data/adapters/__init__.py`
- Test: `tests/data/test_adapters.py`

**Interfaces:**
- Consumes: `DataSource`, `DataFormat`, and timezone-aware retrieval metadata.
- Produces: `RetrievedPayload(content: bytes, data_format: DataFormat, retrieved_at, dataset_version=None)` and a structural `DataAdapter` protocol with `source` and synchronous `retrieve() -> RetrievedPayload`.

- [ ] **Step 1: Write tests first.** Define a local in-test adapter and verify structural compatibility and payload/source metadata. Assert imports do not access the network.
- [ ] **Step 2: Run focused tests and observe the expected missing-module failure.**

Run: `python3 -m pytest -q tests/data/test_adapters.py`

Expected: collection fails because the adapter package does not exist.

- [ ] **Step 3: Implement only the protocol and payload contract.** Include no HTTP client, endpoint, API key, retry, or NASA-specific behavior.
- [ ] **Step 4: Re-run adapter tests.**

Run: `python3 -m pytest -q tests/data/test_adapters.py`

Expected: the local stub satisfies the protocol; no network or optional dependencies are imported.

### Task 7: Public exports and project documentation

**Files:**
- Create: `src/quantum_space_agi/data/__init__.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: public types and functions from Tasks 1–6.
- Produces: deliberate imports for core data models, source/registry, ingestion, schema, quality, export, adapter contract; a concise README statement of ARC-03 capabilities and non-goals.

- [ ] **Step 1: Write import smoke assertions.** Assert each intended data API imports from `quantum_space_agi.data`; assert importing does not mutate root logging or access the environment/network.
- [ ] **Step 2: Run the smoke test before exports exist.**

Run: `python3 -c 'from quantum_space_agi.data import Dataset'`

Expected: import fails because `data/__init__.py` does not yet export `Dataset`.

- [ ] **Step 3: Add intentional exports and update README.** Do not modify `quantum_space_agi/__init__.py`; keep ARC-03 APIs namespaced under `.data`.
- [ ] **Step 4: Re-run import smoke and check local Markdown links.**

Run: `python3 -c 'from quantum_space_agi.data import Dataset, DataSource, load_json, validate_dataset, analyze_quality, export_json'`

Expected: import succeeds without optional dependencies or side effects.

### Task 8: Full integration verification

**Files:**
- No new production files; all ARC-03 source/tests and the README.

**Interfaces:**
- Consumes: completed tasks 1–7.
- Produces: verified offline ARC-00/01/02/03 package and build artifacts.

- [ ] **Step 1: Run the full suite.**

Run: `python3 -m pytest`

Expected: all existing and new tests pass.

- [ ] **Step 2: Run Ruff and mypy.**

Run: `ruff check . && ruff format --check . && mypy`

Expected: no lint, formatting, or type errors.

- [ ] **Step 3: Verify imports and package build.**

Run: `python3 -c 'import quantum_space_agi.data' && python3 -m build --no-isolation`

Expected: import succeeds; source archive and wheel build successfully and wheel includes ARC-03 modules.

- [ ] **Step 4: Check the final diff and scope.**

Run: `git diff --check && git status --short --branch --untracked-files=all`

Expected: no whitespace errors; only planned ARC-03 files plus preserved pre-existing ARC-00/01/02 changes are present; no commit, push, or ARC-04 work occurred.

## Coverage self-review

- Source identification/metadata and registry: Task 1.
- Retrieval time, versions, transformations, and metadata provenance: Tasks 1–2.
- JSON/CSV/local files, encoding, errors, resource safety: Task 2.
- Required fields, types, missing values, invalid records, schema version: Task 3.
- Missing values, duplicates, invalid-record links, field statistics, summary: Task 4.
- JSON/CSV output, metadata policy, safe overwrite: Task 5.
- Generic NASA-ready adapter seam without provider assumptions: Task 6.
- Public API, documentation, offline quality checks and packaging: Tasks 7–8.

No Pydantic decision is needed for this phase: no runtime schema dependency is introduced. Python 3.11–3.13 matrix testing is deferred as requested.
