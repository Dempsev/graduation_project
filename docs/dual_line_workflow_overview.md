# Dual-Line Workflow Overview

This note summarizes how the repository is organized after splitting the project into a prediction line and an optimization line.

## 1. Legacy Mainline

The historical mainline is still present in the repository and should be understood as a mixed closed loop:

1. `stage1/`
   Screen random snake shapes under a trusted baseline point.
2. `stage2/`, `stage2_refine/`
   Low-order parameter screening and local refinement.
3. `stage2_harmonics/`, `stage2_harmonics_refine/`
   Higher-order harmonics probing and refinement.
4. `stage3_dataset/`
   Build unified ML datasets from accumulated physical truth.
5. `stage3_training/`
   Train classifiers / regressors, score candidate pools, build manifests, and run surrogate-based GA branches.
6. `stage4_validation/`
   Run COMSOL validation from generated manifests and feed new truth back into the loop.

This mainline is valuable as repository history and as the source of training data, but it mixes prediction, ranking, and optimization into one storyline.

## 2. New Prediction Line

Directory:

- `stage3_prediction/`

Purpose:

- define a clean forward prediction task
- input: shape geometry descriptors + Fourier parameters
- output: bandgap targets such as `gap34_width_Hz`
- evaluation: train / val / test and external `stage4_validation*` holdout

Current scripts:

- `build_pure_prediction_dataset_v1.py`
- `train_pure_bandgap_regressor_v1.py`
- `train_pure_bandgap_twostage_v1.py`

Runner entry points:

- `runners/run_stage3_build_pure_prediction_dataset_v1.m`
- `runners/run_stage3_train_pure_bandgap_regressor_v1.m`
- `runners/run_stage3_train_pure_bandgap_twostage_v1.m`

The recommended presentation-friendly prediction setup is now the two-stage width predictor:

1. classify whether the fixed `3-4` gap opens
2. regress the positive width
3. combine them into an expected-width prediction

## 3. New Optimization Line

Directories:

- `stage3_optimization/`
- `stage3_optimization_real_ga/`

These should be read as two layers of the optimization side.

### 3.1 Surrogate-Assisted Optimization Layer

Directory:

- `stage3_optimization/`

Purpose:

- isolate optimization tasks from the old mixed `stage3_training/` mainline
- build candidate pools
- score candidates
- build manifests
- run conservative local GA branches

This layer still uses model-assisted screening and is mainly useful for cheaper exploration and seed filtering.

### 3.2 Real COMSOL-In-Loop Optimization Layer

Directory:

- `stage3_optimization_real_ga/`

Purpose:

- run direct COMSOL-in-the-loop GA
- optimize real `gap34_gain_Hz`
- avoid surrogate-only fitness drift

Current scripts:

- `get_comsol_in_loop_ga_config_v1.m`
- `run_comsol_in_loop_ga_v1.m`

Runner:

- `runners/run_stage3_comsol_in_loop_ga_v1.m`

## 4. A + Real-GA Mainline

The recommended optimization mainline is no longer:

- rank everything with a surrogate
- then optionally do a tiny GA tail step

Instead it is:

1. use plan-A style conservative local optimization to probe multiple seed shapes
2. use real COMSOL validation to identify which seeds are genuinely strong
3. pass only those real-validated seeds into direct COMSOL-in-loop GA

Bridge scripts:

- `stage3_optimization_real_ga/select_plan_a_validated_seed_ids_v1.m`
- `stage3_optimization_real_ga/get_comsol_in_loop_ga_plan_a_bridge_config_v1.m`
- `runners/run_stage3_a_then_comsol_in_loop_ga_v1.m`

This means the final real-GA branch now depends on **real validated seed quality**, not on surrogate ranking alone.

## 5. Recommended Thesis Structure

### Prediction Line

- data source: accumulated truth from `stage1/2/4`
- task: shape + parameter -> bandgap
- output: prediction accuracy

### Optimization Line

- stage A: conservative local joint optimization for seed comparison
- stage B: real COMSOL-in-loop GA for final high-confidence refinement

## 6. Repository Reading Guide

If you only want the current thesis-ready structure, focus on:

- prediction:
  - `stage3_prediction/`
- optimization:
  - `stage3_optimization/`
  - `stage3_optimization_real_ga/`
- physical truth source:
  - `stage1/`
  - `stage2/`
  - `stage2_harmonics/`
  - `stage4_validation/`

If you want the historical experiment path, read:

- `stage3_training/`

That directory remains the historical mainline, but it should no longer be treated as the only narrative for the thesis.

## 7. Phase-1 Refactor Reading Order

The repository now has a task-oriented top layer that should be preferred when reading the thesis-ready structure:

1. `physics_pipeline/`
2. `prediction/`
3. `optimization/`
4. `baselines/`

The historical stage directories remain in place underneath that layer to preserve compatibility with existing scripts and experiment artifacts.
