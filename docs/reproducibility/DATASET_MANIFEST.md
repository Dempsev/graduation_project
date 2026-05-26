# Dataset Manifest

This file documents the important local datasets and generated result roots
used by the final thesis workflow. The actual data under `data/` are ignored by
git because they include COMSOL outputs, model checkpoints, and large run
artifacts.

## Target Bands

The final thesis uses six 40 Hz target bands:

| Tag | Frequency range |
| --- | --- |
| `band140_180` | 140-180 Hz |
| `band160_200` | 160-200 Hz |
| `band180_220` | 180-220 Hz |
| `band200_240` | 200-240 Hz |
| `band220_260` | 220-260 Hz |
| `band240_280` | 240-280 Hz |

## Key Local Data Roots

| Root | Role | Git policy |
| --- | --- | --- |
| `data/comsol_batch/` | COMSOL truth outputs, Stage4 validations, real-GA histories | ignored |
| `data/prediction_targetband_param_v1/` | Built target-band datasets | ignored |
| `data/prediction_targetband_param_v1_runs/` | Predictor model runs, metrics, checkpoints | ignored |
| `data/ml_runs/` | Candidate scoring and local refinement outputs | ignored |
| `data/analysis/` | Analysis outputs used by figures/reports | ignored |
| `data/research_validation/` | Chapter-specific intermediate data | ignored |

## Research Validation Output Policy

The source scripts and Markdown notes under `research_validation/` are part of
the public repository. Generated chapter payloads in that tree are ignored:

- CSV summary tables
- rendered PNG/SVG/PDF figures
- local JSON/TXT checklists

Use `scripts/make_figures/` as the public entrypoint layer and regenerate these
outputs locally when reviewing thesis evidence.

## Final Dataset Versions

| Dataset tag | Path | Role |
| --- | --- | --- |
| `windows_dense_v8_truth_plus_exploratory_aug_v1` | `data/prediction_targetband_param_v1/v1/windows_dense_v8_truth_plus_exploratory_aug_v1/targetband_parametric_v1.csv` | Older frozen RF/HGB thesis-mainline dataset |
| `windows_dense_v10_multiband_active_ga_mid_aug_v1` | `data/prediction_targetband_param_v1/v1/windows_dense_v10_multiband_active_ga_mid_aug_v1/` | Active-GA augmented comparison dataset |
| `windows_dense_v11_12gen_freeze_v1` | `data/prediction_targetband_param_v1/v1/windows_dense_v11_12gen_freeze_v1/` | V11 freeze experiment dataset |
| `windows_dense_v12_all_history_ga20_clean_v1` | `data/prediction_targetband_param_v1/v1/windows_dense_v12_all_history_ga20_clean_v1/` | Final all-history + GA20 clean dataset used by chapter-3/5 evidence |

## Common Target-Band Fields

| Field | Meaning |
| --- | --- |
| `shape_id` | Structure contour or geometry identifier |
| `shape_family` | Higher-level structure family/archetype |
| `point_id` | Parametric point or perturbation identifier |
| `target_band_low_Hz` | Lower bound of target band |
| `target_band_high_Hz` | Upper bound of target band |
| `target_band_width_Hz` | Target-band width, usually 40 Hz |
| `active_open` | Whether the real bandgap overlaps the target band |
| `target_overlap_Hz` | Real overlap width between COMSOL bandgap and target band |
| `cover_ratio` | `target_overlap_Hz / target_band_width_Hz` |
| `gap_lower_Hz` | Lower edge of the relevant real bandgap |
| `gap_upper_Hz` | Upper edge of the relevant real bandgap |
| `geometry_valid` | Geometry generation validity flag |
| `contact_valid` | Contact/intersection validity flag |
| `solve_success` | COMSOL solve success flag |

## Model Output Fields

| Field | Meaning |
| --- | --- |
| `predicted_open_prob` | Classifier probability that the target band opens |
| `predicted_cover_ratio` | Regressor estimate of target-band coverage |
| `predicted_overlap_Hz` | Predicted overlap in Hz |
| `predicted_score` | Combined ranking score used for candidate sorting |
| `rank_in_method` | Rank within predictor or baseline method |

## Validation Leakage Tags

The final chapter-5 validation distinguishes screening and independent
evidence:

| Tag | Meaning |
| --- | --- |
| `seen_in_training` | Candidate appears in training data; useful for engineering screening but not independent holdout |
| `seen_in_ga20` | Candidate appears in GA20 history |
| `independent_holdout` | Candidate excluded from training, GA20 history, and previous validation sets |

## Manifest Rule

Before a result is described as physical validation evidence, it must be clear
whether the value came from:

- real COMSOL dispersion calculation;
- real COMSOL-in-loop GA fitness history;
- predictor ranking only;
- random baseline verification;
- postprocess aggregation of completed runs.
