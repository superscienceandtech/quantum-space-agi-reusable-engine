"""Tests for the read-only Exoplanet Archive TAP adapter."""

from __future__ import annotations

import hashlib
import io
import json
from email.message import Message
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

import pytest

from quantum_space_agi.data.adapters import exoplanet_archive as adapter


class _Response(io.BytesIO):
    def __init__(
        self,
        body: bytes,
        content_type: str | None,
        content_length: str | None,
    ) -> None:
        super().__init__(body)
        self.headers = Message()
        if content_type is not None:
            self.headers["Content-Type"] = content_type
        if content_length is not None:
            self.headers["Content-Length"] = content_length
        self.status = 200
        self.read_sizes: list[int] = []

    def read(self, size: int = -1) -> bytes:
        self.read_sizes.append(size)
        return super().read(size)

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _response(
    body: bytes,
    content_type: str | None = "application/json",
    content_length: str | None = None,
) -> _Response:
    return _Response(body, content_type, content_length)


def _fetch(monkeypatch: pytest.MonkeyPatch, body: bytes, **kwargs: object):
    monkeypatch.setattr(
        adapter.urllib.request, "urlopen", lambda *args, **kw: _response(body)
    )
    return adapter.fetch_ps_dataset(
        ["pl_name", "pl_refname", "pl_orbper"],
        order_by=["pl_name", "pl_refname"],
        row_identity_fields=["pl_name", "pl_refname"],
        limit=5,
        **kwargs,
    )


def test_valid_json_builds_dataset_and_preserves_json_scalar_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = (
        b'[{"pl_name":"Planet b","pl_refname":"Ref 1",'
        b'"pl_orbper":null,"flag":true,"count":4,"x":1.25}]'
    )

    dataset = _fetch(monkeypatch, body)

    record = dataset.records[0]
    assert record["pl_orbper"] is None
    assert record["flag"] is True
    assert type(record["count"]) is int
    assert type(record["x"]) is float
    assert dataset.provenance.dataset_id == "nasa-exoplanet-archive:ps"
    assert dataset.provenance.source.identifier == "nasa-exoplanet-archive"
    assert dataset.provenance.dataset_version is None


def test_empty_json_array_returns_empty_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset = _fetch(monkeypatch, b"[]")

    assert dataset.records == ()


def test_zero_byte_response_is_reported_as_invalid_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(adapter.TAPJSONError):
        _fetch(monkeypatch, b"")


def test_maximum_100_row_limit_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        {
            "pl_name": f"Planet {index}",
            "pl_refname": f"Reference {index}",
            "pl_orbper": index + 0.5,
        }
        for index in range(100)
    ]
    body = json.dumps(rows).encode("utf-8")
    monkeypatch.setattr(
        adapter.urllib.request, "urlopen", lambda *args, **kwargs: _response(body)
    )

    dataset = adapter.fetch_ps_dataset(
        ["pl_name", "pl_refname", "pl_orbper"],
        order_by=["pl_name", "pl_refname"],
        row_identity_fields=["pl_name", "pl_refname"],
        limit=100,
    )

    assert len(dataset.records) == 100
    assert dataset.provenance.metadata["tap"]["adql"].startswith("SELECT TOP 100 ")


def test_checksum_covers_exact_response_bytes_and_query_is_recorded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = b'[\n {"pl_name":"Planet b","pl_refname":"Ref 1","pl_orbper":2.5}\n]\n'

    dataset = _fetch(monkeypatch, body)
    tap = dataset.provenance.metadata["tap"]

    assert tap["response_sha256"] == hashlib.sha256(body).hexdigest()
    assert tap["adql"] == (
        "SELECT TOP 5 pl_name, pl_refname, pl_orbper FROM ps "
        "ORDER BY pl_name, pl_refname"
    )
    assert tap["requested_format"] == "json"
    assert tap["ordering"] == {
        "fields": ["pl_name", "pl_refname"],
        "row_identity_fields": ["pl_name", "pl_refname"],
    }


