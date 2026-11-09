from __future__ import annotations

import copy
from datetime import UTC, datetime

import pytest

from quantum_space_agi.data import DataFormat, Dataset, DataSource, Provenance
from quantum_space_agi.ml import (
    FieldConversion,
    PreprocessingError,
    preprocess_dataset,
)


def make_dataset(records: list[dict[str, object]] | None = None) -> Dataset:
    provenance = Provenance(
        dataset_id="dataset-a",
        source=DataSource(
            "catalog",
            version="source-v2",
            metadata={"nested": {"values": ["source"]}},
        ),
        retrieved_at=datetime(2026, 11, 6, tzinfo=UTC),
        data_format=DataFormat.JSON,
        dataset_version="dataset-v3",
        transformations=("source operation",),
        metadata={"nested": {"values": ["provenance"]}},
    )
    return Dataset(
        provenance=provenance,
        records=records if records is not None else [{"value": "12"}],
        metadata={"nested": {"values": ["dataset"]}},
    )


@pytest.mark.parametrize(
    ("target_type", "value", "expected"),
    [
        (int, "-12", -12),
        (int, 12, 12),
        (float, "1.25", 1.25),
        (float, 2, 2.0),
        (float, 2.5, 2.5),
    ],
)
def test_converts_explicit_integer_and_float_values(target_type, value, expected):
    result = preprocess_dataset(
        make_dataset([{"value": value}]),
        conversions=[FieldConversion("value", target_type, "error", "error")],
    )

    assert result.records[0]["value"] == expected


@pytest.mark.parametrize("value", ["1.0", "1e2", "--1", "1_000", ""])
def test_integer_conversion_rejects_non_integer_strings(value):
    with pytest.raises(PreprocessingError, match=r"'value'.*record index 0"):
        preprocess_dataset(
            make_dataset([{"value": value}]),
            conversions=[FieldConversion("value", int, "error", "error")],
        )


@pytest.mark.parametrize(
    "value", ["NaN", "Infinity", "-Infinity", float("nan"), float("inf"), -float("inf")]
)
def test_float_conversion_rejects_non_finite_values(value):
    with pytest.raises(PreprocessingError, match=r"'value'.*record index 0"):
        preprocess_dataset(
            make_dataset([{"value": value}]),
            conversions=[FieldConversion("value", float, "error", "error")],
        )


@pytest.mark.parametrize("value", ["", "not-a-number"])
def test_float_conversion_rejects_invalid_numeric_strings(value):
    with pytest.raises(PreprocessingError, match=r"'value'.*record index 0"):
        preprocess_dataset(
            make_dataset([{"value": value}]),
            conversions=[FieldConversion("value", float, "error", "error")],
        )


@pytest.mark.parametrize("target_type", [int, float])
def test_numeric_conversion_rejects_booleans(target_type):
    with pytest.raises(PreprocessingError, match=r"'value'.*record index 0"):
        preprocess_dataset(
            make_dataset([{"value": True}]),
            conversions=[FieldConversion("value", target_type, "error", "error")],
        )


def test_conversion_error_does_not_expose_the_value():
    with pytest.raises(PreprocessingError) as exc_info:
        preprocess_dataset(
            make_dataset([{"value": "private-invalid-value"}]),
            conversions=[FieldConversion("value", int, "error", "error")],
        )

    assert "private-invalid-value" not in str(exc_info.value)
    assert "record index 0" in str(exc_info.value)
    assert "value" in str(exc_info.value)


def test_absent_field_can_be_preserved():
    result = preprocess_dataset(
        make_dataset([{"other": 1}]),
        conversions=[FieldConversion("value", int, "preserve", "error")],
    )

    assert result.records[0] == {"other": 1}


def test_absent_field_can_raise_error():
    with pytest.raises(PreprocessingError, match=r"'value'.*record index 0"):
        preprocess_dataset(
            make_dataset([{"other": 1}]),
            conversions=[FieldConversion("value", int, "error", "preserve")],
        )


def test_null_field_can_be_preserved():
    result = preprocess_dataset(
        make_dataset([{"value": None}]),
        conversions=[FieldConversion("value", int, "error", "preserve")],
    )

    assert result.records[0]["value"] is None


def test_null_field_can_raise_error():
    with pytest.raises(PreprocessingError, match=r"'value'.*record index 0"):
        preprocess_dataset(
            make_dataset([{"value": None}]),
            conversions=[FieldConversion("value", int, "preserve", "error")],
        )


def test_empty_string_is_not_treated_as_missing():
    with pytest.raises(PreprocessingError, match=r"'value'.*record index 0"):
        preprocess_dataset(
            make_dataset([{"value": ""}]),
            conversions=[FieldConversion("value", int, "preserve", "preserve")],
        )


def test_numeric_sentinel_is_converted_as_a_value():
    result = preprocess_dataset(
        make_dataset([{"value": "-999"}]),
        conversions=[FieldConversion("value", int, "preserve", "preserve")],
    )

    assert result.records[0]["value"] == -999


def test_unconfigured_fields_are_preserved():
    result = preprocess_dataset(
        make_dataset([{"value": "4", "other": {"items": [1, 2]}}]),
        conversions=[FieldConversion("value", int, "error", "error")],
    )

    assert result.records[0]["other"] == {"items": [1, 2]}


def test_rejects_duplicate_field_conversions_before_processing():
    conversions = [
        FieldConversion("value", int, "preserve", "preserve"),
        FieldConversion("value", float, "preserve", "preserve"),
    ]

    with pytest.raises(ValueError, match="duplicate"):
        preprocess_dataset(
            make_dataset([{"value": "not-a-number"}]), conversions=conversions
        )


