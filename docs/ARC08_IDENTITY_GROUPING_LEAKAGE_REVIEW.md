# ARC-08 Identity, Grouping, Leakage, and Split Feasibility Review

**Status: EXPLORATORY REVIEW — NO SPLIT OR SCIENTIFIC POLICY APPROVED.** This review assesses the proposed archive-reported mass-from-radius task. It does not approve the task, eligible cohort, dataset extraction, model fitting, or performance claims.

**Scope:** NASA Exoplanet Archive Planetary Systems (`ps`), candidate target `pl_bmasse`, candidate feature `pl_rade`, and provisional candidate predicate `default_flag = 1 AND pl_bmassprov = 'Mass'`. This is planning evidence only. The prior 2,211-row candidate count is not a final eligible dataset size; no approved snapshot exists for row-level identity or split analysis.

## Evidence and repository boundaries

The task and policy documents record NASA's definitions: `pl_name` is the planet name most commonly used in literature, `hostname` is the host name most commonly used in literature, and `pl_refname` is the publication reference used for the planet parameter set. These descriptions do not establish uniqueness constraints, canonical identifiers, alias resolution, or normalization rules. NASA describes `ps` as retaining parameter sets and the `default_flag` as an expedient selection toward one row per planet; this is not a database uniqueness guarantee. See the [active NASA column definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html) and [NASA FAQ](https://exoplanetarchive.ipac.caltech.edu/docs/faq.html), as already recorded in the project's [task specification](ARC08_BASELINE_ML_TASK_SPEC.md) and [policy matrix](ARC08_BASELINE_ML_POLICY_DECISION_MATRIX.md).

The extraction design requires exact-string audits of missing identities, duplicate names, conflicting host assignments, reference reuse, and connected components. It explicitly states that no row-level graph or component counts are available ([extraction design](ARC08_BASELINE_ML_EXTRACTION_DESIGN.md)). The [scientific eligibility review](ARC08_SCIENTIFIC_ELIGIBILITY_POLICY_REVIEW.md) keeps identity normalization and duplicate resolution subject to review. The [limit-code investigation](ARC08_NASA_LIMIT_CODE_SEMANTICS.md) remains unresolved; that issue may change cohort membership and therefore must be resolved before split feasibility is measured on a final cohort.

Repository inspection finds deterministic scalar preprocessing, but no ARC-08 feature/target preparation, grouping/splitting, fitted preprocessing, or ML evaluation API. Existing preprocessing converts explicitly configured scalar fields; it does not define split boundaries or a scientific dataset contract ([`preprocessing.py`](../src/quantum_space_agi/ml/preprocessing.py), [`test_preprocessing.py`](../tests/ml/test_preprocessing.py)). No relevant NASA identity/split tests or approved snapshot are present.

## Identity-field review

| Field | Documented meaning | What is not guaranteed | Audit treatment proposed for review |
| --- | --- | --- | --- |
| `pl_name` | Planet name most commonly used in the literature. | Unique row key, stable identifier over time, alias policy, or exact spelling/case/whitespace normalization. Multiple `ps` parameter-set records are possible; the default flag is not a uniqueness constraint. | Preserve original text. Count absent, null, blank, exact duplicates, and multiplicity. For each repeated name, compare host, reference, target, and feature values. Do not deduplicate or select a solution automatically. Quarantine unresolved duplicate/ambiguous planet identities from an evaluation unit until reviewed. |
| `hostname` | Host name most commonly used in the literature. | Globally unique canonical host key, alias reconciliation, case-folding/whitespace rules, or guaranteed consistency across all planet records. | Preserve original text. Report missing/blank hosts, exact values, byte-for-byte variants, records/planets per host, and conflicting host assignments for repeated `pl_name`. Do not merge aliases or normalize automatically. Missing/ambiguous host identity prevents reliable host-disjoint assignment and must remain quarantined/unresolved. |
| `pl_refname` | Publication reference used for a given planet parameter set. | Globally unique publication identifier, canonical citation formatting, or equivalence rules for alternate citations to the same work. | Preserve original text. Report missing/blank values, exact reference reuse across hosts, multiple references per name, and reference string variants. Do not normalize references or treat repeated strings as proof of identical measurement provenance without review. |

Exact repeated host values can include multiple planets in one system; that is a grouping relationship, not evidence of duplicate rows. Exact repeated `pl_name` can reflect multiple parameter records or identity ambiguity; it must be audited rather than silently deduplicated. Case or whitespace differences may be aliases or distinct representations; no project-approved normalization exists. The presence of multiple references per planet is consistent with the documented parameter-set structure and cannot be resolved by arbitrarily choosing one.

