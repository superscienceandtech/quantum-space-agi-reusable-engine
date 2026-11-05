import math
import sys
from datetime import UTC, datetime

import pytest

from quantum_space_agi.data.models import Dataset
from quantum_space_agi.data.provenance import DataFormat, Provenance
from quantum_space_agi.data.quality import analyze_quality
from quantum_space_agi.data.schemas import DataSchema, FieldSchema, validate_dataset
from quantum_space_agi.data.sources import DataSource


def make_dataset(records) -> Dataset:
    provenance = Provenance(
        dataset_id="dataset-a",
        source=DataSource("catalog"),
        retrieved_at=datetime(2026, 11, 6, tzinfo=UTC),
        data_format=DataFormat.JSON,
    )
    return Dataset(provenance, records)


def test_quality_report_summarizes_empty_dataset() -> None:
    report = analyze_quality(make_dataset([]))

    assert report.record_count == 0
    assert report.missing_values == {}
    assert report.duplicate_groups == ()
    assert report.invalid_records == ()
    assert report.field_statistics == {}


def test_quality_counts_absent_null_and_blank_values_as_missing() -> None:
    report = analyze_quality(
        make_dataset(
            [
                {"name": "a", "note": ""},
                {"name": " ", "note": None},
                {"name": "c"},
            ]
        )
    )

    assert report.missing_values == {"name": 1, "note": 3}


def test_quality_detects_exact_duplicates_independent_of_key_order() -> None:
    report = analyze_quality(
        make_dataset(
            [
                {"a": 1, "b": "x"},
                {"b": "x", "a": 1},
                {"a": 1, "b": "y"},
                {"a": 1, "b": "x"},
            ]
        )
    )

    assert len(report.duplicate_groups) == 1
    assert report.duplicate_groups[0].record_indices == (0, 1, 3)


def test_quality_includes_invalid_schema_record_indices() -> None:
    dataset = make_dataset([{"value": "bad"}, {"value": 2}])
    schema = DataSchema("values", "1", (FieldSchema("value", int),))
    validation = validate_dataset(dataset, schema)

    report = analyze_quality(dataset, validation_report=validation)

    assert report.invalid_records == (0,)


def test_quality_calculates_finite_numeric_statistics_and_excludes_booleans() -> None:
    report = analyze_quality(
        make_dataset(
            [
                {"value": 1, "flag": True},
                {"value": 2.5, "flag": False},
                {"value": math.inf, "flag": True},
                {"value": math.nan, "flag": False},
                {"value": "3", "flag": True},
            ]
        )
    )

    assert report.field_statistics["value"].count == 2
    assert report.field_statistics["value"].minimum == 1.0
    assert report.field_statistics["value"].maximum == 2.5
    assert report.field_statistics["value"].mean == 1.75
    assert "flag" not in report.field_statistics


@pytest.mark.parametrize(
    ("values", "expected_mean"),
    [
        ([1e308, 1e308], 1e308),
        ([-1e308, -1e308], -1e308),
        ([sys.float_info.max] * 3, sys.float_info.max),
        ([1e308, -1e308, 3.0], 1.0),
        ([1e16, -1e16, 3.0], 1.0),
    ],
)
def test_quality_mean_handles_large_and_mixed_magnitude_values(
    values: list[float], expected_mean: float
) -> None:
    report = analyze_quality(make_dataset([{"value": value} for value in values]))

    mean = report.field_statistics["value"].mean
    assert math.isfinite(mean)
    assert mean == expected_mean


def test_quality_does_not_mutate_source_records() -> None:
    dataset = make_dataset([{"value": 1}, {"value": 1}])
    original = tuple(dict(record) for record in dataset.records)

    analyze_quality(dataset)

    assert tuple(dict(record) for record in dataset.records) == original


def test_quality_analysis_does_not_mutate_nested_values() -> None:
    nested = {"items": [1, {"value": 2}]}
    dataset = make_dataset([{"nested": nested}])
    original = {"items": [1, {"value": 2}]}

    analyze_quality(dataset)

    assert dataset.records[0]["nested"] == original
