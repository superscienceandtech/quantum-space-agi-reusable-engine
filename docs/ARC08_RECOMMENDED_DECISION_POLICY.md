# ARC-08 Recommended Decision Policy for the Exploratory Baseline

**Status: Recommended internal policy — pending stakeholder/scientific sign-off.** This is not a formal scientific approval, dataset authorization, NASA statement, or performance result. It records concrete project recommendations so routine technical choices do not remain unnecessarily vague.

## 1. Executive decision summary

The proposed mass–radius regression is a coherent, narrowly scoped **exploratory baseline** if its output is described as estimating selected NASA Exoplanet Archive-reported mass values from archive-reported radius values. It is not a prediction of independent physical truth, an operational decision tool, a claim that mass is caused by radius, or evidence of general scientific validity. The educational mission evaluator and its fictional score are unrelated and excluded.

Recommend the following working contract, pending the approvals shown below:

- Candidate population: exact `default_flag = 1 AND pl_bmassprov = 'Mass'` in Planetary Systems (`ps`); the historical 2,211 matching rows are planning evidence only.
- Candidate target: `pl_bmasse`, Earth masses. Candidate sole feature: `pl_rade`, Earth radii.
- Exclude missing/malformed/non-finite target or feature from ordinary numeric regression with an auditable reason. Do not coerce or impute. Quarantine zero/negative values from the primary positive-valued analysis while preserving and reporting them; this is a proposed operational convention, not NASA's interpretation of those records.
- Preserve uncertainty, limit, controversy, solution, and identity metadata. Do not use undocumented limit values, uncertainty, IDs, density, derived values, or status fields as model features.
- Prefer host-disjoint evaluation for the proposed unseen-host question; audit exact publication-reference overlap and escalate to host-reference components only if row-level evidence and the approved scientific objective justify that stricter grouping. Never randomly split rows as fallback.
- Use median `DummyRegressor` as the required transparent reference. Ridge is optional and deferred unless a predeclared comparison question and training-only preprocessing/tuning justify it.
- Report MAE in Earth masses as primary; RMSE and R² as diagnostics, on the same untouched test groups as the baseline. Do not invent a pass threshold; pre-register one only if a stakeholder can justify it from the intended use.
- Use a versioned reproducibility manifest and retain exact source bytes internally only after storage/retention permission is established. Internal reproducibility and public redistribution are separate decisions.

**Current gate remains NO-GO for full dataset extraction, model evaluation/training, and scientific performance claims.** The exact active-`ps` limit-code meanings and data-retention/redistribution terms are not resolved by project evidence and must not be guessed.

## 2. Status vocabulary

- **technically resolved:** a deterministic engineering rule can be adopted from repository contracts or ordinary data-processing requirements without asserting scientific meaning. This does not authorize a NASA request.
- **recommended:** a project/methodological choice is recommended with rationale, but stakeholder or scientific-owner sign-off is still required before it defines a scientific cohort or evaluation.
- **externally blocked:** an authoritative external fact or permission is required and is not present. Do not substitute inference or a project-authored guess.

No item below is marked formally approved. “Technically resolved” means only that the implementation behavior is clear, not that all project approvals have been obtained.

## 3. Decision table

