# Optimization

This directory is the task-oriented entry layer for the optimization side of the project.

## Research Question

Given:

- already discovered or validated seed shapes
- a continuous parameter space

find:

- which seed shapes are worth deeper investment
- which parameter combinations give better real physical bandgap gain

## Current Implementation Roots

The task-oriented implementation now lives in:

- `optimization/seed_ranking/`
- `optimization/real_comsol_ga/`

The historical directories are still retained for compatibility:

- surrogate-assisted layer:
  - `stage3_optimization/`
- real COMSOL-in-loop layer:
  - `stage3_optimization_real_ga/`

## Optimization Structure

### Layer 1: seed-level low-cost filtering

This layer can still use historical model-assisted scoring or conservative local search to compare seeds more cheaply.

Preferred entry points:

- surrogate-assisted optimization pipeline:
  - `optimization/runners/run_surrogate_pipeline_v1.py`

### Layer 2: final real optimization

This layer should use real COMSOL fitness rather than surrogate-only fitness.

Preferred entry points:

- direct real GA:
  - `optimization/runners/run_real_ga_v1.m`
- A-then-real-GA bridge:
  - `optimization/runners/run_a_then_real_ga_v1.m`

## Current Thesis-Oriented Recommendation

The preferred optimization mainline is:

1. use plan-A style conservative local search to compare seed shapes
2. keep only seeds with real COMSOL upside
3. run direct COMSOL-in-loop GA on those real-validated seeds

The old mixed stage3 scoring system should now be read as a **front-end candidate discovery baseline**, not as the final optimization definition.
