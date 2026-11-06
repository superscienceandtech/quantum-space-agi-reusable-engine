"""Small, dependency-free CSV/JSON loading with optional metadata association.

Loading parses records only. It does not validate a scientific schema or alter
source files, field names, values, or units.
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class DataLoadError(Exception):
    """Base class for predictable data loading errors."""


class FileAccessError(DataLoadError):
    """The requested input could not be read."""


class DataFormatError(DataLoadError):
    """The input cannot be parsed using the selected format."""


class MetadataAssociationError(DataLoadError):
    """Metadata is malformed, ambiguous, or internally inconsistent."""


class UnsupportedFormatError(DataLoadError):
    """The input file extension is not supported."""


class EmptyDatasetError(DataLoadError):
    """The file contains no records to load."""


@dataclass(frozen=True)
class DatasetLoadResult:
    """Records and traceability information returned for one loaded file."""

    dataset_id: str | None
    source_file: Path
    format: str
    records: list[dict[str, Any]]
    record_count: int
    source_metadata: dict[str, Any] | None
    provenance_metadata: dict[str, Any] | None
    source_metadata_reference: Path | None
    provenance_metadata_reference: Path | None
    dataset_version: str | None
    loaded_at: str
    loading_status: str
    metadata_warnings: tuple[str, ...]
    operation: dict[str, str]


def load_dataset(
    source_file: str | Path,
    *,
    metadata_dir: str | Path | None = None,
    dataset_id: str | None = None,
    encoding: str = "utf-8",
) -> DatasetLoadResult:
    """Load a CSV or JSON file and associate matching sidecar metadata.

    By default metadata is sought at ``<data-root>/metadata``, where
    ``<data-root>`` is the parent of the input file's directory (for example,
    ``data/samples/x.csv`` -> ``data/metadata``). Pass ``metadata_dir`` to
    select another location. Missing sidecars are reported as warnings while
    records remain available; malformed or conflicting metadata raises
    :class:`MetadataAssociationError`.
    """

    path = Path(source_file)
    file_format = path.suffix.lower().lstrip(".")
    if file_format not in {"csv", "json"}:
        raise UnsupportedFormatError(
            f"Unsupported format for '{path.name}'; expected a .csv or .json file."
        )

    try:
        with path.open("r", encoding=encoding, newline="") as stream:
            contents = stream.read()
    except OSError as exc:
        raise FileAccessError(f"Cannot read '{path}': {exc}") from exc
    except (UnicodeError, LookupError) as exc:
        raise DataFormatError(
            f"Cannot decode '{path}' using encoding '{encoding}': {exc}"
        ) from exc

    if not contents.strip():
        raise EmptyDatasetError(f"'{path}' is empty and contains no records.")

    if file_format == "csv":
        records = _parse_csv(contents, path)
    else:
        records = _parse_json(contents, path)
    if not records:
        raise EmptyDatasetError(f"'{path}' contains no records.")

    resolved_path = path.resolve()
    metadata_path = (
        Path(metadata_dir)
        if metadata_dir is not None
        else path.parent.parent / "metadata"
    )
    source_record, source_reference, source_id, warnings = _associate_source(
        resolved_path, metadata_path / "sources", dataset_id
    )
    associated_id = dataset_id or source_id
    provenance_record, provenance_reference, provenance_warnings = (
        _associate_provenance(
            resolved_path,
            metadata_path / "provenance",
            associated_id,
        )
    )
    warnings.extend(provenance_warnings)
    if associated_id is None and provenance_record is not None:
        associated_id = provenance_record["dataset_id"]

    source_version = source_record.get("dataset_version") if source_record else None
    provenance_version = (
        provenance_record.get("dataset_version") if provenance_record else None
    )
    if source_version and provenance_version and source_version != provenance_version:
        raise MetadataAssociationError(
            f"Source metadata version '{source_version}' does not match "
            f"provenance version "
            f"'{provenance_version}' for dataset_id '{associated_id}'."
        )

    loaded_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    status = "loaded_with_metadata_warnings" if warnings else "loaded"
    version = source_version or provenance_version
    return DatasetLoadResult(
        dataset_id=associated_id,
        source_file=resolved_path,
        format=file_format,
        records=records,
        record_count=len(records),
        source_metadata=source_record,
        provenance_metadata=provenance_record,
        source_metadata_reference=source_reference,
        provenance_metadata_reference=provenance_reference,
        dataset_version=version,
        loaded_at=loaded_at,
        loading_status=status,
        metadata_warnings=tuple(warnings),
        operation={
            "operation": "load",
            "format": file_format,
            "loaded_at": loaded_at,
            "source_file": str(resolved_path),
        },
    )


def _parse_csv(contents: str, path: Path) -> list[dict[str, Any]]:
    try:
        reader = csv.reader(io.StringIO(contents, newline=""), strict=True)
        headers = next(reader, None)
        if headers is None:
            raise EmptyDatasetError(f"'{path}' contains no CSV records.")
        if not headers or any(header == "" for header in headers):
            raise DataFormatError(
                f"'{path}' is missing one or more CSV column headers."
            )
        if len(set(headers)) != len(headers):
            raise DataFormatError(f"'{path}' contains duplicate CSV column headers.")

        records = []
        for line_number, values in enumerate(reader, start=2):
            if len(values) != len(headers):
                raise DataFormatError(
                    f"'{path}' has {len(values)} fields on line {line_number}; "
                    f"expected {len(headers)} based on the header."
                )
            records.append(dict(zip(headers, values)))
        return records
    except csv.Error as exc:
        raise DataFormatError(f"Malformed CSV in '{path}': {exc}") from exc


def _parse_json(contents: str, path: Path) -> list[dict[str, Any]]:
    try:
        value = json.loads(contents)
    except json.JSONDecodeError as exc:
        raise DataFormatError(
            f"Malformed JSON in '{path}' at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}."
        ) from exc

    if isinstance(value, list):
        records = value
    elif isinstance(value, dict):
        records = value["records"] if set(value) == {"records"} else [value]
    else:
        raise DataFormatError(
            f"'{path}' must contain a JSON object, an array of objects, "
            "or an object with only a 'records' array."
        )

    if not isinstance(records, list) or any(
        not isinstance(record, dict) for record in records
    ):
        raise DataFormatError(f"'{path}' must contain JSON objects for every record.")
    return records


def _read_metadata(
    directory: Path,
) -> tuple[list[tuple[Path, dict[str, Any]]], list[str]]:
    if not directory.exists():
        return [], [f"Metadata directory is missing: '{directory}'."]
    if not directory.is_dir():
        raise MetadataAssociationError(
            f"Metadata path is not a directory: '{directory}'."
        )

    records = []
    for file_path in sorted(directory.glob("*.json")):
        try:
            value = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise MetadataAssociationError(
                f"Cannot read metadata file '{file_path}': {exc}"
            ) from exc
        if not isinstance(value, dict):
            raise MetadataAssociationError(
                f"Metadata file '{file_path}' must contain a JSON object."
            )
        records.append((file_path.resolve(), value))
    if not records:
        return [], [f"No JSON metadata records found in '{directory}'."]
    return records, []


def _referenced_files(record: dict[str, Any]) -> list[str]:
    refs = record.get("files", [])
    if isinstance(refs, str):
        refs = [refs]
    if not isinstance(refs, list):
        raise MetadataAssociationError(
            "Metadata 'files' must be a list of paths or file objects."
        )
    normalized = []
    for item in refs:
        if isinstance(item, str):
            normalized.append(item)
        elif isinstance(item, dict):
            name = item.get("path") or item.get("filename")
            if isinstance(name, str):
                normalized.append(name)
            else:
                raise MetadataAssociationError(
                    "Each metadata file object must include a string "
                    "'path' or 'filename'."
                )
        else:
            raise MetadataAssociationError(
                "Metadata 'files' entries must be strings or file objects."
            )
    if "source_file" in record:
        if not isinstance(record["source_file"], str):
            raise MetadataAssociationError(
                "Metadata 'source_file' must be a string path."
            )
        normalized.append(record["source_file"])
    return normalized


def _references_input(
    record: dict[str, Any], source_file: Path, metadata_dir: Path
) -> bool:
    # ``directory`` is sources/ or provenance/; three parents up is the
    # repository root in the standard ``data/metadata/<kind>`` layout.
    root = metadata_dir.parent.parent.parent.resolve()
    for reference in _referenced_files(record):
        candidate = Path(reference)
        resolved = (
            candidate.resolve()
            if candidate.is_absolute()
            else (root / candidate).resolve()
        )
        if resolved == source_file or (
            not candidate.parent.parts and candidate.name == source_file.name
        ):
            return True
    return False


def _associate_source(
    source_file: Path, directory: Path, requested_id: str | None
) -> tuple[dict[str, Any] | None, Path | None, str | None, list[str]]:
    records, warnings = _read_metadata(directory)
    if warnings:
        return None, None, requested_id, warnings

    matches = []
    for file_path, record in records:
        record_id = record.get("dataset_id")
        if not isinstance(record_id, str) or not record_id:
            raise MetadataAssociationError(
                f"Source metadata '{file_path}' has no non-empty dataset_id."
            )
        if requested_id is not None:
            if record_id == requested_id and (
                not _referenced_files(record)
                or _references_input(record, source_file, directory)
            ):
                matches.append((file_path, record))
        elif _references_input(record, source_file, directory):
            matches.append((file_path, record))

    if len(matches) > 1:
        raise MetadataAssociationError(
            f"More than one source metadata record matches '{source_file}'."
        )
    if not matches:
        detail = (
            f"No source metadata matches dataset_id '{requested_id}'."
            if requested_id
            else f"No source metadata references '{source_file.name}'."
        )
        return None, None, requested_id, [detail]
    file_path, record = matches[0]
    return record, file_path, record["dataset_id"], []


def _associate_provenance(
    source_file: Path, directory: Path, dataset_id: str | None
) -> tuple[dict[str, Any] | None, Path | None, list[str]]:
    records, warnings = _read_metadata(directory)
    if warnings:
        return None, None, warnings

    path_matches = [
        (file_path, record)
        for file_path, record in records
        if _references_input(record, source_file, directory)
    ]
    id_matches = [
        (file_path, record)
        for file_path, record in records
        if dataset_id is not None and record.get("dataset_id") == dataset_id
    ]
    if (
        path_matches
        and dataset_id is not None
        and any(record.get("dataset_id") != dataset_id for _, record in path_matches)
    ):
        raise MetadataAssociationError(
            f"Provenance for '{source_file.name}' has a dataset_id "
            f"inconsistent with '{dataset_id}'."
        )
    matches = id_matches or path_matches
    if len(matches) > 1:
        raise MetadataAssociationError(
            f"More than one provenance record matches dataset_id '{dataset_id}'."
        )
    if not matches:
        return (
            None,
            None,
            [f"No provenance metadata matches dataset_id '{dataset_id}'."],
        )
    file_path, record = matches[0]
    record_id = record.get("dataset_id")
    if dataset_id is not None and record_id != dataset_id:
        raise MetadataAssociationError(
            f"Provenance dataset_id '{record_id}' does not match "
            f"source dataset_id '{dataset_id}'."
        )
    if not isinstance(record_id, str) or not record_id:
        raise MetadataAssociationError(
            f"Provenance metadata '{file_path}' has no non-empty dataset_id."
        )
    return record, file_path, []
