"""Errors raised by the data engineering package."""

from quantum_space_agi.errors import QuantumSpaceError


class DataEngineeringError(QuantumSpaceError):
    """Base class for data engineering failures."""


class DataFormatError(DataEngineeringError):
    """Raised when an input payload has an invalid or unsupported format."""


class DataSourceError(DataEngineeringError, ValueError):
    """Raised when source metadata or registry operations are invalid."""


class DataExportError(DataEngineeringError):
    """Raised when a dataset cannot be exported safely."""
