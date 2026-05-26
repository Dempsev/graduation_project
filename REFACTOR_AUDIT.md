# Final Public Refactor Audit

## 0. Scope

This audit is P1 of the final public refactor. It records what exists before
large moves are made. It does not change experiment results, rerun COMSOL, or
delete historical work.

Snapshot:

- Branch: `codex/final-public-refactor`
- Defense snapshot tag: `defense-final-snapshot-2026`
- Baseline commit: `052db9ab3a4b6b092b75ba33e037387a844a1924`
- Current worktree: modified and untracked final thesis/experiment support
  material exists and should be sorted into the public refactor.

The final public narrative should follow the finished thesis:

```text
COMSOL dispersion truth
-> target-band conditional prediction
-> real COMSOL-in-loop GA
-> predictor Top5 / random / GA validation comparison
-> high-frequency weak-band boundary analysis
```

## 1. Repository Scale

Tracked repository state:

- `git ls-files`: 594 tracked files.
- Main source/script inventory outside ignored outputs:
  - MATLAB `.m`: 342 files.
  - Python `.py`: 295 files.

Generated or local-only payload:

| Directory | Files | Approx. size | Public-git decision |
| --- | ---: | ---: | --- |
| `data/` | 26117 | 69563.93 MB | Do not commit; index only |
| `output/` | 752 | 613.53 MB | Do not commit; index selected final figures only if needed |
| `tmp/` | 371 | 101.90 MB | Do not commit |
| `tmp_ppt_rebuild/` | 408 | 11.00 MB | Archive or delete from public tree |
| `research_validation/` | 352 | 30.09 MB | Review carefully; contains final thesis evidence plus generated figures |

The `.gitignore` already excludes `data/`, `output/`, `tmp/`,
`tmp_ppt_rebuild/`, Office/PDF/PPT artifacts, and archives. That policy should
remain. The public repo should track code, configs, lightweight reports, and
result indexes, not the full COMSOL/model payload.

## 2. Current Worktree Supplements

Modified tracked files:

- `docs/THESIS_RUNBOOK.md`
- `optimization/real_comsol_ga/run_comsol_in_loop_band_catalog_ga_v1.m`
- `postprocess/plot_v11_freeze_cn.m`
- `src/prediction/targetband_param/tools/analyze_predictor_readiness_v1.py`
- `ARCHIVE_ORIGINAL_STATE.md`

Untracked additions to sort during P2/P3:

- Thesis notes:
  - `docs/THESIS_CH1_CH3_DRAFT_CN.md`
  - `docs/THESIS_CH3_V12_PREDICTOR_DATASET_AND_TRAINING_CN.md`
  - `docs/THESIS_MECHANICS_STYLE_OUTLINE_CN.md`
  - `docs/THESIS_REVISED_OUTLINE_CN.md`
  - `docs/THESIS_TARGETBAND_DATA_INDEX_V10.md`
- Real-GA and candidate-pool additions:
  - `optimization/real_comsol_ga/get_comsol_in_loop_ga_targetband180_220_overlap_config_v1.m`
  - `optimization/real_comsol_ga/get_comsol_in_loop_ga_thesis_band_overlap_config_v1.m`
  - `optimization/real_comsol_ga/get_fourier_only_ga_config_v1.m`
  - `src/optimization/seed_ranking/analyze_targetband_four_arm_results_v1.py`
  - `src/optimization/seed_ranking/build_active_ga_multiband_neighborhood_candidate_pool_v1.py`
  - `src/optimization/seed_ranking/build_active_ga_neighborhood_candidate_pool_v1.py`
  - `src/optimization/seed_ranking/build_fourier_only_real_ga_shape_pool_v1.py`
  - `src/optimization/seed_ranking/build_highfreq_shape_family_candidate_pool_v1.py`
  - `src/optimization/seed_ranking/build_targetband_baseline_abc_manifest_v1.py`
  - `src/optimization/seed_ranking/build_targetband_baseline_v10_manifest_v1.py`
  - `src/optimization/seed_ranking/build_targetband_real_ga_shape_pool_v1.py`
