"""Offline validation of TAP VOTable result completeness metadata."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TypeAlias

from quantum_space_agi.data.models import JSONScalar
from quantum_space_agi.errors import ValidationError

_RESULT_SERIALIZATIONS = frozenset({"TABLEDATA", "BINARY", "BINARY2", "FITS"})
_DTD_OR_ENTITY_DECLARATION = re.compile(rb"<!\s*(?:DOCTYPE|ENTITY)\b", re.IGNORECASE)
_INTEGER_VALUE = re.compile(r"[+-]?[0-9]+\Z")
_FLOAT_VALUE = re.compile(
    r"(?:NaN|[+-]?INF|[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)\Z",
    re.IGNORECASE,
)
VOTABLE_VALIDATOR_VERSION = "arc08-tap-votable-validator/2"
_INTEGER_DATATYPES = frozenset(
    {
        "unsignedByte",
        "short",
        "int",
        "long",
        "unsignedShort",
        "unsignedInt",
        "unsignedLong",
    }
)
_FLOAT_DATATYPES = frozenset({"float", "double"})
_TEXT_DATATYPES = frozenset({"char", "unicodeChar"})
_BOOLEAN_DATATYPE = "boolean"

VOTableScalar: TypeAlias = JSONScalar


class VOTableValidationError(ValidationError):
    """A VOTable document is malformed, incomplete, or ambiguous."""

    def __init__(self, message: str, *, code: str = "invalid_votable") -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class VOTableField:
    """Relevant FIELD schema metadata for a validated result table."""

    name: str
    datatype: str | None
    arraysize: str | None
    unit: str | None
    null_value: str | None


@dataclass(frozen=True, slots=True)
class VOTableValidationResult:
    """Validated structure and query status of one VOTable result table."""

    status: str
    columns: tuple[str, ...]
    serialization: str
    row_count: int | None
    fields: tuple[VOTableField, ...] = ()
    tabledata_rows: tuple[tuple[VOTableScalar, ...], ...] | None = None

    def __post_init__(self) -> None:
        if type(self.status) is not str or self.status != "OK":
            raise VOTableValidationError("validated status must be exactly 'OK'")
        if type(self.columns) is not tuple or any(
            type(column) is not str for column in self.columns
        ):
            raise VOTableValidationError("columns must be a tuple of strings")
        if (
            not self.columns
            or any(not column for column in self.columns)
            or len(set(self.columns)) != len(self.columns)
        ):
            raise VOTableValidationError("columns must be non-empty and unique")
        if type(self.serialization) is not str or (
            self.serialization not in _RESULT_SERIALIZATIONS
        ):
            raise VOTableValidationError("unsupported result serialization")
        if self.row_count is not None and (
            type(self.row_count) is not int or self.row_count < 0
        ):
            raise VOTableValidationError("row_count must be a non-negative integer")
        if (self.serialization == "TABLEDATA") != (self.row_count is not None):
            raise VOTableValidationError(
                "row_count must be present only for TABLEDATA serialization"
            )
        if type(self.fields) is not tuple or any(
            not isinstance(field, VOTableField) for field in self.fields
        ):
            raise VOTableValidationError("fields must contain VOTableField values")
        if self.serialization == "TABLEDATA":
            if (
                self.tabledata_rows is not None
                and len(self.tabledata_rows) != self.row_count
            ):
                raise VOTableValidationError(
                    "TABLEDATA row count does not match parsed rows",
                    code="row_count_mismatch",
                )
        elif self.tabledata_rows is not None:
            raise VOTableValidationError(
                "parsed rows are available only for TABLEDATA serialization"
            )


def validate_tap_votable(
    payload: bytes | str,
    *,
    expected_columns: Sequence[str] | None = None,
    required_columns: Sequence[str] | None = None,
) -> VOTableValidationResult:
    """Validate one complete TAP VOTable result document without network access.

    The query result must contain exactly one primary ``RESOURCE`` of type
    ``results``, one ``TABLE``, the exact expected ``FIELD`` names and order,
    and one initial ``QUERY_STATUS=OK`` before the table. Any further query
    status is rejected, including trailing overflow/error statuses. For
    ``TABLEDATA``, each row is checked against the declared field count. Other
    standard VOTable serializations are structurally checked but not decoded;
    external ``STREAM`` references are rejected because their bytes are not
    part of this offline document.
    """
    if (expected_columns is None) == (required_columns is None):
        raise VOTableValidationError(
            "provide exactly one of expected_columns or required_columns"
        )
    columns_expected = (
        _validate_expected_columns(expected_columns)
        if expected_columns is not None
        else None
    )
    columns_required = (
        _validate_expected_columns(required_columns)
        if required_columns is not None
        else None
    )
    xml_bytes = _validate_payload(payload)
    _reject_dtd_and_entity_declarations(xml_bytes)

    try:
        root = ET.fromstring(xml_bytes)
    except (ET.ParseError, LookupError, ValueError, UnicodeError) as exc:
        raise VOTableValidationError(
            "VOTable XML is malformed or incomplete", code="malformed_votable"
        ) from exc

    root_namespace, root_name = _split_tag(root.tag)
    if root_name != "VOTABLE":
        raise VOTableValidationError("XML root must be a VOTABLE element")

    resource_tag = _qualified_tag(root_namespace, "RESOURCE")
    result_resources = [
        element
        for element in root.iter(resource_tag)
        if element.attrib.get("type") == "results"
    ]
    if len(result_resources) != 1:
        raise VOTableValidationError(
            "VOTable must contain exactly one primary results RESOURCE"
        )

    result_resource = result_resources[0]
    children = list(result_resource)
    table_tag = _qualified_tag(root_namespace, "TABLE")
    tables = [child for child in children if child.tag == table_tag]
    if len(tables) != 1:
        raise VOTableValidationError(
            "primary results RESOURCE must contain exactly one TABLE"
        )
    table = tables[0]
    table_position = children.index(table)

    info_tag = _qualified_tag(root_namespace, "INFO")
    query_status_elements = [
        element
        for element in result_resource.iter(info_tag)
        if element.attrib.get("name") == "QUERY_STATUS"
    ]
    if len(query_status_elements) != 1:
        raise VOTableValidationError(
            "primary results RESOURCE must contain exactly one QUERY_STATUS",
            code="query_status_missing_or_ambiguous",
        )
    query_status = query_status_elements[0]
    if query_status not in children or children.index(query_status) >= table_position:
        raise VOTableValidationError(
            "QUERY_STATUS must be a direct child before the result TABLE",
            code="query_status_placement",
        )
    if query_status.attrib.get("value") != "OK":
        raise VOTableValidationError(
            "initial QUERY_STATUS value must be exactly 'OK'",
            code="query_status_not_ok",
        )

    table_fields = _table_fields(table, root_namespace)
    table_columns = tuple(field.name for field in table_fields)
    if columns_expected is not None and table_columns != columns_expected:
        raise VOTableValidationError(
            "VOTable TABLE columns do not match the expected columns"
        )
    if columns_required is not None:
        missing_columns = tuple(
            column for column in columns_required if column not in table_columns
        )
        if missing_columns:
            raise VOTableValidationError(
                "VOTable TABLE is missing required columns: "
                + ", ".join(missing_columns),
                code="missing_required_columns",
            )

    serialization, parsed_rows = _validate_table_data(
        table, root_namespace, table_fields
    )
    return VOTableValidationResult(
        status="OK",
        columns=table_columns,
        serialization=serialization,
        row_count=len(parsed_rows) if parsed_rows is not None else None,
        fields=table_fields,
        tabledata_rows=parsed_rows,
    )


def _validate_expected_columns(columns: Sequence[str]) -> tuple[str, ...]:
    if isinstance(columns, (str, bytes)) or not isinstance(columns, Sequence):
        raise VOTableValidationError("expected_columns must be a non-empty sequence")
    normalized = tuple(columns)
    if not normalized or any(
        type(column) is not str or not column for column in normalized
    ):
        raise VOTableValidationError("expected_columns must contain non-empty strings")
    if len(set(normalized)) != len(normalized):
        raise VOTableValidationError("expected_columns must be unique")
    return normalized


def _validate_payload(payload: bytes | str) -> bytes:
    if type(payload) is bytes:
        return payload
    if type(payload) is str:
        try:
            return payload.encode("utf-8", errors="strict")
        except UnicodeEncodeError as exc:
            raise VOTableValidationError("VOTable text is not valid Unicode") from exc
    raise VOTableValidationError("payload must be bytes or text")


def _reject_dtd_and_entity_declarations(payload: bytes) -> None:
    # ElementTree does not resolve external entities, but rejecting declarations
    # also prevents input-controlled internal entity expansion.
    declaration_probe = payload.replace(b"\x00", b"")
    if _DTD_OR_ENTITY_DECLARATION.search(declaration_probe):
        raise VOTableValidationError("DTD and entity declarations are not supported")


def _table_fields(table: ET.Element, namespace: str) -> tuple[VOTableField, ...]:
    field_tag = _qualified_tag(namespace, "FIELD")
    field_elements = [child for child in table if child.tag == field_tag]
    names = tuple(field.attrib.get("name", "") for field in field_elements)
    if not names or any(not name for name in names):
        raise VOTableValidationError("result TABLE requires named FIELD elements")
    if len(set(names)) != len(names):
        raise VOTableValidationError(
            "result TABLE FIELD names must be unique", code="duplicate_columns"
        )
    parsed_fields: list[VOTableField] = []
    values_tag = _qualified_tag(namespace, "VALUES")
    for field in field_elements:
        null_elements = [child for child in field if child.tag == values_tag]
        if len(null_elements) > 1:
            raise VOTableValidationError(
                f"FIELD {field.attrib.get('name', '')!r} has ambiguous VALUES metadata"
            )
        null_value = null_elements[0].attrib.get("null") if null_elements else None
        parsed_fields.append(
            VOTableField(
                name=field.attrib.get("name", ""),
                datatype=field.attrib.get("datatype"),
                arraysize=field.attrib.get("arraysize"),
                unit=field.attrib.get("unit"),
                null_value=null_value,
            )
        )
    return tuple(parsed_fields)


def _validate_table_data(
    table: ET.Element, namespace: str, fields: tuple[VOTableField, ...]
) -> tuple[str, tuple[tuple[VOTableScalar, ...], ...] | None]:
    data_tag = _qualified_tag(namespace, "DATA")
    data_elements = [child for child in table if child.tag == data_tag]
    if len(data_elements) != 1:
        raise VOTableValidationError("result TABLE must contain exactly one DATA")

    data = data_elements[0]
    serialization_elements = [
        child
        for child in data
        if _split_tag(child.tag)[0] == namespace
        and _split_tag(child.tag)[1] in _RESULT_SERIALIZATIONS
    ]
    if len(data) != 1 or len(serialization_elements) != 1:
        raise VOTableValidationError(
            "DATA must contain exactly one supported table serialization"
        )

    serialization_element = serialization_elements[0]
    serialization = _split_tag(serialization_element.tag)[1]
    if serialization == "TABLEDATA":
        tr_tag = _qualified_tag(namespace, "TR")
        td_tag = _qualified_tag(namespace, "TD")
        rows = list(serialization_element)
        parsed_rows: list[tuple[VOTableScalar, ...]] = []
        for row in rows:
            if row.tag != tr_tag:
                raise VOTableValidationError("TABLEDATA may contain only TR rows")
            cells = list(row)
            if sum(cell.tag == td_tag for cell in cells) != len(fields) or any(
                cell.tag != td_tag for cell in row
            ):
                raise VOTableValidationError(
                    "TABLEDATA row cell count does not match FIELD count"
                )
            parsed_cells: list[VOTableScalar] = []
            for field, cell in zip(fields, cells, strict=True):
                if list(cell):
                    raise VOTableValidationError(
                        "TABLEDATA cells must contain text only"
                    )
                parsed_cells.append(_decode_cell(field, "".join(cell.itertext())))
            parsed_rows.append(tuple(parsed_cells))
        return serialization, tuple(parsed_rows)

    stream_tag = _qualified_tag(namespace, "STREAM")
    streams = [child for child in serialization_element if child.tag == stream_tag]
    if len(serialization_element) != 1 or len(streams) != 1:
        raise VOTableValidationError(f"{serialization} must contain exactly one STREAM")
    if streams[0].attrib.get("href"):
        raise VOTableValidationError(
            "external VOTable STREAM data cannot be validated offline"
        )
    return serialization, None


def _decode_cell(field: VOTableField, text: str) -> VOTableScalar:
    if field.null_value is not None and text == field.null_value:
        return None
    datatype = field.datatype
    if datatype is None:
        return text
    if datatype in _TEXT_DATATYPES:
        return text
    if field.arraysize is not None:
        raise VOTableValidationError(
            f"array-valued FIELD {field.name!r} cannot be extracted as a scalar",
            code="unsupported_datatype",
        )
    if text == "":
        return None
    if datatype in _INTEGER_DATATYPES:
        if not _INTEGER_VALUE.fullmatch(text):
            raise VOTableValidationError(
                f"FIELD {field.name!r} contains an invalid integer value",
                code="invalid_cell_value",
            )
        try:
            return int(text, 10)
        except ValueError as exc:
            raise VOTableValidationError(
                f"FIELD {field.name!r} contains an invalid integer value",
                code="invalid_cell_value",
            ) from exc
    if datatype in _FLOAT_DATATYPES:
        if not _FLOAT_VALUE.fullmatch(text):
            raise VOTableValidationError(
                f"FIELD {field.name!r} contains an invalid floating-point value",
                code="invalid_cell_value",
            )
        try:
            return float(text)
        except ValueError as exc:
            raise VOTableValidationError(
                f"FIELD {field.name!r} contains an invalid floating-point value",
                code="invalid_cell_value",
            ) from exc
    if datatype == _BOOLEAN_DATATYPE:
        if text in {"T", "1"}:
            return True
        if text in {"F", "0"}:
            return False
        raise VOTableValidationError(
            f"FIELD {field.name!r} contains an invalid boolean value",
            code="invalid_cell_value",
        )
    raise VOTableValidationError(
        f"FIELD {field.name!r} uses unsupported datatype {datatype!r}",
        code="unsupported_datatype",
    )


def _split_tag(tag: str) -> tuple[str, str]:
    if tag.startswith("{"):
        namespace, separator, local_name = tag[1:].partition("}")
        if separator:
            return namespace, local_name
    return "", tag


def _qualified_tag(namespace: str, local_name: str) -> str:
    return f"{{{namespace}}}{local_name}" if namespace else local_name
