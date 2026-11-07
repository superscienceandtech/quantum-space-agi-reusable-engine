from datetime import UTC, datetime

import pytest

from quantum_space_agi.data.models import Dataset
from quantum_space_agi.data.provenance import DataFormat, Provenance
from quantum_space_agi.data.schemas import (
    DataSchema,
    FieldSchema,
    validate_dataset,
)
from quantum_space_agi.data.sources import DataSource
from quantum_space_agi.errors import ValidationError


def make_dataset(records) -> Dataset:
    provenance = Provenance(
        dataset_id="dataset-a",
        source=DataSource("catalog"),
        retrieved_at=datetime(2026, 11, 6, tzinfo=UTC),
        data_format=DataFormat.JSON,
    )
    return Dataset(provenance, records)


def make_schema() -> DataSchema:
    return DataSchema(
        identifier="sample",
        version="2",
        fields=(
            FieldSchema("name", str),
            FieldSchema("count", int),
            FieldSchema("note", str, required=False, allow_none=True),
        ),
    )


def test_schema_reports_all_valid_rows_and_schema_version() -> None:
    report = validate_dataset(
        make_dataset([{"name": "a", "count": 1}, {"name": "b", "count": 2}]),
        make_schema(),
    )

    assert report.is_valid
    assert report.schema_id == "sample"
    assert report.schema_version == "2"
    assert report.record_count == 2
    assert report.valid_count == 2
    assert report.invalid_records == ()


def test_schema_reports_missing_required_fields_by_record_index() -> None:
    report = validate_dataset(
        make_dataset([{"name": "valid", "count": 1}, {"count": 2}]),
        make_schema(),
    )

    assert not report.is_valid
    assert report.valid_count == 1
    assert [invalid.record_index for invalid in report.invalid_records] == [1]
    assert report.invalid_records[0].issues[0].field == "name"
    assert report.invalid_records[0].issues[0].code == "missing"


def test_schema_reports_disallowed_none_and_wrong_types() -> None:
    report = validate_dataset(
        make_dataset([{"name": None, "count": "3", "note": None}]),
        make_schema(),
    )

    assert not report.is_valid
    assert [
        (issue.field, issue.code) for issue in report.invalid_records[0].issues
    ] == [
        ("name", "null"),
        ("count", "type"),
    ]


def test_schema_does_not_accept_boolean_as_integer() -> None:
    report = validate_dataset(
        make_dataset([{"name": "x", "count": True}]), make_schema()
    )

    assert report.invalid_records[0].issues[0].code == "type"


def test_schema_reports_multiple_issues_without_dropping_or_mutating_rows() -> None:
    original = {"count": "wrong"}
    dataset = make_dataset([original, {"name": "valid", "count": 2}])

    report = validate_dataset(dataset, make_schema())

    assert report.record_count == 2
    assert report.valid_count == 1
    assert [issue.field for issue in report.invalid_records[0].issues] == [
        "name",
        "count",
    ]
    assert dataset.records[0] == {"count": "wrong"}


def test_schema_allows_optional_and_nullable_field() -> None:
    report = validate_dataset(
        make_dataset([{"name": "x", "count": 0, "note": None}]),
        make_schema(),
    )

    assert report.is_valid


def test_schema_rejects_duplicate_field_names() -> None:
    with pytest.raises(ValidationError, match="unique"):
        DataSchema(
            "duplicate",
            "1",
            (FieldSchema("value", str), FieldSchema("value", int)),
        )


def test_schema_rejects_empty_identity_or_invalid_field_type() -> None:
    with pytest.raises(ValidationError, match="identifier"):
        DataSchema(" ", "1", ())
    with pytest.raises(ValidationError, match="value_type"):
        FieldSchema("value", "str")  # type: ignore[arg-type]
