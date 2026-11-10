# ARC-08 Dataset Acquisition Readiness Gate

**Status:** Offline readiness assessment only. It makes no NASA request, does
not acquire data, and does not approve scientific truth, model training, or
performance claims.

## Purpose

`quantum_space_agi.ml.acquisition_readiness` evaluates whether documented
decisions and evidence satisfy the repository's current prerequisites for
considering the proposed NASA Exoplanet Archive acquisition. The assessment is
deterministic and does not access the network or read project documents at
runtime.

The gate reports `NOT_READY` when required decisions are absent, insufficient,
or only caller-declared. `READY_FOR_ACQUISITION` remains a status in the
contract, but this implementation cannot produce it: there is no independent
evidence/authenticity verifier or external authorization integration. A future
implementation must add and review such a verification mechanism before the
status can be made reachable.

## Evidence and status rules

Each input `PrerequisiteDecision` records a caller-declared identifier, status,
evidence references, decision-authority text when supplied, and an explanation.
Evidence has a declared kind, such as `FORMAL_APPROVAL`, `AUTHORITATIVE_SOURCE`,
`TECHNICAL_VERIFICATION`, `CURRENT_QUERY_OBSERVATION`, `SOFTWARE_TEST`,
`RETAINED_SNAPSHOT_AUDIT`, `RECOMMENDATION`, or `HISTORICAL_OBSERVATION`.

Each evidence reference has two separate annotations. `availability` describes
only local path presence: caller-created references default to `NOT_CHECKED`,
while the maintained current-repository snapshot
reports `AVAILABLE` only when a safe repository-relative file reference resolves
to a file in the current checkout; absent files are `MISSING`, while external,
composite, unsafe, or otherwise unresolvable references are
`UNRESOLVABLE`. This is a local path-presence check only. It does not inspect
file contents or establish authenticity, approval, scientific validity, or
authorization, and it does not indicate whether a file is tracked by Git (an
untracked local file can be `AVAILABLE`). `verification_status` is fixed to
`DECLARED_NOT_AUTHENTICATED`; no API input can set it to a verified state. Path
availability, an evidence-kind label, an authority string, or a caller's
`APPROVED` decision does not authenticate the reference or its source.
`evidence_sufficient` means only that the supplied evidence-kind declarations
match the prerequisite's required categories; it is not a verification claim.

- Missing decisions become `PENDING`.
- `APPROVED` without all required evidence-kind declarations becomes effective
  `BLOCKED`.
- Even when those kinds and authority text are supplied, an `APPROVED`
  declaration becomes effective `BLOCKED` because the current software cannot
  independently authenticate evidence or authority.
- A named decision authority is recorded as caller-provided text only; it does
  not authenticate the person or establish organizational authorization.
- Recommendations, project summaries, and software tests do not substitute
  for formal scientific or stakeholder approval.
- A historical aggregate cannot satisfy the current candidate-population
  recheck; that prerequisite requires `CURRENT_QUERY_OBSERVATION` evidence.
- Software tests cannot establish eligible host/group counts; that later audit
  requires `RETAINED_SNAPSHOT_AUDIT` evidence tied to an approved snapshot.
- `NOT_APPLICABLE` is accepted only for fixed non-blocking prerequisites that
  allow it and include an explicit reason. It cannot waive a blocker.
- Callers cannot set or clear `blocks_acquisition`; that property comes from
  the fixed prerequisite definitions in code.

The API checks evidence labels and reference structure, not authenticity or the
contents of referenced documents. Independent human/project review and any
required external authorization must occur outside this software and be
documented in a way a future verifier can check. The helper
`assess_current_repository_readiness()` is a
maintained repository-evidence snapshot, not a live document parser; update it
only when its referenced evidence actually changes.

## Prerequisites

Blocking items cover approval of the prediction task and candidate cohort;
missing/non-finite and zero/negative value policies; uncertainty handling;
authoritative active-table limit semantics and the scientific effect of those
limits; controversy and solution status; identity and duplicate handling;
host-disjoint split policy; baseline/metric and acceptance-decision policy;
scientific scope and permitted claims; archive access/reuse terms; internal
snapshot retention; citation requirements; extraction completeness behavior;
a current candidate-population recheck; offline ingestion contract evidence;
and acceptance of the cross-query snapshot limitation.

Public redistribution terms are separately represented as a non-blocking item
when public release is not planned for acquisition. This does not permit a
later release. Quantitative group feasibility is also non-blocking for starting
acquisition because it requires a retained eligible snapshot; it remains a
limitation and must be resolved before any grouped evaluation.

The current repository snapshot is deliberately `NOT_READY`. The project
documents describe the target/cohort and eligibility rules as proposals,
leave active `ps` limit-code meanings unresolved, do not establish full-scale
extraction limits or a current candidate count, and record no approved raw
snapshot retention plan or scientific decision record. The previously observed
2,211 count is historical planning evidence, not current population or final
eligibility evidence. See the Phase 3.12–3.17 documents, especially
[`ARC08_RECOMMENDED_DECISION_POLICY.md`](ARC08_RECOMMENDED_DECISION_POLICY.md),
[`ARC08_NASA_LIMIT_CODE_SEMANTICS.md`](ARC08_NASA_LIMIT_CODE_SEMANTICS.md),
[`ARC08_PROVENANCE_SNAPSHOT_REPRODUCIBILITY_GATE.md`](ARC08_PROVENANCE_SNAPSHOT_REPRODUCIBILITY_GATE.md),
and [`ARC08_BASELINE_ML_EXTRACTION_DESIGN.md`](ARC08_BASELINE_ML_EXTRACTION_DESIGN.md).

## API

```python
from quantum_space_agi.ml import (
    assess_acquisition_readiness,
    assess_current_repository_readiness,
    serialize_acquisition_readiness,
)

current = assess_current_repository_readiness()
assert current.status.value == "NOT_READY"

# For a reviewed decision packet, pass typed PrerequisiteDecision values.
assessment = assess_acquisition_readiness(decisions=())
manifest_bytes = serialize_acquisition_readiness(assessment)
```

The assessment and all nested records are frozen dataclasses backed by tuples.
Serialization is compact, sorted-key UTF-8 JSON with non-ASCII characters
preserved and no BOM. The JSON records declared and effective statuses,
evidence references, blocking policy, and current explanations; it does not
create signatures or approval records.

## Gate boundary

The software gate is not an authorization mechanism. It cannot establish NASA
permission, project authorization, evidence authenticity, verified source
provenance, or scientific approval. The current implementation therefore keeps
caller-assembled approvals unresolved and does not emit
`READY_FOR_ACQUISITION`. A future gate result with that status would still not
substitute for actual organizational authorization or establish scientific
acceptance. A passing software test establishes software behavior only; it
does not validate the scientific task or cohort.

This phase does not implement a client, perform a count query, download or
extract data, create a dataset, interpret undocumented field values, resolve
scientific eligibility, create train/test splits, or train/evaluate a model.
The gate does not establish transactional snapshot consistency, final eligible
row counts, redistribution rights, or scientific performance.
