"""Deterministic serialization of offline snapshot and diagnostic evidence."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from quantum_space_agi.ml.dataset_ingestion import (
    DatasetIngestionResult,
    IngestionMetadata,
)
from quantum_space_agi.ml.group_splitter import (
    PARTITIONS,
    GroupSplitResult,
    SplitConfiguration,
)
from quantum_space_agi.ml.identity_diagnostics import (
    IDENTITY_FIELDS,
    ConnectedComponent,
    GroupingFeasibility,
    HostGroup,
    IdentityFieldDiagnostics,
    IdentityGroupingReport,
    IngestedIdentityDiagnostics,
    LeakageAuditReport,
    RepeatedIdentityTuple,
    RepeatedIdentityValue,
    audit_partition_assignments,
)
from quantum_space_agi.ml.snapshot_artifact import SnapshotArtifactVerification
from quantum_space_agi.ml.verified_ingestion import VerifiedSnapshotIngestionResult

EVIDENCE_REPORT_SCHEMA_VERSION = "arc08-offline-evidence-report/1"


class OfflineEvidenceReportError(ValueError):
    """Input evidence cannot be represented consistently in a report."""


def serialize_offline_evidence_report(
    pipeline: VerifiedSnapshotIngestionResult,
    *,
    identity_diagnostics: IngestedIdentityDiagnostics | None = None,
    split_result: GroupSplitResult | None = None,
) -> bytes:
    """Serialize verified ingestion and optional diagnostics as compact UTF-8 JSON.

    The function performs no filesystem or network access and never creates a
    split. Any supplied split result is reported as supplied, not approved.
    Mechanical acceptance is explicitly distinguished from scientific
    eligibility. Callers may persist the returned bytes separately if they
    have authorization to retain the underlying evidence.
    """
    verification, ingestion = _validate_pipeline(pipeline)
    if identity_diagnostics is not None:
        _validate_identity_mapping(identity_diagnostics, ingestion)
    if split_result is not None:
        if identity_diagnostics is None:
            raise OfflineEvidenceReportError(
                "split_result requires identity diagnostics for source-row mapping"
            )
        _validate_split(split_result, identity_diagnostics, ingestion)

    report = {
        "schema_version": EVIDENCE_REPORT_SCHEMA_VERSION,
        "snapshot": _snapshot_section(
            verification.manifest.caller_metadata, verification
        ),
        "ingestion": _ingestion_section(ingestion),
        "accepted_source_row_indices": list(ingestion.accepted_source_row_indices),
        "exclusion_ledger": [
            {
                "source_row_index": excluded.row_index,
                "findings": [
                    {
                        "field": finding.field,
                        "reason_code": finding.reason_code,
                        "original_value": finding.original_value,
                        "value_omitted": finding.value_omitted,
                    }
                    for finding in excluded.findings
                ],
            }
            for excluded in ingestion.exclusion_ledger
        ],
        "identity_diagnostics": (
            _identity_section(identity_diagnostics)
            if identity_diagnostics is not None
            else None
        ),
        "split_feasibility": (
            _feasibility_section(identity_diagnostics)
            if identity_diagnostics is not None
            else None
        ),
        "split_assignments": _split_section(split_result, identity_diagnostics),
        "approval_status": {
            "scientific": "NOT_ESTABLISHED_BY_THIS_REPORT",
            "acquisition_authorization": "NOT_ESTABLISHED_BY_THIS_REPORT",
        },
        "limitations": [
            "Mechanical validation does not establish scientific eligibility.",
            "Snapshot integrity does not establish source authenticity, NASA "
            "authorization, or data-use rights.",
            "Split feasibility is not a split assignment or evidence of "
            "scientific approval.",
            "This report does not establish scientific review, model evaluation, "
            "or experiment completion.",
        ],
    }
    try:
        return json.dumps(
            report,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, OverflowError) as exc:
        raise OfflineEvidenceReportError(
            "offline evidence report contains unsupported JSON values"
        ) from exc


def _validate_pipeline(
    pipeline: VerifiedSnapshotIngestionResult,
) -> tuple[SnapshotArtifactVerification, DatasetIngestionResult]:
    if type(pipeline) is not VerifiedSnapshotIngestionResult:
        raise OfflineEvidenceReportError(
            "pipeline must be a VerifiedSnapshotIngestionResult"
        )
    verification = pipeline.verification
    ingestion = pipeline.ingestion
    if type(verification) is not SnapshotArtifactVerification:
        raise OfflineEvidenceReportError("snapshot verification has an invalid type")
    if type(ingestion) is not DatasetIngestionResult:
        raise OfflineEvidenceReportError("dataset ingestion has an invalid type")
    raw_bytes = verification.verified_bytes
    if type(raw_bytes) is not bytes:
        raise OfflineEvidenceReportError("verified snapshot bytes are unavailable")
    actual_length = len(raw_bytes)
    actual_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    if (
        type(verification.actual_byte_length) is not int
        or verification.actual_byte_length != actual_length
        or verification.manifest.byte_length != actual_length
        or type(verification.actual_sha256) is not str
        or verification.actual_sha256 != actual_sha256
        or verification.manifest.sha256 != actual_sha256
    ):
        raise OfflineEvidenceReportError(
            "snapshot checksum or byte length is inconsistent"
        )
    manifest = ingestion.manifest
    if (
        manifest.raw_response_byte_count != actual_length
        or manifest.raw_response_sha256 != actual_sha256
        or manifest.caller_metadata != verification.manifest.caller_metadata
        or manifest.extracted_row_count != ingestion.validation_report.record_count
        or manifest.validation_policy_version
        != ingestion.validation_report.policy_version
    ):
        raise OfflineEvidenceReportError(
            "ingestion evidence does not match the verified snapshot or "
            "validation report"
        )
    return verification, ingestion


def _validate_identity_mapping(
    diagnostics: IngestedIdentityDiagnostics,
    ingestion: DatasetIngestionResult,
) -> None:
    if type(diagnostics) is not IngestedIdentityDiagnostics:
        raise OfflineEvidenceReportError(
            "identity_diagnostics must be IngestedIdentityDiagnostics"
        )
    source_indices = diagnostics.source_row_indices
    if (
        type(source_indices) is not tuple
        or any(type(index) is not int for index in source_indices)
        or len(set(source_indices)) != len(source_indices)
        or any(
            not 0 <= index < ingestion.manifest.extracted_row_count
            for index in source_indices
        )
    ):
        raise OfflineEvidenceReportError(
            "identity source-row mapping is invalid or contains duplicates"
        )
    if source_indices != ingestion.accepted_source_row_indices:
        raise OfflineEvidenceReportError(
            "identity source-row mapping does not match accepted ingestion rows"
        )
    report = diagnostics.report
    if (
        type(report) is not IdentityGroupingReport
        or type(report.row_count) is not int
        or report.row_count != len(source_indices)
        or type(report.identity_fields) is not tuple
        or tuple(
            item.field
            for item in report.identity_fields
            if type(item) is IdentityFieldDiagnostics
        )
        != IDENTITY_FIELDS
    ):
        raise OfflineEvidenceReportError(
            "identity report row count does not match its source-row mapping"
        )
    for field in report.identity_fields:
        if type(field) is not IdentityFieldDiagnostics:
            raise OfflineEvidenceReportError("identity field diagnostics are malformed")
        if type(field.field) is not str or type(field.repeated_values) is not tuple:
            raise OfflineEvidenceReportError("identity field diagnostics are malformed")
        _require_local_indices(field.missing_row_indices, len(source_indices))
        _require_local_indices(field.invalid_type_row_indices, len(source_indices))
        if any(
            type(value) is not RepeatedIdentityValue for value in field.repeated_values
        ):
            raise OfflineEvidenceReportError("repeated identity values are malformed")
        for value in field.repeated_values:
            if type(value.value) is not str or not value.value:
                raise OfflineEvidenceReportError(
                    "repeated identity values are malformed"
                )
            _require_local_indices(value.row_indices, len(source_indices))
    if type(report.repeated_identity_tuples) is not tuple or any(
        type(item) is not RepeatedIdentityTuple
        for item in report.repeated_identity_tuples
    ):
        raise OfflineEvidenceReportError("repeated identity tuples are malformed")
    for repeated_tuple in report.repeated_identity_tuples:
        if (
            type(repeated_tuple.identity) is not tuple
            or len(repeated_tuple.identity) != 3
            or any(
                type(value) is not str or not value for value in repeated_tuple.identity
            )
        ):
            raise OfflineEvidenceReportError("repeated identity tuples are malformed")
        _require_local_indices(repeated_tuple.row_indices, len(source_indices))
    if type(report.host_groups) is not tuple or any(
        type(item) is not HostGroup for item in report.host_groups
    ):
        raise OfflineEvidenceReportError("host groups are malformed")
    for host_group in report.host_groups:
        if type(host_group.hostname) is not str or not host_group.hostname:
            raise OfflineEvidenceReportError("host groups are malformed")
        _require_local_indices(host_group.row_indices, len(source_indices))
    if type(report.components) is not tuple or any(
        type(item) is not ConnectedComponent for item in report.components
    ):
        raise OfflineEvidenceReportError("connected components are malformed")
    for component in report.components:
        if (
            type(component.component_index) is not int
            or component.component_index < 0
            or type(component.hostnames) is not tuple
            or any(type(value) is not str for value in component.hostnames)
            or type(component.references) is not tuple
            or any(type(value) is not str for value in component.references)
        ):
            raise OfflineEvidenceReportError("connected components are malformed")
        _require_local_indices(component.row_indices, len(source_indices))
    if report.feasibility is not None:
        _validate_feasibility(report.feasibility, report)


def _require_local_indices(indices: object, row_count: int) -> None:
    if (
        type(indices) is not tuple
        or any(
            type(index) is not int or not 0 <= index < row_count for index in indices
        )
        or len(set(indices)) != len(indices)
    ):
        raise OfflineEvidenceReportError("diagnostic row mapping is invalid")


def _validate_feasibility(
    feasibility: GroupingFeasibility, report: IdentityGroupingReport
) -> None:
    if type(feasibility) is not GroupingFeasibility:
        raise OfflineEvidenceReportError("split feasibility has an invalid type")
    row_count = report.row_count
    for indices in (
        feasibility.missing_host_rows,
        feasibility.missing_reference_rows,
    ):
        _require_local_indices(indices, row_count)
    for value in (
        feasibility.requested_partitions,
        feasibility.host_group_count,
        feasibility.component_count,
        feasibility.largest_component_rows,
    ):
        if type(value) is not int or value < 0:
            raise OfflineEvidenceReportError("split feasibility counts are invalid")
    if any(
        type(value) is not bool
        for value in (
            feasibility.host_structurally_feasible,
            feasibility.components_structurally_feasible,
            feasibility.largest_component_is_majority,
        )
    ):
        raise OfflineEvidenceReportError("split feasibility flags are invalid")
    if type(feasibility.warnings) is not tuple or any(
        type(value) is not str for value in feasibility.warnings
    ):
        raise OfflineEvidenceReportError("split feasibility warnings are invalid")
    if (
        feasibility.requested_partitions < 2
        or feasibility.host_group_count != len(report.host_groups)
        or feasibility.component_count != len(report.components)
        or feasibility.largest_component_rows != report.largest_component_rows
        or feasibility.host_group_count > row_count
        or feasibility.component_count > row_count
        or feasibility.largest_component_rows > row_count
        or feasibility.host_structurally_feasible
        != (
            feasibility.host_group_count >= feasibility.requested_partitions
            and not feasibility.missing_host_rows
        )
        or feasibility.components_structurally_feasible
        != (
            feasibility.component_count >= feasibility.requested_partitions
            and not feasibility.missing_host_rows
            and not feasibility.missing_reference_rows
        )
        or feasibility.largest_component_is_majority
        != (row_count > 0 and feasibility.largest_component_rows * 2 > row_count)
    ):
        raise OfflineEvidenceReportError(
            "split feasibility does not match its counts and missing-identity rows"
        )


def _validate_split(
    split_result: GroupSplitResult,
    diagnostics: IngestedIdentityDiagnostics,
    ingestion: DatasetIngestionResult,
) -> None:
    if type(split_result) is not GroupSplitResult:
        raise OfflineEvidenceReportError("split_result must be a GroupSplitResult")
    if (
        type(split_result.configuration) is not SplitConfiguration
        or type(split_result.leakage_audit) is not LeakageAuditReport
        or type(split_result.ordering_strategy) is not str
        or not split_result.ordering_strategy
    ):
        raise OfflineEvidenceReportError("split result is malformed")
    if split_result.grouping_field != "hostname":
        raise OfflineEvidenceReportError("split result must be grouped by hostname")
    assignments = split_result.row_assignments
    if (
        type(assignments) is not tuple
        or len(assignments) != len(diagnostics.source_row_indices)
        or any(
            type(label) is not str or label not in PARTITIONS for label in assignments
        )
    ):
        raise OfflineEvidenceReportError(
            "split assignments do not match the accepted-row mapping"
        )
    expected_audit = audit_partition_assignments(
        ingestion.accepted_records, assignments
    )
    if split_result.leakage_audit != expected_audit:
        raise OfflineEvidenceReportError(
            "split leakage audit does not match its assignments"
        )
    if expected_audit.host_overlaps:
        raise OfflineEvidenceReportError(
            "supplied split has cross-partition host overlap"
        )
    if (
        type(split_result.configuration.proportions) is not tuple
        or len(split_result.configuration.proportions) != 3
        or any(
            type(value) is not float or not math.isfinite(value)
            for value in split_result.configuration.proportions
        )
        or any(value <= 0 for value in split_result.configuration.proportions)
        or not math.isclose(
            math.fsum(split_result.configuration.proportions),
            1.0,
            rel_tol=0,
            abs_tol=1e-12,
        )
    ):
        raise OfflineEvidenceReportError("split configuration proportions are invalid")
    if type(split_result.configuration.seed) is not int:
        raise OfflineEvidenceReportError("split configuration seed is invalid")


def _snapshot_section(
    metadata: IngestionMetadata, verification: SnapshotArtifactVerification
) -> dict[str, Any]:
    return {
        "artifact_name": verification.manifest.artifact_name,
        "sha256": verification.actual_sha256,
        "byte_length": verification.actual_byte_length,
        "caller_supplied_provenance": {
            "source_identifier": metadata.source_identifier,
            "tap_endpoint": metadata.tap_endpoint,
            "adql_query": metadata.adql_query,
            "query_parameters": {
                key: value for key, value in metadata.query_parameters
            },
            "acquisition_timestamp": (
                metadata.acquisition_timestamp.isoformat()
                if metadata.acquisition_timestamp is not None
                else None
            ),
            "job_identifier": metadata.job_identifier,
            "http_response_metadata": {
                key: value for key, value in metadata.http_response_metadata
            },
        },
    }


def _ingestion_section(ingestion: DatasetIngestionResult) -> dict[str, Any]:
    manifest = ingestion.manifest
    return {
        "manifest_version": manifest.manifest_version,
        "validation_scope": "MECHANICAL_VALIDATION_ONLY",
        "validation_status": manifest.validation_status,
        "serialization": manifest.serialization,
        "detected_fields": [
            {
                "name": field.name,
                "datatype": field.datatype,
                "arraysize": field.arraysize,
                "unit": field.unit,
                "null_value": field.null_value,
            }
            for field in manifest.detected_fields
        ],
        "extracted_row_count": manifest.extracted_row_count,
        "mechanically_accepted_row_count": manifest.accepted_row_count,
        "excluded_row_count": manifest.excluded_row_count,
        "validation_policy_version": manifest.validation_policy_version,
        "votable_validator_version": manifest.validator_version,
        "parser_version": manifest.parser_version,
        "raw_response_sha256": manifest.raw_response_sha256,
        "raw_response_byte_count": manifest.raw_response_byte_count,
        "validation_report": {
            "record_count": ingestion.validation_report.record_count,
            "valid_record_indices": list(
                ingestion.validation_report.valid_record_indices
            ),
            "excluded_source_row_indices": [
                row.row_index for row in ingestion.validation_report.excluded_rows
            ],
        },
    }


def _identity_section(
    diagnostics: IngestedIdentityDiagnostics,
) -> dict[str, Any]:
    report = diagnostics.report
    to_source = diagnostics.source_indices_for
    return {
        "record_scope": "MECHANICALLY_ACCEPTED_RECORDS_ONLY",
        "row_count": report.row_count,
        "source_row_indices": list(diagnostics.source_row_indices),
        "distinct_host_count": report.distinct_host_count,
        "largest_host_group_rows": report.largest_host_group_rows,
        "repeated_identity_values": [
            {
                "field": field.field,
                "value": repeated.value,
                "source_row_indices": list(to_source(repeated.row_indices)),
            }
            for field in report.identity_fields
            for repeated in field.repeated_values
        ],
        "identity_fields": [
            {
                "field": field.field,
                "missing_source_row_indices": list(
                    to_source(field.missing_row_indices)
                ),
                "invalid_type_source_row_indices": list(
                    to_source(field.invalid_type_row_indices)
                ),
            }
            for field in report.identity_fields
        ],
        "repeated_identity_tuples": [
            {
                "identity": list(item.identity),
                "source_row_indices": list(to_source(item.row_indices)),
            }
            for item in report.repeated_identity_tuples
        ],
        "host_groups": [
            {
                "hostname": group.hostname,
                "source_row_indices": list(to_source(group.row_indices)),
            }
            for group in report.host_groups
        ],
        "connected_components": [
            {
                "component_index": component.component_index,
                "source_row_indices": list(to_source(component.row_indices)),
                "hostnames": list(component.hostnames),
                "references": list(component.references),
            }
            for component in report.components
        ],
    }


def _feasibility_section(
    diagnostics: IngestedIdentityDiagnostics,
) -> dict[str, Any] | None:
    feasibility = diagnostics.report.feasibility
    if feasibility is None:
        return None
    return {
        "requested_partitions": feasibility.requested_partitions,
        "host_group_count": feasibility.host_group_count,
        "host_structurally_feasible": feasibility.host_structurally_feasible,
        "component_count": feasibility.component_count,
        "components_structurally_feasible": (
            feasibility.components_structurally_feasible
        ),
        "largest_component_rows": feasibility.largest_component_rows,
        "largest_component_is_majority": feasibility.largest_component_is_majority,
        "missing_host_source_row_indices": list(
            diagnostics.source_indices_for(feasibility.missing_host_rows)
        ),
        "missing_reference_source_row_indices": list(
            diagnostics.source_indices_for(feasibility.missing_reference_rows)
        ),
        "warnings": list(feasibility.warnings),
        "is_assignment": False,
    }


def _split_section(
    split_result: GroupSplitResult | None,
    diagnostics: IngestedIdentityDiagnostics | None,
) -> dict[str, Any]:
    if split_result is None:
        return {
            "assignment_status": "NOT_CREATED_OR_SUPPLIED",
            "assignments": None,
        }
    if diagnostics is None:  # Also guarded before serialization.
        raise OfflineEvidenceReportError(
            "split assignments require identity source-row mapping"
        )
    return {
        "assignment_status": "SUPPLIED_NOT_APPROVED",
        "grouping_field": split_result.grouping_field,
        "ordering_strategy": split_result.ordering_strategy,
        "configuration": {
            "proportions": list(split_result.configuration.proportions),
            "seed": split_result.configuration.seed,
        },
        "assignments": [
            {
                "source_row_index": source_index,
                "partition": partition,
            }
            for source_index, partition in zip(
                diagnostics.source_row_indices,
                split_result.row_assignments,
                strict=True,
            )
        ],
        "leakage_audit": {
            "host_overlap_count": len(split_result.leakage_audit.host_overlaps),
            "reference_overlap_count": len(
                split_result.leakage_audit.reference_overlaps
            ),
            "planet_name_overlap_count": len(
                split_result.leakage_audit.planet_name_overlaps
            ),
            "component_overlap_count": len(
                split_result.leakage_audit.component_overlaps
            ),
            "has_cross_partition_leakage": (
                split_result.leakage_audit.has_cross_partition_leakage
            ),
        },
    }
