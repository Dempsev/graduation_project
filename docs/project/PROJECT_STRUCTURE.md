# Project Structure

This repository is being reorganized from a graduation-project workbench into a
public research project. The final public story is not the full historical
stage tree. It is the thesis workflow:

```text
COMSOL dispersion truth
-> target-band conditional prediction
-> real COMSOL-in-loop GA
-> predictor Top5 / random / GA comparison
-> high-frequency weak-band boundary analysis
```

## Public Layout Under Construction

```text
coad/
  configs/                  Shared experiment and local-environment examples
  docs/
    project/                Project architecture and script-risk indexes
    thesis/                 Thesis-facing method and wording maps
    reproducibility/        Final runbook, result indexes, data manifests
    archive/                Draft notes and historical explanation
  src/                      Final public source layout, created in P3
  scripts/                  Final public command entrypoints, created in P3
  tests/                    Lightweight checks
  archive/                  Historical routes and one-off scripts
```

P2 moved the documentation and result indexes first. P3 is moving the final
thesis source paths behind public wrappers, while keeping small compatibility
shims for older imports.

P3 update: `src/` now exists as the target module layout. The final
target-band prediction package has moved to
`src/prediction/targetband_param/`, and `scripts/` contains public wrappers for
dataset building, model training, result export, and final thesis figures.
The target-band Python optimization entrypoints are also exposed under
`scripts/run_ga/`; MATLAB/COMSOL-heavy implementation folders remain in place
until their path assumptions are normalized.

## Current Mainline Folders

| Current folder | Role in the final thesis workflow | Future home |
| --- | --- | --- |
| `model_core/` | MATLAB helpers that construct and solve COMSOL models | `src/comsol_pipeline/model_core/` |
| `physics_pipeline/` | Truth-layer overview and reading entry | `src/comsol_pipeline/overview/` |
| `snake/` | Snake-inspired topology generation | `src/geometry/snake/` |
| `preprocess/` | Geometry and data preprocessing utilities | `src/geometry/` and `src/dataset/` |
| `src/prediction/targetband_param/` | Final target-band conditional prediction stack | Moved in P3; root `prediction_targetband_param_v1/` is a compatibility shim |
| `optimization/real_comsol_ga/` | Real COMSOL-in-loop GA used as optimization baseline | `src/optimization/real_comsol_ga/` |
| `src/optimization/seed_ranking/` | Candidate-pool construction, ranking, validation manifests | Moved in P3; root `optimization/seed_ranking/` is a compatibility shim |
| `stage4_validation/` | Shared COMSOL validation configs | `src/validation/stage4/` |
| `postprocess/` | Plotting, export, and thesis figure helpers | `src/plotting/` and `scripts/make_figures/` |
| `research_validation/` | Final chapter-specific evidence bundles | `docs/reproducibility/` and `scripts/make_figures/` |
| `src/shared/` | Contracts, shared IO, and helper utilities | Moved in P3; root `shared/` is a compatibility shim |

## Historical Folders

These folders explain how the project evolved but should not dominate the
public mainline:

- `archive/legacy_prediction/prediction/`,
  `archive/legacy_prediction/prediction_targetband_v1/`,
  `archive/legacy_prediction/prediction_v2/` ...
  `archive/legacy_prediction/prediction_v7/`
- `stage1/`, `stage2/`, selected `stage2_*`, and retained
  `stage3_training/` / `stage3_dataset/`
- `archive/legacy_stage_pipelines/stage3_autoresearch/`
- `archive/legacy_stage_pipelines/stage3_optimization/`
- `archive/legacy_stage_pipelines/stage3_optimization_real_ga/`
- `archive/legacy_stage_pipelines/stage3_prediction/`
- most version-ladder wrappers in `archive/legacy_runners/`
- `archive/baselines/`

The legacy prediction family has already moved to `archive/legacy_prediction/`
with root-level import shims. Many old stage and plotting wrappers have moved
to `archive/legacy_runners/`, and unused stage3 route folders have moved to
`archive/legacy_stage_pipelines/`. Remaining MATLAB/COMSOL runners stay in
`runners/` until their risk classification and path behavior are explicit. See
`docs/project/RUNNER_RISK_INDEX.md` for the current remaining-runner
classification.

## Generated Artifacts

The public repository should not track the full generated payload:

- `data/`: COMSOL outputs, datasets, model runs, manifests, local analysis.
- `output/`: thesis PDFs, figure exports, defense assets.
- `tmp/`, `tmp_ppt_rebuild/`, `tmp_ppt_render/`: temporary build products.
- `research_validation/**/*.csv`, `*.png`, `*.svg`, `*.pdf`, `*.txt`,
  `*.json`: regenerated chapter evidence payloads.