- Plotting and thesis figure scripts:
  - `postprocess/export_ch2_snake_fourier_overlay_mesh_v1.m`
  - `postprocess/export_ch2_structure_construction_assets_v1.m`
  - `postprocess/plot_targetband_active_learning_cn_v1.m`
  - `postprocess/plot_targetband_active_learning_v10.m`
  - `postprocess/plot_targetband_chinese_svg_bundle_v1.m`
  - `postprocess/plot_targetband_four_arm_baseline_v1.m`
  - `postprocess/plot_targetband_four_arm_baseline_v10_cn.m`
  - `postprocess/plot_tb180_220_method_compare_v11_freeze_cn.py`
  - `postprocess/plot_thesis_ch5_titleless_cn_bundle_v1.m`
  - `postprocess/plot_v11_model_check_cn.py`
  - `postprocess/plot_v11_typical_case_dispersion_cn.py`
  - `postprocess/run_ch2_mesh_export_via_python312.py`
  - `postprocess/run_ch2_structure_assets_via_python312.py`
- Prediction/model additions:
  - `src/prediction/targetband_param/tools/build_active_learning_augmented_dataset_v10.py`
  - `src/prediction/targetband_param/tools/build_active_learning_augmented_dataset_v9.py`
  - `src/prediction/targetband_param/tools/build_ch2_snake_fourier_overlay_figure_v1.py`
  - `src/prediction/targetband_param/tools/build_multiband_predictor_top1_validation_manifest_v1.py`
  - `src/prediction/targetband_param/tools/build_targetband180_220_predictor_top6_validation_manifest_v11_12gen_freeze.py`
  - `src/prediction/targetband_param/tools/build_targetband180_220_random6_validation_manifest_v11_12gen_freeze.py`
  - `src/prediction/targetband_param/tools/build_thesis_ga20_all_data_dataset_v12.py`
  - `src/prediction/targetband_param/tools/evaluate_active_learning_holdout_v10.py`
  - `src/prediction/targetband_param/tools/evaluate_active_learning_holdout_v9.py`
  - `src/prediction/targetband_param/tools/train_final_parametric_targetband_predictor_v12.py`
- Final thesis evidence folder:
  - `research_validation/`
- Runner/config additions:
  - new `runners/run_*` wrappers for Fourier-only GA, active learning plots,
    V11 freeze validation, V10 baselines, target-band validation, and Stage4.
  - new `stage4_validation/get_stage4_validation_config_*` config files.
- Local one-off material:
  - `test_two_matlab.py`
  - `tools/`

## 3. Directory Roles

| Current path | Current role | Public refactor role |
| --- | --- | --- |
| `README.md`, `README_CN.md` | Existing project intro | Rewrite around final thesis workflow |
| `docs/` | Thesis-mainline docs plus final writing notes | Split into project, thesis, reproducibility, archive docs |
| `docs/architecture/` | Frozen target-band architecture note | Keep under `docs/project/architecture/` or `docs/reproducibility/` |
| `physics_pipeline/` | Truth-layer overview | Move/alias to `src/comsol_pipeline/` |
| `model_core/` | MATLAB COMSOL model construction helpers | Move to `src/comsol_pipeline/model_core/` |
| `snake/` | Snake-inspired geometry generation | Move to `src/geometry/snake/` |
| `preprocess/` | Geometry/data preprocessing utilities | Split between `src/geometry/` and `src/dataset/` |
| `prediction_targetband_param_v1/` | Main target-band conditional prediction stack | Move to `src/prediction/targetband_param/` |
| `optimization/real_comsol_ga/` | Real COMSOL-in-loop GA | Move to `src/optimization/real_comsol_ga/` and expose safe wrappers |
| `src/optimization/seed_ranking/` | Candidate pool, ranking, validation manifests | Moved in P3; root path is a compatibility shim |
| `stage4_validation/` | Shared real-validation configs and wrappers | Move to `src/validation/stage4/` |
| `postprocess/` | Plotting/export scripts | Split into `src/plotting/` plus `scripts/make_figures/` |
| `research_validation/` | Final chapter-specific evidence and figure bundles | Promote selected scripts/reports to `docs/reproducibility/` and `scripts/make_figures/`; archive generated figures |
| `runners/` | Many historical MATLAB/Python entrypoints | Split into public `scripts/` and `archive/legacy_runners/` |
| `prediction/` | Older pure prediction reading entry | Archive or keep as baseline wrapper |
| `prediction_targetband_v1/` | Earlier target-band model line | Archive under `archive/legacy_prediction/` |
| `prediction_v2` to `prediction_v7` | Historical pure-prediction versions | Archive under `archive/legacy_prediction/` |
| `stage1/`, `stage2*`, `stage3_*` | Historical truth/dataset/training pipelines | Archive under `archive/legacy_stage_pipelines/` |
| `baselines/` | Baseline and historical bridge docs | Keep as `archive/baselines/` or `docs/archive/baselines/` |
| `src/shared/` | Contracts and shared IO/helpers | Moved in P3; root `shared/` remains a compatibility shim |
| `configs/` | Experiment configs | Keep as top-level `configs/`; later normalize paths |
| `tests/` | Smoke tests | Keep, then rewrite around public paths |
| `data/` | Local generated data and results | Keep ignored; document through manifests |
| `output/` | Local thesis/doc/figure outputs | Keep ignored; index final outputs |
| `tmp*`, `.worktrees/`, `__pycache__/` | Temporary/generated material | Exclude from public tree |
| `tools/` | Defense PPT builders | Archive unless kept as documented thesis artifact tooling |

