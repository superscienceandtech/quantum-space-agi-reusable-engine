# ARC-08 Provenance, Snapshot, Reproducibility, and Approval Gate

**Status: DOCUMENTATION REVIEW — NO EXTRACTION OR MODEL EVALUATION APPROVED.** This gate consolidates the current ARC-08 evidence and proposed requirements. It does not approve a scientific task, eligibility policy, NASA request, artifact retention, redistribution, model evaluation, or training.

**Scope:** proposed exploratory NASA Exoplanet Archive `ps` mass–radius analysis (`pl_bmasse`, candidate `pl_bmassprov = 'Mass'`, candidate `pl_rade`, provisional `default_flag = 1`). The 2,211 count is an earlier candidate-predicate observation, not a final eligible count or an immutable snapshot.

## 1. Evidence and provenance

### Existing evidence

- **DOCUMENTED in repository:** the current ARC-03 adapter targets `https://exoplanetarchive.ipac.caltech.edu/TAP/sync`, requests bounded JSON from `ps`, records ADQL, retrieval time, and a SHA-256 digest of response bytes, and does not retain the response bytes. Its request limit is 1–100 rows; it has no filter or pagination argument ([task specification](ARC08_BASELINE_ML_TASK_SPEC.md), adapter source [`exoplanet_archive.py`](../src/quantum_space_agi/data/adapters/exoplanet_archive.py)).
- **PRIOR LIVE OBSERVATIONS, not a retained extraction:** the task specification records specific schema and aggregate TAP request times, HTTP status, VOTable status, selected headers/request IDs, and query strings. The query response bodies were inspected but not retained as a complete snapshot. The prior bounded response is also not an immutable full-candidate artifact. These observations do not provide the raw `ps` population or its historical state ([task specification, live verification section](ARC08_BASELINE_ML_TASK_SPEC.md)).
- **IMPLEMENTED OFFLINE, synthetic tests only:** ARC-08 has a VOTable structure/completeness validator, snapshot artifact writer/verifier, verified-byte ingestion, mechanical dataset validation with an exclusion ledger, identity diagnostics, exact-host split tooling, and versioned evidence-report serialization/persistence. These components do not acquire NASA data or establish scientific eligibility.
- **PROPOSED and not implemented:** full-scale NASA asynchronous TAP extraction and acceptance of a complete candidate response remain described in the extraction design. Service limits and full-scale completeness remain to be verified; no NASA extraction is approved for use.
- **UNRESOLVED:** no repository evidence establishes that separate schema, count, and data requests share a transaction, archive version, or point-in-time snapshot.

### Required provenance for a future extraction attempt

The proposed manifest should preserve, without claiming values that were not observed:

- Archive identity, TAP endpoint, table name, protocol mode, and exact ADQL bytes/string submitted.
- Exact request parameters: request type, language, output format, selected columns, ordering, `MAXREC` if sent, timeout/retry configuration, and any client headers relevant to interpretation. Exclude credentials and secrets.
- Attempt/job identifiers and result URL when returned; submission, each observed UWS phase with timestamp, completion, result-download start/end, and final validation timestamps, all timezone-aware and preferably UTC.
- HTTP status, response content type, safe relevant response headers (including date or service request ID when present), and transport completion/error details.
- Exact raw result response bytes retained in an approved durable location; byte length and lowercase SHA-256 over those exact bytes, recomputed independently after write and on later read.
- Parsed row count, VOTable query-status sequence, required columns/schema result, validator/parser name and version, and whether any representation has been decoded or merely structurally inspected.
- Exact schema metadata artifact/query, capture timestamp, byte length/checksum, and schema interpretation/version. Missing metadata must be explicitly marked unavailable; it must not be inferred from a data sample.
- Extraction query/policy version, eligibility-policy version, schema version, feature and target definitions, ordered decision/reason taxonomy, per-row exclusion/pending-review ledger reference and digest, and aggregate counts tied to this snapshot.
- Code revision and dirty-tree/source artifact identity, operating system, Python version, client/parser/validator versions, relevant dependency lock/version information, and manifest schema version.
- For an approved evaluation only: immutable row/group split assignments, grouping keys/policy version, seed and random-generator details if randomness is actually used, fitted preprocessing/model configuration, metric definitions/configuration, and result artifact hashes.

### No invented provenance values

