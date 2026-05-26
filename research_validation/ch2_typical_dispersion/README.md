# Chapter 2.6 Typical Dispersion And Local Perturbation Analysis

This folder contains the reusable scripts for thesis section 2.6.

## Reproduction

1. Build current typical-case manifest:
   `D:\python312\python.exe research_validation/ch2_typical_dispersion/build_ch2_typical_center_manifest_v1.py`

2. Run COMSOL truth evaluations through a shared COMSOL MATLAB engine:
   `D:\python312\python.exe research_validation/ch2_typical_dispersion/run_ch2_typical_local_perturb_via_engine_v1.py --start 1 --max-count 0`

3. Build summary tables:
   `D:\python312\python.exe research_validation/ch2_typical_dispersion/build_ch2_typical_stats_v1.py`

4. Export figures:
   `D:\python312\python.exe research_validation/ch2_typical_dispersion/export_ch2_typical_figures_via_engine_v1.py`

## Outputs

- Case summary: `D:\graduation_project\coad\data\research_validation\ch2_typical_dispersion\ch2_typical_dispersion_case_summary.csv`
- Robustness statistics: `D:\graduation_project\coad\data\research_validation\ch2_typical_dispersion\ch2_local_robustness_stats.csv`
- Variant results: `D:\graduation_project\coad\data\research_validation\ch2_typical_dispersion\ch2_local_perturb_variant_results.csv`
- Raw COMSOL tbl1 exports: `D:\graduation_project\coad\data\research_validation\ch2_typical_dispersion\tbl1_exports`

The local perturbation plan reuses the old thesis setup: a1 +/- 0.01,
a2 +/- 0.01, b2 +/- 0.01, and r0 +/- 0.0008.
