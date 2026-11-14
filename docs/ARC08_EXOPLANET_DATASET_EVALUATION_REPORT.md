# ARC08 Exoplanet Dataset Evaluation Report

**Assessment date:** 2026-11-08
**Branch / HEAD:** `arc/08-ai-ml` / `1d438dc`
**Scope:** Bounded structural exploration of NASA Exoplanet Archive Planetary Systems (`ps`) data. This is not approval for research use or ML training.

## 1. Repository and Branch State

**VERIFIED.** The repository was on `arc/08-ai-ml` at `1d438dc` (`feat(arc-08): add NASA Exoplanet Archive data adapter`). Before this report was created, `git status --short --branch` showed a clean worktree tracking `origin/arc/08-ai-ml`. No branch, index, or commit operation was performed.

**VERIFIED.** The repository has synthetic CSV/JSON fixtures, provenance/source sidecars, and empty `data/raw/` and `data/processed/` placeholders (`data/samples/`, `data/metadata/`, `data/raw/`, `data/processed/`). It has no stored Exoplanet Archive response or approved real training dataset. The sample files are examples, not observations.

## 2. Existing Data Pipeline and API Findings

**VERIFIED.** Structured `Dataset`, `Provenance`, `DataSource`, and `DataFormat` contracts are implemented in `src/quantum_space_agi/data/models.py`, `provenance.py`, and `sources.py`. `Dataset` protects top-level mappings but nested JSON values remain mutable; the ingestion and preprocessing APIs are the intended structured interfaces.

**VERIFIED.** Structured APIs include `load_json(text, *, provenance=None)`, `load_csv(text, *, provenance)`, and `load_file(...)` in `src/quantum_space_agi/data/ingestion.py`. JSON loading retains JSON numbers and nulls; CSV cells remain strings. The legacy `load_dataset(...) -> DatasetLoadResult` in `src/quantum_space_agi/data/loader.py` is a different contract and is not interchangeable with `Dataset`.

**VERIFIED.** `validate_dataset(dataset, schema)` in `src/quantum_space_agi/data/schemas.py` reports structural type/presence errors against an explicit `DataSchema`; it does not infer scientific validity. `analyze_quality(dataset)` in `src/quantum_space_agi/data/quality.py` reports missing values, exact duplicate rows, and finite numeric summaries without mutating records. It derives field names from the union of record keys and counts absent keys, `None`, and blank text for observed fields; a field absent from every record must be checked against an explicit schema.

**VERIFIED.** `preprocess_dataset(dataset, *, conversions)` in `src/quantum_space_agi/ml/preprocessing.py` supports only explicit deterministic scalar conversions. It preserves absent/null values or errors according to per-field policies and does not impute, scale, encode, select features, split data, or train models.

**VERIFIED.** `fetch_ps_dataset(columns, *, order_by, row_identity_fields, limit, timeout=20.0)` is implemented in `src/quantum_space_agi/data/adapters/exoplanet_archive.py` (lines 75–87). It performs a GET to the fixed sync endpoint, requests JSON, allows 1–100 rows, enforces a 10 MiB response limit and finite positive timeout, reads at most `MAX_RESPONSE_BYTES + 1`, rejects missing selected fields, non-finite numbers, null/missing identities and duplicate identities in the returned result, records exact ADQL, a response SHA-256, and retrieval time. It has no retries and retains no response bytes after parsing (lines 23–27, 89–183).

**VERIFIED.** `docs/ML_REQUIREMENTS.md` says no prediction task, target, or training dataset is approved; it requires a decision/use case, unit and timing, features and target, suitable data, baseline, leakage-safe evaluation, and agreed metrics/error thresholds before training (lines 3–21, 38–53).

## 3. NASA Exoplanet Archive `ps` Table Overview

