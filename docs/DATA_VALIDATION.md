# Data Validation

The ARC-03 validator checks loaded records against an explicit, lightweight schema. It is separate from file parsing, non-mutating, and dependency-free. Passing validation means only that records meet the declared structural and basic data-quality rules; it is not scientific validation.

## Architecture and workflow

1. `load_dataset()` parses CSV or JSON into `DatasetLoadResult` without coercion.
2. A caller supplies a schema (or a reviewed schema file loaded as JSON).
3. `validate_dataset()` checks dataset identity, record structure, fields, values, constraints, and optional duplicates.
4. The caller uses the `ValidationReport`; invalid records remain present in the original load result and source file.

```python
import json
from pathlib import Path

from quantum_space_agi.data import load_dataset, validate_dataset

loaded = load_dataset("data/samples/sample_dataset.csv")
schema = json.loads(Path("schemas/sample_dataset.schema.json").read_text())
report = validate_dataset(loaded, schema)

if not report.is_valid:
    for issue in report.errors:
        print(issue.record_index, issue.field_name, issue.category, issue.message)
```

`validate_dataset()` accepts a `DatasetLoadResult`, a mapping with `records` and optional `dataset_id`, or a sequence of record mappings. A schema definition error raises `SchemaDefinitionError`; data problems are returned in the report instead of raised.

## Schema format

Schemas are JSON-compatible objects. `schema_name` and `fields` are required. `dataset_id` is optional and, when set, must match the loaded dataset ID. Each field has a `type`; `required` and `nullable` default to false. Unknown fields are errors unless `allow_unexpected_fields` is true.

```json
{
  "schema_name": "example-v1",
  "dataset_id": "optional-dataset-id",
  "allow_unexpected_fields": false,
  "fields": {
    "record_id": {
      "type": "string",
      "required": true,
      "nullable": false,
      "allow_empty_string": false,
      "min_length": 1,
      "max_length": 80
    },
    "value": {
      "type": "float",
      "required": true,
      "nullable": false,
      "minimum": 0,
      "maximum": 100,
      "allowed_values": [1.5, 2.0]
    },
    "comment": {
      "type": "string",
      "required": false,
      "nullable": true,
      "whitespace_only_is_missing": true
    }
  },
  "duplicate_detection": {
    "enabled": true,
    "strategy": "fields",
    "fields": ["record_id"]
  }
}
```

Supported field types are `string`, `integer`, `float`, `boolean`, `array`, and `object`. `integer` accepts an integer value (not a boolean or float); CSV integer strings must contain only an optional sign and digits. `float` accepts finite integer/float JSON numbers or a finite decimal/exponent string from CSV. `boolean` accepts JSON booleans or the exact lowercase CSV strings `true` and `false`. Arrays and objects are checked by their top-level container type; their nested contents are not recursively schema-validated.

CSV values are not changed: numeric and boolean strings are checked for valid representation but remain strings in `DatasetLoadResult.records`. JSON values also remain unchanged. Invalid numeric strings are errors; no conversion or unit handling occurs.

### Required, optional, null, and empty values

- An absent required key produces `missing_required`; an absent optional key is accepted.
- Explicit JSON `null` is accepted only with `nullable: true`, otherwise `null_not_allowed` is reported. Nullability does not make an absent required key acceptable.
- Empty strings are rejected by default; set `allow_empty_string: true` to accept them.
- Whitespace-only strings are accepted unless `whitespace_only_is_missing: true`, which reports `whitespace_only`.
- Empty strings, whitespace-only strings, nulls, and absent keys have distinct issue categories and are not replaced or trimmed.

### Constraints

- `minimum` and `maximum` apply to `integer` and `float` values, inclusively.
- `min_length` and `max_length` apply to strings and count Unicode code points as Python string length.
- `allowed_values` requires an exact type and value match; a boolean is not treated as an integer value.
- Invalid constraint definitions raise `SchemaDefinitionError` before records are checked.

## Duplicate detection

Duplicate checks are disabled unless configured. `all_fields` compares complete record objects; `fields` compares the listed declared fields. Records with missing or null duplicate-key fields are skipped by key-based comparison so missing keys do not all collapse into one duplicate. Each later match produces a warning and points to the first record index. Duplicates are warnings by default because repeated observations can be legitimate. The validator never removes or changes records.

## Report

`ValidationReport` contains `dataset_id`, `schema_name`, `is_valid`, `total_records`, `valid_records`, `invalid_records`, `errors`, `warnings`, and UTC `validation_timestamp`. Each `ValidationIssue` contains a one-based `record_index` (or `None` for dataset-level issues), optional `field_name`, `category`, `severity`, `expected`, `actual_value`, and `message`.

`invalid_records` counts distinct records with at least one error. Dataset-level errors (such as a dataset ID mismatch or empty dataset) make `is_valid` false but do not increment that count. Duplicate warnings do not make the report invalid. Actual values are omitted by default to reduce accidental exposure of sensitive data; pass `include_actual_values=True` only when reports are handled appropriately.

## Validation layers and limits

- **File parsing:** the loader checks that CSV/JSON syntax and supported record shapes can be parsed.
- **Structural and basic data-quality validation:** this module checks declared fields, top-level types, missing values, simple constraints, and optional duplicates.
- **Scientific validation:** not implemented. Domain equations, physical plausibility, unit compatibility/conversion, coordinate/time semantics, and simulation correctness belong to the appropriate scientific module.

The validator does not infer schemas, coerce values, check date/time formats, recursively validate nested arrays/objects, use schema versions for migration, deduplicate, stream large datasets, or write results back to data or provenance. The generic sample schema includes no scientific bounds; it only describes the synthetic fixture structure.
