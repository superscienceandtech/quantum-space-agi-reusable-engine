# ARC-08 NASA Limit-Code Semantics Investigation

**Investigation date:** 2026-11-09
**Table in scope:** NASA Exoplanet Archive `ps` (Planetary Systems)
**Status:** Evidence review only. This document does not approve eligibility filtering or authorize dataset extraction.

## Scope and method

This investigation checked the current official NASA Exoplanet Archive documentation for `pl_bmasselim` and `pl_radelim`, including the active Planetary Systems column definitions, the FAQ, and official documentation for related but differently named fields. The previously recorded ARC-08 live schema/query observations were inspected in [`ARC08_BASELINE_ML_TASK_SPEC.md`](ARC08_BASELINE_ML_TASK_SPEC.md). No NASA TAP request was made for this document, and no data rows were retrieved.

Evidence is separated into:

- **DOCUMENTED:** explicitly stated by NASA for the named field/table.
- **PRIOR LIVE OBSERVATION:** recorded from a prior query and not repeated here.
- **UNVERIFIED INTERPRETATION:** a possible reading unsupported by the evidence; not a policy.
- **UNRESOLVED:** the available sources do not establish the meaning.

## Findings by field

| Active `ps` field | Directly documented by NASA | Prior live metadata/observation recorded in repository | Code-value meanings | Null meaning |
| --- | --- | --- | --- | --- |
| `pl_bmasselim` | The active [Planetary Systems column definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html) list it as the limit column associated with `pl_bmasse`. The same page describes `pl_bmasse` as the best available planet mass estimate, in Earth masses, and describes `pl_bmassprov` separately. The page does not provide a value-to-meaning table for `pl_bmasselim`. | [`ARC08_BASELINE_ML_TASK_SPEC.md`](ARC08_BASELINE_ML_TASK_SPEC.md), “Field-semantics audit” and “Mechanically Verifiable NASA Field Semantics Review,” records the prior TAP schema type as `int` and a prior aggregate observation of `-1`, `0`, and `1` for the then-current candidate predicate. Prior TAP schema inspection did not expose a nullability attribute. These are scoped observations, not a definition of the codes. | `-1`: **UNRESOLVED**. `0`: **UNRESOLVED**. `1`: **UNRESOLVED**. Whether any other values are allowed is **UNRESOLVED**. No detection/equality, upper-limit, lower-limit, or unconstrained meaning is established for this active `ps` field by the sources inspected. | **UNRESOLVED.** NASA's active field page and the recorded TAP metadata do not define what a null represents, whether it means “not supplied,” “not applicable,” or another state. Do not interpret null as zero or as a detection. |
| `pl_radelim` | The active [Planetary Systems column definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html) list it as the limit column associated with `pl_rade`. The same page defines `pl_rade` as planet radius in Earth radii. The page does not provide a value-to-meaning table for `pl_radelim`. | [`ARC08_BASELINE_ML_TASK_SPEC.md`](ARC08_BASELINE_ML_TASK_SPEC.md), “Field-semantics audit” and “Mechanically Verifiable NASA Field Semantics Review,” records the prior TAP schema type as `int` and a prior aggregate observation of `-1`, `0`, and null for the then-current candidate predicate. Prior TAP schema inspection did not expose a nullability attribute. These are scoped observations, not a definition of the codes. | `-1`: **UNRESOLVED**. `0`: **UNRESOLVED**. `1`: **UNRESOLVED**; its presence in the observed `pl_bmasselim` values does not prove it is allowed or meaningful for this field. Whether any other values are allowed is **UNRESOLVED**. No detection/equality, upper-limit, lower-limit, or unconstrained meaning is established for this active `ps` field by the sources inspected. | **UNRESOLVED.** NASA's active field page and the recorded TAP metadata do not define what a null represents. Do not interpret null as zero, no limit, or a detection. |

## Similar names do not establish a mapping

NASA's [combined-table column guide](https://exoplanetarchive.ipac.caltech.edu/docs/API_combined_table_columns.html) explicitly gives `0 = '='`, `+1 = '>'`, and `-1 = '<'` for fields named `pl_masslim` and `pl_radlim`. Those names are not the active `ps` fields investigated here: they are not `pl_bmasselim` or `pl_radelim`. The same page separately lists `pl_bmasselim` alongside `pl_masse` and `pl_radelim` alongside `pl_rade`, without defining their values. The older guide therefore cannot be used as evidence that the active fields share the mappings. This investigation does not transfer those codes.

