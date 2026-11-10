# ARC-08 ML Readiness Decision

**Decision date:** 2026-11-08
**Branch reviewed:** `arc/08-ai-ml` at `1d438dc`
**Decision:** **NO-GO — baseline ML remains blocked.**
**Scope:** Requirements decision and conditional future implementation specification. No model or ML API is implemented or approved here.

## 1. Executive Decision

**NO-GO.** Do not implement or train a baseline ML model yet. The repository has reusable data ingestion, structural validation, quality analysis, deterministic scalar preprocessing, and a bounded NASA Exoplanet Archive TAP adapter. A Mission Outcome Prediction direction has been proposed for design planning: one pre-execution mission configuration per sample, with numeric final mission score as the proposed target. This is not an approved scientific task or verified simulator capability. Separately, Section 10 records an exploratory NASA mass–radius candidate (`pl_rade` to `pl_bmasse`); it also remains unapproved and has no retained candidate dataset or evaluation. The simulator interface, actual configuration fields, score semantics, suitable dataset, and task-specific evaluation criteria remain unconfirmed.

The primary dataset evidence is [`ARC08_EXOPLANET_DATASET_EVALUATION_REPORT.md`](ARC08_EXOPLANET_DATASET_EVALUATION_REPORT.md). It records a successful 30-row, 13-field retrieval, JSON type/null preservation, and zero exact duplicate rows in that sample. The result was not persisted; the ordered alphabetic sample does not establish archive coverage or representativeness, and its archive release is unknown. This is structural exploration, not evidence that the archive is scientifically suitable for a task.

`docs/ML_REQUIREMENTS.md` explicitly says no prediction task or training dataset is approved and prohibits starting training until the use case, suitable data, target, baseline, leakage-safe evaluation design, metrics, and acceptable errors are agreed (especially “Current readiness,” “Candidate task definition,” and “Readiness gate”). That is sufficient evidence to block implementation of task-specific baseline behavior.

## 2. Existing Evidence

### Repository and project

- **VERIFIED:** The initial repository inspection was on branch `arc/08-ai-ml`, HEAD `1d438dc` (`feat(arc-08): add NASA Exoplanet Archive data adapter`). The existing dataset evaluation report was already untracked when this decision document was started; it is preserved.
- **VERIFIED:** `docs/ML_REQUIREMENTS.md` describes an educational mission-design game and proposes a conceptual Mission Outcome Prediction direction with numeric final mission score as the target. No scientific/product prediction task or target has been formally approved or fully specified, and baseline ML implementation and training remain NO-GO. It says deterministic computation, simulation, or optimization may be preferable where appropriate.
- **VERIFIED:** `docs/ARC08_EXOPLANET_DATASET_EVALUATION_REPORT.md` is the primary evidence for the NASA sample. It reports the exact query, retrieval time, response checksum, observed types/nulls, sample quality, unknown release, and the fact that the rows/response bytes were not saved.
- **VERIFIED:** Repository fixture data under `data/samples/` is synthetic/example data. The repository contains no approved real ML dataset snapshot.

### Existing APIs

- **VERIFIED:** `Dataset`, `Provenance`, `DataSource`, and `DataFormat` are defined in `src/quantum_space_agi/data/models.py`, `provenance.py`, and `sources.py`. The structured JSON/CSV entry points are in `src/quantum_space_agi/data/ingestion.py`; legacy `load_dataset()` in `src/quantum_space_agi/data/loader.py` returns `DatasetLoadResult`, not `Dataset`.
- **VERIFIED:** `validate_dataset(dataset, schema)` in `src/quantum_space_agi/data/schemas.py` checks declared structure and types. `analyze_quality(dataset)` in `src/quantum_space_agi/data/quality.py` reports missing values, exact duplicate groups, and numeric summaries. These APIs do not establish scientific validity or ML readiness.
- **VERIFIED:** `preprocess_dataset(dataset, *, conversions)` in `src/quantum_space_agi/ml/preprocessing.py` performs explicit, deterministic scalar conversions and records a transformation description in provenance. It does not impute, scale, encode, select features, split data, or train models.
- **VERIFIED:** `fetch_ps_dataset(...)` in `src/quantum_space_agi/data/adapters/exoplanet_archive.py` performs bounded JSON retrieval from the fixed `ps` table and records query and response provenance. It does not retain source response bytes, select a scientifically approved subset, or establish training suitability.
- **VERIFIED:** `pyproject.toml` declares no runtime dependencies. It has optional test and quality tool groups. No ML library is currently a required dependency.
- **VERIFIED:** Offline mechanical dataset validation, identity diagnostics, deterministic exact-host split tooling, snapshot integrity, and evidence-report serialization/persistence APIs exist under `src/quantum_space_agi/ml/`. No approved scientific-task feature/target extraction, predictor, task-specific ML metric or model-evaluation result API exists, and no NASA cohort, feasibility assessment, or split assignment has been produced. The educational mission evaluation result API (`EducationalMissionResult`) reports deterministic rule-based exercise outcomes; it is not an ML model-evaluation metric or result API. Baseline ML remains NO-GO.

