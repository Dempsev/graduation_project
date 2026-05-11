# COAD: Physics-Data Co-Optimization for Mechanical Metastructure Design

## Overview

This repository contains the full working codebase for a graduation-project
workflow on **bandgap-oriented design of mechanical / phononic metastructures**.

It is a research workflow rather than a polished end-user package. The core
pipeline is:

1. physical truth production with COMSOL + MATLAB
2. truth accumulation from screening, refinement, and validation rounds
3. prediction / modeling on accumulated truth
4. search / optimization with model guidance and real validation

The repository is read through a thesis-facing three-layer architecture:

1. `physics_pipeline/` as the **truth layer**
2. `prediction/` as the **model layer**
3. `optimization/` as the **search layer**

## Official Thesis Mainline

The repository now treats the **frozen target-band stack** as the single
thesis-facing mainline.

The current thesis-facing branch is `codex/research-architecture-refactor`.
The older `main` branch should be treated as the historical default branch
until this line is merged into `main` or selected as the GitHub default branch.

That mainline is:

- truth production through the historical physics pipeline
- conditional target-band prediction inside the thesis band catalog
- prediction-guided target-band search / refinement
- real COMSOL validation of shortlisted designs
- consolidation into analysis outputs and thesis-facing bundles

The authoritative freeze references are:

- `docs/THESIS_MAINLINE.md`
- `docs/architecture/targetband_mainline_freeze_v1.md`
- `prediction_targetband_param_v1/configs/targetband_mainline_freeze_v1.json`
- `prediction_targetband_param_v1/configs/thesis_band_catalog_v2.json`

## Baselines And Historical Bridge Lines

The repository also preserves older and comparison-oriented routes.

These are still valuable, but they are **not** the default thesis mainline:

- global / fixed-gap prediction lines
- `v10/v11` seed-discovery validation routes
- `ga_v1` gap34 local parametric search
- true global real-GA gap34 optimization
- historical mixed `stage3_training/` entrypoints

Use them as:

- baselines
- historical bridge logic
- reproducibility anchors
- comparison routes against the frozen target-band thesis mainline

## Repository Layout

### Thesis-Facing Layout

```text
coad/
  physics_pipeline/         Truth-layer reading entry
  prediction/               Model-layer reading entry
  optimization/             Search-layer reading entry
  baselines/                Historical or comparison workflows
  shared/                   Shared helpers and contracts

  stage1/                   Historical truth production
  stage2/                   Historical truth production
  stage2_refine/            Historical truth production
  stage2_harmonics/         Historical truth production
  stage2_harmonics_refine/  Historical truth production
  stage3_dataset/           Historical dataset builders
  stage3_training/          Historical bridge / baseline builders
  stage4_validation/        Historical truth-layer validation
  runners/                  MATLAB wrappers and legacy batch entrypoints
```

### Current Directory Interpretation

- `physics_pipeline/`
  - official entry for physical truth production
- `prediction/`
  - official entry for thesis-facing prediction narrative
- `optimization/`
  - official entry for thesis-facing search narrative
- `stage3_training/`
  - preserved baseline / bridge layer, not the default thesis storyline

## Recommended Reading Order

If you want the thesis-facing structure, read in this order:

1. `docs/THESIS_MAINLINE.md`
2. `docs/THESIS_RUNBOOK.md`
3. `docs/THESIS_METHOD_MAP.md`
4. `physics_pipeline/`
5. `prediction/`
6. `optimization/`
7. `docs/mainline_structure.md`

If you need historical baseline context afterward, then read:

- `stage3_training/`

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

## Commit And Data Policy

This repository tracks **source code and documentation**, not generated research outputs.

- All generated tables, manifests, model checkpoints, COMSOL outputs, plots, and logs live under `data/`.
- `data/` is git-ignored on purpose.
- Commit workflow definitions, configuration, source code, and thesis-facing documentation.
- Do not commit generated artifacts from `data/`, `output/`, `tmp/`, or `.worktrees/`.

## What This Repository Is Good For

This codebase is appropriate for:

- reproducing the workflow logic used in the thesis
- understanding the truth / model / search separation
- following the frozen target-band thesis mainline end to end
- using historical stage and seed routes as baselines or bridge comparisons
- writing methods and workflow sections of the thesis from real code
