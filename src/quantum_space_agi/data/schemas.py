"""Small declarative schemas and non-mutating validation reports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from quantum_space_agi.core.validation import validate_non_empty_text
from quantum_space_agi.data.models import Dataset
from quantum_space_agi.errors import ValidationError

SchemaType: TypeAlias = type[object]


@dataclass(frozen=True, slots=True)
class FieldSchema:
    """Type and presence constraints for one record field."""

    name: str
    value_type: SchemaType
    required: bool = True
    allow_none: bool = False

    def __post_init__(self) -> None:
        validate_non_empty_text(self.name, name="field name")
        if not isinstance(self.value_type, type):
            raise ValidationError("value_type must be a type")
        if not isinstance(self.required, bool):
            raise ValidationError("required must be a boolean")
        if not isinstance(self.allow_none, bool):
            raise ValidationError("allow_none must be a boolean")


@dataclass(frozen=True, slots=True)
class DataSchema:
    """Versioned schema for validating dataset records."""

    identifier: str
    version: str
    fields: tuple[FieldSchema, ...]

    def __post_init__(self) -> None:
        validate_non_empty_text(self.identifier, name="schema identifier")
        validate_non_empty_text(self.version, name="schema version")
        normalized_fields = tuple(self.fields)
        if any(not isinstance(item, FieldSchema) for item in normalized_fields):
            raise ValidationError("fields must contain FieldSchema values")
        names = [item.name for item in normalized_fields]
        if len(set(names)) != len(names):
            raise ValidationError("schema field names must be unique")
        object.__setattr__(self, "fields", normalized_fields)


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One field-level schema validation issue."""

    field: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class InvalidRecord:
    """A record index and all schema issues found in that record."""

    record_index: int
    issues: tuple[ValidationIssue, ...]


@dataclass(frozen=True, slots=True)
class SchemaValidationReport:
    """Validation counts and invalid records without altering source data."""

    schema_id: str
    schema_version: str
    record_count: int
    valid_count: int
    invalid_records: tuple[InvalidRecord, ...]

    @property
    def is_valid(self) -> bool:
        """Whether every record satisfies the schema."""
        return not self.invalid_records


def validate_dataset(dataset: Dataset, schema: DataSchema) -> SchemaValidationReport:
    """Report all declared-field issues without coercing or dropping records."""
    invalid_records: list[InvalidRecord] = []
    for record_index, record in enumerate(dataset.records):
        issues: list[ValidationIssue] = []
        for field in schema.fields:
            if field.name not in record:
                if field.required:
                    issues.append(
                        ValidationIssue(
                            field.name,
                            "missing",
                            f"required field {field.name!r} is missing",
                        )
                    )
                continue

            value = record[field.name]
            if value is None:
                if not field.allow_none:
                    issues.append(
                        ValidationIssue(
                            field.name,
                            "null",
                            f"field {field.name!r} must not be null",
                        )
                    )
            elif type(value) is not field.value_type:
                issues.append(
                    ValidationIssue(
                        field.name,
                        "type",
                        f"field {field.name!r} must be {field.value_type.__name__}",
                    )
                )
        if issues:
            invalid_records.append(InvalidRecord(record_index, tuple(issues)))

    return SchemaValidationReport(
        schema_id=schema.identifier,
        schema_version=schema.version,
        record_count=len(dataset.records),
        valid_count=len(dataset.records) - len(invalid_records),
        invalid_records=tuple(invalid_records),
    )