The active NASA page establishes association with a parameter's “Limit Column,” but association alone does not define the stored code vocabulary, direction, equality semantics, null semantics, or whether the value is authoritative for a particular row. Integer storage type and observed frequencies likewise establish no scientific meaning.

## Code-value interpretation matrix

| Field/value or state | Evidence status | Supported interpretation |
| --- | --- | --- |
| `pl_bmasselim = -1` | **UNRESOLVED** | Observed in a prior aggregate for the candidate predicate; NASA active `ps` documentation inspected does not define it. |
| `pl_bmasselim = 0` | **UNRESOLVED** | Observed in a prior aggregate; equality/detection meaning is not verified for this active field. |
| `pl_bmasselim = 1` | **UNRESOLVED** | Observed in a prior aggregate; upper/lower-limit meaning is not verified for this active field. |
| `pl_radelim = -1` | **UNRESOLVED** | Observed in a prior aggregate; NASA active `ps` documentation inspected does not define it. |
| `pl_radelim = 0` | **UNRESOLVED** | Observed in a prior aggregate; equality/detection meaning is not verified for this active field. |
| `pl_radelim = 1` | **UNRESOLVED** | Not listed in the prior candidate aggregate; absence from that aggregate does not establish an invalid or impossible code. Meaning is not documented in the active source inspected. |
| Either field is null | **UNRESOLVED** | Prior schema metadata did not provide nullability semantics; prior row aggregates are not an explanation of null. |
| Other integer values | **UNRESOLVED** | The active field documentation does not publish a complete allowed-value domain. |

No code is classified as “detection,” “upper limit,” “lower limit,” “unconstrained,” or “other” for the active `ps` fields based on the current evidence.

## Eligibility and extraction implications

Neither field can safely support eligibility filtering at this time. The flags and their nulls may be retained verbatim and counted in a future, separately approved extraction audit, but must not be interpreted or used to include/exclude records. Do not silently treat absent/null flags as zero, and do not derive a code mapping from correlations with values, uncertainty fields, or sample rows.

This unresolved interpretation is a blocker to declaring the candidate cohort scientifically eligible. It does not change the proposed `default_flag = 1 AND pl_bmassprov = 'Mass'` candidate predicate, and it does not authorize full dataset extraction. Any future filtering requires an authoritative active-`ps` mapping and scientific-owner approval of how that mapping relates to the proposed target/feature question.

## Questions requiring clarification

Ask NASA Exoplanet Archive support or consult an authoritative active `ps` data dictionary that explicitly answers:

1. What is the complete allowed value domain for `pl_bmasselim` and `pl_radelim` in the current `ps` table?
2. For each code, does it denote an equality/detection, upper limit, lower limit, another censoring state, or something else?
3. What does null mean for each field, and can null coexist with a reported parameter value?
4. Are these codes attached to the specific row's published parameter solution, and what rule should consumers use when the parameter value, uncertainty fields, and limit field appear inconsistent?
5. Do semantics differ between `ps`, `PSCompPars`, retired tables, or API representations, and where is the active `ps` mapping versioned?

The scientific reviewer must separately decide whether and how verified limit states affect inclusion in the exploratory mass–radius cohort. A verified code dictionary alone does not approve that scientific policy.

## Sources and access date

Official NASA Exoplanet Archive pages accessed 2026-11-09:

- [Planetary Systems and Planetary Systems Composite Parameters Data Column Definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html) — active field associations and parameter descriptions. The page was inspected at the rows for `pl_bmasse`/`pl_bmassprov`, `pl_rade`, and their limit columns; it does not define the active limit-code values.
- [NASA Exoplanet Archive FAQ](https://exoplanetarchive.ipac.caltech.edu/docs/faq.html) — default parameter sets and distinctions between `ps` and `PSCompPars`; no limit-code mapping for these fields was found.
- [Column Names Used in Exoplanet Table Data](https://exoplanetarchive.ipac.caltech.edu/docs/API_combined_table_columns.html) — documents mappings for differently named `pl_masslim` and `pl_radlim`, deliberately not applied to the active fields here.

Repository evidence inspected: [`ARC08_BASELINE_ML_TASK_SPEC.md`](ARC08_BASELINE_ML_TASK_SPEC.md), including its recorded TAP schema metadata and prior aggregate observations. No new TAP/schema query, data retrieval, or row-level inspection was performed for this investigation.
