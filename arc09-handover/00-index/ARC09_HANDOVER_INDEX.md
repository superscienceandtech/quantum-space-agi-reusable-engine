# ARC-09 Provisional Internal Handover Index

**Status: PROVISIONAL INTERNAL REVIEW PACKAGE.** This is not an official NASA submission, does not imply project acceptance, and does not approve production integration. Inclusion of an artifact is not approval.

## Package identity

- Repository: `C:\Nasa AGI\quantum-space-agi-reusable-engine`
- Branch: `arc/09-visualization`
- HEAD: `1b7cbac6e88c99a47b689e6a45a2fcbdb9019db4` (`docs(arc-10): add decision approval register`)
- Configured upstream: `origin/arc/09-visualization`
- Locally cached `origin/arc/09-visualization` ref at packaging: `1b7cbac6e88c99a47b689e6a45a2fcbdb9019db4`. No fetch or live remote verification was performed; this value may be stale.
- Package assembled: 2026-11-13 (local task date; not the date of the evidence runs).
- Source tree is a working tree containing pre-existing modified and untracked artifacts. This package preserves the captured current bytes; it is not reproducible from HEAD alone.

### Source working-tree status at package refresh

- Modified tracked source paths: 9. Paths: `arc09-ui-prototype/PROTOTYPE_HANDOFF.md` ( M), `arc09-ui-prototype/README.md` ( M), `arc09-ui-prototype/REVIEW_CHECKLIST.md` ( M), `arc09-ui-prototype/app.js` ( M), `arc09-ui-prototype/index.html` ( M), `arc09-ui-prototype/styles.css` ( M), `arc09-submission-preparation/run_legend_final_custom_python_notebook.py` ( M), `docs/ARC09_FINAL_DECISION_CONFIRMATION_REQUEST.md` ( M), `docs/ARC09_MANUAL_VERIFICATION_REPORT.md` ( M)
- Untracked source items copied: 56. All copied source paths and their individual statuses appear in the inventory below. `.venv/` was excluded.
- No staged changes were present at capture. Existing workspace changes were preserved.

## Package directory map

- `00-index/`: this index, complete SHA-256 manifest, and copy report.
- `01-prototype/current-working-tree/`: current prototype source, fixture, provider, validator, README and handoff copies.
- `02-prototype-tests/`: three isolated standalone test pages, not production pages.
- `03-prototype-review/`: review checklists/reports and manual verification report.
- `04-notebook-lineage/`: all 13 workspace notebooks plus the separately named ZIP-embedded original.
- `05-execution-runs/`: all seven runner scripts and seven version-paired chart directories (42 PNGs); v4 output notebook is in notebook lineage and cross-referenced here.
- `06-experiments/`: two historical resource-chart layout experiments.
- `07-requirements-and-integrity/`: requirements, unchanged historical ZIP, and unchanged historical/stale manifest.
- `08-decisions-and-requests/`: ARC-09 requests, proposals, drafts, decision records, plus the ARC-10 decision register.

## Artifact inventory and integrity

`Source SHA-256` is computed from the source working-tree bytes (or the exact ZIP member bytes for the embedded original). `Package-copy SHA-256` is computed from the copied destination bytes. Matching values verify byte-for-byte copy identity. Git status reflects the source path at capture, not approval status.

