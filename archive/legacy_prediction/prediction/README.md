# Prediction

This directory is the task-oriented entry layer for the **model layer** of the project.

## Official Thesis Mainline

The official thesis-facing prediction line is the **frozen target-band conditional
prediction stack** inside the thesis band catalog.

Use it as:

- `structure + target band -> open probability + cover / overlap prediction`

The frozen reference stack is:

- thesis band catalog:
  - `prediction_targetband_param_v1/configs/thesis_band_catalog_v2.json`
- mainline freeze:
  - `prediction_targetband_param_v1/configs/targetband_mainline_freeze_v1.json`
- default dataset:
  - `data/prediction_targetband_param_v1/v1/windows_dense_v8_truth_plus_exploratory_aug_v1/targetband_parametric_v1.csv`
- classifier family:
  - `RF`
- regressor family:
  - `HGB`
- shape front-end:
  - `data/analysis/targetband_shape_atlas_v1/`

## Stable Entrypoints

The preferred thesis-facing prediction entrypoints are:

- `prediction_targetband_param_v1/runners/run_build_parametric_targetband_dataset_v1.py`
- `prediction_targetband_param_v1/runners/run_train_parametric_targetband_classifier_v1.py`
- `prediction_targetband_param_v1/runners/run_train_parametric_targetband_regressor_v1.py`
- `prediction_targetband_param_v1/runners/run_build_curated_application_bundle_v1.py`

## Baselines And Historical Bridge Lines

These prediction routes remain important, but they are not the default thesis mainline:

- `prediction/runners/run_build_dataset_v1.py`
- `prediction/runners/run_train_regressor_v1.py`
- `prediction/runners/run_train_twostage_v1.py`
- `prediction_v2/` to `prediction_v7/`
- `prediction_targetband_v1/`
- `stage3_prediction/`

Interpret them as:

- baseline modeling lines
- historical bridge code
- comparison anchors against the frozen target-band predictor

## Config Semantics

Use the following boundary when changing prediction behavior:

- `profile` / freeze:
  - thesis-band catalog, dataset freeze, and mainline modeling assumptions
- `policy`:
  - thresholds, ranking cutoffs, or selection rules used around the predictor
- `run config`:
  - CLI args, output roots, resume settings, and run-local overrides

Do not introduce a new top-level `vN` script when the only change is a policy or
run-config change.
