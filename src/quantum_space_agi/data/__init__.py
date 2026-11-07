"""Reusable data engineering models and utilities.

The module-level ``validate_dataset`` and ``ValidationIssue`` are the remote
data-engineering API based on ``Dataset``/``DataSchema``. The earlier ARC-03
record-list validator remains available as ``validate_records`` and through
``quantum_space_agi.data.validator``.
"""

from quantum_space_agi.data.adapters import DataAdapter, RetrievedPayload
from quantum_space_agi.data.errors import (
    DataEngineeringError,
    DataExportError,
    DataFormatError,
    DataSourceError,
)
from quantum_space_agi.data.export import export_csv, export_json
from quantum_space_agi.data.ingestion import load_csv, load_file, load_json
from quantum_space_agi.data.loader import (
    DataFormatError as LoaderDataFormatError,
)
from quantum_space_agi.data.loader import (
    DataLoadError,
    DatasetLoadResult,
    EmptyDatasetError,
    FileAccessError,
    MetadataAssociationError,
    UnsupportedFormatError,
    load_dataset,
)
from quantum_space_agi.data.models import Dataset, JSONScalar, JSONValue, Record
from quantum_space_agi.data.provenance import DataFormat, Provenance
from quantum_space_agi.data.quality import (
    DataQualityReport,
    DuplicateGroup,
    FieldStatistics,
    analyze_quality,
)
from quantum_space_agi.data.schemas import (
    DataSchema,
    FieldSchema,
    InvalidRecord,
    SchemaValidationReport,
    ValidationIssue,
    validate_dataset,
)
from quantum_space_agi.data.sources import DataSource, DataSourceRegistry
from quantum_space_agi.data.validator import (
    SchemaDefinitionError,
    ValidationReport,
)
from quantum_space_agi.data.validator import (
    ValidationIssue as RecordValidationIssue,
)
from quantum_space_agi.data.validator import (
    validate_dataset as validate_records,
)

__all__ = [
    "DataAdapter",
    "DataEngineeringError",
    "DataExportError",
    "DataFormat",
    "DataFormatError",
    "DataLoadError",
    "DatasetLoadResult",
    "LoaderDataFormatError",
    "EmptyDatasetError",
    "FileAccessError",
    "MetadataAssociationError",
    "UnsupportedFormatError",
    "DataQualityReport",
    "DataSchema",
    "DataSource",
    "DataSourceError",
    "DataSourceRegistry",
    "Dataset",
    "DuplicateGroup",
    "FieldSchema",
    "FieldStatistics",
    "InvalidRecord",
    "JSONScalar",
    "JSONValue",
    "Provenance",
    "Record",
    "RecordValidationIssue",
    "RetrievedPayload",
    "SchemaDefinitionError",
    "SchemaValidationReport",
    "ValidationIssue",
    "ValidationReport",
    "analyze_quality",
    "export_csv",
    "export_json",
    "load_csv",
    "load_dataset",
    "load_file",
    "load_json",
    "validate_dataset",
    "validate_records",
]
