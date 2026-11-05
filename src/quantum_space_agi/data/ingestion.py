"""JSON, CSV, and local-file dataset ingestion."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import NoReturn

from quantum_space_agi.data.errors import DataFormatError, DataSourceError
from quantum_space_agi.data.models import Dataset, Record
from quantum_space_agi.data.provenance import DataFormat, Provenance
from quantum_space_agi.data.sources import DataSource


def load_json(text: str, *, provenance: Provenance | None = None) -> Dataset:
    """Load a JSON record array or this package's versioned dataset envelope.

    Plain arrays require caller-supplied provenance. An exported envelope
    carries its own provenance and metadata.
    """
    try:
        payload = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonstandard_constant,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise DataFormatError(f"invalid JSON payload: {exc}") from exc

    if isinstance(payload, list):
        selected_provenance = _require_format(provenance, DataFormat.JSON)
        try:
            records = _records(payload)
        except ValueError as exc:
            raise DataFormatError(f"invalid JSON records: {exc}") from exc
        return Dataset(selected_provenance, records)

    if not isinstance(payload, dict):
        raise DataFormatError("JSON payload must be a record array or dataset envelope")

    if payload.get("format_version") != 1 or isinstance(
        payload.get("format_version"), bool
    ):
        raise DataFormatError("unsupported JSON dataset envelope version")
    if "records" not in payload or "provenance" not in payload:
        raise DataFormatError("JSON dataset envelope requires records and provenance")

    try:
        envelope_provenance = _provenance_from_payload(payload["provenance"])
        records = _records(payload["records"])
        metadata = payload.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise ValueError("envelope metadata must be an object")
        if envelope_provenance.data_format is not DataFormat.JSON:
            raise ValueError("envelope provenance format must be JSON")
    except (KeyError, TypeError, ValueError) as exc:
        raise DataFormatError(f"invalid JSON dataset envelope: {exc}") from exc

    if provenance is not None and provenance != envelope_provenance:
        raise DataFormatError("caller provenance conflicts with envelope provenance")
    return Dataset(envelope_provenance, records, metadata)


def load_csv(text: str, *, provenance: Provenance) -> Dataset:
    """Load CSV records while preserving each cell as a string."""
    _require_format(provenance, DataFormat.CSV)
    try:
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        headers = next(reader, None)
        if headers is None or not headers:
            raise DataFormatError("CSV requires a non-empty header")
        if any(not header.strip() for header in headers):
            raise DataFormatError("CSV header names must not be empty")
        if len(set(headers)) != len(headers):
            raise DataFormatError("CSV header names must be unique")

        records: list[Record] = []
        for row_number, row in enumerate(reader, start=1):
            if len(row) != len(headers):
                raise DataFormatError(
                    f"CSV row {row_number} has {len(row)} cells; "
                    f"expected {len(headers)}"
                )
            records.append(dict(zip(headers, row, strict=True)))
    except csv.Error as exc:
        raise DataFormatError("invalid CSV payload") from exc
    return Dataset(provenance, records)


def load_file(
    path: str | Path,
    *,
    data_format: DataFormat,
    provenance: Provenance | None = None,
    encoding: str = "utf-8",
) -> Dataset:
    """Read a local file using explicit format and text encoding."""
    if not isinstance(data_format, DataFormat):
        raise DataFormatError("data_format must be a DataFormat")
    try:
        with Path(path).open("r", encoding=encoding, newline="") as file:
            text = file.read()
    except (OSError, LookupError) as exc:
        raise DataSourceError(f"could not read data file {str(path)!r}") from exc
    except UnicodeError as exc:
        raise DataFormatError(f"could not decode data file {str(path)!r}") from exc

    if data_format is DataFormat.JSON:
        return load_json(text, provenance=provenance)
    if provenance is None:
        raise DataSourceError("CSV ingestion requires explicit provenance")
    return load_csv(text, provenance=provenance)


def _require_format(provenance: Provenance | None, expected: DataFormat) -> Provenance:
    if not isinstance(provenance, Provenance):
        raise DataSourceError("explicit provenance is required")
    if provenance.data_format is not expected:
        raise DataSourceError(f"provenance data_format must be {expected.value}")
    return provenance


def _records(value: object) -> tuple[Record, ...]:
    if not isinstance(value, list):
        raise ValueError("records must be a JSON array")
    records: list[Record] = []
    for index, record in enumerate(value):
        if not isinstance(record, dict):
            raise ValueError(f"record {index} must be a JSON object")
        records.append(record)
    return tuple(records)


def _provenance_from_payload(value: object) -> Provenance:
    if not isinstance(value, dict):
        raise ValueError("provenance must be an object")
    source_value = value["source"]
    if not isinstance(source_value, dict):
        raise ValueError("provenance source must be an object")
    source = DataSource(
        identifier=source_value["identifier"],
        description=source_value.get("description"),
        url=source_value.get("url"),
        version=source_value.get("version"),
        metadata=_metadata(source_value.get("metadata", {}), "source metadata"),
    )
    retrieved_at = datetime.fromisoformat(value["retrieved_at"])
    data_format = DataFormat(value["data_format"])
    transformations = value.get("transformations", ())
    if not isinstance(transformations, Sequence) or isinstance(
        transformations, (str, bytes)
    ):
        raise ValueError("provenance transformations must be an array")
    return Provenance(
        dataset_id=value["dataset_id"],
        source=source,
        retrieved_at=retrieved_at,
        data_format=data_format,
        dataset_version=value.get("dataset_version"),
        transformations=tuple(transformations),
        metadata=_metadata(value.get("metadata", {}), "provenance metadata"),
    )


def _metadata(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _reject_nonstandard_constant(value: str) -> NoReturn:
    raise ValueError(f"non-standard JSON constant {value!r} is not allowed")


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate object key {key!r}")
        result[key] = value
    return result
