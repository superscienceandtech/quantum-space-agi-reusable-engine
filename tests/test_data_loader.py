import json
import tempfile
import unittest
from pathlib import Path

from quantum_space_agi.data.loader import (
    DataFormatError,
    EmptyDatasetError,
    FileAccessError,
    MetadataAssociationError,
    load_dataset,
)


class DataLoaderTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.metadata_dir = self.root / "metadata"
        (self.metadata_dir / "sources").mkdir(parents=True)
        (self.metadata_dir / "provenance").mkdir()
        self.data_file = self.root / "records.csv"

    def tearDown(self):
        self.temp_dir.cleanup()

    def add_metadata(self, dataset_id="fixture-1", *, source_file=None, provenance_id=None):
        source = {
            "dataset_id": dataset_id,
            "dataset_version": "1.0.0",
            "data_status": "synthetic",
            "files": [str(source_file or self.data_file)],
        }
        (self.metadata_dir / "sources" / "source.json").write_text(json.dumps(source))
        provenance = {
            "dataset_id": provenance_id or dataset_id,
            "artifact_id": "artifact-1",
            "files": [{"path": str(source_file or self.data_file)}],
        }
        (self.metadata_dir / "provenance" / "provenance.json").write_text(json.dumps(provenance))

    def test_loads_csv_records_as_strings(self):
        self.data_file.write_text("name,value\nalpha,2.5\n", encoding="utf-8")
        result = load_dataset(self.data_file, metadata_dir=self.metadata_dir)
        self.assertEqual(result.records, [{"name": "alpha", "value": "2.5"}])
        self.assertEqual(result.format, "csv")
        self.assertEqual(result.record_count, 1)

    def test_csv_preserves_newlines_inside_quoted_field(self):
        self.data_file.write_bytes(b'name,note\r\nalpha,"line one\r\nline two"\r\n')
        result = load_dataset(self.data_file, metadata_dir=self.metadata_dir)
        self.assertEqual(result.records[0]["note"], "line one\r\nline two")

    def test_empty_csv_raises_empty_dataset_error(self):
        self.data_file.write_text("", encoding="utf-8")
        with self.assertRaises(EmptyDatasetError):
            load_dataset(self.data_file, metadata_dir=self.metadata_dir)

    def test_missing_csv_raises_file_access_error(self):
        with self.assertRaises(FileAccessError):
            load_dataset(self.data_file, metadata_dir=self.metadata_dir)

    def test_csv_without_headers_raises_format_error(self):
        self.data_file.write_text("\nalpha,2.5\n", encoding="utf-8")
        with self.assertRaises(DataFormatError):
            load_dataset(self.data_file, metadata_dir=self.metadata_dir)

    def test_malformed_csv_raises_format_error(self):
        self.data_file.write_text('name,value\n"alpha,2.5\n', encoding="utf-8")
        with self.assertRaises(DataFormatError):
            load_dataset(self.data_file, metadata_dir=self.metadata_dir)

    def test_csv_row_with_wrong_field_count_raises_format_error(self):
        self.data_file.write_text("name,value\nalpha\n", encoding="utf-8")
        with self.assertRaises(DataFormatError):
            load_dataset(self.data_file, metadata_dir=self.metadata_dir)

    def test_loads_json_array_of_objects(self):
        path = self.root / "records.json"
        path.write_text('[{"x": 1}, {"x": 2}]', encoding="utf-8")
        result = load_dataset(path, metadata_dir=self.metadata_dir)
        self.assertEqual(result.records, [{"x": 1}, {"x": 2}])

    def test_loads_json_object_as_one_record(self):
        path = self.root / "record.json"
        path.write_text('{"record_id": "EXAMPLE-001", "value": 12.5}', encoding="utf-8")
        result = load_dataset(path, metadata_dir=self.metadata_dir)
        self.assertEqual(result.records, [{"record_id": "EXAMPLE-001", "value": 12.5}])

    def test_loads_json_records_envelope(self):
        path = self.root / "envelope.json"
        path.write_text('{"records": [{"x": 1}]}', encoding="utf-8")
        self.assertEqual(load_dataset(path, metadata_dir=self.metadata_dir).records, [{"x": 1}])

    def test_empty_json_raises_empty_dataset_error(self):
        path = self.root / "empty.json"
        path.write_text("  \n", encoding="utf-8")
        with self.assertRaises(EmptyDatasetError):
            load_dataset(path, metadata_dir=self.metadata_dir)

    def test_empty_json_array_raises_empty_dataset_error(self):
        path = self.root / "empty.json"
        path.write_text("[]", encoding="utf-8")
        with self.assertRaises(EmptyDatasetError):
            load_dataset(path, metadata_dir=self.metadata_dir)

    def test_malformed_json_raises_format_error(self):
        path = self.root / "invalid.json"
        path.write_text("{bad", encoding="utf-8")
        with self.assertRaises(DataFormatError):
            load_dataset(path, metadata_dir=self.metadata_dir)

    def test_missing_json_raises_file_access_error(self):
        with self.assertRaises(FileAccessError):
            load_dataset(self.root / "missing.json", metadata_dir=self.metadata_dir)

    def test_unsupported_extension_raises_unsupported_format_error(self):
        from quantum_space_agi.data.loader import UnsupportedFormatError

        with self.assertRaises(UnsupportedFormatError):
            load_dataset(self.root / "records.tsv", metadata_dir=self.metadata_dir)

    def test_json_array_with_non_object_record_raises_format_error(self):
        path = self.root / "invalid-records.json"
        path.write_text('[{"x": 1}, 2]', encoding="utf-8")
        with self.assertRaises(DataFormatError):
            load_dataset(path, metadata_dir=self.metadata_dir)

    def test_associates_metadata_and_preserves_synthetic_status(self):
        self.data_file.write_text("name\nexample\n", encoding="utf-8")
        self.add_metadata()
        result = load_dataset(self.data_file, metadata_dir=self.metadata_dir)
        self.assertEqual(result.dataset_id, "fixture-1")
        self.assertEqual(result.dataset_version, "1.0.0")
        self.assertEqual(result.source_metadata["data_status"], "synthetic")
        self.assertIsNotNone(result.provenance_metadata)
        self.assertEqual(result.loading_status, "loaded")

    def test_missing_metadata_is_reported_without_fabricating_it(self):
        self.data_file.write_text("name\nexample\n", encoding="utf-8")
        result = load_dataset(self.data_file, metadata_dir=self.metadata_dir)
        self.assertIsNone(result.dataset_id)
        self.assertIsNone(result.source_metadata)
        self.assertTrue(result.metadata_warnings)
        self.assertEqual(result.loading_status, "loaded_with_metadata_warnings")

    def test_provenance_can_identify_dataset_when_source_sidecar_is_missing(self):
        self.data_file.write_text("name\nexample\n", encoding="utf-8")
        self.add_metadata()
        (self.metadata_dir / "sources" / "source.json").unlink()
        result = load_dataset(self.data_file, metadata_dir=self.metadata_dir)
        self.assertEqual(result.dataset_id, "fixture-1")
        self.assertIsNone(result.source_metadata)
        self.assertIsNotNone(result.provenance_metadata)
        self.assertTrue(result.metadata_warnings)

    def test_inconsistent_metadata_ids_raise_metadata_association_error(self):
        self.data_file.write_text("name\nexample\n", encoding="utf-8")
        self.add_metadata(provenance_id="different-id")
        with self.assertRaises(MetadataAssociationError):
            load_dataset(self.data_file, metadata_dir=self.metadata_dir)

    def test_inconsistent_metadata_versions_raise_metadata_association_error(self):
        self.data_file.write_text("name\nexample\n", encoding="utf-8")
        self.add_metadata()
        provenance_path = self.metadata_dir / "provenance" / "provenance.json"
        provenance = json.loads(provenance_path.read_text())
        provenance["dataset_version"] = "2.0.0"
        provenance_path.write_text(json.dumps(provenance))
        with self.assertRaises(MetadataAssociationError):
            load_dataset(self.data_file, metadata_dir=self.metadata_dir)

    def test_same_basename_in_another_directory_does_not_match_metadata(self):
        other = self.root / "other"
        other.mkdir()
        path = other / self.data_file.name
        path.write_text("name\nexample\n", encoding="utf-8")
        self.add_metadata()
        result = load_dataset(path, metadata_dir=self.metadata_dir)
        self.assertIsNone(result.source_metadata)
        self.assertTrue(result.metadata_warnings)

    def test_raw_file_is_not_modified(self):
        original = b"name,value\nalpha,2.5\n"
        self.data_file.write_bytes(original)
        load_dataset(self.data_file, metadata_dir=self.metadata_dir)
        self.assertEqual(self.data_file.read_bytes(), original)

    def test_loads_repository_csv_and_json_samples(self):
        repo_root = Path(__file__).resolve().parents[1]
        for name in ("sample_dataset.csv", "sample_dataset.json"):
            with self.subTest(name=name):
                result = load_dataset(repo_root / "data" / "samples" / name)
                self.assertEqual(result.dataset_id, "synthetic-generic-example-v1")
                self.assertEqual(result.record_count, 1)
                self.assertEqual(result.source_metadata["data_status"], "synthetic")


if __name__ == "__main__":
    unittest.main()
