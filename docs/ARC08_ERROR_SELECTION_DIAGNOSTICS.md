# ARC-08 Synthetic Error and Selection Diagnostics

**Status:** Offline engineering diagnostics for synthetic fixtures only. This
document does not approve the proposed mass-radius task, eligibility policy,
cohort, or acquisition. Scientific review remains pending and acquisition
readiness remains `NOT_READY`.

## Scope and API

`quantum_space_agi.ml.error_selection_diagnostics` consumes caller-supplied
rows, an existing `DatasetValidationReport`, test row identifiers, and
already-produced `SyntheticPrediction` values. It does not fit a model, create
predictions, change the validation ledger, select a scientific cohort, or make
network or filesystem requests. The separate synthetic diagnostic fixture adds
invented categories, host labels, uncertainty-like values, and a deliberately
inconsistent value-bound pair for software tests.

`diagnose_error_selection()` returns frozen result records and
`serialize_error_selection_diagnostics()` emits deterministic compact UTF-8
JSON with sorted object keys and schema version
`arc08-error-selection-diagnostics/1`. A supplied
`ExperimentManifestLinkage` records caller-declared links only; the serializer
does not authenticate manifests or artifacts.

## Residuals and error summaries

Residuals are defined as:

```text
residual = observed_target - predicted_target
```

Each output residual record retains its source row ID, observed target,
prediction, signed residual, absolute error, and squared error. Test IDs must be
unique and refer to mechanically accepted rows. Predictions must cover exactly
the requested test IDs and their feature and observed-target values must match
the identified source rows. Non-numeric, boolean, non-finite, overflowing, or
misaligned prediction values are rejected; they are not silently dropped.

For non-empty samples, summaries include mean absolute error (MAE), root mean
squared error (RMSE), mean and median signed residual, median absolute error,
minimum and maximum residual, and residual quantiles at 0.05, 0.25, 0.50, 0.75,
and 0.95. Quantiles use linear interpolation at position `(n - 1) * p` over
the sorted values. RMSE is the square root of the mean squared residual. An
empty sample has an explicit `UNDEFINED_EMPTY_SAMPLE` status and null metrics;
a one-row sample has `DEFINED_SINGLE_ROW`. No minimum sample size or
performance threshold is imposed.

## Optional error slices

Callers may request grouping by explicit metadata field names. Group values are
kept exact and are not trimmed, merged, normalized, or inferred. Missing and
unsupported values are reported separately. Group MAE, RMSE, and mean signed
residual are descriptive summaries only. The implementation does not impose an
arbitrary minimum group size; small groups must not be interpreted as reliable
scientific estimates.

## Uncertainty-like metadata

Uncertainty fields are opt-in declarations. Lower and upper uncertainty-like
values remain separate, signed/scalar values are retained as supplied, and
coverage, missing values, invalid numeric values, and unsupported metadata
types are reported. Declared lower/upper *value bounds* are compared only when
the caller explicitly supplies matching pair identifiers; lower greater than
upper is flagged without repair. This mechanical comparison does not establish
the meaning of any field.

These diagnostics do not convert asymmetric values to symmetric errors, treat
them as calibrated confidence intervals, estimate statistical uncertainty, or
use them as model features, weights, or eligibility filters. No NASA limit-code
semantics are inferred.

## Selection and exclusion diagnostics

The report reuses the supplied validation report and its source-position
exclusion ledger. It summarizes input, mechanically accepted, and excluded
counts; counts findings by reason and field/reason; reports feature/target
coverage before and after mechanical validation; reports identity-field
coverage through existing identity diagnostics; and compares finite feature
values in accepted and excluded rows where available. Missing or non-finite
values are not imputed.

Mechanical acceptance means only that the existing operational checks passed.
It is not scientific eligibility, an approved cohort, or a sampling frame.
Differences between the included and excluded synthetic fixture rows are not a
quantification of real archive selection bias. Cohort-selection and scientific
eligibility states are explicitly not assessed.

## Interpretation limits

All included example values and output are synthetic software-test material.
They do not establish real ARC-08 model performance, archive representativeness,
scientific validity, or selection bias. The output does not approve any
scientific policy and does not change the acquisition gate. No NASA access,
data acquisition, model fitting, prediction generation, or scientific
evaluation is performed by this module.
