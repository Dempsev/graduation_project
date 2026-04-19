# Phase-1 Logic Refactor Decision

This document is the **single decision source** for the Phase-1 logic refactor.

It does not replace the historical implementation. It defines how the repository
should be interpreted, documented, and extended from this point onward.

## 1. Goal

Phase 1 converts the repository from a stage-only reading style into a thesis-facing
three-layer architecture:

1. `physics_pipeline/` as the **truth layer**
2. `prediction/` as the **model layer**
3. `optimization/` as the **search layer**

The historical stage directories remain in place.

## 2. Core Decision

The repository is now read through this logic:

- old `stage*` routes are primarily about accumulating real physical truth
- prediction learns from that truth
- optimization searches using that truth directly or through prediction support

This replaces the older habit of treating the mixed `stage3_training` path as the
default repository narrative.

## 3. Directory Interpretation

### Truth Layer

Official entry:

- `physics_pipeline/`

Implementation roots kept in place:

- `stage1/`
- `stage2/`
- `stage2_refine/`
- `stage2_harmonics/`
- `stage2_harmonics_refine/`
- `stage4_validation/`

Meaning:

- these directories jointly define **physical truth production**

### Model Layer

Official entry:

- `prediction/`

Meaning:

- this is the thesis-facing entry for prediction and modeling

Internal interpretation:

- global prediction remains the baseline modeling line
- target-band conditional prediction is the planned modeling mainline

### Search Layer

Official entry:

- `optimization/`

Meaning:

- this is the thesis-facing entry for search and optimization

Internal interpretation:

- `optimization/seed_ranking/` is a low-cost baseline
- `optimization/real_comsol_ga/` contains the current real-search strong baseline
- target-band-conditioned optimization is the next planned search mainline

### Historical / Baseline Layer

Baseline entry:

- `baselines/`

Historical mixed implementation source:

- `stage3_training/`

Meaning:

- preserve experiment history
- preserve baseline logic
- preserve comparison routes

## 4. Seed Decision

The repository-wide conclusion on `seed` is now fixed for Phase 1:

- `seed` is still useful
- but only as a **low-cost candidate-generation and comparison baseline**
- not as the final optimization mainline

This means:

- seed ranking stays in the repository
- seed-driven local refinement stays available for baseline comparison
- seed-first logic should no longer be described as the thesis final search route

## 5. Mainline vs Baseline Decisions

### Current Baselines

- global prediction lines
- seed ranking / low-cost local comparison
- true global real GA as the current real-search strong baseline
- historical mixed `stage3_training` logic

### Planned Mainlines

- target-band conditional prediction
- target-band-conditioned optimization

This distinction must remain explicit in all top-level documentation.

## 6. What Phase 1 Does Not Do

Phase 1 is intentionally limited.

It does **not**:

- move directories
- merge stage implementations
- rename historical runners
- rewrite COMSOL solver logic
- extract policy/profile/shared-helper abstractions
- continue target-band feature implementation in this round

It only:

- changes repository interpretation
- changes top-level documentation
- fixes reading order and architectural language
- reserves the mainline position for target-band work in the next step

## 7. Default Follow-Up Order

After Phase 1, the default order is fixed:

1. architecture cleanup first
2. target-band execution second
3. shared helper / policy / profile extraction only if later needed

This ordering is part of the Phase-1 decision and should not be re-opened casually.

## 8. Relationship To Earlier Refactor Notes

Earlier Phase-1 blueprint documents remain useful as historical planning notes.

This document is narrower and stronger:

- it is the current decision source
- it locks the architecture language
- it clarifies the mainline / baseline split

If another document disagrees with this one during Phase 1, follow this file.
