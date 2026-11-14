from datetime import UTC, datetime

import pytest

from quantum_space_agi.data.provenance import DataFormat, Provenance
from quantum_space_agi.data.sources import DataSource


def test_provenance_preserves_source_version_and_transformations() -> None:
    retrieved_at = datetime(2026, 11, 6, 1, 0, tzinfo=UTC)
    provenance = Provenance(
        dataset_id="dataset-a",
        source=DataSource("catalog", version="source-v2"),
        retrieved_at=retrieved_at,
        data_format=DataFormat.JSON,
        dataset_version="dataset-v3",
        transformations=("unit conversion documented by caller",),
        metadata={"record_count": 4},
    )

    assert provenance.dataset_id == "dataset-a"
    assert provenance.source.version == "source-v2"
    assert provenance.retrieved_at is retrieved_at
    assert provenance.data_format is DataFormat.JSON
    assert provenance.dataset_version == "dataset-v3"
    assert provenance.transformations == ("unit conversion documented by caller",)
    assert provenance.metadata == {"record_count": 4}


def test_provenance_rejects_naive_retrieval_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        Provenance(
            dataset_id="dataset-a",
            source=DataSource("catalog"),
            retrieved_at=datetime(2026, 11, 6),
            data_format=DataFormat.CSV,
        )


def test_provenance_rejects_empty_dataset_identifier() -> None:
    with pytest.raises(ValueError, match="dataset_id"):
        Provenance(
            dataset_id=" ",
            source=DataSource("catalog"),
            retrieved_at=datetime(2026, 11, 6, tzinfo=UTC),
            data_format=DataFormat.JSON,
        )


def test_provenance_rejects_unknown_format() -> None:
    with pytest.raises(ValueError, match="data_format"):
        Provenance(
            dataset_id="dataset-a",
            source=DataSource("catalog"),
            retrieved_at=datetime(2026, 11, 6, tzinfo=UTC),
            data_format="json",  # type: ignore[arg-type]
        )
