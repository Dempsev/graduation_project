# Dual-Line Workflow Overview

This note summarizes the Phase-1 thesis-facing architecture after separating the
repository into a truth layer, a model layer, and a search layer.

The most important interpretation change is:

- the old stage-oriented workflow is preserved
- but it is no longer the preferred way to explain the repository

## 1. Historical Mainline

The historical mainline is still present and remains valuable as repository history.

It is the old mixed closed loop:

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

This path should now be read as:

- historical experiment history
- truth accumulation source
- baseline source for later comparison

It should no longer be treated as the only thesis-ready narrative.

## 2. Truth Layer

Directory:

- `physics_pipeline/`

Meaning:

- the official Phase-1 entry point for **physical truth production**

Implementation roots still remain in:

- `stage1/`
- `stage2/`
- `stage2_refine/`
- `stage2_harmonics/`
- `stage2_harmonics_refine/`
- `stage4_validation/`

Interpretation:

- these directories are one connected truth-production layer
- later prediction and optimization layers should be understood as consumers of this truth

## 3. Model Layer

Directory:

- `prediction/`

Meaning:

- the official Phase-1 entry point for **prediction / modeling**

This layer now contains two sub-stories:

### 3.1 Global Prediction Baseline

- shape + parameter -> global bandgap targets
- includes fixed-gap and max-gap style prediction
- remains the modeling baseline

### 3.2 Target-Band Conditional Prediction Mainline

- shape + parameter + target band -> open probability + overlap / cover prediction
- represented by:
  - `prediction_targetband_v1/`
  - `prediction_targetband_param_v1/`

This target-band route is the planned next mainline for design-oriented prediction.

## 4. Search Layer

Directory:

- `optimization/`

Meaning:

- the official Phase-1 entry point for **search / optimization**

This layer should now be read as three routes:

### 4.1 Seed Ranking Baseline

- directory:
  - `optimization/seed_ranking/`
- role:
  - low-cost candidate generation
  - model-assisted front-end filtering
  - comparison baseline

`seed` remains useful, but only as a low-cost baseline and front-end.

### 4.2 True Global Real-GA Baseline

- directory:
  - `optimization/real_comsol_ga/`
- role:
  - direct COMSOL-in-the-loop real search
  - current strongest real-optimization baseline in the repository

### 4.3 Target-Band-Conditioned Optimization Planned Mainline

- next intended route after the architecture cleanup
- uses target-band conditional prediction to drive design-oriented search
- promoted in architecture now, implemented further in the next phase

## 5. What `stage3_training/` Means Now

`stage3_training/` should now be interpreted as:

- a legacy mixed mainline
- a baseline source
- a repository-history anchor

It remains valuable because it still contains:

- historical candidate ranking logic
- training utilities used by later lines
- comparison routes that are still useful in the thesis

But it is no longer the recommended top-level reading entry.

## 6. Recommended Reading Order

If you want the thesis-facing structure, read in this order:

1. `physics_pipeline/`
2. `prediction/`
3. `optimization/`
4. `baselines/`

If you want historical experiment context afterward, read:

- `stage3_training/`

## 7. Default Next-Step Order

Phase 1 fixes the architecture language first.

The default next-step order is:

1. architecture cleanup first
2. target-band execution second

That means:

- Phase 1 does not merge stage directories
- Phase 1 does not remove seed code
- Phase 1 does not yet make target-band optimization the implemented default
- Phase 1 only makes the intended mainline explicit