## Leakage threat matrix

| Threat | Status from current evidence | Leakage mechanism / possible impact | Proposed control and evidence required |
| --- | --- | --- | --- |
| Same host in training and test | **Confirmed structural risk if rows are randomly split; frequency unknown.** NASA identity fields provide a host label, but no approved snapshot has been audited. | Planets around one host can share stellar measurements, system properties, observing methods, or publication context. Test rows may therefore not represent unseen hosts. | Keep all exact-host records in one partition for a host-generalization question; audit aliases/conflicting host assignments before assignment. Confirm by automated no-host-crossing assertion. |
| Same reference in training and test | **Plausible risk; overlap unknown.** NASA documents `pl_refname` as the publication reference for a parameter set. | A shared paper may contribute related parameter estimates or methodology across hosts. The magnitude and relation to target/feature values are unknown. | Audit exact reference overlap across proposed host partitions. Decide whether reference-disjoint or host-reference-component grouping is necessary; do not silently normalize references. |
| Multiple records for one planet | **Possible by table design; candidate-cohort prevalence unknown.** `ps` contains parameter sets; uniqueness of `pl_name` is not guaranteed by the documentation. | Alternate solutions for the same planet can appear on both sides, directly or indirectly duplicating the target/feature pair. | Count exact `pl_name` multiplicity and compare values/references/hosts. Keep rows in the same group or quarantine until a reviewed row-selection policy exists. No order-dependent deduplication. |
| Duplicate or closely related measurements | **Unverified at row level.** No full snapshot or duplicate audit exists. | Exact duplicates or variants can allow near-identical observations/labels across train and test, inflating apparent generalization. | Report exact row duplicates and duplicate candidate keys separately; compare source references and values. Do not infer that every duplicate is erroneous or remove it silently. |
| Host/reference name aliases or formatting variants | **Plausible, not quantified.** NASA defines names descriptively, not as canonical normalized IDs. | The same entity may be split across string variants, allowing entity leakage despite exact-string grouping. Aggressive normalization can also merge distinct identities incorrectly. | Preserve raw strings; report case/space variants for review. Resolve only via an approved, source-supported mapping; prove grouping coverage after resolution. |
| Feature/target leakage | **Design risk; no task pipeline exists.** Candidate feature is only `pl_rade`, target is `pl_bmasse`. Related or derived columns are available in `ps`. | Mass-derived quantities (e.g. density), target uncertainties/provenance/limits, identifiers, or post-target fields can directly encode target or selection. Radius-derived quantities may duplicate/restate the feature. | Enforce a reviewed feature allowlist containing only `pl_rade`; exclude mass/radius uncertainty and limit fields, density, identifiers/group keys, references, status/selection flags, and target-derived values unless the approved task later revises the contract. |
| Preprocessing fit on held-out data | **Not currently present; future implementation risk.** Existing scalar conversion is explicit and deterministic but no learned transformer or split API exists. | Estimating imputation/scaling/feature-selection parameters using validation or test data leaks distribution information. | Split groups first. Fit every learned preprocessing step, feature selector, or estimator on training only; apply frozen parameters to validation/test. Keep explicit non-learned scalar conversions identical and documented across partitions. |
| Hyperparameter or model selection on test | **Not currently present; future implementation risk.** No model/evaluation API exists and ML readiness is NO-GO. | Repeatedly inspecting test MAE/RMSE/R² and selecting a model or policy makes the final test estimate optimistic. | Use validation or grouped CV within training groups for choices. Freeze protocol before opening the final test result; evaluate the chosen baseline once under the approved protocol. |

“Leakage risk” here identifies a plausible failure mode, not proof that a particular overlap exists or that the model would achieve inflated performance. Those claims require row-level evidence from a retained snapshot.

## Grouping alternatives

None of these alternatives is scientifically approved. They answer different generalization questions and must not be treated as interchangeable.

