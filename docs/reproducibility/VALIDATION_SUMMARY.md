# Validation Summary

Chapter 5 compares three evidence types:

1. Predictor-ranked candidates.
2. Same-budget random candidates.
3. Real COMSOL-in-loop GA baselines.

The main source roots are:

- `research_validation/ch5_prediction_vs_ga/`
- `research_validation/ch5_strict_holdout_validation/`
- `data/comsol_batch/ch5_strict_holdout_validation_top5_random5/`

## Evidence Boundary

| Evidence type | Physical status | Thesis role |
| --- | --- | --- |
| Predictor score | Not physical truth | Candidate screening and budget allocation |
| Predictor Top5 with COMSOL verification | Physical after COMSOL solve | Demonstrates ranking value |
| Random candidates with COMSOL verification | Physical after COMSOL solve | Same-budget baseline |
| COMSOL-GA | Physical throughout optimization | Optimization baseline |

## Main Findings

- Predictor-selected candidates beat random candidates in most target bands
  under the same limited verification budget.
- 180-220 Hz and 200-240 Hz are the strongest cases for predictor screening:
  the screened candidates can approach the GA baseline with far fewer COMSOL
  evaluations.
- 240-280 Hz remains weak across predictor, random, and GA evidence. This
  should be framed as a structure-family/parameter-space boundary.

## Final Figures

| Figure family | Source |
| --- | --- |
| Top5/random active-rate comparison | `research_validation/ch5_prediction_vs_ga/figures/ch5_fig5_2_topk_random_active_rate.*` |
| Best-overlap comparison | `research_validation/ch5_prediction_vs_ga/figures/ch5_fig5_3_best_overlap_compare.*` |
| Top5-to-GA ratio | `research_validation/ch5_prediction_vs_ga/figures/ch5_fig5_5_topk_to_ga_ratio.*` |
| Budget-efficiency curve | `research_validation/ch5_prediction_vs_ga/figures/ch5_fig5_6_budget_best_overlap_curve.*` |
| Typical unit-cell comparison | `research_validation/ch5_prediction_vs_ga/figures/ch5_fig5_9_typical_unit_cell_compare.*` |
| Typical dispersion comparison | `research_validation/ch5_prediction_vs_ga/figures/ch5_fig5_10_typical_dispersion_compare.*` |
| High-frequency boundary | `research_validation/ch5_prediction_vs_ga/figures/ch5_fig5_11_highfreq_boundary_analysis.*` |
