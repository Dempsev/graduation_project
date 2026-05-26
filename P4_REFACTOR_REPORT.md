# P4 Refactor Report

## Scope

P4 starts the public-repository slimming pass. The goal is to move historical
routes out of the first-view source tree while preserving compatibility for
imports that still support the final thesis workflow.

## Completed

1. Archived historical prediction routes:
   - `prediction/` -> `archive/legacy_prediction/prediction/`
   - `prediction_targetband_v1/` -> `archive/legacy_prediction/prediction_targetband_v1/`
   - `prediction_v2/` through `prediction_v7/` -> `archive/legacy_prediction/`

2. Added root compatibility packages for archived prediction imports:
   - `prediction/`
   - `prediction_targetband_v1/`
   - `prediction_v2/` through `prediction_v7/`

3. Archived baseline notes:
   - `baselines/` -> `archive/baselines/`

4. Archived obvious legacy top-level runners:
   - `archive/legacy_runners/stage1_stage2/`
   - `archive/legacy_runners/stage3_training/`
   - `archive/legacy_runners/plotting/`
   - `archive/legacy_runners/pilot_scripts/`
   - `archive/legacy_runners/shared_matlab_v11/`

5. Preserved the remaining `runners/` MATLAB/COMSOL wrappers in place for now.

6. Added `docs/project/RUNNER_RISK_INDEX.md` to classify the remaining
   top-level `runners/` files by execution risk.

7. Archived unused stage3 route folders:
   - `stage3_autoresearch/`
   - `stage3_optimization/`
   - `stage3_optimization_real_ga/`
   - `stage3_prediction/`

## Why Some Historical Folders Are Still In Place

The following folders still support current compatibility imports, smoke tests,
or MATLAB/COMSOL execution paths:

- `stage3_training/`
- `stage3_dataset/`
- `stage2_harmonics/`
- `stage2_harmonics_refine/`
- `stage4_validation/`
- `optimization/real_comsol_ga/`
- remaining COMSOL-facing files in `runners/`

Moving these safely requires MATLAB path normalization or dedicated public
wrappers first.

## Current Verification

Safe checks after this pass:

```powershell
python scripts\check_project\check_public_layout.py
python -m unittest tests.test_thesis_mainline_smoke
```
