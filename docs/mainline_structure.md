# Mainline Structure Map

## Official Thesis Mainline

The repository now treats the **frozen target-band stack** as the single
thesis-facing mainline.

Its canonical flow is:

1. produce and accumulate real truth in `physics_pipeline/`
2. train conditional target-band prediction in `prediction_targetband_param_v1/`
3. score and refine target-band candidates in `optimization/`
4. validate shortlisted candidates back in `stage4_validation/`
5. consolidate evidence into analysis outputs and thesis-ready bundles

The frozen references are:

- `docs/architecture/targetband_mainline_freeze_v1.md`
- `prediction_targetband_param_v1/configs/targetband_mainline_freeze_v1.json`
- `prediction_targetband_param_v1/configs/thesis_band_catalog_v2.json`

## Stable Entrypoints

These are the preferred thesis-facing entrypoints:

- `prediction_targetband_param_v1/runners/run_build_parametric_targetband_dataset_v1.py`
- `prediction_targetband_param_v1/runners/run_train_parametric_targetband_classifier_v1.py`
- `prediction_targetband_param_v1/runners/run_train_parametric_targetband_regressor_v1.py`
- `optimization/runners/run_targetband_seed_scoring_v1.py`
- `optimization/runners/run_targetband_local_ga_v1.py`
- `optimization/runners/run_targetband_validation_manifest_v1.py`
- `runners/run_stage4_validation_targetband_v1.m`
- `prediction_targetband_param_v1/runners/run_build_thesis_application_bundle_v1.py`

## Shared Variation Points

These are the preferred places for controlled changes around the frozen stack:

- `prediction_targetband_param_v1/configs/`
  - frozen thesis-band catalog and mainline reference configs
- `stage3_training/profiles/`
  - reusable profile objects for candidate-construction choices
- `stage3_training/policies/`
  - thresholds, quotas, ranking rules, and search-budget settings
- `stage4_validation/build_stage4_validation_config.m`
  - shared MATLAB run-config builder for stage4 validation
- `shared/contracts/stage4_validation_manifest_contract_v1.json`
  - shared Python↔MATLAB manifest contract for stage4 validation handoff

## Baseline / Bridge Layers

These paths are preserved, but they are no longer the repository default mainline:

- `stage3_training/build_candidate_pool_v10.py`
- `stage3_training/build_candidate_pool_v11.py`
- `stage3_training/build_validation_manifest_v10.py`
- `stage3_training/build_validation_manifest_v11.py`
- `stage3_training/build_ga_validation_manifest_v1.py`
- `runners/run_stage4_validation_ab_v10.m`
- `runners/run_stage4_validation_ab_v11.m`
- `runners/run_stage4_validation_ab_ga_v1.m`

Interpret them as:

- reproducible baselines
- historical bridge logic
- comparison routes against the frozen target-band thesis mainline

## Extension Rule

When extending the repository from this point onward:

1. compare against the frozen target-band stack first
2. prefer config/profile/policy updates before adding new scripts
3. keep new thesis-facing entrypoints few and explicit
4. treat `v10/v11/ga_v1` as baseline or bridge logic unless strong evidence justifies promotion
