# ARC-09 Visualization Notebook Preparation

**Project:** Quantum Space AGI — Space Mission Design Game  
**Workstream:** ARC-09 Visualization  
**Contributor:** Hridi  
**Reviewer assignment for the ARC-09 notebook evidence package:** Confirmed — Rafi (confirmation supplied by the user).

**Submission status:** Supplementary custom-runner evidence is available. Official submission location, requirements, and formal acceptance remain unconfirmed.

## Purpose and scope

This notebook demonstrates dashboard-style visualizations, simple structural validation, synthetic-data provenance, and visualization-state concepts. It is an educational visualization example, not a validated scientific model, mission simulation, NASA data analysis, or production application integration.

All datasets and values are synthetic examples authored in the notebook. They are not NASA observations, scientific measurements, mission outcomes, validated model results, or approved product requirements. The scatter values use a fixed NumPy seed. Physical meanings and scientific units are not defined by these examples.

## Current candidate and execution artifacts

The current corrected candidate is:

`ARC09_Visualization_Research_and_Implementation.legend-final-candidate.ipynb`

SHA-256: `E792A2C35E4921B390DFFB7EA550F2E4F70F954011BBEA95692B8873A0D0397F`

The latest successful run used:

| File or directory | Role and status |
|---|---|
| `run_legend_final_custom_python_notebook_v4.py` | Versioned custom in-process Python runner. |
| `ARC09_Visualization_Research_and_Implementation.legend-final-custom-python-runner-execution-v4.ipynb` | v4 execution output; 28 cells, source and cell types matching the candidate. |
| `custom-python-runner-charts-legend-final-v4/` | Six v4 PNG chart outputs, also embedded in the v4 output notebook. |
| `../docs/ARC09_CUSTOM_EXECUTION_REPORT.md` | Detailed v4 execution, chart review, hashes, warning, and limitations. |

The v4 run completed 14 code cells, with zero failures and zero skipped cells. Execution counts were sequential from 1 through 14. The output notebook passed JSON and nbformat validation. All six PNGs were generated, validated, embedded, and visually inspected at full resolution.

This was **custom in-process Python execution, not standard Jupyter execution**. No Jupyter kernel or server was used. The custom runner does not reproduce all Jupyter frontend and kernel behavior, and its successful execution does not establish scientific validity or browser behavior.

The recorded v4 invocation from the repository root was:

```powershell
.venv\Scripts\python.exe arc09-submission-preparation\run_legend_final_custom_python_notebook_v4.py
```

This command documents the completed custom-runner method; it is not a standard Jupyter launch command.

### v4 chart review

The resource chart displays the corrected y-axis label `Illustrative percentage (%) — no total implied` with a U+2014 em dash. The complete label and synthetic-data footer are visible without overlap, and both bars remain readable. The grouped-bar legend and footer are readable; the scatter annotation is readable and does not obscure plotted points.

## Historical versions and source-of-record note

- v2 and v3 are retained as historical custom-runner executions with separate output notebooks and chart directories.
- The v3 resource chart had a clipped y-axis label. The v4 run uses the corrected candidate and its resource chart was visually inspected.
- Earlier runners, candidates, chart directories, and isolated resource-chart experiments remain separate historical artifacts.
- The workspace original, the original notebook embedded in the ZIP, the pre-correction backup, the cell-ID candidate, and the corrected final candidate are distinct copies. Their metadata and/or cell sources differ. **This README does not designate any of them as the authoritative original.** Source-of-record selection requires owner confirmation.

The existing `ARC09_Hridi_Research_Evidence_Package.zip` is stale: it does not contain the corrected current candidate or the v4 runner, v4 execution output, or v4 chart directory. It must not be treated as the current complete evidence package.

## Visualization contents

The notebook contains six Matplotlib figures:

1. Synthetic dashboard metric summary.
2. Illustrative resource percentage display.
3. Synthetic recent-activity example counts.
4. Synthetic line chart.
5. Synthetic grouped-bar comparison.
6. Synthetic scatter demonstration.

The figures include synthetic-data disclosures. Tables are printed as text alternatives. The grouped-bar legend is positioned above the chart title. These examples have no approved mission or scientific interpretation.

## Dependencies and environment

The existing environment used for the v4 run was Python 3.12.10 with:

- NumPy 2.5.4
- pandas 3.1.1
- Matplotlib 3.11.2
- nbformat 5.11.1
- nbclient 0.11.0

Exact pins are listed in `requirements.txt`. No packages were installed for the v4 run. If execution is authorized in an appropriate environment, use that environment's approved Python/Jupyter workflow and follow the project owner's setup instructions; the custom runner is not a substitute for standard Jupyter when Jupyter execution is required.

## Warning captured during v4 execution

The execution notebook captured this nonfatal Matplotlib font-cache permission warning:

`Could not save font_manager cache [Errno 13] Permission denied: 'C:\\Users\\HP\\AppData\\Local\\matplotlib\\fontlist-v3.11.0.json.matplotlib-lock'`

It did not cause a code-cell failure. The warning was **not fixed** and remains disclosed here.

## Integrity and package limitations

`SHA256SUMS-custom-execution.txt` is stale. Before this README update, its 11 entries had two mismatches: the corrected final candidate and the updated custom execution report. Because the manifest also lists this README, this README update makes a third entry stale. The manifest does not cover v4 artifacts and must not be treated as the current complete evidence manifest.

A complete immediate pre-execution snapshot of 62 artifact hashes was not retained. Available recorded checks support preservation of key protected artifacts, but do not prove that all 62 were unchanged. Hash matches establish byte equality against a recorded hash only; they do not establish provenance, scientific validity, or approval.

The existing ZIP and manifest are historical package evidence, not the current complete v4 package. Neither has been updated as part of this README change.

## Limitations and approval status

- Standard Jupyter execution remains unverified. A previous attempt was blocked before notebook cells ran: IPython could not create `C:\Users\HP\.ipython`; a retry failed with `PermissionError: [WinError 5] Access is denied` while setting security on a temporary kernel connection file. No security settings or permissions were changed.
- PNG review is not browser, interactive notebook, or screen-reader testing.
- Data validation is demonstration-level structural validation, not domain or scientific validation.
- No NASA/ARC-08 data, production API, mission result, or approved scientific contract is connected.
- No NASA validation, scientific validity, or production readiness is claimed.
- Official ARC-08.7.2 submission instructions, the required directory layout, the accepted execution method, formal technical review completion, and package acceptance remain **unconfirmed**.
- Rafi’s reviewer assignment for the ARC-09 notebook evidence package is confirmed (confirmation supplied by the user); this does not indicate that the review is complete or the package accepted.
- This work is not represented as a final or officially accepted submission.

## Submission checklist

- [x] Current corrected candidate is identified separately from source and historical copies.
- [x] v4 custom-runner output and six chart files are present and documented.
- [x] v4 chart review and the nonfatal warning are disclosed in the execution report.
- [x] Required dependency pins are listed.
- [ ] Confirm the authoritative source/original and backup with the responsible owner.
- [ ] Confirm official ARC-08.7.2 submission instructions and destination.
- [ ] Confirm the accepted execution method and required package layout.
- [ ] Reconcile the stale manifest and ZIP after package requirements are approved.
- [ ] Record technical review completion and formal package acceptance.
