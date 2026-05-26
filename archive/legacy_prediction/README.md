# Legacy Prediction Routes

This folder holds historical prediction lines that are no longer the public
mainline:

- `prediction/`
- `prediction_targetband_v1/`
- `prediction_v2/` through `prediction_v7/`

The final thesis-facing prediction workflow lives in
`src/prediction/targetband_param/`. Small root-level compatibility packages are
kept for older imports, especially the `prediction_v3` feature helpers still
used by the target-band inference code.