| Decision | Recommended policy | Evidence | Rationale | Status | Required approver, if any |
| --- | --- | --- | --- | --- | --- |
| Prediction task (A) | Supervised regression: estimate archive-reported `pl_bmasse` in Earth masses from archive-reported `pl_rade` in Earth radii. Describe agreement with selected archive values, not independent physical truth or operational prediction. | The task spec defines this candidate pair; NASA field definitions document units and that `pl_bmasse` can represent several mass meanings. `pl_bmassprov='Mass'` narrows the candidate interpretation. | It is a coherent numeric target/feature pair for a simple exploratory regression, but dataset association alone does not validate an astrophysical relation, intended use, or inference-time feature availability. | **recommended** | Scientific reviewer and project/product stakeholder for task purpose, timing, and interpretation. |
| Initial source/cohort (B) | Use `ps` with exact predicates `default_flag = 1` and `pl_bmassprov = 'Mass'`; preserve predicate and raw fields. Do not expand to other mass provenance categories or silently switch to `PSCompPars`. Treat 2,211 as a historical planning count, never final eligible size. | NASA documents `default_flag` as selected default parameter set and identifies mass-provenance categories. Its FAQ explains default selection aims at a useful parameter set, not a universal quality guarantee. Prior live query observed 2,211 matches; no retained full snapshot. | A fixed, narrow source/predicate supports reproducibility and avoids mixing documented projected-mass meanings. It remains a population choice, not a quality filter. | **recommended** | Scientific reviewer and project/product stakeholder. |
| Missing target/feature (C) | Preserve raw rows and values. Missing/absent target or feature is excluded from ordinary numeric regression input and gets a deterministic ledger reason. No target imputation and no radius imputation in this baseline. | ARC-03 JSON ingestion preserves nulls; schema validation is structural, not scientific. A regression input requires numeric X/y. NASA schema does not guarantee per-row non-nullability. | A missing value cannot be used as an ordinary numeric predictor/label without an explicit imputation model, which would change the method. Missingness can be selection-related, so report it. | **technically resolved** for mechanics; **recommended** for cohort application | Technical owner defines ledger behavior; scientific reviewer signs off on resulting complete-case population. |
| Invalid types and non-finite values (C) | Reject malformed numeric types and non-finite target/feature values from regression input, report reason, retain raw artifact. Never coerce booleans, strings, nulls, NaN/Infinity, or exponent-overflow results silently into measurements. | ARC-03 schema contract checks exact declared types; adapter rejects non-finite JSON numbers; explicit preprocessing excludes booleans and finite-checks conversions. | Prevents undefined arithmetic/metrics and concealed data corruption; a mechanical check makes no scientific threshold claim. | **technically resolved** | Technical owner for exact schema/ledger contract. |
| Zero/negative mass or radius (C) | Quarantine values `<= 0` from the primary positive-valued regression table, preserve original records and report separately. Do not rewrite them as null or silently delete them. Revisit only by documented decision. | NASA field descriptions give physical measurement units but the project evidence does not document a row-level rule for zero/negative entries, and no full row-level audit exists. | This is a conservative operational convention for a positive-valued mass/radius relationship, not a claim that NASA defines every such row as invalid. Quarantine permits audit without injecting those values into the primary point-regression dataset. | **recommended** | Scientific reviewer for use as the primary cohort rule. |
| Radius domain / physical cutoffs (C) | Do not add an upper/lower radius threshold or other physical-domain cut. Keep `pl_rade` as the only candidate feature; require missing/non-finite handling above. | No approved domain boundary or prediction scenario is in the repository. | A cutoff could alter the population and would need a task-specific rationale. Avoid invented thresholds. | **recommended** | Scientific reviewer if any future physical restriction is proposed. |
| Measurement uncertainties (D) | Preserve `pl_bmasseerr1/2` and `pl_radeerr1/2` exactly as received and report their availability. Missing uncertainty alone does not exclude a row. Do not invent, absolutize, combine, weight by, or use uncertainties as predictors. Consider a separately specified sensitivity analysis only after review. | NASA documents positive-/negative-side associations; recorded cohort aggregate values are descriptive, not universal sign or null rules. | Requiring uncertainties could select a different reporting population; asymmetric errors need a defined statistical method. | **recommended**; implementation mechanics are clear | Scientific reviewer for any filter, statistical transformation, weighting, feature use, or sensitivity analysis. |
| Limit fields (E) | Preserve `pl_bmasselim`/`pl_radelim` values and nulls as audit metadata. Do not interpret `-1`, `0`, `1`, or null; do not transfer mappings from differently named fields; do not filter by code. A final point-measurement cohort cannot be declared until active `ps` semantics are authoritatively established and reviewed. | Active NASA page associates the fields as limit columns but has no code table/null meaning; prior aggregate observations do not define meaning. Similar legacy mappings are explicitly not transferable ([limit-code review](ARC08_NASA_LIMIT_CODE_SEMANTICS.md)). | A guessed mapping can include censored observations as point measurements or exclude valid rows. | **externally blocked** | NASA authoritative documentation/clarification for semantics; then scientific reviewer for eligibility consequence. |
| Controversy and solution status (F) | Preserve `pl_controv_flag`, `soltype`, raw values and nulls; report counts. Do not automatically exclude controversial records or filter solution types. Any sensitivity cohort must be separately labeled and approved. Do not invent meanings for raw values not documented. | NASA definitions describe the controversy flag and the broad solution/disposition field; no project inclusion rule or complete row-level values are established. | Filtering changes the scientific population. Preserving facts enables review without silently equating status with data quality. | **recommended** | Scientific reviewer for filters/sensitivity analysis. |
| Identity and duplicates (G) | Preserve exact `pl_name`, `hostname`, `pl_refname`. Do not case-fold, trim, alias-merge, normalize references, or deduplicate automatically. Report missing/blank, exact repeats, variants, conflicting associations, and exact duplicate rows separately. Quarantine unresolved planet identity conflicts from the primary unit until reviewed. | NASA documents literature name/host/reference roles, not uniqueness or canonicalization. `ps` stores parameter sets; repeated planet names need not be errors. | Prevents irreversible data loss and arbitrary identity conflation. | **technically resolved** for preserving/auditing; **recommended** for quarantine disposition | Technical owner for diagnostic mechanics; scientific reviewer for final row/unit decisions. |
| Host grouping (H) | Primary proposed split: host-disjoint. It estimates performance on planets around hosts absent from fitting/model selection. Keep each exact `hostname` group wholly within one partition after identity audit. | Task and identity reviews propose held-out hosts; same-host leakage is a structural risk of row-random splitting. No full snapshot or feasibility report exists. | This directly matches the proposed generalization question and blocks same-host overlap. It does not alone prevent shared-reference or alias leakage. | **recommended** | Scientific reviewer approves the generalization claim; technical owner implements/asserts no host crossing. |
| Reference overlap and connected components (H) | Always audit `pl_refname` overlap across host partitions. Do not automatically require component grouping absent evidence. If row-level audit shows a relevant shared-reference leakage path and the approved objective requires unseen references, evaluate host-reference connected components before any fit. If grouping is infeasible, stop; no random-row or silent host-only fallback after committing to components. | No approved snapshot, reference counts, overlap, or component sizes. Existing extraction/identity designs define how to build and test the graph but do not claim feasibility. | Component grouping can reduce leakage through shared references, but can produce a giant component and too few independent partitions. Choice should match the generalization claim, not be selected by model score. | **recommended**; quantitative feasibility is **externally/data blocked** until snapshot is authorized | Scientific reviewer; technical owner for graph/partition audit. |
| Planet duplication across partitions (G/H) | Group all reviewed records for the same exact `pl_name` together in addition to host constraints; if name conflicts across hosts or is ambiguous, quarantine or merge grouping constraints only under an approved identity policy. Never deduplicate to make a split easier. | NASA does not promise uniqueness; existing identity review notes that a host-reference bipartite graph alone does not connect repeated planet names with different host/reference pairs. | Avoids the same named planet appearing on both sides while preserving rows. | **recommended** | Scientific reviewer for identity resolution; technical owner for same-partition assertion. |
| Feature allowlist / leakage (H) | Candidate model input is only `pl_rade`. Exclude `pl_bmasse`-derived fields, density, mass/radius uncertainty and limit flags, IDs/grouping keys, references, `default_flag`, `soltype`, controversy metadata, post-target fields, and other target proxies. Identifiers may be used for auditing/grouping, never as model features. | Task spec explicitly defines sole candidate feature and lists exclusions; no feature/target pipeline exists. | Minimizes direct target leakage and keeps the question interpretable; radius availability at intended inference time still needs approval. | **technically resolved** as an allowlist implementation; overall feature contract **recommended** | Technical owner; scientific reviewer confirms inference-time availability. |
| Mandatory baseline and optional Ridge (I) | Require median `DummyRegressor` fit only on training targets as reference. Compare all candidate models on identical held-out test rows/groups. Defer Ridge unless feature distribution and a predeclared scientific comparison question justify it; any scaling/alpha choice is fitted/tuned only within training/validation. | Task spec proposes median dummy; a constant target reference is transparent. One feature does not automatically justify a second model. | Prevents complex-model claims without a meaningful comparator. | **recommended** | Scientific reviewer/project stakeholder approves whether Ridge adds value; technical owner for train-only boundaries. |
| Split and preprocessing boundaries (H/I) | Make group assignments before fit. Learned preprocessing, selectors, and estimators fit on training only; validation may guide choices; final test remains untouched. Record exact assignments and all grouping keys. Never use ordinary random-row splitting as fallback. | Existing reviews identify leakage risk; no split or learned preprocessing API exists. Existing ARC-08 preprocessing is explicit deterministic scalar conversion, not learned fitting. | Prevents group leakage and train/test distribution-information leakage. | **technically resolved** as future engineering invariant; split choice/proportions **recommended** | Technical owner; scientific reviewer approves group objective and feasibility thresholds. |
| Metrics/acceptance (J) | Primary MAE in Earth masses; RMSE secondary; R² diagnostic with undefined/unstable conditions reported. Include test row count, independent group count, target distribution, exclusions, and DummyRegressor result on the exact same test partition. No numerical threshold unless justified and pre-registered before final test evaluation. | Metrics are proposed in task spec; no use-based threshold, evaluation API, or result exists. | A matched baseline is fair; R² can be undefined or unstable. A threshold selected after seeing test results would be post hoc. | **recommended**; numeric threshold **unresolved pending objective** | Scientific reviewer and product stakeholder for metric meaning/acceptable error. |
| Provenance and manifest (K) | Adopt a versioned manifest capturing endpoint, exact query/parameters, timezone-aware event times, HTTP/UWS metadata, raw response path/length/SHA-256, schema artifact, parser/validator versions, code and environment identity, policy/schema/task versions, exclusion ledger, feature/target contract, group/split assignments, seed if used, estimator/metric configuration, and output hashes. Unknown/unavailable values must be explicit; never fabricate. | Extraction and Phase 3.16 reviews propose these fields; ARC-03 provenance can record source/query/time/metadata but cannot itself retain raw bytes. No complete artifact/manifest exists. | Separates raw evidence from derived dataset and permits byte-level integrity/replay to the extent the archive state is reproducible. | **technically resolved** as manifest design; implementation and actual values **not yet present** | Technical owner; project stakeholder for artifact/retention approval. |
| Cross-query snapshot identity (K) | Do not claim transaction/snapshot consistency from separate schema/count/data queries or matching counts. Describe each response by its own query and retrieval time unless NASA provides a documented common as-of/release token and its use is verified. | Existing documents provide no transaction token or isolation evidence; archive is updated periodically according to recorded NASA FAQ. | Prevents overclaiming reproducibility. Exact retained bytes reproduce a response, not the server's underlying historical database snapshot across requests. | **externally blocked** for any common-snapshot claim | NASA authoritative documentation/authority; technical owner records evidence. |
| Retention and redistribution (L) | Seek approval to retain exact raw response internally in durable, access-controlled storage when permitted and operationally feasible. Treat public redistribution as a separate decision. Do not publish raw data or assert a license/permission from silence. | Existing project docs record NASA public-data/citation guidance but no project-specific storage, retention, redistribution authorization, or dataset-specific DOI. | Internal reproducibility access does not imply publication rights. | **externally blocked** for legal/terms permission; internal storage choice **recommended pending stakeholder sign-off** | Project stakeholder/data steward; NASA authority or applicable terms for unresolved source permissions. |
| Citation/acknowledgment (L) | Follow NASA's recorded archive acknowledgment and citation guidance if publishing results; retain exact `pl_refname` values so used literature can be acknowledged. Determine DOI only if official guidance says it applies to this artifact. | Project matrix records NASA standard acknowledgment, Christiansen et al. (2025) citation guidance, direct paper acknowledgment, and DOI guidance. No paper/result or artifact DOI exists. | Citation requirements are not the same as redistribution permission. | **technically resolved** for known citation instructions; project application **recommended**; artifact DOI applicability **externally blocked if unclear** | Documentation/release owner; NASA guidance/authority for DOI applicability. |

