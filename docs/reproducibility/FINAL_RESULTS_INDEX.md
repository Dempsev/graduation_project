# Final Results Index

This index maps the final thesis figures, tables, and result claims to local
data roots and scripts. It intentionally points to generated data under
`data/` and `output/` without committing those large artifacts.

## Chapter-Level Evidence Roots

| Chapter | Evidence root | Role |
| --- | --- | --- |
| Chapter 2 | `research_validation/ch2_typical_dispersion/` | Typical dispersion cases, reliability stats, local perturbation evidence |
| Chapter 3 | `research_validation/ch3_predictor_v12_figures/` | V12 dataset/model metric figures and tables |
| Chapter 4 | `research_validation/ch4_ga_real_optimization/` | Six-band 20-generation real COMSOL-in-loop GA summary |
| Chapter 5 | `research_validation/ch5_prediction_vs_ga/` | Predictor Top-k, random, and GA comparison figures |
| Chapter 5 strict holdout | `research_validation/ch5_strict_holdout_validation/` | Independent Top5/random COMSOL validation |
| Chapter 5 ablation | `research_validation/ch5_fourier_only_ablation/` | Fourier-only ablation and high-frequency boundary evidence |

## Key Thesis Results

| Chapter | Figure/table | Name | Data source | Script | Output path | Used in thesis | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | Fig. 2 typical | Typical dispersion and structure construction | `data/research_validation/ch2_typical_dispersion/` | `research_validation/ch2_typical_dispersion/build_ch2_typical_stats_v1.py` | `research_validation/ch2_typical_dispersion/` | Yes | Includes chapter-2 numerical-analysis support |
| 3 | Fig. 3 metrics | V12 conditional predictor metrics | `data/analysis/predictor_readiness_v12_all_history_ga20_clean_v1/` | `research_validation/ch3_predictor_v12_figures/build_ch3_predictor_v12_report.py` | `research_validation/ch3_predictor_v12_figures/` | Yes | RF/HGB predictor framing |
| 3 | Table 3 | V12 dataset and predictor evidence tables | `data/prediction_targetband_param_v1/v1/windows_dense_v12_all_history_ga20_clean_v1/` | `src/prediction/targetband_param/tools/build_thesis_ga20_all_data_dataset_v12.py` | `research_validation/ch3_predictor_v12_figures/CH3_V12_EVIDENCE_TABLES_AND_DRAFT_CN.md` | Yes | Prediction remains a screening model |
| 4 | Fig. 4-1 | Real GA workflow | `data/comsol_batch/comsol_in_loop_thesis_band*_overlap_ga_v1/` | `research_validation/ch4_ga_real_optimization/build_ch4_ga_real_optimization_assets_20gen.py` | `research_validation/ch4_ga_real_optimization/figures/ch4_fig4_1_real_ga_flowchart.*` | Yes | Workflow figure |
| 4 | Fig. 4-3 | GA convergence curves | Six-band GA directories under `data/comsol_batch/` | same as above | `research_validation/ch4_ga_real_optimization/figures/ch4_fig4_3_ga_convergence_20gen.*` | Yes | 20 generations, 120 evaluations per band |
| 4 | Fig. 4-4 | Best target-band overlap | `research_validation/ch4_ga_real_optimization/ch4_ga_summary_20gen.csv` | same as above | `research_validation/ch4_ga_real_optimization/figures/ch4_fig4_4_best_overlap_bar_20gen.*` | Yes | Six target bands |
| 4 | Fig. 4-6 | Best unit cells | Six-band GA output directories | `research_validation/ch4_ga_real_optimization/run_ch4_comsol_unit_cell_export.py` | `research_validation/ch4_ga_real_optimization/figures/ch4_fig4_6_*` | Yes | MATLAB/COMSOL export helper |
| 5 | Fig. 5-1 | Comparison workflow | `research_validation/ch5_prediction_vs_ga/ch5_unified_candidate_comparison.csv` | `research_validation/ch5_prediction_vs_ga/build_ch5_prediction_vs_ga_v12.py` | `research_validation/ch5_prediction_vs_ga/figures/ch5_fig5_1_comparison_workflow.*` | Yes | Top-k/random/GA comparison setup |
| 5 | Fig. 5-2 | Top5 vs random active rate | same as above | same as above | `research_validation/ch5_prediction_vs_ga/figures/ch5_fig5_2_topk_random_active_rate.*` | Yes | Same verification-budget comparison |
| 5 | Fig. 5-3 | Best overlap comparison | same as above | same as above | `research_validation/ch5_prediction_vs_ga/figures/ch5_fig5_3_best_overlap_compare.*` | Yes | Predictor Top5 usually beats random |
| 5 | Fig. 5-5 | Top5 / GA ratio | same as above | same as above | `research_validation/ch5_prediction_vs_ga/figures/ch5_fig5_5_topk_to_ga_ratio.*` | Yes | Shows near-GA behavior in selected bands |
| 5 | Fig. 5-6 | Budget-efficiency curve | strict holdout and GA summaries | same as above | `research_validation/ch5_prediction_vs_ga/figures/ch5_fig5_6_budget_best_overlap_curve.*` | Yes | Highlights reduced validation budget |
| 5 | Fig. 5-9/5-10 | Typical unit-cell and dispersion comparison | chapter-5 comparison CSVs and COMSOL exports | same as above plus MATLAB exports | `research_validation/ch5_prediction_vs_ga/figures/ch5_fig5_9_*`, `ch5_fig5_10_*` | Yes | Case-level physical comparison |
| 5 | Fig. 5-11 | High-frequency boundary analysis | high-frequency GA and ablation data | same as above | `research_validation/ch5_prediction_vs_ga/figures/ch5_fig5_11_highfreq_boundary_analysis.*` | Yes | Boundary of current design space |

## Selected Real-GA Six-Band Summary

| Target band | GA output directory | Evaluations | Best overlap Hz | Best cover ratio | Note |
| --- | --- | ---: | ---: | ---: | --- |
| 140-180 Hz | `data/comsol_batch/comsol_in_loop_thesis_band140_180_overlap_ga_v1/` | 120 | 22.2665 | 0.5567 | 20-generation run |
| 160-200 Hz | `data/comsol_batch/comsol_in_loop_thesis_band160_200_overlap_ga_v1/` | 120 | 32.4455 | 0.8111 | 20-generation run |
| 180-220 Hz | `data/comsol_batch/comsol_in_loop_targetband180_220_overlap_ga_v1/` | 120 | 40.0000 | 1.0000 | Full target coverage |
| 200-240 Hz | `data/comsol_batch/comsol_in_loop_thesis_band200_240_overlap_ga_v1/` | 120 | 35.2829 | 0.8821 | Strong coverage |
| 220-260 Hz | `data/comsol_batch/comsol_in_loop_thesis_band220_260_overlap_ga_v1/` | 120 | 4.0976 | 0.1024 | High-frequency weak band |
| 240-280 Hz | `data/comsol_batch/comsol_in_loop_thesis_band240_280_overlap_ga_v1/` | 120 | 3.9345 | 0.0984 | High-frequency weak band |

## Boundary Notes

- `prediction_topk` results are screening and ranking evidence, not physical
  authority by themselves.
- `random` results are same-budget comparison evidence.
- `COMSOL-GA` results use real target-band overlap from COMSOL as fitness and
  serve as the optimization baseline.
- High-frequency weak-band results should be presented as a design-space
  limitation, not a model-only failure.