Use `docs/reproducibility/FINAL_RESULTS_INDEX.md` and
`docs/reproducibility/DATASET_MANIFEST.md` to locate the result roots instead.

## Public Prediction Entrypoints

| Public wrapper | Calls |
| --- | --- |
| `scripts/build_dataset/build_parametric_targetband_dataset_v1.py` | `src/prediction/targetband_param/runners/run_build_parametric_targetband_dataset_v1.py` |
| `scripts/train_prediction/train_parametric_targetband_classifier_v1.py` | `src/prediction/targetband_param/runners/run_train_parametric_targetband_classifier_v1.py` |
| `scripts/train_prediction/train_parametric_targetband_regressor_v1.py` | `src/prediction/targetband_param/runners/run_train_parametric_targetband_regressor_v1.py` |
| `scripts/export_results/build_curated_application_bundle_v1.py` | `src/prediction/targetband_param/runners/run_build_curated_application_bundle_v1.py` |
| `scripts/export_results/build_thesis_application_bundle_v1.py` | `src/prediction/targetband_param/runners/run_build_thesis_application_bundle_v1.py` |

## Public Optimization Entrypoints

| Public wrapper | Calls |
| --- | --- |
| `scripts/run_ga/score_targetband_candidates_v1.py` | `src/optimization/seed_ranking/run_targetband_seed_scoring_v1.py` |
| `scripts/run_ga/run_targetband_local_ga_v1.py` | `src/optimization/seed_ranking/run_targetband_local_ga_v1.py` |
| `scripts/run_ga/build_targetband_validation_manifest_v1.py` | `src/optimization/seed_ranking/build_targetband_ga_validation_manifest_v1.py` |

## Public COMSOL Entrypoints

| Public wrapper | Calls |
| --- | --- |
| `scripts/run_comsol/run_comsol_stage4_targetband_top6_v1.m` | `runners/run_stage4_validation_targetband_top6_v1.m` |
| `scripts/run_comsol/run_comsol_stage4_targetband_v1.m` | `runners/run_stage4_validation_targetband_v1.m` |
| `scripts/run_comsol/run_real_ga_thesis_band_overlap_v1.m` | `runners/run_stage3_comsol_in_loop_thesis_band_overlap_ga_v1.m` |
| `scripts/run_comsol/run_real_ga_targetband180_220_overlap_v1.m` | `runners/run_stage3_comsol_in_loop_targetband180_220_overlap_ga_v1.m` |
| `scripts/run_comsol/run_real_ga_fourier_only_band_v1.m` | `runners/run_fourier_only_band_ga_v1.m` |
| `scripts/run_comsol/run_real_ga_fourier_only_bands_ga20_v1.m` | `runners/run_fourier_only_bands_ga20_v1.m` |

## Public Figure Entrypoints

| Public wrapper | Calls |
| --- | --- |
| `scripts/make_figures/ch2/build_ch2_typical_stats_v1.py` | `research_validation/ch2_typical_dispersion/build_ch2_typical_stats_v1.py` |
| `scripts/make_figures/ch2/build_ch2_reliability_stats_v1.py` | `research_validation/build_ch2_reliability_stats_v1.py` |
| `scripts/make_figures/ch3/build_ch3_predictor_v12_report.py` | `research_validation/ch3_predictor_v12_figures/build_ch3_predictor_v12_report.py` |
| `scripts/make_figures/ch4/build_ch4_ga_real_optimization_assets_20gen.py` | `research_validation/ch4_ga_real_optimization/build_ch4_ga_real_optimization_assets_20gen.py` |
| `scripts/make_figures/ch5/build_ch5_prediction_vs_ga_v12.py` | `research_validation/ch5_prediction_vs_ga/build_ch5_prediction_vs_ga_v12.py` |
| `scripts/make_figures/ch5/build_ch5_strict_holdout_validation_v1.py` | `research_validation/ch5_strict_holdout_validation/build_ch5_strict_holdout_validation_v1.py` |
| `scripts/make_figures/ch5/build_fourier_only_ablation_v1.py` | `research_validation/ch5_fourier_only_ablation/build_fourier_only_ablation_v1.py` |
| `scripts/make_figures/postprocess/plot_bandgap_summary.py` | `postprocess/plot_bandgap_summary.py` |

## Public Check Entrypoints

| Public wrapper | Checks |
| --- | --- |
| `scripts/check_project/check_public_layout.py` | Required public docs, moved source packages, compatibility shims, JSON configs, and Python entrypoint compilation |
