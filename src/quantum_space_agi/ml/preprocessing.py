"""Explicit, deterministic preprocessing for structured datasets."""

from __future__ import annotations

import copy
import json
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Literal

from quantum_space_agi.data import Dataset
from quantum_space_agi.data.models import JSONValue

FieldPolicy = Literal["preserve", "error"]
_INTEGER_PATTERN = re.compile(r"[+-]?[0-9]+\Z")


class PreprocessingError(ValueError):
    """A configured preprocessing operation could not be applied."""

    def __init__(self, record_index: int, field_name: str, reason: str) -> None:
        self.record_index = record_index
        self.field_name = field_name
        super().__init__(
            f"Preprocessing failed for field {field_name!r} at record index "
            f"{record_index}: {reason}."
        )


@dataclass(frozen=True, slots=True)
class FieldConversion:
    """An explicit scalar conversion and policies for absent or null values."""

    field_name: str
    target_type: type[int] | type[float]
    absent_policy: FieldPolicy
    null_policy: FieldPolicy

    def __post_init__(self) -> None:
        if not isinstance(self.field_name, str) or not self.field_name.strip():
            raise ValueError("field_name must be a non-empty string")
        if self.target_type is not int and self.target_type is not float:
            raise ValueError("target_type must be int or float")
        if self.absent_policy not in ("preserve", "error"):
            raise ValueError("absent_policy must be 'preserve' or 'error'")
        if self.null_policy not in ("preserve", "error"):
            raise ValueError("null_policy must be 'preserve' or 'error'")


def preprocess_dataset(
    dataset: Dataset,
    *,
    conversions: Sequence[FieldConversion],
) -> Dataset:
    """Apply declared scalar conversions, returning a provenance-linked copy.

    Record indexes in :class:`PreprocessingError` are zero-based. Integer string
    conversion accepts an optional sign and ASCII base-10 digits, with no
    whitespace or separators. Float conversion accepts finite integers, floats,
    and strings accepted by :class:`float` when the result is finite. Booleans
    are never treated as numbers.
    """
    if not isinstance(dataset, Dataset):
        raise TypeError("dataset must be a Dataset")
    normalized_conversions = _validate_conversions(conversions)

    records: list[dict[str, JSONValue]] = []
    for record_index, source_record in enumerate(dataset.records):
        record = {name: copy.deepcopy(value) for name, value in source_record.items()}
        for conversion in normalized_conversions:
            if conversion.field_name not in record:
                if conversion.absent_policy == "error":
                    raise PreprocessingError(
                        record_index, conversion.field_name, "field is absent"
                    )
                continue

            value = record[conversion.field_name]
            if value is None:
                if conversion.null_policy == "error":
                    raise PreprocessingError(
                        record_index, conversion.field_name, "value is null"
                    )
                continue

            record[conversion.field_name] = _convert_value(
                value, conversion, record_index
            )
        records.append(record)

    provenance = dataset.provenance
    copied_source = replace(
        provenance.source,
        metadata=copy.deepcopy(dict(provenance.source.metadata)),
    )
    copied_provenance = replace(
        provenance,
        source=copied_source,
        transformations=(
            *provenance.transformations,
            _transformation_description(normalized_conversions),
        ),
        metadata=copy.deepcopy(dict(provenance.metadata)),
    )
    return Dataset(
        provenance=copied_provenance,
        records=records,
        metadata=copy.deepcopy(dict(dataset.metadata)),
    )


def _validate_conversions(
    conversions: Sequence[FieldConversion],
) -> tuple[FieldConversion, ...]:
    if isinstance(conversions, (str, bytes)) or not isinstance(conversions, Sequence):
        raise TypeError("conversions must be a sequence of FieldConversion values")

    validated: list[FieldConversion] = []
    seen_fields: set[str] = set()
    for conversion in conversions:
        if not isinstance(conversion, FieldConversion):
            raise TypeError("conversions must contain FieldConversion values")
        if conversion.field_name in seen_fields:
            raise ValueError(
                f"duplicate conversion for field {conversion.field_name!r}"
            )
        seen_fields.add(conversion.field_name)
        validated.append(conversion)
    return tuple(validated)


def _convert_value(
    value: JSONValue,
    conversion: FieldConversion,
    record_index: int,
) -> int | float:
    if isinstance(value, bool):
        raise PreprocessingError(
            record_index, conversion.field_name, "boolean is not a numeric value"
        )

    try:
        if conversion.target_type is int:
            if type(value) is int:
                return value
            if not isinstance(value, str) or not _INTEGER_PATTERN.fullmatch(value):
                raise ValueError
            return int(value, 10)

        if type(value) is int or type(value) is float or isinstance(value, str):
            numeric_value = value
        else:
            raise ValueError
        converted = float(numeric_value)
        if not math.isfinite(converted):
            raise ValueError
        return converted
    except (OverflowError, TypeError, ValueError) as exc:
        raise PreprocessingError(
            record_index,
            conversion.field_name,
            f"value cannot be converted to {conversion.target_type.__name__}",
        ) from exc


def _transformation_description(
    conversions: Sequence[FieldConversion],
) -> str:
    description = [
        {
            "absent_policy": conversion.absent_policy,
            "field_name": conversion.field_name,
            "null_policy": conversion.null_policy,
            "target_type": conversion.target_type.__name__,
        }
        for conversion in sorted(conversions, key=lambda item: item.field_name)
    ]
    serialized = json.dumps(description, sort_keys=True, separators=(",", ":"))
    return f"preprocess_dataset:{serialized}"
