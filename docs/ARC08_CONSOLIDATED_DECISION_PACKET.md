# ARC-08 Consolidated Decision Packet

**Status:** Internal decision proposal only. No scientific, acquisition, retention, or redistribution approval is implied.

## 1. Project decision summary

The proposed exploratory task is to estimate selected NASA Exoplanet Archive `ps` records' archive-reported planet mass (`pl_bmasse`, Earth masses) from archive-reported radius (`pl_rade`, Earth radii). The candidate predicate is the exact expression `default_flag = 1 AND pl_bmassprov = 'Mass'`. The interpretation is agreement with selected archive values, not independent physical truth, a causal relation, or an operational prediction.

This task, feature availability, and cohort remain proposals. The 2,211 count recorded in the extraction design is a historical query observation, not a current population count or frozen eligible cohort. The documented acquisition gate is **NOT_READY**. The educational mission evaluator and its fictional score are unrelated and must not be used as an ML target.

## 2. Consolidated decision table

“Can proceed” refers to offline engineering under the stated working default; it does not authorize NASA access or establish scientific eligibility.

| Decision | Recommended working default | Classification | Can implementation proceed? | Missing evidence or approval |
| --- | --- | --- | --- | --- |
| Task and inference | Estimate selected archive-reported `pl_bmasse` from `pl_rade`; state the intended inference context before evaluation. Claim agreement with archive values only. | `SCIENTIFIC_DECISION_REQUIRED` | Mechanical interfaces/tests only; no cohort or model evaluation. | Scientific/project decision on purpose, prediction unit, timing, and feature availability. |
| Candidate cohort | Exact `ps` predicate `default_flag = 1 AND pl_bmassprov = 'Mass'`; preserve raw predicate fields. | `SCIENTIFIC_DECISION_REQUIRED` | Query/schema tooling can be developed offline; do not acquire or call the cohort eligible. | Approval that this selected population answers the intended question; a fresh count at acquisition time. |
| Missing, malformed, non-finite | Preserve raw rows; report distinct conditions; do not coerce or impute. Require usable numeric X/y for ordinary regression input. | `INTERNAL_TECHNICAL_DEFAULT` | Yes, as mechanical validation; resulting complete-case cohort still needs review. | Approved interpretation of resulting missingness/selection effects. |
| Zero/negative mass or radius | Preserve and ledger; quarantine from a proposed positive-valued analysis pending decision. Do not silently discard or call records scientifically invalid. | `SCIENTIFIC_DECISION_REQUIRED` | Ledger/report mechanics only; do not freeze an analytic cohort. | Scientific approval of final disposition. Existing validator excludes these from accepted input, so that behavior must not be mistaken for final eligibility. |
| `pl_bmasselim`, `pl_radelim` | Preserve values/nulls; do not infer or apply code mappings. Do not finalize point-measurement eligibility while their effect is unresolved. | `EXTERNAL_EVIDENCE_REQUIRED` | Offline raw-field preservation/tests only. | Authoritative active-`ps` meanings and null semantics; then scientific decision on eligibility impact. |
| Uncertainty fields | Preserve exactly and report availability; do not filter, transform, weight, or use as predictors. | `SCIENTIFIC_DECISION_REQUIRED` | Yes, for lossless handling and descriptive counts on an approved snapshot. | Approval for any exclusion, weighting, feature use, or sensitivity analysis. |
| Controversy and solution status | Preserve and report `pl_controv_flag`, `soltype`, and nulls; do not filter from unverified values. | `SCIENTIFIC_DECISION_REQUIRED` | Yes, for raw-field capture and diagnostics. | Approved inclusion/sensitivity policy based on verified values. |
| Identity, duplicates, prediction unit | Preserve exact strings; audit missing, repeated, variant, and conflicting identities; never normalize or silently deduplicate. Quarantine unresolved identity conflicts from analysis while retaining source rows. | `SCIENTIFIC_DECISION_REQUIRED` | Yes, for diagnostics/ledger using synthetic fixtures. | Approved row/prediction unit and disposition of identity conflicts. |
| Generalization and split | Proposed unseen-host objective: exact-host-disjoint split, with reference/planet overlap audit. Consider host-reference components only if the objective and observed overlap justify it. No random-row fallback. | `SCIENTIFIC_DECISION_REQUIRED` | Yes, for synthetic split/diagnostic testing; no actual NASA split. | Approved objective, policy, proportions, seed, minimum group criteria, and feasibility on retained cohort. |
| Baseline and metrics | Median `DummyRegressor`; MAE in Earth masses primary, RMSE and R² diagnostics. Defer Ridge unless justified in advance. No post-hoc acceptance threshold. | `SCIENTIFIC_DECISION_REQUIRED` | Evaluation code can be developed with synthetic fixtures after protocol approval; no real evaluation. | Metric interpretation, test adequacy, any justified threshold, and approval to evaluate. |
| Raw snapshot/provenance | Retain exact bytes internally only under approved storage/access/retention terms; record exact query, endpoint, times, schema, checksum, versions, ledger, split and experiment metadata. | `AUTHORIZATION_REQUIRED` | Offline manifest/writer tests with synthetic bytes only. | Project authorization for storage and retention; actual acquisition artifacts and metadata. |
| Reuse, citation, redistribution | Follow verified citation guidance; do not infer permission from public accessibility or silence. Treat public redistribution separately from internal retention. | `EXTERNAL_EVIDENCE_REQUIRED` | Citation metadata plumbing can be designed; no public release. | Applicable NASA terms/guidance and project stakeholder decision for intended use/release. |

