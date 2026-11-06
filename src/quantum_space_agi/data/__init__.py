"""Data ingestion interfaces and utilities."""

from .loader import (
    DataFormatError,
    DataLoadError,
    DatasetLoadResult,
    EmptyDatasetError,
    FileAccessError,
    MetadataAssociationError,
    UnsupportedFormatError,
    load_dataset,
)
from .validator import (
    SchemaDefinitionError,
    ValidationIssue,
    ValidationReport,
    validate_dataset,
)

__all__ = [
    "DataFormatError",
    "DataLoadError",
    "DatasetLoadResult",
    "EmptyDatasetError",
    "FileAccessError",
    "MetadataAssociationError",
    "UnsupportedFormatError",
    "SchemaDefinitionError",
    "ValidationIssue",
    "ValidationReport",
    "load_dataset",
    "validate_dataset",
]
