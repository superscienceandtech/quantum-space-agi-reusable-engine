"""Deterministic synthetic-only regression smoke test for ARC-08 engineering.

This module never acquires data. Its seeded random-row split is deliberately
limited to the built-in synthetic fixture and is not a scientific split policy.
"""

from __future__ import annotations

import hashlib
import json
import math
import platform
import random
import sys
from dataclasses import dataclass
from statistics import median
from typing import TypeAlias, cast

from quantum_space_agi.ml.dataset_validation import (
    DatasetValidationReport,
    validate_baseline_records,
)
from quantum_space_agi.ml.experiment_manifest import (
    POLICY_IDS,
    ArtifactReference,
    DatasetDeclaration,
    DecisionDeclaration,
    DecisionStatus,
    ExecutionEnvironment,
    ExperimentConfiguration,
    ExperimentLifecycle,
    IdentityAndSplit,
    ModelEvaluation,
    NamedSeed,
    OutputArtifact,
    PolicyDeclaration,
    ResearchTask,
    VariableDeclaration,
    create_experiment_manifest,
    experiment_configuration_sha256,
    serialize_experiment_configuration,
    serialize_experiment_manifest,
)

SYNTHETIC_BASELINE_SCHEMA_VERSION = "arc08-synthetic-baseline-result/1"
SYNTHETIC_FIXTURE_ID = "arc08-synthetic-mass-radius-fixture/1"
DEFAULT_RANDOM_SEED = 1729
DEFAULT_TEST_FRACTION = 0.25
FEATURE_FIELD = "pl_rade"
TARGET_FIELD = "pl_bmasse"
_RESULT_ARTIFACT_PATH = "synthetic-output/arc08-synthetic-baseline-result.json"
_CONFIGURATION_ARTIFACT_PATH = "synthetic-output/arc08-experiment-configuration.json"
_MANIFEST_ARTIFACT_PATH = "synthetic-output/arc08-experiment-manifest.json"

SyntheticRecord: TypeAlias = dict[str, str | int | float | None]
FeatureInput: TypeAlias = tuple[int | float, ...] | tuple[tuple[int | float, ...], ...]


class SyntheticBaselineError(ValueError):
    """Invalid synthetic pipeline input or an unusable synthetic split."""


@dataclass(frozen=True, slots=True)
class SyntheticPrediction:
    """One held-out synthetic prediction linked to its fixture row."""

    row_id: str
    feature_value: float
    observed_target: float
    predicted_target: float


@dataclass(frozen=True, slots=True)
class SyntheticMetrics:
    """Metrics for held-out synthetic rows; R-squared may be undefined."""

    mae: float
    rmse: float
    r2: float | None
    r2_status: str


@dataclass(frozen=True, slots=True)
class SyntheticBaselineResult:
    """Immutable report and manifest linkage for a synthetic smoke test."""

    result_bytes: bytes
    configuration_bytes: bytes
    manifest_bytes: bytes
    configuration_sha256: str
    manifest_sha256: str
    validation_report: DatasetValidationReport
    train_row_ids: tuple[str, ...]
    test_row_ids: tuple[str, ...]
    predictions: tuple[SyntheticPrediction, ...]
    metrics: SyntheticMetrics


class MedianDummyRegressor:
    """Small standard-library implementation of median DummyRegressor behavior.

    Scikit-learn is not declared as a project dependency and is not installed in
    the inspected project environment. This implementation stores only the
    median of the explicitly supplied training targets and predicts that value.
    """

    def __init__(self) -> None:
        self._constant: float | None = None

    def fit(
        self, feature_values: FeatureInput, target_values: tuple[int | float, ...]
    ) -> MedianDummyRegressor:
        """Fit the training-target median; feature values are validated, unused."""
        _validate_feature_input(feature_values)
        if len(feature_values) != len(target_values) or not target_values:
            raise SyntheticBaselineError("training feature/target lengths must match")
        if any(
            type(value) not in (int, float) or not math.isfinite(value)
            for value in target_values
        ):
            raise SyntheticBaselineError("training values must be finite numbers")
        self._constant = float(median(target_values))
        return self

    @property
    def constant(self) -> float:
        """Return the fitted training median."""
        if self._constant is None:
            raise SyntheticBaselineError("model has not been fitted")
        return self._constant

    def predict(self, feature_values: FeatureInput) -> tuple[float, ...]:
        """Predict the fitted training median for each supplied feature value."""
        if self._constant is None:
            raise SyntheticBaselineError("model has not been fitted")
        _validate_feature_input(feature_values)
        return (self._constant,) * len(feature_values)


