# ARC-08 ML Readiness Decision

**Decision date:** 2026-11-08
**Branch reviewed:** `arc/08-ai-ml` at `1d438dc`
**Decision:** **NO-GO — baseline ML remains blocked.**
**Scope:** Requirements decision and conditional future implementation specification. No model or ML API is implemented or approved here.

## 1. Executive Decision

**NO-GO.** Do not implement or train a baseline ML model yet. The repository has reusable data ingestion, structural validation, quality analysis, deterministic scalar preprocessing, and a bounded NASA Exoplanet Archive TAP adapter. It does not have an approved product/scientific prediction question, prediction unit and timing, target, available-at-inference feature set, or task-specific baseline and evaluation criteria.

The primary dataset evidence is [`ARC08_EXOPLANET_DATASET_EVALUATION_REPORT.md`](ARC08_EXOPLANET_DATASET_EVALUATION_REPORT.md). It records a successful 30-row, 13-field retrieval, JSON type/null preservation, and zero exact duplicate rows in that sample. The result was not persisted; the ordered alphabetic sample does not establish archive coverage or representativeness, and its archive release is unknown. This is structural exploration, not evidence that the archive is scientifically suitable for a task.

`docs/ML_REQUIREMENTS.md` explicitly says no prediction task or training dataset is approved and prohibits starting training until the use case, suitable data, target, baseline, leakage-safe evaluation design, metrics, and acceptable errors are agreed (especially “Current readiness,” “Candidate task definition,” and “Readiness gate”). That is sufficient evidence to block implementation of task-specific baseline behavior.

## 2. Existing Evidence

### Repository and project

- **VERIFIED:** The initial repository inspection was on branch `arc/08-ai-ml`, HEAD `1d438dc` (`feat(arc-08): add NASA Exoplanet Archive data adapter`). The existing dataset evaluation report was already untracked when this decision document was started; it is preserved.
- **VERIFIED:** `docs/ML_REQUIREMENTS.md` describes an educational mission-design game but states that no measurable prediction target, task, or training dataset is defined. It says deterministic computation, simulation, or optimization may be preferable where appropriate.
- **VERIFIED:** `docs/ARC08_EXOPLANET_DATASET_EVALUATION_REPORT.md` is the primary evidence for the NASA sample. It reports the exact query, retrieval time, response checksum, observed types/nulls, sample quality, unknown release, and the fact that the rows/response bytes were not saved.
- **VERIFIED:** Repository fixture data under `data/samples/` is synthetic/example data. The repository contains no approved real ML dataset snapshot.

### Existing APIs

- **VERIFIED:** `Dataset`, `Provenance`, `DataSource`, and `DataFormat` are defined in `src/quantum_space_agi/data/models.py`, `provenance.py`, and `sources.py`. The structured JSON/CSV entry points are in `src/quantum_space_agi/data/ingestion.py`; legacy `load_dataset()` in `src/quantum_space_agi/data/loader.py` returns `DatasetLoadResult`, not `Dataset`.
- **VERIFIED:** `validate_dataset(dataset, schema)` in `src/quantum_space_agi/data/schemas.py` checks declared structure and types. `analyze_quality(dataset)` in `src/quantum_space_agi/data/quality.py` reports missing values, exact duplicate groups, and numeric summaries. These APIs do not establish scientific validity or ML readiness.
- **VERIFIED:** `preprocess_dataset(dataset, *, conversions)` in `src/quantum_space_agi/ml/preprocessing.py` performs explicit, deterministic scalar conversions and records a transformation description in provenance. It does not impute, scale, encode, select features, split data, or train models.
- **VERIFIED:** `fetch_ps_dataset(...)` in `src/quantum_space_agi/data/adapters/exoplanet_archive.py` performs bounded JSON retrieval from the fixed `ps` table and records query and response provenance. It does not retain source response bytes, select a scientifically approved subset, or establish training suitability.
- **VERIFIED:** `pyproject.toml` declares no runtime dependencies. It has optional test and quality tool groups. No ML library is currently a required dependency.
- **VERIFIED:** No feature/target extraction API, split API, predictor, task-specific metric, evaluation result, or reproducibility artifact API exists under `src/quantum_space_agi/ml/`.

## 3. ML Readiness Gate Assessment

All gates below are applicable to supervised baseline evaluation unless the team approves a different task type. **No gate is marked PASS based on inference.**

