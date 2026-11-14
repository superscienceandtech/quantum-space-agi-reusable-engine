# ARC-08 Exploratory Baseline ML Task Specification

**Status: EXPLORATORY INTERNAL BASELINE PROPOSAL — NOT SCIENTIFICALLY OR TEAM APPROVED.** This document records a candidate for review. It does not approve a scientific result, operational prediction capability, dataset generation, model evaluation, or training. Do not use it to claim that a mass–radius relationship has been validated.

This proposal is limited to NASA Exoplanet Archive Planetary Systems (`ps`) records. The deterministic educational mission evaluator and its fictional score are unrelated and are not an ML target.

## 1. Candidate task

**Proposed objective:** Estimate the archive-reported planet mass in Earth masses from the archive-reported planet radius in Earth radii, for records whose mass provenance is reported as `Mass`. Evaluate only on host systems excluded from fitting and model selection. The interpretation is agreement with selected archive-reported values under a declared extraction policy; it is not prediction of independent physical truth or an observing decision.

| Contract item | Provisional proposal | Status |
| --- | --- | --- |
| Unit | One selected default parameter-set row for one planet, subject to identity and duplicate audits. | Proposed; selection and uniqueness need review on a retained snapshot. |
| Target | `pl_bmasse` (Earth masses), filtered to exact `pl_bmassprov = 'Mass'`. | Candidate; target meaning and scientific question require approval. |
| Feature | `pl_rade` (Earth radii), sole initial feature. | Candidate; availability at the hypothetical inference time requires approval. |
| Baseline | Median `sklearn.dummy.DummyRegressor`, fitted on training targets only. | Proposed reference; scikit-learn is not a runtime dependency. |
| Optional comparison | One-feature Ridge only if a reviewer finds a meaningful reason to compare it. | Not required; avoid complexity without a stated analysis purpose. |
| Primary metric | Test-set MAE in Earth masses. | Proposed; no acceptable threshold is defined. |
| Secondary diagnostics | RMSE in Earth masses and R², reporting undefined or unstable R² rather than forcing a value. | Proposed; interpretation and minimum test-group size require review. |

## 2. Repository and prior-audit evidence

**VERIFIED in repository:** `fetch_ps_dataset()` in [`exoplanet_archive.py`](../src/quantum_space_agi/data/adapters/exoplanet_archive.py) requests JSON from the fixed `ps` table. `limit` is a caller argument but is constrained to 1–100 by `MAX_ROWS`; the query uses `SELECT TOP`. There is no filter or pagination/offset parameter. It records exact ADQL, actual retrieval time, and SHA-256 of response bytes, then parses the response through `load_json()`. The original response bytes are not retained. Adapter-produced table/column descriptions, units, and archive types are `None`; the adapter does not fetch TAP schema metadata.

**VERIFIED in repository:** ARC-03 defines `Dataset`, `Provenance`, `DataSchema`, `validate_dataset()`, and `analyze_quality()` in `src/quantum_space_agi/data/`. Dataset records preserve JSON values and nulls. `DataSchema` checks declared field presence, nullability, and exact Python types; it does not enforce numeric ranges, NASA flag vocabularies, units, or scientific eligibility. `analyze_quality()` reports structural/missingness and basic numeric summaries, not scientific validity.

**PRIOR AUDIT EVIDENCE, not a current extraction:** the Phase 3.1 audit recorded 40,387 `ps` rows, 6,464 rows with `default_flag = 1`, 2,211 of those with the observed mass-provenance string `Mass`, and 1,586 of that subset with non-null `pl_rade`. These counts predate the proposed finite/positive, limit, uncertainty, controversy, duplicate, and grouping policies. The bounded 30-row response was alphabetically ordered and not persisted. No eligible candidate dataset or current row-level audit is available here.

### Field-semantics audit