## 4. Core Code And Evidence

The public repo should center on these modules:

- Geometry:
  - `snake/`
  - `preprocess/`
  - geometry-related builders in `src/optimization/seed_ranking/`
  - chapter-2 geometry export scripts in `postprocess/` and `research_validation/ch2_typical_dispersion/`
- COMSOL truth and model construction:
  - `model_core/`
  - `physics_pipeline/`
  - COMSOL wrappers in `runners/`
  - real-GA MATLAB functions in `optimization/real_comsol_ga/`
- Dataset:
  - `src/prediction/targetband_param/dataset/build_parametric_targetband_dataset_v1.py`
  - V9/V10/V12 augmentation scripts in `src/prediction/targetband_param/tools/`
  - final local data roots under `data/prediction_targetband_param_v1/`
- Prediction:
  - `src/prediction/targetband_param/models/`
  - `src/prediction/targetband_param/runners/`
  - predictor readiness and v12 scripts under `src/prediction/targetband_param/tools/`
  - chapter-3 evidence under `research_validation/ch3_predictor_v12_figures/`
- Real COMSOL-in-loop GA:
  - `optimization/real_comsol_ga/`
  - `optimization/runners/run_band_catalog_real_ga_v1.m`
  - `runners/run_stage3_comsol_in_loop_*`
  - chapter-4 evidence under `research_validation/ch4_ga_real_optimization/`
- Validation and comparison:
  - `stage4_validation/`
  - `src/shared/io/stage4_validation_manifest.py`
  - `src/shared/contracts/stage4_validation_manifest_contract_v1.json`
  - chapter-5 evidence under `research_validation/ch5_prediction_vs_ga/`
  - strict holdout evidence under `research_validation/ch5_strict_holdout_validation/`
- Plotting:
  - `postprocess/`
  - chapter-specific plot/export scripts under `research_validation/`

## 5. Experiment Data And Result Roots

Important local-only result roots:

| Local root | Role |
| --- | --- |
| `data/comsol_batch/` | COMSOL truth, Stage4 validations, real-GA batches |
| `data/prediction_targetband_param_v1/` | Built target-band datasets |
| `data/prediction_targetband_param_v1_runs/` | Main RF/HGB model runs and metrics |
| `data/ml_runs/` | Candidate scoring, local GA, old ML runs |
| `data/analysis/` | Analysis summaries, predictor readiness outputs, shape atlas references |
| `data/research_validation/` | Some chapter-specific generated data |
| `output/doc/` | Thesis PDF/DOC exports |
| `output/thesis_charts/` | Thesis chart exports |
| `output/defense_ppt_assets/` | Defense visual assets |

Largest `data/` roots:

- `data/prediction_targetband_param_v1_runs/`: about 62.9 GB.
- `data/pure_prediction_v7_runs/`: about 1.4 GB.
- `data/prediction_targetband_param_v1/`: about 1.1 GB.
- `data/comsol_batch/`: about 134 MB.

These should not be moved blindly. The public repo needs manifests that point
to these locations and explain whether each root is required for postprocess,
model retraining, real COMSOL reruns, or historical comparison only.