def test_unknown_archive_and_column_metadata_are_explicitly_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset = _fetch(
        monkeypatch,
        b'[{"pl_name":"Planet b","pl_refname":"Ref 1","pl_orbper":2.5}]',
    )

    tap = dataset.provenance.metadata["tap"]
    metadata = dataset.metadata["tap"]
    assert tap["archive_release"] is None
    assert tap["citation"]["doi"] is None
    assert metadata["table_description"] is None
    assert metadata["column_metadata_source"] is None
    assert metadata["columns"] == {
        "pl_name": {"description": None, "unit": None, "archive_type": None},
        "pl_refname": {"description": None, "unit": None, "archive_type": None},
        "pl_orbper": {"description": None, "unit": None, "archive_type": None},
    }


def test_query_is_url_encoded_and_timeout_is_forwarded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request: object, *, timeout: float) -> object:
        captured["url"] = request.full_url  # type: ignore[attr-defined]
        captured["timeout"] = timeout
        return _response(
            b'[{"pl_name":"Planet b","pl_refname":"Ref 1","pl_orbper":2.5}]'
        )

    monkeypatch.setattr(adapter.urllib.request, "urlopen", fake_urlopen)
    adapter.fetch_ps_dataset(
        ["pl_name", "pl_refname", "pl_orbper"],
        order_by=["pl_name", "pl_refname"],
        row_identity_fields=["pl_name", "pl_refname"],
        limit=5,
        timeout=7.0,
    )

    query_params = parse_qs(urlsplit(str(captured["url"])).query)
    assert query_params == {
        "query": [
            "SELECT TOP 5 pl_name, pl_refname, pl_orbper FROM ps "
            "ORDER BY pl_name, pl_refname"
        ],
        "format": ["json"],
    }
    assert captured["timeout"] == 7.0


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf"), -float("inf")])
def test_invalid_timeout_fails_before_network_access(
    monkeypatch: pytest.MonkeyPatch, timeout: float
) -> None:
    def unexpected_request(*args: object, **kwargs: object) -> object:
        pytest.fail("invalid timeout must fail before network access")

    monkeypatch.setattr(adapter.urllib.request, "urlopen", unexpected_request)
    with pytest.raises(ValueError, match="timeout"):
        adapter.fetch_ps_dataset(
            ["pl_name"],
            order_by=["pl_name"],
            row_identity_fields=["pl_name"],
            limit=1,
            timeout=timeout,
        )


@pytest.mark.parametrize(
    ("columns", "order_by", "identity", "limit"),
    [
        ([], ["pl_name"], ["pl_name"], 2),
        (["pl_name"], [], ["pl_name"], 2),
        (["pl_name"], ["pl_name"], [], 2),
        (["pl-name"], ["pl-name"], ["pl-name"], 2),
        (["pl_name", "pl_name"], ["pl_name"], ["pl_name"], 2),
        (["pl_name"], ["pl_name", "pl_name"], ["pl_name"], 2),
        (["pl_name"], ["pl_name"], ["pl_name", "pl_name"], 2),
        (["pl_name"], ["pl_name"], ["pl_refname"], 2),
        (["pl_name", "pl_refname"], ["pl_name"], ["pl_refname"], 2),
        (["pl_name"], ["pl_name"], ["pl_name"], 0),
        (["pl_name"], ["pl_name"], ["pl_name"], -1),
        (["pl_name"], ["pl_name"], ["pl_name"], True),
        (["pl_name"], ["pl_name"], ["pl_name"], 1.5),
        (["pl_name"], ["pl_name"], ["pl_name"], 101),
    ],
)
def test_invalid_query_inputs_fail_before_network_access(
    monkeypatch: pytest.MonkeyPatch,
    columns: list[str],
    order_by: list[str],
    identity: list[str],
    limit: object,
) -> None:
    def unexpected_request(*args: object, **kwargs: object) -> object:
        pytest.fail("invalid input must fail before network access")

    monkeypatch.setattr(adapter.urllib.request, "urlopen", unexpected_request)
    with pytest.raises(ValueError):
        adapter.fetch_ps_dataset(
            columns,
            order_by=order_by,
            row_identity_fields=identity,
            limit=limit,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("content_type", [None, "text/plain", "text/csv"])
def test_missing_or_unexpected_content_type_is_rejected(
    monkeypatch: pytest.MonkeyPatch, content_type: str | None
) -> None:
    monkeypatch.setattr(
        adapter.urllib.request,
        "urlopen",
        lambda *args, **kwargs: _response(b"[]", content_type),
    )

    with pytest.raises(adapter.TAPContentTypeError):
        adapter.fetch_ps_dataset(
            ["pl_name"],
            order_by=["pl_name"],
            row_identity_fields=["pl_name"],
            limit=2,
        )


def test_json_content_type_parameters_are_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        adapter.urllib.request,
        "urlopen",
        lambda *args, **kwargs: _response(b"[]", "application/json; charset=utf-8"),
    )

    dataset = adapter.fetch_ps_dataset(
        ["pl_name"],
        order_by=["pl_name"],
        row_identity_fields=["pl_name"],
        limit=1,
    )

    assert dataset.records == ()


