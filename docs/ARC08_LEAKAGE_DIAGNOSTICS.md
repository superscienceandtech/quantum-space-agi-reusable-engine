# ARC-08 Split Integrity and Leakage Diagnostics

**Status:** Engineering diagnostics only. The checks do not approve the
proposed scientific task, cohort, eligibility rules, or split policy. Tests use
synthetic fixtures only.

## API and scope

`quantum_space_agi.ml.leakage_diagnostics.diagnose_split_integrity()` accepts
an ordered row sequence, declared train/test row IDs, prediction row IDs, and
explicit experiment/split metadata. It analyzes the supplied assignment; it
does not create or repair a split. The sequence passed as `rows` is the
population being checked, so every supplied row must be assigned exactly once
for the structural membership status to pass. The caller remains responsible
for deciding which rows enter that population.

The returned frozen `LeakageDiagnosticReport` includes:

- Source/train/test counts, exact row-ID overlap, missing/invalid/duplicate
  source IDs, duplicate partition IDs, unknown assignment IDs, and
  unassigned/multiply assigned source positions.
- Prediction membership with missing, unexpected, or duplicated prediction
  row IDs.
- Per-field identity coverage and exact train/test overlaps for `pl_name`,
  `hostname`, `pl_refname`, and an optional explicit `component_id` field.
- Existing ARC-08 host/reference graph-component overlap findings from
  `identity_diagnostics.audit_partition_assignments()` when row membership is
  structurally valid.
- Exact duplicate-record groups, cross-partition duplicate payloads with the
  row-ID field omitted, and repeated exact scalar feature/target pairs.
- Determinism status. It is `NOT_CHECKED` unless callers supply a repeated
  assignment and seed; then the ordered assignments and seeds are compared.

`serialize_leakage_diagnostics()` emits deterministic compact UTF-8 JSON. A
caller may provide an `ExperimentManifestLinkage` built from existing
configuration/manifest output. Its checksum strings are declarative references;
this diagnostics module does not read or authenticate artifacts.

## Interpreting identity and overlap results

Identity strings are compared byte-for-byte as Python strings. The code does
not trim, case-fold, alias-resolve, merge, or deduplicate. Missing values and
invalid types are counted separately. Reported overlap includes affected row
IDs and counts; an overlap is an observation that may be relevant to a chosen
inference objective, not proof that a split is scientifically invalid. No
observed exact overlap does not prove independence because aliases, related
measurements, shared methods, and unrecognized relationships may remain.

The host/reference connected components use the existing graph construction
from `identity_diagnostics.py`; explicit `component_id` values are separately
compared as exact identifiers. This module does not assign connected
components to partitions or replace the existing host splitter. A
row-level random split can show host, reference, planet, or component crossings;
it does not establish host/reference/component disjointness.

Exact duplicate comparisons use JSON-like record contents without coercion or
normalization. Values that cannot be compared deterministically are listed by
source row index. Cross-partition payload comparison omits only the configured
row-ID field, making same-content rows with different IDs visible. Identical
feature/target pairs are a structural warning, not proof of leakage. Automated
checks cannot detect all semantic target leakage or scientifically related
measurements.

No findings cause records to be removed, identities to be changed, or
assignments to be altered. A `PASS` split-integrity status means only that the
declared row IDs account for the supplied rows exactly once. It does not mean
that the assignment is leakage-safe or scientifically approved. Scientific
policy status remains `PENDING_REVIEW`.

## Synthetic coverage and limits

The focused tests use a separate small synthetic identity fixture to exercise
host, planet, reference, explicit component, missing-identity, no-overlap,
duplicate-content, and prediction-alignment cases. The existing synthetic
baseline split is unchanged. No host-grouped demonstration or automatic split
is added. No NASA records, network requests, model training, or scientific
evaluation are used.