## 6. Thesis Chapter Mapping

| Thesis chapter | Current evidence locations | Public target |
| --- | --- | --- |
| Chapter 2 physical model and numerical analysis | `model_core/`, `physics_pipeline/`, `research_validation/ch2_typical_dispersion/`, `postprocess/export_ch2_*` | `src/comsol_pipeline/`, `src/geometry/`, `scripts/make_figures/ch2_*`, `docs/reproducibility/ch2_*` |
| Chapter 3 target-band prediction | `prediction_targetband_param_v1/`, `research_validation/ch3_predictor_v12_figures/` | `src/prediction/targetband_param/`, `scripts/train_prediction/`, `docs/reproducibility/ch3_*` |
| Chapter 4 real COMSOL-in-loop GA | `optimization/real_comsol_ga/`, `optimization/runners/`, `research_validation/ch4_ga_real_optimization/` | `src/optimization/real_comsol_ga/`, `scripts/run_ga/`, `docs/reproducibility/ch4_*` |
| Chapter 5 prediction vs random vs GA validation | `stage4_validation/`, `research_validation/ch5_prediction_vs_ga/`, `research_validation/ch5_strict_holdout_validation/`, `research_validation/ch5_fourier_only_ablation/` | `src/validation/`, `scripts/export_results/`, `scripts/make_figures/ch5_*`, `docs/reproducibility/ch5_*` |
| Chapter 6 conclusions and boundaries | `docs/THESIS_*`, final thesis PDF under `output/doc/` | `docs/thesis/` and public README claim-boundary text |

## 7. Scripts That Can Trigger COMSOL Or MATLAB Heavy Work

Treat these as unsafe-by-default in the public repo. They need explicit names,
warnings, or dry-run/preflight modes:

- `optimization/real_comsol_ga/run_comsol_in_loop_band_catalog_ga_v1.m`
- `optimization/real_comsol_ga/run_comsol_in_loop_ga_v1.m`
- `optimization/real_comsol_ga/run_comsol_in_loop_global_ga_v1.m`
- `optimization/real_comsol_ga/run_comsol_in_loop_champion_local_v3.m`
- `optimization/runners/run_*real_ga*.m`
- `runners/run_stage3_comsol_in_loop_*.m`
- `runners/run_stage4_validation_*.m`
- `research_validation/ch2_typical_dispersion/run_ch2_typical_local_perturb_validation_v1.m`
- `research_validation/ch5_strict_holdout_validation/run_ch5_strict_holdout_comsol_manifest_v1.m`

Safer postprocess-only candidates:

- `research_validation/ch3_predictor_v12_figures/build_ch3_predictor_v12_report.py`
- `research_validation/ch4_ga_real_optimization/build_ch4_ga_real_optimization_assets_20gen.py`
- `research_validation/ch5_prediction_vs_ga/build_ch5_prediction_vs_ga_v12.py`
- `postprocess/plot_*`

However, some Python wrappers start MATLAB/COMSOL paths directly and still need
warnings:

- `postprocess/run_ch2_mesh_export_via_python312.py`
- `postprocess/run_ch2_structure_assets_via_python312.py`
- `research_validation/*/run_*via_engine*.py`

## 8. Current Test Status

Command:

```powershell
python -m unittest tests.test_thesis_mainline_smoke
```

Initial P1 result: 9 tests run; 7 pass, 1 failure, 1 error.

Known failures:

- Missing configured shape frontend:
  - `src/prediction/targetband_param/configs/targetband_mainline_freeze_v1.json`
  - `frozen_mainline.shape_frontend = data/analysis/targetband_shape_atlas_v1`
  - Current path does not exist.
- Missing historical stage1 positive CSV:
  - `data/comsol_batch/stage1_shape_screening/stage1_positive_shapes.csv`
  - Required by `stage3_training/seed_discovery_profiles.py` for
    `candidate_pool_optimization_v1`.

Interpretation:

- This is not proof that final thesis results are invalid.
- It does prove that legacy smoke tests are still wired to old/historical
  data paths and should be rewritten for the final public structure.
- P2 should decide whether to restore these data pointers, update configs to
  final result roots, or move these tests to `archive/legacy_tests/`.

P2 update:

- The documentation paths in `tests/test_thesis_mainline_smoke.py` now point to
  `docs/thesis/` and `docs/reproducibility/`.