def test_invalid_utf8_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(adapter.TAPJSONError):
        _fetch(monkeypatch, b"\xff")


@pytest.mark.parametrize("body", [b"{", b"[NaN]"])
def test_invalid_json_is_reported(monkeypatch: pytest.MonkeyPatch, body: bytes) -> None:
    with pytest.raises(adapter.TAPJSONError):
        _fetch(monkeypatch, body)


@pytest.mark.parametrize("body", [b"{}", b"null", b"[1]"])
def test_invalid_json_record_structure_is_reported(
    monkeypatch: pytest.MonkeyPatch, body: bytes
) -> None:
    with pytest.raises(adapter.TAPRecordStructureError):
        _fetch(monkeypatch, body)


def test_record_missing_selected_column_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(adapter.TAPRecordStructureError):
        _fetch(monkeypatch, b'[{"pl_name":"Planet b","pl_refname":"Ref 1"}]')


def test_duplicate_declared_identity_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = (
        b'[{"pl_name":"Planet b","pl_refname":"Ref 1","pl_orbper":2.5},'
        b'{"pl_name":"Planet b","pl_refname":"Ref 1","pl_orbper":3.5}]'
    )

    with pytest.raises(adapter.TAPRecordStructureError, match="duplicate"):
        _fetch(monkeypatch, body)


@pytest.mark.parametrize(
    "content_length",
    [None, "1", str(20 * 1024 * 1024)],
    ids=["missing", "incorrectly-small", "incorrectly-large"],
)
def test_oversized_response_is_rejected_after_a_bounded_read(
    monkeypatch: pytest.MonkeyPatch, content_length: str | None
) -> None:
    response_body = b" " * (adapter.MAX_RESPONSE_BYTES + 1)
    response = _response(response_body, content_length=content_length)
    monkeypatch.setattr(adapter.urllib.request, "urlopen", lambda *a, **k: response)

    with pytest.raises(adapter.TAPRecordStructureError, match="10 MB"):
        adapter.fetch_ps_dataset(
            ["pl_name"],
            order_by=["pl_name"],
            row_identity_fields=["pl_name"],
            limit=1,
        )

    assert response.read_sizes == [adapter.MAX_RESPONSE_BYTES + 1]


