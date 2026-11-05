"""Opt-in configuration helpers for the package's standard-library loggers."""

from __future__ import annotations

import logging

from quantum_space_agi.config import Settings

_LOGGER_NAME = "quantum_space_agi"


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger in the package namespace."""
    logger_name = _LOGGER_NAME if not name else f"{_LOGGER_NAME}.{name}"
    return logging.getLogger(logger_name)


def configure_logging(settings: Settings | None = None) -> logging.Logger:
    """Set the package logger level without changing handlers or the root logger.

    Applications remain responsible for installing handlers and formatting.
    """
    selected_settings = Settings() if settings is None else settings
    logger = get_logger()
    logger.setLevel(selected_settings.log_level)
    return logger
