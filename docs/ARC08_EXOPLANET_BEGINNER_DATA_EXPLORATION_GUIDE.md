# NASA Exoplanet Archive: Beginner Data Exploration Guide

This guide explains the 13 fields used in the ARC-08 evaluation of NASA's Planetary Systems (`ps`) table. It is a learning and data-literacy document. It does not approve a scientific study, an ML task, or model training.

The evaluation report is the source for the retrieved sample's exact query, values summary, provenance, and limitations: [`ARC08_EXOPLANET_DATASET_EVALUATION_REPORT.md`](ARC08_EXOPLANET_DATASET_EVALUATION_REPORT.md). The 30-row response itself was not saved. This guide does not recreate or claim to contain those records.

## 1. Introduction

You will learn what the examined fields describe, how to distinguish a measurement from an identifier or archive label, and how to use existing project APIs to inspect a dataset. Definitions explicitly attributed to NASA were checked against NASA's archive documentation. Beginner-friendly English and Bangla explanations are paraphrases to make those definitions easier to understand.

### The exact 13 fields examined

The query in the evaluation report selected exactly:

```text
pl_name, pl_refname, hostname, default_flag, soltype,
pl_orbper, pl_orbpererr1, pl_orbpererr2, pl_orbperlim,
pl_rade, pl_radeerr1, pl_radeerr2, pl_radelim
```

No other fields are described as part of that sample.

## 2. What Is an Exoplanet?

