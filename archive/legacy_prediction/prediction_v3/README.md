`prediction_v3/` is the tail-aware pure prediction line.

It extends `prediction_v2/` in two directions:

- adds local contour descriptors from `data/shape_contours`
- trains a main regressor plus a large-width specialist uplift head

Typical commands:

```bash
python prediction_v3/runners/run_build_dataset_v3.py
python prediction_v3/runners/run_train_tail_specialist_regressor_v3.py --target gap34_width_Hz --eval-mode stratified_group_kfold --group-key shape_family --run-name gap34width_family_v3
python prediction_v3/runners/run_train_tail_specialist_regressor_v3.py --target gap34_width_Hz --eval-mode leave_one_stage_out --run-name gap34width_stage_v3 --min-stage-rows 10
```
