# Thesis Runbook

## Purpose

This runbook turns the frozen target-band thesis mainline into a compact,
appendix-ready command list.

It does **not** replace the broader architecture notes in
`docs/THESIS_MAINLINE.md`. It exists so that a reader can answer:

- what to run
- in what order
- with which explicit frozen arguments
- which output directory is authoritative

Use `docs/THESIS_METHOD_MAP.md` when you want the thesis wording and code
entrypoints side by side.

All commands below assume the working directory is the repository root:

```powershell
Set-Location D:\graduation_project\coad
```

## 1. Build The Frozen Target-Band Dataset

```powershell
python prediction_targetband_param_v1\runners\run_build_parametric_targetband_dataset_v1.py `
  --dataset-tags band140_180,band160_200,band180_220,band200_240,band220_260,band240_280 `
  --out-tag windows_dense_v8_truth_plus_exploratory_aug_v1
```

Authoritative output:

- `data/prediction_targetband_param_v1/v1/windows_dense_v8_truth_plus_exploratory_aug_v1/targetband_parametric_v1.csv`

## 2. Train The Frozen Classifier

```powershell
python prediction_targetband_param_v1\runners\run_train_parametric_targetband_classifier_v1.py `
  --dataset data/prediction_targetband_param_v1/v1/windows_dense_v8_truth_plus_exploratory_aug_v1/targetband_parametric_v1.csv `
  --model-family random_forest `
  --eval-mode stratified_group_kfold `
  --group-key shape_family `
  --run-name param_targetband_cls_rf_dense_v8_cmp_v1
```

Authoritative output root:

- `data/prediction_targetband_param_v1_runs/param_targetband_cls_rf_dense_v8_cmp_v1/stratified_group_kfold/`

## 3. Train The Frozen Regressor

```powershell
python prediction_targetband_param_v1\runners\run_train_parametric_targetband_regressor_v1.py `
  --dataset data/prediction_targetband_param_v1/v1/windows_dense_v8_truth_plus_exploratory_aug_v1/targetband_parametric_v1.csv `
  --model-family hist_gradient_boosting `
  --eval-mode stratified_group_kfold `
  --group-key shape_family `
  --run-name param_targetband_cover_hgb_dense_v8_cmp_v1
```

Authoritative output root:

- `data/prediction_targetband_param_v1_runs/param_targetband_cover_hgb_dense_v8_cmp_v1/stratified_group_kfold/`

## 4. Score Target-Band Candidates

The frozen showcase band is `180-220 Hz`.

```powershell
python optimization\runners\run_targetband_seed_scoring_v1.py `
  --dataset data/ml_dataset/v12/candidate_pool_optimization_v1/candidate_pool_optimization_v1.csv `
  --classifier-run-root data/prediction_targetband_param_v1_runs/param_targetband_cls_rf_dense_v8_cmp_v1/stratified_group_kfold `
  --regressor-run-root data/prediction_targetband_param_v1_runs/param_targetband_cover_hgb_dense_v8_cmp_v1/stratified_group_kfold `
  --band-low 180 `
  --band-high 220 `
  --run-name targetband_seed_scoring_v1
```

Authoritative output:

- `data/ml_runs/targetband_seed_scoring_v1/band180_220/targetband_seed_predictions.csv`

## 5. Run Local Target-Band Refinement

```powershell
python optimization\runners\run_targetband_local_ga_v1.py `
  --scored-csv data/ml_runs/targetband_seed_scoring_v1/band180_220/targetband_seed_predictions.csv `
  --classifier-run-root data/prediction_targetband_param_v1_runs/param_targetband_cls_rf_dense_v8_cmp_v1/stratified_group_kfold `
  --regressor-run-root data/prediction_targetband_param_v1_runs/param_targetband_cover_hgb_dense_v8_cmp_v1/stratified_group_kfold `
  --band-low 180 `
  --band-high 220 `
  --only-point-id rf09_h00_center
```

Authoritative output root:

- `data/ml_runs/targetband_local_ga_v1/band180_220/`

