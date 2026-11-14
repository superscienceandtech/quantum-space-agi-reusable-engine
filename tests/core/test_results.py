from dataclasses import FrozenInstanceError

import pytest

from quantum_space_agi.core import ErrorInfo, Result, ResultStatus


def test_success_result_preserves_typed_value() -> None:
    result: Result[int] = Result.success(42)

    assert result.status is ResultStatus.SUCCESS
    assert result.is_success
    assert not result.is_failure
    assert result.value == 42


def test_success_result_allows_none_as_value() -> None:
    result: Result[None] = Result.success(None)

    assert result.is_success
    assert result.value is None


def test_failure_result_contains_structured_error() -> None:
    error = ErrorInfo(code="missing-data", message="Required data was not found")
    result: Result[int] = Result.failure(error)

    assert result.status is ResultStatus.FAILURE
    assert result.is_failure
    assert not result.is_success
    assert result.error == error


def test_result_value_is_unavailable_for_failure() -> None:
    result: Result[int] = Result.failure(ErrorInfo("invalid", "Invalid input"))

    with pytest.raises(ValueError, match="successful result"):
        _ = result.value


def test_result_error_is_unavailable_for_success() -> None:
    result: Result[int] = Result.success(1)

    with pytest.raises(ValueError, match="failed result"):
        _ = result.error


@pytest.mark.parametrize(
    ("status", "value", "error"),
    [
        (ResultStatus.SUCCESS, 1, ErrorInfo("invalid", "Invalid state")),
        (ResultStatus.FAILURE, 1, ErrorInfo("invalid", "Invalid state")),
        (ResultStatus.FAILURE, None, None),
        ("success", 1, None),
    ],
)
def test_result_rejects_invalid_state_combinations(
    status: ResultStatus,
    value: object,
    error: ErrorInfo | None,
) -> None:
    with pytest.raises(ValueError):
        Result(status, value, error)


def test_result_rejects_success_state_without_value() -> None:
    with pytest.raises(ValueError):
        Result(ResultStatus.SUCCESS)


def test_result_and_error_info_are_immutable() -> None:
    result = Result.success("ready")
    error = ErrorInfo("unavailable", "Service unavailable")

    with pytest.raises(FrozenInstanceError):
        result.status = ResultStatus.FAILURE  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        error.code = "changed"  # type: ignore[misc]


def test_equal_results_have_predictable_value_equality_and_repr() -> None:
    first = Result.success([1, 2])
    second = Result.success([1, 2])

    assert first == second
    assert repr(first) == "Result(status=<ResultStatus.SUCCESS: 'success'>)"