| Alternative | Generalization question | Leakage it prevents | Leakage that may remain | Sample-efficiency trade-off | Evidence needed before choice |
| --- | --- | --- | --- | --- | --- |
| **A. Planet-level random row split** | Performance on randomly held-out rows drawn from the same row-generating mixture. | Only prevents the exact same row from appearing in two partitions, assuming duplicates have already been detected. | Same host, same planet under alternate records, shared references, aliases, related measurements, and any unrecognized duplicates can cross partitions. | Usually retains the most nominal rows in each partition, but effective independent sample size may be much smaller. | Duplicate/identity audit, but even with it this does not test the proposed held-out-host objective. Not recommended for that objective. |
| **B. Host-disjoint split** | Transfer to hosts absent from training/model selection. | Prevents exact `hostname` groups from crossing partitions, once identity resolution is adequate. | Shared references across hosts, planet-name conflicts/aliases, alternate citations, and other related measurement pathways may remain. | Can retain useful counts if enough hosts and reasonable group-size balance exist; actual feasibility unknown. | Approved snapshot, identity consistency and alias review, host count/size distribution, cross-partition reference audit, and approved test-group criteria. |
| **C. Reference-disjoint split** | Transfer to records associated with publication references absent from training. | Prevents exact `pl_refname` strings from crossing partitions. | Same host or same planet across different references, citation variants, and host aliases may cross. Exact reference text may not be canonical. | Publications may span many planets or hosts; grouping can reduce effective sample count and imbalance partitions. Unknown until audit. | Reference normalization policy, multiplicity distribution, host/planet overlap audit, group counts/sizes, and a scientific reason to generalize to unseen references. |
| **D. Host-reference connected components** | Transfer to groups of hosts and references connected through shared host/reference relationships; a stricter joint holdout. | Prevents exact host or reference nodes connected in the graph from crossing partitions. Planet identity constraints must also be enforced. | Alias/normalization errors, related measurements not represented by the exact reference field, or publication links hidden by alternate strings may remain. | Potentially the lowest effective sample count. A high-degree reference can connect many hosts into one giant component, leaving too few independent components for train/validation/test. | Approved snapshot; exact-string identity audit; component count/size distribution; giant-component diagnostics; preapproved minimum independent group counts and partition feasibility criteria. |

Host-only is the current task specification’s provisional direction, not an approved choice. A reference-disjoint policy is not automatically safer if it leaves the same host/planet across partitions. Connected components are stricter for exact observed host/reference strings, but may make evaluation infeasible. No split ratios, seed, minimum groups, or performance thresholds are established by the available evidence.

## Connected-component construction and feasibility

The extraction design proposes a bipartite graph with two disjoint node namespaces:

- `host:<exact-hostname>` nodes;
- `ref:<exact-pl_refname>` nodes.

For every source row retained for grouping, add an edge between its host node and reference node. Store a stable source-row identifier/ordinal and the raw `pl_name` as edge-associated record attributes. Keep parallel edges or an equivalent list of edge-associated row IDs; do not deduplicate source rows to build the graph. Compute connected components deterministically from sorted exact node and edge representations. Assign each complete component to one partition and assert that neither exact host nor exact reference appears in more than one partition.

This graph alone does not connect two edges that share a `pl_name` if the rows have different host/reference pairs. Therefore, after duplicate/name audit, all edges/records with the same reviewed planet identity must receive an additional same-partition constraint: either quarantine unresolved repeated-name cases or merge their associated components for partition assignment. Do not normalize names to make that link without an approved mapping. If identity is missing or ambiguous, do not invent a graph node; mark the row unresolved and stop or quarantine it under an approved policy.

Quantitative feasibility is **UNKNOWN**. There is no approved, complete, retained snapshot and no host/reference/planet component report. Do not invent component counts, sizes, giant-component prevalence, or achievable split proportions. A future feasibility report must include row, distinct planet/host/reference counts; missing and ambiguous identity counts; duplicate-name and cross-host counts; reference overlap; component count and size distribution; largest-component share; and simulated assignments under only preapproved partition criteria. Stop if the selected grouping cannot provide the required independent partitions. Never break a component or silently fall back to a random-row or weaker grouping strategy.

## Proposed evaluation protocol — pending approval

