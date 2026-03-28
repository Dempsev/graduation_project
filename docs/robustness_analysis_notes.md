# Robustness Analysis Notes

## Goal

This module adds a pure post-processing analysis layer.

It does **not** change the current training or validation mainline.

The current scope is:

- add relative / normalized gap metrics on top of existing csv outputs
- analyze threshold-perturbation robustness from `seed_discovery_predictions.csv`
- analyze material-scenario robustness from one or more `validation_results.csv`
- export tables and figures that are directly usable in paper writing

## New Files

- `stage3_training/normalization_metrics.py`
- `stage3_training/run_robustness_analysis_v1.py`

## Supported Normalized Metrics

The helper adds normalization columns when the required source columns exist.

Examples:

- `gap34_Hz_over_ref_gap34_Hz`
- `gap34_gain_Hz_over_ref_gap34_Hz`
- `gap34_gain_Hz_pct_of_ref_gap34_Hz`
- `max_gap_Hz_over_ref_gap34_Hz`
- `<prediction_col>_over_stage1_reference_gap_Hz`
- `<metric>_zscore`
- `<metric>_robust_zscore`

This is intentionally additive.

Existing columns such as:

- `gap34_Hz`
- `gap34_gain_Hz`
- `gap34_rel`
- `gap34_gain_rel`

remain unchanged.

## Default Run

```bash
python stage3_training/run_robustness_analysis_v1.py
```

Default inputs:

- `data/ml_runs/candidate_pool_seed_discovery_v10/seed_discovery_predictions.csv`
- `data/comsol_batch/stage4_validation_ab_v10/stage4_validation_results.csv`

Default outputs:

- `data/ml_runs/robustness_analysis_v1/normalized_seed_discovery_predictions.csv`
- `data/ml_runs/robustness_analysis_v1/normalized_validation_results.csv`
- `data/ml_runs/robustness_analysis_v1/threshold_scenario_summary.csv`
- `data/ml_runs/robustness_analysis_v1/threshold_pairwise_stability.csv`
- `data/ml_runs/robustness_analysis_v1/material_scenario_summary.csv`
- `data/ml_runs/robustness_analysis_v1/material_pairwise_stability.csv`
- `data/ml_runs/robustness_analysis_v1/threshold_stability_overview.png`
- `data/ml_runs/robustness_analysis_v1/material_stability_overview.png`
- `data/ml_runs/robustness_analysis_v1/robustness_analysis_summary.json`

## What The Script Measures

### 1. Threshold perturbation robustness

Using existing `seed_discovery_predictions.csv`, the script perturbs:

- `contact_threshold`
- `positive_threshold`
- `contact_weight`
- `reg_min`

For each scenario it reports:

- ranking stability against baseline
- top-k overlap stability against baseline
- validation hit rate stability against baseline selections
- gate-count changes

Current ranking stability metrics:

- Spearman rank correlation
- top-k Jaccard overlap
- top-k overlap count

Current validation stability metrics:

- validated selected count
- validated coverage rate
- validated positive hit count
- validated positive hit rate

### 2. Material-scenario robustness

This part compares one or more `validation_results.csv` files.

The baseline scenario is always the `--validation-csv` file.

Additional scenarios can be passed with:

```bash
python stage3_training/run_robustness_analysis_v1.py \
  --material-scenario baseline_alt=data/comsol_batch/stage4_validation_ab_v10_alt_material/stage4_validation_results.csv \
  --material-scenario baseline_alt2=data/comsol_batch/stage4_validation_ab_v10_alt_material_2/stage4_validation_results.csv
```

For each material scenario it reports:

- mean / median / best objective value
- top-k positive hit rate
- pairwise rank correlation between scenarios
- pairwise top-k overlap between scenarios

## Objective Switch Support

The script currently supports these observed-objective views:

- `gap34_gain_Hz`
- `gap34_Hz`
- `gap34_rel`
- `gap34_gain_rel`
- `max_gap_Hz`
- `gap34_gain_Hz_over_ref`
- `gap34_Hz_over_ref`
- `max_gap_Hz_over_ref`

Example:

```bash
python stage3_training/run_robustness_analysis_v1.py --objective gap34_Hz_over_ref
```

This changes the observed objective used in the validation/material robustness summary.

## Current Design Boundary

This module is intentionally post-hoc only.

It does **not**:

- retrain surrogate models
- rewrite the stage3 scoring pipeline
- regenerate COMSOL validation manifests
- automatically run material perturbation simulations

Instead, it reuses files that already exist and adds analysis on top.

## Recommended Use

### Paper-ready threshold robustness

Use the default command first.

This gives:

- normalized prediction / validation tables
- threshold sensitivity tables
- threshold sensitivity figure

### Paper-ready material robustness

After you have produced validation results under multiple material settings,
run the script again with multiple `--material-scenario` inputs.

This gives:

- cross-material objective summary table
- cross-material pairwise stability table
- material stability figure

## TODO

Reasonable next extensions, if needed later:

- add Kendall tau when an extra dependency is acceptable
- add experiment-config json support for robustness runs
- add direct merge with the experiment scaffold outputs
- add profile-aware automatic discovery of multiple material validation runs
