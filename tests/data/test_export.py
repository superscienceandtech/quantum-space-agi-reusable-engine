import csv
import io
from datetime import UTC, datetime

import pytest

from quantum_space_agi.data.errors import DataExportError
from quantum_space_agi.data.export import export_csv, export_json
from quantum_space_agi.data.ingestion import load_csv, load_json
from quantum_space_agi.data.models import Dataset
from quantum_space_agi.data.provenance import DataFormat, Provenance
from quantum_space_agi.data.sources import DataSource


def make_dataset(records) -> Dataset:
    provenance = Provenance(
        dataset_id="dataset-a",
        source=DataSource(
            "catalog",
            description="Source description",
            url="https://example.test/data",
            version="source-1",
            metadata={"provider_note": "kept"},
        ),
        retrieved_at=datetime(2026, 11, 6, 1, 0, tzinfo=UTC),
        data_format=DataFormat.JSON,
        dataset_version="dataset-2",
        transformations=("normalized by user",),
        metadata={"retrieval": "offline fixture"},
    )
    return Dataset(provenance, records, {"license": "source provided"})


def test_json_export_round_trips_records_and_provenance(tmp_path) -> None:
    dataset = make_dataset([{"value": 2, "nested": {"ok": True}}])
    path = tmp_path / "dataset.json"

    export_json(dataset, path)
    loaded = load_json(path.read_text(encoding="utf-8"))

    assert loaded.records == dataset.records
    assert loaded.provenance == dataset.provenance
    assert loaded.metadata == dataset.metadata


def test_csv_export_round_trips_string_records_with_sorted_headers(tmp_path) -> None:
    dataset = make_dataset([{"z": "last", "a": "first"}, {"a": "only"}])
    path = tmp_path / "dataset.csv"

    export_csv(dataset, path)
    with path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    reloaded = load_csv(
        path.read_text(encoding="utf-8"),
        provenance=Provenance(
            "dataset-a",
            DataSource("catalog"),
            datetime(2026, 11, 6, tzinfo=UTC),
            DataFormat.CSV,
        ),
    )

    assert path.read_text(encoding="utf-8").splitlines()[0] == "a,z"
    assert rows == [{"a": "first", "z": "last"}, {"a": "only", "z": ""}]
    assert reloaded.records == tuple(rows)


@pytest.mark.parametrize("value", [{"nested": "value"}, ["nested"], object()])
def test_csv_export_rejects_non_scalar_cells_without_creating_file(
    tmp_path, value: object
) -> None:
    path = tmp_path / "invalid.csv"

    with pytest.raises(DataExportError, match="CSV scalar"):
        export_csv(make_dataset([{"value": value}]), path)

    assert not path.exists()
    assert list(tmp_path.iterdir()) == []


def test_export_refuses_to_overwrite_existing_file_by_default(tmp_path) -> None:
    path = tmp_path / "existing.json"
    path.write_text("original", encoding="utf-8")

    with pytest.raises(FileExistsError):
        export_json(make_dataset([]), path)

    assert path.read_text(encoding="utf-8") == "original"
    assert sorted(item.name for item in tmp_path.iterdir()) == ["existing.json"]


def test_export_overwrites_only_when_explicitly_requested(tmp_path) -> None:
    path = tmp_path / "existing.json"
    path.write_text("original", encoding="utf-8")

    export_json(make_dataset([{"value": "new"}]), path, overwrite=True)

    assert load_json(path.read_text(encoding="utf-8")).records == ({"value": "new"},)


def test_export_failure_preserves_existing_file_and_cleans_temporary_file(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "existing.json"
    path.write_text("original", encoding="utf-8")

    def fail_replace(source, target) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr("quantum_space_agi.data.export.os.replace", fail_replace)
    with pytest.raises(DataExportError) as error:
        export_json(make_dataset([]), path, overwrite=True)

    assert isinstance(error.value.__cause__, OSError)
    assert path.read_text(encoding="utf-8") == "original"
    assert list(tmp_path.iterdir()) == [path]


def test_csv_export_does_not_embed_provenance_or_dataset_metadata(tmp_path) -> None:
    path = tmp_path / "dataset.csv"

    export_csv(make_dataset([{"value": "x"}]), path)

    contents = path.read_text(encoding="utf-8")
    assert "license" not in contents
    assert "dataset-a" not in contents


def test_csv_export_of_empty_dataset_is_empty(tmp_path) -> None:
    path = tmp_path / "empty.csv"

    export_csv(make_dataset([]), path)

    assert path.read_text(encoding="utf-8") == ""


def test_json_export_does_not_mutate_nested_dataset_values(tmp_path) -> None:
    dataset = make_dataset([{"nested": {"items": [1, {"value": 2}]}}])
    original = {"nested": {"items": [1, {"value": 2}]}}
    path = tmp_path / "nested.json"

    export_json(dataset, path)

    assert dataset.records[0] == original


def test_csv_export_uses_csv_escaping(tmp_path) -> None:
    path = tmp_path / "escaped.csv"
    export_csv(make_dataset([{"value": "a,b"}]), path)

    rows = list(csv.reader(io.StringIO(path.read_text(encoding="utf-8"))))

    assert rows == [["value"], ["a,b"]]
