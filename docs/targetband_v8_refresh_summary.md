# Target-Band V8 Refresh Summary

## Scope

This note captures the first full refresh after folding the `exploratory v2` weak-band search back into the target-band learning pipeline.

The update includes:

- harvesting `comsol_in_loop_band_supplement_exploratory_v2`
- building `windows_dense_v8_truth_plus_exploratory_aug_v1`
- retraining the agreed main model pair
  - classifier: random forest
  - regressor: hist-gradient-boosting
- selecting representative inverse-design candidates from the exploratory run

## Dataset Update

Main dataset:

- `data/prediction_targetband_param_v1/v1/windows_dense_v8_truth_plus_exploratory_aug_v1/targetband_parametric_v1.csv`

Dataset summary:

- rows: `45536`
- unique designs: `2471`
- unique families: `81`

Compared with `v7`, `v8` mainly adds the new weak-band truth assets harvested from:

- `data/comsol_batch/comsol_in_loop_band_supplement_exploratory_v2/ga_history_v1.csv`

The new truth-asset fixed-window exports were written as:

- `data/prediction_targetband_v1/band140_180_truth_assets_v3`
- `data/prediction_targetband_v1/band160_200_truth_assets_v3`
- `data/prediction_targetband_v1/band180_220_truth_assets_v3`
- `data/prediction_targetband_v1/band200_240_truth_assets_v3`
- `data/prediction_targetband_v1/band220_260_truth_assets_v3`
- `data/prediction_targetband_v1/band240_280_truth_assets_v3`

## Main Model Results

### Classifier: RF

Family-CV:

- `v7`: `f1=0.9491`, `balanced_accuracy=0.9172`
- `v8`: `f1=0.9406`, `balanced_accuracy=0.9049`

Files:

- `data/prediction_targetband_param_v1_runs/param_targetband_cls_rf_dense_v7_cmp_v1/stratified_group_kfold/metrics_summary.json`
- `data/prediction_targetband_param_v1_runs/param_targetband_cls_rf_dense_v8_cmp_v1/stratified_group_kfold/metrics_summary.json`

Leave-one-band:

- `v7`: `f1=0.7595`, `balanced_accuracy=0.7580`
- `v8`: `f1=0.7600`, `balanced_accuracy=0.7455`

Files:

- `data/prediction_targetband_param_v1_runs/param_targetband_cls_rf_dense_v7_cmp_v1/leave_one_band_tag_out/metrics_summary.json`
- `data/prediction_targetband_param_v1_runs/param_targetband_cls_rf_dense_v8_cmp_v1/leave_one_band_tag_out/metrics_summary.json`

Interpretation:

- classifier quality stayed broadly stable after adding the exploratory truth
- `v8` is slightly harder overall, so the small family-CV drop is acceptable
- the more important point is that weak-band classification did not collapse after the dataset became more realistic

### Regressor: HGB

Family-CV:

- `v7`: `mae=0.0461`, `r2=0.8670`
- `v8`: `mae=0.0513`, `r2=0.8774`

Files:

- `data/prediction_targetband_param_v1_runs/param_targetband_cover_hgb_dense_v7_cmp_v1/stratified_group_kfold/metrics_summary.json`
- `data/prediction_targetband_param_v1_runs/param_targetband_cover_hgb_dense_v8_cmp_v1/stratified_group_kfold/metrics_summary.json`

Leave-one-band:

- `v7`: `mae=0.0870`, `r2=0.6735`
- `v8`: `mae=0.1044`, `r2=0.5908`

Files:

- `data/prediction_targetband_param_v1_runs/param_targetband_cover_hgb_dense_v7_cmp_v1/leave_one_band_tag_out/metrics_summary.json`
- `data/prediction_targetband_param_v1_runs/param_targetband_cover_hgb_dense_v8_cmp_v1/leave_one_band_tag_out/metrics_summary.json`

Interpretation:

