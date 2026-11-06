"""Deterministic, non-mutating dataset quality analysis."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import TypeAlias

from quantum_space_agi.data.models import Dataset, Record
from quantum_space_agi.data.schemas import SchemaValidationReport
from quantum_space_agi.errors import ValidationError

_CanonicalValue: TypeAlias = tuple[object, ...]


@dataclass(frozen=True, slots=True)
class FieldStatistics:
    """Basic statistics for finite numeric values in one field."""

    count: int
    minimum: float
    maximum: float
    mean: float


@dataclass(frozen=True, slots=True)
class DuplicateGroup:
    """Indices of records with identical JSON-compatible values."""

    record_indices: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class DataQualityReport:
    """Counts and summaries computed without modifying dataset records."""

    record_count: int
    missing_values: Mapping[str, int]
    duplicate_groups: tuple[DuplicateGroup, ...]
    invalid_records: tuple[int, ...]
    field_statistics: Mapping[str, FieldStatistics]


def analyze_quality(
    dataset: Dataset,
    *,
    validation_report: SchemaValidationReport | None = None,
) -> DataQualityReport:
    """Summarize missing values, exact duplicates, invalid rows, and numbers.

    A value is missing when its key is absent, its value is ``None``, or it is
    empty/whitespace-only text. Numeric summaries include finite integers and
    floats but exclude booleans. Means use scaled summation to avoid overflow.
    They remain binary64 approximations, so contributions too small relative
    to larger magnitudes may be rounded away.
    """
    field_names = sorted({name for record in dataset.records for name in record})
    missing_values = {
        name: sum(_is_missing(record.get(name)) for record in dataset.records)
        for name in field_names
    }

    duplicate_indices: dict[_CanonicalValue, list[int]] = {}
    for index, record in enumerate(dataset.records):
        key = _canonical_record(record)
        duplicate_indices.setdefault(key, []).append(index)
    duplicate_groups = tuple(
        DuplicateGroup(tuple(indices))
        for indices in duplicate_indices.values()
        if len(indices) > 1
    )

    numeric_values: dict[str, list[float]] = {name: [] for name in field_names}
    for record in dataset.records:
        for name in field_names:
            value = record.get(name)
            if isinstance(value, bool) or not isinstance(value, int | float):
                continue
            try:
                number = float(value)
            except OverflowError:
                continue
            if math.isfinite(number):
                numeric_values[name].append(number)

    statistics = {
        name: FieldStatistics(
            count=len(values),
            minimum=min(values),
            maximum=max(values),
            mean=_finite_mean(values),
        )
        for name, values in numeric_values.items()
        if values
    }
    invalid_records = (
        tuple(item.record_index for item in validation_report.invalid_records)
        if validation_report is not None
        else ()
    )
    return DataQualityReport(
        record_count=len(dataset.records),
        missing_values=MappingProxyType(missing_values),
        duplicate_groups=duplicate_groups,
        invalid_records=invalid_records,
        field_statistics=MappingProxyType(statistics),
    )


def _finite_mean(values: list[float]) -> float:
    count = len(values)
    try:
        mean = math.fsum(value / count for value in values)
    except OverflowError:
        scale = max(abs(value) for value in values)
        normalized_mean = math.fsum(value / scale for value in values) / count
        mean = scale * normalized_mean

    if not math.isfinite(mean):
        raise ArithmeticError("finite input values produced a non-finite mean")
    return mean


def _is_missing(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _canonical_record(record: Record) -> _CanonicalValue:
    return _canonical_value(record)


def _canonical_value(value: object) -> _CanonicalValue:
    if isinstance(value, Mapping):
        return (
            "mapping",
            tuple(
                (key, _canonical_value(item))
                for key, item in sorted(value.items(), key=lambda pair: pair[0])
            ),
        )
    if isinstance(value, list):
        return ("list", tuple(_canonical_value(item) for item in value))
    if value is None:
        return ("none",)
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, int):
        return ("int", value)
    if isinstance(value, float):
        if math.isnan(value):
            return ("float", "nan")
        if math.isinf(value):
            return ("float", "inf" if value > 0 else "-inf")
        return ("float", value)
    if isinstance(value, str):
        return ("str", value)
    raise ValidationError(
        f"quality analysis requires JSON-compatible values, got {type(value).__name__}"
    )