1. Approve the task, target/feature contract, cohort rules, identity disposition, grouping objective, and snapshot before any model evaluation. Preserve exact source rows and an exclusion/pending-review ledger.
2. Audit exact identities and resolve or quarantine missing, duplicate, conflicting, and ambiguous cases according to an approved policy. Do not normalize aliases or deduplicate by query order.
3. Compare host-only, reference-only, and host-reference component feasibility using identity/group summaries, without using model scores to choose grouping. Record the scientific generalization question that motivates the selected scheme.
4. Define train, validation, and final test group assignments, proportions, minimum group/sample criteria, and a deterministic seed before fitting. No arbitrary ratios or seed are approved here. Assert the selected group keys/components are disjoint across partitions.
5. Fit a proposed median `DummyRegressor` using training targets only. If any learned preprocessing, feature selection, or model tuning is later approved, fit/tune only within training data (using grouped validation/CV where needed). Do not inspect the final test partition for choices.
6. Keep the final test set untouched until task, eligibility, split, and analysis protocol are frozen. Report MAE in Earth masses as proposed primary metric, RMSE and R² as secondary diagnostics only if the scientific owner approves the metrics and test-set adequacy. Always report test rows and independent group counts; report undefined/unstable metrics without forcing values.
7. Store exact split assignments, group IDs as audit metadata (not features), seed, query/snapshot checksum, schema and policy version, code/dependency versions, preprocessing configuration, baseline configuration, exclusions, and metric definitions/results.

Before reporting any MAE, RMSE, or R² as evaluation evidence, minimum prerequisites are: an approved task and target interpretation; an approved, retained, reproducible snapshot and cohort policy; row-level identity/duplicate/exclusion audit; a predeclared group strategy and feasible disjoint assignments; verified no-crossing assertions for required identities; no learned preprocessing or model selection fitted on held-out data; a frozen baseline/metric protocol; an untouched test partition with adequate independent group counts approved in advance; and exact reproducibility artifacts. A metric computed without these is descriptive only and must not be presented as generalization performance.

## Unresolved decisions and approval questions

1. Is the desired claim prediction for a new host, a new publication, or some other population? This determines which split design is relevant.
2. Does exact `hostname` represent the host grouping unit adequately after aliases, multiple-star systems, and conflicting planet-to-host associations are audited?
3. How are exact repeated `pl_name` rows resolved, and which ambiguous/missing identities must be quarantined?
4. Is exact `pl_refname` suitable for source-overlap auditing; should reference overlap define groups or remain an audit warning?
5. Do observed connected components leave enough independent groups for train/validation/test? This cannot be answered before an approved retained dataset exists.
6. What partition proportions, minimum independent group/test counts, seed, and stop thresholds are justified? None are approved or measurable from the current repository.
7. What is the approved eligible cohort, given the unresolved limit-code, zero/negative-value, uncertainty, controversy, solution-status, and missingness policies documented in the linked reviews?
8. Which person/team owns the scientific approval of the generalization claim and evaluation protocol? The handoff assigns Yousuf architecture/scientific review responsibility; no approval is implied by this document.

## Safe implementation boundary

**May be implemented independently, using synthetic fixtures only:** exact-string identity diagnostics; missing/blank/case/whitespace variant reports; duplicate and conflicting-identity reports; deterministic bipartite component construction; component-size summaries; partition validator assertions; leakage checks; and train-only preprocessing-boundary tests. These tools must preserve source rows, expose unresolved cases, and avoid claiming scientific eligibility.

**Must remain blocked:** full NASA extraction; row-level eligibility decisions; alias normalization or deduplication; choosing host/reference/component split policy or numerical split thresholds; assigning actual NASA rows to partitions; fitting/evaluating a model; and scientific or performance claims. No random-row split or silent fallback is allowed.

## References

Repository evidence and design:

- [`ARC08_BASELINE_ML_TASK_SPEC.md`](ARC08_BASELINE_ML_TASK_SPEC.md)
- [`ARC08_BASELINE_ML_EXTRACTION_DESIGN.md`](ARC08_BASELINE_ML_EXTRACTION_DESIGN.md)
- [`ARC08_BASELINE_ML_POLICY_DECISION_MATRIX.md`](ARC08_BASELINE_ML_POLICY_DECISION_MATRIX.md)
- [`ARC08_NASA_LIMIT_CODE_SEMANTICS.md`](ARC08_NASA_LIMIT_CODE_SEMANTICS.md)
- [`ARC08_SCIENTIFIC_ELIGIBILITY_POLICY_REVIEW.md`](ARC08_SCIENTIFIC_ELIGIBILITY_POLICY_REVIEW.md)
- [`src/quantum_space_agi/ml/preprocessing.py`](../src/quantum_space_agi/ml/preprocessing.py) and [`tests/ml/test_preprocessing.py`](../tests/ml/test_preprocessing.py)

Official NASA sources already recorded in the project documents:

- [Planetary Systems and Planetary Systems Composite Parameters column definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html)
- [NASA Exoplanet Archive FAQ](https://exoplanetarchive.ipac.caltech.edu/docs/faq.html)

No new NASA query or dataset inspection was performed for this review.
