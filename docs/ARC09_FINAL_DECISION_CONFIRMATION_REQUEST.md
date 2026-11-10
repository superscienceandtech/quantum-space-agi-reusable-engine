# ARC-09 Final Decision Confirmation Request

**To:** Authorized project owner / Team Lead
**Subject:** Written confirmation needed before finalizing the ARC-09 evidence package

The ARC-09 notebook evidence is technically prepared, but several submission decisions remain unconfirmed. Please confirm the following five items in writing so the package can be finalized against the approved requirements.

## 1. Authoritative source notebook

The repository contains distinct notebook artifacts:

- Workspace original: `arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.ipynb` — SHA-256 `FBE44C2A946B0B04D4B8C9ABB50A0E543D8C0FD70EC6816631E9815368DC2E4F`
- ZIP-embedded original: `ARC09_Hridi_Research_Evidence_Package.zip` entry `ARC09_Visualization_Research_and_Implementation.ipynb` — SHA-256 `03B1C073DE3274E68AD6253A431E943B2C09BBA72FCAEA1130C48DCC6160634F`
- Preserved pre-correction backup: `arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.pre-correction-backup.ipynb` — SHA-256 `4DE94E3E6132E7A62CAADA3CE86CC96DAEDC07F812C917F5391DF114ED8E0121`
- Cell-ID candidate: `arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.cell-id-candidate.ipynb` — SHA-256 `A53684EF51E3F8ED761644299A090B3F336CAE3CEB1891AE67EDDD3C091EF22D`
- Corrected final candidate: `arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.legend-final-candidate.ipynb` — SHA-256 `E792A2C35E4921B390DFFB7EA550F2E4F70F954011BBEA95692B8873A0D0397F`

Which exact file and SHA-256 should be treated as authoritative? Please also confirm how the other copies should be labeled. No copy has been silently substituted for another.

## 2. Accepted execution method

The v4 custom in-process Python runner completed 14 code cells: 14 succeeded, 0 failed, 0 skipped, and six charts were generated and embedded. This was **not standard Jupyter execution**. The run also recorded a nonfatal Matplotlib font-cache permission warning; it was not resolved.

Is this custom-runner result acceptable as supplementary evidence for review? Is standard Jupyter execution mandatory? If it is mandatory, please identify the approved environment and required execution procedure.

## 3. Official submission destination and package structure

Please provide the exact official ARC-08.7.2 repository and folder path, and the required package structure and contents. These are not confirmed in the available project documents.

## 4. SHA-256 manifest

Please confirm the required SHA-256 manifest format and scope, including whether it must cover the v4 runner, v4 execution notebook, and all six v4 charts. The existing `arc09-submission-preparation/SHA256SUMS-custom-execution.txt` is stale: it has three mismatches and does not cover the v4 artifacts. It should not be treated as the final manifest.

## 5. Reviewer and formal acceptance

Rafi is listed for review coordination and proposed as an independent technical reviewer, but formal assignment and availability have not been confirmed. Is Rafi the designated reviewer, and does he accept the assignment? Please also provide the formal acceptance criteria and specify where/how review and acceptance must be recorded.

## Current factual status

- v4 technical execution evidence exists; it does not establish formal approval.
- The existing ZIP is stale and does not include the corrected candidate or v4 evidence.
- The existing manifest has three mismatches.
- Source identity remains ambiguous.
- No formal reviewer acceptance has been located.

Please provide written confirmation of all five decisions before the final package is rebuilt. No submission approval or final acceptance is implied by this request.