def create_synthetic_regression_fixture() -> tuple[SyntheticRecord, ...]:
    """Return twelve stable synthetic rows, including two validator cases.

    Values are invented solely for software tests and carry no archive evidence.
    The two final rows exercise null-feature and non-finite-target handling.
    """
    values = (
        (0.8, 1.1),
        (1.0, 1.7),
        (1.2, 2.4),
        (1.5, 3.2),
        (1.8, 4.0),
        (2.1, 5.1),
        (2.4, 6.0),
        (2.8, 7.4),
        (3.2, 8.8),
        (3.6, 10.5),
        (4.0, 12.0),
        (4.5, 13.8),
    )
    records: list[SyntheticRecord] = [
        _synthetic_record(index, feature, target)
        for index, (feature, target) in enumerate(values)
    ]
    records.extend(
        (
            _synthetic_record(12, None, 15.0),
            _synthetic_record(13, 5.0, float("nan")),
        )
    )
    return tuple(records)


def run_synthetic_baseline(
    *,
    seed: int = DEFAULT_RANDOM_SEED,
    test_fraction: float = DEFAULT_TEST_FRACTION,
    experiment_id: str = "arc08-synthetic-mass-radius-smoke-test-v1",
) -> SyntheticBaselineResult:
    """Validate, split, fit, evaluate, and serialize the synthetic fixture only.

    The split is a deterministic seeded random-row software test. It does not
    implement or imply host/reference/component independence or approval.
    """
    if type(seed) is not int or seed < 0:
        raise SyntheticBaselineError("seed must be a non-negative integer")
    if type(experiment_id) is not str or not experiment_id.strip():
        raise SyntheticBaselineError("experiment_id must be non-empty text")
    if (
        type(test_fraction) is not float
        or not math.isfinite(test_fraction)
        or not 0.0 < test_fraction < 1.0
    ):
        raise SyntheticBaselineError("test_fraction must be between zero and one")

    records = create_synthetic_regression_fixture()
    validation_report = validate_baseline_records(records)
    accepted_indices = list(validation_report.valid_record_indices)
    if len(accepted_indices) < 2:
        raise SyntheticBaselineError("at least two mechanically accepted rows required")

    shuffled_indices = accepted_indices.copy()
    random.Random(seed).shuffle(shuffled_indices)
    test_count = max(
        1, min(len(shuffled_indices) - 1, int(len(shuffled_indices) * test_fraction))
    )
    test_indices = tuple(shuffled_indices[:test_count])
    train_indices = tuple(shuffled_indices[test_count:])
    effective_test_fraction = test_count / len(shuffled_indices)

    train_records = tuple(records[index] for index in train_indices)
    test_records = tuple(records[index] for index in test_indices)
    train_features = tuple(_number(record[FEATURE_FIELD]) for record in train_records)
    train_targets = tuple(_number(record[TARGET_FIELD]) for record in train_records)
    test_features = tuple(_number(record[FEATURE_FIELD]) for record in test_records)
    test_targets = tuple(_number(record[TARGET_FIELD]) for record in test_records)

    model = MedianDummyRegressor().fit(train_features, train_targets)
    predictions = model.predict(test_features)
    prediction_records = tuple(
        SyntheticPrediction(
            row_id=_row_id(record),
            feature_value=feature,
            observed_target=target,
            predicted_target=prediction,
        )
        for record, feature, target, prediction in zip(
            test_records, test_features, test_targets, predictions, strict=True
        )
    )
    metrics = _calculate_metrics(test_targets, predictions)
    configuration = _build_configuration(
        seed=seed,
        test_fraction=effective_test_fraction,
        experiment_id=experiment_id,
    )
    manifest = create_experiment_manifest(configuration, _CONFIGURATION_ARTIFACT_PATH)
    configuration_bytes = serialize_experiment_configuration(configuration)
    manifest_bytes = serialize_experiment_manifest(manifest, configuration)
    configuration_sha256 = experiment_configuration_sha256(configuration)
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    result_bytes = _serialize_result(
        seed=seed,
        requested_test_fraction=test_fraction,
        effective_test_fraction=effective_test_fraction,
        validation_report=validation_report,
        records=records,
        train_indices=train_indices,
        test_indices=test_indices,
        train_targets=train_targets,
        model=model,
        predictions=prediction_records,
        metrics=metrics,
        configuration_sha256=configuration_sha256,
        manifest_sha256=manifest_sha256,
        experiment_id=experiment_id,
    )
    return SyntheticBaselineResult(
        result_bytes=result_bytes,
        configuration_bytes=configuration_bytes,
        manifest_bytes=manifest_bytes,
        configuration_sha256=configuration_sha256,
        manifest_sha256=manifest_sha256,
        validation_report=validation_report,
        train_row_ids=tuple(_row_id(records[index]) for index in train_indices),
        test_row_ids=tuple(_row_id(records[index]) for index in test_indices),
        predictions=prediction_records,
        metrics=metrics,
    )


