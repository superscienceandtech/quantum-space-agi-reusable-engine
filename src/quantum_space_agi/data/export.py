"""Safe JSON and CSV dataset export."""

from __future__ import annotations

import csv
import io
import json
import os
import tempfile
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path

from quantum_space_agi.data.errors import DataExportError
from quantum_space_agi.data.models import Dataset
from quantum_space_agi.data.provenance import DataFormat, Provenance

_FORMAT_VERSION = 1


def export_json(
    dataset: Dataset,
    path: str | Path,
    *,
    overwrite: bool = False,
    encoding: str = "utf-8",
) -> None:
    """Write a versioned JSON envelope with records and full provenance."""
    envelope = {
        "format_version": _FORMAT_VERSION,
        "provenance": _provenance_payload(dataset.provenance),
        "records": [_to_plain(dict(record)) for record in dataset.records],
        "metadata": _to_plain(dataset.metadata),
    }
    try:
        content = json.dumps(
            envelope,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
        )
    except (TypeError, ValueError) as exc:
        raise DataExportError("dataset cannot be represented as standard JSON") from exc
    _write_text(Path(path), f"{content}\n", overwrite=overwrite, encoding=encoding)


def export_csv(
    dataset: Dataset,
    path: str | Path,
    *,
    overwrite: bool = False,
    encoding: str = "utf-8",
) -> None:
    """Write ordinary CSV rows; provenance and metadata are not representable.

    Headers are inferred from record keys. An empty dataset has no keys, so
    this writes an empty file rather than inventing a header.
    """
    headers = sorted({key for record in dataset.records for key in record})
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=headers, extrasaction="raise")
    if headers:
        writer.writeheader()
        for record in dataset.records:
            row = {
                name: _csv_cell(record[name], name)
                for name in headers
                if name in record
            }
            writer.writerow(row)
    _write_text(Path(path), output.getvalue(), overwrite=overwrite, encoding=encoding)


def _csv_cell(value: object, field_name: str) -> str:
    if value is None:
        return ""
    if isinstance(value, str | int | float | bool):
        return str(value)
    raise DataExportError(
        f"CSV scalar field {field_name!r} cannot contain {type(value).__name__}"
    )


def _provenance_payload(provenance: Provenance) -> dict[str, object]:
    source = provenance.source
    return {
        "dataset_id": provenance.dataset_id,
        "source": {
            "identifier": source.identifier,
            "description": source.description,
            "url": source.url,
            "version": source.version,
            "metadata": _to_plain(source.metadata),
        },
        "retrieved_at": provenance.retrieved_at.isoformat(),
        "data_format": provenance.data_format.value,
        "dataset_version": provenance.dataset_version,
        "transformations": list(provenance.transformations),
        "metadata": _to_plain(provenance.metadata),
    }


def _to_plain(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _to_plain(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_to_plain(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, DataFormat):
        return value.value
    return value


def _write_text(
    target: Path,
    content: str,
    *,
    overwrite: bool,
    encoding: str,
) -> None:
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding=encoding,
            newline="",
            dir=target.parent,
            prefix=f".{target.name}.",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        if temporary_path is None:
            raise DataExportError("temporary export file was not created")
        if overwrite:
            os.replace(temporary_path, target)
        else:
            os.link(temporary_path, target)
    except FileExistsError:
        raise
    except (OSError, LookupError, UnicodeError) as exc:
        raise DataExportError(f"could not write dataset to {str(target)!r}") from exc
    finally:
        if temporary_path is not None:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass
            except OSError as exc:
                raise DataExportError(
                    f"could not clean temporary export file {str(temporary_path)!r}"
                ) from exc