**NASA definition:** An exoplanet is a planet outside our Solar System, usually orbiting another star. NASA also describes candidate detections as objects that need additional observations before their nature is certain. [NASA Science: What is an exoplanet?](https://science.nasa.gov/exoplanets/big-questions/) · [NASA Science: Exoplanet facts](https://science.nasa.gov/exoplanets/facts/)

**বাংলা:** এক্সোপ্ল্যানেট হলো আমাদের সৌরজগতের বাইরের একটি গ্রহ; সাধারণত এটি অন্য একটি নক্ষত্রকে প্রদক্ষিণ করে।

An exoplanet table is a scientific catalog: it organizes names, measurements or reported parameters, references, and classifications. A catalog entry is not necessarily a direct telescope reading. A value may have been estimated or derived by researchers from observations and a scientific model. The particular method must be checked in its source paper or other field-specific documentation.

## 3. Understanding NASA's Planetary Systems (`ps`) Table

**NASA describes `ps` as a table of planetary-system solutions.** Each row contains a self-contained group of planet, stellar, and system parameters for a reference; the table contains one row per planet per reference. It includes multiple solutions and can include candidate solutions associated with confirmed systems. NASA's separate `PSCompPars` product is more filled-in and has one row per planet, but may combine parameters that are not self-consistent. These are different products; this guide concerns `ps`. [NASA: About the Planetary Systems table](https://exoplanetarchive.ipac.caltech.edu/docs/planetarysystems_about.html) · [NASA: Planetary Systems table definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html)

**বাংলা:** `ps` টেবিলটি গ্রহ-ব্যবস্থার বিভিন্ন প্রকাশিত সমাধান বা parameter set রাখে। একই গ্রহের জন্য একাধিক প্রকাশনা বা সমাধান থাকলে একাধিক সারি হতে পারে।

- A **planetary system** is a star or group of stars and the associated planets and other bodies considered together. NASA's table can include systems with multiple stars and unusual cases such as free-floating planets.
- A **planet record** in `ps` is not necessarily one unique physical planet row across the whole table. The table's row unit is a planet's parameter solution associated with a reference.
- A **planetary solution** here means a set of parameters associated with a particular reference. Different research papers can report different parameter sets for the same planet; their methods, evidence, and publication dates can differ.
- A **candidate** is a possible planet detection whose status can require more observations or validation. NASA notes that candidate solutions are included in the table. The exact category values for `soltype` were not included in the saved evaluation summary, so this guide does not list or decode specific tokens.
- `default_flag` and `soltype` are archive descriptors, not measurements of the planet's physical size or orbit. A default parameter set is selected by the archive; it is not automatically the “best” value for every research question. NASA's FAQ explains that default values are selected from a single published reference for internal consistency and to balance completeness and precision. [NASA FAQ: What are default parameters?](https://exoplanetarchive.ipac.caltech.edu/docs/faq.html)

**Hypothetical example (not a claim about the 30 retrieved rows):** if two papers publish different orbital-period/radius parameter sets for the same named planet, `ps` may contain a row for each reference. Treating those two rows as independent planets would double-count the planet and may leak nearly identical information across a later statistical split.

## 4. Scientific Data Dictionary — All 13 Fields

### How to read the type information

The types below are **observed JSON value types in the 30-row sample**, as recorded in the evaluation report. They are not a complete NASA database schema. The adapter does not fetch `TAP_SCHEMA`; a new response may contain other values or different null patterns. NASA's column definitions provide meanings and units, while the report provides only these sample-level JSON types and null counts.

“Larger” and “smaller” are discussed only for numerical quantities where NASA's definition supports that interpretation. Identifiers and categories have no natural numerical ordering. Every Bangla explanation is a beginner-friendly paraphrase, not an official NASA translation.

### 4.1 `pl_name` — Planet name

- **NASA definition:** The planet name most commonly used in the literature.
- **সহজ বাংলা:** গবেষণাপত্রে গ্রহটির জন্য সবচেয়ে প্রচলিত নাম।
- **Scientific role:** Name/identifier-like text; it is not a physical measurement. **Observed JSON type:** string; **unit:** none; nulls in sample: 0.
- **Value meaning:** A name identifies a catalog object in context; being alphabetically earlier/later or having a longer name has no scientific magnitude.
- **Caveat and possible use:** Useful for looking up or grouping records, but do not assume this field alone is a globally stable row key. One planet can have multiple reference/solution rows. Could support record linkage after an explicit identity policy is reviewed; it is not automatically a model feature or target.

### 4.2 `pl_refname` — Planetary parameter reference

- **NASA definition:** The publication reference used for the given planet parameter set.
- **সহজ বাংলা:** এই সারির গ্রহ-সংক্রান্ত পরামিতিগুলোর জন্য ব্যবহৃত প্রকাশনার সূত্র।
- **Scientific role:** Source/provenance metadata; not a measurement. **Observed JSON type:** string; **unit:** none; nulls in sample: 0.
- **Value meaning:** Different reference text points to a different source reference; it is not a numerical quality score.
- **Caveat and possible use:** Important for tracing and comparing solutions. Combined with `pl_name`, it was the declared identity pair for checking duplicate identities in the 30-row sample. It does not by itself tell you a paper's method, reliability, or whether its value is preferred for a particular task.

### 4.3 `hostname` — Host name

- **NASA definition:** The stellar name most commonly used in the literature.
- **সহজ বাংলা:** যে নক্ষত্রকে ঘিরে গ্রহটি আছে, সেই নক্ষত্রের প্রচলিত নাম।
- **Scientific role:** Host-star identifier-like text; not a measurement. **Observed JSON type:** string; **unit:** none; nulls in sample: 0.
- **Value meaning:** Different names are labels, not larger/smaller physical values.
- **Caveat and possible use:** Can help relate planets to a host system, but confirm name conventions and grouping rules. One host can have multiple planets and multiple published solutions. It could be useful for group-aware descriptive analysis once identity handling is reviewed.

### 4.4 `default_flag` — Default parameter-set flag

- **NASA definition:** A Boolean flag indicating whether the given set of planet parameters was selected as the default (`1=yes`, `0=no`).
- **সহজ বাংলা:** আর্কাইভ এই parameter set-টিকে default হিসেবে বেছে নিয়েছে কি না তা বোঝায় (`1=হ্যাঁ`, `0=না`)।
- **Scientific role:** Archive selection/classification metadata, not a measured physical quantity. **Observed JSON type:** integer; **unit:** none; nulls in sample: 0.
- **Value meaning:** NASA documents `1` as selected default and `0` as not selected. These are categories, not a scale where 1 is “twice” 0.
- **Caveat and possible use:** Default selection reflects the archive's selection policy and may be useful for a clearly defined table-filtering task. It is not a confidence score, universal scientific truth, or automatic instruction to discard other solutions. NASA explains that default parameters for confirmed planets are drawn from a single reference to support internal consistency and balance completeness with precision. [NASA FAQ](https://exoplanetarchive.ipac.caltech.edu/docs/faq.html)

### 4.5 `soltype` — Solution type

- **NASA definition:** The disposition of the planet according to the given planet parameter set.
- **সহজ বাংলা:** এই parameter set অনুযায়ী গ্রহটির অবস্থা বা disposition-এর শ্রেণি।
- **Scientific role:** Categorical archive metadata. **Observed JSON type:** string; **unit:** none; nulls in sample: 0.
- **Value meaning:** It identifies a category/disposition, not an ordered numeric quantity. **Specific category names and their meanings: Unknown / Not verified** from the saved sample evaluation.
- **Caveat and possible use:** Do not treat this as a scientifically approved label or target. To interpret a particular token, consult the current column/product documentation and inspect the relevant source. It may support stratification only after a domain reviewer confirms the category semantics and intended use.

### 4.6 `pl_orbper` — Orbital period

- **NASA definition:** The time the planet takes to complete an orbit around its host star or system. NASA gives the unit as days.
- **সহজ বাংলা:** গ্রহটির তার নক্ষত্র বা ব্যবস্থাকে একবার প্রদক্ষিণ করতে যত সময় লাগে; একক দিন।
- **Scientific role:** Reported planet parameter for a solution; whether a particular value is directly measured or derived from a model depends on its reference. **Observed JSON type:** float or null; 6 nulls; unit: days.
- **Value meaning:** A larger value means a longer orbital period; a smaller value means a shorter period, in this field's definition. This alone does not establish orbital distance or cause.
- **Caveat and possible use:** Preserve the associated reference, error fields, and limit flag. The 30-row report observed values from 1.644224613 to 141.24164672 days, but that is only a range in an alphabetic sample, not a population summary. Could be relevant to a future, reviewed orbital-parameter study; it is not an approved target.

### 4.7 `pl_orbpererr1` — Upper orbital-period uncertainty

- **NASA definition:** The `(+)` uncertainty column associated with `pl_orbper`; the uncertainty is expressed in the period's unit, days.
- **সহজ বাংলা:** কক্ষপথের সময়ের ঊর্ধ্বমুখী অনিশ্চয়তার মান; একক দিন।
- **Scientific role:** Uncertainty metadata associated with a reported parameter. **Observed JSON type:** float or null; 7 nulls; unit: days.
- **Value meaning:** A larger positive uncertainty magnitude indicates a wider upper-side uncertainty as reported; it is not a second period value.
- **Caveat and possible use:** The uncertainty's statistical convention and comparability depend on the source analysis. Keep it paired with the measurement and `pl_refname`; do not average values from different papers without a scientific method. Useful for uncertainty-aware comparisons if a future question is approved.

### 4.8 `pl_orbpererr2` — Lower orbital-period uncertainty

- **NASA definition:** The `(-)` uncertainty column associated with `pl_orbper`; unit: days.
- **সহজ বাংলা:** কক্ষপথের সময়ের নিম্নমুখী অনিশ্চয়তার মান; একক দিন।
- **Scientific role:** Lower-side uncertainty metadata. **Observed JSON type:** float or null; 7 nulls; unit: days.
- **Value meaning:** The evaluation sample contained negative values, consistent with a signed lower-side uncertainty representation. A more negative number can have a larger absolute uncertainty magnitude; it does **not** mean the orbital period itself is negative.
- **Caveat and possible use:** Do not change signs or combine the upper/lower errors without a documented rule. The precise confidence/statistical interpretation can depend on the reference. Potentially useful when comparing reported precision with source context.

### 4.9 `pl_orbperlim` — Orbital-period limit flag

- **NASA definition:** The limit-column field associated with `pl_orbper`; the column documentation identifies it as a limit field.
- **সহজ বাংলা:** orbital period-এর মানটি কী ধরনের সীমা বা limit হিসেবে রিপোর্ট হয়েছে তা নির্দেশ করার archive field।
- **Scientific role:** Encoded limit metadata, not a period measurement. **Observed JSON type:** integer or null; 6 nulls; **unit:** none.
- **Value meaning:** All non-null values in the sample were `0`. **The meaning of numeric code `0` and other possible codes: Unknown / Not verified** for this report; do not infer it from the name.
- **Caveat and possible use:** Treat as categorical/encoded metadata until the current `ps` code definition is verified. It may be important for deciding whether a value is a detection, bound, or other limit, but that decision requires an authoritative code mapping and domain review.

### 4.10 `pl_rade` — Planet radius in Earth radii

- **NASA definition:** A line-segment length from the planet's center to its surface, measured in Earth radii.
- **সহজ বাংলা:** গ্রহের কেন্দ্র থেকে পৃষ্ঠ পর্যন্ত ব্যাসার্ধ, পৃথিবীর ব্যাসার্ধের এককে প্রকাশিত।
- **Scientific role:** Reported planet parameter for a solution. Whether a specific value is directly reported, inferred, or calculated depends on its source. **Observed JSON type:** float or null; 9 nulls; unit: Earth radii.
- **Value meaning:** A larger value means a larger reported radius relative to Earth's radius; a smaller value means a smaller reported radius.
- **Caveat and possible use:** Radius estimates depend on observational/model context. Preserve its source reference, upper/lower uncertainty, and limit field. The sample range (0.823–14.19 Earth radii) is descriptive only for these 21 non-null sample entries. Could be relevant to future size or population studies after domain review, not automatically an ML target.

### 4.11 `pl_radeerr1` — Upper radius uncertainty

- **NASA definition:** The positive/upper uncertainty column associated with `pl_rade`; unit: Earth radii.
- **সহজ বাংলা:** পৃথিবীর ব্যাসার্ধের এককে গ্রহের radius-এর ঊর্ধ্বমুখী অনিশ্চয়তা।
- **Scientific role:** Uncertainty metadata. **Observed JSON type:** float or null; 9 nulls; unit: Earth radii.
- **Value meaning:** Larger reported upper uncertainty magnitude generally means a wider upper-side uncertainty, not a larger planet radius.
- **Caveat and possible use:** Source methods and confidence conventions may differ. Keep it paired with `pl_rade` and the reference. It may be useful for uncertainty-aware analysis after scientific review.

### 4.12 `pl_radeerr2` — Lower radius uncertainty

- **NASA definition:** The negative/lower uncertainty column associated with `pl_rade`; unit: Earth radii.
- **সহজ বাংলা:** পৃথিবীর ব্যাসার্ধের এককে গ্রহের radius-এর নিম্নমুখী অনিশ্চয়তা।
- **Scientific role:** Lower-side uncertainty metadata. **Observed JSON type:** float or null; 9 nulls; unit: Earth radii.
- **Value meaning:** The sample included negative values, matching a signed lower-side uncertainty representation. More negative may indicate a larger absolute lower-side uncertainty; it does not mean a negative radius.
- **Caveat and possible use:** Do not take the absolute value or combine asymmetric errors without an explicit analysis rule. Compare uncertainties only with attention to their references and methods.

### 4.13 `pl_radelim` — Radius limit flag

- **NASA definition:** The limit-column field associated with `pl_rade`; NASA's column definitions identify it as the radius limit column.
- **সহজ বাংলা:** radius-এর রিপোর্ট করা মান কোনো limit বা সীমা হিসেবে দেওয়া হয়েছে কি না তা বোঝানোর archive field।
- **Scientific role:** Encoded limit metadata, not a radius measurement. **Observed JSON type:** integer or null; 7 nulls; **unit:** none.
- **Value meaning:** All non-null sample values were `0`. **The meaning of numeric code `0` and other possible codes: Unknown / Not verified** from the materials used for this evaluation.
- **Caveat and possible use:** Do not interpret it as a numerical quantity. Verify the current `ps` code mapping before deciding whether radius values are detections or limits. It may matter for future analysis of censored/limited measurements.

### Field-definition references

NASA's column page defines `pl_name`, `hostname`, `default_flag`, `soltype`, `pl_refname`, the orbital-period and radius fields, and their associated uncertainty/limit columns. [NASA Exoplanet Archive: Planetary Systems column definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html)

The precise numeric codes for `pl_orbperlim` and `pl_radelim` were not established from the evidence captured in the evaluation report. Their code meanings are therefore intentionally marked unknown above. The archive's TAP schema/data type information was not retrieved; listed types describe the observed sample only.

## 5. Understanding Units, Uncertainty, and Missing Values

### Units

A unit tells you what a number measures. Here `pl_orbper` uses **days** and `pl_rade` uses **Earth radii**. Their associated uncertainty fields use the same measurement units. Do not compare or combine numeric values with different units as if they meant the same thing. The `*lim` fields have no physical unit because they are encoded limit metadata.

**বাংলা:** একক (unit) বলে দেয় সংখ্যাটি কী পরিমাপ করছে। কক্ষপথের সময় দিনের এককে, আর radius পৃথিবীর ব্যাসার্ধের এককে। একক না মিলিয়ে সংখ্যা তুলনা করা ঠিক নয়।

### Uncertainty

An uncertainty describes the reported range or error around a parameter. NASA lists separate upper (`err1`, `+`) and lower (`err2`, `−`) uncertainty columns. They can be asymmetric. A negative `err2` value in the sample is not a negative physical period or radius. Do not erase the sign, average the two sides, or compare uncertainty values across papers as a quality score without checking how each source calculated them.

**বাংলা:** অনিশ্চয়তা (uncertainty) কোনো পরিমাপ কতটা নির্ভুল বা অনির্দিষ্ট হতে পারে তা জানায়। `err1` ও `err2` দুই দিকের আলাদা সীমা দেখায়; সেগুলো সমান হওয়া বাধ্যতামূলক নয়।

### Missing values

The sample contained JSON `null` values; the adapter/loader preserved these as Python `None`. NASA's interactive-table guidance describes null as a blank space meaning no value was entered, and distinguishes null from zero. This supports treating `null` as unavailable in this context, not as zero. It does not tell us why a particular value is absent. [NASA Interactive Exoplanet Viewer: Filtering null values](https://exoplanetarchive.ipac.caltech.edu/docs/ICEexohelp.html)

**বাংলা:** `null` মানে এখানে মানটি দেওয়া নেই; এটি শূন্য (`0`) নয়। কেন মানটি নেই, তা আলাদা করে জানতে হতে পারে।

Missingness can affect a scientific conclusion. For example, values may be absent because a parameter was not measured, not published, or not selected for a particular solution. Which explanation applies is **unknown for an individual null** unless the reference or archive documentation says more. Do not replace missing values with zero or a guessed value.

## 6. Understanding Multiple Planetary Solutions

NASA says each `ps` row is a planet's parameter set for a reference. Different publications can analyze the same planet and publish different values or different subsets of parameters. The table can therefore contain multiple rows associated with one planet. `pl_refname` helps identify the publication reference; `default_flag` marks a parameter set the archive selected as default; `soltype` records the disposition of a planet according to that set.

This means:

- One table row is not automatically one independent planet.
- Two rows for one planet may be related observations or estimates, not independent examples.
- A host (`hostname`) can have multiple planets, and each planet can have multiple references/solutions.
- A default selection is an archive choice with a stated policy; it does not make other solutions scientifically irrelevant.
- Candidate/confirmed distinctions and solution categories must be interpreted using their current documentation and the intended scientific question.

**বাংলা:** একই গ্রহের একাধিক গবেষণাপত্রে আলাদা পরিমাপ বা বিশ্লেষণ থাকতে পারে। তাই টেবিলের দুই সারি মানেই দুইটি স্বাধীন গ্রহ নয়।

## 7. Dataset Quality and Limitations

The evaluation report records a single query: `SELECT TOP 30 ... FROM ps ORDER BY pl_name, pl_refname`, retrieving 30 rows and 13 fields. The query sorted planet and reference names and selected the first 30 rows under that ordering. This is useful for a small structural inspection, but it is not a random or representative sample. Alphabetical ordering can over-represent whichever names happen to come first and says nothing about coverage across planets, systems, discovery methods, or publication periods.

The adapter checked the selected `(pl_name, pl_refname)` row identity fields for duplicates in the returned result; it accepted the sample. `analyze_quality()` reported zero **exactly identical full rows**. These findings mean only that this small response had no duplicate declared identity pair and no exact duplicate record among its 30 rows.

They do **not** prove:

- that the identity pair is unique across all of `ps` or remains unique in future archive versions;
- that there are no repeated planets, hosts, or related solutions;
- that the sample represents the archive or the universe of exoplanets;
- that all required values are present or that present values are scientifically accurate;
- that the archive is approved for any ML task.

The report recorded nulls in orbital period (6/30), its upper and lower uncertainties (7/30 each), its limit field (6/30), radius (9/30), both radius uncertainties (9/30 each), and its limit field (7/30). Names, reference, host, solution type, and default flag had no nulls in this sample. Missing values can reflect data availability or reporting choices; their causes were not individually determined.

The numeric range summary is sample-only: `pl_orbper` ranged 1.644224613–141.24164672 days over 24 non-null values; `pl_rade` ranged 0.823–14.19 Earth radii over 21 non-null values. Ranges and averages do not establish errors or scientific outliers. `analyze_quality()` converts finite numeric values to floats for statistics and excludes booleans; means of flags and signed uncertainties should not be interpreted as physical summaries.

The sample is not approved for ML training because there is no approved prediction question, target, feature availability rule, dataset snapshot/coverage assessment, baseline, split strategy, or task-specific metric. `docs/ML_REQUIREMENTS.md` and [`ARC08_ML_READINESS_DECISION.md`](ARC08_ML_READINESS_DECISION.md) record the current **NO-GO** decision.

## 8. Practical Data Exploration with Existing Project APIs

### What can be reproduced

The repository can reproduce the **request definition** from the evaluation report, including its query fields, ordering, and limit. It can make a future fresh retrieval using `fetch_ps_dataset(...)`, but this guide intentionally does not do so. The exact 30-row response was not saved, so the repository cannot reload or recompute statistics over those exact rows. The recorded checksum can verify bytes only if those bytes are available; it cannot recreate them.

The APIs below are demonstrated on **synthetic, in-memory examples only**. The names `Example b` and `Example c`, their period/radius values, and the CSV values below are invented solely to illustrate code; they are not NASA records.

### Load JSON, validate declared structure, and analyze quality

Actual public interfaces used here:

- `load_json(text: str, *, provenance: Provenance | None = None) -> Dataset`
- `DataSchema(identifier: str, version: str, fields: tuple[FieldSchema, ...])`
- `FieldSchema(name: str, value_type: type[object], required: bool = True, allow_none: bool = False)`
- `validate_dataset(dataset: Dataset, schema: DataSchema) -> SchemaValidationReport`
- `analyze_quality(dataset: Dataset, *, validation_report: SchemaValidationReport | None = None) -> DataQualityReport`

```python
from datetime import UTC, datetime

from quantum_space_agi.data import (
    DataFormat,
    DataSchema,
    DataSource,
    FieldSchema,
    Provenance,
    analyze_quality,
    load_json,
    validate_dataset,
)

provenance = Provenance(
    dataset_id="synthetic:exoplanet-example",
    source=DataSource(
        identifier="synthetic-example",
        description="Synthetic example for learning only",
    ),
    retrieved_at=datetime.now(UTC),
    data_format=DataFormat.JSON,
)

text = (
    '[{"pl_name":"Example b","pl_orbper":12.5,"pl_rade":2.1},'
    '{"pl_name":"Example c","pl_orbper":null,"pl_rade":4.0}]'
)
dataset = load_json(text, provenance=provenance)

schema = DataSchema(
    identifier="synthetic-exoplanet-example",
    version="1",
    fields=(
        FieldSchema("pl_name", str),
        FieldSchema("pl_orbper", float, allow_none=True),
        FieldSchema("pl_rade", float, allow_none=True),
    ),
)
validation = validate_dataset(dataset, schema)
quality = analyze_quality(dataset, validation_report=validation)

print(validation.is_valid)
print(quality.record_count, dict(quality.missing_values))
print(quality.duplicate_groups)
```

Schema validation checks only the types and presence rules declared in `schema`. It does not verify astronomy, units, plausible ranges, or whether these synthetic records are real. `analyze_quality()` derives field names from the union of record keys and counts absent keys, `None`, and empty/whitespace-only strings as missing for those observed fields. A declared field absent from every record is not reported by quality analysis; use schema validation to detect it. Quality analysis also reports exact duplicate rows and basic finite numeric statistics. Inspect each report rather than treating a successful call as scientific validation.

### Load CSV and apply an explicit conversion

Actual public interfaces used here:

- `load_csv(text: str, *, provenance: Provenance) -> Dataset`
- `FieldConversion(field_name: str, target_type: type[int] | type[float], absent_policy: FieldPolicy, null_policy: FieldPolicy)`; `FieldPolicy` is defined in `quantum_space_agi.ml.preprocessing`, is not re-exported from `quantum_space_agi.ml`, and allows `"preserve"` or `"error"`.
- `preprocess_dataset(dataset: Dataset, *, conversions: Sequence[FieldConversion]) -> Dataset`

```python
from datetime import UTC, datetime

from quantum_space_agi.data import DataFormat, DataSource, Provenance, load_csv
from quantum_space_agi.ml import FieldConversion, preprocess_dataset

csv_provenance = Provenance(
    dataset_id="synthetic:csv-example",
    source=DataSource(
        identifier="synthetic-csv-example",
        description="Synthetic example for learning only",
    ),
    retrieved_at=datetime.now(UTC),
    data_format=DataFormat.CSV,
)
csv_dataset = load_csv(
    "pl_name,pl_orbper\nExample b,12.5\nExample c,365\n",
    provenance=csv_provenance,
)
processed = preprocess_dataset(
    csv_dataset,
    conversions=(
        FieldConversion(
            field_name="pl_orbper",
            target_type=float,
            absent_policy="error",
            null_policy="preserve",
        ),
    ),
)
```

CSV values start as strings, which is why the example explicitly converts the period field. This conversion changes representation only; it does not convert units or check whether the values are scientifically valid. The example contains no empty cell: `load_csv()` preserves empty cells as empty strings, and `preprocess_dataset()` does not treat `""` as `None`, so an empty string would fail float conversion. Choose and document a missing-value policy before processing actual data.

To read a local file, the actual signature is `load_file(path, *, data_format: DataFormat, provenance: Provenance | None = None, encoding: str = "utf-8") -> Dataset`. JSON arrays require provenance; CSV ingestion requires explicit provenance. A reproducible example should never point to the absent original NASA response and pretend it is on disk.

### Read the NASA provenance if you have a future returned `Dataset`

`fetch_ps_dataset(...)` returns a structured `Dataset`; the adapter records query and checksum under `dataset.provenance.metadata["tap"]`. Its `DataSource`, `Provenance`, and returned records can be inspected without using the legacy `DatasetLoadResult` API. For future real data, preserve the exact response artifact if reprocessing the same snapshot matters; the adapter currently keeps only its checksum, not the response bytes.

## 9. Potential Scientific Research Directions

These are hypotheses for discussion, not approved tasks or targets. Any use would require a scientific question, source review, defined row/analysis unit, adequate dataset, and appropriate statistical design.

| Hypothesis | Examined fields that might help | Additional evidence/review needed | Why it is not automatically ML |
| --- | --- | --- | --- |
| Study whether reported orbital periods and radii vary together across a defined population. | `pl_orbper`, `pl_rade`, their uncertainty fields, `pl_refname`, `pl_name`, `hostname`, and possibly `default_flag`/`soltype` for documented filtering. | A larger defensibly sampled dataset, explicit population inclusion rules, repeated-solution policy, detection/completeness bias, unit and uncertainty treatment, and domain/statistical review. | Correlation does not establish causation. A descriptive plot or statistical model may answer the question more clearly than ML. |
| Explore planetary-system structure. | `hostname`, `pl_name`, `pl_refname` can help relate records; the examined 13 fields do not include a complete system inventory. | Add reviewed system-level fields and identity definitions; determine how multi-star systems, candidates, and repeated solutions are handled. | Grouping or counting may be a deterministic analysis. An ML cluster is not automatically a physically meaningful class. |
| Examine how uncertainty differs among published solutions. | `pl_orbpererr1/2`, `pl_radeerr1/2`, `pl_refname`, and values. | Reference papers, uncertainty conventions, selection effects, consistent definitions, and more than the non-representative 30-row slice. | This may be a measurement-method or meta-analysis question, not a prediction problem. |
| Study how multiple solutions change interpretation. | `pl_name`, `pl_refname`, `default_flag`, `soltype`, period/radius and their uncertainty/limit fields. | All relevant references/solutions, archived snapshots or publication chronology, verified category/limit codes, and a domain rule for comparing solutions. | Comparing published solutions can be direct evidence review or statistical analysis; no prediction target follows automatically. |

Across all directions, an observed correlation can arise from selection, measurement, or archive-inclusion effects. Correlation alone does not show that one property causes another. No direction here selects a target, feature set, model, or ML task.

## 10. Beginner Learning Checklist

- [ ] **Understand what an exoplanet is.** Explain that it is a planet beyond our Solar System, usually orbiting another star.
- [ ] **Understand planetary systems.** Recognize that a host may have multiple planets and may itself be a multiple-star system.
- [ ] **Understand the `ps` table.** Explain that rows represent planet parameter sets per reference and can include multiple solutions/candidates.
- [ ] **Understand all 13 examined fields.** Identify which fields are names, references, archive categories, measurements, uncertainties, or limit metadata.
- [ ] **Understand numeric versus categorical data.** Know that integer flags and string categories are not continuous measurements.
- [ ] **Understand missing values.** Keep `null`/`None`, blank text, zero, and any sentinel distinct; find the reason for missingness before filling values.
- [ ] **Understand measurement uncertainty and units.** Keep period in days, radius in Earth radii, and preserve separate upper/lower uncertainty fields.
- [ ] **Understand duplicate records and related solutions.** Distinguish exact row duplicates from multiple valid references for one planet or multiple planets around one host.
- [ ] **Understand dataset provenance.** Find the source, query, retrieval timestamp, checksum, version availability, and whether exact source bytes were retained.
- [ ] **Understand why this dataset is not yet ML-ready.** Name the missing approved task, target, features, snapshot/coverage evidence, baseline, split, metrics, and error thresholds.

## 11. What We Have Learned

- The 30-row exploration confirms that the adapter and JSON path can return a structured `Dataset` with numeric values and `null`s preserved.
- The examined columns mix identifiers, source references, archive categories, physical parameters, uncertainties, and encoded limit fields. Treating them all as ordinary numeric features would be a mistake.
- A planet/reference identity pair and zero exact duplicate rows in a 30-row sample do not prove archive-wide uniqueness or independence.
- The existing project can validate a declared structure and summarize quality, but domain meaning, units, source comparability, completeness, and scientific validity need separate review.
- The NASA response was not persisted. The report keeps its query, time, checksum, and sample-level summaries, but exact row-level re-analysis requires a future retrieval and would be a new snapshot.

## 12. What We Must Not Assume Yet

- Do not assume the first 30 alphabetically ordered rows represent all planets or systems.
- Do not assume one row is an independent planet, one host name is a complete system key, or one planet has only one solution.
- Do not assume `default_flag` is a confidence score, `soltype` is a ready-made ML label, or a numeric limit flag is a measurement.
- Do not assume missing values are zero, all `null`s have the same cause, or the sample's data types define NASA's complete database schema.
- Do not change units, signs, uncertainty definitions, candidate/default selection, or parameter values without a documented rule.
- Do not infer causation from correlation or scientific validity from a successful parse/schema check.
- Do not treat this exploration as approval for a research task, feature/target definition, dataset, or model. `docs/ARC08_ML_READINESS_DECISION.md` records **NO-GO** until team approvals and evidence exist.

## 13. References

- [NASA Science — What is an exoplanet?](https://science.nasa.gov/exoplanets/big-questions/)
- [NASA Science — Exoplanet facts, including confirmed and candidate discoveries](https://science.nasa.gov/exoplanets/facts/)
- [NASA Exoplanet Archive — About the Planetary Systems table](https://exoplanetarchive.ipac.caltech.edu/docs/planetarysystems_about.html)
- [NASA Exoplanet Archive — Planetary Systems and PSCompPars column definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html)
- [NASA Exoplanet Archive — FAQ: default parameters](https://exoplanetarchive.ipac.caltech.edu/docs/faq.html)
- [NASA Exoplanet Archive — Interactive Exoplanet Viewer: filtering null values](https://exoplanetarchive.ipac.caltech.edu/docs/ICEexohelp.html)
- Repository evidence: [`ARC08_EXOPLANET_DATASET_EVALUATION_REPORT.md`](ARC08_EXOPLANET_DATASET_EVALUATION_REPORT.md), [`ARC08_ML_READINESS_DECISION.md`](ARC08_ML_READINESS_DECISION.md), [`ML_REQUIREMENTS.md`](ML_REQUIREMENTS.md), [`EXOPLANET_ARCHIVE_ADAPTER.md`](EXOPLANET_ARCHIVE_ADAPTER.md), and the APIs in `src/quantum_space_agi/data/` and `src/quantum_space_agi/ml/`.