| Original source path | Package destination | Source Git status | Bytes | Source SHA-256 (= copy SHA-256 after validation) | Role / qualification |
| --- | --- | --- | --- | --- | --- |
| arc09-ui-prototype/index.html | 01-prototype/current-working-tree/index.html |  M | 16092 | 2B9B91A85BDBD6BD4CC88E82B95A5A00053C75972A9ABDC1AED89A4A5D60E4A6 | current working-tree prototype source/support |
| arc09-ui-prototype/styles.css | 01-prototype/current-working-tree/styles.css |  M | 23065 | F2B9316116A215F5BA5FF9F6DE87F4409AE6C5213AB24E306342B455148A34F8 | current working-tree prototype source/support |
| arc09-ui-prototype/data.js | 01-prototype/current-working-tree/data.js | clean | 2726 | 7FF5582055D887B975FCE57C1A4CFE71891992AB060C730E69EE42EAFA90C2B1 | current working-tree prototype source/support |
| arc09-ui-prototype/data-provider.js | 01-prototype/current-working-tree/data-provider.js | ?? | 371 | CC2F308EDD4D17DF54B9EA57FEBDD514EC2E1262521DC5DB8363F60D1DB84260 | current working-tree prototype source/support |
| arc09-ui-prototype/data-validation.js | 01-prototype/current-working-tree/data-validation.js | ?? | 1312 | ECF7178D99D6CF8545FB8BB0F92FD2B455EDA1CADBF7AFB13ADD9F7749EF5B3A | current working-tree prototype source/support |
| arc09-ui-prototype/charts.js | 01-prototype/current-working-tree/charts.js | clean | 15451 | 2630B546A25E4FA6310204B28B1C02915A6EAEC6A40BE3E8A5D66E8C3DB11CD3 | current working-tree prototype source/support |
| arc09-ui-prototype/app.js | 01-prototype/current-working-tree/app.js |  M | 14868 | 6E7831DA9B9FF2B10333440A1E022E085AB9E2576E1B7B348BA2CB2CE01C4507 | current working-tree prototype source/support |
| arc09-ui-prototype/README.md | 01-prototype/current-working-tree/README.md |  M | 6387 | B5D1A862A44E0A8D6B6BB752D8CE8E05FE36F95FA49FE5C447372CB6841447B2 | current working-tree prototype source/support |
| arc09-ui-prototype/PROTOTYPE_HANDOFF.md | 01-prototype/current-working-tree/PROTOTYPE_HANDOFF.md |  M | 10065 | 8C96242E9F6DCEE9C02E61DFE3D961B5F60F6A3BD21A921F8E11D1FF0AD8DFE0 | current working-tree prototype source/support |
| arc09-ui-prototype/data-validation.test.html | 02-prototype-tests/data-validation.test.html | ?? | 4003 | 1A3F6B8F8EEBF4B6766529755CCC7E84BA792EDD8C414761CEB1F6D01280EDAC | isolated test page; not a production application page |
| arc09-ui-prototype/startup-rejection.test.html | 02-prototype-tests/startup-rejection.test.html | ?? | 20625 | B2EC355A5E4DC7E014B7C3E6F7979E4A7EB3A2F8652476A55A616B47BF7F6270 | isolated test page; not a production application page |
| arc09-ui-prototype/startup-invalid-data.test.html | 02-prototype-tests/startup-invalid-data.test.html | ?? | 21633 | 4CEE50051543DF69340E16E20B631F4E08EF15BB473BC6935BE4A6E42816ED29 | isolated test page; not a production application page |
| arc09-ui-prototype/STATIC_AUDIT.md | 03-prototype-review/STATIC_AUDIT.md | clean | 18269 | 1E4E94F6BB702A87455BA357C7F268919485599020C919F5418F9C142CCD4DF2 | prototype review / manual verification evidence |
| arc09-ui-prototype/REVIEW_CHECKLIST.md | 03-prototype-review/REVIEW_CHECKLIST.md |  M | 3830 | B1F4B82E81CE62CFC6F5332C3AAA06079958DF6DFE105206943D8D59CA204BA0 | prototype review / manual verification evidence |
| arc09-ui-prototype/FINAL_REVIEW_SUMMARY.md | 03-prototype-review/FINAL_REVIEW_SUMMARY.md | clean | 5166 | 8D1CF8D76F90369A1D54E0FFAE8A0BBB004F27F102C687F3B98CD500106A608D | prototype review / manual verification evidence |
| docs/ARC09_MANUAL_VERIFICATION_REPORT.md | 03-prototype-review/ARC09_MANUAL_VERIFICATION_REPORT.md |  M | 9491 | 69F33915938039E1CDD6A0B5B1E517E87A6786EBC26437814FF2D5C6554F20FE | prototype review / manual verification evidence |
| arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.cell-id-candidate.ipynb | 04-notebook-lineage/ARC09_Visualization_Research_and_Implementation.cell-id-candidate.ipynb | ?? | 44292 | A53684EF51E3F8ED761644299A090B3F336CAE3CEB1891AE67EDDD3C091EF22D | cell-ID candidate |
| arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.custom-python-runner-execution.ipynb | 04-notebook-lineage/ARC09_Visualization_Research_and_Implementation.custom-python-runner-execution.ipynb | ?? | 404080 | 7209DF222FE9C5982338D21AF848F8D85D9BCA2DA73597475CA0222F554B4127 | historical custom-runner execution output |
| arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.ipynb | 04-notebook-lineage/ARC09_Visualization_Research_and_Implementation.ipynb | ?? | 43274 | FBE44C2A946B0B04D4B8C9ABB50A0E543D8C0FD70EC6816631E9815368DC2E4F | workspace original; source authority unresolved |
| arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.legend-candidate.ipynb | 04-notebook-lineage/ARC09_Visualization_Research_and_Implementation.legend-candidate.ipynb | ?? | 28064 | 0BBBBFD6B5D0AD44613DC7F903F161385D8BCDE8AEF48ABA7D5E3D7819E1EE3B | legend candidate |
| arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.legend-custom-python-runner-execution.ipynb | 04-notebook-lineage/ARC09_Visualization_Research_and_Implementation.legend-custom-python-runner-execution.ipynb | ?? | 395218 | B765C798E694C4F894613B535182684F260AEE67A22E01168D9D5E5A2183898E | historical custom-runner execution output |
| arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.legend-final-candidate.ipynb | 04-notebook-lineage/ARC09_Visualization_Research_and_Implementation.legend-final-candidate.ipynb | clean | 29127 | E792A2C35E4921B390DFFB7EA550F2E4F70F954011BBEA95692B8873A0D0397F | corrected legend-final candidate; source authority unresolved |
| arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.legend-final-custom-python-runner-execution-v2.ipynb | 04-notebook-lineage/ARC09_Visualization_Research_and_Implementation.legend-final-custom-python-runner-execution-v2.ipynb | ?? | 402924 | CFCB707E6EBA94FDCEDF23F26041A79976B04962F098639EBB19E2CA03557C9E | historical custom-runner execution output |
| arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.legend-final-custom-python-runner-execution-v3.ipynb | 04-notebook-lineage/ARC09_Visualization_Research_and_Implementation.legend-final-custom-python-runner-execution-v3.ipynb | ?? | 403251 | E290DD66EFE103CE67E7C2F15E4D330B4E9852C46362335AB21ADA47538F84B0 | historical custom-runner execution output |
| arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.legend-final-custom-python-runner-execution-v4.ipynb | 04-notebook-lineage/ARC09_Visualization_Research_and_Implementation.legend-final-custom-python-runner-execution-v4.ipynb | clean | 396969 | C253BDFE58FEF05CE55410454D2A1F06EC547548411E56762A49EF3F93B9177A | historical custom-runner execution output; v4 referenced by paired v4 runner in 05-execution-runs |
| arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.legend-final-custom-python-runner-execution.ipynb | 04-notebook-lineage/ARC09_Visualization_Research_and_Implementation.legend-final-custom-python-runner-execution.ipynb | clean | 398579 | DE8A41DBE7589063C5DB82490D136196C6534B9F44B4236FFF9A1466877FC62C | historical custom-runner execution output |
| arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.polished-candidate.ipynb | 04-notebook-lineage/ARC09_Visualization_Research_and_Implementation.polished-candidate.ipynb | ?? | 28008 | 60A5DF0D9C2DDFB7F2B5B25F69092A5E61F1951B97D14A0E1D761592220FA6B9 | polished candidate |
| arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.polished-custom-python-runner-execution.ipynb | 04-notebook-lineage/ARC09_Visualization_Research_and_Implementation.polished-custom-python-runner-execution.ipynb | ?? | 403334 | 56C42BC9BDE33817C41E171DB64EFE98991404F66F3481795E151AC90F4ED3DE | historical custom-runner execution output |
| arc09-submission-preparation/ARC09_Visualization_Research_and_Implementation.pre-correction-backup.ipynb | 04-notebook-lineage/ARC09_Visualization_Research_and_Implementation.pre-correction-backup.ipynb | ?? | 42525 | 4DE94E3E6132E7A62CAADA3CE86CC96DAEDC07F812C917F5391DF114ED8E0121 | preserved pre-correction backup |
| arc09-submission-preparation/ARC09_Hridi_Research_Evidence_Package.zip::ARC09_Visualization_Research_and_Implementation.ipynb | 04-notebook-lineage/ARC09_Visualization_Research_and_Implementation.zip-embedded-original.ipynb | archive entry from untracked historical ZIP | 43116 | 03B1C073DE3274E68AD6253A431E943B2C09BBA72FCAEA1130C48DCC6160634F | separately identified original embedded in historical ZIP; not selected as canonical |
| arc09-submission-preparation/run_custom_python_notebook.py | 05-execution-runs/runners/run_custom_python_notebook.py | ?? | 8324 | 1DD07C197FC60C608766B46D3507FB3C19A63F1679A852C0CF9C2D3CE4F63E86 | custom Python runner; supplementary, not standard Jupyter execution |
| arc09-submission-preparation/run_legend_custom_python_notebook.py | 05-execution-runs/runners/run_legend_custom_python_notebook.py | ?? | 8340 | 4BAA4AF5D2A4D551E5D94CDDCB52DAE049AA256E4B29812BD35FC1D43A15FDB0 | custom Python runner; supplementary, not standard Jupyter execution |
| arc09-submission-preparation/run_legend_final_custom_python_notebook.py | 05-execution-runs/runners/run_legend_final_custom_python_notebook.py |  M | 8358 | 5D2BCA9173C002580DC977E683BC73811EF529C9EB05D343CB8169676D35F965 | custom Python runner; supplementary, not standard Jupyter execution |
| arc09-submission-preparation/run_legend_final_custom_python_notebook_v2.py | 05-execution-runs/runners/run_legend_final_custom_python_notebook_v2.py | ?? | 9203 | 8FECC194BACB9374D4C249656240769E816B1A7B40F9B4FD1C5628A7B660F243 | custom Python runner; supplementary, not standard Jupyter execution |
| arc09-submission-preparation/run_legend_final_custom_python_notebook_v3.py | 05-execution-runs/runners/run_legend_final_custom_python_notebook_v3.py | ?? | 9203 | B260D2F3174AC07D1E61FA987F68367B3CE4DEA3E67301A241C583CB554EB5B7 | custom Python runner; supplementary, not standard Jupyter execution |
| arc09-submission-preparation/run_legend_final_custom_python_notebook_v4.py | 05-execution-runs/runners/run_legend_final_custom_python_notebook_v4.py | clean | 9203 | 6EBD4E7A63775AE6A2245D44E03E449F1B56957662D2F01B83B1189C1A6287E1 | custom Python runner; supplementary, not standard Jupyter execution |
| arc09-submission-preparation/run_polished_custom_python_notebook.py | 05-execution-runs/runners/run_polished_custom_python_notebook.py | ?? | 8346 | CCE3D95E4D010DB8900AC41BD8B2516D175472B4D9F0080DE0881CC7950E7CE8 | custom Python runner; supplementary, not standard Jupyter execution |
| arc09-submission-preparation/custom-python-runner-charts-legend-final-v2/chart-cell-13-figure-1.png | 05-execution-runs/custom-python-runner-charts-legend-final-v2/chart-cell-13-figure-1.png | ?? | 39690 | 3569BFBEDD54615DAAB5EB09820E1F08121B212E09D9F554DEC0F652D954B268 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final-v2/chart-cell-14-figure-2.png | 05-execution-runs/custom-python-runner-charts-legend-final-v2/chart-cell-14-figure-2.png | ?? | 46622 | C8E635B0416A4A7C129521DFF2863A75673C9DC58353257BBB625DD3BFA4AD66 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final-v2/chart-cell-15-figure-3.png | 05-execution-runs/custom-python-runner-charts-legend-final-v2/chart-cell-15-figure-3.png | ?? | 45597 | 646E142327D757FCDC411906D1C3CDB5DC49897E254700CCDD920E57983C1800 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final-v2/chart-cell-16-figure-4.png | 05-execution-runs/custom-python-runner-charts-legend-final-v2/chart-cell-16-figure-4.png | ?? | 52192 | 23CBF771D4F286AEF418B9F04617911CD813F872BD7029065F6294111429D68A | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final-v2/chart-cell-17-figure-5.png | 05-execution-runs/custom-python-runner-charts-legend-final-v2/chart-cell-17-figure-5.png | ?? | 36702 | E5CE38723D7C94FD2BF9E891E98531BFD03A10D90C555E0116C35EE07E2B4884 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final-v2/chart-cell-18-figure-6.png | 05-execution-runs/custom-python-runner-charts-legend-final-v2/chart-cell-18-figure-6.png | ?? | 48858 | 244007490BCCA2B792AA72243AB953A34E3D943069D17B309073A700D54EB042 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final-v3/chart-cell-13-figure-1.png | 05-execution-runs/custom-python-runner-charts-legend-final-v3/chart-cell-13-figure-1.png | ?? | 39690 | 3569BFBEDD54615DAAB5EB09820E1F08121B212E09D9F554DEC0F652D954B268 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final-v3/chart-cell-14-figure-2.png | 05-execution-runs/custom-python-runner-charts-legend-final-v3/chart-cell-14-figure-2.png | ?? | 46866 | C79A80E0587145474F259FCB206A646D9887000D927FF6E483468E74895F1FA9 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final-v3/chart-cell-15-figure-3.png | 05-execution-runs/custom-python-runner-charts-legend-final-v3/chart-cell-15-figure-3.png | ?? | 45597 | 646E142327D757FCDC411906D1C3CDB5DC49897E254700CCDD920E57983C1800 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final-v3/chart-cell-16-figure-4.png | 05-execution-runs/custom-python-runner-charts-legend-final-v3/chart-cell-16-figure-4.png | ?? | 52192 | 23CBF771D4F286AEF418B9F04617911CD813F872BD7029065F6294111429D68A | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final-v3/chart-cell-17-figure-5.png | 05-execution-runs/custom-python-runner-charts-legend-final-v3/chart-cell-17-figure-5.png | ?? | 36702 | E5CE38723D7C94FD2BF9E891E98531BFD03A10D90C555E0116C35EE07E2B4884 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final-v3/chart-cell-18-figure-6.png | 05-execution-runs/custom-python-runner-charts-legend-final-v3/chart-cell-18-figure-6.png | ?? | 48858 | 244007490BCCA2B792AA72243AB953A34E3D943069D17B309073A700D54EB042 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final-v4/chart-cell-13-figure-1.png | 05-execution-runs/custom-python-runner-charts-legend-final-v4/chart-cell-13-figure-1.png | clean | 39690 | 3569BFBEDD54615DAAB5EB09820E1F08121B212E09D9F554DEC0F652D954B268 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final-v4/chart-cell-14-figure-2.png | 05-execution-runs/custom-python-runner-charts-legend-final-v4/chart-cell-14-figure-2.png | clean | 42164 | 09D63E9D4899DE28B74ABE8000D6DEDE686A6A571DD8E5770A2F00B99FF8F597 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final-v4/chart-cell-15-figure-3.png | 05-execution-runs/custom-python-runner-charts-legend-final-v4/chart-cell-15-figure-3.png | clean | 45597 | 646E142327D757FCDC411906D1C3CDB5DC49897E254700CCDD920E57983C1800 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final-v4/chart-cell-16-figure-4.png | 05-execution-runs/custom-python-runner-charts-legend-final-v4/chart-cell-16-figure-4.png | clean | 52192 | 23CBF771D4F286AEF418B9F04617911CD813F872BD7029065F6294111429D68A | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final-v4/chart-cell-17-figure-5.png | 05-execution-runs/custom-python-runner-charts-legend-final-v4/chart-cell-17-figure-5.png | clean | 36702 | E5CE38723D7C94FD2BF9E891E98531BFD03A10D90C555E0116C35EE07E2B4884 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final-v4/chart-cell-18-figure-6.png | 05-execution-runs/custom-python-runner-charts-legend-final-v4/chart-cell-18-figure-6.png | clean | 48858 | 244007490BCCA2B792AA72243AB953A34E3D943069D17B309073A700D54EB042 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final/chart-cell-13-figure-1.png | 05-execution-runs/custom-python-runner-charts-legend-final/chart-cell-13-figure-1.png | clean | 39690 | 3569BFBEDD54615DAAB5EB09820E1F08121B212E09D9F554DEC0F652D954B268 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final/chart-cell-14-figure-2.png | 05-execution-runs/custom-python-runner-charts-legend-final/chart-cell-14-figure-2.png | clean | 44058 | A5C21305AED1D590CE136649F3437EB03D646B013BB26E618DA2AD320DDD7B38 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final/chart-cell-15-figure-3.png | 05-execution-runs/custom-python-runner-charts-legend-final/chart-cell-15-figure-3.png | clean | 45597 | 646E142327D757FCDC411906D1C3CDB5DC49897E254700CCDD920E57983C1800 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final/chart-cell-16-figure-4.png | 05-execution-runs/custom-python-runner-charts-legend-final/chart-cell-16-figure-4.png | clean | 52192 | 23CBF771D4F286AEF418B9F04617911CD813F872BD7029065F6294111429D68A | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final/chart-cell-17-figure-5.png | 05-execution-runs/custom-python-runner-charts-legend-final/chart-cell-17-figure-5.png | clean | 36702 | E5CE38723D7C94FD2BF9E891E98531BFD03A10D90C555E0116C35EE07E2B4884 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend-final/chart-cell-18-figure-6.png | 05-execution-runs/custom-python-runner-charts-legend-final/chart-cell-18-figure-6.png | clean | 48858 | 244007490BCCA2B792AA72243AB953A34E3D943069D17B309073A700D54EB042 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend/chart-cell-13-figure-1.png | 05-execution-runs/custom-python-runner-charts-legend/chart-cell-13-figure-1.png | ?? | 39690 | 3569BFBEDD54615DAAB5EB09820E1F08121B212E09D9F554DEC0F652D954B268 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend/chart-cell-14-figure-2.png | 05-execution-runs/custom-python-runner-charts-legend/chart-cell-14-figure-2.png | ?? | 44058 | A5C21305AED1D590CE136649F3437EB03D646B013BB26E618DA2AD320DDD7B38 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend/chart-cell-15-figure-3.png | 05-execution-runs/custom-python-runner-charts-legend/chart-cell-15-figure-3.png | ?? | 45597 | 646E142327D757FCDC411906D1C3CDB5DC49897E254700CCDD920E57983C1800 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend/chart-cell-16-figure-4.png | 05-execution-runs/custom-python-runner-charts-legend/chart-cell-16-figure-4.png | ?? | 52192 | 23CBF771D4F286AEF418B9F04617911CD813F872BD7029065F6294111429D68A | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend/chart-cell-17-figure-5.png | 05-execution-runs/custom-python-runner-charts-legend/chart-cell-17-figure-5.png | ?? | 34190 | C74DC78B6E38F085D0207AF81F9DFE56F11C9218B36F0F9144A939BB95DD0855 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-legend/chart-cell-18-figure-6.png | 05-execution-runs/custom-python-runner-charts-legend/chart-cell-18-figure-6.png | ?? | 48858 | 244007490BCCA2B792AA72243AB953A34E3D943069D17B309073A700D54EB042 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-polished/chart-cell-13-figure-1.png | 05-execution-runs/custom-python-runner-charts-polished/chart-cell-13-figure-1.png | ?? | 39690 | 3569BFBEDD54615DAAB5EB09820E1F08121B212E09D9F554DEC0F652D954B268 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-polished/chart-cell-14-figure-2.png | 05-execution-runs/custom-python-runner-charts-polished/chart-cell-14-figure-2.png | ?? | 44058 | A5C21305AED1D590CE136649F3437EB03D646B013BB26E618DA2AD320DDD7B38 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-polished/chart-cell-15-figure-3.png | 05-execution-runs/custom-python-runner-charts-polished/chart-cell-15-figure-3.png | ?? | 45597 | 646E142327D757FCDC411906D1C3CDB5DC49897E254700CCDD920E57983C1800 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-polished/chart-cell-16-figure-4.png | 05-execution-runs/custom-python-runner-charts-polished/chart-cell-16-figure-4.png | ?? | 52192 | 23CBF771D4F286AEF418B9F04617911CD813F872BD7029065F6294111429D68A | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-polished/chart-cell-17-figure-5.png | 05-execution-runs/custom-python-runner-charts-polished/chart-cell-17-figure-5.png | ?? | 40317 | 1D18A8513911DB89B41024A721C5B0E552AE1CF959B2FEBD331539E026C4C9A6 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts-polished/chart-cell-18-figure-6.png | 05-execution-runs/custom-python-runner-charts-polished/chart-cell-18-figure-6.png | ?? | 48858 | 244007490BCCA2B792AA72243AB953A34E3D943069D17B309073A700D54EB042 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts/chart-cell-13-figure-1.png | 05-execution-runs/custom-python-runner-charts/chart-cell-13-figure-1.png | ?? | 39690 | 3569BFBEDD54615DAAB5EB09820E1F08121B212E09D9F554DEC0F652D954B268 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts/chart-cell-14-figure-2.png | 05-execution-runs/custom-python-runner-charts/chart-cell-14-figure-2.png | ?? | 44058 | A5C21305AED1D590CE136649F3437EB03D646B013BB26E618DA2AD320DDD7B38 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts/chart-cell-15-figure-3.png | 05-execution-runs/custom-python-runner-charts/chart-cell-15-figure-3.png | ?? | 45597 | 646E142327D757FCDC411906D1C3CDB5DC49897E254700CCDD920E57983C1800 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts/chart-cell-16-figure-4.png | 05-execution-runs/custom-python-runner-charts/chart-cell-16-figure-4.png | ?? | 52192 | 23CBF771D4F286AEF418B9F04617911CD813F872BD7029065F6294111429D68A | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts/chart-cell-17-figure-5.png | 05-execution-runs/custom-python-runner-charts/chart-cell-17-figure-5.png | ?? | 40477 | B6482C29296D94407D2E8F277EAC3FA2DFC5971389201D506DC349EFF9427A91 | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/custom-python-runner-charts/chart-cell-18-figure-6.png | 05-execution-runs/custom-python-runner-charts/chart-cell-18-figure-6.png | ?? | 49278 | A5B853737B669EB8D80F1066A261FEF332617A7353577CA29269E32B94CC742F | generated chart image; paired by versioned chart-directory name |
| arc09-submission-preparation/resource-chart-layout-experiment-v1.png | 06-experiments/resource-chart-layout-experiment-v1.png | ?? | 42239 | 3DF7A22BF2B873F1B9813ED66586680DE3FECDFD404064072208BE2AD72DC240 | historical resource-chart layout experiment |
| arc09-submission-preparation/resource-chart-layout-experiment-v2.png | 06-experiments/resource-chart-layout-experiment-v2.png | ?? | 42164 | 09D63E9D4899DE28B74ABE8000D6DEDE686A6A571DD8E5770A2F00B99FF8F597 | historical resource-chart layout experiment |
| arc09-submission-preparation/requirements.txt | 07-requirements-and-integrity/requirements.txt | clean | 79 | 389B86C317ED57DD13A51089F8B58695212CACC444387852BFC5563D20C818F6 | dependency record |
| arc09-submission-preparation/SHA256SUMS-custom-execution.txt | 07-requirements-and-integrity/SHA256SUMS-custom-execution.txt | clean | 1979 | 5ECDEC3EF2F3EB67E37ADFF2844326DC7DA3979309016AD46894228C8AB95E47 | historical/stale manifest; excludes current v4 evidence |
| arc09-submission-preparation/ARC09_Hridi_Research_Evidence_Package.zip | 07-requirements-and-integrity/ARC09_Hridi_Research_Evidence_Package.zip | ?? | 552536 | 3817D304231D0F302766BCD7578F0C0893E253DB8B0534C1CA47A5907998EE7A | historical/stale ZIP; does not contain current v4 runner/output/chart set |
| docs/ARC09_BACKEND_DATA_CONTRACT_REQUEST.md | 08-decisions-and-requests/ARC09_BACKEND_DATA_CONTRACT_REQUEST.md | clean | 9106 | 9CA6272095AB04E661989CDA582F3C35DD6D66DF5B830EA344162D635FFD33B5 | request / proposal / draft / decision record; inclusion does not mean approval |
| docs/ARC09_CUSTOM_EXECUTION_REPORT.md | 08-decisions-and-requests/ARC09_CUSTOM_EXECUTION_REPORT.md | clean | 6511 | 1139670B091F3B04999D6EF08D69111676FB07BE73701756D29E3A8FB822B707 | request / proposal / draft / decision record; inclusion does not mean approval |
| docs/ARC09_DASHBOARD_API_INTEGRATION_REQUEST.md | 08-decisions-and-requests/ARC09_DASHBOARD_API_INTEGRATION_REQUEST.md | ?? | 1226 | C8F483E43D9359A4D1291C07868E8B48A786E72C3260FF878ECB4D99DF369735 | request / proposal / draft / decision record; inclusion does not mean approval |
| docs/ARC09_DASHBOARD_INTEGRATION_BLUEPRINT.md | 08-decisions-and-requests/ARC09_DASHBOARD_INTEGRATION_BLUEPRINT.md | ?? | 38181 | 014F10FB9E385171DDFEE009A2D7D3732DB03D6C0C26E8D72DD01468CE7E0072 | request / proposal / draft / decision record; inclusion does not mean approval |
| docs/ARC09_DECISION_REGISTER.md | 08-decisions-and-requests/ARC09_DECISION_REGISTER.md | clean | 8008 | 3C51DFDFE99CDB01A133964AD9CAC5FEA67F6D67202CB10AAD2B29C78C642FC5 | request / proposal / draft / decision record; inclusion does not mean approval |
| docs/ARC09_FINAL_DECISION_CONFIRMATION_REQUEST.md | 08-decisions-and-requests/ARC09_FINAL_DECISION_CONFIRMATION_REQUEST.md |  M | 3915 | DA4E465A4669C884F8864CF87DED80D9B01CAE0AB9A5C6DA3415D02B1F225157 | request / proposal / draft / decision record; inclusion does not mean approval |
| docs/ARC09_PRODUCTION_INTEGRATION_HANDOVER.md | 08-decisions-and-requests/ARC09_PRODUCTION_INTEGRATION_HANDOVER.md | ?? | 26837 | 91E8BE05D9426A61563A1D4562848B55C7500A30E4631D88548071E28A949E55 | request / proposal / draft / decision record; inclusion does not mean approval |
| docs/ARC09_TEAM_LEAD_DECISION_MESSAGE_DRAFT.md | 08-decisions-and-requests/ARC09_TEAM_LEAD_DECISION_MESSAGE_DRAFT.md | clean | 1085 | CFC2C24DB0A196E20E6DB6CFC91F30E3F305082E6B08E18B6BF9DB5AABDBAA56 | request / proposal / draft / decision record; inclusion does not mean approval |
| docs/ARC10_DECISION_APPROVAL_REGISTER.md | 08-decisions-and-requests/ARC10_DECISION_APPROVAL_REGISTER.md | clean | 22170 | D0018973B45549ED2372DBD918074E82F1A8E279AB4BD6A84296445B0C128B3E | request / proposal / draft / decision record; inclusion does not mean approval |

