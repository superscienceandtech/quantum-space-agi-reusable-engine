# ARC-08 Educational Mission Evaluator Design

**Status:** Design record for the implemented V1 educational configuration and evaluator. This document does not implement the code. No real mission simulator or scientific score rule is provided.

This proposal defines a small, self-contained educational resource-selection exercise that ARC-08 could own. It is not real orbital mechanics, flight-grade planning, NASA scoring, or a replacement for ARC-04 scientific computing or ARC-05 simulation.

## 1. Verified Repository Facts

- **VERIFIED:** The project describes itself as a reusable engineering foundation for future space-mission design. It is not a mission-ready flight system or authoritative source of scientific data ([`README.md`](../README.md)).
- **VERIFIED:** The repository contains an educational mission configuration, immutable scenario catalog, deterministic evaluator, and outcome type ([`mission_configuration.py`](../src/quantum_space_agi/ml/mission_configuration.py), [`mission_scenarios.py`](../src/quantum_space_agi/ml/mission_scenarios.py), [`mission_evaluator.py`](../src/quantum_space_agi/ml/mission_evaluator.py)). These are not orbital mechanics or a real mission simulator. No simulation execution interface or physical mission score is established here.
- **VERIFIED:** ARC-03 provides `Dataset`, `Provenance`, `DataSchema`, `validate_dataset()`, and `analyze_quality()`. Structured schema validation checks declared presence, nullability, and exact Python types; it does not establish scientific validity ([`DATA_ARCHITECTURE.md`](DATA_ARCHITECTURE.md), [`data/models.py`](../src/quantum_space_agi/data/models.py), [`data/schemas.py`](../src/quantum_space_agi/data/schemas.py), [`data/quality.py`](../src/quantum_space_agi/data/quality.py)).
- **VERIFIED:** ARC-08 provides deterministic scalar preprocessing and separate offline data-engineering utilities, including identity diagnostics and a deterministic host-based split utility. These do not provide a mission simulator, educational-evaluator dataset generator, scientific-task predictor, or model-training API ([`ml/preprocessing.py`](../src/quantum_space_agi/ml/preprocessing.py), [`ml/identity_diagnostics.py`](../src/quantum_space_agi/ml/identity_diagnostics.py), [`ml/group_splitter.py`](../src/quantum_space_agi/ml/group_splitter.py)).
- **VERIFIED:** `Dataset` copies its top-level record mappings but does not deep-copy nested lists and dictionaries. Consumers that retain mutable configuration data must copy it themselves or treat it as immutable ([`data/models.py`](../src/quantum_space_agi/data/models.py)).
- **VERIFIED:** `Provenance` requires `dataset_id`, `source`, timezone-aware `retrieved_at`, and `data_format`; it can also carry a dataset version, transformations, and metadata ([`data/provenance.py`](../src/quantum_space_agi/data/provenance.py)).
- **VERIFIED:** The project currently declares no runtime dependencies in `pyproject.toml`.

## 2. Proposed Educational Scenario

**PROPOSED:** A resource-selection exercise. A learner chooses a set of fictional payload cards for one preconfigured educational mission. Each card has project-authored educational value points and abstract budget, mass, and power costs. The evaluator totals those values, checks fixed limits, and reports feasibility and an optional score.

This is small enough to implement and test deterministically. It demonstrates configuration validation, resource constraints, trade-offs, and structured outcomes without claiming to model a spacecraft, trajectory, orbit, propulsion, or physical mission success.

### Illustrative version-one scenario catalog

The following values are **illustrative project-authored constants**, not repository facts, measured properties, or NASA rules. All resource quantities are abstract game units, not dollars, kilograms, watts, or engineering limits.

| Payload ID | Educational value points | Budget units | Mass units | Power units |
| --- | ---: | ---: | ---: | ---: |
| `imager` | 5 | 3 | 2 | 2 |
| `spectrometer` | 8 | 5 | 3 | 3 |
| `relay` | 3 | 2 | 1 | 1 |