def test_rejects_unsupported_target_type():
    with pytest.raises(ValueError, match="target_type"):
        FieldConversion("value", str, "preserve", "preserve")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("absent_policy", "null_policy"),
    [("ignore", "preserve"), ("preserve", "ignore")],
)
def test_rejects_invalid_policies(absent_policy, null_policy):
    with pytest.raises(ValueError, match="policy"):
        FieldConversion("value", int, absent_policy, null_policy)  # type: ignore[arg-type]


@pytest.mark.parametrize("field_name", ["", "  "])
def test_rejects_invalid_field_names(field_name):
    with pytest.raises(ValueError, match="field_name"):
        FieldConversion(field_name, int, "preserve", "preserve")


def test_processes_multiple_records():
    dataset = make_dataset([{"value": "1"}, {"value": "2"}])
    result = preprocess_dataset(
        dataset,
        conversions=[FieldConversion("value", int, "error", "error")],
    )

    assert [record["value"] for record in result.records] == [1, 2]
    assert [record["value"] for record in dataset.records] == ["1", "2"]


def test_input_nested_records_and_metadata_are_independent_from_output():
    dataset = make_dataset([{"nested": {"items": [1, {"value": 2}]}}])
    original_record = copy.deepcopy(dict(dataset.records[0]))
    original_metadata = copy.deepcopy(dict(dataset.metadata))
    result = preprocess_dataset(dataset, conversions=[])

    result.records[0]["nested"]["items"][1]["value"] = 99  # type: ignore[index]
    result.metadata["nested"]["values"].append("output")  # type: ignore[index, union-attr]

    assert dataset.records[0] == original_record
    assert dict(dataset.metadata) == original_metadata


def test_output_does_not_alias_source_or_provenance_metadata():
    dataset = make_dataset()
    result = preprocess_dataset(dataset, conversions=[])

    result.provenance.source.metadata["nested"]["values"].append("output")  # type: ignore[index, union-attr]
    result.provenance.metadata["nested"]["values"].append("output")  # type: ignore[index, union-attr]

    assert dataset.provenance.source.metadata == {"nested": {"values": ["source"]}}
    assert dataset.provenance.metadata == {"nested": {"values": ["provenance"]}}


def test_preserves_identity_source_version_and_appends_deterministic_history():
    dataset = make_dataset()
    conversion = FieldConversion("value", int, "preserve", "preserve")

    result = preprocess_dataset(dataset, conversions=[conversion])
    repeated = preprocess_dataset(dataset, conversions=[conversion])

    assert result is not dataset
    assert result.provenance.dataset_id == dataset.provenance.dataset_id
    assert result.provenance.source.identifier == dataset.provenance.source.identifier
    assert result.provenance.source.version == dataset.provenance.source.version
    assert result.provenance.retrieved_at == dataset.provenance.retrieved_at
    assert result.provenance.data_format is dataset.provenance.data_format
    assert result.provenance.dataset_version == dataset.provenance.dataset_version
    assert result.provenance.transformations[0] == "source operation"
    assert (
        result.provenance.transformations[1:] == repeated.provenance.transformations[1:]
    )


def test_transformation_description_contains_specs_and_is_order_independent():
    dataset = make_dataset([{"count": "3", "ratio": "1.5"}])
    count_conversion = FieldConversion("count", int, "error", "preserve")
    ratio_conversion = FieldConversion("ratio", float, "preserve", "error")

    forward = preprocess_dataset(
        dataset, conversions=[count_conversion, ratio_conversion]
    )
    reversed_order = preprocess_dataset(
        dataset, conversions=[ratio_conversion, count_conversion]
    )
    description = forward.provenance.transformations[-1]

    assert '"field_name":"count"' in description
    assert '"target_type":"int"' in description
    assert '"absent_policy":"error"' in description
    assert '"null_policy":"preserve"' in description
    assert '"field_name":"ratio"' in description
    assert '"target_type":"float"' in description
    assert '"absent_policy":"preserve"' in description
    assert '"null_policy":"error"' in description
    assert description == reversed_order.provenance.transformations[-1]


def test_conversion_error_reports_later_record_index_and_field():
    dataset = make_dataset([{"value": "2"}, {"value": "invalid"}])

    with pytest.raises(PreprocessingError) as exc_info:
        preprocess_dataset(
            dataset,
            conversions=[FieldConversion("value", int, "error", "error")],
        )

    assert exc_info.value.record_index == 1
    assert exc_info.value.field_name == "value"


def test_nested_values_remain_isolated_when_scalar_conversion_is_applied():
    dataset = make_dataset(
        [{"value": "7", "nested": {"items": [1, {"label": "original"}]}}]
    )

    result = preprocess_dataset(
        dataset,
        conversions=[FieldConversion("value", int, "error", "error")],
    )
    result.records[0]["nested"]["items"][1]["label"] = "changed"  # type: ignore[index]
    result.records[0]["nested"]["items"].append(2)  # type: ignore[index, union-attr]

    assert result.records[0]["value"] == 7
    assert dataset.records[0] == {
        "value": "7",
        "nested": {"items": [1, {"label": "original"}]},
    }


def test_empty_conversions_return_independent_dataset_and_append_history():
    dataset = make_dataset()

    result = preprocess_dataset(dataset, conversions=[])

    assert result is not dataset
    assert result.records == dataset.records
    assert len(result.provenance.transformations) == 2
    assert result.provenance.transformations[0] == "source operation"
