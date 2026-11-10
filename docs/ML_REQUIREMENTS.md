# ML Requirements and Readiness

**Status:** Requirements analysis only. No model, training code, dataset, or prediction task is approved by this document.

## Current readiness

The project brief describes an educational mission-design game. ARC-08 now includes reusable offline data-preparation, leakage-diagnostic, and regression-evaluation interfaces, but their presence is engineering capability only. The exploratory NASA mass–radius proposal in [`ARC08_BASELINE_ML_TASK_SPEC.md`](ARC08_BASELINE_ML_TASK_SPEC.md) is not an approved scientific prediction task, dataset, or evaluation. Baseline scientific implementation and model training remain NO-GO. Do not use the educational evaluator's fictional score as a scientific target. Prefer deterministic scientific computation, simulation, or optimization where those methods meet the product need.

## Candidate task definition (to complete later)

Before selecting an algorithm, document:

- User or system decision that a prediction supports, and why prediction is needed.
- Unit of prediction and intended inference time (what information is available then).
- Candidate input features and their source, meaning, type, and units.
- Target/output variable, label-generation method, and prediction horizon, if supervised.
- Dataset size, coverage, sampling process, quality, rights, and known biases.
- Baseline non-ML rule and the minimum performance improvement that matters.
- Costs of false positives/negatives and required human oversight.

Potential future inputs may include validated tabular observations or outputs from a simulation. These are possibilities, not available data. Outputs and targets are task-dependent and must not be invented in advance.

## Method suitability

- **Supervised learning** requires representative examples with trustworthy labels/targets and a defined prediction objective.
- **Unsupervised learning** can explore grouping or structure without labels, but clusters do not automatically have useful meaning or establish scientific truth.
- **Rules, optimization, and simulation** may be better when behavior is governed by known equations, constraints, or transparent domain logic.
- Do not select a method until the task, data, baseline, and success metric are agreed.

## Data preparation and feature design

- Validate schema, types, missingness, duplicates, units, coordinate/time conventions, and source quality first.
- Split before fitting learned preprocessing steps. Fit imputers, scalers, encoders, feature selection, and similar transforms on training data only; apply the fitted transform to validation/test data.
- Keep missingness explicit and document any imputation. Avoid treating sentinel values as measurements.
- Engineer features from domain reasoning and document units, derivations, and availability at prediction time.
- Avoid features that are post-outcome, identifiers that encode the target, or proxies that would not be available in real use.

## Evaluation and reproducibility

- Choose split strategy to reflect intended use: random split only when observations are independent and exchangeable; use time-based, group-based, or source-based splits where temporal, entity, or dataset leakage is possible.
- Keep a final test set untouched until model and decisions are fixed. Use validation or cross-validation for model selection. Ensure preprocessing is inside each training fold.
- Compare against a simple baseline. Report sample counts, split strategy, metric definitions, uncertainty where feasible, and subgroup/source performance where relevant.
- Match metrics to task and error costs: classification may use precision, recall, F1, ROC-AUC or PR-AUC; regression may use MAE, RMSE, and suitable scale-aware metrics. Accuracy alone is insufficient for imbalanced classes; R² alone is insufficient as a practical error measure. Select metrics before examining test results.
- Record dataset IDs/checksums, schema and preprocessing versions, code revision, dependency/environment versions, random seeds, model parameters, split assignments, and evaluation results.
- Check for overfitting through validation discipline, simpler baselines, learning curves or cross-validation where appropriate. Avoid repeated tuning against the final test set.

## Risks and limits

Risks include leakage through time/entity overlap or preprocessing, non-representative samples, label noise, selection bias, confounding, distribution shift, small samples, and misleading aggregate metrics. A model's output is not scientific validation or NASA certification. Communicate uncertainty and limits to end users if a model is eventually deployed.

## Readiness gate

Do not start training until the team has approved a specific use case, identified lawful and suitable data, defined a target and baseline, selected a leakage-safe evaluation design, and agreed on metrics and acceptable error. Revisit this document when those inputs exist.
