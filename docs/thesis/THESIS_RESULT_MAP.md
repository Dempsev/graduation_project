# Thesis Result Map

This file maps the final thesis chapters to the repository evidence used after
the public refactor.

## Chapter 2

Topic: periodic structure model, COMSOL dispersion calculation, mesh and
typical-response analysis.

Evidence:

- `model_core/`
- `physics_pipeline/`
- `research_validation/ch2_typical_dispersion/`
- `postprocess/export_ch2_snake_fourier_overlay_mesh_v1.m`
- `postprocess/export_ch2_structure_construction_assets_v1.m`

## Chapter 3

Topic: target-band conditional prediction.

Evidence:

- `src/prediction/targetband_param/`
- `data/prediction_targetband_param_v1/v1/windows_dense_v12_all_history_ga20_clean_v1/`
- `data/analysis/predictor_readiness_v12_all_history_ga20_clean_v1/`
- `research_validation/ch3_predictor_v12_figures/`

Claim boundary:

- The classifier/regressor ranks and screens candidates.
- It does not replace finite-element dispersion calculation.

## Chapter 4

Topic: real COMSOL-in-loop genetic optimization.

Evidence:

- `optimization/real_comsol_ga/`
- `data/comsol_batch/comsol_in_loop_thesis_band*_overlap_ga_v1/`
- `data/comsol_batch/comsol_in_loop_targetband180_220_overlap_ga_v1/`
- `research_validation/ch4_ga_real_optimization/`

Claim boundary:

- GA fitness is true COMSOL target-band overlap.
- The six-band 20-generation result is the optimization baseline.

## Chapter 5

Topic: predictor screening versus random candidates and real GA baseline.

Evidence:

- `research_validation/ch5_prediction_vs_ga/`
- `research_validation/ch5_strict_holdout_validation/`
- `research_validation/ch5_fourier_only_ablation/`
- `stage4_validation/`

Claim boundary:

- Predictor Top5 is valuable when it reduces validation budget or approaches
  GA results after COMSOL verification.
- High-frequency weak bands are a limitation of the current design space, not
  a predictor-only failure.

## Chapter 6

Topic: conclusion and outlook.

Use the following final framing:

- Physical truth comes from COMSOL dispersion calculation.
- Prediction is a screening and ranking layer.
- Real COMSOL-in-loop GA is the optimization benchmark.
- Final performance claims require COMSOL-backed validation.
- Future work should expand high-frequency structure families and improve
  physics-informed features.
