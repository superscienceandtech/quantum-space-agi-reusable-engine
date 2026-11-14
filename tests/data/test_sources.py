import pytest

from quantum_space_agi.data.errors import DataSourceError
from quantum_space_agi.data.sources import DataSource, DataSourceRegistry


def test_source_preserves_identity_and_optional_metadata() -> None:
    metadata = {"mission": "example"}
    source = DataSource(
        identifier="catalog-a",
        description="Local research catalog",
        url="https://example.test/catalog",
        version="v1",
        metadata=metadata,
    )

    metadata["mission"] = "changed"
    assert source.identifier == "catalog-a"
    assert source.description == "Local research catalog"
    assert source.url == "https://example.test/catalog"
    assert source.version == "v1"
    assert source.metadata == {"mission": "example"}


def test_source_allows_unknown_metadata_without_inventing_values() -> None:
    source = DataSource(identifier="unversioned")

    assert source.description is None
    assert source.url is None
    assert source.version is None
    assert source.metadata == {}


@pytest.mark.parametrize("identifier", ["", " ", "\t"])
def test_source_rejects_empty_identifier(identifier: str) -> None:
    with pytest.raises(DataSourceError, match="identifier"):
        DataSource(identifier=identifier)


def test_registry_registers_and_returns_sources_in_insertion_order() -> None:
    registry = DataSourceRegistry()
    first = DataSource("first")
    second = DataSource("second")

    registry.register(first)
    registry.register(second)

    assert registry.get("first") is first
    assert registry.sources == (first, second)


def test_registry_rejects_duplicate_identifier() -> None:
    registry = DataSourceRegistry()
    registry.register(DataSource("same"))

    with pytest.raises(DataSourceError, match="already registered"):
        registry.register(DataSource("same"))


def test_registry_reports_unknown_identifier() -> None:
    with pytest.raises(DataSourceError, match="not registered"):
        DataSourceRegistry().get("missing")
