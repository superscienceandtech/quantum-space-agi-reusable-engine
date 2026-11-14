"""Offline tests for TAP VOTable completeness validation."""

from __future__ import annotations

import pytest

from quantum_space_agi.ml import (
    VOTableValidationError,
    validate_tap_votable,
)

EXPECTED_COLUMNS = ("pl_name", "pl_rade")


def _table() -> str:
    return (
        "<TABLE>"
        '<FIELD name="pl_name" datatype="char" arraysize="*"/>'
        '<FIELD name="pl_rade" datatype="double"/>'
        "<DATA><TABLEDATA><TR><TD>Planet b</TD><TD>1.0</TD></TR></TABLEDATA></DATA>"
        "</TABLE>"
    )


def _votable(
    resource_contents: str = '<INFO name="QUERY_STATUS" value="OK"/>' + _table(),
    *,
    resources: str | None = None,
) -> str:
    if resources is None:
        resources = f'<RESOURCE type="results">{resource_contents}</RESOURCE>'
    return (
        '<VOTABLE xmlns="http://www.ivoa.net/xml/VOTable/v1.3">'
        f"{resources}</VOTABLE>"
    )


def test_valid_votable_returns_structured_result() -> None:
    result = validate_tap_votable(
        _votable().encode("utf-8"), expected_columns=EXPECTED_COLUMNS
    )

    assert result.status == "OK"
    assert result.columns == EXPECTED_COLUMNS
    assert result.serialization == "TABLEDATA"
    assert result.row_count == 1


def test_unrelated_info_before_and_after_table_is_allowed() -> None:
    contents = (
        '<INFO name="QUERY_STATUS" value="OK"/>'
        '<INFO name="QUERY" value="select ..."/>'
        "<TABLE>"
        '<FIELD name="pl_name" datatype="char" arraysize="*"/>'
        '<FIELD name="pl_rade" datatype="double"/>'
        "<DATA><TABLEDATA/></DATA>"
        "</TABLE>"
        '<INFO name="SERVICE_NOTE" value="complete"/>'
    )
    assert validate_tap_votable(
        _votable(contents), expected_columns=EXPECTED_COLUMNS
    ).row_count == 0


@pytest.mark.parametrize("value", ["OVERFLOW", "ERROR"])
def test_non_ok_initial_status_is_rejected(value: str) -> None:
    resource_contents = (
        f'<INFO name="QUERY_STATUS" value="{value}"/>' + _table()
    )
    with pytest.raises(VOTableValidationError, match="initial QUERY_STATUS"):
        validate_tap_votable(
            _votable(resource_contents), expected_columns=EXPECTED_COLUMNS
        )


@pytest.mark.parametrize("value", ["OVERFLOW", "ERROR"])
def test_trailing_query_status_is_rejected(value: str) -> None:
    contents = _votable().split('<RESOURCE type="results">', 1)[1].split(
        "</RESOURCE>", 1
    )[0]
    contents += f'<INFO name="QUERY_STATUS" value="{value}"/>'
    with pytest.raises(VOTableValidationError, match="exactly one QUERY_STATUS"):
        validate_tap_votable(
            _votable(resources=f'<RESOURCE type="results">{contents}</RESOURCE>'),
            expected_columns=EXPECTED_COLUMNS,
        )


def test_missing_status_is_rejected() -> None:
    with pytest.raises(VOTableValidationError, match="exactly one QUERY_STATUS"):
        validate_tap_votable(
            _votable(_votable().split('<INFO name="QUERY_STATUS" value="OK"/>')[1]
                     .split("</RESOURCE>", 1)[0]),
            expected_columns=EXPECTED_COLUMNS,
        )


def test_duplicate_initial_status_is_rejected() -> None:
    contents = (
        '<INFO name="QUERY_STATUS" value="OK"/>'
        '<INFO name="QUERY_STATUS" value="OK"/>'
        + _table()
    )
    with pytest.raises(VOTableValidationError, match="exactly one QUERY_STATUS"):
        validate_tap_votable(
            _votable(contents), expected_columns=EXPECTED_COLUMNS
        )


def test_status_after_table_is_rejected() -> None:
    contents = _votable().split('<RESOURCE type="results">', 1)[1].split(
        "</RESOURCE>", 1
    )[0]
    contents = contents.replace(
        "</TABLE>", '</TABLE><INFO name="QUERY_STATUS" value="OK"/>'
    )
    with pytest.raises(VOTableValidationError, match="exactly one QUERY_STATUS"):
        validate_tap_votable(
            _votable(resources=f'<RESOURCE type="results">{contents}</RESOURCE>'),
            expected_columns=EXPECTED_COLUMNS,
        )


def test_nested_status_is_rejected_as_ambiguous_placement() -> None:
    contents = (
        '<GROUP><INFO name="QUERY_STATUS" value="OK"/></GROUP>' + _table()
    )
    with pytest.raises(VOTableValidationError, match="direct child before"):
        validate_tap_votable(
            _votable(contents), expected_columns=EXPECTED_COLUMNS
        )


def test_missing_primary_results_resource_is_rejected() -> None:
    resources = '<RESOURCE type="meta">' + _votable().split(
        '<RESOURCE type="results">', 1
    )[1].split("</RESOURCE>", 1)[0] + "</RESOURCE>"
    with pytest.raises(VOTableValidationError, match="exactly one primary"):
        validate_tap_votable(
            _votable(resources=resources), expected_columns=EXPECTED_COLUMNS
        )


def test_multiple_primary_results_resources_are_rejected() -> None:
    result_resource = _votable().split("<VOTABLE", 1)[1].split("</VOTABLE>", 1)[0]
    result_resource = result_resource.split(">", 1)[1]
    with pytest.raises(VOTableValidationError, match="exactly one primary"):
        validate_tap_votable(
            _votable(resources=result_resource + result_resource),
            expected_columns=EXPECTED_COLUMNS,
        )


@pytest.mark.parametrize(
    "contents",
    [
        '<INFO name="QUERY_STATUS" value="OK"/>',
        '<INFO name="QUERY_STATUS" value="OK"/><TABLE></TABLE><TABLE></TABLE>',
    ],
)
def test_missing_or_multiple_result_tables_are_rejected(contents: str) -> None:
    with pytest.raises(VOTableValidationError, match="exactly one TABLE"):
        validate_tap_votable(_votable(contents), expected_columns=EXPECTED_COLUMNS)


def test_missing_data_is_rejected() -> None:
    contents = (
        '<INFO name="QUERY_STATUS" value="OK"/>'
        "<TABLE><FIELD name=\"pl_name\"/><FIELD name=\"pl_rade\"/></TABLE>"
    )
    with pytest.raises(VOTableValidationError, match="exactly one DATA"):
        validate_tap_votable(_votable(contents), expected_columns=EXPECTED_COLUMNS)


def test_unexpected_table_columns_are_rejected() -> None:
    contents = _votable().replace('name="pl_rade"', 'name="pl_mass"')
    with pytest.raises(VOTableValidationError, match="columns do not match"):
        validate_tap_votable(contents, expected_columns=EXPECTED_COLUMNS)


@pytest.mark.parametrize("payload", [b"<VOTABLE>", b"<VOTABLE><RESOURCE></VOTABLE>"])
def test_malformed_and_truncated_xml_are_rejected(payload: bytes) -> None:
    with pytest.raises(VOTableValidationError, match="malformed or incomplete"):
        validate_tap_votable(payload, expected_columns=EXPECTED_COLUMNS)
