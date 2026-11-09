"""Read-only JSON ingestion from the NASA Exoplanet Archive TAP service."""

from __future__ import annotations

import hashlib
import json
import math
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import NoReturn

from quantum_space_agi.data.errors import DataEngineeringError, DataFormatError
from quantum_space_agi.data.ingestion import load_json
from quantum_space_agi.data.models import Dataset
from quantum_space_agi.data.provenance import DataFormat, Provenance
from quantum_space_agi.data.sources import DataSource

TAP_ENDPOINT = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
TAP_CITATION_GUIDANCE_URL = "https://exoplanetarchive.ipac.caltech.edu/docs/doi.html"
MAX_ROWS = 100
MAX_RESPONSE_BYTES = 10 * 1024 * 1024
DEFAULT_TIMEOUT = 20.0

_IDENTIFIER_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


class ExoplanetArchiveError(DataEngineeringError):
    """Base class for Exoplanet Archive adapter failures."""


class TAPTransportError(ExoplanetArchiveError):
    """The TAP request could not be completed due to a transport failure."""


class TAPHTTPError(ExoplanetArchiveError):
    """The TAP endpoint returned an unsuccessful HTTP response."""

    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"Exoplanet Archive TAP returned HTTP status {status_code}")


class TAPQueryError(ExoplanetArchiveError):
    """The service returned a recognizable TAP query error."""

    def __init__(self, status_code: int | None = None) -> None:
        self.status_code = status_code
        message = "Exoplanet Archive TAP rejected the query"
        if status_code is not None:
            message += f" (HTTP status {status_code})"
        super().__init__(message)


class TAPContentTypeError(ExoplanetArchiveError):
    """The service response was not JSON as requested."""


class TAPJSONError(ExoplanetArchiveError):
    """The service response was not valid UTF-8 JSON."""


class TAPRecordStructureError(ExoplanetArchiveError):
    """The JSON payload did not satisfy the requested row structure."""


class TAPMetadataError(ExoplanetArchiveError):
    """The source or provenance metadata could not be constructed."""


