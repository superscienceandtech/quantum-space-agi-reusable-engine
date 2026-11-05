import json
from datetime import UTC, datetime

import pytest

from quantum_space_agi.data.errors import DataFormatError, DataSourceError
from quantum_space_agi.data.ingestion import load_csv, load_file, load_json
from quantum_space_agi.data.models import Dataset
from quantum_space_agi.data.provenance import DataFormat, Provenance
from quantum_space_agi.data.sources import DataSource


def make_provenance(data_format: DataFormat = DataFormat.JSON) -> Provenance:
    return Provenance(
        dataset_id="dataset-a",
        source=DataSource(
            "catalog",
            description="Provided by the test",
            url="https://example.test/data",
            version="source-1",
        ),
        retrieved_at=datetime(2026, 11, 6, 1, 0, tzinfo=UTC),
        data_format=data_format,
        dataset_version="dataset-2",
    )


def test_load_json_preserves_json_record_values_with_explicit_provenance() -> None:
    dataset = load_json(
        '[{"count": 3, "enabled": true, "note": null}]',
        provenance=make_provenance(),
    )

    assert dataset.records == ({"count": 3, "enabled": True, "note": None},)
    assert dataset.provenance == make_provenance()


@pytest.mark.parametrize(
    "text",
    [
        '[{"value": 1, "value": 2}]',
        '[{"value": {"nested": 1, "nested": 2}}]',
    ],
)
def test_load_json_rejects_duplicate_object_keys(text: str) -> None:
    with pytest.raises(DataFormatError, match="duplicate object key") as error:
        load_json(text, provenance=make_provenance())

    assert isinstance(error.value.__cause__, ValueError)
    assert "duplicate object key" in str(error.value.__cause__)


def test_load_json_accepts_unique_keys_at_multiple_object_levels() -> None:
    dataset = load_json(
        '[{"outer": {"inner": 1, "other": 2}, "value": 3}]',
        provenance=make_provenance(),
    )

    assert dataset.records == ({"outer": {"inner": 1, "other": 2}, "value": 3},)


def test_load_json_rejects_plain_records_without_provenance() -> None:
    with pytest.raises(DataSourceError, match="provenance"):
        load_json('[{"value": 1}]')


def test_load_json_rejects_non_object_records() -> None:
    with pytest.raises(DataFormatError, match="record 1"):
        load_json('[{"ok": true}, 2]', provenance=make_provenance())


def test_load_json_preserves_versioned_envelope_provenance_and_metadata() -> None:
    provenance = make_provenance()
    envelope = {
        "format_version": 1,
        "provenance": {
            "dataset_id": provenance.dataset_id,
            "source": {
                "identifier": provenance.source.identifier,
                "description": provenance.source.description,
                "url": provenance.source.url,
                "version": provenance.source.version,
                "metadata": {},
            },
            "retrieved_at": provenance.retrieved_at.isoformat(),
            "data_format": "json",
            "dataset_version": provenance.dataset_version,
            "transformations": [],
            "metadata": {},
        },
        "records": [{"value": 2}],
        "metadata": {"license": "source provided"},
    }

    loaded = load_json(json.dumps(envelope))

    assert loaded.provenance == provenance
    assert loaded.records == ({"value": 2},)
    assert loaded.metadata == {"license": "source provided"}


@pytest.mark.parametrize(
    "text",
    [
        "",
        "{",
        "[NaN]",
        "[Infinity]",
        "[-Infinity]",
    ],
)
def test_load_json_rejects_malformed_and_nonstandard_json_with_cause(text: str) -> None:
    with pytest.raises(DataFormatError) as error:
        load_json(text, provenance=make_provenance())

    assert error.value.__cause__ is not None


@pytest.mark.parametrize(
    "text",
    [
        '{"records": []}',
        '{"format_version": 2, "records": []}',
        '{"format_version": 1, "records": [1]}',
    ],
)
def test_load_json_rejects_unsupported_envelopes(text: str) -> None:
    with pytest.raises(DataFormatError):
        load_json(text)