## 4. Explicit policy for proposed defaults A–L

### A. Prediction task

Adopt the proposed `pl_bmasse` target and sole `pl_rade` feature, with target units of Earth masses and feature units of Earth radii, as a coherent exploratory supervised regression formulation. Wording must be “estimate selected archive-reported mass values from selected archive-reported radius values.” Do not claim the target is independent ground truth, causality, operational prediction capability, or scientific validation. This is a recommended task contract pending stakeholder/scientific sign-off.

### B. Initial cohort

Retain exact `default_flag = 1 AND pl_bmassprov = 'Mass'` as the candidate cohort, with no expanded predicates. The 2,211 observation is historical planning evidence and not final count. Preserve rows outside the candidate predicate in a raw audit only if the separately approved extraction query and policy call for them; do not use the count as approval.

### C. Missing, invalid, non-finite and nonpositive values

Missing/absent target or feature is excluded from primary regression input and logged by deterministic reason. Non-finite/malformed numeric inputs are rejected from analysis input and reported. No coercion, target replacement, or radius imputation. Values `<= 0` are preserved and quarantined from the proposed positive-valued primary dataset pending scientific sign-off; report counts and values rather than calling them NASA-invalid. These are operational rules, not NASA definitions.

### D. Measurement uncertainties

Preserve all available uncertainty fields. Missing uncertainty does not alone exclude a record. Never invent uncertainty values or automatically use uncertainties as features or weights. Report field coverage and stored values. A distinct uncertainty sensitivity analysis requires an explicit statistical rationale and review.