## 3. Decisions ARC-08 can make internally

These are conservative **engineering defaults**, not scientific approvals:

- Preserve raw values and exact query/identity strings; never silently coerce, impute, normalize, deduplicate, or erase source rows.
- Use a versioned row-level ledger with deterministic reason codes and explicit pending-review status; reconcile all source-row counts.
- Keep feature inputs behind an explicit allowlist containing only the approved feature (currently proposed as `pl_rade`). Keep target, identifiers, uncertainty, status, limit, density, and derived fields out of predictors unless a future approved contract changes that.
- Keep learned preprocessing/model fitting within training data; never use the final test partition for choices.
- Reuse the implemented offline validation, ingestion, identity diagnostics, host splitter, snapshot integrity, evidence-report, persistence, and readiness-gate components. Any future changes should address demonstrated gaps and use synthetic fixtures unless acquisition is separately authorized.
- Record unknown values as unavailable; a software test, recommendation, checksum, or historical count cannot substitute for approval or retained source data.

These defaults do not resolve non-positive-value eligibility, limit-code semantics, whether the proposed cohort is scientifically appropriate, or legal/organizational authorization.

## 4. Hard blockers

**Before NASA acquisition:** blocking scientific/task and cohort decisions; active limit semantics and eligibility consequences; approved retention/access and applicable reuse terms; extraction completeness and service-limit acceptance; current candidate-population recheck; documented project authorization. A `READY_FOR_ACQUISITION` software result alone is not authorization.

**Before cohort freezing:** retained complete raw snapshot; approved missing/non-finite and non-positive handling; limit, uncertainty, controversy and solution policies; identity/duplicate disposition; reconciled row-level ledger; schema and policy versions. Do not call rows scientifically eligible while required decisions remain pending.

**Before model evaluation:** approved prediction unit and inference context; frozen cohort; feasible and approved leakage-safe split; frozen assignments and seed; train-only baseline/model protocol; metric definitions and any acceptance threshold decided before final-test inspection; retained reproducibility artifacts.

Public redistribution has its own terms/authorization question and is not implied by internal acquisition or retention.

## 5. Execution sequence

1. **Record decisions:** use this packet to obtain explicit project/scientific decisions for the blocking rows. Do not recast recommendations as approvals.
2. **Pass acquisition gate:** update existing evidence inputs only when real approvals/evidence exist; verify the gate result and separately record acquisition authorization.
3. **Acquire and retain:** after the gate and separate authorization pass, implement the still-missing bounded async extraction path using the existing VOTable validator and snapshot writer. Require complete status/schema checks, raw bytes, checksum, manifest, and recovery behavior before accepting an artifact.
4. **Freeze cohort:** reuse offline ingestion/validation, apply only approved eligibility policy, preserve all rows/reasons, and produce a versioned cohort artifact/fingerprint.
5. **Audit and freeze split:** reuse identity diagnostics, host splitter, and evidence reporting; add only missing cohort-specific feasibility evidence. Stop if approved overlap/group criteria fail.
6. **Evaluate baseline:** implement minimal median-dummy metrics/output; add Ridge only if prejustified. Keep the test partition untouched until protocol is fixed.
7. **Analyze and report:** produce traceable error and within-snapshot selection analyses, then independently reconcile the reproducibility manifest and claim boundaries.

No acquisition, split, prediction, or evaluation is authorized by this sequence itself.

## 6. Immediate next engineering task

The offline engineering capabilities in the original next-task recommendation now exist, including snapshot writing/verification, verified ingestion, row-level mechanical validation, identity diagnostics, exact-host split tooling, and evidence-report serialization/persistence. No further generic offline persistence task is identified by this packet. The next work that can advance the research is obtaining explicit scientific/task decisions and project authorization for acquisition and retention; keep the acquisition gate **NOT_READY** until the required evidence is documented. Any future engineering task should be tied to a demonstrated gap in the approved acquisition or evaluation protocol, not to an assumption that these offline components authorize actual NASA data handling.

## 7. References and status

This packet consolidates, without replacing, the [recommended decision policy](ARC08_RECOMMENDED_DECISION_POLICY.md), [acquisition readiness gate](ARC08_ACQUISITION_READINESS.md), [baseline task specification](ARC08_BASELINE_ML_TASK_SPEC.md), [extraction design](ARC08_BASELINE_ML_EXTRACTION_DESIGN.md), [scientific eligibility review](ARC08_SCIENTIFIC_ELIGIBILITY_POLICY_REVIEW.md), [identity/grouping review](ARC08_IDENTITY_GROUPING_LEAKAGE_REVIEW.md), [NASA limit-code review](ARC08_NASA_LIMIT_CODE_SEMANTICS.md), and [provenance/reproducibility gate](ARC08_PROVENANCE_SNAPSHOT_REPRODUCIBILITY_GATE.md).

The ARC-08.6 and ARC-08.7 review outputs were not found as separate repository artifacts during this task; the packet uses the findings conveyed in the project handoff/conversation and the current repository documents. The current acquisition assessment remains **NOT_READY**. No pending decision was changed to approved.
