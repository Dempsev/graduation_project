# Prediction

This directory is the task-oriented entry layer for the **model layer** of the project.

In Phase 1, prediction is no longer described as a single fixed-gap regression task.
It is the modeling layer that learns from accumulated physical truth and supports two
different thesis roles:

- a global bandgap prediction baseline
- a target-band conditional prediction mainline

## Model-Layer Research Question

Given:

- shape geometry descriptors
- Fourier / structural parameters
- optionally a target frequency window

predict:

- bandgap width or related global gap targets
- whether a desired target band opens
- how much of that target band is covered when it opens

The prediction layer should stay separate from:

- real COMSOL search loops
- manifest-building logic
- final optimization-budget allocation

## Current Implementation Roots

The clean task-oriented implementation still begins in:

- `prediction/dataset/`
- `prediction/models/`

Additional prediction lines that already extend the modeling story include:

- `prediction_v2/` to `prediction_v7/`
- `prediction_targetband_v1/`
- `prediction_targetband_param_v1/`

The old `stage3_prediction/` directory remains a compatibility layer and historical
anchor rather than the preferred reading entry.

## Prediction Storyline In Phase 1

### 1. Global Prediction Baseline

Use the existing pure-structure global bandgap line as the modeling baseline.

This includes:

- fixed-gap width prediction
- max-gap style prediction
- presentation-friendly two-stage prediction for the fixed `3-4` gap

### 2. Target-Band Conditional Prediction Mainline

The next thesis-facing modeling direction is:

- structure + target band -> open probability + overlap / cover prediction

This direction is already represented by:

- `prediction_targetband_v1/`
- `prediction_targetband_param_v1/`

In Phase 1, this target-band line is promoted to the **planned modeling mainline**
for design-oriented use cases, while the older fixed-gap line remains the baseline.

## Preferred Reading Order

If you want the current thesis-ready modeling story, read in this order:

1. `prediction/`
2. `prediction_v7/`
3. `prediction_targetband_v1/`
4. `prediction_targetband_param_v1/`

This reading order reflects the intended interpretation:

- global prediction first, as baseline
- conditional target-band prediction second, as the next mainline

## Preferred Scripts

### Global Prediction Baseline

- dataset build:
  - `prediction/runners/run_build_dataset_v1.py`
- single-stage regressor:
  - `prediction/runners/run_train_regressor_v1.py`
- two-stage predictor:
  - `prediction/runners/run_train_twostage_v1.py`

### Target-Band Conditional Prediction

- fixed-band dataset build:
  - `prediction_targetband_v1/runners/run_build_targetband_dataset_v1.py`
- conditional stacked dataset build:
  - `prediction_targetband_param_v1/runners/run_build_parametric_targetband_dataset_v1.py`
- conditional classifier:
  - `prediction_targetband_param_v1/runners/run_train_parametric_targetband_classifier_v1.py`
- conditional regressor:
  - `prediction_targetband_param_v1/runners/run_train_parametric_targetband_regressor_v1.py`

## Phase-1 Recommendation

For thesis structure and future implementation planning:

- treat the global bandgap predictor as the **baseline modeling line**
- treat the target-band conditional predictor as the **planned modeling mainline**

The default next-step order is:

1. architecture cleanup first
2. target-band execution second

So this round only changes the modeling narrative and reading order. It does not
change the already trained models or force a new implementation architecture yet.
