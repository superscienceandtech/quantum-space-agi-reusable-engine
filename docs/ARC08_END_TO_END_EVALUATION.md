# ARC-08 Offline Regression Workflow

`prepare_and_evaluate_regression(dataset, task, schema, *, training_source_row_indices, evaluation_source_row_indices, model, model_identifier, source_row_indices=None)` connects an existing ARC-03 `Dataset` to
the ARC-08 preparation and explicit-partition evaluation APIs. It accepts a
caller-declared `ResearchTask`, `DataSchema`, source-row mapping, training and
evaluation source-row identities, a model, and a model identifier.

The function calls `prepare_regression_dataset()` and then
`evaluate_regression_model()`. It does not read files, make network requests,
create partitions, or change records. Preparation and evaluation errors are
propagated with their original types and error codes.

The immutable `RegressionWorkflowResult` exposes both the prepared dataset and
the evaluation result. It checks that task, fields, schema, and provenance agree
between them; that partitions refer to accepted prepared rows; and that each
observed evaluation target matches its original prepared source row. Accepted
records and the preparation exclusion ledger remain available on the result.
The evaluation result keeps each prediction aligned with its explicit source
row identity.

The workflow is deterministic only to the extent that the supplied dataset,
task, schema, row identities, model implementation/state, and environment are
the same. It does not create a seed, split, or experiment manifest. A successful
workflow result is a software evaluation record, not evidence that the
partitions are scientifically appropriate or leakage-independent.

```python
workflow = prepare_and_evaluate_regression(
    dataset,
    task,
    schema,
    source_row_indices=original_row_indices,
    training_source_row_indices=train_ids,
    evaluation_source_row_indices=test_ids,
    model=model,
    model_identifier="model-name/version",
)
```

All integration tests use invented synthetic records. Mechanical acceptance
does not imply scientific eligibility; task decisions and provenance are not
authenticated. No scientific filters, imputation, thresholds, split policy,
or approval are introduced here. The existing acquisition readiness gate and
scientific acceptance decisions are unchanged.

See [`ARC08_TASK_DATA_PREPARATION.md`](ARC08_TASK_DATA_PREPARATION.md) for
mechanical row acceptance and [`ARC08_MODEL_EVALUATION.md`](ARC08_MODEL_EVALUATION.md)
for partition and metric semantics. NASA archive field definitions and adapter
limitations are summarized in
[`ARC08_NASA_OPEN_DATA_REFERENCE.md`](ARC08_NASA_OPEN_DATA_REFERENCE.md).
