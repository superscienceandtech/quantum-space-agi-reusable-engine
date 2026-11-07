# CSV/JSON Loader

The ARC-03 loader parses one explicitly selected CSV or JSON file and returns records plus any matching source/provenance metadata. It uses only Python's standard library. Successful parsing means only that the file has a supported, parseable structure; it does not establish scientific validity or schema correctness.

## Use

From the repository root, with `src` on the import path:

```python
from quantum_space_agi.data import load_dataset

result = load_dataset("data/samples/sample_dataset.csv")
print(result.dataset_id)
print(result.records)
print(result.loading_status)
```

Run tests with:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

On Windows PowerShell, set the import path for the command with `$env:PYTHONPATH = "src"` before running Python.

The function accepts `load_dataset(source_file, *, metadata_dir=None, dataset_id=None, encoding="utf-8")`. Metadata is looked up under `<data-root>/metadata` by default (for example, `data/samples/file.csv` uses `data/metadata`). Supply `metadata_dir` for another layout. An explicit `dataset_id` selects matching metadata, but a source record that names files must still reference the input.

## Input structures and output

- **CSV:** first row is the header; each following row becomes a dictionary. Values remain strings. Duplicate or empty header names and row widths that do not match the header are errors. Blank input rows are not silently discarded.
- **JSON object:** one object becomes one record. JSON value types are preserved.
- **JSON array:** an array of objects becomes the record list; non-object entries are errors.
- **JSON records envelope:** an object whose only key is `records` and whose value is an array of objects is treated as an envelope. If an object has `records` plus other keys, the entire object is treated as one record so no fields are silently dropped.

The immutable `DatasetLoadResult` includes `dataset_id`, absolute `source_file`, `format`, `records`, `record_count`, source and provenance metadata objects and references, `dataset_version`, UTC `loaded_at`, `loading_status`, `metadata_warnings`, and a small `operation` record. CSV is not type-inferred and neither CSV nor JSON fields are renamed or unit-converted.

## Metadata association

The source sidecar is selected by matching its `files` (or `source_file`) reference to the requested path, or by `dataset_id` if supplied. Provenance is associated by dataset ID and, when present, matching file references. Source `data_status`, including `synthetic`, is returned unchanged. Dataset version is taken from source metadata, or provenance when absent in the source record.

Missing metadata is not fabricated: records are returned with `loading_status="loaded_with_metadata_warnings"` and explanatory `metadata_warnings`; `dataset_id` may remain `None` unless the caller supplied one. Malformed, ambiguous, or inconsistent metadata raises `MetadataAssociationError`. Loading never writes to source files or provenance sidecars.

## Errors

All loader exceptions derive from `DataLoadError`:

| Exception | Meaning |
| --- | --- |
| `FileAccessError` | Input could not be opened/read. |
| `DataFormatError` | Malformed CSV/JSON, undecodable text, or unsupported record shape. |
| `MetadataAssociationError` | Sidecar is malformed, ambiguous, or inconsistent. |
| `UnsupportedFormatError` | File extension is not `.csv` or `.json`. |
| `EmptyDatasetError` | File or parsed dataset has no records. |

## Limits and next work

The loader materializes the full file and record list in memory; no file-size limit or streaming behavior is implemented. It does not apply `config/data_config.json` automatically, recursively discover files, enforce schemas, preprocess, calculate checksums, or append a load event to provenance. Existing provenance history is read-only. For schema contracts, null/duplicate/range behavior, structured reports, and scientific-validation limits, see [DATA_VALIDATION.md](DATA_VALIDATION.md). Downstream ARC-04/05/08/10 modules can depend on the small result structure without depending on the CSV or JSON parser details.