- on family-CV, the regressor improved slightly in `r2`, which is encouraging given the harder `v8` distribution
- on leave-one-band, performance is mixed and remains the hardest part of the project
- this still supports our current wording strategy:
  - emphasize catalog-internal conditional prediction and inverse design as the main claim
  - mention unseen-band extrapolation only when the per-band evidence is clearly strong

## Weak-Band Readout

The most useful view is the weak-band, leave-one-band behavior after the exploratory truth was added.

Representative classifier changes:

- `band200_240`
  - `v7`: `f1=0.0108`, `bal_acc=0.4214`
  - `v8`: `f1=0.0166`, `bal_acc=0.5976`
- `band200_240_truth_assets`
  - `v7 truth_assets_v2`: `f1=0.4830`, `bal_acc=0.6567`
  - `v8 truth_assets_v3`: `f1=0.6600`, `bal_acc=0.6497`
- `band220_260`
  - `v7`: `f1=0.4560`, `bal_acc=0.5561`
  - `v8`: `f1=0.6890`, `bal_acc=0.5826`
- `band240_280`
  - `v7`: `f1=0.1701`, `bal_acc=0.5465`
  - `v8`: `f1=0.2311`, `bal_acc=0.5653`

Representative regressor changes:

- `band200_240_truth_assets`
  - `v7 truth_assets_v2`: `mae=0.1037`, `r2=0.6816`
  - `v8 truth_assets_v3`: `mae=0.1570`, `r2=0.5543`
- `band220_260_truth_assets`
  - `v7 truth_assets_v2`: `mae=0.0446`, `r2=0.2235`
  - `v8 truth_assets_v3`: `mae=0.1042`, `r2=0.5865`
- `band240_280_truth_assets`
  - `v7 truth_assets_v2`: `mae=0.0224`, `r2=-4.5083`
  - `v8 truth_assets_v3`: `mae=0.0676`, `r2=-0.2903`

Takeaway:

- the exploratory weak-band truth clearly helped the classifier side for the hardest bands
- the regressor now sees a much broader and harsher distribution, so not every raw metric goes up
- however, weak-band coverage and inverse-design usefulness improved enough to justify keeping `v8` as the new main dataset

## Representative Inverse-Design Cases

These candidates come from:

- `data/comsol_batch/comsol_in_loop_band_supplement_exploratory_v2/ga_band_catalog_summary_v1.csv`

### Case A: `band200_240`

- shape: `ep193_step51_contour_xy`
- cover ratio: `1.0000`
- overlap: `40.00 Hz`
- gap edges: `197.87 Hz -> 259.61 Hz`
- gap width: `61.73 Hz`

### Case B: `band220_260`

- shape: `ep253_step54_contour_xy`
- cover ratio: `1.0000`
- overlap: `40.00 Hz`
- gap edges: `208.43 Hz -> 275.93 Hz`
- gap width: `67.49 Hz`

### Case C: `band240_280`

- shape: `ep253_step54_contour_xy`
- cover ratio: `0.8982`
- overlap: `35.93 Hz`
- gap edges: `208.43 Hz -> 275.93 Hz`
- gap width: `67.49 Hz`

### Case D: `band180_220`

- shape: `ep248_step27_contour_xy`
- cover ratio: `1.0000`
- overlap: `40.00 Hz`
- gap edges: `179.77 Hz -> 226.44 Hz`
- gap width: `46.67 Hz`

## Current Position

The project is now in a stronger place than before the exploratory supplement run:

- weak-band search is no longer trapped in the old `gap34 / 200Hz` basin
- shape selection is now band-aware instead of only `gap34_gain`-aware
- the new truth has been folded back into the learning pipeline
- `v8` should be treated as the current main training dataset

Recommended mainline after this refresh:

- dataset: `windows_dense_v8_truth_plus_exploratory_aug_v1`
- classifier: RF
- regressor: HGB
- inverse-design workflow:
  1. specify target band
  2. RF screens for likely-open candidates
  3. HGB ranks by predicted cover ratio
  4. real COMSOL optimization/refinement validates and fine-tunes the shortlist
