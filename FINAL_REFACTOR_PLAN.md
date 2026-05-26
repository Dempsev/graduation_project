# Final Public Refactor Plan

## 0. Intent

This plan turns the repository into a public, thesis-aligned research project.
It is more aggressive than a defense-safe cleanup, but it keeps the defense
snapshot recoverable through:

- branch: `codex/final-public-refactor`
- tag: `defense-final-snapshot-2026`
- state record: `ARCHIVE_ORIGINAL_STATE.md`

The target public repo should answer four questions quickly:

1. What physical/design problem does this project solve?
2. Which code produces truth, datasets, predictions, GA, and validation?
3. Which scripts are safe postprocess and which call COMSOL?
4. Which thesis figures/results came from which data and scripts?

## 1. Target Public Tree

```text
coad/
  README.md
  README_CN.md
  configs/
    local.example.json
    experiments/
  docs/
    project/
    thesis/
    reproducibility/
    archive/
  src/
    geometry/
    comsol_pipeline/
    dataset/
    prediction/
    optimization/
    validation/
    plotting/
    shared/
  scripts/
    build_dataset/
    train_prediction/
    run_ga/
    make_figures/
    export_results/
    check_project/
  tests/
  archive/
    legacy_prediction/
    legacy_stage_pipelines/
    legacy_runners/
    oneoff_thesis_scripts/
    generated_reports/
```

## 2. Movement Map

| Current path | Target path | Priority | Notes |
| --- | --- | --- | --- |
| `physics_pipeline/` | `src/comsol_pipeline/overview/` | P3 | Keep README semantics |
| `model_core/` | `src/comsol_pipeline/model_core/` | P3 | MATLAB COMSOL helpers |
| `snake/` | `src/geometry/snake/` | P3 | Preserve geometry generation history |
| `preprocess/` | `src/geometry/` and `src/dataset/` | P4 | Split after import scan |
| `prediction_targetband_param_v1/` | `src/prediction/targetband_param/` | Done in P3 | Main final prediction stack; root path is a compatibility shim |
| `prediction/` | `archive/legacy_prediction/pure_prediction_v1/` or `src/prediction/baselines/` | P4 | Decide after README rewrite |
| `prediction_targetband_v1/` | `archive/legacy_prediction/targetband_v1/` | P4 | Earlier target-band route |
| `prediction_v2` to `prediction_v7` | `archive/legacy_prediction/` | P4 | Historical pure prediction |
| `optimization/real_comsol_ga/` | `src/optimization/real_comsol_ga/` | P3 | Final chapter-4 method |
| `optimization/seed_ranking/` | `src/optimization/seed_ranking/` | Done in P3 | Candidate construction/ranking; root path is a compatibility shim |
| `optimization/runners/` | `scripts/run_ga/` or `archive/legacy_runners/optimization/` | P4 | Split final vs old |
| `stage4_validation/` | `src/validation/stage4/` | P3 | Final COMSOL validation configs |
| `shared/` | `src/shared/` | Done in P3 | Contracts, IO, helpers; root path is a compatibility shim |
| `postprocess/` | `src/plotting/` plus `scripts/make_figures/` | P3 | Split library code vs entry scripts |
| `research_validation/ch2_typical_dispersion/` | `docs/reproducibility/ch2/` plus `scripts/make_figures/ch2/` | P2 | Promote final chapter evidence |
| `research_validation/ch3_predictor_v12_figures/` | `docs/reproducibility/ch3/` plus `scripts/make_figures/ch3/` | P2 | Promote final prediction evidence |
| `research_validation/ch4_ga_real_optimization/` | `docs/reproducibility/ch4/` plus `scripts/make_figures/ch4/` | P2 | Promote final GA evidence |
| `research_validation/ch5_prediction_vs_ga/` | `docs/reproducibility/ch5/` plus `scripts/make_figures/ch5/` | P2 | Promote final comparison evidence |
| `research_validation/ch5_strict_holdout_validation/` | `docs/reproducibility/ch5/strict_holdout/` | P2 | Important validation evidence |
| `research_validation/ch5_fourier_only_ablation/` | `docs/reproducibility/ch5/fourier_ablation/` | P3 | Supplementary high-frequency/baseline evidence |
| top-level `runners/` | `scripts/` and `archive/legacy_runners/` | In progress in P4 | Legacy stage/plot wrappers archived; COMSOL-facing wrappers retained pending risk index |
| `stage1/`, `stage2*`, `stage3_*` | `archive/legacy_stage_pipelines/` | P4 | Historical route, not final public mainline |
| `baselines/` | `archive/baselines/` or `docs/archive/baselines/` | P4 | Keep readable |
| `docs/THESIS_*` | `docs/thesis/` or `docs/archive/thesis_notes/` | P2 | Split final notes vs old drafting notes |
| `tools/` | `archive/oneoff_thesis_scripts/tools/` | P4 | Defense PPT builders unless kept |
| `test_two_matlab.py` | `archive/oneoff_thesis_scripts/` | P4 | One-off MATLAB check |

