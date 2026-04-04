# Pure Prediction Branch

This directory isolates the prediction-only workflow from the existing optimization-oriented stage3 mainline.

## Scope

- Input: structure parameters plus geometry-only descriptors
- Output: direct bandgap targets such as `gap34_Hz`
- Metrics: `MAE`, `RMSE`, `R2`

This branch intentionally excludes:

- gain-based labels such as `gap34_gain_Hz`
- reference-relative labels such as `is_positive_shape`
- seed-discovery scoring
- shortlist / manifest logic
- GA refinement

## Scripts

- `build_pure_prediction_dataset_v1.py`
  Builds a clean prediction dataset from the unified physical truth already accumulated in the repository.
  In addition to the original area / perimeter style fields, this version derives geometry-only descriptors such as compactness, extent, radial statistics, and edge-length statistics.
- `train_pure_bandgap_regressor_v1.py`
  Trains a standalone MLP regressor for direct bandgap prediction.
- `train_pure_bandgap_twostage_v1.py`
  Trains a pure-prediction two-stage model:
  first classify whether the fixed `3-4` gap opens, then regress the positive width and combine them into an expected-width prediction.

## Inputs

- Structural parameters: `a1~a5`, `b1~b5`, `r0`
- Base geometry features: area, perimeter, bounding-box size, centroid, point count
- Extended geometry features: compactness, extent, radial mean / std / cv, edge-length mean / std / cv

These are all admissible prediction-side inputs because they are known once the structure is defined, before any optimization logic is applied.

## Outputs

- `gap34_Hz`
- `gap34_rel`
- `gap34_width_Hz`
- `gap34_width_rel`
- `gap34_is_open`
- `max_gap_Hz`
- `max_gap_rel`
- `max_gap_is_open`

`gap34_width_Hz` and `gap34_width_rel` are the clipped, physically cleaner forms of the fixed 3-4 target:

- if the raw fixed-gap value is positive, keep it
- if the raw fixed-gap value is negative, map it to `0`

This is often easier to explain to the advisor because a bandgap width is naturally nonnegative; negative raw values really mean "no valid fixed 3-4 gap opened".

## Split Modes

- `grouped`
  Randomly splits train / val / test while grouping by `shape_id` or `shape_family` to measure interpolation / family generalization.
- `stage_holdout`
  Uses earlier screening stages for train / val and leaves `stage4_validation*` as an external test set. This is the cleaner prediction-first protocol when you want to show the advisor that optimization-stage validation was not used during training.

## Loss

- Default loss: `huber`

The fixed-gap regression labels contain large-magnitude failures and stage-mixed distributions, so Huber loss is more robust than pure MSE for the prediction branch.

## Recommended Baseline

- dataset: `data/pure_prediction/v1/pure_bandgap_regression_v1.csv`
- feature preset: `pure_structural_extended`
- target: `gap34_width_rel` when you want the most stable normalized prediction target, or `gap34_width_Hz` when you want the physically clipped absolute width
- split mode: `grouped` for model development, `stage_holdout` for prediction-first external testing

This setup is meant to be the presentation-ready prediction task for the thesis split requested by the advisor.

## Recommended Upgrade

The fixed `3-4` target is zero-inflated:

- many early screening rows have no opened fixed gap, so `gap34_width_* = 0`
- later validation rows are mostly positive-gap confirmations

For that reason, the upgraded prediction line supports a two-stage pure-prediction view:

1. classify whether the fixed `3-4` gap opens (`gap34_is_open`)
2. regress the positive width only on opened-gap samples
3. combine them into an expected-width prediction

This is still a pure prediction task because both subproblems are forward prediction from known geometry + parameters; no optimization-side labels are involved.