## 3. ML Readiness Gate Assessment

All gates below are applicable to supervised baseline evaluation unless the team approves a different task type. **No gate is marked PASS based on inference.**

| Gate | Status | Available evidence | Missing evidence / required decision |
| --- | --- | --- | --- |
| Approved scientific/product use case | **BLOCKED** | Mission Outcome Prediction is a proposed decision-support direction, not an approved task; the project brief describes the mission-design game. | Confirm the product decision and whether prediction adds value over directly running the simulation. |
| Prediction unit and inference timing | **PROPOSED; NOT VERIFIED** | The working direction proposes one complete configuration per sample, predicted before execution. No simulator contract verifies this unit or available inputs. | Confirm the actual configuration boundary and information available at prediction time. |
| Feature definitions | **BLOCKED** | No mission simulator fields are present in the ARC-08 branch. Exoplanet fields are unrelated to this proposed task. | The simulation owner must identify verified fields, types, units, derivations, and availability; do not infer them. |
| Target/label and scientific meaning | **PROPOSED; NOT VERIFIED** | Numeric final mission score/outcome is the proposed target; score semantics, scale, rubric, and generation method are unconfirmed. | Confirm how the simulator produces the score and what it means before treating it as a label. |
| Suitable dataset, provenance, and version | **BLOCKED** | The NASA response was not persisted and is not approved for this mission-score direction. No simulator-generated mission dataset is present in the repository. | Confirm lawful/suitable simulator data generation, coverage, schema, retention, source/version metadata, and exact artifact reproducibility. |
| Appropriate non-ML baseline | **BLOCKED** | A constant regression reference is proposed, but it is not established as the task-relevant comparator. Direct simulation may itself meet the decision need. | Agree on the meaningful non-ML comparator and minimum useful improvement. |
| Leakage-safe train/validation/test strategy | **BLOCKED** | No simulator scenario/configuration group ID or grouping rule is confirmed. Related configurations could leak across a random row split. | Confirm grouping and evaluation scenario; keep related groups together and the final test partition controlled. |
| Task-appropriate metrics | **PROPOSED; NOT VERIFIED** | MAE is proposed as primary, RMSE secondary, and R² diagnostic for the proposed score target. Score semantics and evaluation data are unconfirmed. | Confirm metric definitions, aggregation, and interpretation against the score and intended use. |
| Error costs and acceptance thresholds | **BLOCKED** | No error costs or minimum improvement are specified. | Decide false-positive/false-negative or regression-error consequences, acceptable ranges, and human review expectations. |
| Reproducibility requirements | **BLOCKED** | Requirements call for dataset identity, code/dependency versions, seeds, split assignments, parameters, and results. Simulator identity/version, seed guarantees, run metadata, and a retained simulation dataset are unconfirmed. | Confirm simulator metadata and artifact retention; define the experiment record needed to reproduce evaluation. |

**Decision rule:** baseline implementation that encodes task assumptions remains blocked until all relevant gates have named owners and documented decisions. Task-independent reuse of existing loader, schema, quality, and preprocessing APIs may continue; it does not require creating a generic ML framework.

## 4. Exoplanet Dataset Research Potential