def test_incorrectly_large_content_length_does_not_override_actual_body_size(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = _response(b"[]", content_length=str(20 * 1024 * 1024))
    monkeypatch.setattr(adapter.urllib.request, "urlopen", lambda *a, **k: response)

    dataset = adapter.fetch_ps_dataset(
        ["pl_name"],
        order_by=["pl_name"],
        row_identity_fields=["pl_name"],
        limit=1,
    )

    assert dataset.records == ()
    assert response.read_sizes == [adapter.MAX_RESPONSE_BYTES + 1]


@pytest.mark.parametrize("value", ["1e999", "-1e999"])
def test_numeric_overflow_in_non_identity_field_is_rejected(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    body = (
        f'[{{"pl_name":"Planet b","pl_refname":"Ref 1","pl_orbper":{value}}}]'
    ).encode()

    with pytest.raises(adapter.TAPRecordStructureError):
        _fetch(monkeypatch, body)


def test_numeric_overflow_in_identity_field_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = b'[{"pl_name":1e999,"pl_refname":"Ref 1","pl_orbper":2.5}]'

    with pytest.raises(adapter.TAPRecordStructureError):
        _fetch(monkeypatch, body)


def test_finite_integer_and_float_values_remain_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset = _fetch(
        monkeypatch,
        b'[{"pl_name":"Planet b","pl_refname":"Ref 1","pl_orbper":2.5,"count":7}]',
    )

    assert dataset.records[0]["pl_orbper"] == 2.5
    assert type(dataset.records[0]["pl_orbper"]) is float
    assert dataset.records[0]["count"] == 7
    assert type(dataset.records[0]["count"]) is int


def test_non_finite_numeric_value_nested_in_record_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = b'[{"pl_name":"Planet b","pl_refname":"Ref 1","details":{"values":[1e999]}}]'

    with pytest.raises(adapter.TAPRecordStructureError):
        _fetch(monkeypatch, body)


def test_null_row_identity_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = b'[{"pl_name":"Planet b","pl_refname":null,"pl_orbper":2.5}]'

    with pytest.raises(adapter.TAPRecordStructureError, match="null"):
        _fetch(monkeypatch, body)


def test_duplicate_null_row_identities_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = (
        b'[{"pl_name":"Planet b","pl_refname":null,"pl_orbper":2.5},'
        b'{"pl_name":"Planet b","pl_refname":null,"pl_orbper":3.5}]'
    )

    with pytest.raises(adapter.TAPRecordStructureError, match="null"):
        _fetch(monkeypatch, body)


def test_identity_values_keep_distinct_json_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = b'[{"pl_name":1},{"pl_name":1.0},{"pl_name":true}]'
    monkeypatch.setattr(
        adapter.urllib.request, "urlopen", lambda *a, **k: _response(body)
    )

    dataset = adapter.fetch_ps_dataset(
        ["pl_name"],
        order_by=["pl_name"],
        row_identity_fields=["pl_name"],
        limit=3,
    )

    values = [record["pl_name"] for record in dataset.records]
    assert [type(value) for value in values] == [int, float, bool]


def test_retrieval_timestamp_is_captured_immediately_after_bounded_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = _response(
        b'[{"pl_name":"Planet b","pl_refname":"Ref 1","pl_orbper":2.5}]'
    )
    monkeypatch.setattr(adapter.urllib.request, "urlopen", lambda *a, **k: response)
    timestamp = adapter.datetime(2026, 11, 7, tzinfo=adapter.UTC)
    clock_called = False

    class Clock:
        @staticmethod
        def now(tz: object = None) -> object:
            nonlocal clock_called
            assert response.read_sizes == [adapter.MAX_RESPONSE_BYTES + 1]
            assert tz is adapter.UTC
            clock_called = True
            return timestamp

    is_tap_error = adapter._is_tap_error

    def check_timestamp_precedes_response_parsing(body: bytes) -> bool:
        assert clock_called
        return is_tap_error(body)

    monkeypatch.setattr(adapter, "datetime", Clock)
    monkeypatch.setattr(
        adapter, "_is_tap_error", check_timestamp_precedes_response_parsing
    )

    dataset = adapter.fetch_ps_dataset(
        ["pl_name", "pl_refname", "pl_orbper"],
        order_by=["pl_name", "pl_refname"],
        row_identity_fields=["pl_name", "pl_refname"],
        limit=1,
    )

    assert dataset.provenance.retrieved_at is timestamp


def test_success_json_tap_error_payload_is_query_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        adapter.urllib.request,
        "urlopen",
        lambda *a, **k: _response(b'{"QUERY_STATUS":"ERROR"}'),
    )

    with pytest.raises(adapter.TAPQueryError):
        adapter.fetch_ps_dataset(
            ["pl_name"],
            order_by=["pl_name"],
            row_identity_fields=["pl_name"],
            limit=1,
        )


def test_response_over_10_mb_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    body = b" " * (10 * 1024 * 1024 + 1)

    with pytest.raises(adapter.TAPRecordStructureError, match="10 MB"):
        _fetch(monkeypatch, body)


def test_http_failure_retains_status_without_response_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failure = HTTPError(
        adapter.TAP_ENDPOINT,
        503,
        "unavailable",
        Message(),
        io.BytesIO(b"private server response"),
    )
    monkeypatch.setattr(
        adapter.urllib.request, "urlopen", lambda *a, **k: _raise(failure)
    )

    with pytest.raises(adapter.TAPHTTPError) as error:
        adapter.fetch_ps_dataset(
            ["pl_name", "pl_refname", "pl_orbper"],
            order_by=["pl_name", "pl_refname"],
            row_identity_fields=["pl_name", "pl_refname"],
            limit=5,
        )

    assert error.value.status_code == 503
    assert "private server response" not in str(error.value)


def _raise(error: Exception) -> object:
    raise error


@pytest.mark.parametrize("failure", [URLError("offline"), TimeoutError("timed out")])
def test_network_failure_maps_to_transport_error_without_retry(
    monkeypatch: pytest.MonkeyPatch, failure: Exception
) -> None:
    calls = 0

    def fail(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        raise failure

    monkeypatch.setattr(adapter.urllib.request, "urlopen", fail)
    with pytest.raises(adapter.TAPTransportError):
        adapter.fetch_ps_dataset(
            ["pl_name"],
            order_by=["pl_name"],
            row_identity_fields=["pl_name"],
            limit=1,
        )

    assert calls == 1


def test_recognizable_tap_votable_error_is_classified_as_query_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = HTTPError(
        adapter.TAP_ENDPOINT,
        400,
        "bad query",
        Message(),
        io.BytesIO(
            b'<VOTABLE><INFO name="QUERY_STATUS" value="ERROR">'
            b"bad ADQL</INFO></VOTABLE>"
        ),
    )
    monkeypatch.setattr(
        adapter.urllib.request, "urlopen", lambda *a, **k: _raise(error)
    )

    with pytest.raises(adapter.TAPQueryError):
        adapter.fetch_ps_dataset(
            ["pl_name", "pl_refname", "pl_orbper"],
            order_by=["pl_name", "pl_refname"],
            row_identity_fields=["pl_name", "pl_refname"],
            limit=5,
        )


def test_non_tap_xml_http_error_is_not_classified_as_query_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = HTTPError(
        adapter.TAP_ENDPOINT,
        500,
        "server error",
        Message(),
        io.BytesIO(b"<html>failure</html>"),
    )
    monkeypatch.setattr(
        adapter.urllib.request, "urlopen", lambda *a, **k: _raise(error)
    )

    with pytest.raises(adapter.TAPHTTPError):
        adapter.fetch_ps_dataset(
            ["pl_name", "pl_refname", "pl_orbper"],
            order_by=["pl_name", "pl_refname"],
            row_identity_fields=["pl_name", "pl_refname"],
            limit=5,
        )


def test_success_response_with_tap_error_xml_is_classified_before_content_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = b'<VOTABLE><INFO name="QUERY_STATUS" value="ERROR">bad ADQL</INFO></VOTABLE>'
    monkeypatch.setattr(
        adapter.urllib.request,
        "urlopen",
        lambda *args, **kwargs: _response(body, "application/xml"),
    )

    with pytest.raises(adapter.TAPQueryError):
        adapter.fetch_ps_dataset(
            ["pl_name", "pl_refname", "pl_orbper"],
            order_by=["pl_name", "pl_refname"],
            row_identity_fields=["pl_name", "pl_refname"],
            limit=5,
        )


def test_generic_json_error_is_not_classified_as_tap_query_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        adapter.urllib.request,
        "urlopen",
        lambda *args, **kwargs: _response(b'{"error":"unauthorized"}'),
    )

    with pytest.raises(adapter.TAPRecordStructureError):
        adapter.fetch_ps_dataset(
            ["pl_name"],
            order_by=["pl_name"],
            row_identity_fields=["pl_name"],
            limit=1,
        )


def test_metadata_construction_error_is_chained(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_source(*args: object, **kwargs: object) -> object:
        raise ValueError("bad source metadata")

    monkeypatch.setattr(adapter, "DataSource", fail_source)
    with pytest.raises(adapter.TAPMetadataError) as error:
        _fetch(
            monkeypatch,
            b'[{"pl_name":"Planet b","pl_refname":"Ref 1","pl_orbper":2.5}]',
        )

    assert isinstance(error.value.__cause__, ValueError)
