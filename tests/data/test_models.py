from datetime import UTC, datetime

from quantum_space_agi.data.models import Dataset
from quantum_space_agi.data.provenance import DataFormat, Provenance
from quantum_space_agi.data.sources import DataSource


def make_provenance() -> Provenance:
    return Provenance(
        dataset_id="dataset-a",
        source=DataSource("local-file"),
        retrieved_at=datetime(2026, 11, 6, tzinfo=UTC),
        data_format=DataFormat.JSON,
    )


def test_dataset_preserves_records_and_metadata_without_aliasing_top_level_maps() -> (
    None
):
    record = {"value": 2, "label": "raw"}
    metadata = {"study": "sample"}
    dataset = Dataset(provenance=make_provenance(), records=[record], metadata=metadata)

    record["label"] = "changed"
    metadata["study"] = "changed"

    assert dataset.records[0]["label"] == "raw"
    assert dataset.metadata == {"study": "sample"}
    assert dataset.provenance.dataset_id == "dataset-a"


def test_dataset_records_are_read_only_mappings() -> None:
    dataset = Dataset(
        provenance=make_provenance(),
        records=[{"value": 2}],
    )

    try:
        dataset.records[0]["value"] = 3  # type: ignore[index]
    except TypeError:
        pass
    else:
        raise AssertionError("dataset record mapping should be read-only")


def test_dataset_nested_dicts_and_lists_remain_mutable_and_shared() -> None:
    nested = {"items": [1, {"value": 2}]}
    dataset = Dataset(make_provenance(), [{"nested": nested}])

    nested["items"][1]["value"] = 3

    assert dataset.records[0]["nested"] == {"items": [1, {"value": 3}]}