The repository currently has no accepted NASA candidate extraction artifact, candidate-specific manifest/checksum/byte length, parser run on a NASA candidate snapshot, candidate row-level exclusion ledger, or NASA split assignment. Offline artifact, ingestion, ledger, identity, split-feasibility, and evidence-report APIs exist and have synthetic test coverage; those synthetic outputs are not candidate data or research evidence. Do not fill candidate fields from the prior count or tiny service tests. An attempt may record a field as `not_available` with a reason, or `not_applicable` with a reason; if the field is required for artifact acceptance, the attempt remains `blocked`/`incomplete` until evidence exists. A checksum without retained bytes identifies bytes only if they still exist; it cannot reconstruct them.

## 2. Snapshot consistency

The prior candidate count, schema query, and a future row extraction are separate requests made at separate times. NASA's FAQ, as cited in the project evidence, says archive content is updated periodically; even matching query predicates or row counts do not show that separate requests observed identical database state. A count can match after rows have changed, and a schema response can describe a different service state than the data response. The prior queries were not executed as one transaction and the repository has no evidence of an archive snapshot token, version pin, or repeatable-read mechanism for them.

**Do not claim snapshot isolation.** The project evidence does not establish that NASA TAP offers transactionally consistent multi-request snapshots. A matching independent `COUNT(*)`, matching schema, timestamps, checksums, or a completed UWS job are useful diagnostics/provenance, but do not by themselves prove that count/schema/data queries saw one common state.

Evidence sufficient to make a snapshot-consistency claim would require authoritative NASA documentation or service behavior establishing a stable release/as-of identifier or transaction/snapshot token that is attached to and honored by all relevant requests, plus recorded proof that the same identifier governed the schema, count, and data artifacts. If that capability is unavailable, describe the artifact as the exact response from one query at its recorded retrieval time—not as a transactional archive snapshot. Any separate count remains a planning/cross-check observation with its time-of-query limitation.

## 3. Proposed reproducibility manifest

**PROPOSED:** a versioned JSON manifest alongside an immutable raw artifact, as designed in [`ARC08_BASELINE_ML_EXTRACTION_DESIGN.md`](ARC08_BASELINE_ML_EXTRACTION_DESIGN.md). “Mandatory” below means mandatory for a future artifact to be accepted; it does not mean the value exists today.

| Manifest group/key | Requirement status | Current evidence/status |
| --- | --- | --- |
| `manifest_schema_version`, attempt state, snapshot/artifact identifier | Mandatory | Offline snapshot and evidence-report manifests exist for caller-supplied bytes; a manifest for a NASA extraction attempt and its identifier format remain unimplemented/unreviewed. |
| Archive name, TAP endpoint, table (`ps`), exact query bytes/text and query digest | Mandatory | Endpoint/table are documented; extraction ADQL is proposed, not executed. No extraction query digest exists. |
| Request parameters, selected columns/order, format, protocol, `MAXREC`, client configuration | Mandatory | Proposed async VOTable design; actual full-extraction parameters are unavailable. Record omitted parameters as omitted/unknown, never assume defaults. |
| Submission/job/result timestamps, UTC offset, HTTP metadata, job ID/phase history/result URL | Mandatory when provided by service; explicitly record unavailable fields | Small prior checks have timestamps/status identifiers in task spec. No candidate extraction job exists. |
| Exact raw response path, byte length, SHA-256, transfer completion, checksum verification result | Mandatory | Offline writer/verifier can persist and verify supplied bytes. No NASA candidate response is retained and no storage/retention approval exists. |
| Schema artifact/query, capture time, checksum, types/units/nullability metadata actually returned | Mandatory for accepted parsing; each absent attribute must be marked unavailable | Some prior live schema facts are recorded; they do not form a retained schema snapshot for the future data response. Nullability was not exposed in the recorded metadata. |
| Parser, VOTable validator, schema validator, versions, validation status and query-status sequence | Mandatory | Offline VOTable validation and ingestion code exist; neither has been run on a retained NASA candidate response. Parser acceptance/version for such a run must be recorded. |
| Parsed row count, required columns, completeness/overflow evidence, effective service limits | Mandatory for artifact acceptance | No full extraction values. Effective large-response/byte limits and full-scale completeness remain blockers in extraction design. |
| Extraction, eligibility, schema, feature/target contract versions | Mandatory before scientific rows are classified | Policy documents are proposals and blockers remain; no approved policy/schema version is evidenced. |
| Exclusion/pending-review ledger, reason taxonomy/version, aggregate row counts | Mandatory for future cohort artifact | Proposed in extraction/task specifications; no row-level ledger or eligible count exists. |
| Code commit, dirty-tree/source artifact digest, runtime and dependency versions | Mandatory for reproducible parser/analysis run | Repository HEAD is `d236854` per current inspected status, but untracked/modified ARC-08 work is also present. A commit hash alone would not identify the current dirty implementation; record a reviewed source artifact or tree digest in future. |
| Split algorithm/grouping policy, immutable assignments, seed/RNG details | Conditional: required if an evaluation split is made; seed only if randomized | A deterministic exact-host split API and synthetic feasibility tests exist. No approved split policy, NASA cohort feasibility assessment, or NASA assignments exist. Deterministic non-random schemes need algorithm/configuration and assignments, not a fabricated seed. |
| Baseline/model settings, fitted preprocessing, metric definitions and results | Conditional: required only after evaluation is separately approved | No model run, fitted artifact, metrics, or acceptance threshold exists. |
| Citation/acknowledgment and archive-release/DOI identifiers | Citation metadata required for any applicable publication; release/DOI value only when verified/applicable | NASA guidance is referenced in existing docs. No release identifier or dataset-specific DOI has been established for a future query; do not invent one. |

