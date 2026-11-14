# ARC-08 Reusable Regression Evaluation

`evaluate_regression_model(prepared, *, training_source_row_indices, evaluation_source_row_indices, model, model_identifier)` evaluates a numeric regression model against an already prepared `PreparedRegressionDataset`. The row-index arguments are sequences of unique, non-negative built-in integers; each partition must be non-empty and they must not overlap. Callers provide the training and evaluation `source_row_index` values explicitly. The function does not generate or modify partitions.

The model follows the small `NumericRegressionModel` protocol:

```python
class Model:
    def fit(self, feature_rows, target_values): ...
    def predict(self, feature_rows): ...
```

Both inputs are immutable tuples. `fit` receives only the requested training
features and targets; `predict` receives only requested evaluation features.
The API does not fit preprocessing transformations or prevent a caller's model
from using external state; any learned preprocessing must be fitted using
training data only by the caller/model implementation.
The evaluator rejects empty, duplicate, unknown, excluded, or overlapping row
identities, and requires one finite numeric prediction for each evaluation
row. Result predictions preserve the requested evaluation order and link each
prediction to its source row and observed target.

The immutable result carries the declared `ResearchTask`, model identifier,
feature and target fields, target unit, schema ID/version, source provenance,
partition identities, predictions, metrics, and the explicit-partition
protocol description. The preparation contract has no experiment identifier,
so the result does not invent one. Task decision and provenance values are
descriptive metadata; this API does not authenticate approval or provenance.

MAE and RMSE are reported in the declared target unit when available. R² is
unitless and has an explicit `UNDEFINED` status and reason when there are fewer
than two evaluation rows or the observed evaluation targets are constant. No
performance threshold is applied.

All new evaluation tests use invented synthetic records. This API establishes
software behavior only; it does not establish scientific validity, acquisition
authorization, or model performance on NASA data. It does not address group
selection: the caller remains responsible for providing an approved split.
For the thin prepare-then-evaluate orchestration API, see
[`ARC08_END_TO_END_EVALUATION.md`](ARC08_END_TO_END_EVALUATION.md). NASA archive
field definitions and the current adapter's limits are in
[`ARC08_NASA_OPEN_DATA_REFERENCE.md`](ARC08_NASA_OPEN_DATA_REFERENCE.md).
