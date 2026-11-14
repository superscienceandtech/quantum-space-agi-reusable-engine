# ARC-08 Synthetic Reproducibility and Audit Package

**Status:** Offline engineering audit for the built-in synthetic experiment
only. It is not NASA-approved, scientifically validated, or evidence of real
ARC-08 performance. Acquisition readiness remains `NOT_READY`, and scientific
acceptance remains `PENDING_REVIEW`.

## Architecture

`quantum_space_agi.ml.reproducibility_audit.audit_synthetic_evidence_bundle()`
accepts an in-memory `SyntheticEvidenceBundle` from
`synthetic_experiment_runner`. It performs no network access, filesystem scan,
or write. It returns a frozen `ReproducibilityAuditReport`; call
`serialize_reproducibility_audit()` for deterministic compact UTF-8 JSON.

The auditor inventories the runner's required payload set, verifies exact
payload byte lengths and SHA-256 values, parses canonical JSON, checks supported
bundle and artifact schema versions, resolves references between bundled
configuration, manifest, and baseline-result artifacts, and checks key
cross-payload relationships. It also records explicitly unavailable
reproducibility metadata and pending scientific/external decisions.

For the experiment manifest, the audit checks that `configuration_reference`
points to the bundled configuration payload and that its nested SHA-256 equals
the digest recalculated from those exact configuration bytes. It also checks
the manifest's top-level configuration digest and existing outer payload
digests. Recomputing outer hashes does not make a conflicting inner link valid.
The readiness payload must use `READY_FOR_ACQUISITION` or `NOT_READY`; the
auditor checks prerequisite IDs, declared/effective statuses, fixed blocking
flags, evidence-kind sufficiency declarations, overall status, and summary
lists for internal consistency. This check validates serialized structure and
declared evidence kinds only; it does not authenticate referenced evidence.

The audit does not regenerate predictions, refit a model, re-run scientific
analysis, access artifact paths, or authenticate the bundle's source.

## Reproducibility record

The report contains schema `arc08-reproducibility-record/1` with stable named
fields for experiment and bundle schemas, experiment identity, configuration
and manifest digests, fixture identity, seed/split strategy, feature and target
declarations, baseline identity/configuration, execution environment, lockfile
and repository revision, readiness, scientific review state, and source
snapshot applicability.

Each field has a value (or JSON `null`), optional artifact ID, explanation, and
one status:

- `VERIFIED`: internally cross-checked against exact supplied payload bytes or
  another supplied declaration.
- `RECORDED_NOT_INDEPENDENTLY_VERIFIED`: present as a declaration but not
  independently checked outside the bundle.
- `MISSING`: not supplied; no value is guessed.
- `PENDING_REVIEW`: scientific acceptance or policy is still pending.
- `NOT_APPLICABLE`: for example, an acquired source snapshot does not apply to
  a generated fixture.

The record is `INCOMPLETE` when required reproducibility metadata is missing.
The current synthetic bundle does not include a resolved dependency lockfile
or repository revision, so the record remains incomplete even when all
included payloads pass integrity checks. Python version and platform are
recorded from the experiment configuration and are not independently compared
to the audit process environment.

## Artifact inventory and references

Every bundled artifact gets a stable identifier (its runner payload name),
type, applicable schema version, exact byte length, declared digest, recalculated
digest, UTF-8/JSON representation, required flag, integrity status, and
references to other bundled payload identifiers. V1 requires the configuration,
manifest, baseline result, fixture metadata, validation summary, exclusion
ledger, split, model, predictions, metrics, leakage diagnostics, error/selection
diagnostics, and readiness assessment.

For each payload, the auditor hashes the exact immutable bytes in memory and
checks the declared byte length. It rejects missing required entries, duplicate
or conflicting identifiers, invalid/noncanonical JSON, unsupported schema
versions, unresolved references, and configuration/manifest/baseline-linkage
mismatches. It cross-checks validation exclusions and source-row accounting,
train/test and prediction IDs, training model declarations, metrics, readiness,
fixture identity, and pending policy states.

Bundle payload digests are generated from exact serialized bytes. Matching
SHA-256 and length verify byte integrity relative to the declaration. They do
not prove who created the payload, whether a source was authorized, whether an
approval is authentic, or whether the scientific content is valid.

## Audit report statuses

- Overall/integrity `VERIFIED` means the supported bundle structure and
  required payload integrity/linkage checks passed. It does not mean scientific
  reproducibility or acceptance.
- Overall/integrity `FAILED` means at least one required integrity, schema,
  reference, or internal consistency check failed. Findings are returned in
  deterministic code/artifact/message order.
- Reproducibility `INCOMPLETE` means one or more requested provenance fields
  are unavailable even if the supplied payload bytes verify.
- Scientific status remains `PENDING_REVIEW`; acquisition status is copied
  from the bundled readiness assessment, currently `NOT_READY`.
- Synthetic bundle execution status (`SUCCESSFUL_SYNTHETIC_EXECUTION`) is a
  separate field from the canonical acquisition-readiness status. Neither
  status establishes scientific approval or grants authorization.

The report includes experiment/fixture identity, execution status, artifact
inventory, reproducibility fields, validation and exclusion counts, split and
prediction-alignment status, baseline identity, metric names, readiness,
scientific status, unresolved decisions, findings, and limitations. A failed or
unsupported input produces a structured failed report where the input object
cannot be audited; verification never mutates the supplied bundle.

## Determinism and limitations

Audit findings, artifact inventory, metadata fields, references, and serialized
JSON use stable ordering. Serialization adds no timestamp or random identifier.
The same immutable bundle produces the same audit bytes. If payloads, local
readiness evidence, environment declarations, or code change, the audit result
can change accordingly.

Three claims remain separate:

1. **Synthetic software execution reproducibility:** deterministic execution
   and byte inventory for the same inputs, seed, code, environment, and local
   readiness snapshot.
2. **Scientific-analysis reproducibility:** not established; no frozen NASA
   cohort, authorized snapshot, or real-data evaluation is included.
3. **Scientific validity and acceptance:** not established; task, cohort,
   eligibility, split, and metric decisions remain pending review.

No original ARC-08 evidence archive, reviewer assignment, external approval,
data acquisition/reuse authorization, or repository history is authenticated
by this package. An audit pass must not be cited as approval or scientific
performance evidence.

## Run the offline audit

From the repository root, with the project environment installed:

```bash
python -c 'from quantum_space_agi.ml.reproducibility_audit import audit_synthetic_evidence_bundle, serialize_reproducibility_audit; from quantum_space_agi.ml.synthetic_experiment_runner import run_synthetic_experiment; bundle = run_synthetic_experiment(experiment_id="local-synthetic-audit-v1", seed=1729); report = audit_synthetic_evidence_bundle(bundle); print(serialize_reproducibility_audit(report).decode("utf-8"))'
```

This command generates only the built-in synthetic fixtures in memory, includes
the local readiness assessment, and prints the audit JSON. It does not write
artifacts or contact NASA or any external service.
