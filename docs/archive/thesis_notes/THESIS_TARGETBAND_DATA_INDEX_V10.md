# Target-Band V10 Data Index

## Purpose

This document fixes the current thesis-facing data boundary for the target-band inverse design experiments.
It answers four questions for every important artifact:

- whether it is physical truth, training data, holdout evidence, model output, or final thesis figure data
- whether it enters the thesis main predictor training
- whether it is used only as an independent comparison or holdout
- whether it should be used in the paper

The current thesis mainline should use **v10 multiband active-learning data and the full-pool v10 comparison figures**. Older comparison directories are kept only for provenance.

## Final Thesis Mainline

| Role | Adopted artifact | Thesis status |
|---|---|---|
| Main predictor training dataset | `data/prediction_targetband_param_v1/v1/windows_dense_v10_multiband_active_ga_mid_aug_v1/targetband_parametric_v1.csv` | Adopt |
| Main classifier | `data/prediction_targetband_param_v1_runs/param_targetband_cls_hgb_dense_v10_multiband_active_mid_aug_v1/stratified_group_kfold/` | Adopt |
| Main regressor | `data/prediction_targetband_param_v1_runs/param_targetband_cover_hgb_dense_v10_multiband_active_mid_aug_v1/stratified_group_kfold/` | Adopt |
| Expanded candidate pool | `data/ml_dataset/v12/candidate_pool_active_ga_multiband_neighborhood_v1/candidate_pool_active_ga_multiband_neighborhood_v1.csv` | Adopt |
| v10 candidate scoring | `data/ml_runs/targetband_seed_scoring_v10_multiband_neighborhood_v1/` | Adopt |
| Final method comparison | `data/analysis/targetband_four_arm_baseline_v10_fullpool_v1/` | Adopt |
| Active-learning/holdout analysis | `data/analysis/targetband_active_learning_v10/` | Adopt |
| Real GA long-run comparison | `data/comsol_batch/comsol_in_loop_targetband180_220_overlap_ga_v1/` | Adopt as GA reference only |

## Training And Holdout Boundary

The v10 predictor is trained from the base dense target-band dataset plus multiband COMSOL-in-loop GA mid-trajectory samples.
Near-best GA samples are intentionally withheld to check whether the model learned a high-potential region rather than memorizing the final answers.

| Quantity | Count |
|---|---:|
| Base dataset rows | 45,536 |
| Valid multiband GA source rows | 381 |
| GA source rows added to training | 371 |
| Near-best GA source rows held out | 10 |
| Added training rows after six-band expansion | 2,226 |
| Holdout rows after six-band expansion | 60 |
| Final v10 training dataset rows | 47,762 |

Holdout source rows by origin band:

| Origin band | Held-out source rows | Best held-out origin overlap |
|---|---:|---:|
| `band140_180` | 1 | 20.74 Hz |
| `band160_200` | 1 | 30.07 Hz |
| `band180_220` | 1 | 36.90 Hz |
| `band200_240` | 1 | 31.38 Hz |
| `band220_260` | 1 | 2.87 Hz |
| `band240_280` | 5 | 3.00 Hz |

The 180-220 Hz long-run GA data reaching 40 Hz is **not** part of the v10 thesis predictor training set. It is kept as the real-GA comparison and physical upper-reference evidence.

## Physical Truth Sources

| Path | Type | Enters v10 training? | Thesis use |
|---|---|---:|---|
| `data/comsol_batch/comsol_in_loop_targetband180_220_overlap_ga_v1/` | Real COMSOL-in-loop GA long run, 120 evaluations, reaches 40 Hz | No | Main real-GA comparison curve and upper-reference |
| `data/comsol_batch/comsol_in_loop_thesis_band140_180_overlap_ga_v1/` | 12-generation GA for 140-180 Hz | Mid-trajectory only | Active-learning data source |
| `data/comsol_batch/comsol_in_loop_thesis_band160_200_overlap_ga_v1/` | 12-generation GA for 160-200 Hz | Mid-trajectory only | Active-learning data source |
| `data/comsol_batch/comsol_in_loop_thesis_band180_220_overlap_ga_v1/` | 12-generation GA for 180-220 Hz | Mid-trajectory only | Active-learning data source and holdout source |
| `data/comsol_batch/comsol_in_loop_thesis_band200_240_overlap_ga_v1/` | 12-generation GA for 200-240 Hz | Mid-trajectory only | Active-learning data source |
| `data/comsol_batch/comsol_in_loop_thesis_band220_260_overlap_ga_v1/` | 12-generation GA for 220-260 Hz | Mid-trajectory only | Shows high-frequency structural-family weakness |
| `data/comsol_batch/comsol_in_loop_thesis_band240_280_overlap_ga_v1/` | 12-generation GA for 240-280 Hz | Mid-trajectory only | Shows high-frequency structural-family weakness |
| `data/comsol_batch/stage4_validation_targetband_baseline_v10_fullpool_v1/` | COMSOL validation of random top-6 and v10 full-pool predictor top-6 | No | Final method comparison truth |