The following are **hypothetical research directions only**, not approved use cases, labels, feature lists, or implementations. The archive documents multiple solutions and candidate records; these are reasons for domain review, not permission to treat table fields as truth labels.

| Hypothetical direction | Possible question and data concepts | Main risks / required review | Likely method comparison |
| --- | --- | --- | --- |
| Estimate a reported planetary parameter | Could other observations or system descriptors estimate a parameter such as `pl_rade` or `pl_orbper`? Those columns and their uncertainty fields exist in `ps`; a future task would need a label source and feature availability rule. | Same-source calculated quantities, literature solution overlap, repeated planets/systems, asymmetric uncertainty, missing-not-at-random measurements, and whether the parameter is known at inference time. A domain reviewer must establish whether the label is an observation, derived quantity, or prediction target. | Compare a simple domain/statistical calculation first. ML is only relevant if the intended decision and a measurable gain are defined. |
| Characterize candidate/solution dispositions | Could available evidence help prioritize follow-up or distinguish solution states represented by fields such as `soltype`? No such decision or target is approved. | `soltype` may encode a disposition assigned after observing evidence; predicting it from post-disposition or proxy fields could leak the answer. Archive selection and changing status over time require historical snapshots and defined inference time. | A transparent rule or review-prioritization process may be more suitable. ML would require time-stamped training examples and an explicitly approved label. |
| Describe system-level structure | Could grouping or statistical summaries reveal useful patterns in multi-planet systems or measurement solutions? This is exploratory analysis, not a present product requirement. | Clusters do not establish physical classes; rows are dependent; distance/scaling choices can dominate; archive completeness and detection bias affect apparent structure. | Start with descriptive statistics, visualization, domain equations, or simulation. Unsupervised ML is not automatically more informative. |

No direction above has an approved prediction unit, inference scenario, target, feature contract, or evaluation criterion. No direction is ready for implementation.

## 5. Reasons Baseline ML Is Currently Blocked

1. The proposed decision-support use has not been approved or shown to add value over direct simulation.
2. The unit and timing are proposed at a high level, but no simulator contract confirms the configuration boundary or available-at-prediction fields.
3. Numeric final mission score is a proposed target, but its definition, rubric, scale, and label-generation process are unconfirmed.
4. No simulator-generated mission dataset or retained simulation snapshot is available. The exploratory Exoplanet Archive sample is not approved for this task.
5. No scenario/configuration group ID or grouping rule is confirmed. Randomly splitting related configurations could overstate generalization.
6. The simulator's score generation, configuration missingness, and relevant scientific assumptions are not documented for this task; they must not be guessed or silently transformed.
7. A constant reference and MAE/RMSE/R² are proposed, but the meaningful non-ML comparator, metric interpretation, error costs, and acceptance thresholds still require review.
8. `docs/ML_REQUIREMENTS.md` explicitly requires these decisions before training. A numeric table alone does not justify supervised learning.

## 6. Future Baseline Implementation Specification

This section is a conditional design outline only, not API approval. Some task-independent offline foundations described below are now implemented (mechanical validation, identity diagnostics, host-based splitting, snapshot/evidence integrity and persistence). The task-specific feature/target contract, predictor, ML metrics/results, and model evaluation remain unimplemented and blocked. Add only components needed for an approved task; do not start with a generic model framework.

### Component plan