def _synthetic_record(
    index: int, feature: float | None, target: float
) -> SyntheticRecord:
    return {
        "synthetic_row_id": f"synthetic-row-{index:03d}",
        FEATURE_FIELD: feature,
        TARGET_FIELD: target,
        "pl_name": f"SYNTHETIC-ONLY planet {index:03d}",
        "hostname": f"SYNTHETIC-ONLY host {index % 4:02d}",
        "pl_refname": f"SYNTHETIC-ONLY reference {index % 3:02d}",
        "synthetic_fixture_id": SYNTHETIC_FIXTURE_ID,
    }


def _row_id(record: SyntheticRecord) -> str:
    value = record.get("synthetic_row_id")
    if type(value) is not str:
        raise SyntheticBaselineError("synthetic fixture row identifier is invalid")
    return value


def _number(value: object) -> float:
    if type(value) not in (int, float):
        raise SyntheticBaselineError("validated synthetic numeric value is invalid")
    numeric_value = cast(int | float, value)
    if not math.isfinite(numeric_value):
        raise SyntheticBaselineError("validated synthetic numeric value is invalid")
    return float(numeric_value)


def _calculate_metrics(
    observed: tuple[float, ...], predicted: tuple[float, ...]
) -> SyntheticMetrics:
    if not observed or len(observed) != len(predicted):
        raise SyntheticBaselineError("metric inputs must be non-empty and aligned")
    if any(not math.isfinite(value) for value in (*observed, *predicted)):
        raise SyntheticBaselineError("metric inputs must be finite numbers")
    errors = tuple(
        actual - estimate for actual, estimate in zip(observed, predicted, strict=True)
    )
    mae = sum(abs(error) for error in errors) / len(errors)
    rmse = math.sqrt(sum(error * error for error in errors) / len(errors))
    r2: float | None
    if len(observed) < 2:
        r2 = None
        r2_status = "undefined: fewer than two test rows"
    else:
        mean_observed = sum(observed) / len(observed)
        total_sum_squares = sum((value - mean_observed) ** 2 for value in observed)
        if total_sum_squares == 0.0:
            r2 = None
            r2_status = "undefined: constant test targets"
        else:
            r2 = 1.0 - sum(error * error for error in errors) / total_sum_squares
            r2_status = "defined"
    return SyntheticMetrics(
        mae,
        rmse,
        r2,
        r2_status,
    )


