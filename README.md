# COAD: Physics-Data Co-Optimization for Mechanical Metastructure Design

## Overview

This repository contains the full working codebase for a graduation-project workflow on **bandgap-oriented design of mechanical / phononic metastructures**.

The project is not a single surrogate-model demo. It is a closed loop that combines:

1. COMSOL + MATLAB physical screening
2. database construction from random snake shapes, low-order Fourier perturbations, and higher-order harmonics
3. classifier / regressor training
4. cascade-style candidate ranking
5. physical re-validation back in COMSOL

The current codebase preserves the full iteration history from `v1` to `v10` and is organized around the research finding that **broad-transfer points do not generalize reliably, while targeted exploitation does**.

## Current Research Status

The main thesis storyline is now stable.

- The physical evaluation baseline is fixed: soft matrix + hard inclusion, trusted baseline point, and the fixed `3-4` bandgap label (`gap34_Hz`, `gap34_gain_Hz`).
- Broad rollout has been tested and rejected through multiple physical validation rounds.
- The validated high-value exploitation point is currently:
  - `rf09_h09_b5_002_a4_0015`
- Two transfer modes have been established:
  - **directional exploitation** on already validated families
  - **seed-only discovery** on unseen families
- Across the later validation rounds, the most reliable new-family entry point is currently:
  - `stage1 weak_positive` seeds

In other words, this repository now reflects a **family-aware / step-aware targeted exploitation workflow**, not a global blind search workflow.

## Repository Layout

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

### Directory Roles

- `model_core/`: shared COMSOL-side functions such as materials, geometry setup, boundary selection, eigenfrequency extraction, and result packaging.
- `stage1/` to `stage2_harmonics_refine/`: physical screening logic before machine learning.
- `stage3_dataset/`: converts accumulated physical results into versioned training datasets.
- `stage3_training/`: trains MLP classifiers / regressors, builds candidate pools, runs cascade scoring, and produces validation manifests.
- `stage4_validation/`: centralizes `stage4_validation_ab_v*.m` configuration and CSV summary generation.
- `runners/`: the main operational entry points used from MATLAB.
- `data/`: all generated CSVs, manifests, COMSOL outputs, plots, and model checkpoints. This directory is intentionally git-ignored.

## Phase Structure

## 1. Physical Screening Before ML

### Stage 1: random snake shape screening

Main runner:
- `runners/run_stage1_shape_screening.m`

Purpose:
- test a large random snake library under the trusted baseline point
- identify geometry-valid, contact-valid, and positive-gain shapes
- produce the initial seed library for later transfer and ML

### Stage 2: low-order robustness and refinement

Main runners:
- `runners/run_stage2_fourier_robustness_screening.m`
- `runners/run_stage2_refine_screening.m`

Purpose:
- validate that strong positive results are not one-off lucky points
- narrow the low-order parameter region (`a2 < 0`, `a1 ~ 0.45-0.50`, `b2 ~ 0-0.04`, small `r0` adjustment)

### Stage 2 harmonics: higher-order exploitation signals

Main runners:
- `runners/run_stage2_harmonics_screening.m`
- `runners/run_stage2_harmonics_refine_screening.m`

Purpose:
- test higher-order terms on top of the trusted low-order region
- preserve the main finding that `a4 > 0` is the most useful retained harmonics direction on the main line

## 2. Dataset and Model Building

Dataset builders live in:
- `stage3_dataset/`

Training and scoring code live in:
- `stage3_training/`

Important tracked dataset/training versions:
- `build_v5_training_dataset.py`: directional context introduced
- `build_v6_training_dataset.py`: later validation data integrated
- `build_v7_training_dataset.py`: training dataset updated through `stage4_validation_ab_v8`, with `stage1` reference context added for seed-only discovery

Current model families:
- contact classifier
- positive-gain classifier
- surrogate regressor

The cascade logic always treats the classifiers as primary and the regressor as auxiliary.

## 3. Candidate Discovery and Validation

Candidate-pool builders and validation manifests are versioned.

Examples:
- `stage3_training/build_candidate_pool_v5.py`
- `stage3_training/build_candidate_pool_v8.py`
- `stage3_training/build_candidate_pool_v9.py`
- `stage3_training/build_candidate_pool_v10.py`

Validation runners:
- `runners/run_stage4_validation_ab_v5.m`
- `runners/run_stage4_validation_ab_v6.m`
- `runners/run_stage4_validation_ab_v7.m`
- `runners/run_stage4_validation_ab_v8.m`
- `runners/run_stage4_validation_ab_v9.m`
- `runners/run_stage4_validation_ab_v10.m`

These runners:
- read a staged validation manifest
- evaluate the requested shape-point cases in COMSOL
- write per-case results
- generate arm / point / shape summary tables automatically

## Versioned Experiment Map

### `v1`
- first successful cascade broad validation
- showed that the classifier front-end is necessary

### `v2` to `v4`
- tested parameter-aware models and broad-transfer assumptions
- physically showed that broad transfer is not reliable

### `v5` to `v6`
- moved to targeted exploitation around validated seeds / families
- established directional step exploitation on validated families

### `v7`
- tested optional new families with local transfer probes
- showed that new families support seed transfer but not direct neighborhood expansion

### `v8`
- first strong seed-only discovery round on unseen families

### `v9`
- seed-only model-assisted discovery with a more conservative ranking line
- showed the model had ranking value but should not be used as a hard gate on tail candidates

### `v10`
- refined shortlist strategy
- prioritized `weak_positive` / `strong_positive` seeds and reduced neutral seeds to small probe slots

## Current Recommended Workflow

If continuing the thesis from the current state, the recommended operational sequence is:

1. Update / rebuild the training dataset if new physical truth has been added.
2. Retrain the seed-discovery or directional models as needed.
3. Build and score the next candidate pool.
4. Generate a validation manifest.
5. Run COMSOL validation with the matching `stage4_validation_ab_v*.m` runner.
6. Analyze the resulting arm / point / shape summaries.

For the current repository state, the latest seed-only refined path is:

- candidate pool: `stage3_training/build_candidate_pool_v10.py`
- scoring: `stage3_training/run_seed_discovery_scoring_v7.py`
- manifest: `stage3_training/build_validation_manifest_v10.py`
- COMSOL validation: `runners/run_stage4_validation_ab_v10.m`

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
- continuing targeted validation rounds
- extending the dataset / training scripts
- writing the methods and workflow sections of the thesis from real code

It is not intended to be a polished end-user software package. It is a research codebase with preserved experiment history.