### E. Limit fields

Preserve raw limit fields and nulls; apply no code mapping/filter. The active `ps` codes and null semantics are an external factual blocker: obtain an authoritative active-table definition before declaring point-valued target/feature eligibility. Do not transfer meanings from differently named archive fields.

### F. Controversy and solution type

Preserve `pl_controv_flag`, `soltype`, their raw values and nulls; report counts. Do not automatically exclude controversial records or filter solution types. A separate sensitivity analysis may be proposed after exact values and interpretation are verified; do not invent meanings.

### G. Identity and duplicate handling

Preserve exact names and references; do not trim, case-fold, alias-merge, normalize, or deduplicate automatically. Report missing/conflicting/repeated values. Keep same reviewed planet identity in a common partition; quarantine unresolved name/host conflicts pending identity policy.

### H. Grouping and leakage

Recommend host-disjoint split as the primary candidate because it answers “how does the baseline perform for planets around hosts not represented during fitting/model selection?” Audit exact `pl_refname` overlap and planet-name overlap. If evidence and the approved generalization target require unseen references, evaluate host-reference connected-component grouping. Quantitative feasibility is unknown until an approved row-level snapshot exists. If grouping cannot create valid partitions, stop and report; do not switch to random rows or silently weaken the chosen rule.

### I. Baseline models

