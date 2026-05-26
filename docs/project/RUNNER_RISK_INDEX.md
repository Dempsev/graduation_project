# Runner Risk Index

This index explains the remaining top-level `runners/` directory after the P4
archive pass.

Use `scripts/` for public Python commands. Treat `runners/` as MATLAB/COMSOL
launch material unless a file is clearly a CSV template.

## Remaining Runner Groups

| Group | Risk | Remaining examples | Why kept in `runners/` for now |
| --- | --- | --- | --- |
| Manifest templates | `SAFE` | `fourier_*_case_manifest.template.csv` | Input templates, no execution |
| Shape / Fourier batch wrappers | `COMSOL` | `run_shape_batch.m`, `run_fourier_screening_batch.m`, `run_fourier_hard_screening_batch.m`, `run_fourier_shape_overlay_batch.m` | MATLAB/COMSOL path assumptions still need normalization |
| Thesis physical export wrappers | `MATLAB` / `COMSOL` | `run_ch6_physical_figure_bundle_v1.m`, `run_export_*_mode_shapes_v1.m` | Figure export may touch MATLAB/COMSOL assets |
| Real COMSOL-in-loop GA wrappers | `REAL_GA` | `run_stage3_comsol_in_loop_*`, `run_stage3_a_then_comsol_in_loop_ga_v1.m`, `run_fourier_only_*` | Expensive optimization routes; keep visible but clearly risky |
| Stage4 validation wrappers | `COMSOL` | `run_stage4_validation_targetband_top6_v1.m`, `run_stage4_validation_targetband_v1.m`, `run_stage4_validation_*` | Final and comparison validation launches |
| Historical AB validation ladder | `COMSOL` | `run_stage4_validation_ab_v1.m` through `run_stage4_validation_ab_v11.m`, `run_stage4_validation_ab_ga_v1.m` | Baseline bridge runs; not public first path |

## Archived Runner Groups

The following runner families moved to `archive/legacy_runners/`:

- `stage1_stage2/`: early shape and stage-2 screening launchers.
- `stage3_training/`: version-ladder dataset, model, scoring, and manifest
  launchers.
- `plotting/`: older target-band plotting launchers now superseded by
  `scripts/make_figures/`.
- `pilot_scripts/`: small exploratory local launchers.
- `shared_matlab_v11/`: V11 freeze helper launchers kept for traceability.

## Public Alternatives

| Need | Public location |
| --- | --- |
| Build target-band datasets | `scripts/build_dataset/` |
| Train target-band predictors | `scripts/train_prediction/` |
| Score/refine/export target-band validation manifests | `scripts/run_ga/` |
| Launch final COMSOL/real-GA wrappers | `scripts/run_comsol/` |
| Build thesis figures and reports from existing outputs | `scripts/make_figures/` |
| Check public layout without COMSOL | `scripts/check_project/check_public_layout.py` |

## Rule For Future Moves

Before moving a remaining MATLAB/COMSOL runner, update the wrapper path,
`addpath` behavior, and documentation together. Anything that can start COMSOL
must stay listed in `docs/project/COMSOL_SCRIPT_INDEX.md`.