**VERIFIED.** NASA describes `ps` as an archive of planetary-system solutions, including all solutions for confirmed systems and Kepler, K2, and TESS candidate solutions. A row contains planet, stellar, and system properties; the table can include atypical systems and multiple stars. Thus rows are not simply one independent, definitive record per host system. [NASA: About the Planetary Systems Table](https://exoplanetarchive.ipac.caltech.edu/docs/planetarysystems_about.html)

**VERIFIED.** `pl_name` is a commonly used planet name; `hostname` is a commonly used stellar name; `pl_refname` identifies the publication reference for a parameter set. `default_flag` identifies a selected default parameter set and `soltype` describes solution disposition. [NASA: Planetary Systems column definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html)

**VERIFIED.** `pl_orbper` is orbital period in days, with upper/lower uncertainty columns `pl_orbpererr1` and `pl_orbpererr2` and a limit column. `pl_rade` is planet radius in Earth radii, with corresponding uncertainty and limit columns. The archive documents the meaning of these fields, but their interpretation still depends on the specific published solution. [NASA: Planetary Systems column definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html)

**VERIFIED.** NASA's interactive-table guidance says nulls are displayed as blank spaces and mean no value was entered; zero is not null. In this request's JSON response, missing measurements arrived as JSON `null`, which the existing adapter and loader preserved as Python `None`. This does not establish every missing-value convention for every archive field or format. [NASA: Interactive Exoplanet Viewer, “Filtering Null Values”](https://exoplanetarchive.ipac.caltech.edu/docs/ICEexohelp.html)

**VERIFIED.** The NASA TAP guide documents the synchronous `/TAP/sync` endpoint, named-column ADQL queries, and JSON output. [NASA: TAP User Guide](https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html)

**VERIFIED.** NASA publishes a DOI for the Planetary Systems table: `10.26133/NEA12`. That is a table citation, not a unique immutable identifier for this exact query result. The adapter's `citation.doi` remains `None`, and `dataset_version`/`archive_release` are `None`; the response checksum identifies the retrieved bytes but cannot recover them. [NASA: DOI tags](https://exoplanetarchive.ipac.caltech.edu/docs/doi.html)

## 4. Dataset Acquisition Details

**VERIFIED.** One bounded acquisition was made through the existing adapter after its limits and the chosen columns were checked. The first sandboxed attempt failed at DNS resolution before reaching NASA. The same single request was then retried once after the execution environment authorized network access; it succeeded. No additional data request was made.

The request selected 13 documented fields and returned 30 records. Identity fields were `pl_name` and `pl_refname`; both were included in the order clause. The exact query recorded by the adapter was:

```sql
SELECT TOP 30 pl_name, pl_refname, hostname, default_flag, soltype, pl_orbper, pl_orbpererr1, pl_orbpererr2, pl_orbperlim, pl_rade, pl_radeerr1, pl_radeerr2, pl_radelim FROM ps ORDER BY pl_name, pl_refname
```

**VERIFIED provenance from the returned in-memory `Dataset`:**

- `dataset_id`: `nasa-exoplanet-archive:ps`
- Source endpoint: `https://exoplanetarchive.ipac.caltech.edu/TAP/sync`
- `retrieved_at`: `2026-11-08T07:40:19.985933+00:00`
- Response SHA-256: `b665c3a3b93b096df9bfa13e74cfa38f36f40bd8d30e5248b144314c5511690e`
- `dataset_version`: `None`; `archive_release`: `None`
- Requested response format: JSON

The 30-row result existed only in the Python process and was not saved. The adapter itself states that it does not retain response bytes after parsing. A checksum and query/time are useful provenance, but an evolving archive may return different bytes for the same query later.

## 5. Dataset Structure and Quality Evaluation

**VERIFIED.** The response contained 30 records and 13 fields. Every selected field was present in each record, the selected identity values were non-null, and the adapter accepted the result without finding duplicate `(pl_name, pl_refname)` identities in this sample. `analyze_quality()` found **zero exact duplicate rows**. These are sample-level checks only; they do not prove uniqueness across the complete archive or at another retrieval time.

**VERIFIED observed JSON types and null counts:**

| Field(s) | Observed types in 30 rows | Null count |
| --- | --- | ---: |
| `pl_name`, `pl_refname`, `hostname`, `soltype` | string | 0 each |
| `default_flag` | integer | 0 |
| `pl_orbper`, `pl_orbpererr1`, `pl_orbpererr2` | float or null | 6, 7, 7 |
| `pl_orbperlim` | integer or null | 6 |
| `pl_rade`, `pl_radeerr1`, `pl_radeerr2` | float or null | 9 each |
| `pl_radelim` | integer or null | 7 |

There were no absent selected fields or empty-string values in the returned records. `analyze_quality()` derives the fields it reports from the union of record keys; its missing counts include absent keys, `None`, and blank text for those observed fields. A field absent from every record requires an explicit schema check (see `src/quantum_space_agi/data/quality.py`, lines 46–63).

**VERIFIED sample-only numeric ranges:** `pl_orbper` ranged from 1.644224613 to 141.24164672 days across 24 non-null values; `pl_rade` ranged from 0.823 to 14.19 Earth radii across 21 non-null values. The negative `pl_orbpererr2` and `pl_radeerr2` values are lower-uncertainty fields, not automatically invalid negative measurements. The quality utility's arithmetic means for uncertainty and flag columns are not scientifically meaningful summary statistics. No outlier was declared erroneous.

**Schema validation not run.** No approved versioned schema for these selected JSON wire types was found in the repository. The column documentation establishes scientific names/units but the adapter does not retrieve TAP_SCHEMA, and deriving a production schema from one 30-row sample would overstate evidence. `validate_dataset()` should be used once an explicit schema has been reviewed; for this exploratory sample, adapter structural checks and `analyze_quality()` were defensible.

## 6. Scientific Meaning, Units, and Provenance

**VERIFIED.** The period and radius units and asymmetric error-field roles are documented by NASA. The sample's null measurements are preserved rather than replaced. `pl_orbperlim`/`pl_radelim` values were zero where non-null, but this assessment does not assign their numeric code semantics without a confirmed table-specific code definition.

**UNKNOWN.** The sample does not establish publication-level scientific validity, consistent measurement methods, uncertainty calibration, detection completeness, observational selection, a temporal snapshot, or suitability for a particular inference. The ordered `TOP 30` request is an alphabetic slice based on planet/reference names, not a representative sample.

**VERIFIED limitation.** The adapter records source, query, retrieval time, checksum, ordering, identity fields, and null/absent behavior (`exoplanet_archive.py`, lines 191–235). Its dataset metadata leaves table/column descriptions, units, and archive types unset. For this report, authoritative documentation supplied definitions and units externally; those definitions were not inserted into the acquired `Dataset`. The known table DOI also is not a snapshot identifier.

## 7. Preprocessing Readiness

**VERIFIED.** Numeric JSON values arrived as Python `float` or `int`, and nulls arrived as `None`; no string-to-number conversion is needed for the sampled numeric fields. `default_flag` and limit fields arrived as integers. Do not convert them to booleans, reinterpret limit flags, combine asymmetric uncertainties, convert units, impute nulls, or select a “default” row without an explicit scientific rule.

`preprocess_dataset()` can apply explicit scalar conversion with `preserve` or `error` policies (`src/quantum_space_agi/ml/preprocessing.py`, lines 32–64), but no conversion was applied. Decisions are still needed about missingness, candidate versus confirmed solutions, row selection, uncertainty/limit semantics, and whether one row or multiple literature solutions form the analysis unit.

## 8. ML Readiness and Limitations

**VERIFIED.** The repository has no approved target/label, feature-target extraction, split API, predictor, task-specific metric, or evaluation framework. `docs/ML_REQUIREMENTS.md` explicitly blocks model training until the task, data, baseline, evaluation design, metrics, and acceptable errors are approved.

**Conclusion: baseline ML is not currently justified.** A successful parse, zero duplicate rows in a small query, and usable numerical columns do not define a user decision or prediction target. This sample is too small and deliberately alphabetically bounded to support coverage, representativeness, or performance claims. The table's multiple solutions and related rows create possible entity/reference leakage if a later task splits records without grouping by planet/system/source. A domain problem may also be better answered by deterministic calculation, simulation, or optimization.

No target is proposed here. Any future task must document prediction unit and timing, available-at-inference features, label-generation process, dataset rights/coverage, baseline, error costs, leakage-safe split, and preselected metrics before model work begins.

## 9. Amran's Required ARC-08 Contributions

**VERIFIED assessment:** no separate ARC-08 implementation contribution from Amran is required to complete this bounded structural exploration. The existing adapter and data-quality APIs were sufficient.

**Future domain-review question, before scientific use:** for the intended analysis, which PS solution records are admissible, and how should `default_flag`, `soltype`, `pl_refname`, `pl_orbper`/`pl_rade`, asymmetric `err1`/`err2`, and limit fields determine inclusion and interpretation? This needs a task-specific scientific decision; it is not a request to build ARC-04/05 systems or to approve a target now.

## 10. Blockers and Recommended Next Steps

1. Keep this result classified as an exploratory, non-persisted sample; do not describe it as an approved training dataset.
2. If the team chooses to preserve a dataset artifact, agree on storage/retention and save the exact response bytes alongside query, checksum, timestamp, and citation. Do not treat a checksum as a substitute for the source bytes.
3. Define the scientific question and intended decision before choosing records, features, or a target. Have an appropriate domain reviewer decide how solutions, candidate dispositions, references, uncertainties, limits, and missing values should be handled.
4. Define and review a versioned schema from authoritative TAP type metadata plus domain constraints, then run `validate_dataset()` on a deliberately acquired dataset.
5. Assess coverage and bias using a defensible extraction strategy; the alphabetic 30-row slice cannot answer those questions.
6. Only after task approval, determine whether prediction adds value beyond deterministic computation; then define a non-ML baseline, leakage-safe evaluation split, error costs, and metrics as required by `docs/ML_REQUIREMENTS.md`.

## 11. Final Dataset Readiness Verdict

**STRUCTURALLY EVALUABLE; NOT SCIENTIFICALLY OR ML READY.** The adapter successfully acquired a bounded, provenance-linked sample, preserved JSON values/nulls, and passed its structural and sample identity checks. The existing quality utility found missing measurements and no exact duplicate rows in that sample. Scientific inclusion rules, dataset representativeness, an approved ML task, a target, and an evaluation plan remain unresolved. No model or training pipeline should begin.

## Execution Record

- **Executed:** inspected repository state, adapter and tests, data APIs, requirements and architecture documents; consulted NASA Exoplanet Archive primary documentation; made one successful bounded request through `fetch_ps_dataset()` and evaluated its in-memory result with `analyze_quality()`.
- **Network:** two execution attempts were made for the same query; the first failed at DNS before reaching the service, and the single authorized retry succeeded. Thus the archive returned data only once.
- **Tests/checks:** no pytest, Ruff, mypy, or compile checks were run. This assessment used the one live adapter call and existing quality utility; it is not a test-suite verification.
- **Data persistence:** no downloaded rows or response bytes were saved.
- **Files:** created this requested report only. No implementation, fixture, configuration, or Git index/commit was changed.

## Beginner Learning Notes

- JSON `null` becomes Python `None`; keep missing data distinct from zero and do not fill it without a domain rule.
- A dataset row's meaning comes from its schema and sampling process. In PS, related planets and multiple published solutions mean rows may not be independent.
- Units and uncertainty columns are part of the measurement contract. Preserve asymmetric errors and limit flags until their meanings are explicitly reviewed.
- A small, sorted sample is useful for checking connectivity and parsing, but not for judging scientific representativeness or training a model.
- Provenance helps identify a retrieval; storing the exact source bytes is necessary if the artifact must be reprocessed later.
- ML readiness starts with a decision and trustworthy target, not with finding numeric columns.