Median `DummyRegressor` is mandatory and fit on training targets only. Ridge is optional, deferred unless feature distribution and a predeclared question justify it. Any scaling, feature selection, imputation added later, or Ridge hyperparameter choice must be fitted/tuned within training/validation groups only; the proposed primary workflow has no imputation.

### J. Metrics

Report MAE in Earth masses as primary, RMSE as secondary, and R² as a diagnostic with limitations and undefined cases. Report sample count, independent group count, target distribution, exclusions, and baseline comparison on the exact same held-out rows. No numerical acceptance threshold is approved. If a decision threshold is necessary, justify it from the project objective and preregister it before final test evaluation.

### K. Provenance and snapshot

Use the manifest contract in the decision table and the detailed proposal in [`ARC08_PROVENANCE_SNAPSHOT_REPRODUCIBILITY_GATE.md`](ARC08_PROVENANCE_SNAPSHOT_REPRODUCIBILITY_GATE.md). Record exact query/request, times with timezone, safe HTTP/UWS metadata, exact response bytes/length/SHA-256, schema artifact, parser/validator versions, policy/task/schema versions, feature/target definitions, exclusion ledger, group assignments, seed only if used, code/source tree and environment versions, and metrics/configuration only if evaluation is separately approved. Do not claim snapshot isolation.

