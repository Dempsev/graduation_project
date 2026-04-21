# Target-Band Mainline Freeze V1

## Purpose

This document formalizes the first explicit freeze of the thesis-facing target-band mainline.

The goal is simple:

- stop reopening the basic mainline definition every few days
- keep experiment interpretation consistent
- let later results be compared against a fixed reference stack

This freeze is active until clearly stronger evidence justifies replacing part of it.

## Frozen Items

### 1. Thesis Claim

The working thesis claim is frozen as:

**The project establishes a target-band-conditioned prediction and inverse-design workflow inside the thesis band catalog, where a conditional predictor proposes candidates for a specified band, band-aware search/refinement improves them under real COMSOL evaluation, and the final structures are validated as usable target-band designs.**

### 2. Thesis Band Catalog

The active thesis band catalog is frozen as:

- `prediction_targetband_param_v1/configs/thesis_band_catalog_v2.json`

The current serving bands are:

- `band140_180`
- `band160_200`
- `band180_220`
- `band200_240`
- `band220_260`
- `band240_280`

### 3. Default Dataset

The default training dataset is frozen as:

- tag: `windows_dense_v8_truth_plus_exploratory_aug_v1`
- path: `data/prediction_targetband_param_v1/v1/windows_dense_v8_truth_plus_exploratory_aug_v1/targetband_parametric_v1.csv`

This replaces earlier `v5`, `v6`, and `v7` as the main thesis-facing dataset.

### 4. Default Model Pair

The main prediction stack is frozen as:

- classifier: `RF`
- regressor: `HGB`

Current reference runs are:

- classifier:
  - `data/prediction_targetband_param_v1_runs/param_targetband_cls_rf_dense_v8_cmp_v1/`
- regressor:
  - `data/prediction_targetband_param_v1_runs/param_targetband_cover_hgb_dense_v8_cmp_v1/`

### 5. Shape-Aware Front-End

The current shape front-end is frozen as:

- `data/analysis/targetband_shape_atlas_v1/`

Its role is:

- band-aware shape selection
- family-balanced pool construction
- role-aware shape retention

This means the project no longer treats shape as a passive background variable selected only by old `gap34_gain_Hz`.

## Why This Freeze Is Justified

The freeze is not arbitrary. It reflects the current strongest integrated evidence:

- the predictor stack is already stable enough for inverse-design use
- the shape-aware front-end materially changes weak-band search behavior
- exploratory weak-band search has produced strong real-COMSOL cases
- the new truth has already been harvested back into `v8`

In other words, the project now has a coherent stack rather than isolated pieces.

## What This Freeze Does Not Mean

This freeze does **not** mean:

- no future model improvement is allowed
- no future band catalog revision is allowed
- no future material-profile extension is allowed

It means:

- such changes should now be treated as deliberate upgrades
- they should be compared against the frozen stack
- they should not silently replace the current thesis mainline

## Upgrade Rule

The following rule is now active:

**Do not reopen model-family choice, dataset-mainline choice, or basic target-band problem definition unless strong new evidence clearly outperforms the frozen stack or solves a limitation that the frozen stack cannot reasonably address.**

## Immediate Follow-Up

After this freeze, the default next actions are:

1. produce a predictor-readiness report
2. formalize canonical inverse-design case studies
3. standardize baseline comparisons
4. track weak-band coverage as a standing analysis item

That is, the project should now prioritize evidence packaging and case-study consolidation over re-debating the mainline itself.
