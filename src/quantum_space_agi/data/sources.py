"""Data source metadata and an explicit in-memory source registry."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from quantum_space_agi.core.validation import validate_non_empty_text
from quantum_space_agi.data.errors import DataSourceError


@dataclass(frozen=True, slots=True)
class DataSource:
    """Known metadata about a source; unknown metadata remains unset."""

    identifier: str
    description: str | None = None
    url: str | None = None
    version: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        try:
            validate_non_empty_text(self.identifier, name="source identifier")
            for name in ("description", "url", "version"):
                value = getattr(self, name)
                if value is not None:
                    validate_non_empty_text(value, name=f"source {name}")
        except ValueError as exc:
            raise DataSourceError(str(exc)) from exc
        if not isinstance(self.metadata, Mapping):
            raise DataSourceError("source metadata must be a mapping")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


class DataSourceRegistry:
    """An explicit registry scoped to one caller-owned instance."""

    def __init__(self) -> None:
        self._sources: dict[str, DataSource] = {}

    def register(self, source: DataSource) -> None:
        """Register a source, rejecting duplicate identifiers."""
        if not isinstance(source, DataSource):
            raise DataSourceError("source must be a DataSource")
        if source.identifier in self._sources:
            raise DataSourceError(f"source {source.identifier!r} is already registered")
        self._sources[source.identifier] = source

    def get(self, identifier: str) -> DataSource:
        """Return a registered source or raise ``DataSourceError``."""
        try:
            return self._sources[identifier]
        except KeyError as exc:
            raise DataSourceError(f"source {identifier!r} is not registered") from exc

    @property
    def sources(self) -> tuple[DataSource, ...]:
        """Return registered sources in insertion order."""
        return tuple(self._sources.values())