### L. Retention, citation and redistribution

Recommend exact raw response retention internally only after stakeholders approve location, access, retention, and permission. Keep this separate from public redistribution, which must remain blocked until applicable terms are verified. Apply NASA's existing citation/acknowledgment instructions when publishing; direct literature references should be retained for attribution. Do not invent dataset DOI, license, retention permission, or redistribution permission.

## 5. Decisions ARC-08 can make and implement internally

These engineering defaults do not resolve scientific or legal approval:

1. Use explicit exact-value comparisons and preserve raw source fields/nulls; never silently coerce, impute, normalize, or erase records.
2. Make a row-level exclusion/pending-review ledger with stable reason codes and record both overlapping reasons and one declared primary disposition without losing detail.
3. Validate expected schema and finite numeric values mechanically; keep schema validity distinct from eligibility.
4. Enforce a feature allowlist (`pl_rade`) and prohibit identifiers/status/target-derived fields from model input.
5. Implement deterministic exact-string identity/reference diagnostics and no-crossing assertions with synthetic fixtures.
6. Keep host groups indivisible in any proposed split and implement a split feasibility report that stops on insufficient groups; no random-row fallback.
7. Fit learned preprocessing/model/selection only on training and keep test untouched; record immutable assignments and exact configurations.
8. Design manifest schema, checksums, validation, atomic writing/recovery, and offline/mock tests. Mark data not yet acquired and values unavailable; do not issue network requests in these engineering tests.
9. Keep the median dummy baseline and any optional model evaluated on identical rows and report units/counts/undefined metrics.

Actual implementation, NASA data access, and model evaluation remain outside this documentation phase and subject to the blockers below.

## 6. Genuine external blockers and required sign-off

### Requires authoritative NASA evidence

- Complete active-`ps` semantics and allowed values for `pl_bmasselim` and `pl_radelim`, including null meaning; existing limit investigation found this unresolved.
- Effective large-result/output limits, full-scale truncation signaling and any common as-of/snapshot mechanism; the recorded small TAP checks do not establish these properties.
- Applicable source terms for retaining or redistributing exact response bytes if official NASA documentation does not answer the project's use case. No permissions are inferred from public accessibility or documentation silence.

### Requires project stakeholder/scientific-owner decision

- Whether the task, prediction timing, target interpretation, default/`Mass` cohort, and `pl_rade` availability answer a useful project question.
- Whether the proposed operational quarantine of nonpositive values and complete-case target/feature rule are suitable for the intended scientific interpretation.
- How limit semantics, uncertainties, controversy, solution status, repeated/missing identities affect scientific eligibility once authoritative evidence is available.
- Whether host-disjoint generalization is the intended claim; whether reference-component grouping is needed after overlap diagnostics; minimum group/test evidence and stop conditions.
- Internal snapshot storage/access/retention plan; whether any public redistribution is intended; citation/release/DOI choices for actual outputs.
- Whether baseline metrics meet the evaluation need and any predeclared error/improvement threshold. Do not derive a threshold post hoc from test results.

