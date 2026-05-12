# Thesis Mainline

## Official Thesis Claim

The repository now treats the **frozen target-band stack** as the single official
thesis-facing mainline.

The working thesis claim is:

> We establish a target-band-conditioned prediction and inverse-design workflow
> inside the thesis band catalog, where a conditional predictor proposes
> candidates for a specified band, prediction-guided search/refinement improves
> them under real physical constraints, and the final structures are validated
> as usable target-band designs.

The authoritative freeze references are:

- `docs/architecture/targetband_mainline_freeze_v1.md`
- `prediction_targetband_param_v1/configs/targetband_mainline_freeze_v1.json`
- `prediction_targetband_param_v1/configs/thesis_band_catalog_v2.json`
- `docs/THESIS_RUNBOOK.md`
- `docs/THESIS_METHOD_MAP.md`

## Canonical Pipeline

The canonical thesis pipeline is:

1. truth production in `physics_pipeline/`
2. target-band dataset and model training in `prediction_targetband_param_v1/`
3. target-band seed scoring and local refinement in `optimization/`
4. real validation through stage4 / COMSOL
5. analysis packaging and thesis-facing application bundles

## Stable Entrypoints

Use this set as the fixed thesis-facing entrypoint set:

- `prediction_targetband_param_v1/configs/targetband_mainline_freeze_v1.json`
- `prediction_targetband_param_v1/configs/thesis_band_catalog_v2.json`
- `prediction_targetband_param_v1/runners/run_build_parametric_targetband_dataset_v1.py`
- `prediction_targetband_param_v1/runners/run_train_parametric_targetband_classifier_v1.py`
- `prediction_targetband_param_v1/runners/run_train_parametric_targetband_regressor_v1.py`
- `optimization/runners/run_targetband_seed_scoring_v1.py`
- `optimization/runners/run_targetband_local_ga_v1.py`
- `optimization/runners/run_targetband_validation_manifest_v1.py`
- `runners/run_stage4_validation_targetband_top6_v1.m`
- `runners/run_stage4_validation_targetband_v1.m`
- `prediction_targetband_param_v1/runners/run_build_thesis_application_bundle_v1.py`

## Baseline / Historical Bridge Lines

The following routes remain important, but they should now be described as
baseline or bridge logic rather than the repository default mainline:

- `stage3_training/build_candidate_pool_v10.py`
- `stage3_training/build_candidate_pool_v11.py`
- `stage3_training/build_validation_manifest_v10.py`
- `stage3_training/build_validation_manifest_v11.py`
- `stage3_training/build_ga_validation_manifest_v1.py`
- `optimization/runners/run_real_ga_v1.m`
- `optimization/runners/run_global_real_ga_v1.m`
- `optimization/runners/run_band_catalog_real_ga_v1.m`

Use them for:

- reproducible baseline comparisons
- historical interpretation
- bridge runs during refactor-safe maintenance

## Config Semantics

Use one vocabulary across Python and MATLAB:

- `profile`
  - frozen research assumptions, thesis-band choices, candidate-construction choices
- `policy`
  - thresholds, quotas, ranking rules, validation allocation, GA limits
- `run config`
  - paths, output roots, resume settings, and per-run execution overrides

Current shared contract / run-config anchors are:

- `stage3_training/profiles/`
- `stage3_training/policies/`
- `stage4_validation/build_stage4_validation_config.m`
- `shared/contracts/stage4_validation_manifest_contract_v1.json`

## Recommended Run Sequence

For thesis-facing reproduction, use this order:

1. build the parametric target-band dataset
   - `prediction_targetband_param_v1/runners/run_build_parametric_targetband_dataset_v1.py`
2. train the conditional classifier
   - `prediction_targetband_param_v1/runners/run_train_parametric_targetband_classifier_v1.py`
3. train the conditional regressor
   - `prediction_targetband_param_v1/runners/run_train_parametric_targetband_regressor_v1.py`
4. score candidate seeds for a target band
   - `optimization/runners/run_targetband_seed_scoring_v1.py`
5. run local target-band refinement
   - `optimization/runners/run_targetband_local_ga_v1.py`
6. build the real-validation manifest
   - `optimization/runners/run_targetband_validation_manifest_v1.py`
7. launch stage4 validation
   - `runners/run_stage4_validation_targetband_top6_v1.m`
   - authoritative chapter-6 output: `data/comsol_batch/stage4_validation_targetband_top6_v1/`
   - supplementary 4-row refinement batch: `data/comsol_batch/stage4_validation_targetband_v1/`
8. package thesis-facing application outputs
   - `prediction_targetband_param_v1/runners/run_build_thesis_application_bundle_v1.py`

The chapter-6 Stage4 validation funnel uses `stage4_validation_targetband_top6_v1`.
That batch contains 6 submitted candidates, 6 geometry-valid candidates, 5
contact-valid and solved candidates, and 5 positive `gap34` gains. Do not use
the smaller `stage4_validation_targetband_v1` batch as the source for the
top-6 funnel.

## Output Layering

Use the following output interpretation:

- truth assets:
  - `data/comsol_batch/`
- processed target-band datasets:
  - `data/prediction_targetband_param_v1/`
- trained conditional model runs:
  - `data/prediction_targetband_param_v1_runs/`
- target-band seed scoring outputs:
  - `data/ml_runs/targetband_seed_scoring_v1/`
- target-band local refinement outputs:
  - `data/ml_runs/targetband_local_ga_v1/`
- shape-aware front-end builder:
  - `prediction_targetband_param_v1/tools/build_targetband_shape_atlas_v1.py`
- thesis-facing application bundles:
  - `data/prediction_targetband_param_v1_app/`
- thesis documentation and narrative assets:
  - `docs/`
