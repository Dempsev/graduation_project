# Prediction

This directory is the task-oriented entry layer for the clean forward-prediction line.

## Research Question

Given:

- shape geometry descriptors
- Fourier / structural parameters

predict:

- absolute bandgap targets such as `gap34_Hz`
- nonnegative width targets such as `gap34_width_Hz`
- whether the fixed `3-4` bandgap opens

The prediction line should not depend on:

- `gap34_gain_Hz`
- `is_positive_shape`
- reference-point gain labels
- shortlist / manifest / GA logic

## Current Implementation Root

The implementation currently lives in:

- `stage3_prediction/`

Phase 1 keeps that implementation intact and provides cleaner entry points from:

- `prediction/runners/`

## Preferred Scripts

- dataset build:
  - `prediction/runners/run_build_dataset_v1.py`
- single-stage regressor:
  - `prediction/runners/run_train_regressor_v1.py`
- two-stage predictor:
  - `prediction/runners/run_train_twostage_v1.py`

## Current Thesis-Oriented Recommendation

Use the two-stage width predictor as the main storyline:

1. classify whether the `3-4` bandgap opens
2. regress positive width
3. combine them into an expected-width prediction

Keep the single-stage regressor as a baseline.