- Missing generated data under ignored `data/` roots is treated as a local-data
  skip instead of a public-repo failure.

## 9. Hardcoded Path Findings

Hardcoded absolute paths exist and should be normalized before public release.
Examples:

- `docs/THESIS_RUNBOOK.md`: `Set-Location D:\graduation_project\coad`
- `optimization/real_comsol_ga/generate_efficiency_frontier_plots_v4.py`:
  `ROOT = Path(r"d:\graduation_project\coad")`
- `postprocess/run_ch2_mesh_export_via_python312.py`:
  hardcoded COMSOL server, MATLAB executable, and COMSOL MLI paths.
- `postprocess/run_ch2_structure_assets_via_python312.py`:
  hardcoded COMSOL server, MATLAB executable, and COMSOL MLI paths.
- `src/prediction/targetband_param/tools/build_ch2_snake_fourier_overlay_figure_v1.py`:
  Windows font paths.
- `research_validation/` README/report files contain absolute local data and
  output paths.

Public refactor rule:

- Repository root should be resolved from `Path(__file__).resolve()` or `pwd`.
- Local MATLAB/COMSOL executable paths should live in `configs/local.example.json`
  or environment variables.
- Final result reports may mention local paths, but the public index should
  also provide repository-relative or logical paths.

## 10. Repetition And Naming Issues

Main issues:

- Many runner generations remain side by side:
  - `run_stage3_build_candidate_pool_v3` through `v10`.
  - `run_stage4_validation_ab_v1` through `v11`.
  - multiple `targetband_baseline_v10`, `abc`, `fullpool`, `v11_freeze`
    variants.
- Prediction versions `prediction_v2` through `prediction_v7` are useful for
  history but visually overwhelm the final method.
- `research_validation/` mixes source scripts, generated PNG/SVG/PDF figures,
  CSV tables, reports, and `__pycache__`.
- Top-level `runners/` mixes safe postprocess wrappers with full COMSOL
  validation and historical stage wrappers.
- `tools/` currently holds defense PPT builders, not reusable core tools.

Public refactor rule:

- Preserve final thesis scripts in public paths.
- Move older versioned route families to archive with notes.
- Do not leave generated images and `__pycache__` in source-oriented folders.
- Use script names that disclose risk:
  - `make_*` for postprocess.
  - `train_*` for model training.
  - `run_comsol_*` or `run_real_ga_*` for COMSOL-triggering work.

## 11. Cannot-Move-Yet List

Do not move these until imports and wrapper paths are updated together:

- `optimization/`
- `stage4_validation/`
- `runners/`
- `model_core/`
- `postprocess/`
- `research_validation/`

Do not commit these heavy roots:

- `data/`
- `output/`
- `tmp/`
- `tmp_ppt_rebuild/`
- `.worktrees/`

Do not delete these final evidence roots without a replacement manifest:

- `research_validation/ch3_predictor_v12_figures/`
- `research_validation/ch4_ga_real_optimization/`
- `research_validation/ch5_prediction_vs_ga/`
- `research_validation/ch5_strict_holdout_validation/`
- `research_validation/ch5_fourier_only_ablation/`

## 12. Recommended P2 Priorities

1. Create the public skeleton:
   - `src/`
   - `scripts/`
   - `docs/project/`
   - `docs/thesis/`
   - `docs/reproducibility/`
   - `docs/archive/`
   - `archive/`
2. Move documentation first:
   - current thesis docs to `docs/thesis/` or `docs/archive/thesis_notes/`.
   - final runbook and result maps to `docs/reproducibility/`.
3. Promote `research_validation/` selectively:
   - scripts and lightweight reports into `scripts/make_figures/` and
     `docs/reproducibility/`.
   - generated PDF/PNG/SVG bundles either remain ignored or move to
     `archive/generated_figures/` only if the user wants them tracked.
4. Build public script indexes before moving code:
   - `COMSOL_SCRIPT_INDEX.md`
   - `FINAL_RESULTS_INDEX.md`
   - `DATASET_MANIFEST.md`
5. Rewrite tests after paths stabilize:
   - keep final smoke tests for path existence and postprocess-only scripts.
   - move historical data-dependent smoke tests to archive or mark them
     legacy.