Key artifact:

- `data/ml_runs/targetband_local_ga_v1/band180_220/targetband_ga_candidate_manifest_v1.csv`

## 6. Build The Stage4 Validation Manifest

```powershell
python optimization\runners\run_targetband_validation_manifest_v1.py `
  --ga-csv data/ml_runs/targetband_local_ga_v1/band180_220/targetband_ga_candidate_manifest_v1.csv `
  --out-dir data/ml_runs/targetband_local_ga_v1/band180_220/validation_manifest_v1 `
  --total-k 6 `
  --per-shape-k 2
```

Authoritative output:

- `data/ml_runs/targetband_local_ga_v1/band180_220/validation_manifest_v1/targetband_ga_validation_manifest_v1.csv`

This manifest is now checked by the shared contract:

- `shared/contracts/stage4_validation_manifest_contract_v1.json`

## 7. Launch Real Validation

```matlab
run(fullfile(pwd, 'runners', 'run_stage4_validation_targetband_v1.m'));
```

Primary output root:

- `data/comsol_batch/stage4_validation_targetband_v1/`

## 7A. MATLAB Preflight Only

Run this first if you want to confirm that the manifest contract, paths, and
MATLAB-side loader are consistent before COMSOL work begins:

```matlab
manifestPath = fullfile(pwd, 'data', 'ml_runs', 'targetband_local_ga_v1', ...
    'band180_220', 'validation_manifest_v1', ...
    'targetband_ga_validation_manifest_v1.csv');
contractPath = fullfile(pwd, 'shared', 'contracts', ...
    'stage4_validation_manifest_contract_v1.json');
manifestTable = readtable(manifestPath);
validate_stage4_validation_manifest_contract_v1(manifestTable, manifestPath, contractPath);
disp('Stage4 manifest preflight passed.');
```

## 7B. MATLAB Small-Batch Validation

If the preflight passes, run a very small batch before the full stage4 job:

```matlab
cfg = get_stage4_validation_config_targetband_v1();
run_stage4_validation_from_manifest(cfg, 1, 2);
```

This runs rows `1:2` from the manifest and writes the same output family under:

- `data/comsol_batch/stage4_validation_targetband_v1/`

## 7C. MATLAB Full Validation

After the small-batch sanity check succeeds, run the normal wrapper:

```matlab
run(fullfile(pwd, 'runners', 'run_stage4_validation_targetband_v1.m'));
```

This is equivalent to:

```matlab
cfg = get_stage4_validation_config_targetband_v1();
run_stage4_validation_from_manifest(cfg, 1, 0);
```

Expected stage4 artifacts include:

- `data/comsol_batch/stage4_validation_targetband_v1/stage4_validation_results.csv`
- `data/comsol_batch/stage4_validation_targetband_v1/stage4_validation_point_summary.csv`
- `data/comsol_batch/stage4_validation_targetband_v1/stage4_validation_shape_summary.csv`

## 8. Build The Thesis-Facing Application Bundle

```powershell
python prediction_targetband_param_v1\runners\run_build_thesis_application_bundle_v1.py
```

Authoritative output root:

- `data/prediction_targetband_param_v1_app/v1/thesis_band_catalog_v2_bundle_v1/`

Note:

- family-level frozen RF/HGB metrics are treated as authoritative
- missing band leave-one-out metrics are allowed to remain `NaN` for thesis bands not fully covered by the older secondary reference runs

## Output Map

Use this interpretation in the thesis appendix:

- truth assets:
  - `data/comsol_batch/`
- processed target-band datasets:
  - `data/prediction_targetband_param_v1/`
- frozen conditional model runs:
  - `data/prediction_targetband_param_v1_runs/`
- candidate scoring and local refinement:
  - `data/ml_runs/targetband_seed_scoring_v1/`
  - `data/ml_runs/targetband_local_ga_v1/`
- thesis-facing serving bundle:
  - `data/prediction_targetband_param_v1_app/v1/thesis_band_catalog_v2_bundle_v1/`