No approval name/date is recorded here. The handoff identifies Yousuf as responsible for architecture/scientific review, but this document does not assert that review occurred.

## 7. Practical extraction-readiness checklist

Full candidate acquisition may be considered only after these items are evidenced:

- [ ] Written project decision on the exploratory objective, target interpretation, prediction unit/timing, exact candidate predicate, and candidate feature availability.
- [ ] Documented active-`ps` limit code/null semantics from authoritative NASA evidence; scientific decision on the effect on point-regression eligibility.
- [ ] Approved policies for missing, malformed, non-finite, zero/negative values; uncertainty metadata; controversy/solution fields; duplicate and ambiguous identity handling. Preserve quarantined rows and reasons.
- [ ] Approved exact-string identity audit and host/reference grouping objective. Split feasibility thresholds/proportions/seed determined before model scores; no random-row fallback.
- [ ] Full-scale retrieval format, async behavior, actual effective row/byte limits, overflow/truncation behavior, result expiry/recovery, and raw schema capture verified sufficiently for completeness. Small smoke checks alone do not pass this gate.
- [ ] Approved internal durable storage/retention/access and separate redistribution/terms decision; citation instructions documented for any publication.
- [ ] Versioned manifest/schema/policy contract implemented and tested offline; exact query/request and raw response bytes retained with independently verified byte length and SHA-256.
- [ ] VOTable completeness/schema checks pass, required status is unambiguous with no overflow, transfer completed, and any required count cross-check passed with its separate-query snapshot limitation disclosed.
- [ ] Per-row audit ledger accounts for every source row, overlapping exclusion reasons, pending review, and exact raw identity values; no unknown scientific decision is silently converted to eligible.
- [ ] Only after the above: report row/group counts, graph components, eligible count, and a final split feasibility assessment tied to that immutable artifact. If infeasible, stop.

Completing this checklist would authorize only a separately approved extraction attempt if project stakeholders permit it and every artifact acceptance condition passes. It would not, by itself, authorize model fitting or scientific claims.

## 8. Final recommendation

Proceed now with internally owned, offline engineering design and synthetic-fixture tooling for manifests, lossless audit ledgers, exact-identity diagnostics, group feasibility checks, and train-only boundaries. Keep the recommended task/cohort/policies clearly marked **pending stakeholder/scientific sign-off**.

Keep full NASA extraction blocked until the external active-limit semantics and acquisition-completeness/retention gates are resolved, and until the project approves the scientific task and cohort. Keep model evaluation/training and scientific-performance claims blocked until an approved retained snapshot, eligible-row policy, feasible predeclared group split, and metric protocol exist. No dataset has been generated or evaluated by this policy review.

## References

- [Exploratory task specification](ARC08_BASELINE_ML_TASK_SPEC.md)
- [Extraction design](ARC08_BASELINE_ML_EXTRACTION_DESIGN.md)
- [Policy decision matrix](ARC08_BASELINE_ML_POLICY_DECISION_MATRIX.md)
- [NASA limit-code semantics review](ARC08_NASA_LIMIT_CODE_SEMANTICS.md)
- [Scientific eligibility policy review](ARC08_SCIENTIFIC_ELIGIBILITY_POLICY_REVIEW.md)
- [Identity, grouping, leakage review](ARC08_IDENTITY_GROUPING_LEAKAGE_REVIEW.md)
- [Provenance and reproducibility gate](ARC08_PROVENANCE_SNAPSHOT_REPRODUCIBILITY_GATE.md)
- NASA [active Planetary Systems field definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html), [FAQ](https://exoplanetarchive.ipac.caltech.edu/docs/faq.html), [acknowledgment guidance](https://exoplanetarchive.ipac.caltech.edu/docs/acknowledge.html), and [DOI guidance](https://exoplanetarchive.ipac.caltech.edu/docs/doi.html), as recorded in the existing reviews. No external query was performed for this document.
