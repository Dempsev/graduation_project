## Prediction V2

This directory hosts a comparison-friendly second prediction line.

It keeps the original `prediction/` line intact and now covers:

1. aggregate repeated measurements at the design-point level
2. evaluate with stronger split protocols
3. add a tree-model baseline
4. add a second-wave enriched-feature forest baseline
5. add a third-wave HistGB + RF blend baseline

## Current Scope

- dataset:
  - `prediction_v2/dataset/build_pure_prediction_dataset_v2.py`
- model baseline:
  - `prediction_v2/models/train_histgb_regressor_v2.py`
  - `prediction_v2/models/train_rf_regressor_v2.py`
  - `prediction_v2/models/train_ensemble_regressor_v2.py`
- runners:
  - `prediction_v2/runners/run_build_dataset_v2.py`
  - `prediction_v2/runners/run_train_histgb_regressor_v2.py`
  - `prediction_v2/runners/run_train_rf_regressor_v2.py`
  - `prediction_v2/runners/run_train_ensemble_regressor_v2.py`

## Design Principles

- do not modify the original `prediction/` implementation
- deduplicate by design point (`shape_id + point_id`)
- keep the latest stage as the primary split label while averaging repeated truth values
- prefer robust cross-validation over a single optimistic split
- use `HistGradientBoostingRegressor` from `scikit-learn` as the first tree baseline
- add enriched harmonic / geometry features for the second-wave comparison
- blend first-wave and second-wave models with an inner validation-selected weight

## Recommended First Comparison

1. build the aggregated dataset
2. train `gap34_width_Hz` with:
   - `--eval-mode stratified_group_kfold --group-key shape_family`
3. train the same target with:
   - `--eval-mode leave_one_stage_out`
4. compare against the old `prediction/` results under the same target
5. compare first-wave `HistGB` against second-wave `RandomForest + enriched features`
6. compare the blended ensemble against both base models