def _validate_feature_input(feature_values: FeatureInput) -> int:
    if type(feature_values) is not tuple:
        raise SyntheticBaselineError("feature values must be an immutable tuple")
    if not feature_values:
        return 0
    rows: tuple[tuple[int | float, ...], ...]
    if all(type(value) in (int, float) for value in feature_values):
        rows = tuple((cast(int | float, value),) for value in feature_values)
    else:
        if any(type(row) is not tuple or not row for row in feature_values):
            raise SyntheticBaselineError("feature rows must be non-empty tuples")
        rows = cast(tuple[tuple[int | float, ...], ...], feature_values)
        if any(len(row) != len(rows[0]) for row in rows):
            raise SyntheticBaselineError("feature rows must have equal widths")
    if any(
        type(value) not in (int, float) or not math.isfinite(value)
        for row in rows
        for value in row
    ):
        raise SyntheticBaselineError("feature values must be finite numbers")
    return len(rows)


def _build_configuration(
    *, seed: int, test_fraction: float, experiment_id: str
) -> ExperimentConfiguration:
    pending = DecisionDeclaration(
        DecisionStatus.PENDING_REVIEW,
        rationale="Synthetic software exercise; scientific decision remains pending.",
    )
    policies = tuple(
        PolicyDeclaration(policy_id, None, pending) for policy_id in POLICY_IDS
    )
    return ExperimentConfiguration(
        experiment_id=experiment_id,
        schema_version="arc08-experiment-configuration/1",
        description=(
            "Synthetic-only engineering baseline; no NASA records or scientific "
            "acceptance."
        ),
        experiment_type="synthetic_regression_smoke_test",
        lifecycle=ExperimentLifecycle.EXECUTED,
        created_at=None,
        research_task=ResearchTask(
            objective="Predict a synthetic target from a synthetic scalar feature.",
            target=VariableDeclaration(
                TARGET_FIELD, "Earth masses (synthetic convention)"
            ),
            features=(
                VariableDeclaration(
                    FEATURE_FIELD, "Earth radii (synthetic convention)"
                ),
            ),
            inference_description=(
                "Held-out rows from the built-in synthetic fixture only."
            ),
            decision=pending,
        ),
        dataset=DatasetDeclaration(
            source_identity="ARC-08 synthetic fixture generator",
            source_table=SYNTHETIC_FIXTURE_ID,
            query_artifact=None,
            raw_snapshot_artifact=None,
            schema_artifact=None,
            extraction_metadata_artifact=None,
            dataset_version=SYNTHETIC_FIXTURE_ID,
        ),
        policies=policies,
        identity_and_split=IdentityAndSplit(
            identity_fields=("synthetic_row_id",),
            duplicate_policy=None,
            grouping_objective="Synthetic software split only; no independence claim.",
            grouping_fields=(),
            split_strategy="seeded random row split (synthetic fixture only)",
            train_fraction=1.0 - test_fraction,
            validation_fraction=0.0,
            test_fraction=test_fraction,
            seed=seed,
            ordering_strategy=(
                "Python random.Random seeded shuffle of accepted row indices"
            ),
            leakage_constraints=(),
            decision=pending,
        ),
        model_evaluation=ModelEvaluation(
            baseline_model_identifier=(
                "median_dummy_regressor (standard-library implementation)"
            ),
            optional_model_identifiers=(),
            preprocessing="none",
            primary_metric="MAE in synthetic target units",
            secondary_metrics=("RMSE in synthetic target units", "R2 diagnostic"),
            evaluation_protocol=(
                "Training-only median fit; held-out synthetic rows only."
            ),
            acceptance_criteria_reference=None,
            decision=pending,
        ),
        environment=ExecutionEnvironment(
            python_version=platform.python_version(),
            lockfile_reference=None,
            lockfile_sha256=None,
            platform=sys.platform,
            repository_commit=None,
            branch=None,
            random_seeds=(NamedSeed("synthetic_split", seed),),
            execution_command=None,
            entry_point=ArtifactReference(
                "src/quantum_space_agi/ml/synthetic_baseline.py"
            ),
        ),
        output_artifacts=(
            OutputArtifact(
                "synthetic_baseline_result", ArtifactReference(_RESULT_ARTIFACT_PATH)
            ),
        ),
    )


