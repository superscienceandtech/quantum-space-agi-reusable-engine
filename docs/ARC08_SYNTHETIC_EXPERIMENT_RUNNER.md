# ARC-08 Synthetic Experiment Runner and Evidence Bundle

**Status:** Offline engineering integration using synthetic fixtures only.
This runner does not provide a real-data execution mode, scientific acceptance,
or acquisition authorization. The current acquisition readiness remains
`NOT_READY`; experiment and policy decisions remain pending review.

## Architecture and workflow

`quantum_space_agi.ml.synthetic_experiment_runner.run_synthetic_experiment()`
is the orchestration entry point. Callers must provide an experiment ID and
non-negative seed. The runner uses the built-in ARC-08 synthetic mass-radius
fixture plus its separate synthetic diagnostic metadata fixture.

The workflow delegates analysis to existing components:

1. `run_synthetic_baseline()` validates the fixture, deterministically splits
   accepted rows, fits the median dummy baseline on training targets only,
   predicts held-out rows, computes baseline metrics, and creates configuration
   and manifest bytes.
2. The runner validates the validation report, accepted/excluded accounting,
   train/test membership, prediction alignment, training-target list, and
   fitted training median.
3. `diagnose_split_integrity()` checks the declared assignment and identity
   overlaps for accepted rows. It does not create or repair the split.
4. `diagnose_error_selection()` consumes the original rows, validation ledger,
   and already-produced predictions to summarize residuals, synthetic metadata,
   coverage, and exclusions.
5. The existing acquisition-readiness API is included as a separately
   serialized payload. It does not grant permission to acquire data.
6. The runner assembles immutable exact-byte payloads into a versioned
   in-memory evidence bundle.

The runner does not use the snapshot artifact or evidence-report persistence
APIs. This synthetic fixture is generated data, not an acquired raw snapshot;
creating a snapshot artifact or claiming snapshot provenance would imply a
source artifact that does not exist. Callers may persist a serialized bundle
separately, but this API performs no filesystem writes.

## Evidence bundle schema

Schema version: `arc08-synthetic-experiment-evidence-bundle/1`.

The frozen `SyntheticEvidenceBundle` contains the explicit experiment ID,
fixture ID, seed, runner version, successful synthetic execution status,
completed workflow and diagnostic stage statuses, scientific acceptance state,
current acquisition readiness state, limitations, and a name-sorted tuple of
`SyntheticEvidencePayload` records. Payloads cover:

- Experiment configuration and manifest.
- Synthetic fixture metadata.
- Validation summary and source-row exclusion ledger.
- Train/test assignments, model declaration/configuration, predictions, and
  metrics.
- Leakage/identity and error/uncertainty/selection diagnostics.
- Acquisition-readiness assessment.

Each payload is exact serialized bytes with media type, an explicit synthetic
designation, byte length, and SHA-256 calculated from those exact bytes. The
bundle serializer encodes payload bytes as Base64 inside deterministic compact
UTF-8 JSON. These calculated digests detect changes to the serialized payload;
they do not authenticate a source, prove an approval, or prove that an artifact
exists outside the bundle.

The bundle does not generate timestamps. Configuration timestamps remain
absent. Repeated execution with identical seed, experiment ID, code, Python
environment, and local readiness-document availability yields byte-identical
serialization. Environment or readiness-document changes can change payload
bytes and therefore bundle output.

## Failure behavior

All stages required by V1 must complete. A validation, split-integrity,
prediction-alignment, diagnostic, manifest-linkage, or bundle-construction
failure raises `SyntheticExperimentError`, whose `execution_status` is
`FAILED` and whose `stage` names the failing stage. The runner never returns a
success-labelled partial bundle. V1 has no optional diagnostic stage; all
declared diagnostics must complete. Its immutable success bundle records each
completed stage explicitly.

The runner checks that accepted source rows are partitioned exactly once,
train/test IDs do not overlap, and prediction IDs match test IDs. It also
rechecks the baseline's serialized training targets against the training row
IDs and verifies that the fitted constant is their median. The underlying
median implementation remains the existing standard-library implementation;
no new model-fitting logic is introduced.

## Scientific and reproducibility limits

- Every input row and output is synthetic; no NASA, network, or external data
  access occurs.
- Mechanical validation exclusions are preserved with reasons, but mechanical
  acceptance is not scientific eligibility or an approved cohort.
- The seeded random-row split is a software smoke test, not a host-disjoint or
  approved scientific evaluation protocol.
- Residual, metric, group, uncertainty-metadata, and feature-coverage summaries
  describe only invented fixture values. They are not scientific performance
  findings or a real selection-bias estimate.
- Configuration/manifest status strings are declarations. They do not
  authenticate decisions, evidence, authority, or artifact contents.
- Bundle payload digests establish integrity only for the exact serialized
  bytes packaged in memory. They do not establish source authenticity or
  archival provenance.
- No actual split-feasibility decision about a NASA cohort is made, and no
  real-world reproducibility claim is supported.

Any future authorized real-data workflow must be designed and approved
separately. This synthetic runner deliberately accepts no caller-supplied
dataset and cannot be switched into a real-data mode.
