"""Dataset provenance and supported interchange formats."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import MappingProxyType

from quantum_space_agi.core.validation import validate_non_empty_text
from quantum_space_agi.data.sources import DataSource


class DataFormat(Enum):
    """Supported tabular data interchange formats."""

    JSON = "json"
    CSV = "csv"


@dataclass(frozen=True, slots=True)
class Provenance:
    """Traceable source, retrieval, and transformation metadata for a dataset."""

    dataset_id: str
    source: DataSource
    retrieved_at: datetime
    data_format: DataFormat
    dataset_version: str | None = None
    transformations: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validate_non_empty_text(self.dataset_id, name="dataset_id")
        if not isinstance(self.source, DataSource):
            raise ValueError("source must be a DataSource")
        if not isinstance(self.retrieved_at, datetime):
            raise ValueError("retrieved_at must be a datetime")
        if self.retrieved_at.tzinfo is None or self.retrieved_at.utcoffset() is None:
            raise ValueError("retrieved_at must be timezone-aware")
        if not isinstance(self.data_format, DataFormat):
            raise ValueError("data_format must be a DataFormat")
        if self.dataset_version is not None:
            validate_non_empty_text(self.dataset_version, name="dataset_version")
        if any(
            not isinstance(item, str) or not item.strip()
            for item in self.transformations
        ):
            raise ValueError("transformations must contain non-empty strings")
        if not isinstance(self.metadata, Mapping):
            raise ValueError("provenance metadata must be a mapping")
        object.__setattr__(self, "transformations", tuple(self.transformations))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