| Component | Purpose and proposed contract | Existing dependency / location | Acceptance tests after approval |
| --- | --- | --- | --- |
| Task and feature/target specification | Describe a single approved objective, prediction unit/time, ordered feature names, target name/meaning/type/units, label provenance, and fields unavailable at inference. Proposed module: `src/quantum_space_agi/ml/task.py`; input: immutable task specification + `Dataset`; output: task-bound rows with explicit feature/target separation, or structured validation errors. | Reuse `data.models.Dataset`, `data.schemas.validate_dataset`, and source/provenance metadata. Keep dependency one-way: `ml → data`. | Reject unknown/missing fields and incompatible types; preserve source records; prove target and excluded fields cannot enter feature matrix; test null and unit metadata requirements; retain source identity/provenance. |
| Dataset readiness and schema checks | Reuse the existing mechanical ARC-08 baseline validator and ARC-03 schema/quality tools; do not add an `is_ml_ready` boolean. Scientific cohort policy remains separate. | `src/quantum_space_agi/ml/dataset_validation.py`; ARC-03 `validate_dataset()` and `analyze_quality()` remain available. | Preserve raw values and deterministic findings; scientific constraints remain explicit and separately reviewed. |
| Leakage-aware split | Select a split only after the approved prediction unit and inference scenario are known. An exact-host split implementation exists; it does not establish reference/component independence or real-cohort feasibility. | `src/quantum_space_agi/ml/group_splitter.py` and `identity_diagnostics.py`; no data-layer dependency on ML. | On an approved cohort, verify group overlap, no silent row loss, frozen assignments, and test isolation; do not assume host-only splitting proves all leakage absent. |
| Non-ML baseline | Set a task-specific reference score using the simplest approved transparent rule, calculation, or simulation. Proposed module: `src/quantum_space_agi/ml/baselines.py`; input: task contract and training partition (or declared constants); output: predictions and baseline metadata. | Domain computation may live in a separately approved module; avoid introducing dependency on a model library unless needed. | Baseline uses only inference-available inputs; deterministic; edge cases documented; metric calculated on the same held-out partitions as candidates. |
| Simple ML baseline | Add only if ML is approved and a baseline can be meaningfully evaluated. Proposed module: `src/quantum_space_agi/ml/models.py`; input: training features/targets plus explicit configuration; output: fitted predictor and configuration metadata. Do not select an algorithm in this document. | Select dependency only after task/algorithm decision. Current `pyproject.toml` has no runtime dependencies. | Fit only on training data; preprocessing fit inside training folds; predictions have declared shape/type; fixed seed behavior where applicable; no target/identifier leakage. |
| Task-specific evaluation | Compute preselected metrics and compare against non-ML baseline. Proposed `src/quantum_space_agi/ml/evaluation.py`; input: true labels, predictions, task metric specification, partition identity; output: a result record with metric values, counts, uncertainty where agreed, and baseline comparison. | Pure Python if sufficient; chosen dependencies only after requirements are known. | Correct hand-calculated metric fixtures; undefined/degenerate cases; class imbalance or missing predictions; same test rows for comparisons; metric direction and threshold checked without retuning on final test. |
| Experiment reproducibility record | Record exact data artifact/checksum, source query/terms, schema and preprocessing IDs, code revision, environment, seed, split assignments, model configuration, metric definitions/results. Proposed `src/quantum_space_agi/ml/experiment.py` or a format agreed with existing provenance. | Extend/reuse provenance only after confirming whether training-run metadata belongs in `Provenance` or a distinct evaluation artifact. Preserve ARC-03 contracts unless separately approved. | Round-trip/serialization; stable references to input artifacts; required fields enforced; no secrets; replay metadata is sufficient to identify data and configuration. |

### Implementation order after approval

1. Approve and document one task, target, prediction unit/time, feature availability, data rights, and scientific interpretation.
2. Persist and version an appropriate dataset snapshot; define a reviewed schema and row/group identity rules.
3. Reuse `validate_dataset()`, `analyze_quality()`, and explicit `preprocess_dataset()` conversions as applicable; decide missing-value handling explicitly.
4. Define leakage constraints and split assignment before fitting any learned transformation.
5. Implement a transparent non-ML baseline and preselected metric/acceptance threshold.
6. Only if baseline ML is still justified, select the smallest suitable model/dependency and compare it on the same held-out partitions.
7. Add experiment provenance, tests, and documentation, then verify without modifying ARC-03 behavior.

## 7. ARC-08 Coordination with Amran

**No immediate implementation contribution is required from Amran** to record this NO-GO decision. No adapter or preprocessing change is necessary until the simulator contract is confirmed.

For the proposed Mission Outcome direction, Amran or the responsible simulation owner should confirm the configuration and execution interfaces, outcome/score semantics, scenario grouping, and reproducibility metadata before ARC-08 builds an adapter. This is a coordination dependency, not an assertion that the work is absent elsewhere. Rafi owns the ARC-08 adapter, provenance mapping, preprocessing, and baseline/evaluation work if justified. Yousuf provides architecture approval and scientific review. Do not modify or duplicate the simulation component from ARC-08.