The primary source is NASA's [Planetary Systems and Planetary Systems Composite Parameters column definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html). NASA's [FAQ](https://exoplanetarchive.ipac.caltech.edu/docs/faq.html) provides additional context on default parameter sets and `soltype`. “Meaning documented” below means the field description is available from those sources; it does not validate a particular row or its scientific quality.

| Field | Documented meaning / unit / categories | Type and nullability | Audit status |
| --- | --- | --- | --- |
| `pl_bmasse` | Best available mass estimate; may represent Mass, M*sin(i)/sin(i), or M*sin(i); Earth masses. | Live `ps` TAP schema: `double`, unit `Mearth`; no nullability attribute. | Meaning/unit verified; actual per-row semantics require `pl_bmassprov` and source review. |
| `pl_bmassprov` | Provenance category for the best mass; NASA documents options `Mass`, `M*sin(i)/sin(i)`, `M*sini`. | Live `ps` TAP schema: `char`, arraysize/size 200; no nullability attribute. Prior aggregate audit observed alternate spellings that must not be normalized implicitly. | Categories documented; exact extraction values need snapshot verification. |
| `pl_bmasseerr1` | Positive-side uncertainty column for `pl_bmasse`, in the mass parameter's Earth-mass scale. | Live schema: `double`, unit `Mearth`; NASA labels positive (+). Candidate-cohort aggregate: 2,041 positive, 170 null, none zero/negative. No nullability attribute or universal stored-sign rule. | Side association/unit verified; cohort sign counts are descriptive only; do not use as a filter/feature. |
| `pl_bmasseerr2` | Negative-side uncertainty column for `pl_bmasse`, in the mass parameter's Earth-mass scale. | Live schema: `double`, unit `Mearth`; NASA labels negative (-). Candidate-cohort aggregate: 2,041 negative, 170 null, none zero/positive. No nullability attribute or universal stored-sign rule. | Side association/unit verified; do not generalize cohort counts or treat as a mass value. |
| `pl_bmasselim` | Limit flag associated with `pl_bmasse`. | Live `ps` TAP schema: `int`; candidate-cohort values `-1`, `0`, `1`. No nullability attribute or active-table code mapping. | Field role documented; exact current table code meanings unresolved. |
| `pl_rade` | Planet radius, Earth radii. | Live `ps` TAP schema: `double`, unit `Rearth`; no nullability attribute. | Meaning/unit verified; radius must be audited from the retained snapshot. |
| `pl_radeerr1` | Positive-side uncertainty column for `pl_rade`, in the radius parameter's Earth-radius scale. | Live schema: `double`, unit `Rearth`; NASA labels positive (+). Candidate-cohort aggregate: 1,569 positive, 642 null, none zero/negative. No nullability attribute or universal stored-sign rule. | Side association/unit verified; cohort sign counts are descriptive only; do not use as a filter/feature. |
| `pl_radeerr2` | Negative-side uncertainty column for `pl_rade`, in the radius parameter's Earth-radius scale. | Live schema: `double`, unit `Rearth`; NASA labels negative (-). Candidate-cohort aggregate: 1,567 negative, 642 null, 2 zero, none positive. No nullability attribute or universal stored-sign rule. | Side association/unit verified; do not generalize cohort counts or treat as a radius value. |
| `pl_radelim` | Limit flag associated with radius. | Live `ps` TAP schema: `int`; candidate-cohort values `-1`, `0`, null. No nullability attribute or active-table code mapping. | Field role documented; exact current table code meanings unresolved. |
| `default_flag` | Whether this parameter set is selected as default; NASA documents `1=yes`, `0=no`. | Live `ps` TAP schema: `int`; no nullability attribute. | Meaning and stated values verified; default is a selection aid, not a quality guarantee. |
| `pl_name` | Planet name most commonly used in literature. | Live `ps` TAP schema: `char`, size 30; no nullability attribute. | Meaning documented; uniqueness and normalization are not guaranteed. |
| `hostname` | Stellar/host name most commonly used in literature. | Live `ps` TAP schema: `char`, size 28; no nullability attribute. | Meaning documented; grouping key suitability must be audited on the snapshot. |
| `pl_refname` | Publication reference used for the given planet parameter set. | Live `ps` TAP schema: `char`, size 200; no nullability attribute. | Meaning documented; reference identity/normalization and overlap need snapshot audit. |
| `soltype` | Disposition/source class for the parameter set. NASA FAQ names “Published Confirmed,” “Kepler Project Candidate,” and “TESS Project Candidate.” | Type/nullability and exact raw strings/case not specified by the column definitions. Prior sample observed strings. | Broad categories documented; exact values and inclusion policy unresolved. |
| `pl_controv_flag` | Whether confirmation status has been questioned in published literature; NASA documents `1=yes`, `0=no`. | Live `ps` TAP schema: `int`; no nullability attribute. | Meaning and stated values verified; null policy and row-level interpretation require review. |

NASA's column-definition page does not provide active `ps` storage types; the live TAP schema query documented in Section 9 supplies types for the requested fields. Neither the page nor `TAP_SCHEMA.columns` supplies per-column nullability. The prior 30-row observations are sample evidence only. Do not infer a missingness policy or exact flag mapping from that sample or from code mappings for other/retired table columns.

## 3. Provisional eligibility and feature policies

The following are **technical recommendations for review**, not approved scientific inclusion rules. Preserve raw source values, flags, and excluded-row reasons in the retained audit artifact.

| Area | Provisional working recommendation | Evidence / rationale | Approval still required |
| --- | --- | --- | --- |
| Parameter-set selection | Use `ps`; provisionally filter `default_flag = 1`. Treat this as an archive selection, not a scientific quality ranking. | NASA says `ps` contains parameter sets; its FAQ says default is a convenient one-row-per-planet filter and may not be the most precise value. `PSCompPars` is more filled-in but can combine values and is not necessarily self-consistent. | Confirm that the default-set question is appropriate; verify uniqueness in the retained snapshot. |
| Target provenance | Require exact documented/observed `pl_bmassprov = 'Mass'`; do not mix projected-mass categories. Preserve the original string. | `pl_bmasse` can denote different mass meanings, and NASA identifies provenance as the discriminator. Historical aggregate strings and spelling discrepancy need row-level review. | Confirm `Mass` is the intended label and resolve exact category spellings/case before extraction. |
| Missing/non-numeric/non-finite | Candidate eligibility requires present non-null finite numeric target and feature; no coercion or imputation. Preserve and count missing/invalid rows. | ARC-03 JSON ingestion preserves types/nulls; its structural schema does not establish scientific validity. | Approve wire-type policy after checking current schema and full response. |
| Zero/negative values | Quarantine and count them; do not silently include or exclude until their archive meaning is reviewed. If scientific review confirms ordinary positive measurements are required, exclude them by explicit rule. | Aggregate audit did not inspect value distributions. Negative values could be data issues or field conventions; no row evidence is available. | Domain reviewer must decide treatment and document exclusions. |
| Target/radius limits | Retain `pl_bmasselim` and `pl_radelim`; do not assume any code values. For ordinary point regression, exclude limit/censored records only after the `ps` mapping is verified; until then generation is blocked. | NASA documents the limit fields but current `ps` code mappings are not verified in sources inspected. | Verify mappings from authoritative `ps` documentation/schema and retained values; approve point-regression eligibility. |
| Uncertainty | Retain both asymmetric uncertainty fields for audit; do not use them as predictors, take absolute values, combine them, or silently weight observations. Missing uncertainties should be reported. Do not require complete uncertainty fields until selection effects are reviewed. | Error roles and units are documented; coverage and conventions are not established by the sample. Requiring reported uncertainties may select a different cohort. | Decide complete-uncertainty cohort vs broader cohort; review their interpretation and whether uncertainty-aware analysis is needed. |
| Solution/controversy | Preserve `soltype` and `pl_controv_flag`. Do not silently interpret null as confirmed/non-controversial. A conservative exclusion of candidate or questioned records is a proposal only. | NASA describes broad solution categories and binary controversy meanings, but exact raw categories, table coverage, and their relevance to this task are unresolved. | Verify exact values and decide allowed categories/missing-flag handling. |
| Features | Use only `pl_rade`. Exclude target/mass fields, uncertainty and limit fields, density, identity/group fields, `default_flag`, `soltype`, controversy metadata, and radius-derivation proxies such as `pl_ratror` and `st_rad`. | A single predeclared feature limits leakage opportunities. Proxy/derived-variable dependencies require domain scrutiny. | Confirm radius availability at intended inference time and approve feature exclusions. |
| Planet/identity audit | Compare exact returned identity strings and report duplicate `pl_name`, missing identity, and conflicting host/reference associations. Keep every raw row; do not deduplicate or automatically exclude duplicates. Missing identities prevent the corresponding identity/group operation until resolved. | NASA describes literature names and parameter references; `ps` has one row per planet per reference, so names are not a documented unique key. Repository models impose no NASA identity contract. | Review how repeated names map to the proposed prediction unit and approve any normalization or grouping policy. |

Do not treat any row labeled `Mass` as automatically eligible: target value, target provenance, target limit semantics, radius value/limit semantics, solution status, controversy handling, identity, and grouping all remain subject to review. The 1,586 historical non-null intersection is not a final eligible count.

## 4. Leakage and split proposal

**Primary group proposal:** assign all eligible planets with the same `hostname` to one partition. `pl_name` identifies the planet for duplicate auditing and traceability, not as a feature. Audit `pl_name` uniqueness and `hostname` assignment consistency before splitting.

**Reference-overlap proposal:** audit `pl_refname` across host groups. A host-only split does not prevent the same reference/publication from appearing on both sides. If reference overlap is material, form a bipartite host–reference graph and assign each connected component wholly to one partition. This is technically implementable once a retained, eligible row set exists; current repository evidence has no row-level graph, host count, reference count, or component distribution.

Connected components can create a giant component or leave too few independent components for three partitions. Before fitting, stop and report the task as blocked if components make train/validation/test partitions infeasible, severely imbalanced, or too small for a meaningful held-out test. Do not split a component or fall back to random row splitting to force a result. Group-count and minimum-size criteria must be agreed before evaluation; do not invent thresholds after seeing scores.

**Split proposal:** use deterministic group assignment to train, validation, and test only after eligible snapshot and grouping are approved. A fixed seed such as `20261109` can make an implementation reproducible, but this project-authored example seed and partition proportions require review and must be recorded with exact assignments. Keep test groups untouched until selection and analysis choices are fixed. A seed cannot remedy an invalid grouping design.

## 5. Baseline, metrics, and reproducibility proposal

- Fit a median `DummyRegressor` on training targets only; compare any optional model on exactly the same held-out records. This is a transparent reference for regression, not a scientific benchmark.
- Consider Ridge only if a reviewer identifies a useful question that the median baseline cannot answer. With one feature, it is a simple linear comparison, but no improvement claim or dependency addition is justified yet.
- Report test MAE (Earth masses) as primary; RMSE (Earth masses) and R² as secondary diagnostics. State row and group counts, exact target/feature contract, exclusions, target and feature ranges, missingness, grouping, split seed/assignments, and metric definitions. Report R² as undefined where its test-set conditions make it undefined. No acceptable error or minimum useful improvement is specified; a domain/scientific reviewer and product owner must set a threshold before examining the final test score.

Before any future extraction/evaluation, retain:

- Archive identity, TAP endpoint, table, exact ADQL, requested format, retrieval timestamp, archive citation guidance, and response SHA-256.
- Exact raw response bytes or a durable serialized snapshot plus checksum and retention location. A checksum alone cannot reconstruct a response.
- Schema and filtering-policy versions; raw target/feature, uncertainty, limit, solution, controversy and identity fields; per-rule exclusion counts; selected row identities.
- Code revision and runtime/dependency versions; feature/target definitions; group construction and overlap audit; split seed and exact assignments; estimator configuration; metric definitions and results.

The current adapter can record query, retrieval timestamp, and response checksum, but not raw bytes or an archive release/version. It permits at most 100 rows per call, has no pagination/filter parameter, and fixes the table to `ps`. Therefore it cannot obtain the historical 1,586 preliminary candidate intersection in one request. No larger extraction should be attempted until a bounded reproducible acquisition/retention method is approved; do not bypass the adapter limit or change ARC-03 in this specification.

## 6. Remaining blockers and approval gate

Dataset generation and ML remain **NO-GO** pending all of the following:

1. Review and approve the scientific question, intended decision, prediction unit, and timing; establish whether archive radius is available then and whether this comparison is meaningful.
2. Verify active `ps` types/nullability, raw `pl_bmassprov` values, target/radius limit code semantics, exact `soltype` values, and uncertainty conventions from authoritative schema/documentation and a retained extraction.
3. Approve missingness, zero/negative, limit/censoring, uncertainty, solution/controversy, default-row, and duplicate-resolution rules.
4. Obtain and retain an approved snapshot; define its schema, checksum, citation/terms, filtering-policy version, and reproducible acquisition beyond the adapter's 100-row cap.
5. Audit host, planet, and reference overlap and component sizes. Approve whether host grouping alone is enough or connected components are required; establish in advance what constitutes feasible partitions.
6. Approve deterministic partition proportions/seed, baseline comparison, metric reporting, and an acceptable-error/minimum-improvement threshold before final test evaluation.

Yousuf's architecture/scientific review remains required before this proposal is treated as approved. No new NASA TAP request, dataset generation, model fitting, or evaluation is authorized by this document.

## 7. Scientific limitations and prohibited claims

The archive contains published parameter sets with heterogeneous sources, methods, uncertainty, censoring, and possible dependence by planet, host, and reference. A default-selected, filtered subset would not be a representative sample of all planets. Host/reference-held-out metrics would describe agreement with archive-reported values under the retained snapshot and policies only.

Do not claim independent physical-truth prediction, generalization to all planets, scientific validation, operational usefulness, full-archive coverage, population representativeness, or NASA endorsement. This is an exploratory internal baseline proposal, not an approved scientific task. The educational evaluator is not involved.

## 8. Final Eligibility Policy — Pre-Extraction Review

**Status: review proposal; dataset extraction remains blocked.** This section makes the proposed row-screening sequence explicit without treating unresolved scientific choices as approved rules. The task remains exploratory and is not a scientifically approved use of the archive.

### Candidate population

The verified aggregate query in the Phase 3.8 observation recorded in [`ARC08_BASELINE_ML_EXTRACTION_DESIGN.md`](ARC08_BASELINE_ML_EXTRACTION_DESIGN.md) returned **2,211 rows** for the exact predicate `default_flag = 1 AND pl_bmassprov = 'Mass'`. The uncertainty aggregate in Section 9 independently returned the same candidate-row count on 2026-11-09. The earlier asynchronous VOTable result contained one integer count row with `QUERY_STATUS=OK` and no overflow. These are counts observed at their respective query times, not a retained row snapshot, final eligible count, or guarantee about a later extraction. They do not include an explicit `pl_bmasse IS NOT NULL` clause, so do not describe them as counts of non-null target values.

### Decision classifications

| Decision | Classification | Provisional handling before approval |
| --- | --- | --- |
| Candidate predicate `default_flag = 1` and exact `pl_bmassprov = 'Mass'` | **VERIFIED / mechanically enforceable** as exact field comparisons; **PROVISIONAL** as the scientific cohort definition | Preserve raw fields; select by exact values only. Do not normalize category spelling or infer target meaning for other values. Scientific suitability of default rows and the `Mass` cohort still needs approval. |
| Target `pl_bmasse` present, non-null, and finite numeric | **VERIFIED / mechanically enforceable** once the retained response schema and wire types are checked | Report absent, null, invalid type, and non-finite separately; reject booleans and do not coerce. A missing/invalid target cannot enter a numeric point-regression input. |
| Target `pl_bmasse > 0` | **PROVISIONAL** | Compute and report the predicate, but quarantine zero/negative values as pending review; do not silently exclude them until a scientific reviewer approves the positive-target rule. No additional mass threshold or filter is proposed. |
| Feature `pl_rade` present, non-null, and finite numeric | **VERIFIED / mechanically enforceable** once response schema and wire types are checked | Report missing/null/type/non-finite separately. The baseline does not impute radius; a row without usable radius cannot be a complete-case model input. Whether complete-case selection is scientifically acceptable needs approval. |
| Feature `pl_rade > 0` | **PROVISIONAL** | Compute and report the predicate; quarantine zero/negative radius values pending explicit approval. Do not silently remove them or add a radius range threshold. |
| `pl_bmasseerr1`, `pl_bmasseerr2`, `pl_radeerr1`, `pl_radeerr2` | NASA side labels and current candidate-cohort aggregate signs are **VERIFIED**; general nullability, row-level meaning, and scientific treatment remain **UNRESOLVED**; proposed use is **PROVISIONAL** | Retain the exact raw values for audit only. Do not use as eligibility filters, predictors, weights, absolute values, or combined uncertainty. Missing uncertainty alone does not exclude a row under this provisional policy. Scientific approval is required for this non-filtering treatment. |
| `pl_bmasselim`, `pl_radelim` | **UNRESOLVED / blocking** for point-label eligibility | Preserve raw codes. Do not map, filter, or treat a value/null as a detection without verified active-`ps` semantics. Until the policy for limit/censored measurements is approved, no final point-regression eligible cohort can be declared. |
| `pl_controv_flag`, `soltype` | `pl_controv_flag` meaning/codes (int; 1=yes, 0=no) are **VERIFIED**; nullability and task-specific admissibility remain **UNRESOLVED**. `soltype` values/nullability and task-specific admissibility remain **UNRESOLVED**; non-filtering is **PROVISIONAL** | Preserve exact raw values. Apply no confirmation, controversy, or solution-status filter and infer no meaning from null. A reviewer must approve whether this non-filtering policy is scientifically suitable before defining the final cohort. |
| Duplicate and missing planet/host/reference identity | Detection is **VERIFIED / mechanically enforceable** on raw values; consequences for the task unit/grouping are **PROVISIONAL or UNRESOLVED** | Preserve rows and report exact-string duplicate and missing/blank identity findings. Do not deduplicate or automatically exclude; an identity-dependent operation remains pending if it cannot assign the row. No NASA-backed normalization rule is available. See below. |
| Grouping and leakage protection | **UNRESOLVED / blocking** for evaluation readiness | Audit exact host/reference relationships and components. Host-only versus host-reference components, identity sufficiency, and component-size stop thresholds require approval. Never fall back to random row splitting. |
| Initial feature contract | `pl_rade` alone is the **PROVISIONAL** candidate | Do not add features unless separately approved. This is not an approved feature-availability contract. |

“Mechanically enforceable” means a deterministic check can be applied to retained source values; it does not mean the check is a scientifically approved inclusion rule. ARC-03 `DataSchema` can validate declared field presence, nullability, and exact Python types. `analyze_quality()` can report missing values, exact duplicate records, and finite numeric summaries. Neither enforces measurement validity, positive-value policy, flag semantics, duplicate resolution, or scientific eligibility.

### Duplicate and identity handling

- Compare `pl_name` values exactly as returned. Missing key, JSON null, empty string, and whitespace-only string are distinct ledger conditions; do not trim or case-fold them into a normalized identity.
- Count exact-name groups among rows passing the candidate predicate. If an exact `pl_name` occurs more than once, record the group as `duplicate_pl_name_exact_audit`; do not drop rows, quarantine them automatically, or choose first/last by query ordering. A repeated name with different host or reference values is additionally marked `identity_pl_name_host_conflict` or `identity_pl_name_multiple_references` as applicable. NASA documents `ps` as one row per planet per reference, so repeated names are an audit finding, not an automatic error or equivalence claim.
- A missing, null, empty, or whitespace-only `pl_name` receives the corresponding `identity_pl_name_*` audit reason. It cannot serve as a planet identifier until resolved; retain the source row and mark its task-unit status pending review rather than automatically removing it from the raw data.
- Preserve `hostname` and `pl_refname` exactly. Multiple planets with the same exact hostname form a candidate host group only under the proposed exact-string grouping rule; this is not a NASA canonical-identity guarantee. A missing/blank hostname receives an `identity_hostname_*` audit reason and cannot be assigned in that exact-key host grouping without resolution.
- A missing/blank `pl_refname` receives an `identity_pl_refname_*` audit reason and cannot participate in the proposed host-reference overlap graph. Do not treat missing references as one shared reference node. Reference spelling variants remain distinct for the audit unless an approved, documented normalization rule is later adopted.
- The provisional source-aware audit uses exact-string bipartite nodes `host:<hostname>` and `ref:<pl_refname>` and connects them for each otherwise eligible row. Rows with unresolved identity cannot enter the graph. Whether connected components, rather than host groups alone, govern the final split remains **UNRESOLVED**. Giant-component limits, minimum component counts, and partition proportions are not specified; stop if a leakage-safe split cannot be made under thresholds approved before evaluation.

### Leakage exclusions

The sole candidate predictor is `pl_rade`. The baseline must not use `pl_bmasse` or any mass-derived field, `pl_bmasseerr1`/`pl_bmasseerr2`, density, radius uncertainty or limit fields, radius-derived fields such as `pl_ratror` or `st_rad`, identifiers (`pl_name`, `hostname`, `pl_refname`), reference or solution metadata, `default_flag`, `pl_controv_flag`, post-target fields, or any other feature that can encode or depend on the target. Grouping identifiers may be used to assign partitions, never as model inputs. This candidate feature set still requires approval for availability at the intended prediction time.

### Ordered eligibility ledger and deterministic reason taxonomy

For a future approved raw snapshot, retain every source row and emit a ledger entry for every row. Run checks in this exact order. Keep all applicable reason codes in stage order; within each stage use the field order shown below. If an exclusive primary disposition is needed, use the first failing stage as its primary reason, without discarding later diagnostic reasons.

1. **Candidate row:** verify exact `default_flag = 1` and `pl_bmassprov = 'Mass'`. Reasons: `candidate_default_flag_not_one`, `target_provenance_mismatch`, `candidate_flag_missing`, `candidate_flag_null`, `candidate_flag_invalid_type`, `target_provenance_missing`, `target_provenance_null`, `target_provenance_invalid_type`. Such rows are outside the 2,211-row predicate population but remain in the raw extraction ledger if the approved extraction includes them.
2. **Target validity:** check `pl_bmasse` key presence, nullness, exact numeric type (integer or float, excluding booleans), and finiteness, in that order. Reasons: `target_absent`, `target_null`, `target_invalid_type`, `target_non_finite`. Record `target_non_positive_pending_review` for values `<= 0`; this is unresolved and is not a final exclusion until approved.
3. **Feature validity:** check `pl_rade` key presence, nullness, exact numeric type (integer or float, excluding booleans), and finiteness, in that order. Reasons: `feature_radius_absent`, `feature_radius_null`, `feature_radius_invalid_type`, `feature_radius_non_finite`. Do not impute. Record `feature_radius_non_positive_pending_review` for values `<= 0`; do not make it a final exclusion until approved.
4. **Duplicate/identity audit:** exact taxonomy codes are `identity_pl_name_absent`, `identity_pl_name_null`, `identity_pl_name_blank`, `duplicate_pl_name_exact_audit`, `identity_pl_name_host_conflict`, `identity_pl_name_multiple_references`, `identity_hostname_absent`, `identity_hostname_null`, `identity_hostname_blank`, `identity_pl_refname_absent`, `identity_pl_refname_null`, and `identity_pl_refname_blank`. Emit only applicable codes; the `absent`, `null`, and `blank` conditions are distinct. These are audit markers, not automatic exclusion reasons; retain all source rows. Missing identity prevents only the operation requiring that identity until reviewed.
5. **Unresolved scientific fields:** emit `eligibility_unresolved_mass_limit_semantics` and `eligibility_unresolved_radius_limit_semantics` until limit decisions are approved. Emit `eligibility_unresolved_uncertainty_policy`, `eligibility_unresolved_solution_policy`, and `eligibility_unresolved_controversy_policy` as row/global pending-review markers while these policies remain undecided. Retain original field values; do not turn these markers into invented flag meanings or filters.
6. **Grouping eligibility:** emit `grouping_hostname_missing_or_ambiguous`, `grouping_reference_missing_or_ambiguous`, `grouping_duplicate_planet_unresolved`, or `grouping_split_infeasible` as applicable. Missing or ambiguous identities prevent group assignment; unresolved duplicate names and an infeasible component split block the proposed evaluation. Do not random-split affected rows.
7. **Final disposition:** set `eligible` only if the row passes every approved mechanical and scientific criterion and can be assigned under the approved leakage-safe grouping policy. While any scientific-policy decision above remains unresolved, disposition is `pending_review`, not `eligible`. Use `excluded` only for an approved deterministic exclusion, retaining every reason code.

### Extraction blockers

The 2,211 count does not resolve or approve eligibility. **Do not generate the dataset yet.** Dataset extraction remains blocked until the scientific reviewer/team approves the intended archive-reported target interpretation and default-row selection; the active-`ps` limit/censoring rules; the provisional non-filtering treatment of uncertainties, controversy, and solution status (or a replacement policy); the positive-value and missing-radius complete-case policies; how repeated planet names affect the prediction unit without silent deduplication; identity sufficiency and host/reference grouping; and the final schema, snapshot retention, citation/terms, and extraction policy version. The approved extraction/completeness requirements in [`ARC08_BASELINE_ML_EXTRACTION_DESIGN.md`](ARC08_BASELINE_ML_EXTRACTION_DESIGN.md) must also be satisfied. No group counts, eligible count, or training readiness are implied by the aggregate count.

## 9. Mechanically Verifiable NASA Field Semantics Review

**Scope:** This review uses NASA's current [Planetary Systems and Planetary Systems Composite Parameters column definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html), live official TAP `TAP_SCHEMA.columns` results for table `ps`, aggregate-only queries, and repository implementation. The live schema supplies active storage types and descriptive metadata, but exposes no column-nullability attribute. NASA's definitions identify uncertainty sides and associated limit-column names; the active `ps` definitions do not explain the limit-code values. No row-level data were exported or persisted.

| Field | Verified meaning | Evidence | Eligibility consequence |
| --- | --- | --- | --- |
| `pl_bmasse` | Best available planet mass-like estimate, in Earth masses; depending on availability it may represent `Mass`, `M*sin(i)/sin(i)`, or `M*sin(i)`. | NASA column definitions describe the meaning/unit and associate `pl_bmassprov`; live `ps` TAP schema reports `double` and unit `Mearth`. No nullability attribute is exposed. | **VERIFIED:** exact numeric/type and finite checks are mechanically appropriate before arithmetic; finite is a computational validity check, not a NASA scientific quality rule. **PROVISIONAL:** values `<= 0` can be flagged mechanically, but NASA documentation does not establish their invalidity, so do not exclude without approval. Restricting to `Mass` remains a proposed scientific cohort choice. |
| `pl_rade` | Planet radius expressed in Earth radii; NASA describes it as the center-to-surface length. | NASA column definitions give meaning/unit and associate `pl_radeerr1`, `pl_radeerr2`, and `pl_radelim`; live `ps` TAP schema reports `double` and unit `Rearth`. No nullability attribute is exposed. | **VERIFIED:** require a usable finite numeric value for numeric feature processing; do not impute. **PROVISIONAL:** flag `<= 0` mechanically, but NASA documentation does not specify a valid range or authorize excluding such rows. Complete-case selection needs scientific review. |
| `pl_bmassprov` | Provenance category for the best mass; documented options are `Mass`, `M*sin(i)/sin(i)`, and `M*sini`. | NASA column definitions and live `ps` TAP schema (`char`, arraysize/size 200); no nullability attribute is exposed. | Exact string comparison is mechanically enforceable. Using exact `Mass` to define the target cohort is still **PROVISIONAL** and must not normalize spelling or imply approval. |
| `pl_bmasselim` | The column definitions identify this as the limit column associated with `pl_bmasse`. | NASA column definitions and live `ps` TAP schema (`int`). The active-table page gives no code meanings; candidate-cohort aggregates observed `-1`, `0`, and `1` but do not assign meanings. | **UNRESOLVED / blocking:** preserve raw value; do not map, filter, or infer point-measurement status. No values from retired or unrelated tables are imported. |
| `pl_radelim` | The column definitions identify this as the limit column associated with `pl_rade`. | NASA column definitions and live `ps` TAP schema (`int`). The active-table page gives no code meanings; candidate-cohort aggregates observed `-1`, `0`, and null but do not assign meanings. | **UNRESOLVED / blocking:** preserve raw value; do not map, filter, or infer point-measurement status. |
| `pl_bmasseerr1` | Positive-side uncertainty column associated with `pl_bmasse`, in its Earth-mass scale. | NASA labels the uncertainty side `(positive +)`; live `ps` TAP schema reports `double`, unit `Mearth`. Candidate-cohort aggregate: 2,041 positive, 170 null, zero zero/negative. No nullability attribute or universal stored-sign rule is exposed. | **VERIFIED:** side association and active storage type/unit. **PROVISIONAL:** retain raw for audit; no filtering, weighting, transformation, or feature use. |
| `pl_bmasseerr2` | Negative-side uncertainty column associated with `pl_bmasse`, in its Earth-mass scale. | NASA labels the uncertainty side `(negative -)`; live `ps` TAP schema reports `double`, unit `Mearth`. Candidate-cohort aggregate: 2,041 negative, 170 null, zero positive/zero. No nullability attribute or universal stored-sign rule is exposed. | **VERIFIED:** side association and active storage type/unit. **PROVISIONAL:** retain raw for audit; do not generalize the cohort sign count or use as a filter, weight, or feature. |
| `pl_radeerr1` | Positive-side uncertainty column associated with `pl_rade`, in its Earth-radius scale. | NASA labels the uncertainty side `(positive +)`; live `ps` TAP schema reports `double`, unit `Rearth`. Candidate-cohort aggregate: 1,569 positive, 642 null, zero zero/negative. No nullability attribute or universal stored-sign rule is exposed. | **VERIFIED:** side association and active storage type/unit. **PROVISIONAL:** retain raw for audit; no filtering, weighting, transformation, or feature use. |
| `pl_radeerr2` | Negative-side uncertainty column associated with `pl_rade`, in its Earth-radius scale. | NASA labels the uncertainty side `(negative -)`; live `ps` TAP schema reports `double`, unit `Rearth`. Candidate-cohort aggregate: 1,567 negative, 642 null, two zero, zero positive. No nullability attribute or universal stored-sign rule is exposed. | **VERIFIED:** side association and active storage type/unit. **PROVISIONAL:** retain raw for audit; do not generalize the cohort sign count or use as a filter, weight, or feature. |
| `pl_name` | Planet name most commonly used in literature. | NASA column definitions state that `ps` has one row per planet per reference; live schema reports `char` (size 30). No nullability attribute or canonical-name/uniqueness guarantee is exposed. | **VERIFIED:** exact duplicate-name detection is mechanically possible. Keep it as an audit marker; do not deduplicate or exclude automatically. Missing/ambiguous names remain available in the raw ledger and require review for the proposed planet-level unit. |
| `hostname` | Stellar/host name most commonly used in literature. | NASA column definitions; live schema reports `char` (size 28). No nullability, uniqueness, canonical spelling, alias-resolution, or normalization guarantee is exposed. | Preserve raw; exact-string host grouping is a **PROVISIONAL** implementation rule, not a NASA-guaranteed identity mapping. Missing/ambiguous values prevent that grouping until reviewed; do not silently discard source rows. |
| `pl_refname` | Publication reference used for a given planet parameter set. | NASA column definitions; live schema reports `char` (size 200). No nullability, canonical normalization, or uniqueness guarantee is exposed. | Preserve raw; exact-value overlap counting is mechanically possible, but using it to connect split groups is **PROVISIONAL**. Missing/ambiguous values leave reference leakage unresolved; do not invent a shared missing-reference node. |

### Live NASA TAP schema and aggregate verification (2026-11-09)

**Endpoint:** `https://exoplanetarchive.ipac.caltech.edu/TAP/sync` (official NASA Exoplanet Archive TAP endpoint used by the repository adapter). All successful requests used `REQUEST=doQuery`, `LANG=ADQL`, `FORMAT=votable`. The VOTable responses had HTTP 200, `Content-Type: application/xml`, and an initial `QUERY_STATUS=OK`. Timestamps below are the response `Date` header in UTC; Cloudflare request IDs are included as request provenance. Response bodies were inspected but not retained or independently checksummed.

NASA's [TAP guide](https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html) describes using `TAP_SCHEMA` for table/column metadata. The live `TAP_SCHEMA.columns` self-description exposed these metadata attributes: `table_name`, `column_index`, `column_name`, `datatype`, `arraysize`, `xtype`, `size`, `description`, `utype`, `unit`, `ucd`, `indexed`, `principal`, `std`, and `format`. It exposes no `nullable` attribute. Blank metadata cells below mean the response supplied an empty/null value; they do not establish SQL nullability.

| Field | datatype | arraysize | size | format | Description and unit returned |
| --- | --- | --- | ---: | --- | --- |
| `default_flag` | `int` | — | — | `13d` | Default Parameter Set |
| `hostname` | `char` | `28` | 28 | `28s` | Host Name |
| `pl_bmasse` | `double` | — | — | `14.8f` | Planet Mass or Mass*sin(i) [Earth Mass]; `Mearth` |
| `pl_bmasseerr1` | `double` | — | — | `14.8f` | Planet Mass or Mass*sin(i) [Earth Mass] Upper Unc.; `Mearth` |
| `pl_bmasseerr2` | `double` | — | — | `14.8f` | Planet Mass or Mass*sin(i) [Earth Mass] Lower Unc.; `Mearth` |
| `pl_bmasselim` | `int` | — | — | `13d` | Planet Mass or Mass*sin(i) [Earth Mass] Limit Flag |
| `pl_bmassprov` | `char` | `200` | 200 | `200s` | Planet Mass or Mass*sin(i) Provenance |
| `pl_controv_flag` | `int` | — | — | `16d` | Controversial Flag |
| `pl_name` | `char` | `30` | 30 | `30s` | Planet Name |
| `pl_rade` | `double` | — | — | `14.8f` | Planet Radius [Earth Radius]; `Rearth` |
| `pl_radeerr1` | `double` | — | — | `14.8f` | Planet Radius Upper Unc. [Earth Radius]; `Rearth` |
| `pl_radeerr2` | `double` | — | — | `14.8f` | Planet Radius Lower Unc. [Earth Radius]; `Rearth` |
| `pl_radelim` | `int` | — | — | `11d` | Planet Radius Limit Flag |
| `pl_refname` | `char` | `200` | 200 | `200s` | Planetary Parameter Reference |

For all 14 fields, `xtype`, `utype`, and `ucd` were empty; `unit` was populated only for the six mass/radius value and uncertainty fields shown above. Every field returned `indexed=0`, `principal=1`, and `std=0`. Empty numeric `arraysize`/`size` values are metadata absence, not evidence about null values in `ps`. The live schema therefore resolves the active TAP storage-type blocker: mass/radius and uncertainty columns are `double`; limit flags and the two integer flags are `int`; identifiers/provenance/reference columns are `char`. It does not resolve nullability for all fields.

#### Exact live queries and response provenance

The first successful schema inventory query was:

```sql
SELECT column_name, datatype FROM TAP_SCHEMA.columns WHERE table_name = 'ps'
```

Observed `2026-11-09T05:57:39Z`, HTTP 200, VOTable `QUERY_STATUS=OK`, Cloudflare request ID `a57a94c16a07fc55-DAC`. It returned active column names and types; the response was too broad for inclusion here, so the narrowly projected query below was used for the field table.

```sql
SELECT column_name, datatype, arraysize, description FROM TAP_SCHEMA.columns WHERE table_name = 'TAP_SCHEMA.columns'
```

Observed `2026-11-09T05:58:20Z`, HTTP 200, VOTable `QUERY_STATUS=OK`, Cloudflare request ID `a57a95c169a436c6-DAC`. This self-description query established the metadata attributes listed above and confirmed that no nullability attribute is exposed.

```sql
SELECT column_name, datatype, arraysize, xtype, "size", description, utype, unit, ucd, indexed, principal, std, format FROM TAP_SCHEMA.columns WHERE table_name = 'ps' AND column_name IN ('pl_bmasse','pl_bmassprov','pl_bmasselim','pl_bmasseerr1','pl_bmasseerr2','pl_rade','pl_radelim','pl_radeerr1','pl_radeerr2','pl_name','hostname','pl_refname','default_flag','pl_controv_flag') ORDER BY column_name
```

Observed `2026-11-09T05:58:36Z`, HTTP 200, VOTable `QUERY_STATUS=OK`, Cloudflare request ID `a57a96253e1e9ec8-DAC`. This is the source for the 14-field table above.

The paired limit-code distribution query was:

```sql
SELECT pl_bmasselim, pl_radelim, COUNT(*) AS row_count FROM ps WHERE default_flag = 1 AND pl_bmassprov = 'Mass' GROUP BY pl_bmasselim, pl_radelim ORDER BY pl_bmasselim, pl_radelim
```

Observed from `2026-11-09T05:59:15Z` to `2026-11-09T05:59:16Z`, HTTP 200, VOTable `QUERY_STATUS=OK`, Cloudflare request ID `a57a971dd832a488-DAC`. It returned seven code-pair groups, totaling 2,211 rows:

| `pl_bmasselim` | `pl_radelim` | Rows |
| ---: | ---: | ---: |
| -1 | -1 | 2 |
| -1 | null | 9 |
| 0 | -1 | 3 |
| 0 | 0 | 1,437 |
| 0 | null | 608 |
| 1 | 0 | 144 |
| 1 | null | 8 |

These are observed integer/null values only. NASA's active `ps` column definition calls each field a “Limit Flag” but does not define what `-1`, `0`, or `1` mean. An official NASA [combined-table page](https://exoplanetarchive.ipac.caltech.edu/docs/API_combined_table_columns.html) describes differently named fields (`pl_masslim` and `pl_radlim`); its mapping is not applied to the active `ps` fields without an authoritative active-table mapping. Keep both fields out of eligibility rules until their meanings are confirmed.

The uncertainty aggregate query was:

```sql
SELECT COUNT(*) AS candidate_rows, SUM(CASE WHEN pl_bmasseerr1 IS NULL THEN 1 ELSE 0 END) AS mass_err1_null, SUM(CASE WHEN pl_bmasseerr1 > 0 THEN 1 ELSE 0 END) AS mass_err1_pos, SUM(CASE WHEN pl_bmasseerr1 = 0 THEN 1 ELSE 0 END) AS mass_err1_zero, SUM(CASE WHEN pl_bmasseerr1 < 0 THEN 1 ELSE 0 END) AS mass_err1_neg, SUM(CASE WHEN pl_bmasseerr2 IS NULL THEN 1 ELSE 0 END) AS mass_err2_null, SUM(CASE WHEN pl_bmasseerr2 > 0 THEN 1 ELSE 0 END) AS mass_err2_pos, SUM(CASE WHEN pl_bmasseerr2 = 0 THEN 1 ELSE 0 END) AS mass_err2_zero, SUM(CASE WHEN pl_bmasseerr2 < 0 THEN 1 ELSE 0 END) AS mass_err2_neg, SUM(CASE WHEN pl_radeerr1 IS NULL THEN 1 ELSE 0 END) AS radius_err1_null, SUM(CASE WHEN pl_radeerr1 > 0 THEN 1 ELSE 0 END) AS radius_err1_pos, SUM(CASE WHEN pl_radeerr1 = 0 THEN 1 ELSE 0 END) AS radius_err1_zero, SUM(CASE WHEN pl_radeerr1 < 0 THEN 1 ELSE 0 END) AS radius_err1_neg, SUM(CASE WHEN pl_radeerr2 IS NULL THEN 1 ELSE 0 END) AS radius_err2_null, SUM(CASE WHEN pl_radeerr2 > 0 THEN 1 ELSE 0 END) AS radius_err2_pos, SUM(CASE WHEN pl_radeerr2 = 0 THEN 1 ELSE 0 END) AS radius_err2_zero, SUM(CASE WHEN pl_radeerr2 < 0 THEN 1 ELSE 0 END) AS radius_err2_neg FROM ps WHERE default_flag = 1 AND pl_bmassprov = 'Mass'
```

Observed from `2026-11-09T05:59:49Z` to `2026-11-09T05:59:51Z`, HTTP 200, VOTable `QUERY_STATUS=OK`, Cloudflare request ID `a57a97f31a5c9cba-DAC`. Counts in this exact 2,211-row cohort were:

| Field | SQL NULL | Positive | Zero | Negative |
| --- | ---: | ---: | ---: | ---: |
| `pl_bmasseerr1` | 170 | 2,041 | 0 | 0 |
| `pl_bmasseerr2` | 170 | 0 | 0 | 2,041 |
| `pl_radeerr1` | 642 | 1,569 | 0 | 0 |
| `pl_radeerr2` | 642 | 0 | 2 | 1,567 |

The result agrees with NASA's documented upper/positive (`err1`) and lower/negative (`err2`) side labels for this cohort, but does not establish universal sign conventions, uncertainty validity, or missingness behavior outside this predicate. These current aggregate counts are descriptive only and are not eligibility rules.

Two earlier schema-query attempts returned HTTP 400 and were not used for conclusions. The attempt at `2026-11-09T05:56:03Z` used `SELECT column_name,datatype,arraysize,size,principal,std FROM TAP_SCHEMA.columns WHERE table_name='ps' AND column_name IN ('pl_bmasse','pl_bmassprov','pl_bmasselim','pl_bmasseerr1','pl_bmasseerr2','pl_rade','pl_radelim','pl_radeerr1','pl_radeerr2','pl_name','hostname','pl_refname','default_flag','pl_controv_flag')`; the error body was not captured. The attempt at `2026-11-09T05:56:39Z` used `SELECT column_name, datatype, arraysize, size, principal, std FROM TAP_SCHEMA.columns WHERE table_name = 'ps' AND column_name IN ('pl_bmasse','pl_bmassprov','pl_bmasselim','pl_bmasseerr1','pl_bmasseerr2','pl_rade','pl_radelim','pl_radeerr1','pl_radeerr2','pl_name','hostname','pl_refname','default_flag','pl_controv_flag')`; NASA returned VOTable `QUERY_STATUS=ERROR` with `ORA-00936: missing expression`. Neither produced evidence about the fields.

### What repository code establishes

- **VERIFIED:** ARC-03 has generic `DataSchema`/`FieldSchema`; `validate_dataset()` checks only declared presence, nullability, and exact Python types. There is no NASA-specific field schema in the current source or tests, and these models do not encode NASA units, value ranges, limit codes, or scientific rules.
- **VERIFIED:** `analyze_quality()` distinguishes absent/null/blank values, reports exact duplicate *whole records*, and summarizes finite numeric values while excluding booleans. It does not detect duplicate `pl_name` by itself or decide whether records are eligible.
- **VERIFIED:** `Dataset` has no identity or uniqueness contract. It shallow-copies top-level record mappings; `Provenance` records source/retrieval metadata, not scientific identity semantics.
- **VERIFIED:** The current Exoplanet Archive adapter requires caller-selected identity fields to be present and non-null and rejects duplicate values for the caller-supplied identity tuple. That is generic adapter behavior, not a NASA guarantee that `pl_name` or a reference is unique. The adapter performs no NASA-name trimming, case folding, or alias normalization. A future raw extraction intended to audit duplicates must preserve the response and report duplicate groups rather than silently lose them through a selected identity constraint.

### Updated classification and blockers

**Resolved from authoritative documentation and live schema:** physical field descriptions/units and active TAP storage types for the listed fields; the positive-side (`err1`) versus negative-side (`err2`) association; that `pl_bmasselim`/`pl_radelim` are associated limit columns; and the literature-name/reference meanings of `pl_name`, `hostname`, and `pl_refname`. This establishes that numeric checks can operate on `double` mass/radius fields and exact identity audits can operate on `char` columns. Live aggregates establish current null/sign/code counts only for the exact candidate predicate and query time; they do not establish a universal schema nullability or scientific eligibility rule.

**Still UNRESOLVED / blocking:** per-column nullability for the active `ps` schema (not exposed by `TAP_SCHEMA.columns`); uncertainty-value meaning/sign policy beyond NASA's upper/lower side labels and the observed cohort distributions; allowed values and meanings of either active `ps` limit field; scientific handling of zero/negative target or feature values; whether uncertainty-only retention is adequate; eligibility treatment of solution/controversy fields; default-row and `Mass`-cohort approval; and row/unit decisions if exact planet names repeat or identity is missing/ambiguous. Host/reference grouping policy and split feasibility also remain unapproved. Duplicate-name detection itself is an audit operation, not an automatic exclusion rule.

Therefore the previous extraction blockers are narrowed for active TAP storage types, field definitions, uncertainty side-labels, candidate-cohort aggregate distributions, and the ability to define mechanical checks. The limit/censoring blocker itself is not resolved because the active `ps` code meanings remain undocumented. The remaining blockers above, plus reproducible complete extraction, retained raw snapshot/schema, citation/terms review, and documented scientific approval, still prevent dataset generation. This review does not approve the exploratory task, an eligibility cutoff, a final row count, model evaluation, or training.
