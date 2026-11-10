# ARC-08 Task-Driven Data Preparation

`prepare_regression_dataset(dataset, task, schema, *, source_row_indices=None)` turns an ARC-03 `Dataset` into aligned numeric
feature/target rows using an explicit `ResearchTask` and `DataSchema`. It is a
mechanical preparation boundary for scalar numeric regression; it does not
approve a task, apply scientific eligibility rules, impute, normalize,
deduplicate, or change source values.

The task's `features` declaration selects one or more feature fields, and its
`target` declaration selects the target field. Every declared field must exist
in the supplied schema and declare `int` or `float`. At the row boundary either
value must have the exact built-in type declared for that field; the API does
not coerce values. `ResearchTask.objective` supplies the human-readable task name/objective;
preparation does not invent a stable task identifier. The task declaration's
decision state is preserved as caller metadata;
the preparation API does not authenticate or infer approval.
The source `Provenance` object and schema identifier/version are retained in the
result.

Each accepted record contains the declared feature values in declaration order,
the target value, and a `source_row_index`. By default this index is the
zero-based position in `Dataset.records`; callers may supply
`source_row_indices` to retain an upstream row mapping. The accepted rows and
the reused `ExcludedRow` ledger account for every input row exactly once.
The optional mapping must be a sequence containing one unique, non-negative
built-in integer per input record; `bool` is rejected. Accepted and excluded
indices preserve input order. This is source-row traceability, not a planet
identity or grouping rule.

Missing fields, nulls, non-numeric values (including booleans), and non-finite
floats become deterministic row-level findings. Finite built-in integers and
floats are preserved exactly, including zero and negative values; this layer
does not set physical or scientific bounds. Structural errors such as an
unknown schema field, incomplete task, invalid row mapping, or empty dataset
raise `DatasetPreparationError`. A non-empty dataset with no accepted rows
returns an empty accepted tuple and its full exclusion ledger.

```python
prepared = prepare_regression_dataset(dataset, research_task, data_schema)

for row in prepared.accepted_records:
    print(row.source_row_index, row.feature_values, row.target_value)
```

All examples and tests for this interface use synthetic records. The existing
synthetic baseline remains a separate fixed-purpose smoke test and is not yet
adapted to consume this result. This interface creates no splits, predictions,
metrics, or scientific evidence.

For the later explicit-partition evaluation contract, see
[`ARC08_MODEL_EVALUATION.md`](ARC08_MODEL_EVALUATION.md). NASA table semantics
and adapter limits are summarized separately in
[`ARC08_NASA_OPEN_DATA_REFERENCE.md`](ARC08_NASA_OPEN_DATA_REFERENCE.md).
