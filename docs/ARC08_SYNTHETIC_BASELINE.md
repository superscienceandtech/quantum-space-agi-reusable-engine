# ARC-08 Synthetic Baseline Engineering Smoke Test

**Status:** Synthetic software exercise only. This is not a scientifically
approved task, NASA dataset, scientific result, or evidence of operational
prediction capability. Scientific decisions and acquisition readiness remain
pending; the acquisition gate remains `NOT_READY`.

## Purpose and data flow

`quantum_space_agi.ml.synthetic_baseline` exercises the existing mechanical
validation and experiment configuration/manifest APIs without network or
filesystem access. `create_synthetic_regression_fixture()` returns 12 invented
rows with stable `synthetic_row_id` values. Twelve rows contain positive
numeric feature/target values; one has a null feature and one a non-finite
target so the existing validator's exclusion reporting is exercised.

`run_synthetic_baseline()` applies the existing `validate_baseline_records()`
contract to `pl_rade`, `pl_bmasse`, and required identity strings. That
validator mechanically accepts only finite positive numbers and non-empty
identities. The two excluded rows and their source positions/reasons are
preserved in the output ledger. This engineering behavior does not finalize
scientific eligibility, and the fixture is not scientific evidence.

The twelve mechanically accepted fixture rows are shuffled with
`random.Random(seed)` and split 75/25 by row. The default seed is `1729`; the
default requested and realized test fraction is `0.25`. For other row counts,
the result records both requested and realized fractions after integer
allocation. The assignment is deterministic for the
same Python random implementation, seed, and fixture order. It is only a
software test split. It does not implement host-disjoint, reference-disjoint,
or connected-component evaluation and says nothing about independence.

The model is a small standard-library implementation of median
`DummyRegressor` behavior: it fits the median of training targets only and
returns that constant for held-out feature rows. Scikit-learn is not declared
in the repository's dependencies and is unavailable in the inspected project
environment, so no dependency was added. The implementation does not use the
feature to fit or predict. No Ridge or other comparison model is included.

MAE is the primary engineering metric. RMSE and R² are diagnostics. R² is
serialized as JSON `null` with an explicit reason when it is undefined because
there are fewer than two held-out rows or the held-out targets are constant.
No threshold is used. Units in the report (“Earth radii” and “Earth masses”)
are fixture conventions, not observed archive units or measurements.

## Reproducibility and manifest linkage

The result serializer emits compact, sorted-key UTF-8 JSON with no timestamp.
The output contains the seed, fixture and validation versions, train/test row
IDs, row-aligned predictions, metrics, exclusion ledger, model identity,
configuration hash, manifest hash, and output references. The experiment
configuration and manifest are created and serialized with the existing
`experiment_manifest` APIs. Task, policy, split, and model/evaluation
decisions remain `PENDING_REVIEW`; the manifest records declarations but does
not authenticate approval, verify artifact existence, or prove source
authenticity. The manifest records the available Python and platform values;
it does not capture a dependency lockfile or the exact command used by an
interactive caller.

The API returns bytes and does not write files. The declared result and
manifest locations are under `synthetic-output/`; they are portable references
only, not files created by this module. A caller choosing to persist them must
use a new synthetic-only location and avoid overwriting existing artifacts.

## Limitations

- No NASA, network, or external data access occurs.
- Synthetic values and metrics are not scientific findings or performance
  estimates.
- Mechanical validation is not scientific eligibility or acceptance.
- Random row splitting is not the proposed host-based scientific evaluation
  and makes no leakage-independence claim.
- The standard-library median model mirrors the relevant median constant
  behavior but is not scikit-learn's implementation.
- No extraction, cohort freezing, approval, or acquisition authorization is
  provided by this smoke test.