def _serialize_result(
    *,
    seed: int,
    requested_test_fraction: float,
    effective_test_fraction: float,
    validation_report: DatasetValidationReport,
    records: tuple[SyntheticRecord, ...],
    train_indices: tuple[int, ...],
    test_indices: tuple[int, ...],
    train_targets: tuple[float, ...],
    model: MedianDummyRegressor,
    predictions: tuple[SyntheticPrediction, ...],
    metrics: SyntheticMetrics,
    configuration_sha256: str,
    manifest_sha256: str,
    experiment_id: str,
) -> bytes:
    excluded = [
        {
            "source_row_index": row.row_index,
            "row_id": _row_id(records[row.row_index]),
            "findings": [
                {
                    "field": finding.field,
                    "reason_code": finding.reason_code,
                    "original_value": finding.original_value,
                    "value_omitted": finding.value_omitted,
                }
                for finding in row.findings
            ],
        }
        for row in validation_report.excluded_rows
    ]
    document: dict[str, object] = {
        "schema_version": SYNTHETIC_BASELINE_SCHEMA_VERSION,
        "evidence_classification": "synthetic software evidence only",
        "scientific_acceptance": "PENDING_REVIEW",
        "limitations": [
            "No NASA or external archive data were accessed.",
            "Mechanical acceptance is not scientific eligibility.",
            "Random row splitting does not establish host/reference independence.",
            "Metrics describe invented fixture values only.",
        ],
        "experiment": {
            "experiment_id": experiment_id,
            "fixture_id": SYNTHETIC_FIXTURE_ID,
            "feature": {
                "field": FEATURE_FIELD,
                "unit": "Earth radii (synthetic convention)",
            },
            "target": {
                "field": TARGET_FIELD,
                "unit": "Earth masses (synthetic convention)",
            },
            "seed": seed,
            "split": {
                "strategy": "seeded random row split (synthetic fixture only)",
                "requested_test_fraction": requested_test_fraction,
                "effective_test_fraction": effective_test_fraction,
                "train_row_ids": [_row_id(records[index]) for index in train_indices],
                "test_row_ids": [_row_id(records[index]) for index in test_indices],
            },
            "model": {
                "name": "median_dummy_regressor",
                "implementation": "standard-library median; no scikit-learn dependency",
                "configuration": {"strategy": "median", "fitted_value": model.constant},
                "training_targets": list(train_targets),
            },
        },
        "validation": {
            "policy_version": validation_report.policy_version,
            "input_row_count": validation_report.record_count,
            "mechanically_accepted_source_row_indices": list(
                validation_report.valid_record_indices
            ),
            "excluded_row_count": validation_report.excluded_row_count,
            "exclusion_ledger": excluded,
        },
        "predictions": [
            {
                "row_id": prediction.row_id,
                "feature_value": prediction.feature_value,
                "observed_target": prediction.observed_target,
                "predicted_target": prediction.predicted_target,
            }
            for prediction in predictions
        ],
        "metrics": {
            "primary": {
                "name": "MAE",
                "value": metrics.mae,
                "unit": "synthetic target units",
            },
            "diagnostics": {
                "RMSE": {"value": metrics.rmse, "unit": "synthetic target units"},
                "R2": {"value": metrics.r2, "status": metrics.r2_status},
            },
            "threshold": None,
        },
        "manifest_linkage": {
            "configuration_artifact": _CONFIGURATION_ARTIFACT_PATH,
            "configuration_sha256": configuration_sha256,
            "manifest_artifact": _MANIFEST_ARTIFACT_PATH,
            "manifest_sha256": manifest_sha256,
            "manifest_schema_version": "arc08-experiment-manifest/1",
            "artifact_references_are_declarative_only": True,
        },
    }
    try:
        return json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, OverflowError) as exc:
        raise SyntheticBaselineError("synthetic result cannot be serialized") from exc
