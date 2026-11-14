# NASA Exoplanet Archive TAP Adapter

The source-specific adapter demonstrates read-only synchronous JSON ingestion
from the NASA Exoplanet Archive's Planetary Systems (`ps`) table. It returns a
`Dataset` with query and response provenance. It does not approve the archive
for ML training, define a prediction task, or establish scientific validity.

## Usage

```python
from quantum_space_agi.data.adapters.exoplanet_archive import fetch_ps_dataset

dataset = fetch_ps_dataset(
    ["pl_name", "pl_refname", "pl_orbper"],
    order_by=["pl_name", "pl_refname"],
    row_identity_fields=["pl_name", "pl_refname"],
    limit=5,
)

print(dataset.records)
print(dataset.provenance.metadata["tap"]["adql"])
print(dataset.provenance.metadata["tap"]["response_sha256"])
```

The adapter constructs a `SELECT TOP ... FROM ps ORDER BY ...` query. Columns,
ordering fields, and row-identity fields must be valid identifiers. Identity
fields must be selected and ordered, and their values must be present and
non-null. Duplicate identities are rejected within the returned query result;
this check does not establish global uniqueness. Finite JSON numbers, booleans,
and `null` values are preserved as Python numeric types, `bool`, and `None`.
Overflowed or otherwise non-finite numbers and absent selected fields are
rejected. No scientific type or unit conversion is inferred.

## Provenance and limits

The `Provenance` object stores `dataset_id`, source, UTC `retrieved_at` captured
after the response bytes are read (not a server-side publication timestamp), JSON
format, and a `metadata["tap"]` mapping containing the endpoint, table, exact
generated ADQL, output format, SHA-256 checksum, citation guidance, ordering,
row identity fields, and missing-value semantics. Unknown archive release and
DOI values are `None`. `Dataset.metadata["tap"]` contains table/column
description, unit, and type fields; these remain `None` because the adapter
does not fetch TAP_SCHEMA or archive column documentation.

The adapter uses Python's standard-library `urllib`, allows at most 100 rows,
rejects responses larger than 10 MiB, and uses a 20-second default timeout. It
does not retry automatically. These are adapter engineering limits, not NASA
service limits. It hashes the exact response bytes before UTF-8 decoding but
does not retain the original response after parsing; the checksum alone cannot
reconstruct that artifact.

Input validation raises `ValueError`. Network, HTTP, TAP query, content type,
JSON, record structure, and metadata failures use the source-specific
`ExoplanetArchiveError` subclasses in the adapter module. Error messages do
not include full server response bodies. Callers may apply
`quantum_space_agi.data.validate_dataset()` with an explicit schema; passing
structural validation is not scientific validation.

## Citation

The provenance records the archive's [citation guidance](https://exoplanetarchive.ipac.caltech.edu/docs/doi.html).
A data DOI is recorded only when verified for the returned data. Review the
archive's current table definitions, product documentation, and applicable
data-use terms before research use.