## Notebook lineage and source ambiguity

- The package contains the workspace original and the original notebook embedded in the historical ZIP as separate, distinctly named artifacts. Their bytes/hashes are not treated as interchangeable.
- It also preserves the pre-correction backup, cell-ID candidate, legend candidate, polished candidate, legend-final candidate, and all seven execution-output notebooks.
- No canonical/source-of-record notebook is selected. Source identity remains unresolved pending explicit owner confirmation.
- Every notebook keeps its original workspace filename except the ZIP member, whose destination name explicitly marks its archive origin. No candidate is renamed to the original notebook name.

## Visualization count reconciliation

- The prototype source presents three overview metric cards, two resource cards, recent activity, and four chart/graph regions: line, grouped bar, scatter, and a conceptual relationship graph. Cards/activity are separate dashboard regions, not extra charts.
- The notebook execution evidence has six generated chart PNGs per run directory. Those six notebook charts do not imply six production dashboard visualizations.
- Relationship graph entities/edges and prototype values are synthetic/conceptual; they are not authoritative scientific or mission data.

## Browser Test 1–11 Evidence

All outcomes below are user-reported/user-confirmed manual browser results, not independently reproduced by the package preparer.

| Test | Recorded outcome |
| --- | --- |
| 1 ? Normal dashboard startup | PASS ? user-reported |
| 2 ? Operational loading status | PASS ? user-reported; user did not clarify whether transient indicator was visibly observed or disappeared too quickly |
| 3 ? Cards and visualizations | PASS ? user-reported: three overview cards, two resource cards, illustrative 68%/42% shares, line/grouped-bar/scatter and conceptual graph |
| 4 ? Activity filters | PASS ? user-reported; four filter options |
| 5 ? Keyboard/accessibility-related manual checks | PASS ? user-reported; does not establish screen-reader testing or compliance |
| 6 ? Responsive layout/overflow | PASS ? user-reported; no viewport-by-viewport measurements or screenshots supplied |
| 7 ? Chart tables and graph text alternative | PASS ? user-reported |
| 8 ? Static loading/empty/error previews | PASS ? user-reported; static demonstrations, not backend requests |
| 9 ? Data validation harness | PASS ? user-reported, expected 10/10 |
| 10 ? Rejected-Promise startup harness | PASS ? user-reported, expected 8/8 |
| 11 ? Invalid-resolved-data startup harness | PASS ? user-reported, expected 9/9 |

