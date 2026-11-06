import copy
import json
import tempfile
import unittest
from pathlib import Path

from quantum_space_agi.data import load_dataset
from quantum_space_agi.data.validator import (
    SchemaDefinitionError,
    validate_dataset,
)


class DataValidationTests(unittest.TestCase):
    def setUp(self):
        self.schema = {
            "schema_name": "test-record",
            "fields": {
                "name": {"type": "string", "required": True, "nullable": False},
                "count": {"type": "integer", "required": True, "nullable": False},
                "ratio": {"type": "float", "required": False, "nullable": True},
                "active": {"type": "boolean", "required": False, "nullable": False},
                "tags": {"type": "array", "required": False, "nullable": False},
                "details": {"type": "object", "required": False, "nullable": False},
            },
            "allow_unexpected_fields": False,
        }

    def issue_categories(self, report):
        return [issue.category for issue in report.errors + report.warnings]

    def test_accepts_valid_values_for_supported_types(self):
        records = [
            {
                "name": "sensor",
                "count": 3,
                "ratio": 1.25,
                "active": True,
                "tags": ["a"],
                "details": {"source": "example"},
            }
        ]
        report = validate_dataset(records, self.schema)
        self.assertTrue(report.is_valid)
        self.assertEqual(report.total_records, 1)
        self.assertEqual(report.valid_records, 1)
        self.assertEqual(report.invalid_records, 0)

    def test_accepts_csv_numeric_strings_without_converting_values(self):
        report = validate_dataset(
            [{"name": "sensor", "count": "3", "ratio": "1.25"}], self.schema
        )
        self.assertTrue(report.is_valid)

    def test_missing_required_field_is_reported_one_based(self):
        report = validate_dataset([{"count": "3"}], self.schema)
        issue = next(
            issue for issue in report.errors if issue.category == "missing_required"
        )
        self.assertEqual(issue.record_index, 1)
        self.assertEqual(issue.field_name, "name")

    def test_unexpected_fields_follow_schema_policy(self):
        record = {"name": "x", "count": 1, "extra": True}
        report = validate_dataset([record], self.schema)
        self.assertIn("unexpected_field", self.issue_categories(report))
        permissive = {**self.schema, "allow_unexpected_fields": True}
        self.assertTrue(validate_dataset([record], permissive).is_valid)

    def test_empty_record_is_invalid(self):
        report = validate_dataset([{}], self.schema)
        self.assertIn("empty_record", self.issue_categories(report))

    def test_empty_dataset_is_invalid(self):
        report = validate_dataset([], self.schema)
        self.assertFalse(report.is_valid)
        self.assertEqual(report.total_records, 0)
        self.assertIn("empty_dataset", self.issue_categories(report))

    def test_invalid_values_for_each_type_are_reported(self):
        record = {
            "name": 7,
            "count": "2.0",
            "ratio": "NaN",
            "active": "yes",
            "tags": {},
            "details": [],
        }
        report = validate_dataset([record], self.schema)
        issues = [issue for issue in report.errors if issue.category == "type_mismatch"]
        self.assertEqual({issue.field_name for issue in issues}, set(record))

    def test_boolean_is_not_accepted_as_integer_or_float(self):
        schema = {
            "schema_name": "numeric",
            "fields": {
                "count": {"type": "integer", "required": True},
                "value": {"type": "float", "required": True},
            },
        }
        report = validate_dataset([{"count": True, "value": False}], schema)
        self.assertEqual(
            len([i for i in report.errors if i.category == "type_mismatch"]), 2
        )

    def test_json_float_is_not_accepted_for_integer_field(self):
        report = validate_dataset([{"name": "x", "count": 3.0}], self.schema)
        self.assertTrue(
            any(
                issue.category == "type_mismatch" and issue.field_name == "count"
                for issue in report.errors
            )
        )

    def test_json_null_requires_nullable_field(self):
        report = validate_dataset([{"name": None, "count": 1}], self.schema)
        issue = next(issue for issue in report.errors if issue.field_name == "name")
        self.assertEqual(issue.category, "null_not_allowed")
        nullable = copy.deepcopy(self.schema)
        nullable["fields"]["name"]["nullable"] = True
        self.assertTrue(
            validate_dataset([{"name": None, "count": 1}], nullable).is_valid
        )

    def test_absent_null_empty_and_whitespace_values_are_distinct(self):
        schema = {
            "schema_name": "missing",
            "fields": {
                "required": {"type": "string", "required": True},
                "empty": {
                    "type": "string",
                    "required": False,
                    "allow_empty_string": False,
                },
                "space": {
                    "type": "string",
                    "required": False,
                    "whitespace_only_is_missing": True,
                },
                "nullable": {"type": "string", "required": False, "nullable": True},
            },
        }
        report = validate_dataset(
            [{"empty": "", "space": "   ", "nullable": None}], schema
        )
        self.assertEqual(
            {issue.category for issue in report.errors},
            {"missing_required", "empty_string", "whitespace_only"},
        )

    def test_min_max_allowed_values_and_string_lengths(self):
        schema = {
            "schema_name": "constraints",
            "fields": {
                "value": {
                    "type": "float",
                    "required": True,
                    "minimum": 1,
                    "maximum": 5,
                },
                "mode": {
                    "type": "string",
                    "required": True,
                    "allowed_values": ["safe", "fast"],
                },
                "label": {
                    "type": "string",
                    "required": True,
                    "min_length": 2,
                    "max_length": 4,
                },
            },
        }
        report = validate_dataset(
            [
                {"value": "0", "mode": "turbo", "label": "a"},
                {"value": "6", "mode": "fast", "label": "a long label"},
            ],
            schema,
        )
        self.assertEqual(
            {issue.category for issue in report.errors},
            {
                "minimum_violation",
                "maximum_violation",
                "allowed_value",
                "min_length",
                "max_length",
            },
        )

    def test_duplicate_detection_is_warning_only_and_does_not_remove_records(self):
        schema = {
            "schema_name": "duplicates",
            "fields": {
                "key": {"type": "string", "required": True},
            },
            "duplicate_detection": {
                "enabled": True,
                "strategy": "fields",
                "fields": ["key"],
            },
        }
        records = [{"key": "a"}, {"key": "a"}]
        report = validate_dataset(records, schema)
        self.assertTrue(report.is_valid)
        self.assertEqual(report.total_records, 2)
        self.assertEqual(len(report.warnings), 1)
        self.assertEqual(report.warnings[0].record_index, 2)
        self.assertEqual(len(records), 2)

    def test_duplicate_detection_can_be_disabled(self):
        schema = {
            "schema_name": "duplicates",
            "fields": {
                "key": {"type": "string", "required": True},
            },
            "duplicate_detection": {"enabled": False},
        }
        report = validate_dataset([{"key": "a"}, {"key": "a"}], schema)
        self.assertEqual(report.warnings, ())

    def test_all_fields_duplicate_strategy(self):
        schema = {
            "schema_name": "duplicates",
            "fields": {
                "key": {"type": "string", "required": True},
            },
            "duplicate_detection": {"enabled": True, "strategy": "all_fields"},
        }
        report = validate_dataset(
            [{"key": "a"}, {"key": "a"}, {"key": "a", "x": 1}], schema
        )
        self.assertEqual(
            len([i for i in report.warnings if i.category == "duplicate_record"]), 1
        )

    def test_actual_values_are_hidden_unless_requested(self):
        record = {"name": "private-value", "count": "bad"}
        hidden = validate_dataset([record], self.schema)
        shown = validate_dataset([record], self.schema, include_actual_values=True)
        issue = next(issue for issue in hidden.errors if issue.field_name == "count")
        shown_issue = next(
            issue for issue in shown.errors if issue.field_name == "count"
        )
        self.assertIsNone(issue.actual_value)
        self.assertEqual(shown_issue.actual_value, "bad")

    def test_dataset_id_mismatch_is_reported(self):
        dataset = {"dataset_id": "actual", "records": [{"name": "x", "count": 1}]}
        schema = {**self.schema, "dataset_id": "expected"}
        report = validate_dataset(dataset, schema)
        self.assertIn("dataset_id_mismatch", self.issue_categories(report))

    def test_invalid_schema_raises_schema_definition_error(self):
        with self.assertRaises(SchemaDefinitionError):
            validate_dataset(
                [],
                {
                    "schema_name": "bad",
                    "fields": {
                        "x": {"type": "date", "required": True},
                    },
                },
            )

    def test_unhashable_schema_type_raises_schema_definition_error(self):
        with self.assertRaises(SchemaDefinitionError):
            validate_dataset(
                [],
                {
                    "schema_name": "bad",
                    "fields": {
                        "x": {"type": [], "required": True},
                    },
                },
            )

    def test_csv_loader_then_validation_and_source_unchanged(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "records.csv"
            original = b"record_id,value\nEX-1,12.5\n"
            path.write_bytes(original)
            loaded = load_dataset(path)
            schema = {
                "schema_name": "csv",
                "fields": {
                    "record_id": {"type": "string", "required": True},
                    "value": {"type": "float", "required": True},
                },
            }
            report = validate_dataset(loaded, schema)
            self.assertTrue(report.is_valid)
            self.assertEqual(path.read_bytes(), original)

    def test_json_loader_then_validation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "records.json"
            original = b'[{"name":"x","count":2}]'
            path.write_bytes(original)
            loaded = load_dataset(path)
            report = validate_dataset(loaded, self.schema)
            self.assertTrue(report.is_valid)
            self.assertEqual(report.dataset_id, loaded.dataset_id)
            self.assertEqual(path.read_bytes(), original)

    def test_repository_samples_validate_against_sample_schema(self):
        repo_root = Path(__file__).resolve().parents[1]
        schema = json.loads(
            (repo_root / "schemas" / "sample_dataset.schema.json").read_text()
        )
        for filename in ("sample_dataset.csv", "sample_dataset.json"):
            with self.subTest(filename=filename):
                loaded = load_dataset(repo_root / "data" / "samples" / filename)
                report = validate_dataset(loaded, schema)
                self.assertTrue(report.is_valid, report.errors)


if __name__ == "__main__":
    unittest.main()
