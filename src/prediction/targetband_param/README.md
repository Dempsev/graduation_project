# Parametric Target-Band Prediction V1

`src/prediction/targetband_param/` is the first conditional target-band line.
The root `prediction_targetband_param_v1/` package is retained only as a
compatibility shim for older imports.

It stacks several validated fixed windows into one dataset and appends the window definition as model input:

- `target_band_low_Hz`
- `target_band_high_Hz`
- `target_band_center_Hz`
- `target_band_width_Hz`

The intended use is a first-step approximation to frequency-conditioned screening:

- input: `structure + target frequency window`
- output: whether that window opens, and if it opens, how much is covered

This version is still constrained to the currently validated windows rather than arbitrary continuous ranges.

## Current Status

This line is no longer only an exploratory branch.

For the current thesis-facing mainline, the frozen default deployment is now:

- thesis band catalog: `src/prediction/targetband_param/configs/thesis_band_catalog_v2.json`
- default dataset: `windows_dense_v8_truth_plus_exploratory_aug_v1`
- classifier: RF
- regressor: HGB
- shape front-end: `data/analysis/targetband_shape_atlas_v1`

The line now supports a multi-scale window stack, including both:

- multiple center frequencies
- multiple window widths

This makes `target_band_width_Hz` a real condition variable rather than a constant placeholder.

The main score remains `family CV`, which measures generalization to unseen structure families under known target-band conditions.

To probe whether the model is approaching true continuous-band behavior, an auxiliary `leave_one_band_tag_out` evaluation is also used:

- strong results here would mean the model can extrapolate to an unseen validated window
- weak results mean it still relies on the discrete windows observed during training

## Recommended Deployment Pattern

This line now supports a two-layer integration pattern:

- internal training layer: use the dense multi-window grid
- external application layer: expose only a curated engineering-facing band catalog

This is intentional rather than contradictory:

- the dense grid improves conditional frequency learning
- the curated catalog keeps engineering output interpretable and easy to use

In practice this means:

1. train the conditional model on a richer dense grid
2. evaluate and package a smaller curated set of application-facing windows
3. report curated-band scores to users instead of the full internal training grid

## Current Freeze Reference

The current thesis-facing freeze is documented in:

- `docs/project/architecture/targetband_mainline_freeze_v1.md`
- `src/prediction/targetband_param/configs/targetband_mainline_freeze_v1.json`