### Browser evidence limitations

- Browser, browser version, OS version, viewport, zoom, device-pixel ratio, exact test-run timestamp, screenshots, screen recordings, and Console exports were not supplied; these are NOT RECORDED.
- No screen-reader/accessibility-tree test is established. User-reported keyboard/accessibility-related checks are not an accessibility compliance claim.
- The manual report records a user-reported `favicon.ico` 404 warning; exact request URL, current response, and current reproducibility were not independently verified.
- Separate user-reported Cursor Node v24.22.1 syntax checks reportedly exited 0 for `app.js`, `charts.js`, `data-provider.js`, and `data-validation.js`; this package operation did not independently rerun those checks.

## Provider boundary and startup evidence

- Current prototype source has a synchronous fixture provider exposing `getData()`; startup also awaits provider results and therefore supports Promise-returning providers by source design. The fixture/provider remain prototype-only.
- Prototype-shape validation occurs before rendering; it is not an approved backend DTO/schema contract. Failure paths handle provider/validation/startup errors with loading, dashboard busy-state, cleanup, and generic alert behavior, as documented/source-inspected.
- Three standalone browser test pages are kept separate from the production page; their results above are user-reported.
- No production API transport, endpoint, DTO, authentication, or backend integration is included or approved by this package.

## Historical ZIP and manifest status

