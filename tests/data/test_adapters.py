from datetime import UTC, datetime

import pytest

from quantum_space_agi.data.adapters.base import DataAdapter, RetrievedPayload
from quantum_space_agi.data.provenance import DataFormat
from quantum_space_agi.data.sources import DataSource


class FixtureAdapter:
    source = DataSource("local-fixture")

    def retrieve(self) -> RetrievedPayload:
        return RetrievedPayload(
            content=b'{"value": 1}',
            data_format=DataFormat.JSON,
            retrieved_at=datetime(2026, 11, 6, tzinfo=UTC),
            dataset_version="fixture-v1",
        )


def test_local_adapter_satisfies_structural_contract() -> None:
    adapter = FixtureAdapter()

    assert isinstance(adapter, DataAdapter)
    assert adapter.source.identifier == "local-fixture"
    assert adapter.retrieve().content == b'{"value": 1}'


def test_retrieved_payload_preserves_retrieval_metadata() -> None:
    retrieved_at = datetime(2026, 11, 6, tzinfo=UTC)
    payload = RetrievedPayload(
        content=b"raw bytes",
        data_format=DataFormat.CSV,
        retrieved_at=retrieved_at,
        dataset_version="provider-v2",
    )

    assert payload.content == b"raw bytes"
    assert payload.data_format is DataFormat.CSV
    assert payload.retrieved_at is retrieved_at
    assert payload.dataset_version == "provider-v2"


def test_retrieved_payload_requires_aware_time_and_valid_format() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        RetrievedPayload(
            content=b"",
            data_format=DataFormat.JSON,
            retrieved_at=datetime(2026, 11, 6),
        )

    with pytest.raises(ValueError, match="data_format"):
        RetrievedPayload(
            content=b"",
            data_format="json",  # type: ignore[arg-type]
            retrieved_at=datetime(2026, 11, 6, tzinfo=UTC),
        )