| Scenario ID | Budget limit | Mass limit | Power limit | Payload-slot limit |
| --- | ---: | ---: | ---: | ---: |
| `resource-selection-demo-v1` | 7 | 4 | 4 | 2 |

For example, selecting `spectrometer` and `relay` uses 7 budget units, 4 mass units, and 4 power units, occupies two slots, and is feasible under this proposed catalog. Its optional educational score would be 11 value points. This example only demonstrates the arithmetic of the proposed game rule.

## 3. Proposed Mission Configuration

For this minimal scenario, a configuration means the complete selected payload set under the fixed scenario identified by `scenario_id`. No other spacecraft or mission fields are implied.

| Field | Proposed type | Required | Validation and availability |
| --- | --- | --- | --- |
| `scenario_id` | non-empty string | Yes | Must identify a known, immutable scenario catalog and its limits. Known before evaluation. V1 proposes only `resource-selection-demo-v1`. |
| `selected_payload_ids` | non-empty JSON-compatible list of strings | Yes | Every ID must exist in that scenario's catalog and IDs must be unique. Normalize by sorting IDs in ascending lexical order before evaluation or serialization. The selected count is checked as a resource constraint during evaluation so an over-limit configuration can return a slot violation. Known before evaluation. |

**PROPOSED JSON configuration shape:** A configuration is a JSON object with a string `scenario_id` and a JSON array (Python `list`) of string `selected_payload_ids`, for example `{"scenario_id": "resource-selection-demo-v1", "selected_payload_ids": ["imager", "relay"]}`. The list must be non-empty. Canonical normalization validates the supplied list without coercion, rejects duplicate or unknown IDs, then sorts the IDs in ascending lexical order. Thus payload input order has no meaning; `selected_payload_ids` in outcomes and generated records uses this normalized list.

The immutable Python configuration model accepts that list at construction and stores the normalized IDs as a tuple, preventing later mutation while preserving the JSON list representation at the input boundary.

**PROPOSED validation rules:** Reject unknown scenario or payload IDs, duplicate payload IDs, an empty selection, and any input with the wrong container or scalar types. These are invalid configurations and must be rejected without producing an outcome. A configuration with known unique payload IDs is valid even if its selected count or summed resources exceed limits; it produces a normal infeasible outcome with violations. Do not coerce values. In particular, booleans are not accepted as numeric configuration values; V1 has no caller-supplied numeric resource values.

Catalog costs and values are evaluator-owned scenario data, not learner-supplied fields. This prevents a configuration from changing its own scoring or limits. Field names and types above are a new proposed ARC-08 contract, not existing simulator fields.

## 4. Proposed Evaluation Rules

The evaluator is a pure deterministic function of the configuration and a versioned scenario catalog. It uses integer arithmetic only.

1. Resolve the selected IDs against the fixed catalog for `scenario_id`.
2. Sum budget, mass, power, payload count, and educational value points.
3. Emit one violation for each total strictly greater than its corresponding limit. Equality with a limit is feasible.
4. `feasible` is true only when there are no violations.
5. If feasible, `educational_score` is the sum of the selected cards' fictional, project-authored utility/value points. It measures only that arithmetic total; it does not measure educational learning outcomes, scientific quality, or real mission performance. If infeasible, `educational_score` is `None`; feasibility and violations remain available separately.
6. Return violations in a stable documented order: budget, mass, power, payload slots.

These rules are **PROPOSED educational game rules**. The point values and resource limits are invented for this project exercise and must not be attributed to NASA or interpreted as physical mission constraints. There is no risk model, uncertainty, orbital calculation, or external data lookup.

## 5. Proposed Mission Outcome Contract

The following conceptual output is a proposal, not a current repository type or approved Python API.

