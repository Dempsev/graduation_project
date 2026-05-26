# COMSOL Script Index

This index separates safe postprocess scripts from scripts that may start
MATLAB, COMSOL, LiveLink, Stage4 validation, or real COMSOL-in-loop GA.

For the P4 status of the remaining top-level `runners/` directory, see
`docs/project/RUNNER_RISK_INDEX.md`.

Risk levels:

- `SAFE`: Reads existing CSV/JSON/MAT outputs and writes reports or plots.
- `MATLAB`: Starts MATLAB but should only postprocess/export if inputs exist.
- `COMSOL`: Opens or controls COMSOL models; can be slow.
- `REAL_GA`: Runs COMSOL inside optimization loops; long and expensive.

## Real COMSOL-In-Loop GA

| Risk | Script | Purpose |
| --- | --- | --- |
| `REAL_GA` | `optimization/real_comsol_ga/run_comsol_in_loop_band_catalog_ga_v1.m` | Six-band thesis GA baseline runner |
| `REAL_GA` | `optimization/real_comsol_ga/run_comsol_in_loop_ga_v1.m` | Earlier real-GA runner |
| `REAL_GA` | `optimization/real_comsol_ga/run_comsol_in_loop_global_ga_v1.m` | Global real-GA route |
| `REAL_GA` | `optimization/real_comsol_ga/run_comsol_in_loop_champion_local_v3.m` | Champion local refinement route |
| `REAL_GA` | `scripts/run_comsol/run_real_ga_thesis_band_overlap_v1.m` | Public thesis-band real-GA wrapper |
| `REAL_GA` | `scripts/run_comsol/run_real_ga_targetband180_220_overlap_v1.m` | Public 180-220 Hz real-GA wrapper |
| `REAL_GA` | `scripts/run_comsol/run_real_ga_fourier_only_band_v1.m` | Public Fourier-only ablation GA wrapper |
| `REAL_GA` | `scripts/run_comsol/run_real_ga_fourier_only_bands_ga20_v1.m` | Public Fourier-only multi-band GA wrapper |

## Stage4 Validation

| Risk | Script | Purpose |
| --- | --- | --- |
| `COMSOL` | `runners/run_stage4_validation_multiband_predictor_top1_v1.m` | Multiband predictor Top1 validation |
| `COMSOL` | `runners/run_stage4_tb180_predictor_top6_v11_freeze.m` | 180-220 predictor Top6 validation |
| `COMSOL` | `runners/run_stage4_tb180_random6_v11_freeze.m` | 180-220 random6 validation |
| `COMSOL` | `scripts/run_comsol/run_comsol_stage4_targetband_top6_v1.m` | Public thesis target-band Top6 validation wrapper |
| `COMSOL` | `scripts/run_comsol/run_comsol_stage4_targetband_v1.m` | Public supplementary target-band validation wrapper |
| `COMSOL` | `runners/run_stage4_validation_targetband_baseline_v10_fullpool_v1.m` | V10 full-pool target-band baseline validation |
| `COMSOL` | `runners/run_stage4_validation_targetband_baseline_v10_v1.m` | V10 target-band baseline validation |
| `COMSOL` | `runners/run_stage4_validation_targetband_baseline_abc_v1.m` | ABC baseline validation |
| `COMSOL` | `research_validation/ch5_strict_holdout_validation/run_ch5_strict_holdout_comsol_manifest_v1.m` | Strict holdout Top5/random COMSOL manifest validation |

## MATLAB/COMSOL Export Helpers

| Risk | Script | Purpose |
| --- | --- | --- |
| `MATLAB` | `postprocess/run_ch2_mesh_export_via_python312.py` | Starts COMSOL server and MATLAB for chapter-2 mesh export |
| `MATLAB` | `postprocess/run_ch2_structure_assets_via_python312.py` | Starts COMSOL server and MATLAB for chapter-2 structure assets |
| `MATLAB` | `research_validation/ch2_typical_dispersion/run_ch2_typical_local_perturb_via_engine_v1.py` | MATLAB-engine wrapper for local perturbation validation |
| `COMSOL` | `research_validation/ch2_typical_dispersion/run_ch2_typical_local_perturb_validation_v1.m` | Chapter-2 COMSOL perturbation validation |
| `MATLAB` | `research_validation/ch4_ga_real_optimization/run_ch4_comsol_unit_cell_export.py` | Exports final GA unit-cell figures through MATLAB/COMSOL |
| `MATLAB` | `research_validation/ch5_fourier_only_ablation/run_fourier_only_ablation_geometry_export_v1.py` | Exports Fourier-only ablation unit-cell figures |

## Safe Postprocess And Report Builders

| Risk | Script | Purpose |
| --- | --- | --- |
| `SAFE` | `scripts/make_figures/ch2/build_ch2_typical_stats_v1.py` | Public wrapper for chapter-2 typical stats |
| `SAFE` | `scripts/make_figures/ch3/build_ch3_predictor_v12_report.py` | Public wrapper for chapter-3 predictor evidence |
| `SAFE` | `scripts/make_figures/ch4/build_ch4_ga_real_optimization_assets_20gen.py` | Public wrapper for chapter-4 GA evidence |
| `SAFE` | `scripts/make_figures/ch5/build_ch5_prediction_vs_ga_v12.py` | Public wrapper for chapter-5 comparison evidence |
| `SAFE` | `scripts/make_figures/ch5/build_ch5_strict_holdout_validation_v1.py` | Public wrapper for strict holdout summaries |
| `SAFE` | `scripts/make_figures/ch5/build_fourier_only_ablation_v1.py` | Public wrapper for Fourier-only ablation summaries |
| `SAFE` | `research_validation/ch3_predictor_v12_figures/build_ch3_predictor_v12_report.py` | Builds chapter-3 model metric report/figures |
| `SAFE` | `research_validation/ch4_ga_real_optimization/build_ch4_ga_real_optimization_assets_20gen.py` | Builds chapter-4 GA tables and figures from existing outputs |
| `SAFE` | `research_validation/ch5_prediction_vs_ga/build_ch5_prediction_vs_ga_v12.py` | Builds chapter-5 prediction/random/GA comparison assets |
| `SAFE` | `research_validation/ch5_strict_holdout_validation/build_ch5_strict_holdout_validation_v1.py` | Builds strict holdout summaries from completed COMSOL validations |
| `SAFE` | `research_validation/ch5_fourier_only_ablation/build_fourier_only_ablation_v1.py` | Builds Fourier-only ablation summaries |
| `SAFE` | `postprocess/plot_bandgap_summary.py` | Plots bandgap summaries from existing postprocess CSVs |
| `SAFE` | `postprocess/plot_tb180_220_method_compare_v11_freeze_cn.py` | Plots 180-220 Hz method comparison from existing outputs |

## Public Refactor Rule

All `COMSOL` and `REAL_GA` scripts should eventually move under
`scripts/run_ga/` or `scripts/export_results/` with clear warnings and local
environment configuration. Safe postprocess scripts should move under
`scripts/make_figures/` or `scripts/export_results/`.
