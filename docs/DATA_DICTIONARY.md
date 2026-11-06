# Generic Data Dictionary

This dictionary defines the illustrative fields used by `data_template.csv` and `data_template.json`. All sample values are synthetic placeholders, not observations or mission facts.

| Field | Type | Required | Meaning | Constraints / units |
| --- | --- | --- | --- | --- |
| `record_id` | string | Yes | Stable identifier for one example record. | Unique within this example dataset; replace with source-appropriate key. |
| `observed_at` | string (date-time) | Yes | Time associated with the record. | ISO 8601 with timezone recommended; sample is explicitly illustrative. |
| `value` | number | Yes | Generic measured or calculated quantity. | No universal range; define per dataset. |
| `unit` | string | Yes | Unit for `value`. | Must be explicit; `unitless` only when justified. |
| `category` | string | No | Optional grouping or label. | Controlled vocabulary should be documented when used. |
| `notes` | string/null | No | Optional explanatory note. | Do not store secrets or sensitive personal information. |

The JSON template uses the same fields and represents one record. A dataset-level JSON envelope could be introduced later if the loader contract requires metadata and multiple records in one document.

The matching structural example schema is `schemas/sample_dataset.schema.json`. It checks only the declared field presence/types and does not define scientifically meaningful ranges or validate the date-time string format.
