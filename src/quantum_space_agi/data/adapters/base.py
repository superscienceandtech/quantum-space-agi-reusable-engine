"""Provider-neutral adapter contract for future data integrations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from quantum_space_agi.core.validation import validate_non_empty_text
from quantum_space_agi.data.provenance import DataFormat
from quantum_space_agi.data.sources import DataSource


@dataclass(frozen=True, slots=True)
class RetrievedPayload:
    """Raw bytes and retrieval facts supplied by a data provider adapter."""

    content: bytes
    data_format: DataFormat
    retrieved_at: datetime
    dataset_version: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.content, bytes):
            raise ValueError("content must be bytes")
        if not isinstance(self.data_format, DataFormat):
            raise ValueError("data_format must be a DataFormat")
        if not isinstance(self.retrieved_at, datetime):
            raise ValueError("retrieved_at must be a datetime")
        if self.retrieved_at.tzinfo is None or self.retrieved_at.utcoffset() is None:
            raise ValueError("retrieved_at must be timezone-aware")
        if self.dataset_version is not None:
            validate_non_empty_text(self.dataset_version, name="dataset_version")


@runtime_checkable
class DataAdapter(Protocol):
    """Synchronous provider contract; transport and endpoint details are external."""

    @property
    def source(self) -> DataSource:
        """Return the adapter's explicitly declared source metadata."""

    def retrieve(self) -> RetrievedPayload:
        """Retrieve one payload and return provider-supplied retrieval metadata."""