| Output field | Proposed type | Meaning and limitation |
| --- | --- | --- |
| `selected_payload_ids` | list of strings | Canonically sorted payload IDs for the evaluated configuration. This traces the outcome to its normalized input; equivalent input orderings yield the same list. |
| `evaluator_version` | string | Identifies the evaluator implementation and its validation, outcome, and scoring semantics. It is distinct from the scenario and dataset/schema versions. |
| `scenario_id` | string | Identifies the immutable scenario catalog and limits applied to this result; it is grouping metadata, not a model feature by default. It is distinct from the evaluator version. |
| `feasible` | boolean | True when all declared abstract resource limits pass. It means only feasible under this educational rule set. |
| `violations` | sequence of violation records | Zero or more records with a stable code, observed integer total, and integer limit. They describe only the resource checks above. |
| `resource_totals` | record of integer totals | Budget units, mass units, power units, and payload slots consumed by this configuration. |
| `educational_score` | integer or null | Sum of fictional project-authored utility/value points for feasible configurations; null for infeasible configurations. It does not measure learning outcomes, scientific quality, or real mission performance, and is not an approved scientific target. |

The result intentionally separates feasibility from violations and score. A future dataset must not silently replace `None` with zero or treat an infeasible configuration as a zero-score successful mission.

## 6. Determinism and Versioning

**PROPOSED:** V1 requires no randomness and accepts no seed. The same valid configuration, `scenario_id`, and evaluator version must always return the same output. Normalize `selected_payload_ids` into ascending lexical order before evaluation, and use that same list in outcomes and generated records. Violations retain their documented order. Before implementation, finalize the exact canonical JSON serialization policy, including field order, encoding, null representation, and stable output representation. Equivalent configurations with different input list order must produce equivalent outputs and dataset records under that policy.

**V1 canonical JSON serialization policy:** Encode serialized JSON as UTF-8 without a byte-order mark. Preserve non-ASCII Unicode characters rather than escaping them (`ensure_ascii=False`); reject strings that cannot be encoded as strict UTF-8. Emit compact JSON with no insignificant whitespace and no trailing newline. For configuration objects, emit fields in this exact order: `scenario_id`, then `selected_payload_ids`; future outcome and dataset-record objects must use the exact field order defined by their approved contracts. Serialize null as `null`, booleans as lowercase `true`/`false`, and integers as base-10 digits with no leading zeros (except `0`) and a leading minus sign when negative. V1 does not serialize floating-point numbers. Normalize `selected_payload_ids` to ascending lexical order before serialization. Reject unsupported values including floats, NaN/infinities, tuples, sets, bytes, custom objects, and objects with non-string keys; only null, booleans, integers, strings, lists, and string-keyed objects are permitted where their contract allows them. Use Python's standard-library JSON support with explicit options; do not add a serialization dependency.

Use an explicit evaluator version such as `educational-mission-evaluator/0.1.0` in results and provenance. It identifies evaluator rules and output semantics; increment it when an evaluator rule, validation semantic, or output semantic changes. `scenario_id` identifies which immutable scenario catalog and limits were applied; a scenario catalog change must use a new `scenario_id` and does not by itself require an evaluator-version increment. A future dataset version identifies a generated dataset artifact/release, while a schema version identifies its record contract. These are separate identifiers and must not be substituted for one another; their formats and change policies require separate review.

## 7. Future ARC-03 Dataset Integration

**PROPOSED, BLOCKED:** Each generated record should retain the pre-evaluation configuration and its separate result. A flattened JSON-compatible record could contain `scenario_id`, canonically sorted list-valued `selected_payload_ids`, `evaluator_version`, `feasible`, `violation_codes`, resource totals, and nullable `educational_score`. Equivalent configurations must serialize these fields identically. Do not place post-evaluation fields among pre-evaluation features. ARC-03 Dataset integration remains blocked until the meaning of required `Provenance.retrieved_at` and a compatible mapping for locally generated records are verified and approved; do not construct the ARC-03 Dataset before that is resolved.

Use ARC-03 `Dataset` and `Provenance`; do not add a parallel dataset/provenance implementation. Candidate provenance information includes:

- Dataset identity and a reviewed artifact/schema version.
- A `DataSource` identifying the ARC-08 educational evaluator.
- Evaluator and scenario-catalog versions.
- Dataset generation timestamp, code revision, and record-generation procedure.
- Any source configuration or generation parameters needed to reproduce the records.
- A checksum of a retained serialized artifact, if an artifact is written.
- A transformation entry describing conversion from evaluator results to dataset records.