Any future extraction-attempt manifest must distinguish `unknown`, `not_available`, and `not_applicable`; none may be represented by an invented empty string, zero, hash, release, or timestamp. The repository's offline snapshot and evidence-report manifests cover caller-supplied artifact integrity, not all NASA extraction-attempt metadata. Define and review any additional extraction-manifest schema before implementing that acquisition workflow. Never include secrets.

## 4. Retention, redistribution, citation, and terms

### Internal reproducibility retention

The extraction design proposes storing exact raw response bytes, query, schema evidence, checksum/integrity record, manifest, eligibility ledger, and derived reports outside Git in an approved durable location. This is a technical proposal, **not evidence that a retention location or permission has been approved**. Internal retention is distinct from publishing or redistributing the raw NASA response. A retained checksum alone does not provide reproducibility if its bytes are deleted or inaccessible.

Before acquisition, a project stakeholder/data steward must approve storage location, access control, backup, retention duration, deletion responsibility, and whether raw responses and derived records may be retained for the intended internal research. The manifest should record the decision/reference, not infer authorization.

### Public redistribution and citation

The existing policy matrix records NASA guidance that archive data are public and may be used for additional research with appropriate acknowledgments; NASA's acknowledgment page requests its standard archive acknowledgment, citation of Christiansen et al. (2025), and direct acknowledgment of specific literature references used. NASA also provides DOI guidance. These are citation/use instructions recorded in the repository, not a blanket project-specific permission to redistribute a downloaded snapshot or third-party literature content. Silence about a particular redistribution arrangement is not permission.

Keep internal reproducibility access separate from a public release. Before publishing raw or derived artifacts, project stakeholders must determine applicable NASA/archive terms, third-party source/reference restrictions, attribution, DOI applicability, and what artifact may be redistributed. Obtain authoritative NASA documentation or clarification where terms are unclear. Do not claim a dataset license or redistribution right not evidenced by an authoritative source.

## 5. Approval matrix

Statuses are based only on the inspected repository. **Approved** means explicit approval evidence is recorded; a proposal, recommendation, or prior aggregate observation is not approval. No item below is marked approved.

