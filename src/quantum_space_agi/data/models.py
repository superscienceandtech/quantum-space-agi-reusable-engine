"""Dataset records and JSON-compatible value types."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TypeAlias

from quantum_space_agi.data.provenance import Provenance

JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]
Record: TypeAlias = Mapping[str, JSONValue]


@dataclass(frozen=True, slots=True)
class Dataset:
    """A dataset's records and provenance, kept separate from transforms.

    Top-level record and metadata mappings are copied and exposed read-only.
    Nested dictionaries and lists remain mutable and are not deep-copied; callers
    should avoid mutating them when they need stable dataset contents.
    """

    provenance: Provenance
    records: Sequence[Record]
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.provenance, Provenance):
            raise ValueError("provenance must be a Provenance")
        copied_records: list[Record] = []
        for index, record in enumerate(self.records):
            if not isinstance(record, Mapping):
                raise ValueError(f"record {index} must be a mapping")
            if any(not isinstance(key, str) for key in record):
                raise ValueError(f"record {index} keys must be strings")
            copied_records.append(MappingProxyType(dict(record)))
        if not isinstance(self.metadata, Mapping):
            raise ValueError("dataset metadata must be a mapping")
        object.__setattr__(self, "records", tuple(copied_records))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
