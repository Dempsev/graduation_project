# COAD: Physics-Data Co-Optimization for Mechanical Metastructure Design

## Overview

This repository contains the full working codebase for a graduation-project workflow on **bandgap-oriented design of mechanical / phononic metastructures**.

The project is not a single surrogate-model demo. It is a research workflow that combines:

1. physical truth production with COMSOL + MATLAB
2. truth accumulation from snake-generated shapes, Fourier perturbations, and later validation rounds
3. prediction / modeling over the accumulated truth
4. search / optimization using real truth or model guidance

Phase 1 now interprets the repository through a thesis-facing three-layer architecture:

1. `physics_pipeline/` as the **truth layer**
2. `prediction/` as the **model layer**
3. `optimization/` as the **search layer**

The historical `stage*` and `stage3_training/` paths are preserved, but they are no
longer the preferred top-level reading path.

## Current Research Status

The current thesis-facing picture is:

- the physical baseline is fixed around the soft-matrix / hard-inclusion setup and the trusted reference point
- the repository already contains a large accumulated body of real physical truth from `stage1` through `stage4_validation`
- global and fixed-gap prediction lines are working baselines
- target-band conditional prediction has already been established as the next modeling direction
- real COMSOL-in-loop GA now provides the strongest current real-search baseline

The most important optimization interpretation change is:

- `seed` is still useful
- but only as a **low-cost candidate-generation and comparison baseline**
- not as the final optimization mainline

That means the repository should now be read as:

- truth first
- model second
- search third

rather than as one mixed seed-first stage3 storyline.

## Repository Layout

### Historical Layout

```text
coad/
  model_core/                Core COMSOL geometry / material / result helpers
  stage1/                    Early stage utilities and screening helpers
  stage2/                    Low-order Fourier robustness screening logic
  stage2_refine/             Low-order parameter refinement logic
  stage2_harmonics/          Higher-order harmonics screening logic
  stage2_harmonics_refine/   Higher-order refinement logic
  stage3_dataset/            Dataset builders for versioned ML datasets
  stage3_training/           Model training, scoring, candidate-pool builders
  stage4_validation/         Validation config and summary-table writers
  runners/                   MATLAB entry points for all major batch workflows
  preprocess/                Shape / contour preprocessing utilities
  postprocess/               tbl1 analysis and plotting utilities
  snake/                     Snake-based random binary shape generation
  data/                      Generated artifacts only (ignored by git)
  README.md
  README_CN.md
  .gitignore
```

### Phase-1 Thesis-Facing Layout

```text
coad/
  physics_pipeline/         Truth-layer entry for physical data production
  prediction/               Model-layer entry for prediction and target-band modeling
  optimization/             Search-layer entry for baseline and real optimization
  baselines/                Historical or comparison workflows
  shared/                   Future home for extracted shared helpers

  stage1/                   Historical physical truth production
  stage2/                   Historical physical truth production
  stage2_refine/            Historical physical truth production
  stage2_harmonics/         Historical physical truth production
  stage2_harmonics_refine/  Historical physical truth production
  stage3_dataset/           Historical dataset builders
  stage3_training/          Historical mixed mainline / baseline source
  stage3_prediction/        Historical compatibility layer
  stage3_optimization/      Historical compatibility layer
  stage3_optimization_real_ga/
                           Historical compatibility layer
  stage4_validation/        Historical physical validation stage
```

### Current Directory Interpretation

- `physics_pipeline/`
  - official Phase-1 entry for **physical truth production**
- `prediction/`
  - official Phase-1 entry for **prediction / modeling**
- `optimization/`
  - official Phase-1 entry for **search / optimization**
- `baselines/`
  - home for historical or comparison routes
- `stage3_training/`
  - legacy mixed mainline and baseline source, not the preferred top-level narrative

## How To Read The Repository Now

### 1. Truth Layer

Use:

- `physics_pipeline/`

Implementation roots remain in:

- `stage1/`
- `stage2/`
- `stage2_refine/`
- `stage2_harmonics/`
- `stage2_harmonics_refine/`
- `stage4_validation/`

### 2. Model Layer

Use:

- `prediction/`

Interpretation:

- global bandgap prediction remains the modeling baseline
- target-band conditional prediction is the planned modeling mainline

Relevant directories include:

- `prediction/`
- `prediction_v2/` to `prediction_v7/`
- `prediction_targetband_v1/`
- `prediction_targetband_param_v1/`

### 3. Search Layer

Use:

- `optimization/`

Interpretation:

- `optimization/seed_ranking/` is the low-cost baseline / front-end
- `optimization/real_comsol_ga/` contains the current real-search strong baseline
- target-band-conditioned optimization is the planned next mainline

Initial executable target-band prototypes now exist at:

- `optimization/seed_ranking/run_targetband_seed_scoring_v1.py`
- `optimization/seed_ranking/run_targetband_local_ga_v1.py`

## Optimization Positioning In Phase 1

The optimization layer now contains three roles:

1. **Seed ranking baseline**
   - cheap candidate generation
   - historical comparison route
   - not the final optimization mainline
2. **True global real-GA baseline**
   - current strongest real-search baseline
   - direct COMSOL-in-loop search without surrogate-only drift
3. **Target-band-conditioned optimization**
   - next planned thesis-facing mainline after the Phase-1 cleanup

This means the old seed-first narrative should now be interpreted as a baseline,
not as the final thesis search definition.

## Recommended Reading Order

If you want the current thesis-facing structure, read in this order:

1. `physics_pipeline/`
2. `prediction/`
3. `optimization/`
4. `baselines/`

If you need historical context afterward, then read:

- `stage3_training/`

## Default Next-Step Order

Phase 1 fixes the architecture language first.

The default next-step order is now fixed as:

1. architecture cleanup first
2. target-band execution second

So this round does **not**:

- move directories
- rename runners
- rewrite COMSOL solver logic
- remove seed code

It only makes the repository mainline and baseline positions explicit.

## Environment

Typical environment used by this project:

- MATLAB
- COMSOL with MATLAB LiveLink
- Python 3
- Python packages used in the ML/training utilities:
  - `numpy`
  - `pandas`
  - `torch`
  - `matplotlib`

## Commit and Data Policy

This repository tracks **source code and documentation**, not generated research outputs.

- All generated tables, manifests, model checkpoints, COMSOL outputs, plots, and logs live under `data/`.
- `data/` is git-ignored on purpose.
- Commit only the code that defines the workflow, not the results produced by running it.

## What This Repository Is Good For

This codebase is appropriate for:

- reproducing the workflow logic used in the thesis
- understanding the truth / model / search separation
- continuing target-band or global-search oriented work after the Phase-1 cleanup
- using historical stage and seed routes as baselines or comparison points
- writing methods and workflow sections of the thesis from real code

It is not intended to be a polished end-user software package. It is a research codebase with preserved experiment history.