| Decision/blocker | Status | Evidence in repository | Required approver type |
| --- | --- | --- | --- |
| Research objective, prediction unit/timing, interpretation of archive-reported mass | **proposed; unresolved; blocked** | Task spec calls it exploratory and readiness remains NO-GO; no approved use case. | Scientific reviewer and project/product stakeholder. |
| Candidate cohort `default_flag=1`, exact `pl_bmassprov='Mass'`, target `pl_bmasse`, feature `pl_rade` | **proposed; requires approval; blocked** | 2,211 is a historical candidate-predicate count only. Task and eligibility docs explicitly withhold cohort approval. | Scientific reviewer; project stakeholder for intended use. |
| Missing/non-finite/malformed values and missing-radius complete-case rule | **proposed; unresolved for final cohort; blocked** | Mechanical reporting is proposed; no final extraction snapshot or approved scientific missingness policy. | Technical owner for validation contract; scientific reviewer for cohort/missingness interpretation. |
| Zero/negative target/radius and physical-domain restrictions | **unresolved; blocked** | Existing reviews recommend audit/quarantine only; no thresholds supported. | Scientific reviewer. |
| `pl_bmasselim` / `pl_radelim` mappings and filter use | **unresolved; blocked** | Active-table code and null meanings remain undocumented in repository investigation; similar legacy mapping not transferred. | NASA authoritative documentation/authority for semantics, then scientific reviewer for eligibility consequences. |
| Uncertainty fields: inclusion, missingness, sign processing, weights/sensitivity | **proposed raw metadata only; unresolved; blocked for analysis policy** | NASA side labels and prior aggregate values are documented, but no complete interpretation/uncertainty method approved. | Scientific reviewer; technical owner for lossless capture. |
| `pl_controv_flag` and `soltype` cohort treatment | **proposed preserve/report; unresolved; blocked for filtering** | Field descriptions exist; no inclusion/exclusion rule approved. | Scientific reviewer. |
| Duplicate `pl_name`, identity ambiguity, aliases/case/whitespace normalization | **proposed audit without deduplication; unresolved; blocked for resolution** | No retained full row set; NASA does not document uniqueness/canonical normalization. | Scientific reviewer for unit/row policy; technical owner for exact audit mechanics; NASA documentation if identity mapping is needed. |
| Host (`hostname`) grouping and reference (`pl_refname`) overlap policy | **proposed; unresolved; blocked** | Reviews propose exact-string audits and compare host-only/source-aware grouping; no counts or component graph. | Scientific reviewer. |
| Train/validation/test strategy, proportions, seed, group thresholds and test isolation | **proposed; unresolved; blocked** | A deterministic exact-host split API exists, but no NASA cohort group feasibility or assignments exist; no policy/proportions/thresholds are approved. | Scientific reviewer; technical owner for deterministic implementation/reproducibility. |
| Full extraction method, VOTable completeness, effective service limits and recovery behavior | **proposed; partly verified only by small service tests; blocked** | Tiny async/status/`MAXREC` observations recorded; extraction design says full-scale limits and absence of other truncation remain unverified. | NASA authoritative documentation/authority for service limits where unclear; technical owner for acceptance tests and implementation. |
| Snapshot consistency across count/schema/data queries | **unresolved; blocked for any transactional consistency claim** | Existing evidence provides no common as-of token or isolation guarantee. | NASA authority for service capability; technical owner to record evidence. |
| Snapshot storage, retention, backup, access, deletion | **proposed; unresolved; blocked** | Design proposes off-Git durable storage; no stakeholder decision is recorded. | Project stakeholder/data steward. |
| Public redistribution and applicable terms | **unresolved; blocked for publication/release** | NASA citation guidance is recorded; no project-specific redistribution decision/license is evidenced. | Project stakeholder/data steward; NASA authority if archive terms require clarification. |
| Citation/acknowledgment/DOI handling | **documented guidance; project application proposed; unresolved where artifact DOI applies** | NASA acknowledgment/DOI guidance is cited in project docs; no data-specific DOI or actual publication exists. | Technical/documentation owner to apply verified citations; project stakeholder for release; NASA guidance for DOI applicability. |
| Median DummyRegressor, optional Ridge, MAE/RMSE/R² and acceptance threshold | **proposed; unresolved; blocked** | Task spec proposes the baseline and metrics; no model/evaluation API or result exists; no acceptance threshold. | Scientific reviewer and project/product stakeholder. |
| Manifest/schema/policy versioning and run reproducibility fields | **partly implemented offline; unresolved; blocked for actual artifact acceptance** | Snapshot and evidence-report integrity manifests exist for supplied bytes; the NASA extraction manifest, approved schema/policy versions, and candidate run record do not. | Technical owner; project stakeholder for retention/policy decisions. |

## 6. Go/no-go decision

### Decision: **NO-GO for full NASA extraction and ML evaluation/training**

The gate is not passed by completion of this document. The candidate task and cohort remain proposals; limit semantics, row eligibility, identity resolution, grouping feasibility, retention/terms, extraction completeness, and evaluation protocol remain unresolved or blocked. No scientifically approved eligible dataset exists.

### Safe work now

- Documentation and approval-packet refinement.
- Maintenance and focused hardening of the existing offline manifest, VOTable, ingestion, validation, identity, split-readiness, evidence-report, and persistence components using synthetic fixtures only.
- Offline exact-string identity, duplicate, connected-component, and partition-integrity diagnostics, provided they preserve records and do not encode unapproved eligibility rules.
- Tests of response parsing, checksum verification, manifest state transitions, error/recovery behavior, and no-leakage invariants using synthetic or mocked responses only.

### Remains blocked

- Full NASA candidate extraction or dataset generation.
- Scientific filtering, active limit-code interpretation, identity normalization/deduplication, or publication of a final eligible cohort.
- Snapshot publication or claims of permission to redistribute raw/derived data.
- Actual row/group split assignment, model fitting, model evaluation, metric reporting as generalization evidence, or training.
- Claims that the dataset or mass–radius relationship is scientifically validated, representative, operationally predictive, or approved.

### Evidence checklist before any extraction begins