- The copied `ARC09_Hridi_Research_Evidence_Package.zip` and `SHA256SUMS-custom-execution.txt` are preserved byte-for-byte as historical artifacts. Audit evidence identifies the ZIP as stale and incomplete for v4: it does not include the v4 runner, v4 output notebook, or six v4 charts.
- The copied manifest is stale for current working-tree content, with three previously recorded mismatches, and does not cover current v4 artifacts. It is not the manifest for this handover package. `00-index/ARC09_HANDOVER_SHA256SUMS.txt` is a separate package-copy manifest.

## Completed package tasks

- Copied the specified current prototype sources, three isolated test pages, review documents, all notebook lineage artifacts, all seven runner/chart sets, experiments, requirements/integrity artifacts, and decision/request documents.
- Source/destination byte sizes and SHA-256 hashes are recorded in the copy report and artifact inventory.
- `.venv/` and unrelated files are excluded. The existing ZIP was copied unchanged; no replacement ZIP was generated.

## Remaining decisions and blockers

- Confirm the authoritative/source-of-record notebook by exact path/hash; preserve the distinction among workspace, ZIP-embedded, backup, candidates, and outputs.
- Confirm official ARC-08.7.2 destination, package structure, accepted execution method, manifest format/scope, and final submission authorization.
- Obtain authoritative first-party Dashboard API contract and production frontend target/architecture, including endpoints, schemas, units, semantics, auth/security, errors, test environment, and acceptance criteria before production integration.
- Notebook evidence reviewer assignment for Rafi is user-confirmed in the Decision Register; availability, completed review, review outcome/package acceptance, and formal submission approval remain pending.
- Custom in-process runner execution is supplementary technical evidence and is not standard Jupyter execution.

## Governance and status

This package is a provisional internal handover for owner review only. It does not establish scientific validity, NASA acceptance, canonical source approval, formal reviewer acceptance, production readiness, production integration approval, or authorization to submit. Synthetic examples must remain separate from NASA research/production data.


## Security-scan qualification

The copy report now records a separate, independent, limited credential-marker scan performed after package assembly: 61 text/text-like files and ZIP text members were scanned for private-key markers, common GitHub token patterns, AWS access-key IDs, and credential-bearing URLs; no matches were detected. Fifty PNG files were excluded. This was not comprehensive secret detection and does not prove that the package contains no secrets. The original package-generation process did not document or claim to have performed this scan.

See the complete seven-group SHA-256-to-path mapping in `00-index/ARC09_HANDOVER_COPY_REPORT.md` under **Duplicate PNG content groups**. All listed files remain preserved.
