# ARC-08 NASA Exoplanet Archive Open Data Reference

**Checked:** 2026-11-10
**Status:** Public-documentation reference for engineering familiarization. This is not an approval to acquire, retain, redistribute, or scientifically use archive data.

This document records public NASA Exoplanet Archive documentation and compares it with the repository's current interfaces. “Documented” below means stated by the linked NASA page; “repository behavior” means observed in this checkout's code. Neither category is scientific approval or acquisition authorization.

## Archive and table identity

NASA describes the Exoplanet Archive as a repository of exoplanet data and services for research. Its Planetary Systems (`ps`) table contains archived parameter sets as rows by planet and reference, with a self-contained set of planet, stellar, and system parameters for each reference. `PSCompPars` instead provides one row per planet and can fill gaps from multiple parameter sets, so NASA cautions that it is not necessarily self-consistent. These are different table contracts and must not be treated as interchangeable.

The NASA FAQ says archive data are added generally weekly, with occasional skipped weeks. It also explains that the default parameter set is selected from a single publication for internal consistency and a balance of completeness and precision; a default is not necessarily the most precise available result. NASA describes filtering `ps` by the default flag as an expeditious way to select one row per planet for general use. That description is not a database uniqueness guarantee for arbitrary predicates or future archive states.

## Public TAP documentation

NASA documents TAP access through `https://exoplanetarchive.ipac.caltech.edu/TAP`; the synchronous endpoint used by the adapter is `https://exoplanetarchive.ipac.caltech.edu/TAP/sync`. Its guide documents query requests with a `query` parameter, optional output `format`, synchronous and asynchronous execution, and VOTable as the default output. It lists VOTable, IPAC, JSON, TSV, and CSV formats. The guide recommends TAP clients for large retrievals and describes asynchronous execution as a background job whose state can be checked.

NASA also documents `TAP_SCHEMA` as service metadata. The existing ARC-08 adapter does not query `TAP_SCHEMA`, use asynchronous UWS jobs, inspect server capabilities, or paginate. This document does not verify the live service's current result cap or establish that an arbitrarily high row request is complete. The official guide's general format and async descriptions do not prove a full-table extraction contract.

## Field definitions relevant to the proposed task

The column-definition page documents descriptions and units. It does not establish field nullability, uniqueness constraints, a complete live value domain, or scientific eligibility. Exact limit-code meanings remain unresolved in the project's separate [limit-code investigation](ARC08_NASA_LIMIT_CODE_SEMANTICS.md).

| Field | NASA-documented description | Eligibility/API interpretation boundary |
| --- | --- | --- |
| `pl_name` | Planet name most commonly used in literature. | A display/identity label; no uniqueness guarantee or alias-normalization rule is documented here. |
| `hostname` | Stellar name most commonly used in literature. | A host grouping candidate; no uniqueness or canonicalization guarantee is documented here. |
| `pl_refname` | Publication reference used for the given planet parameter set. | Preserve the supplied reference string; no canonical reference key is established here. |
| `default_flag` | Boolean-like flag for whether the parameter set is selected as default (`1=yes`, `0=no`). | Describes NASA's default selection. It does not by itself approve a cohort. |
| `pl_bmassprov` | Provenance options for best mass: `Mass`, `M*sin(i)/sin(i)`, `M*sini`. | Exact documented option spellings are retained. Restricting to `Mass` remains a proposed task policy, not approved scientific eligibility. |
| `pl_bmasse` | Best available planet mass or projected-mass quantity, in Earth masses, with documented preference order among mass meanings. | The value alone can represent different mass semantics; consult `pl_bmassprov`. Unit and description do not approve use as a target. |
| `pl_rade` | Planet radius in Earth radii. | Unit/description only; no positive-value threshold or task suitability follows from it. |
| `pl_bmasseerr1`, `pl_bmasseerr2` | Associated positive/upper and negative/lower uncertainty columns for the mass parameter. | NASA's column table labels the upper/lower association; it does not establish observed numeric signs, this project's missingness policy, or uncertainty use. |
| `pl_radeerr1`, `pl_radeerr2` | Associated positive/upper and negative/lower uncertainty columns for radius. | Same boundary: preserve raw values; no filter, transformation, or weighting is approved. |
| `pl_bmasselim`, `pl_radelim` | Limit columns associated with the corresponding mass and radius values. | Active `ps` code meanings and null semantics are unresolved. Do not map codes or filter by them. |
| `pl_controv_flag` | Indicates whether confirmation status has been questioned in published literature (`1=yes`, `0=no`). | Does not determine inclusion policy or null interpretation. |
| `soltype` | Disposition of the planet according to the given parameter set. The FAQ names source classes “Published Confirmed,” “Kepler Project Candidate,” and “TESS Project Candidate.” | These descriptions do not establish an exhaustive set of exact stored tokens or an eligibility rule. Preserve and audit raw values. |

The NASA interactive-viewer help says blank table cells indicate that no value has been entered for that parameter and that zero is not null. This is a documented interactive-table convention, not a complete statement of TAP/JSON wire encoding. The adapter preserves JSON `null` as Python `None`, rejects absent selected fields, and rejects non-finite JSON constants. The underlying service's encoding for all forms of missing data remains **not established** here.

## Current repository adapter contract

