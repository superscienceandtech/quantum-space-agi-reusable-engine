from copy import deepcopy
from datetime import UTC, datetime

import pytest

from quantum_space_agi.data import DataFormat, Dataset, DataSource, Provenance
from quantum_space_agi.ml.dataset_validation import validate_baseline_dataset


def make_dataset(records: list[dict[str, object]]) -> Dataset:
    return Dataset(
        provenance=Provenance(
            dataset_id="synthetic-validation-fixture",
            source=DataSource("synthetic-fixture"),
            retrieved_at=datetime(2026, 11, 9, tzinfo=UTC),
            data_format=DataFormat.JSON,
        ),
        records=records,  # type: ignore[arg-type]
    )


def valid_record(**overrides: object) -> dict[str, object]:
    return {
        "pl_rade": 1.5,
        "pl_bmasse": 2,
        "pl_name": "Synthetic planet b",
        "hostname": "Synthetic star",
        "pl_refname": "Synthetic reference",
        **overrides,
    }


def test_accepts_positive_numeric_feature_target_and_identity_values() -> None:
    report = validate_baseline_dataset(make_dataset([valid_record()]))

    assert report.is_valid
    assert report.valid_record_indices == (0,)
    assert report.excluded_rows == ()
    assert report.record_count == 1


@pytest.mark.parametrize("field", ["pl_rade", "pl_bmasse"])
def test_reports_missing_and_null_numeric_values(field: str) -> None:
    absent = valid_record()
    del absent[field]
    explicit_null = valid_record(**{field: None})

    report = validate_baseline_dataset(make_dataset([absent, explicit_null]))

    assert [row.findings[0].reason_code for row in report.excluded_rows] == [
        "missing_field",
        "null_value",
    ]
    assert [row.findings[0].field for row in report.excluded_rows] == [field, field]


@pytest.mark.parametrize("value", ["1.2", True, {"value": 1}, [1]])
def test_reports_non_numeric_values_without_coercion(value: object) -> None:
    report = validate_baseline_dataset(make_dataset([valid_record(pl_rade=value)]))

    finding = report.excluded_rows[0].findings[0]
    assert finding.field == "pl_rade"
    assert finding.reason_code == "non_numeric"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_reports_non_finite_values_and_omits_non_json_numbers(value: float) -> None:
    report = validate_baseline_dataset(make_dataset([valid_record(pl_bmasse=value)]))

    finding = report.excluded_rows[0].findings[0]
    assert finding.reason_code == "non_finite"
    assert finding.original_value is None
    assert finding.value_omitted


@pytest.mark.parametrize("value", [0, 0.0, -1, -0.5])
def test_reports_zero_and_negative_numeric_values(value: int | float) -> None:
    report = validate_baseline_dataset(make_dataset([valid_record(pl_rade=value)]))

    finding = report.excluded_rows[0].findings[0]
    assert finding.reason_code == "non_positive"
    assert finding.original_value == value
    assert not finding.value_omitted


def test_reports_multiple_findings_and_missing_identity_metadata() -> None:
    row = valid_record(pl_rade=0, pl_bmasse="bad", hostname="  ")
    del row["pl_refname"]

    report = validate_baseline_dataset(make_dataset([row]))

    excluded = report.excluded_rows[0]
    assert excluded.row_index == 0
    assert [(finding.field, finding.reason_code) for finding in excluded.findings] == [
        ("pl_bmasse", "non_numeric"),
        ("pl_rade", "non_positive"),
        ("hostname", "missing_identity"),
        ("pl_refname", "missing_identity"),
    ]


def test_row_indices_trace_to_original_input_order() -> None:
    rows = [valid_record(), valid_record(pl_bmasse=None), valid_record()]
    report = validate_baseline_dataset(make_dataset(rows))

    assert report.valid_record_indices == (0, 2)
    assert report.excluded_rows[0].row_index == 1
    assert report.excluded_row_count == 1


def test_validation_does_not_mutate_caller_owned_records() -> None:
    rows = [valid_record(pl_rade="bad", nested={"items": [1, 2]})]
    original = deepcopy(rows)

    validate_baseline_dataset(make_dataset(rows))

    assert rows == original


def test_validation_results_are_deterministic() -> None:
    dataset = make_dataset(
        [valid_record(pl_rade=float("nan")), valid_record(pl_bmasse=0)]
    )

    first = validate_baseline_dataset(dataset)
    second = validate_baseline_dataset(dataset)

    assert first == second


def test_omits_large_or_non_scalar_original_values() -> None:
    report = validate_baseline_dataset(
        make_dataset([valid_record(pl_rade={"large": "x" * 1000})])
    )

    finding = report.excluded_rows[0].findings[0]
    assert finding.reason_code == "non_numeric"
    assert finding.original_value is None
    assert finding.value_omitted
