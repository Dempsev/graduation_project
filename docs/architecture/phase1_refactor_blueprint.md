# Phase-1 Refactor Blueprint

## Goal

Convert the repository from a purely stage-oriented historical layout into a thesis-friendly task-oriented layout without breaking already validated workflows.

Phase 1 is intentionally conservative.

It does **not**:

- rewrite the COMSOL logic
- replace the legacy stage3 implementation
- move every historical directory

It **does**:

- create a task-oriented top-level architecture
- provide new runner entry points
- document which historical directories now play which role

## New Top-Level Roles

### `physics_pipeline/`

Role:

- reading guide for real physical data production
- points to the existing stage1 / stage2 / stage4 directories

### `prediction/`

Role:

- clean forward-prediction storyline
- wraps the existing `stage3_prediction/` implementation

### `optimization/`

Role:

- optimization storyline
- wraps surrogate-assisted optimization and real COMSOL-in-loop GA

### `baselines/`

Role:

- legacy mixed mainline and comparison workflows

### `shared/`

Role:

- reserved home for second-stage extraction of duplicated utilities

## Mapping Table

| New refactor role | Current implementation root |
| --- | --- |
| `physics_pipeline/` | `stage1/`, `stage2/`, `stage2_refine/`, `stage2_harmonics/`, `stage2_harmonics_refine/`, `stage4_validation/` |
| `prediction/` | `stage3_prediction/` |
| `optimization/` | `stage3_optimization/`, `stage3_optimization_real_ga/` |
| `baselines/legacy_stage3_training/` | `stage3_training/` |
| `shared/` | future extraction target |

## New Entry Points Added In Phase 1

### Prediction

- `prediction/runners/run_build_dataset_v1.py`
- `prediction/runners/run_train_regressor_v1.py`
- `prediction/runners/run_train_twostage_v1.py`

### Optimization

- `optimization/runners/run_surrogate_pipeline_v1.py`
- `optimization/runners/run_real_ga_v1.m`
- `optimization/runners/run_a_then_real_ga_v1.m`

## Why The Legacy Mainline Is Preserved

The historical mixed stage3 mainline is still useful because it serves as:

- a repository-history anchor
- a baseline for comparison
- a source of trained models and historical rankings

That makes it a baseline, not the final thesis-ready architecture.

## Planned Phase-2 Work

Once the task-oriented reading order is stable, phase 2 can:

1. extract shared objective / feature / split helpers
2. move new-mainline code into task-oriented implementation directories
3. leave thin wrappers behind in old locations for backward compatibility