def test_load_json_rejects_conflicting_caller_and_envelope_provenance() -> None:
    envelope_provenance = make_provenance()
    envelope = {
        "format_version": 1,
        "provenance": {
            "dataset_id": "other",
            "source": {"identifier": envelope_provenance.source.identifier},
            "retrieved_at": envelope_provenance.retrieved_at.isoformat(),
            "data_format": "json",
        },
        "records": [],
    }

    with pytest.raises(DataFormatError, match="provenance"):
        load_json(json.dumps(envelope), provenance=make_provenance())


def test_load_csv_preserves_cells_as_strings() -> None:
    dataset = load_csv(
        "count,enabled,blank\n3,true,\n",
        provenance=make_provenance(DataFormat.CSV),
    )

    assert dataset.records == ({"count": "3", "enabled": "true", "blank": ""},)


@pytest.mark.parametrize("text", ["", "\n", ",value\n1,2\n", "a,a\n1,2\n"])
def test_load_csv_rejects_empty_or_duplicate_headers(text: str) -> None:
    with pytest.raises(DataFormatError, match="header"):
        load_csv(text, provenance=make_provenance(DataFormat.CSV))


@pytest.mark.parametrize("text", ["a,b\n1\n", "a,b\n1,2,3\n"])
def test_load_csv_rejects_inconsistent_row_widths(text: str) -> None:
    with pytest.raises(DataFormatError, match="row 1"):
        load_csv(text, provenance=make_provenance(DataFormat.CSV))


def test_load_csv_rejects_malformed_quoting_with_cause() -> None:
    with pytest.raises(DataFormatError) as error:
        load_csv(
            'value\n"unterminated\n',
            provenance=make_provenance(DataFormat.CSV),
        )
    assert error.value.__cause__ is not None


def test_load_json_rejects_duplicate_keys_in_nested_envelope_objects() -> None:
    text = (
        '{"format_version": 1, "provenance": {"dataset_id": "x", '
        '"source": {"identifier": "catalog", "metadata": {"tag": 1, "tag": 2}}, '
        '"retrieved_at": "2026-11-06T00:00:00+00:00", "data_format": "json"}, '
        '"records": []}'
    )

    with pytest.raises(DataFormatError, match="duplicate object key") as error:
        load_json(text)

    assert isinstance(error.value.__cause__, ValueError)
    assert "duplicate object key" in str(error.value.__cause__)


def test_load_file_honors_explicit_encoding_and_closes_file(tmp_path) -> None:
    path = tmp_path / "records.csv"
    path.write_bytes("name\ncafé\n".encode("latin-1"))

    dataset = load_file(
        path,
        data_format=DataFormat.CSV,
        provenance=make_provenance(DataFormat.CSV),
        encoding="latin-1",
    )

    assert dataset.records == ({"name": "café"},)


def test_load_file_reports_io_failure_with_original_cause(tmp_path) -> None:
    with pytest.raises(DataSourceError) as error:
        load_file(
            tmp_path / "missing.json",
            data_format=DataFormat.JSON,
            provenance=make_provenance(),
        )

    assert isinstance(error.value.__cause__, FileNotFoundError)


def test_load_file_requires_provenance_for_plain_json(tmp_path) -> None:
    path = tmp_path / "records.json"
    path.write_text('[{"value": 1}]', encoding="utf-8")

    with pytest.raises(DataSourceError, match="provenance"):
        load_file(path, data_format=DataFormat.JSON)


def test_load_file_rejects_unknown_format(tmp_path) -> None:
    path = tmp_path / "records.data"
    path.write_text("", encoding="utf-8")

    with pytest.raises(DataFormatError, match="data_format"):
        load_file(path, data_format="binary")  # type: ignore[arg-type]


def test_load_json_with_empty_array_produces_empty_dataset() -> None:
    dataset = load_json("[]", provenance=make_provenance())

    assert isinstance(dataset, Dataset)
    assert dataset.records == ()
