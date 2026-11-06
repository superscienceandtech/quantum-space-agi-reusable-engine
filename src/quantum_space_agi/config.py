"""Explicit, validated runtime configuration."""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from dataclasses import dataclass

from quantum_space_agi.errors import ConfigurationError

_LOG_LEVEL_ENV = "QUANTUM_SPACE_AGI_LOG_LEVEL"
_NAMED_LOG_LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "FATAL": logging.FATAL,
    "ERROR": logging.ERROR,
    "WARN": logging.WARNING,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}


@dataclass(frozen=True, slots=True)
class Settings:
    """Validated package settings.

    Environment variables are only read by an explicit call to :meth:`from_env`.
    """

    log_level: int = logging.INFO

    def __post_init__(self) -> None:
        if isinstance(self.log_level, bool) or not isinstance(self.log_level, int):
            raise ConfigurationError("log_level must be an integer logging level")
        if self.log_level < logging.NOTSET:
            raise ConfigurationError("log_level must be non-negative")

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Settings:
        """Create settings from the log-level environment variable.

        Args:
            environ: Optional environment mapping, useful for explicit and
                deterministic configuration. If omitted, the process environment
                is read when this method is called.

        Raises:
            ConfigurationError: If the configured log level is invalid.
        """
        source = os.environ if environ is None else environ
        raw_level = source.get(_LOG_LEVEL_ENV)
        if raw_level is None:
            return cls()

        normalized_level = raw_level.strip().upper()
        try:
            if normalized_level in _NAMED_LOG_LEVELS:
                level = _NAMED_LOG_LEVELS[normalized_level]
            else:
                level = int(normalized_level)
        except ValueError as exc:
            raise ConfigurationError(
                f"{_LOG_LEVEL_ENV} must be a logging level name or integer"
            ) from exc

        return cls(log_level=level)