| Gate | Status | Available evidence | Missing evidence / required decision |
| --- | --- | --- | --- |
| Approved scientific/product use case | **BLOCKED** | Mission-design game is described in project documentation; `docs/ML_REQUIREMENTS.md` says no measurable ML use case is specified. | Team must define the user/system decision and explain why prediction adds value. |
| Prediction unit and inference timing | **BLOCKED** | The `ps` sample contains planet/reference solution rows; related rows and multiple solutions are possible. | Approve whether predictions concern a planet, system, solution, candidate, mission state, or other unit, and what information exists at prediction time. |
| Feature definitions | **BLOCKED** | The sample includes documented fields such as `pl_orbper`, `pl_rade`, `default_flag`, and `soltype`; see the dataset report and adapter. | Choose features only after the task is defined; document units, derivation, source, availability time, and exclusions. |
| Target/label and scientific meaning | **BLOCKED** | No target or label-generation method is approved in `docs/ML_REQUIREMENTS.md`. | Approve the output, label source/method, scientific interpretation, and (if relevant) horizon. |
| Real dataset, source terms, coverage, provenance, version | **BLOCKED** | One real archive response was fetched in memory; adapter records query/time/checksum. Dataset report says it was not persisted, is alphabetically bounded, and has unknown release/version. NASA documentation provides a table DOI, not an immutable query snapshot identifier. | Select an appropriate dataset and extraction process; review terms, coverage, bias, schema, retention, and exact snapshot/artifact reproducibility. |
| Appropriate non-ML baseline | **BLOCKED** | Requirements require a simple baseline. No task exists to define a meaningful rule/calculation. | Domain and product owners must define the simplest task-relevant non-ML method and minimum useful improvement. |
| Leakage-safe train/validation/test strategy | **BLOCKED** | Requirements warn about temporal/entity/source leakage. `ps` can contain related planet/system/reference rows. | Approve split unit and strategy based on inference scenario and dataset dependencies; keep final test use controlled. |
| Task-appropriate metrics | **BLOCKED** | Requirements list possible metric families only as examples and say metrics must match task/error costs. | Select metric definitions and aggregation after task type, target, imbalance, and usage are known. |
| Error costs and acceptance thresholds | **BLOCKED** | No error costs or minimum improvement are specified. | Decide false-positive/false-negative or regression-error consequences, acceptable ranges, and human review expectations. |
| Reproducibility requirements | **BLOCKED** | Requirements call for recording dataset identity/checksum, schema/preprocessing versions, code/dependency versions, seeds, split assignments, model parameters, and results. Adapter stores checksum but not returned bytes; archive release is unknown. | Approve artifact retention and the full experiment record required for repeatable results. |

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

1. There is no product/scientific decision that a prediction would support.
2. The prediction unit and inference time are undefined, so it is not possible to know which fields would truly be available at prediction time.
3. There is no approved target, trustworthy label-generation process, or target meaning.
4. The acquired archive sample was a small alphabetically ordered slice, was not saved, and has no archive release/version identifier. It cannot support coverage or representativeness claims.
5. `ps` may include multiple solutions, candidates, and related system records. Row-level random splitting could leak information across the same planet, host system, publication, or time period.
6. Missing measurements, uncertainty conventions, limit flags, and candidate/default selection require task-specific scientific decisions. They must not be silently coerced or imputed.
7. Without a task, neither a useful non-ML baseline nor appropriate metrics, error costs, or acceptance thresholds can be defined.
8. `docs/ML_REQUIREMENTS.md` explicitly requires these decisions before training. A numeric table alone does not justify supervised learning.

## 6. Future Baseline Implementation Specification

This section is a conditional design outline only. It is not API approval and no component below is implemented. Add only the parts needed for the eventual approved task; do not start with a generic model framework.

### Component plan

| Component | Purpose and proposed contract | Existing dependency / location | Acceptance tests after approval |
| --- | --- | --- | --- |
| Task and feature/target specification | Describe a single approved objective, prediction unit/time, ordered feature names, target name/meaning/type/units, label provenance, and fields unavailable at inference. Proposed module: `src/quantum_space_agi/ml/task.py`; input: immutable task specification + `Dataset`; output: task-bound rows with explicit feature/target separation, or structured validation errors. | Reuse `data.models.Dataset`, `data.schemas.validate_dataset`, and source/provenance metadata. Keep dependency one-way: `ml → data`. | Reject unknown/missing fields and incompatible types; preserve source records; prove target and excluded fields cannot enter feature matrix; test null and unit metadata requirements; retain source identity/provenance. |
| Dataset readiness and schema checks | Validate against an explicit task schema, then summarize quality; do not add an `is_ml_ready` boolean. Input: `Dataset` + approved `DataSchema`; output: existing `SchemaValidationReport` and `DataQualityReport`, plus only task-specific decisions if truly required. | Reuse `validate_dataset()` and `analyze_quality()` in `src/quantum_space_agi/data/`; do not duplicate generic checks in ML. | Known schema errors reported; missingness and exact duplicates surfaced; no mutation; scientific constraints remain explicit and separately reviewed. |
| Leakage-aware split | Assign examples according to approved prediction unit and inference scenario. Proposed module: `src/quantum_space_agi/ml/splitting.py`; input: task-prepared rows + approved split specification/group/time keys; output: immutable train/validation/test partitions plus assignments and split metadata. | Uses task specification and `Dataset`; no data-layer dependency on ML. Do not choose random/group/time split before task and data relationships are known. | Deterministic assignment for fixed seed where randomness is approved; no group overlap when grouping is required; temporal cutoff is respected when appropriate; no records dropped silently; final test partition is not used for fitting/tuning. |
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

## 7. Required ARC-08 Contributions from Amran

**No immediate implementation contribution is required from Amran** to record this NO-GO decision. No adapter or preprocessing change is necessary.

After a use case is proposed, Amran's relevant ARC-08 work is a focused review of the task contract and scientific/data assumptions: prediction unit/time, target/label meaning, admissible `ps` solutions, units/uncertainties/missingness, group/time leakage constraints, baseline appropriateness, and acceptable errors. Which specific review is needed depends on the approved task. Do not assign Amran ARC-04 or ARC-05 ownership under this decision.

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

## 10. Final Go/No-Go Decision

### NO-GO

Do not train or implement a baseline ML model at this time. Continue only task-independent data engineering and requirements work that does not presume a target, feature set, split, metric, or model. Reopen the decision after the conditions in Section 9 are met and reviewed. This decision does not reject the Exoplanet Archive as a possible future source; it says the present evidence is insufficient to approve it for any specific ML task.
