"""Durable local persistence and verification for offline evidence reports."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quantum_space_agi.ml.evidence_report import EVIDENCE_REPORT_SCHEMA_VERSION
from quantum_space_agi.ml.snapshot_artifact import (
    SnapshotArtifactError,
    SnapshotArtifactVerification,
    SnapshotArtifactWriteResult,
    verify_snapshot_artifact,
    write_snapshot_artifact,
)


class EvidenceReportPersistenceError(ValueError):
    """A report payload is malformed or is linked to the wrong source snapshot."""


@dataclass(frozen=True, slots=True)
class EvidenceReportWriteResult:
    """Published report artifact and the source snapshot it describes."""

    artifact: SnapshotArtifactWriteResult
    source_snapshot_sha256: str

    @property
    def report_sha256(self) -> str:
        """SHA-256 calculated by the snapshot artifact writer."""
        return self.artifact.manifest.sha256

    @property
    def byte_length(self) -> int:
        """Exact persisted report byte length."""
        return self.artifact.manifest.byte_length


@dataclass(frozen=True, slots=True)
class VerifiedEvidenceReport:
    """Verified report bytes, integrity values, and linked source snapshot."""

    artifact: SnapshotArtifactVerification
    source_snapshot_sha256: str

    @property
    def report_bytes(self) -> bytes:
        """Exact report bytes hashed by artifact verification."""
        payload = self.artifact.verified_bytes
        if payload is None:  # The verifier is called with include_bytes=True.
            raise RuntimeError("verified report bytes were not retained")
        return payload

    @property
    def report_sha256(self) -> str:
        """SHA-256 recalculated from the stored report bytes."""
        return self.artifact.actual_sha256

    @property
    def byte_length(self) -> int:
        """Length recalculated from the stored report bytes."""
        return self.artifact.actual_byte_length


def persist_evidence_report(
    report_bytes: bytes,
    destination: str | Path,
    *,
    expected_source_snapshot_sha256: str,
    overwrite: bool = False,
) -> EvidenceReportWriteResult:
    """Persist an already serialized report using snapshot artifact safeguards.

    The report bytes are validated but never rewritten. The existing snapshot
    artifact sidecar binds the report's exact bytes; the report's embedded
    ``snapshot.sha256`` links it to the caller-supplied source snapshot digest.
    """
    source_sha256 = _validate_sha256(
        expected_source_snapshot_sha256, "expected_source_snapshot_sha256"
    )
    _validate_report_bytes(report_bytes, source_sha256)

    artifact_path = Path(destination)
    manifest_path = Path(f"{artifact_path}.manifest.json")
    if overwrite and (artifact_path.exists() or manifest_path.exists()):
        # Do not replace an integrity-valid but malformed/unsupported report.
        # The writer below handles incomplete pairs and preserves valid pairs.
        existing = verify_snapshot_artifact(artifact_path, include_bytes=True)
        existing_bytes = existing.verified_bytes
        if existing_bytes is None:
            raise EvidenceReportPersistenceError(
                "existing report bytes were not returned by verification"
            )
        existing_report = _parse_report(existing_bytes)
        existing_source_sha256 = _report_source_sha256(existing_report)
        _validate_report_bytes(existing_bytes, existing_source_sha256)

    try:
        written = write_snapshot_artifact(
            report_bytes, artifact_path, overwrite=overwrite
        )
    except SnapshotArtifactError:
        raise
    return EvidenceReportWriteResult(written, source_sha256)


def verify_evidence_report(
    artifact_path: str | Path,
    *,
    expected_source_snapshot_sha256: str,
    manifest_path: str | Path | None = None,
) -> VerifiedEvidenceReport:
    """Verify report artifact integrity and its expected source snapshot link."""
    source_sha256 = _validate_sha256(
        expected_source_snapshot_sha256, "expected_source_snapshot_sha256"
    )
    artifact = verify_snapshot_artifact(
        artifact_path, manifest_path, include_bytes=True
    )
    report_bytes = artifact.verified_bytes
    if report_bytes is None:
        raise EvidenceReportPersistenceError(
            "verified report bytes were not returned by artifact verification"
        )
    _validate_report_bytes(report_bytes, source_sha256)
    return VerifiedEvidenceReport(artifact, source_sha256)


def _validate_report_bytes(report_bytes: bytes, expected_source_sha256: str) -> None:
    if type(report_bytes) is not bytes:
        raise EvidenceReportPersistenceError("report_bytes must be built-in bytes")
    report = _parse_report(report_bytes)
    if report.get("schema_version") != EVIDENCE_REPORT_SCHEMA_VERSION:
        raise EvidenceReportPersistenceError("unsupported evidence report schema")
    required_fields = {
        "schema_version",
        "snapshot",
        "ingestion",
        "accepted_source_row_indices",
        "exclusion_ledger",
        "identity_diagnostics",
        "split_feasibility",
        "split_assignments",
        "approval_status",
        "limitations",
    }
    if set(report) != required_fields:
        raise EvidenceReportPersistenceError(
            "report is incomplete or contains unsupported top-level fields"
        )
    _validate_report_structure(report)
    source_sha256 = _report_source_sha256(report)
    if source_sha256 != expected_source_sha256:
        raise EvidenceReportPersistenceError(
            "report source snapshot checksum does not match expected checksum"
        )


def _parse_report(report_bytes: bytes) -> dict[str, Any]:
    if type(report_bytes) is not bytes:
        raise EvidenceReportPersistenceError("report_bytes must be built-in bytes")
    try:
        report = json.loads(
            report_bytes.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_json_constant,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValueError,
        OverflowError,
    ) as exc:
        raise EvidenceReportPersistenceError(
            "report must be valid UTF-8 JSON without duplicate keys or non-JSON values"
        ) from exc
    if type(report) is not dict:
        raise EvidenceReportPersistenceError("report JSON root must be an object")
    _reject_non_finite_values(report)
    return report


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceReportPersistenceError("report JSON contains duplicate keys")
        result[key] = value
    return result


def _reject_non_json_constant(value: str) -> None:
    raise EvidenceReportPersistenceError(f"unsupported JSON numeric constant: {value}")


def _reject_non_finite_values(value: object) -> None:
    if type(value) is float and not math.isfinite(value):
        raise EvidenceReportPersistenceError("report JSON contains a non-finite number")
    if type(value) is list:
        for item in value:
            _reject_non_finite_values(item)
    elif type(value) is dict:
        for item in value.values():
            _reject_non_finite_values(item)


def _validate_report_structure(report: dict[str, Any]) -> None:
    snapshot = report["snapshot"]
    if type(snapshot) is not dict or set(snapshot) != {
        "artifact_name",
        "sha256",
        "byte_length",
        "caller_supplied_provenance",
    }:
        raise EvidenceReportPersistenceError("report snapshot section is malformed")
    if type(snapshot["artifact_name"]) is not str or not snapshot["artifact_name"]:
        raise EvidenceReportPersistenceError("report snapshot artifact name is invalid")
    if type(snapshot["byte_length"]) is not int or snapshot["byte_length"] < 0:
        raise EvidenceReportPersistenceError("report snapshot byte length is invalid")
    provenance = snapshot["caller_supplied_provenance"]
    if type(provenance) is not dict or set(provenance) != {
        "source_identifier",
        "tap_endpoint",
        "adql_query",
        "query_parameters",
        "acquisition_timestamp",
        "job_identifier",
        "http_response_metadata",
    }:
        raise EvidenceReportPersistenceError("report provenance section is malformed")
    if (
        type(provenance["query_parameters"]) is not dict
        or type(provenance["http_response_metadata"]) is not dict
    ):
        raise EvidenceReportPersistenceError("report provenance mappings are malformed")
    for field in ("source_identifier", "tap_endpoint", "adql_query", "job_identifier"):
        if provenance[field] is not None and type(provenance[field]) is not str:
            raise EvidenceReportPersistenceError("report provenance text is malformed")
    if (
        provenance["acquisition_timestamp"] is not None
        and type(provenance["acquisition_timestamp"]) is not str
    ):
        raise EvidenceReportPersistenceError("report provenance timestamp is malformed")
    if any(type(key) is not str for key in provenance["http_response_metadata"]):
        raise EvidenceReportPersistenceError("report HTTP metadata is malformed")
    if any(
        type(key) is not str or type(value) not in (str, int, float, bool, type(None))
        for key, value in provenance["query_parameters"].items()
    ):
        raise EvidenceReportPersistenceError("report query parameters are malformed")

    ingestion = report["ingestion"]
    ingestion_fields = {
        "manifest_version",
        "validation_scope",
        "validation_status",
        "serialization",
        "detected_fields",
        "extracted_row_count",
        "mechanically_accepted_row_count",
        "excluded_row_count",
        "validation_policy_version",
        "votable_validator_version",
        "parser_version",
        "raw_response_sha256",
        "raw_response_byte_count",
        "validation_report",
    }
    if type(ingestion) is not dict or set(ingestion) != ingestion_fields:
        raise EvidenceReportPersistenceError(
            "report ingestion section is incomplete or malformed"
        )
    count_names = (
        "extracted_row_count",
        "mechanically_accepted_row_count",
        "excluded_row_count",
    )
    if any(
        type(ingestion.get(name)) is not int or ingestion[name] < 0
        for name in count_names
    ):
        raise EvidenceReportPersistenceError("report ingestion counts are invalid")
    extracted = ingestion["extracted_row_count"]
    if (
        ingestion["mechanically_accepted_row_count"] + ingestion["excluded_row_count"]
        != extracted
    ):
        raise EvidenceReportPersistenceError("report ingestion counts do not reconcile")
    if (
        ingestion["validation_scope"] != "MECHANICAL_VALIDATION_ONLY"
        or any(
            type(ingestion[name]) is not str or not ingestion[name]
            for name in (
                "manifest_version",
                "validation_status",
                "serialization",
                "validation_policy_version",
                "votable_validator_version",
                "parser_version",
            )
        )
        or type(ingestion["detected_fields"]) is not list
        or type(ingestion["raw_response_byte_count"]) is not int
        or ingestion["raw_response_byte_count"] < 0
    ):
        raise EvidenceReportPersistenceError("report ingestion metadata is malformed")
    for field in ingestion["detected_fields"]:
        if (
            type(field) is not dict
            or set(field)
            != {
                "name",
                "datatype",
                "arraysize",
                "unit",
                "null_value",
            }
            or any(
                field[name] is not None and type(field[name]) is not str
                for name in ("name", "datatype", "arraysize", "unit", "null_value")
            )
        ):
            raise EvidenceReportPersistenceError("report detected field is malformed")
    validation_report = ingestion["validation_report"]
    if type(validation_report) is not dict or set(validation_report) != {
        "record_count",
        "valid_record_indices",
        "excluded_source_row_indices",
    }:
        raise EvidenceReportPersistenceError("report validation summary is malformed")
    if (
        type(validation_report["record_count"]) is not int
        or validation_report["record_count"] != extracted
        or type(validation_report["valid_record_indices"]) is not list
        or type(validation_report["excluded_source_row_indices"]) is not list
    ):
        raise EvidenceReportPersistenceError(
            "report validation summary is inconsistent"
        )
    _validate_source_row_indices(
        validation_report["valid_record_indices"], extracted, "valid_record_indices"
    )
    _validate_source_row_indices(
        validation_report["excluded_source_row_indices"],
        extracted,
        "excluded_source_row_indices",
    )
    accepted = report["accepted_source_row_indices"]
    exclusions = report["exclusion_ledger"]
    if type(accepted) is not list or any(type(index) is not int for index in accepted):
        raise EvidenceReportPersistenceError(
            "accepted source-row indices are malformed"
        )
    if type(exclusions) is not list:
        raise EvidenceReportPersistenceError("exclusion ledger must be an array")
    excluded_indices: list[int] = []
    for excluded in exclusions:
        if type(excluded) is not dict or set(excluded) != {
            "source_row_index",
            "findings",
        }:
            raise EvidenceReportPersistenceError("exclusion ledger entry is malformed")
        index = excluded["source_row_index"]
        findings = excluded["findings"]
        if type(index) is not int or not 0 <= index < extracted:
            raise EvidenceReportPersistenceError(
                "exclusion source-row index is invalid"
            )
        if type(findings) is not list or not findings:
            raise EvidenceReportPersistenceError("exclusion findings are malformed")
        excluded_indices.append(index)
        for finding in findings:
            if type(finding) is not dict or set(finding) != {
                "field",
                "reason_code",
                "original_value",
                "value_omitted",
            }:
                raise EvidenceReportPersistenceError("exclusion finding is malformed")
            if (
                type(finding["field"]) is not str
                or not finding["field"]
                or type(finding["reason_code"]) is not str
                or not finding["reason_code"]
                or type(finding["value_omitted"]) is not bool
                or (
                    finding["original_value"] is not None
                    and type(finding["original_value"]) not in (str, int, float, bool)
                )
                or (finding["value_omitted"] and finding["original_value"] is not None)
            ):
                raise EvidenceReportPersistenceError("exclusion finding is malformed")
    if (
        len(set(accepted)) != len(accepted)
        or len(set(excluded_indices)) != len(excluded_indices)
        or set(accepted).intersection(excluded_indices)
        or set(accepted).union(excluded_indices) != set(range(extracted))
        or len(accepted) != ingestion["mechanically_accepted_row_count"]
        or len(excluded_indices) != ingestion["excluded_row_count"]
        or accepted != validation_report["valid_record_indices"]
        or excluded_indices != validation_report["excluded_source_row_indices"]
        or ingestion["raw_response_byte_count"] != snapshot["byte_length"]
        or ingestion["raw_response_sha256"] != snapshot["sha256"]
    ):
        raise EvidenceReportPersistenceError("report source-row ledger is inconsistent")

    identity = report["identity_diagnostics"]
    if identity is not None:
        _validate_identity_section(identity, accepted, extracted)
    feasibility = report["split_feasibility"]
    if feasibility is not None:
        if identity is None:
            raise EvidenceReportPersistenceError(
                "split feasibility requires identity diagnostics"
            )
        _validate_feasibility_section(feasibility, identity, accepted)
    _validate_assignment_section(
        report["split_assignments"], identity, feasibility, accepted
    )
    status = report["approval_status"]
    if type(status) is not dict or status != {
        "scientific": "NOT_ESTABLISHED_BY_THIS_REPORT",
        "acquisition_authorization": "NOT_ESTABLISHED_BY_THIS_REPORT",
    }:
        raise EvidenceReportPersistenceError("report approval status is malformed")
    if type(report["limitations"]) is not list or any(
        type(item) is not str for item in report["limitations"]
    ):
        raise EvidenceReportPersistenceError("report limitations are malformed")


def _validate_identity_section(
    identity: object, accepted: list[int], extracted: int
) -> None:
    identity_fields = {
        "record_scope",
        "row_count",
        "source_row_indices",
        "distinct_host_count",
        "largest_host_group_rows",
        "repeated_identity_values",
        "identity_fields",
        "repeated_identity_tuples",
        "host_groups",
        "connected_components",
    }
    if (
        type(identity) is not dict
        or set(identity) != identity_fields
        or identity.get("source_row_indices") != accepted
        or identity.get("record_scope") != "MECHANICALLY_ACCEPTED_RECORDS_ONLY"
        or type(identity.get("row_count")) is not int
        or identity["row_count"] != len(accepted)
        or type(identity.get("distinct_host_count")) is not int
        or identity["distinct_host_count"] < 0
        or type(identity.get("largest_host_group_rows")) is not int
        or identity["largest_host_group_rows"] < 0
    ):
        raise EvidenceReportPersistenceError("identity diagnostics are malformed")
    host_groups = identity["host_groups"]
    components = identity["connected_components"]
    repeated = identity["repeated_identity_values"]
    identity_fields_report = identity["identity_fields"]
    tuples = identity["repeated_identity_tuples"]
    if any(
        type(value) is not list
        for value in (host_groups, components, repeated, identity_fields_report, tuples)
    ):
        raise EvidenceReportPersistenceError(
            "identity diagnostics arrays are malformed"
        )
    _validate_row_list(identity["source_row_indices"], accepted, "identity")
    host_names: set[str] = set()
    host_group_rows: list[int] = []
    for group in host_groups:
        if (
            type(group) is not dict
            or set(group) != {"hostname", "source_row_indices"}
            or type(group["hostname"]) is not str
            or not group["hostname"]
            or group["hostname"] in host_names
        ):
            raise EvidenceReportPersistenceError("identity host group is malformed")
        host_names.add(group["hostname"])
        _validate_row_list(group["source_row_indices"], accepted, "host group")
        if not group["source_row_indices"]:
            raise EvidenceReportPersistenceError("identity host group is empty")
        host_group_rows.extend(group["source_row_indices"])
    component_rows: list[int] = []
    component_sizes: list[int] = []
    for expected_index, component in enumerate(components):
        if (
            type(component) is not dict
            or set(component)
            != {"component_index", "source_row_indices", "hostnames", "references"}
            or type(component["component_index"]) is not int
            or component["component_index"] != expected_index
            or type(component["hostnames"]) is not list
            or any(type(value) is not str for value in component["hostnames"])
            or type(component["references"]) is not list
            or any(type(value) is not str for value in component["references"])
        ):
            raise EvidenceReportPersistenceError("identity component is malformed")
        _validate_row_list(component["source_row_indices"], accepted, "component")
        if not component["source_row_indices"]:
            raise EvidenceReportPersistenceError("identity component is empty")
        if len(set(component["hostnames"])) != len(component["hostnames"]):
            raise EvidenceReportPersistenceError(
                "identity component hosts are duplicated"
            )
        if len(set(component["references"])) != len(component["references"]):
            raise EvidenceReportPersistenceError(
                "identity component references are duplicated"
            )
        component_rows.extend(component["source_row_indices"])
        component_sizes.append(len(component["source_row_indices"]))
    if sorted(component_rows) != accepted:
        raise EvidenceReportPersistenceError(
            "identity components must account for accepted source rows exactly once"
        )
    if len(host_groups) != identity["distinct_host_count"] or (
        max((len(group["source_row_indices"]) for group in host_groups), default=0)
        != identity["largest_host_group_rows"]
    ):
        raise EvidenceReportPersistenceError("identity host summaries are inconsistent")
    if len(set(host_group_rows)) != len(host_group_rows):
        raise EvidenceReportPersistenceError("identity host groups overlap")
    component_by_row = {
        row_index: component
        for component in components
        for row_index in component["source_row_indices"]
    }
    for group in host_groups:
        group_components = {
            component_by_row[row_index]["component_index"]
            for row_index in group["source_row_indices"]
        }
        if (
            len(group_components) != 1
            or group["hostname"]
            not in components[next(iter(group_components))]["hostnames"]
        ):
            raise EvidenceReportPersistenceError(
                "identity host group contradicts connected components"
            )
    for component in components:
        component_hostnames = {
            group["hostname"]
            for group in host_groups
            if group["source_row_indices"][0] in component["source_row_indices"]
        }
        if component_hostnames != set(component["hostnames"]):
            raise EvidenceReportPersistenceError(
                "identity component hosts contradict host groups"
            )
    repeated_keys: set[tuple[str, str]] = set()
    repeated_rows: dict[str, set[int]] = {}
    for item in repeated:
        if (
            type(item) is not dict
            or set(item) != {"field", "value", "source_row_indices"}
            or item["field"] not in {"pl_name", "hostname", "pl_refname"}
            or type(item["value"]) is not str
            or not item["value"]
        ):
            raise EvidenceReportPersistenceError("repeated identity value is malformed")
        _validate_row_list(item["source_row_indices"], accepted, "repeated identity")
        key = (item["field"], item["value"])
        if key in repeated_keys or len(item["source_row_indices"]) < 2:
            raise EvidenceReportPersistenceError(
                "repeated identity value is duplicated or not repeated"
            )
        repeated_keys.add(key)
        prior_rows = repeated_rows.setdefault(item["field"], set())
        rows = set(item["source_row_indices"])
        if prior_rows.intersection(rows):
            raise EvidenceReportPersistenceError(
                "repeated identity values overlap within a field"
            )
        prior_rows.update(rows)
        if item["field"] == "pl_refname":
            component_ids = {
                component_by_row[row_index]["component_index"] for row_index in rows
            }
            if len(component_ids) != 1:
                raise EvidenceReportPersistenceError(
                    "repeated references cross connected components"
                )
            component = components[next(iter(component_ids))]
            if item["value"] not in component["references"]:
                raise EvidenceReportPersistenceError(
                    "repeated reference is absent from its component"
                )
    expected_identity_fields = ("pl_name", "hostname", "pl_refname")
    if (
        tuple(
            item.get("field") if type(item) is dict else None
            for item in identity_fields_report
        )
        != expected_identity_fields
    ):
        raise EvidenceReportPersistenceError(
            "identity field summaries must follow the declared identity fields"
        )
    identity_rows_by_field: dict[str, set[int]] = {}
    for item in identity_fields_report:
        if (
            type(item) is not dict
            or set(item)
            != {
                "field",
                "missing_source_row_indices",
                "invalid_type_source_row_indices",
            }
            or item["field"] not in {"pl_name", "hostname", "pl_refname"}
        ):
            raise EvidenceReportPersistenceError("identity field summary is malformed")
        _validate_row_list(
            item["missing_source_row_indices"], accepted, "missing identity"
        )
        _validate_row_list(
            item["invalid_type_source_row_indices"], accepted, "invalid identity"
        )
        missing_rows = set(item["missing_source_row_indices"])
        invalid_rows = set(item["invalid_type_source_row_indices"])
        if missing_rows.intersection(invalid_rows):
            raise EvidenceReportPersistenceError(
                "identity missing and invalid rows overlap"
            )
        identity_rows_by_field[item["field"]] = missing_rows | invalid_rows
    unusable_hosts = identity_rows_by_field["hostname"]
    expected_host_rows = set(accepted) - unusable_hosts
    if set(host_group_rows) != expected_host_rows:
        raise EvidenceReportPersistenceError(
            "identity host groups do not match usable hostname rows"
        )
    for item in tuples:
        if (
            type(item) is not dict
            or set(item) != {"identity", "source_row_indices"}
            or type(item["identity"]) is not list
            or len(item["identity"]) != 3
            or any(type(value) is not str or not value for value in item["identity"])
        ):
            raise EvidenceReportPersistenceError("repeated identity tuple is malformed")
        _validate_row_list(item["source_row_indices"], accepted, "identity tuple")
        if len(item["source_row_indices"]) < 2:
            raise EvidenceReportPersistenceError(
                "repeated identity tuple is not repeated"
            )


def _validate_row_list(values: object, accepted: list[int], label: str) -> None:
    if (
        type(values) is not list
        or any(type(index) is not int or index not in accepted for index in values)
        or len(set(values)) != len(values)
    ):
        raise EvidenceReportPersistenceError(f"{label} source-row mapping is malformed")


def _validate_source_row_indices(
    indices: object, source_row_count: int, field_name: str
) -> None:
    if type(indices) is not list or any(
        type(index) is not int or not 0 <= index < source_row_count for index in indices
    ):
        raise EvidenceReportPersistenceError(
            f"{field_name} must contain in-range integer source-row indices"
        )


def _validate_feasibility_section(
    feasibility: object, identity: dict[str, Any], accepted: list[int]
) -> None:
    required = {
        "requested_partitions",
        "host_group_count",
        "host_structurally_feasible",
        "component_count",
        "components_structurally_feasible",
        "largest_component_rows",
        "largest_component_is_majority",
        "missing_host_source_row_indices",
        "missing_reference_source_row_indices",
        "warnings",
        "is_assignment",
    }
    if type(feasibility) is not dict or set(feasibility) != required:
        raise EvidenceReportPersistenceError("split feasibility section is malformed")
    integer_fields = (
        "requested_partitions",
        "host_group_count",
        "component_count",
        "largest_component_rows",
    )
    if any(
        type(feasibility[field]) is not int or feasibility[field] < 0
        for field in integer_fields
    ):
        raise EvidenceReportPersistenceError("split feasibility counts are invalid")
    boolean_fields = (
        "host_structurally_feasible",
        "components_structurally_feasible",
        "largest_component_is_majority",
        "is_assignment",
    )
    if any(type(feasibility[field]) is not bool for field in boolean_fields):
        raise EvidenceReportPersistenceError("split feasibility flags are invalid")
    if feasibility["is_assignment"]:
        raise EvidenceReportPersistenceError(
            "split feasibility cannot be an assignment"
        )
    if feasibility["requested_partitions"] < 2:
        raise EvidenceReportPersistenceError(
            "requested partition count must be at least two"
        )
    for field in (
        "missing_host_source_row_indices",
        "missing_reference_source_row_indices",
    ):
        _validate_row_list(feasibility[field], accepted, "feasibility identity")
    if type(feasibility["warnings"]) is not list or any(
        type(item) is not str for item in feasibility["warnings"]
    ):
        raise EvidenceReportPersistenceError("split feasibility warnings are malformed")
    components = identity["connected_components"]
    largest_component = max(
        (len(component["source_row_indices"]) for component in components), default=0
    )
    missing_hosts = feasibility["missing_host_source_row_indices"]
    missing_references = feasibility["missing_reference_source_row_indices"]
    identity_fields = {field["field"]: field for field in identity["identity_fields"]}
    expected_missing_hosts = sorted(
        set(identity_fields["hostname"]["missing_source_row_indices"])
        | set(identity_fields["hostname"]["invalid_type_source_row_indices"])
    )
    expected_missing_references = sorted(
        set(identity_fields["pl_refname"]["missing_source_row_indices"])
        | set(identity_fields["pl_refname"]["invalid_type_source_row_indices"])
    )
    row_count = len(accepted)
    if (
        feasibility["host_group_count"] != len(identity["host_groups"])
        or feasibility["component_count"] != len(components)
        or feasibility["largest_component_rows"] != largest_component
        or feasibility["host_structurally_feasible"]
        != (
            feasibility["host_group_count"] >= feasibility["requested_partitions"]
            and not missing_hosts
        )
        or feasibility["components_structurally_feasible"]
        != (
            feasibility["component_count"] >= feasibility["requested_partitions"]
            and not missing_hosts
            and not missing_references
        )
        or feasibility["largest_component_is_majority"]
        != (row_count > 0 and largest_component * 2 > row_count)
        or missing_hosts != expected_missing_hosts
        or missing_references != expected_missing_references
    ):
        raise EvidenceReportPersistenceError(
            "split feasibility summary contradicts identity diagnostics"
        )


def _validate_assignment_section(
    assignments: object,
    identity: dict[str, Any] | None,
    feasibility: dict[str, Any] | None,
    accepted: list[int],
) -> None:
    if type(assignments) is not dict or assignments.get("assignment_status") not in {
        "NOT_CREATED_OR_SUPPLIED",
        "SUPPLIED_NOT_APPROVED",
    }:
        raise EvidenceReportPersistenceError("split assignment section is malformed")
    status = assignments["assignment_status"]
    values = assignments.get("assignments")
    if status == "NOT_CREATED_OR_SUPPLIED":
        if values is not None or set(assignments) != {
            "assignment_status",
            "assignments",
        }:
            raise EvidenceReportPersistenceError(
                "absent split assignments are malformed"
            )
        return
    expected_keys = {
        "assignment_status",
        "grouping_field",
        "ordering_strategy",
        "configuration",
        "assignments",
        "leakage_audit",
    }
    if (
        set(assignments) != expected_keys
        or assignments["grouping_field"] != "hostname"
        or type(assignments["ordering_strategy"]) is not str
        or not assignments["ordering_strategy"]
        or identity is None
        or type(values) is not list
        or len(values) != len(accepted)
    ):
        raise EvidenceReportPersistenceError("supplied split assignments are malformed")
    configuration = assignments["configuration"]
    if type(configuration) is not dict or set(configuration) != {"proportions", "seed"}:
        raise EvidenceReportPersistenceError("split configuration is malformed")
    proportions = configuration["proportions"]
    if (
        type(proportions) is not list
        or len(proportions) != 3
        or any(
            type(value) is not float or not math.isfinite(value) or value <= 0
            for value in proportions
        )
        or not math.isclose(math.fsum(proportions), 1.0, rel_tol=0, abs_tol=1e-12)
        or type(configuration["seed"]) is not int
    ):
        raise EvidenceReportPersistenceError("split configuration values are invalid")
    partitions: list[str] = []
    label_by_row: dict[int, str] = {}
    for index, item in enumerate(values):
        if (
            type(item) is not dict
            or set(item) != {"source_row_index", "partition"}
            or type(item["source_row_index"]) is not int
            or item["source_row_index"] != accepted[index]
            or type(item["partition"]) is not str
            or item["partition"] not in {"train", "validation", "test"}
        ):
            raise EvidenceReportPersistenceError("split assignment row is malformed")
        partitions.append(item["partition"])
        label_by_row[item["source_row_index"]] = item["partition"]
    if set(partitions) != {"train", "validation", "test"}:
        raise EvidenceReportPersistenceError("split assignments omit a partition")
    if any(
        len({label_by_row[row_index] for row_index in group["source_row_indices"]}) > 1
        for group in identity["host_groups"]
    ):
        raise EvidenceReportPersistenceError(
            "split assignments violate exact-host grouping"
        )
    if feasibility is not None and not feasibility["host_structurally_feasible"]:
        raise EvidenceReportPersistenceError(
            "split assignments contradict infeasible host grouping"
        )
    _validate_leakage_audit(assignments["leakage_audit"], identity, values)


def _validate_leakage_audit(
    audit: object, identity: dict[str, Any], assignments: list[dict[str, Any]]
) -> None:
    fields = {
        "host_overlap_count",
        "reference_overlap_count",
        "planet_name_overlap_count",
        "component_overlap_count",
        "has_cross_partition_leakage",
    }
    if type(audit) is not dict or set(audit) != fields:
        raise EvidenceReportPersistenceError("split leakage audit is malformed")
    counts = fields - {"has_cross_partition_leakage"}
    if any(type(audit[name]) is not int or audit[name] < 0 for name in counts):
        raise EvidenceReportPersistenceError("split leakage counts are invalid")
    if type(audit["has_cross_partition_leakage"]) is not bool:
        raise EvidenceReportPersistenceError("split leakage flag is invalid")
    label_by_row = {item["source_row_index"]: item["partition"] for item in assignments}
    host_overlaps = sum(
        len({label_by_row[index] for index in group["source_row_indices"]}) > 1
        for group in identity["host_groups"]
    )
    identity_overlaps: dict[str, int] = {"pl_refname": 0, "pl_name": 0}
    for item in identity["repeated_identity_values"]:
        field = item["field"]
        if (
            field in identity_overlaps
            and len({label_by_row[index] for index in item["source_row_indices"]}) > 1
        ):
            identity_overlaps[field] += 1
    component_overlaps = sum(
        len({label_by_row[index] for index in component["source_row_indices"]}) > 1
        for component in identity["connected_components"]
    )
    expected_counts = {
        "host_overlap_count": host_overlaps,
        "reference_overlap_count": identity_overlaps["pl_refname"],
        "planet_name_overlap_count": identity_overlaps["pl_name"],
        "component_overlap_count": component_overlaps,
    }
    if any(audit[name] != expected for name, expected in expected_counts.items()):
        raise EvidenceReportPersistenceError(
            "split leakage counts contradict identity diagnostics and assignments"
        )
    if audit["has_cross_partition_leakage"] != any(expected_counts.values()):
        raise EvidenceReportPersistenceError(
            "split leakage flag contradicts overlap counts"
        )


def _report_source_sha256(report: dict[str, Any]) -> str:
    snapshot = report.get("snapshot")
    if type(snapshot) is not dict:
        raise EvidenceReportPersistenceError(
            "report snapshot section must be an object"
        )
    byte_length = snapshot.get("byte_length")
    if type(byte_length) is not int or byte_length < 0:
        raise EvidenceReportPersistenceError(
            "report snapshot.byte_length must be a non-negative integer"
        )
    return _validate_sha256(snapshot.get("sha256"), "report snapshot.sha256")


def _validate_sha256(value: object, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise EvidenceReportPersistenceError(f"{name} must be lowercase SHA-256")
    return value