def fetch_ps_dataset(
    columns: Sequence[str],
    *,
    order_by: Sequence[str],
    row_identity_fields: Sequence[str],
    limit: int,
    timeout: float = DEFAULT_TIMEOUT,
) -> Dataset:
    """Fetch a bounded JSON result from the Planetary Systems (``ps``) table.

    No filters, retries, scalar coercion, or scientific interpretation are
    applied. The response checksum covers the exact bytes received; V1 does not
    retain those bytes after parsing.
    """
    selected_columns = _validate_identifiers(columns, name="columns")
    ordering = _validate_identifiers(order_by, name="order_by")
    identity_fields = _validate_identifiers(
        row_identity_fields, name="row_identity_fields"
    )
    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 1 <= limit <= MAX_ROWS
    ):
        raise ValueError(f"limit must be an integer between 1 and {MAX_ROWS}")
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, int | float)
        or not math.isfinite(timeout)
        or timeout <= 0
    ):
        raise ValueError("timeout must be a positive finite number")
    if any(field not in selected_columns for field in identity_fields):
        raise ValueError("row identity fields must be selected columns")
    if any(field not in ordering for field in identity_fields):
        raise ValueError("row identity fields must be included in order_by")

    adql = (
        f"SELECT TOP {limit} {', '.join(selected_columns)} FROM ps "
        f"ORDER BY {', '.join(ordering)}"
    )
    query_parameters = urllib.parse.urlencode({"query": adql, "format": "json"})
    request_url = f"{TAP_ENDPOINT}?{query_parameters}"
    request = urllib.request.Request(
        request_url,
        headers={"Accept": "application/json"},
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status_code = _status_code(response)
            response_bytes = response.read(MAX_RESPONSE_BYTES + 1)
            retrieved_at = datetime.now(UTC)
            content_type = response.headers.get("Content-Type")
    except urllib.error.HTTPError as exc:
        response_bytes = exc.read(MAX_RESPONSE_BYTES + 1)
        if _is_tap_error(response_bytes):
            raise TAPQueryError(exc.code) from exc
        raise TAPHTTPError(exc.code) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise TAPTransportError("Exoplanet Archive TAP request failed") from exc

    if status_code < 200 or status_code >= 300:
        if _is_tap_error(response_bytes):
            raise TAPQueryError(status_code)
        raise TAPHTTPError(status_code)
    if _is_tap_error(response_bytes):
        raise TAPQueryError(status_code)
    if len(response_bytes) > MAX_RESPONSE_BYTES:
        raise TAPRecordStructureError("TAP response exceeds the 10 MB adapter limit")
    if (
        content_type is None
        or content_type.split(";", maxsplit=1)[0].strip().lower() != "application/json"
    ):
        raise TAPContentTypeError("TAP response content type is not application/json")

    response_sha256 = hashlib.sha256(response_bytes).hexdigest()
    try:
        response_text = response_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise TAPJSONError("TAP response is not valid UTF-8") from exc

    try:
        payload = json.loads(response_text, parse_constant=_reject_json_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        raise TAPJSONError("TAP response is not valid JSON") from exc
    if not isinstance(payload, list):
        if isinstance(payload, dict) and _is_json_tap_error(payload):
            raise TAPQueryError(status_code)
        raise TAPRecordStructureError("TAP JSON response must be an array of records")
    for index, record in enumerate(payload):
        if not isinstance(record, dict):
            raise TAPRecordStructureError(
                f"TAP record at index {index} must be an object"
            )
        if _contains_non_finite_float(record):
            raise TAPRecordStructureError(
                f"TAP record at index {index} contains a non-finite number"
            )
        missing_columns = [name for name in selected_columns if name not in record]
        if missing_columns:
            raise TAPRecordStructureError(
                f"TAP record at index {index} is missing selected columns"
            )

    duplicate = _has_duplicate_identity(payload, identity_fields)
    if duplicate:
        raise TAPRecordStructureError("TAP response contains duplicate row identities")

    try:
        source = DataSource(
            identifier="nasa-exoplanet-archive",
            description="NASA Exoplanet Archive TAP source",
            url=TAP_ENDPOINT,
        )
        provenance = Provenance(
            dataset_id="nasa-exoplanet-archive:ps",
            source=source,
            retrieved_at=retrieved_at,
            data_format=DataFormat.JSON,
            dataset_version=None,
            metadata={
                "tap": {
                    "archive_id": "nasa-exoplanet-archive",
                    "tap_endpoint": TAP_ENDPOINT,
                    "table": "ps",
                    "adql": adql,
                    "requested_format": "json",
                    "response_sha256": response_sha256,
                    "archive_release": None,
                    "citation": {
                        "guidance_url": TAP_CITATION_GUIDANCE_URL,
                        "doi": None,
                    },
                    "ordering": {
                        "fields": list(ordering),
                        "row_identity_fields": list(identity_fields),
                    },
                    "missing_values": {
                        "json_null": "preserved_as_none",
                        "absent_field": "rejected",
                    },
                }
            },
        )
    except (TypeError, ValueError) as exc:
        raise TAPMetadataError("could not construct TAP source provenance") from exc

    try:
        dataset = load_json(response_text, provenance=provenance)
    except DataFormatError as exc:
        raise TAPJSONError("TAP response could not be parsed as JSON records") from exc

    dataset_metadata = {
        "tap": {
            "table_description": None,
            "columns": {
                name: {"description": None, "unit": None, "archive_type": None}
                for name in selected_columns
            },
            "column_metadata_source": None,
        }
    }
    try:
        return Dataset(
            provenance=dataset.provenance,
            records=dataset.records,
            metadata=dataset_metadata,
        )
    except (TypeError, ValueError) as exc:
        raise TAPMetadataError("could not construct TAP dataset metadata") from exc


def _validate_identifiers(values: Sequence[str], *, name: str) -> tuple[str, ...]:
    if (
        isinstance(values, (str, bytes))
        or not isinstance(values, Sequence)
        or not values
    ):
        raise ValueError(f"{name} must be a non-empty sequence of identifiers")
    result = tuple(values)
    if any(
        not isinstance(value, str) or not _IDENTIFIER_PATTERN.fullmatch(value)
        for value in result
    ):
        raise ValueError(f"{name} must contain valid column identifiers")
    if len(set(result)) != len(result):
        raise ValueError(f"{name} must not contain duplicates")
    return result


def _status_code(response: object) -> int:
    status = getattr(response, "status", None)
    if status is None:
        getcode = getattr(response, "getcode", None)
        status = getcode() if callable(getcode) else None
    if not isinstance(status, int):
        raise TAPHTTPError(0)
    return status


def _has_duplicate_identity(
    records: list[dict[str, object]], identity_fields: tuple[str, ...]
) -> bool:
    identities: set[str] = set()
    for index, record in enumerate(records):
        missing_fields = [field for field in identity_fields if field not in record]
        if missing_fields:
            raise TAPRecordStructureError(
                f"TAP record at index {index} is missing row identity fields"
            )
        values = [record[field] for field in identity_fields]
        if any(value is None for value in values):
            raise TAPRecordStructureError(
                f"TAP record at index {index} has a null row identity value"
            )
        try:
            identity = json.dumps(
                values,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise TAPRecordStructureError(
                f"TAP record at index {index} has an invalid row identity value"
            ) from exc
        if identity in identities:
            return True
        identities.add(identity)
    return False


def _contains_non_finite_float(value: object) -> bool:
    pending = [value]
    while pending:
        current = pending.pop()
        if isinstance(current, float):
            if not math.isfinite(current):
                return True
        elif isinstance(current, dict):
            pending.extend(current.values())
        elif isinstance(current, list):
            pending.extend(current)
    return False


def _is_tap_error(response_bytes: bytes) -> bool:
    if not response_bytes:
        return False
    try:
        root = ET.fromstring(response_bytes)
    except ET.ParseError:
        try:
            payload = json.loads(response_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return False
        return isinstance(payload, dict) and _is_json_tap_error(payload)
    for element in root.iter():
        if element.tag.rsplit("}", maxsplit=1)[-1] == "INFO":
            if (
                element.attrib.get("name", "").upper() == "QUERY_STATUS"
                and element.attrib.get("value", "").upper() == "ERROR"
            ):
                return True
    return False


def _is_json_tap_error(payload: dict[str, object]) -> bool:
    query_status = payload.get("QUERY_STATUS", payload.get("query_status"))
    return isinstance(query_status, str) and query_status.upper() == "ERROR"


def _reject_json_constant(value: str) -> NoReturn:
    raise ValueError(f"non-standard JSON constant {value} is not allowed")