`Provenance.retrieved_at` is required and named for retrieval, while this source would generate records locally. Its semantics and a compatible mapping for locally generated records are unresolved. Do not assign `generated_at` to `retrieved_at`, invent a retrieval event, or construct a `Provenance`/`Dataset` until this mapping is verified. Record no seed for V1; do not invent source version or external provenance.

The current `DataSchema` can check exact top-level Python types, presence, and nullability. It does not validate item types inside nested lists, numeric ranges, or the evaluator's arithmetic rules. Those must be checked by the evaluator and its focused tests; ARC-03 behavior should remain unchanged.

## 8. Testing Strategy

When implementation is separately approved, add focused tests for:

- Valid minimal configuration and each valid payload ID.
- Unknown scenario and payload IDs; empty and duplicate selections; wrong scalar/container types; boolean/non-string identifiers.
- Every resource limit exactly met, then exceeded by one unit; each violation independently and multiple simultaneous violations.
- Feasibility matching the empty/non-empty violation list.
- Score equals the catalog value sum when feasible and is `None` when infeasible.
- Canonical payload ordering: reordered equivalent input lists normalize to the same `selected_payload_ids`, outcome serialization, and generated dataset record.
- Repeated evaluation of the same input and version produces equal results and does not mutate the input.
- A scenario catalog change uses a new `scenario_id`; an evaluator rule, validation semantic, or output semantic change increments `evaluator_version`. A catalog-only change does not by itself require an evaluator-version increment.
- Canonical JSON serialization matches the policy finalized before implementation, including field order, encoding, null representation, and stable output representation.
- ARC-03 integration preserves configuration/outcome distinctions, provenance, and source data; schema and quality reports are exercised without claiming scientific validation.

No tests or source code are added in this design phase.

## 9. Future ML Suitability and Limitations

Generated examples could later test ARC-08 dataset adaptation, schema validation, provenance, leakage controls, and end-to-end ML plumbing. They are synthetic educational examples, not NASA or scientific training data.

The proposed score is computed directly from a small fixed catalog. A model trained on these results would learn to imitate that deterministic scoring rule; direct evaluation is simpler, exact, and easier to explain. V1 has one scenario family and only seven non-empty payload combinations. It cannot support credible evaluation of generalization to held-out scenario families, and random splitting of these combinations does not solve that limitation. ML training and performance claims remain **NO-GO** until independently designed scenario families and an appropriate evaluation protocol exist. Scenario IDs must not be treated as model features merely because they are used for grouping.

**Scientific limitations:** This evaluator does not model orbital mechanics, spacecraft dynamics, communications, reliability, uncertainty, environments, costs in real currency, or mission success. The abstract resource limits and value points are pedagogical choices only. Passing its checks is not engineering validation, mission feasibility, NASA endorsement, or evidence of prediction quality.

## 10. Decisions Requiring Future Review

- Approve the resource-selection exercise and its ARC-08 ownership boundary without modifying ARC-04/05.
- Review the proposed payload catalog, abstract values, resource limits, and whether an optional score should exist at all.
- Decide whether the score is useful for the educational product or whether explicit feasibility/constraint feedback is sufficient.
- Approve the configuration and output field names/types, versioning policy, and violation semantics.
- Resolve the semantics of ARC-03's required `Provenance.retrieved_at` for locally generated records and verify an explicitly compatible mapping before ARC-03 Dataset integration; do not infer a retrieval event or substitute `generated_at`.
- Define how future scenario families are generated and grouped if ML evaluation is later considered.
- Review all scientific/educational claims and keep the no-flight-grade/no-NASA-scoring limitations visible.

Until those decisions are reviewed, this remains a design proposal. It does not change the NO-GO status for ML implementation or training in [`ARC08_ML_READINESS_DECISION.md`](ARC08_ML_READINESS_DECISION.md).
