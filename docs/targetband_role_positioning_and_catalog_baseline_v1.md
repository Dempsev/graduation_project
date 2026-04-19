# Target-Band Lines Positioning And Catalog Baseline Notes

## 1. Role Positioning Table

| Line | Primary role | Secondary role | Current status | How to talk about it |
| --- | --- | --- | --- | --- |
| `pure_prediction_v7` | Legacy global bandgap predictor baseline | Historical comparison point | Completed baseline | Structural-only prediction of overall gap quality, not target-band inverse design |
| `prediction_targetband_param_v1` | Main conditional predictor for thesis target bands | Drives target-band scoring and candidate ranking | Main modeling line | `structure + target band -> open probability / cover ratio` |
| `targetband local GA + COMSOL validation` | Prediction-driven inverse-design prototype | Teacher-facing proof that conditional prediction can propose physically valid target-band candidates | Prototype completed and validated on `180-220 Hz` | Prediction-guided local refinement and shortlist validation |
| `band-catalog real GA` | Real-COMSOL target-band search baseline | Historical truth asset source after harvesting | Baseline completed to `14` generations before plateau stop | Direct target-band global search without prediction; used to compare against prediction-driven search |
| `band-supplement GA` | Targeted weak-band data supplementation | Conservative supplementation baseline | Running / conservative version | Weak-band-oriented truth production, not final predictor baseline |
| `stage2_gapdiversity_exploration_v1` | Exploratory truth production outside the legacy `3-4`-dominant basin | Major source of new target-band labels | High-value supplementation asset | Wide-coverage exploratory data rather than optimization baseline |
| `true global GA (gap34)` | Legacy strongest baseline for “maximize overall gap” | Historical truth asset source | Completed | Useful for maximum-gap comparison, but not the right main baseline for target-band inverse design |

## 2. Main Narrative Going Forward

The mainline should now be described as:

1. Build and expand a finite thesis band catalog instead of claiming arbitrary continuous-band generalization.
2. Train conditional target-band predictors on all reusable truth assets.
3. Use prediction-driven search as the main inverse-design line.
4. Use real-COMSOL target-band search as the baseline comparison line.
5. Use weak-band supplementation lines to fill coverage gaps in the catalog.

This means:

- We do **not** need to overclaim “fully unseen-band extrapolation”.
- We **can** say that the system targets conditional prediction and inverse design **within the thesis band catalog**.
- If later leave-one-band behavior improves, that can be presented as an additional generalization bonus rather than the core claim.

## 3. What Was Recovered From Band-Catalog GA

Historical truth assets were harvested with:

- `prediction_targetband_v1/dataset/build_truth_asset_targetband_dataset_v1.py`

Outputs were folded into:

- `data/prediction_targetband_v1/band140_180_truth_assets_v1/`
- `data/prediction_targetband_v1/band160_200_truth_assets_v1/`
- `data/prediction_targetband_v1/band180_220_truth_assets_v1/`
- `data/prediction_targetband_v1/band200_240_truth_assets_v1/`
- `data/prediction_targetband_v1/band220_260_truth_assets_v1/`
- `data/prediction_targetband_v1/band240_280_truth_assets_v1/`
- `data/prediction_targetband_param_v1/v1/windows_dense_v6_truth_assets_aug_v1/`

The harvested truth pool contains four sources:

- `comsol_in_loop_true_global_ga_v1`
- `comsol_in_loop_band_catalog_ga_v1`
- `stage4_validation_targetband_v1`
- `stage4_validation_targetband_top6_v1`

For each thesis band, the harvested training-ready rows contributed by `band-catalog GA` are:

- `139` rows per band

This means band-catalog GA has already been absorbed as reusable truth and does not need to be justified only by its optimization performance.

Examples of positive-label contribution inside harvested truth assets:

- `band180_220_truth_assets_v1`: band-catalog GA contributed `65 / 139` positive rows
- `band200_240_truth_assets_v1`: band-catalog GA contributed only `5 / 139` positive rows

This contrast is important: the line is much more useful as a mid-band baseline than as a weak-band data engine.

## 4. What The 14-Generation Band-Catalog GA Actually Achieved

Source files:

- `data/comsol_batch/comsol_in_loop_band_catalog_ga_v1/ga_generation_summary_v1.csv`
- `data/comsol_batch/comsol_in_loop_band_catalog_ga_v1/ga_band_catalog_summary_v1.csv`
- `data/comsol_batch/comsol_in_loop_band_catalog_ga_v1/ga_band_catalog_best_candidates_v1.csv`

The run stopped by plateau:

- `stop_reason = plateau_after_gen_14`
- best global fitness was reached earlier and later generations did not exceed the configured improvement threshold

Best per-band results:

| Band | Best cover ratio | Best overlap (Hz) | Best generation | Best shape |
| --- | ---: | ---: | ---: | --- |
| `140-180` | `0.4621` | `18.48` | `3` | `ep252_step21_contour_xy` |
| `160-200` | `0.7748` | `30.99` | `8` | `ep205_step69_contour_xy` |
| `180-220` | `0.7222` | `28.89` | `1` | `ep205_step69_contour_xy` |
| `200-240` | `0.2964` | `11.86` | `1` | `ep205_step69_contour_xy` |

## 5. What It Means As A Baseline For Target-Band Prediction

As a baseline against the prediction-driven line, the old band-catalog GA shows:

1. Direct real-COMSOL target-band search can work well for easier mid bands.
   - `160-200` is the clearest success case.

2. It does **not** automatically solve weak-band coverage.
   - `200-240` remained weak.
   - The best `200-240` candidate was already present at generation `1`, which suggests the run did not discover a stronger weak-band basin later.

3. The run quickly concentrated around a small set of already-strong families.
   - `ep205` dominated multiple bands.
   - This is useful as a baseline, but weak as a supplementation strategy.

4. Therefore, the old band-catalog GA supports the motivation for the prediction-driven and supplementation lines rather than replacing them.

In thesis language, it can be framed as:

- A **real-search baseline** for conditional target-band design
- A proof that direct search can already solve some mid-band tasks
- A negative result for weak-band coverage, showing why targeted data supplementation and conditional prediction remain necessary

## 6. Practical Conclusion

The old band-catalog GA should now be used in three ways:

1. As a baseline comparison line against target-band prediction-driven search.
2. As a harvested truth asset source that has already been folded into the new training set.
3. As evidence that weak bands such as `200-240` are still not well served by direct search under the current conservative setup.

It should **not** be treated as the main weak-band supplementation engine going forward.
