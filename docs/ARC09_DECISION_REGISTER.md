# ARC-09 Decision Register

**Purpose:** Track decisions and evidence required before finalizing the ARC-09 notebook evidence package.
**Status basis:** Repository documents and artifacts inspected on 2026-11-10.
**Important:** Technical execution evidence is not formal approval, reviewer acceptance, or submission authorization.

## 1. Authoritative source notebook

**Current status: CONFLICTING** — multiple distinct notebook copies exist; no inspected approval record designates the authoritative source. The ZIP copy and workspace original have matching cell types and source but different cell-ID metadata. The corrected final candidate has edited cell sources and is not identified as the original source.

| Copy | Repository path / location | SHA-256 | Observed structure |
|---|---|---|---|
| Workspace original | `arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.ipynb` | `FBE44C2A946B0B04D4B8C9ABB50A0E543D8C0FD70EC6816631E9815368DC2E4F` | 28 cells; 14 code cells; 16 cells have IDs and 12 do not. |
| ZIP-embedded original | `arc09-submission-preparation/ARC09_Hridi_Research_Evidence_Package.zip` entry `ARC09_Visualization_Research_and_Implementation.ipynb` | `03B1C073DE3274E68AD6253A431E943B2C09BBA72FCAEA1130C48DCC6160634F` | 28 cells; 14 code cells; no cell IDs. Cell types and source match the workspace original. |
| Preserved pre-correction backup | `arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.pre-correction-backup.ipynb` | `4DE94E3E6132E7A62CAADA3CE86CC96DAEDC07F812C917F5391DF114ED8E0121` | 28 cells; 14 code cells; no cell IDs. Its cell source differs from the workspace original. |
| Cell-ID candidate | `arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.cell-id-candidate.ipynb` | `A53684EF51E3F8ED761644299A090B3F336CAE3CEB1891AE67EDDD3C091EF22D` | 28 cells; 14 code cells; IDs on all cells; source and cell types match the workspace original. |
| Corrected final candidate | `arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.legend-final-candidate.ipynb` | `E792A2C35E4921B390DFFB7EA550F2E4F70F954011BBEA95692B8873A0D0397F` | 28 cells; 14 code cells; IDs on all cells; corrected candidate source, distinct from the original copies. |

**Available evidence:** The source-copy inventory above; `arc09-submission-preparation/README.md` (source-of-record note); the ZIP inventory; and the candidate identified in `docs/ARC09_CUSTOM_EXECUTION_REPORT.md`.

**Decision owner:** Not identified by name in the inspected approval documents.
**Still required:** Explicit owner confirmation naming which file is the authoritative source and how the other copies should be labeled in the final package. Do not infer authority from the word “final” in a filename.

## 2. Accepted execution method

**Current status: PENDING** — v4 custom-runner execution is evidenced, but acceptance of that method and whether standard Jupyter is mandatory are not approved in the inspected records.

- v4 runner: `arc09-submission-preparation/run_legend_final_custom_python_notebook_v4.py`; output: `arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.legend-final-custom-python-runner-execution-v4.ipynb`; charts: `arc09-submission-preparation/custom-python-runner-charts-legend-final-v4/`.
- Recorded result: 14 code cells succeeded; 0 failed; 0 skipped; six charts generated and embedded; output notebook JSON and nbformat checks passed; charts were visually inspected.
- Execution mode: **custom in-process Python runner, not standard Jupyter execution**.
- Standard Jupyter mandatory: **PENDING**.

**Available evidence:** `docs/ARC09_CUSTOM_EXECUTION_REPORT.md` and `arc09-submission-preparation/README.md` document the v4 result and explicitly distinguish it from standard Jupyter. They also record a nonfatal Matplotlib font-cache permission warning; it was not resolved.

**Decision owner:** Not identified by name in an approval record.
**Still required:** Written confirmation that the custom runner is acceptable for the intended review, or a requirement and supported environment for standard Jupyter execution.

## 3. Official submission destination and package structure

**Current status: PENDING**.

- Official ARC-08.7.2 destination: **PENDING**.
- Approved directory layout and required package structure: **PENDING**.
- No destination or layout is proposed here as an official requirement.

**Available evidence:** `arc09-submission-preparation/README.md` and `docs/ARC09_CUSTOM_EXECUTION_REPORT.md` state that the official location and requirements remain unconfirmed. The existing ZIP is not a current complete package.

**Decision owner:** Not identified by name in the inspected approval documents.
**Still required:** An authoritative instruction naming the destination, required contents, naming/layout rules, and whether historical artifacts belong in the package.

## 4. SHA-256 manifest requirements

**Current status: CONFLICTING** — the existing manifest is stale against current files, and no approved final scope or format was found.

- Existing manifest: `arc09-submission-preparation/SHA256SUMS-custom-execution.txt`.
- Its documented scope is 11 files: candidate, earlier unversioned runner, earlier unversioned execution output, six PNGs in `custom-python-runner-charts-legend-final/`, README, and execution report. It excludes the manifest itself, source/backup, earlier evidence, environment, and approval records.
- Current recomputation found 3 mismatches: corrected final candidate, README, and execution report. The README mismatch is in addition to the two mismatches identified before the README was updated.
- v4 runner, v4 output notebook, and v4 charts are not covered.
- Whether v4 artifacts must be included: **PENDING**.
- Required manifest format, scope, and approval: **PENDING**.

**Available evidence:** The manifest itself, `arc09-submission-preparation/README.md`, and the hash comparison described above. Hash agreement only verifies bytes against a recorded digest; it does not establish provenance or approval.

**Decision owner:** Not identified by name in the inspected approval documents.
**Still required:** Approval of which files to hash, path convention, hash algorithm/format, whether the manifest is self-excluded, and who verifies/approves it.

## 5. Reviewer and formal acceptance

**Current status: PENDING** — reviewer assignment is confirmed, but technical review completion and formal package acceptance remain pending.

- Reviewer assignment: **CONFIRMED — Rafi** for the ARC-09 notebook evidence package (confirmation supplied by the user).
- Reviewer availability: **PENDING**.
- Formal technical review completion: **PENDING**.
- Formal package acceptance and submission approval: **PENDING**.
- Formal acceptance criteria and how acceptance must be recorded: **PENDING**.

**Available evidence:** The reviewer assignment confirmation was supplied by the user and is recorded in the README. `docs/ARC09_CUSTOM_EXECUTION_REPORT.md` provides technical execution evidence, and `docs/ARC09_MANUAL_VERIFICATION_REPORT.md` records test results; neither establishes formal review completion or package acceptance.

**Decision owner:** No approver is explicitly named in an approval record.
**Still required:** Confirm reviewer availability, objective review criteria, required evidence, and the authoritative record or system where review completion and acceptance are documented.

## Next Actions After Confirmation

Proceed in this order only after decisions are documented:

1. Confirm source identity.
2. Confirm execution-method acceptance.
3. Confirm destination and package structure.
4. Confirm manifest scope and format.
5. Confirm reviewer availability and acceptance criteria.
6. Reconcile README and execution report.
7. Rebuild ZIP and manifest.
8. Verify all hashes and ZIP contents.
9. Perform final read-only audit.
10. Obtain explicit submission authorization.
