# Research Validation Workspace

This directory contains chapter-specific validation and figure-building
workflows used by the final thesis evidence map.

## Git Policy

Track:

- reusable Python scripts
- reusable MATLAB scripts
- lightweight Markdown reports and notes
- this directory-level index

Do not track generated payloads here:

- `*.csv`
- `*.png`
- `*.svg`
- `*.pdf`
- `*.txt`
- `*.json`

The generated files remain useful locally, but they are reproducible from the
tracked scripts plus the ignored data roots documented in
`docs/reproducibility/DATASET_MANIFEST.md`.

## Public Entrypoints

The public wrappers for the most important chapter evidence builders live under
`scripts/make_figures/`. Use those wrappers first when possible, then inspect
the chapter subdirectories here for the lower-level implementation details.

## Chapter Map

| Folder | Role |
| --- | --- |
| `ch2_typical_dispersion/` | Chapter-2 typical dispersion, reliability, and perturbation evidence |
| `ch3_predictor_v12_figures/` | Chapter-3 V12 predictor metrics and thesis tables |
| `ch4_ga_real_optimization/` | Chapter-4 six-band real COMSOL-in-loop GA evidence |
| `ch5_prediction_vs_ga/` | Chapter-5 predictor, random baseline, and GA comparison |
| `ch5_strict_holdout_validation/` | Chapter-5 independent holdout COMSOL validation |
| `ch5_fourier_only_ablation/` | Chapter-5 Fourier-only ablation and high-frequency boundary evidence |