1. **Scientific contract:** documented approval of purpose, target interpretation, prediction unit/timing, candidate cohort, feature availability, and meaning of the intended generalization claim.
2. **Eligibility:** authoritative active-`ps` limit semantics; reviewed policy for null/missing, non-finite, zero/negative, uncertainty, controversy, solution status, duplicates, and ambiguous identities; exact exclusion/reason taxonomy.
3. **Acquisition completeness:** verified official async protocol, actual effective row/byte limits and overflow handling for the chosen output, job expiry/recovery behavior, required schema metadata, count-check policy, and explicit acknowledgment that separate queries do not prove snapshot identity absent a verified as-of mechanism.
4. **Retention/terms:** stakeholder-approved internal storage, access, backup, retention/deletion plan; separate determination for public redistribution; documented citation/acknowledgment and any applicable DOI.
5. **Reproducibility:** accepted versioned manifest/schema, exact-query recording, raw-byte retention and checksum verification, parser/validator versions, code/environment identity, policy versions, and recoverable artifact locations.
6. **Identity/group feasibility:** after a separately authorized artifact exists, produce row-level identity/duplicate/reference/component diagnostics; approve grouping and predeclare feasible group counts, split proportions, seed/algorithm, stop rules, and test isolation. If components make a valid split infeasible, stop; no random-row fallback.

Passing this checklist would permit a separately authorized extraction attempt only if all source-completeness acceptance criteria pass. It would not itself approve model training or establish scientific validity.

## 7. Open questions and next actions, ranked

1. **Highest impact — scientific task and eligibility decisions:** Is the proposed mass-from-radius question the desired research objective, and is the default/`Mass` cohort meaningful for it? Resolve target/feature timing and zero/negative, uncertainty, controversy, solution, and duplicate policies. Required before declaring cohort or extraction purpose.
2. **Highest technical blocker — active limit semantics:** Obtain authoritative active-`ps` documentation or NASA clarification for both limit code domains and null meaning; then have the scientific owner decide their eligibility impact. Do not repeat numeric-frequency investigations as a substitute for semantics.
3. **Acquisition gate — service completeness and snapshot capability:** The existing small tests do not verify full-scale effective limits or cross-query consistency. Use existing recorded evidence; identify only missing authoritative service-limit facts, and do not run candidate extraction as a test.
4. **Retention and terms:** Project stakeholder/data steward specifies internal raw artifact storage/retention and separately decides whether any public redistribution is intended and permitted; apply NASA citation guidance accurately.
5. **Identity/group gate:** Once a retained dataset is separately approved and available, audit exact identities and compute group/component feasibility. Current evidence cannot answer these quantitatively.
6. **Evaluation gate:** Only after cohort and split feasibility are approved, predeclare baseline/metrics, test isolation, and threshold decision process. No threshold is to be selected from observed test results.

**Smallest useful next action:** assemble one written approval record against the decision matrix (task purpose/cohort and scientific row policies first), while separately requesting authoritative active-`ps` limit-code semantics if current NASA documentation remains insufficient. This advances real blockers without querying for or extracting the dataset. Do not represent a missing response as approval.

## Cross-references

- [`ARC08_BASELINE_ML_TASK_SPEC.md`](ARC08_BASELINE_ML_TASK_SPEC.md)
- [`ARC08_BASELINE_ML_EXTRACTION_DESIGN.md`](ARC08_BASELINE_ML_EXTRACTION_DESIGN.md)
- [`ARC08_BASELINE_ML_POLICY_DECISION_MATRIX.md`](ARC08_BASELINE_ML_POLICY_DECISION_MATRIX.md)
- [`ARC08_NASA_LIMIT_CODE_SEMANTICS.md`](ARC08_NASA_LIMIT_CODE_SEMANTICS.md)
- [`ARC08_SCIENTIFIC_ELIGIBILITY_POLICY_REVIEW.md`](ARC08_SCIENTIFIC_ELIGIBILITY_POLICY_REVIEW.md)
- [`ARC08_IDENTITY_GROUPING_LEAKAGE_REVIEW.md`](ARC08_IDENTITY_GROUPING_LEAKAGE_REVIEW.md)
- NASA citation guidance already recorded in the policy matrix: [acknowledgment](https://exoplanetarchive.ipac.caltech.edu/docs/acknowledge.html), [DOI guidance](https://exoplanetarchive.ipac.caltech.edu/docs/doi.html), and [FAQ](https://exoplanetarchive.ipac.caltech.edu/docs/faq.html).

No NASA request, data extraction, model training/evaluation, implementation change, or new scientific observation was performed for this review.