## Final Comparison Figures

Use the SVG figures under:

`data/analysis/targetband_four_arm_baseline_v10_fullpool_v1/figures/`

| Figure | Meaning |
|---|---|
| `figure_5_6a_target_overlap_comparison_v10_cn.svg` | Final random vs v10 predictor vs real-GA overlap comparison |
| `figure_5_6b_validation_hit_rates_v10_cn.svg` | Contact/solve/target-hit rates |
| `figure_5_6c_budget_efficiency_curve_v10_cn.svg` | Budget-efficiency curve against real GA |
| `figure_5_6d_budget_quality_scatter_v10_cn.svg` | Budget vs best candidate quality |

Final comparison summary:

| Method | COMSOL evaluations | Contact valid | Target hit rate | Mean overlap | Best overlap |
|---|---:|---:|---:|---:|---:|
| Random balanced | 6 | 4 | 50.0% | 6.62 Hz | 17.07 Hz |
| v10 conditional predictor | 6 | 6 | 100.0% | 37.07 Hz | 39.57 Hz |
| Real COMSOL-in-loop GA | 120 | 111 | 89.2% | 28.20 Hz | 40.00 Hz |

This is the clean comparison to cite in the thesis: the predictor does not replace real GA globally, but it finds near-optimal candidates with much lower COMSOL validation budget.

## Active-Learning Figures

Use the SVG figures under:

`data/analysis/targetband_active_learning_v10/figures/`

| Figure | Meaning |
|---|---|
| `figure_5_7a_multiband_ga_convergence_v10_cn.svg` | Six target-window COMSOL-in-loop GA trajectories |
| `figure_5_7b_multiband_ga_final_best_v10_cn.svg` | Final best overlap after 12 generations per band |
| `figure_5_7c_holdout_truth_vs_prediction_v10_cn.svg` | Near-best holdout truth vs v10 prediction |
| `figure_5_7d_candidate_pool_predicted_best_v10_cn.svg` | Expanded candidate pool prediction results |

The holdout figure is **not** the main predictor-vs-GA comparison. It is evidence that v10 learned high-potential regions without directly training on the withheld near-best samples.

## Deprecated Or Diagnostic Artifacts

These directories may remain in the repository for traceability, but should not be cited as final thesis evidence.

| Path | Reason not final |
|---|---|
| `data/analysis/targetband_four_arm_baseline_v1/` | Older predictor/comparison version |
| `data/analysis/targetband_four_arm_baseline_v10_v1/` | Used v10 scoring but accidentally filtered the predictor candidates back to the old `rf09_h00_center` initial pool |
| `data/prediction_targetband_param_v1/v1/windows_dense_v9_active_ga_mid_aug_v1/` | Single-band active-learning intermediate dataset |
| `data/analysis/targetband_active_learning_v9/` | Diagnostic comparison before multiband v10 |

## Reproducibility Entry Points

| Task | Entrypoint |
|---|---|
| Build v10 active-learning dataset | `prediction_targetband_param_v1/tools/build_active_learning_augmented_dataset_v10.py` |
| Evaluate v10 holdout | `prediction_targetband_param_v1/tools/evaluate_active_learning_holdout_v10.py` |
| Build multiband candidate pool | `optimization/seed_ranking/build_active_ga_multiband_neighborhood_candidate_pool_v1.py` |
| Score candidates with v10 model | `optimization/seed_ranking/run_targetband_seed_scoring_v1.py` with v10 model roots |
| Build full-pool v10 comparison manifest | `optimization/seed_ranking/build_targetband_baseline_v10_manifest_v1.py --point-id __all__` |
| Run full-pool v10 COMSOL validation | `runners/run_stage4_validation_targetband_baseline_v10_fullpool_v1.m` |
| Plot final v10 Chinese comparison SVGs | `runners/run_plot_targetband_four_arm_baseline_v10_cn.m` |
| Plot active-learning Chinese SVG bundle | `runners/run_plot_targetband_chinese_svg_bundle_v1.m` |

## Thesis Wording Boundary

Use this claim boundary:

The conditional predictor is a low-budget candidate-prioritization model. It is trained without the near-best holdout samples and without the 40 Hz long-run GA endpoint. It can identify near-optimal candidates in the expanded candidate pool, while the final physical confirmation and absolute optimum still depend on COMSOL validation and real GA search.

Avoid this overclaim:

The predictor replaces COMSOL or GA optimization.