`quantum_space_agi.data.adapters.exoplanet_archive.fetch_ps_dataset(columns, *, order_by, row_identity_fields, limit, timeout=20.0)` is an opt-in network adapter. This reference does not call it.

- It sends a synchronous GET request to the fixed `/TAP/sync` endpoint with `query=<generated SQL>` and `format=json`, and an `Accept: application/json` header.
- The query selects caller-named columns from `ps`, orders by caller-supplied fields, and uses SQL `TOP`. Column/order/identity identifiers must match the module's identifier pattern. Identity fields must be selected and included in ordering.
- `limit` is a required exact integer from 1 through the local `MAX_ROWS = 100`; booleans are rejected. Timeout defaults to 20 seconds and must be positive and finite. The adapter reads at most 10 MiB plus one byte to detect its own response-size cap.
- The adapter accepts successful 2xx HTTP responses with JSON content type; parses strict UTF-8 JSON; requires an array of object records and all selected columns; rejects non-finite values, null/missing identity values, duplicate requested row identities, recognizable TAP errors, oversized bodies, and malformed responses. It does not coerce scalar values or apply scientific filters.
- It records a UTC retrieval time, endpoint/table, exact generated query, requested format, SHA-256 of the exact response bytes, ordering/identity declarations, and adapter-side missing-value handling in ARC-03 provenance. The digest is calculated but raw response bytes are not retained by this adapter. Column metadata fields remain unset.
- It has no query filter argument, pagination, retry, async job handling, `MAXREC` parameter, raw-byte snapshot writing, live schema lookup, or completeness proof. `TOP` and the adapter caps are local bounding behavior; they are not evidence of a NASA service-wide limit or a complete result. A successful HTTP status and parsed JSON do not establish that a broader requested population was fully retrieved.
- Separate requests (including count, metadata, and row queries) do not establish a shared transactional archive snapshot. No snapshot-isolation guarantee is asserted.

Use the offline snapshot writer/verifier and verified-ingestion path when working with already supplied bytes. A checksum can identify bytes only when those bytes are retained and independently checked; it does not prove source authenticity, scientific validity, NASA authorization, or snapshot consistency.

## Citation, reuse, and permission boundary

NASA's acknowledgement guidance requests its standard archive acknowledgment in published material using archive services, asks users of data from specific literature references to acknowledge those references, and directs users to cite Christiansen et al. (2025), which replaces Akeson et al. (2013). NASA's FAQ says published archive data can be used for additional research with appropriate acknowledgements. The DOI page describes archive DOIs as persistent links to data and services.

These pages provide citation guidance and a general research-use statement. They do **not**, as reviewed here, establish project-specific authorization, a blanket license, raw snapshot retention duration, or permission for public redistribution. Silence is not permission. Those questions remain subject to authoritative terms and project stakeholder review before acquisition, retention, or release.

## Status boundary

Public documentation familiarization and offline API engineering may proceed independently. Mechanical validation is not scientific eligibility. This reference does not approve the mass-radius task, candidate cohort, exclusion policies, identities, split strategy, metric thresholds, or claims. The repository's acquisition readiness remains `NOT_READY`; no NASA dataset has been acquired or evaluated by this documentation work.

## NASA sources checked on 2026-11-10

1. NASA Exoplanet Archive, [Overview and Holdings](https://exoplanetarchive.ipac.caltech.edu/docs/intro.html) — archive purpose and programmatic access overview.
2. NASA Exoplanet Archive, [Planetary Systems and Planetary Systems Composite Parameters Data Column Definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html) — table distinction, field descriptions, units, flags, uncertainties, and associated limit columns. Page reports last updated 4 June 2026.
3. NASA Exoplanet Archive, [Retrieving Exoplanet Archive Data With Table Access Protocol](https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html) — TAP endpoint, request convention, sync/async descriptions, and formats.
4. NASA Exoplanet Archive, [Frequently Asked Questions](https://exoplanetarchive.ipac.caltech.edu/docs/faq.html) — default parameter selection, table distinction, update cadence, and general reuse-with-acknowledgement statement. Page reports last updated 1 July 2026.
5. NASA Exoplanet Archive, [Using the Interactive Exoplanet Viewer](https://exoplanetarchive.ipac.caltech.edu/docs/ICEexohelp.html) — interactive-table blank/null convention; not asserted as TAP wire encoding.
6. NASA Exoplanet Archive, [Acknowledging the NASA Exoplanet Archive in Publications](https://exoplanetarchive.ipac.caltech.edu/docs/acknowledge.html) — publication acknowledgment and citation guidance. Page reports last updated 13 August 2025.
7. NASA Exoplanet Archive, [Citing the NASA Exoplanet Archive With Digital Object Identifiers](https://exoplanetarchive.ipac.caltech.edu/docs/doi.html) — DOI purpose and archive citation options.

The public documentation was checked on the date above. During this review, direct page opens for the TAP guide and column-definition page returned HTTP 503 in the research browser; the specific page content used for those claims was available from the official NASA pages' indexed content. Recheck those pages before implementing new acquisition behavior. No TAP query, metadata endpoint request, dataset request, or archive data download was made. Service-side output limits, wire-level null behavior for every format, active limit-code values, and retention/redistribution permissions remain unverified or unresolved as stated above.