## 8. Beginner Learning Roadmap

1. **Dataset and scientific observation:** learn what each row represents, how observations were selected, and what the archive includes. In `ps`, multiple solutions and candidate records mean row count is not automatically independent planet count.
2. **Features and target:** features are information available to a prediction; the target is the value/decision the task asks to estimate. A column such as `pl_rade` is not a target until the team defines why it should be predicted and how it is labeled.
3. **Classification versus regression:** classification predicts a category; regression predicts a numerical quantity. For example, a hypothetical `soltype` category task differs from estimating a hypothetical radius value. Neither is approved here.
4. **Training, validation, and test:** training fits the model; validation supports choices; a final test estimates performance after choices are fixed. The split must match how future cases differ from training cases.
5. **Data leakage:** leakage occurs when training uses information unavailable at prediction time or related examples cross partitions. Related solution, planet, host, and publication rows require explicit consideration.
6. **Baseline models:** first define a simple transparent rule/calculation that answers the same task. A complex model is useful only if it improves on that baseline in a way that matters.
7. **Evaluation metrics:** choose metrics based on target type and error consequences before examining final test results. A metric score without context or an agreed threshold is not a success criterion.
8. **Reproducibility:** retain or identify the exact data snapshot and record query, checksum, schema, transformations, split, code/environment, seed, model settings, and metrics. A checksum alone cannot restore data that was not saved.

These points are learning guidance, not additional product requirements.

## 9. Conditions for Starting Baseline ML

Baseline ML may be reconsidered only after the team has documented and approved:

- The concrete product/scientific decision and why prediction is useful.
- Prediction unit, inference time, and information available then.
- Target/label definition, provenance, scientific interpretation, and generation method.
- Feature definitions, units, derivation, availability, and exclusions.
- Lawful, relevant dataset source; terms; snapshot/retention plan; schema; coverage and limitations.
- Missing-value, duplicate, uncertainty, limit-flag, and row-selection policies.
- A task-appropriate non-ML baseline and minimum useful improvement.
- Leakage constraints and train/validation/test design.
- Metrics, error costs, acceptance thresholds, and oversight expectations.
- Reproducibility metadata and responsibilities for review/approval.

If a deterministic calculation or simulation directly meets the need, the team should compare that option before authorizing ML. Passing structural validation or obtaining a successful adapter response is not sufficient to pass this gate.

## 10. Phase 3.1 NASA Dataset Audit and Candidate Task

**Audit date:** 2026-11-08. **Status:** evidence review and task proposal only; no dataset snapshot was retained, no task is formally approved, and no model was trained.

### Verified archive facts

