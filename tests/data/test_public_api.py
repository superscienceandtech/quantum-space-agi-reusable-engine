"""Public data package exports and import behavior."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_data_public_api_imports_without_environment_or_network_access() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    script = """
import logging
import os
import socket
from collections.abc import Mapping

root_logger = logging.getLogger()
initial_handlers = tuple(root_logger.handlers)
initial_level = root_logger.level

class ForbiddenEnvironment(Mapping):
    def __getitem__(self, key):
        raise AssertionError("package import accessed the environment")
    def __iter__(self):
        raise AssertionError("package import accessed the environment")
    def __len__(self):
        raise AssertionError("package import accessed the environment")

os.environ = ForbiddenEnvironment()
os.getenv = lambda *args, **kwargs: (_ for _ in ()).throw(
    AssertionError("package import accessed the environment")
)
socket.socket = lambda *args, **kwargs: (_ for _ in ()).throw(
    AssertionError("package import opened a network socket")
)
socket.create_connection = lambda *args, **kwargs: (_ for _ in ()).throw(
    AssertionError("package import opened a network connection")
)

from quantum_space_agi.data import (
    DataAdapter,
    DataEngineeringError,
    DataExportError,
    DataFormat,
    DataFormatError,
    DataQualityReport,
    DataSchema,
    DataSource,
    DataSourceError,
    DataSourceRegistry,
    Dataset,
    DuplicateGroup,
    FieldSchema,
    FieldStatistics,
    InvalidRecord,
    JSONScalar,
    JSONValue,
    Provenance,
    Record,
    RetrievedPayload,
    SchemaValidationReport,
    ValidationIssue,
    analyze_quality,
    export_csv,
    export_json,
    load_csv,
    load_file,
    load_json,
    validate_dataset,
)

assert tuple(root_logger.handlers) == initial_handlers
assert root_logger.level == initial_level
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(repository_root / "src")
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=repository_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