## 3. Public Documentation Set

Create or rewrite:

- `README.md`
- `README_CN.md`
- `docs/project/PROJECT_STRUCTURE.md`
- `docs/project/COMSOL_SCRIPT_INDEX.md`
- `docs/reproducibility/FINAL_RUNBOOK.md`
- `docs/reproducibility/FINAL_RESULTS_INDEX.md`
- `docs/reproducibility/DATASET_MANIFEST.md`
- `docs/reproducibility/GA_FINAL_SUMMARY.md`
- `docs/reproducibility/VALIDATION_SUMMARY.md`
- `docs/thesis/THESIS_RESULT_MAP.md`
- `archive/ARCHIVE_NOTES.md`

README should foreground:

- final thesis route, not historical stage evolution;
- COMSOL as physical authority;
- prediction as candidate screening/ranking;
- real COMSOL-in-loop GA as optimization baseline;
- high-frequency weak-band boundary;
- safe postprocess commands versus COMSOL-triggering commands.

## 4. Script Classification Rules

Use these destinations:

- `scripts/build_dataset/`: builds CSV/JSON datasets from local data.
- `scripts/train_prediction/`: trains or evaluates RF/HGB/MLP models.
- `scripts/run_ga/`: starts real GA or COMSOL-in-loop runs; every script needs
  a warning banner.
- `scripts/make_figures/`: postprocess-only figure/table creation.
- `scripts/export_results/`: gathers final result indexes and thesis tables.
- `scripts/check_project/`: lightweight path/test checks.

Naming rules:

- `make_*`: postprocess-only.
- `build_*`: dataset, manifest, or report construction.
- `train_*`: model training.
- `check_*`: lightweight validation.
- `run_comsol_*`: can start COMSOL.
- `run_real_ga_*`: can start COMSOL-in-loop GA.

## 5. Archive Rules

Archive, do not foreground:

- `prediction_v2` through `prediction_v7`.
- old `stage1`, `stage2`, and `stage3_*` families.
- most `runners/run_stage3_*` and version-ladder wrappers.
- one-off PPT/doc tools.
- `tmp_ppt_rebuild/`, `tmp_ppt_render/`, and other generated presentation
  build folders.
- generated figure duplicates when the source script and final selected figure
  index exist.

Do not archive yet:

- `research_validation/` chapter evidence until selected scripts and reports
  are promoted.
- remaining MATLAB and Python imports that still assume old root-level module
  locations beyond the `shared/` compatibility shim.
- `stage4_validation/` configs until public validation wrappers are stable.

## 6. P2 Execution Order

1. Create target folders.
2. Move docs first, because docs do not usually break imports.
3. Generate `FINAL_RESULTS_INDEX.md` from `research_validation/` and current
   thesis output paths.
4. Generate `COMSOL_SCRIPT_INDEX.md` and mark risk levels.
5. Add `configs/local.example.json` for MATLAB/COMSOL executable paths.
6. Rewrite README files against the final public tree.
7. Only then start moving source modules.

## 7. P3/P4 Execution Order

1. Move core source module folders.
2. Update Python imports and MATLAB `addpath`/`fullfile` references.
3. Move final runners into `scripts/`.
4. Move historical route families into `archive/`.
5. Rewrite tests against final public paths.
6. Run lightweight checks:
   - path/index checker;
   - postprocess-only figure smoke checks;
   - Python unit tests that do not require missing data;
   - MATLAB syntax/path preflight when safe.

## 8. Known Risks

- Historical smoke tests currently rely on missing local data paths.
- `research_validation/` includes generated artifacts and Python bytecode.
- Several scripts hardcode `D:\graduation_project\coad`, COMSOL, MATLAB, and
  Windows font paths.
- MATLAB wrappers may rely on current relative folder layout.
- Large `data/` payload should not be committed or moved by refactor scripts.

## 9. Success Criteria

The public refactor is complete when:

- README points to the final thesis workflow in under one screen.
- final chapter evidence is indexed from script to data to figure/table.
- every COMSOL-triggering script is labeled clearly.
- legacy routes are out of the main path but recoverable in `archive/`.
- `data/` and `output/` remain ignored.
- lightweight checks pass without needing large COMSOL runs.
