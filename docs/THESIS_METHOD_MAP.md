# Thesis Method Map

## Purpose

This page maps the thesis method chapter wording to the frozen target-band
code entrypoints. Use it when writing the method section, the experiment
section, or the appendix command references.

The repository now treats the **frozen target-band stack** as the single
official thesis mainline. This is the single official thesis mainline. Older
v10/v11/ga_v1 routes remain valid, but they
should be described as **baseline / historical bridge** lines rather than the
default workflow.

## Method-Term Mapping

| Thesis wording | What it means in the codebase | Official entrypoint / config | Authoritative outputs |
| --- | --- | --- | --- |
| truth production | Historical COMSOL + MATLAB pipeline used to produce physics-grounded labels and reference cases | `physics_pipeline/`, `stage1/`, `stage2/`, `stage2_harmonics_refine/` | `data/comsol_batch/` |
| thesis band catalog | The frozen set of target bands used by the thesis-facing conditional workflow | `prediction_targetband_param_v1/configs/thesis_band_catalog_v2.json` | `prediction_targetband_param_v1/configs/thesis_band_catalog_v2.json` |
| frozen thesis mainline | The officially frozen target-band workflow and wording boundary for the thesis | `docs/THESIS_MAINLINE.md`, `prediction_targetband_param_v1/configs/targetband_mainline_freeze_v1.json` | `docs/THESIS_MAINLINE.md` |
| target-band parametric dataset | The consolidated supervised dataset that pairs structural descriptors with target-band labels and regression targets | `prediction_targetband_param_v1/runners/run_build_parametric_targetband_dataset_v1.py` | `data/prediction_targetband_param_v1/v1/windows_dense_v8_truth_plus_exploratory_aug_v1/` |
| conditional classifier | The model that predicts target-band opening likelihood for a requested band | `prediction_targetband_param_v1/runners/run_train_parametric_targetband_classifier_v1.py` | `data/prediction_targetband_param_v1_runs/param_targetband_cls_rf_dense_v8_cmp_v1/stratified_group_kfold/` |
| conditional regressor | The model that predicts target-band cover ratio / overlap quality for a requested band | `prediction_targetband_param_v1/runners/run_train_parametric_targetband_regressor_v1.py` | `data/prediction_targetband_param_v1_runs/param_targetband_cover_hgb_dense_v8_cmp_v1/stratified_group_kfold/` |
| shape-aware front-end | The shape archetype / family interpretation layer used to explain why the target-band workflow is physically plausible and not a black box | `data/analysis/targetband_shape_atlas_v1/`, `docs/targetband_formal_execution_plan_v1.md` | `data/analysis/targetband_shape_atlas_v1/` |
| seed scoring | The first prediction-guided screening step that ranks candidate seeds under a specified target band | `optimization/runners/run_targetband_seed_scoring_v1.py` | `data/ml_runs/targetband_seed_scoring_v1/band180_220/` |
| local refinement / local GA | The prediction-guided local search step that refines promising seeds around the requested target band | `optimization/runners/run_targetband_local_ga_v1.py` | `data/ml_runs/targetband_local_ga_v1/band180_220/` |
| stage4 validation manifest | The COMSOL-ready shortlist exported from Python and handed to MATLAB through the shared manifest contract | `optimization/runners/run_targetband_validation_manifest_v1.py`, `shared/contracts/stage4_validation_manifest_contract_v1.json` | `data/ml_runs/targetband_local_ga_v1/` |
| real validation | The MATLAB + COMSOL execution that checks whether shortlisted candidates are physically valid target-band designs | `runners/run_stage4_validation_targetband_v1.m`, `stage4_validation/run_stage4_validation_from_manifest.m` | `data/comsol_batch/stage4_validation_targetband_v1/` |
| thesis application bundle | The compact bundle of thesis-facing catalog outputs, metrics, and serving artifacts | `prediction_targetband_param_v1/runners/run_build_thesis_application_bundle_v1.py` | `data/prediction_targetband_param_v1_app/v1/thesis_band_catalog_v2_bundle_v1/` |
| baseline / historical bridge | Older v10/v11 seed-discovery and ga_v1 routes kept for comparison and interpretability | `stage3_training/`, `optimization/runners/run_real_ga_v1.m`, `optimization/runners/run_global_real_ga_v1.m`, `optimization/runners/run_band_catalog_real_ga_v1.m` | `data/ml_dataset/`, `data/ml_runs/`, `data/comsol_batch/` |

## Vocabulary Boundary

Use the following wording consistently across the thesis text and the code:

- profile
  - frozen research assumptions, band choices, and candidate-construction rules
- policy
  - thresholds, quotas, ranking logic, and shortlist allocation rules
- run config
  - paths, output roots, resume behavior, and execution-time overrides

## Recommended Citation Pattern In The Thesis

When you describe the method, the cleanest one-sentence pipeline is:

> We first consolidate physics-grounded truth into a target-band parametric
> dataset, then train conditional predictor models, use those models to score
> and locally refine candidate designs for a requested band, and finally
> validate shortlisted structures with MATLAB/COMSOL stage4 runs.

If you need to mention comparison lines, describe them as:

> baseline or historical bridge workflows used for comparison against the
> frozen target-band thesis mainline.