- NASA documents `ps` as one row per planet per reference, whereas `PSCompPars` has one row per planet and more filled-in but not necessarily self-consistent parameters. The current adapter is fixed to `ps`. [NASA Planetary Systems definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html)
- NASA defines `default_flag=1` as a parameter set selected as the default. It is an archive selection flag, not an independent scientific quality guarantee.
- NASA defines `pl_bmasse` as a best-available Earth-mass field that can represent mass, M*sin(i)/sin(i), or M*sin(i); `pl_bmassprov` records which applies. Therefore unfiltered `pl_bmasse` is not a uniform true-mass target. NASA documents `pl_rade` in Earth radii and `pl_orbper` in days. [NASA column definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html)
- NASA asks publications using the archive to include its standard acknowledgment and cite relevant source literature. Applicable reuse terms and project-specific citation practice still need review. [NASA acknowledgment guidance](https://exoplanetarchive.ipac.caltech.edu/docs/acknowledge.html)

### Observed current aggregate coverage

The following read-only ADQL aggregate queries were sent to `https://exoplanetarchive.ipac.caltech.edu/TAP/sync` with JSON output on 2026-11-08. Only aggregate JSON counts were returned; no row snapshot or raw response artifact was saved. Counts are current-query observations, not a stable archive release, and `COUNT(column)` establishes non-null coverage only, not valid measurement, acceptable uncertainty, representativeness, or eligibility after scientific filters.

A separate bounded request through `fetch_ps_dataset()` returned 30 rows, ordered by `pl_name, pl_refname`. Its exact ADQL was `SELECT TOP 30 pl_name, pl_refname, hostname, default_flag, pl_bmasse, pl_bmassprov, pl_rade, pl_orbper, st_teff, st_mass FROM ps ORDER BY pl_name, pl_refname`. The adapter recorded `retrieved_at=2026-11-08T17:28:25.808963+00:00` and response SHA-256 `e3ec6bfe06f2116867aa44e09f2963ea0c284aa9f502678a98aacfba4ea7f2eb`. Non-null counts in these 30 alphabetically ordered rows were: `pl_bmasse` 5, `pl_bmassprov` 5, `pl_rade` 21, `pl_orbper` 24, `st_teff` 25, and `st_mass` 23. The response bytes and rows were not persisted. This small slice is for adapter/field inspection only and is not representative.

```sql
SELECT COUNT(*) AS n_rows,
       COUNT(pl_rade) AS n_pl_rade,
       COUNT(pl_bmasse) AS n_pl_bmasse,
       COUNT(pl_orbper) AS n_pl_orbper,
       COUNT(st_teff) AS n_st_teff,
       COUNT(st_mass) AS n_st_mass,
       COUNT(st_rad) AS n_st_rad
FROM ps
```

Observed counts: 40,387 rows; `pl_rade` 27,877; `pl_bmasse` 7,679; `pl_orbper` 36,990; `st_teff` 36,706; `st_mass` 33,767; `st_rad` 36,920.

```sql
SELECT COUNT(*) AS n_rows,
       COUNT(pl_rade) AS n_pl_rade,
       COUNT(pl_bmasse) AS n_pl_bmasse,
       COUNT(pl_orbper) AS n_pl_orbper,
       COUNT(st_teff) AS n_st_teff,
       COUNT(st_mass) AS n_st_mass,
       COUNT(st_rad) AS n_st_rad
FROM ps
WHERE default_flag = 1
```

Observed default-subset counts: 6,464 rows; radius 4,838; `pl_bmasse` 3,203; period 6,096; stellar temperature 5,686; stellar mass 5,583; stellar radius 5,619.

```sql
SELECT pl_bmassprov,
       COUNT(*) AS n_rows,
       COUNT(pl_rade) AS n_pl_rade,
       COUNT(pl_orbper) AS n_pl_orbper,
       COUNT(st_teff) AS n_st_teff,
       COUNT(st_mass) AS n_st_mass
FROM ps
WHERE default_flag = 1 AND pl_bmasse IS NOT NULL
GROUP BY pl_bmassprov
```

Observed default-subset mass-provenance groups: `Mass` 2,211 rows (1,586 also have non-null radius), `Msini` 982 (5 with radius), and `Msin(i)/sin(i)` 10 (2 with radius). Within the `Mass` group, marginal non-null counts were period 1,854, stellar temperature 1,617, and stellar mass 2,172. These feature counts are not a jointly complete row count. Exact positive-value, limit-flag, controversy, solution-type, and full-feature intersection counts remain **NOT VERIFIED**.

### Candidate comparison and recommendation

| Candidate target | Evidence | Main blocker |
| --- | --- | --- |
| `pl_rade` (Earth radii) | 27,877 non-null in all `ps` rows and 4,838 in the `default_flag=1` subset. | No approved inference decision or feature-availability contract. Radius-related inputs such as planet/star radius ratio or stellar radius may encode the target's derivation; require a domain-reviewed leakage policy. |
| `pl_bmasse` (Earth-mass scale) | 7,679 non-null overall and 3,203 in the default subset. The default subset contains 2,211 rows whose `pl_bmassprov` is `Mass`, with 1,586 also having `pl_rade`. | The unfiltered field mixes distinct mass meanings. Limit flags, uncertainty treatment, solution admissibility, and distribution/host-group coverage are not yet resolved. |
| `pl_orbper` (days) | 36,990 non-null overall and 6,096 in the default subset. | High coverage does not establish a useful prediction decision or features available before a period is measured. |

**PROPOSED candidate for team approval, not a finalized or approved task:** estimate the archive-reported true planet mass from reported planet radius for a held-out host system. This is the most interpretable candidate from the audited fields because the archive exposes an explicit provenance category for true mass and 1,586 default rows have both that mass category and radius. It is an exploratory mass–radius relation on published measurements; it must not be described as a physical simulator, a validated mass estimator for arbitrary planets, or an approved product capability.

Conditional contract if the candidate is approved:

- **Prediction unit/timing:** one planet's selected default parameter-set row; estimate its reported true mass when radius is available and mass is not, before using the mass value. NASA's `default_flag` selection must be reviewed for suitability.
- **Target:** `pl_bmasse` in Earth-mass units, restricted to `pl_bmassprov = 'Mass'`. Exclude censored/limit rows only after the exact `pl_bmasselim` semantics are verified. Retain asymmetric uncertainty and provenance fields for audit; do not turn limits into exact labels.
- **Candidate feature:** `pl_rade` in Earth-radius units only for the first comparison. Exclude mass fields, mass uncertainties/limits/provenance, density, identifiers, and radius-derivation fields such as `pl_ratror` and `st_rad` unless a domain review establishes they are appropriate and non-leaking. Verify input availability at the proposed inference time.
- **Eligibility/missingness:** complete cases for target and radius, no imputation in the first baseline; apply reviewed mass/radius limit, controversy, and solution policies. The 1,586 count is before those additional checks and is not the guaranteed final sample size.
- **Grouping/split:** keep all rows for a `hostname` in one partition and use a fixed, recorded group-split seed. Audit `pl_refname` overlap across partitions; if publication-level overlap could bias the result, define a source-aware grouping rule before evaluation. Do not use a random row split.
- **Comparison/metrics:** training-set median via `DummyRegressor` as the transparent non-ML reference; compare a simple `Ridge` regression only after the final complete-case count and feature distribution are reviewed. Use MAE in Earth masses as primary, RMSE and R² as secondary diagnostics; report counts and errors by relevant size ranges. Error costs and a minimum acceptable improvement are not specified, so no pass threshold can be set.

### Readiness and exact blockers

This evidence supports **one candidate for review**, not selection of a final task. Before dataset generation, the team must approve the decision the estimate supports, prediction timing, the target's meaning and limit/uncertainty policy, `default_flag`/solution/controversy rules, the allowed feature set, and acceptance criteria. A grouped host/reference audit and complete-case query must establish whether the candidate remains evaluable. The current `fetch_ps_dataset()` only selects from `ps`, has no row filter/pagination parameter, and caps one request at 100 rows; it cannot acquire the 1,586-row candidate subset as one call. Do not bypass that contract or alter ARC-03 here; agree on a reproducible extraction/snapshot path before acquisition.

The adapter's `Provenance.retrieved_at` is populated at the real external response read, and its metadata records the exact ADQL and response-byte SHA-256. That is appropriate for identifying an actual retrieval event. It does not retain response bytes, and the current aggregate audit did not create an ARC-03 `Dataset` or retained snapshot. A future experiment also needs a separately retained, checksummed dataset artifact/schema and experiment record for feature/target definitions, group assignments, split seed, model configuration, and results. Keep the educational evaluator's fictional score entirely separate from this NASA task.

**Decision:** baseline ML remains **NO-GO** in this phase. The mass–radius candidate should move to a task/data review first; do not generate the training snapshot or fit a model until the task, data extraction, leakage policy, and acceptance criteria are approved.

## 11. Final Go/No-Go Decision

### NO-GO

Do not train or implement a baseline ML model at this time. Continue only documentation, interface discussion, and task-independent data engineering. The proposed Mission Outcome direction does not confirm the simulator contract, score meaning, feature set, group split, or evaluation acceptance criteria. The Phase 3.1 mass–radius direction is only a candidate for review; no task or retained NASA snapshot is approved. Reopen implementation readiness after the dependencies and conditions in Section 9 and the review items in Section 10 are resolved. This decision does not reject the Exoplanet Archive as a possible future source.
