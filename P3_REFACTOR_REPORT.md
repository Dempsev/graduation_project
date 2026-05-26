# P3 Refactor Report

## Scope

P3 starts the source/script structure refactor without moving MATLAB-heavy core
folders yet. The goal is to expose a clean public command surface while keeping
existing generated evidence paths stable.

## Completed

1. Created the target `src/` layout:
   - `src/geometry/`
   - `src/comsol_pipeline/`
   - `src/dataset/`
   - `src/prediction/`
   - `src/optimization/`
   - `src/validation/`
   - `src/plotting/`
   - `src/shared/`

2. Moved the shared contract/helper package:
   - `shared/` -> `src/shared/`
   - added root compatibility shim `shared/__init__.py`

3. Added public script wrappers under `scripts/make_figures/`:
   - `scripts/make_figures/ch2/build_ch2_typical_stats_v1.py`
   - `scripts/make_figures/ch2/build_ch2_reliability_stats_v1.py`
   - `scripts/make_figures/ch3/build_ch3_predictor_v12_report.py`
   - `scripts/make_figures/ch4/build_ch4_ga_real_optimization_assets_20gen.py`
   - `scripts/make_figures/ch5/build_ch5_prediction_vs_ga_v12.py`
   - `scripts/make_figures/ch5/build_ch5_strict_holdout_validation_v1.py`
   - `scripts/make_figures/ch5/build_fourier_only_ablation_v1.py`
   - `scripts/make_figures/postprocess/plot_bandgap_summary.py`

4. Kept generated evidence under existing roots:
   - `research_validation/`
   - `data/`
   - `output/`

5. Archived obvious one-off local material:
   - `test_two_matlab.py` -> `archive/oneoff_thesis_scripts/test_two_matlab.py`
   - `tools/` -> `archive/oneoff_thesis_scripts/tools/`

6. Updated public documentation:
   - `docs/project/PROJECT_STRUCTURE.md`
   - `docs/project/COMSOL_SCRIPT_INDEX.md`
   - `archive/ARCHIVE_NOTES.md`
   - `README.md`
   - `README_CN.md`

7. Moved the final target-band prediction stack:
   - `prediction_targetband_param_v1/` -> `src/prediction/targetband_param/`
   - added root compatibility shim `prediction_targetband_param_v1/__init__.py`
   - updated package-root path discovery from the old directory depth to the
     new `src/` layout

8. Added public prediction/data/result wrappers:
   - `scripts/build_dataset/build_parametric_targetband_dataset_v1.py`
   - `scripts/train_prediction/train_parametric_targetband_classifier_v1.py`
   - `scripts/train_prediction/train_parametric_targetband_regressor_v1.py`
   - `scripts/export_results/build_curated_application_bundle_v1.py`
   - `scripts/export_results/build_thesis_application_bundle_v1.py`

9. Moved the pure-Python target-band seed-ranking stack:
   - `optimization/seed_ranking/` -> `src/optimization/seed_ranking/`
   - added root compatibility shim `optimization/seed_ranking/__init__.py`
   - exposed public wrappers under `scripts/run_ga/`

## Why Core MATLAB/Python Modules Were Not Moved Yet

The following folders still contain many relative path and MATLAB path
assumptions:

- `optimization/`
- `stage4_validation/`
- root `shared/` compatibility shim until all imports are migrated.
- `model_core/`
- `postprocess/`
- `research_validation/`

Moving them in one batch would make it harder to distinguish import failures
from real test failures. The public wrapper layer now exists, so the next
P3/P4 step can move one module family at a time.

## Next Recommended Moves

1. Move `optimization/real_comsol_ga/` after MATLAB runner paths are normalized.
2. Move `postprocess/` into `src/plotting/` once wrappers are stable.
3. Archive historical prediction and stage pipelines in P4.
