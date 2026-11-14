"""Package-specific exceptions."""


class QuantumSpaceError(Exception):
    """Base class for errors raised by this package."""


class ConfigurationError(QuantumSpaceError):
    """Raised when package configuration is invalid."""


class ValidationError(QuantumSpaceError, ValueError):
    """Raised when a value does not satisfy a reusable input constraint."""
