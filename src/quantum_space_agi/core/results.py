"""Immutable result values for expected success and failure outcomes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar, cast

T = TypeVar("T")
_UNSET = object()


class ResultStatus(Enum):
    """The explicit state of a :class:`Result`."""

    SUCCESS = "success"
    FAILURE = "failure"


@dataclass(frozen=True, slots=True)
class ErrorInfo:
    """A compact, serializable description of an expected failure."""

    code: str
    message: str


@dataclass(frozen=True, slots=True)
class Result(Generic[T]):
    """An immutable success value or structured expected failure.

    Use a result for an expected alternative outcome in normal control flow.
    Raise an exception for invalid state, programmer errors, and exceptional
    conditions that callers are not expected to handle as ordinary outcomes.
    """

    status: ResultStatus
    _value: object = field(default=_UNSET, repr=False)
    _error: ErrorInfo | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.status, ResultStatus):
            raise ValueError("status must be a ResultStatus")
        if self.status is ResultStatus.SUCCESS:
            if self._value is _UNSET or self._error is not None:
                raise ValueError("a successful result requires a value and no error")
        elif self._value is not _UNSET or not isinstance(self._error, ErrorInfo):
            raise ValueError("a failed result requires an error and no value")

    @classmethod
    def success(cls, value: T) -> Result[T]:
        """Create a successful result; ``None`` is a valid value."""
        return cls(ResultStatus.SUCCESS, _value=value)

    @classmethod
    def failure(cls, error: ErrorInfo) -> Result[T]:
        """Create a failed result from structured error information."""
        return cls(ResultStatus.FAILURE, _error=error)

    @property
    def is_success(self) -> bool:
        """Whether the result contains a successful value."""
        return self.status is ResultStatus.SUCCESS

    @property
    def is_failure(self) -> bool:
        """Whether the result contains a failure."""
        return self.status is ResultStatus.FAILURE

    @property
    def value(self) -> T:
        """Return the successful value or raise ``ValueError`` on failure."""
        if self.is_failure:
            raise ValueError("value is only available from a successful result")
        return cast(T, self._value)

    @property
    def error(self) -> ErrorInfo:
        """Return failure information or raise ``ValueError`` on success."""
        if self.is_success:
            raise ValueError("error is only available from a failed result")
        return cast(ErrorInfo, self._error)
