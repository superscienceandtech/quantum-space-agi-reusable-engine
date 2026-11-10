# ARC-09 Custom Notebook Execution Report

**Project:** Quantum Space AGI — Space Mission Design Game
**Scope:** Supplementary execution evidence for the ARC-09 visualization notebook
**Latest execution:** v4 custom in-process Python runner
**Execution mode:** Custom Python cell runner; **not standard Jupyter execution**
**Official submission status:** Pending confirmation of the approved ARC-08.7.2 submission location and acceptance requirements.

## Artifact versions

The v4 execution is the latest successful execution of the corrected candidate. Earlier outputs remain historical evidence and have not been replaced.

- Candidate: `arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.legend-final-candidate.ipynb`
- v4 runner: `arc09-submission-preparation/run_legend_final_custom_python_notebook_v4.py`
- v4 execution output: `arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.legend-final-custom-python-runner-execution-v4.ipynb`
- v4 chart directory: `arc09-submission-preparation/custom-python-runner-charts-legend-final-v4/`
- Earlier v2 and v3 execution notebooks and chart directories remain historical artifacts. The v3 resource chart had a clipped label; v4 includes the corrected candidate label.

## v4 environment and method

The candidate was run using the existing repository `.venv\Scripts\python.exe` with Python 3.12.10. The recorded environment versions were NumPy 2.5.4, pandas 3.1.1, Matplotlib 3.11.2, and nbformat 5.11.1.

The custom runner evaluated code cells sequentially in one shared Python namespace, preserved Markdown and code source, captured outputs, and saved actual Matplotlib figures. No Jupyter kernel, Jupyter server, or WSL process was used, and no packages were installed. Custom-runner execution does not establish standard Jupyter behavior, browser behavior, or scientific validity.

## v4 execution and notebook validation

| Check | Result |
|---|---|
| Runner process exit code | 0 |
| Notebook cells | 28; source and cell types match the candidate |
| Code cells | 14 succeeded; 0 failed; 0 skipped |
| Execution counts | Sequential, 1 through 14 |
| Output notebook JSON and nbformat validation | PASS |
| Generated chart PNGs | 6; valid PNG signatures |
| Embedded figures | All 6 embedded byte-for-byte in the output notebook |
| Runner stderr | Empty |

### v4 artifact hashes

- Candidate SHA-256: `E792A2C35E4921B390DFFB7EA550F2E4F70F954011BBEA95692B8873A0D0397F`
- v4 runner SHA-256: `70E979B335C2AB26A94E6C5D7F8E29D435C08FA285F35EEB8F1AD5AE92220D6C`
- v4 output notebook SHA-256: `c253bdfe58fef05ce55410454d2a1f06ec547548411e56762a49ef3f93b9177a`

| Chart | Dimensions | SHA-256 |
|---|---:|---|
| `chart-cell-13-figure-1.png` — dashboard metric summary | 1034 × 531 | `3569bfbedd54615daab5eb09820e1f08121b212e09d9f554dec0f652d954b268` |
| `chart-cell-14-figure-2.png` — resource illustration | 817 × 555 | `09d63e9d4899de28b74abe8000d6dede686a6a571dd8e5770a2f00b99ff8f597` |
| `chart-cell-15-figure-3.png` — activity counts | 897 × 531 | `646e142327d757fcdc411906d1c3cdb5dc49897e254700ccdd920e57983c1800` |
| `chart-cell-16-figure-4.png` — line chart | 884 × 531 | `23cbf771d4f286aef418b9f04617911cd813f872bd7029065f6294111429d68a` |
| `chart-cell-17-figure-5.png` — grouped-bar chart | 904 × 523 | `e5ce38723d7c94fd2bf9e891e98531bfd03a10d90c555e0116c35ee07e2b4884` |
| `chart-cell-18-figure-6.png` — scatter chart | 750 × 606 | `244007490bcca2b792aa72243ab953a34e3d943069d17b309073a700d54eb042` |

## v4 visual review

All six v4 PNGs were visually inspected at full resolution. The resource chart displays the complete y-axis label `Illustrative percentage (%) — no total implied`; its em dash is U+2014. The label is fully visible, does not overlap the synthetic-data footer, and both bars remain readable. The grouped-bar legend and footer are readable and do not overlap the bars. The scatter annotation is readable and does not obscure plotted points. This is inspection of rendered PNGs, not browser, screen-reader, or standard Jupyter frontend testing.

## Warning captured during v4 execution

The execution notebook captured this nonfatal Matplotlib font-cache warning:

`Could not save font_manager cache [Errno 13] Permission denied: 'C:\\Users\\HP\\AppData\\Local\\matplotlib\\fontlist-v3.11.0.json.matplotlib-lock'`

It did not cause a code-cell failure. The warning was not resolved and should not be interpreted as resolved.

## Historical evidence and integrity limitations

The v2 and v3 notebooks and chart directories remain separate historical artifacts. v4 wrote to its versioned output notebook and chart directory; no historical artifact was intentionally overwritten.

Available recorded hash checks support preservation of key protected artifacts. However, the complete immediate pre-execution snapshot of 62 artifact hashes was not retained, so this report does not claim that all 62 were independently proven unchanged. A previously noted historical notebook hash discrepancy was traced to a transcription error: the current historical notebook hash matches its recorded inventory value. This does not establish a complete comparison against the lost immediate pre-execution snapshot.

The existing manifest `arc09-submission-preparation/SHA256SUMS-custom-execution.txt` has its own documented scope. This report does not update or extend that manifest, and v4 hash entries above should not be read as claims that the existing manifest covers v4 artifacts.

## Limitations and pending approval

This evidence demonstrates successful custom in-process execution of 14 code cells and generation and visual inspection of six PNGs. It does not establish standard Jupyter execution, interactive notebook behavior, browser behavior, scientific validation, NASA data use, product readiness, or official submission acceptance.

The standard Jupyter execution path remains unverified. A prior attempt failed before notebook cells started: IPython could not create `C:\Users\HP\.ipython`; a retry using temporary directories encountered `PermissionError: [WinError 5] Access is denied` while setting security on a temporary kernel connection file. No security controls or permissions were changed.

The official ARC-08.7.2 submission directory, required package structure, and acceptance requirements remain pending confirmation by the responsible project owner. Do not represent this package as an official submission until those decisions are confirmed.
