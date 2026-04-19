# Optimization

This directory is the task-oriented entry layer for the **search layer** of the project.

Phase 1 changes the optimization story in one important way:

- `seed` remains useful
- but only as a **low-cost candidate-generation and comparison baseline**
- not as the final optimization mainline

## Search-Layer Research Question

Given:

- real physical truth from `physics_pipeline/`
- model guidance from `prediction/`
- a continuous structural parameter space

find:

- strong candidates worth real validation
- better-performing parameter settings under real physical objectives
- eventually, target-band-conditioned search routes for design-oriented tasks

## Current Implementation Roots

The task-oriented implementation currently lives in:

- `optimization/seed_ranking/`
- `optimization/real_comsol_ga/`

Historical compatibility directories remain available:

- `stage3_optimization/`
- `stage3_optimization_real_ga/`

## Search-Layer Structure In Phase 1

### 1. Seed Ranking Baseline

Directory:

- `optimization/seed_ranking/`

Role:

- low-cost front-end candidate generation
- model-assisted ranking
- conservative local comparison
- baseline route for comparison and ablation

This layer is still useful, but it should now be read as a **baseline / front-end**
instead of the final optimization definition.

### 2. True Global Real-GA Baseline

Directory:

- `optimization/real_comsol_ga/`

Role:

- direct COMSOL-in-the-loop global search
- real objective optimization without surrogate-only drift
- current strongest real-optimization baseline in the repository

Preferred entry point:

- `optimization/runners/run_global_real_ga_v1.m`

In Phase 1, this route should be treated as the current **real optimization strong baseline**.

### 3. Target-Band-Conditioned Optimization Planned Mainline

This route is the planned next-step optimization direction after the Phase-1 cleanup.

Its intended role is:

- use target-band conditional prediction as the front-end objective layer
- optimize for desired band opening / overlap / coverage
- become the next thesis-facing optimization mainline

In this round, it is promoted in the architecture and documentation, but not yet
rolled out as the default implemented mainline.

An initial executable prototype now exists for the local-refinement part:

- `optimization/seed_ranking/run_targetband_seed_scoring_v1.py`
- `optimization/seed_ranking/run_targetband_local_ga_v1.py`
- `optimization/seed_ranking/build_targetband_ga_validation_manifest_v1.py`

This should still be read as an **early target-band route**:

- useful for proving the conditional-optimization idea
- not yet the final real-validation mainline
- still downstream of the stronger `true global real GA` baseline

## What Seed Means After Phase 1

`seed` is still kept in the repository because it remains valuable as:

- a low-cost candidate-generation front-end
- a historical comparison route
- a baseline for measuring whether later target-band or global-search methods are better

It should **not** be treated as:

- the final optimization thesis mainline
- the expected winner over true global GA

## Preferred Entry Points

### Baseline / Low-Cost Search

- `optimization/runners/run_surrogate_pipeline_v1.py`

### Real Search Baselines

- `optimization/runners/run_real_ga_v1.m`
- `optimization/runners/run_global_real_ga_v1.m`
- `optimization/runners/run_a_then_real_ga_v1.m`
- `optimization/runners/run_band_catalog_real_ga_v1.m`

### Optimization-Oriented Comparison Runs

- `optimization/runners/run_optimization_probe_then_refine_v1.m`
- `optimization/runners/run_optimization_champion_funnel_v1.m`
- `optimization/runners/run_optimization_champion_funnel_v2.m`
- `optimization/runners/run_optimization_champion_funnel_v3.m`
- `optimization/runners/run_optimization_champion_funnel_v4.m`

## Phase-1 Recommendation

The optimization layer should now be read as three distinct routes:

1. `seed_ranking` as the low-cost baseline
2. `true global real GA` as the current real-search strong baseline
3. `target-band-conditioned optimization` as the next planned mainline

That means the old mixed stage3 scoring logic and seed-driven local refinement
should no longer be described as the final thesis mainline.

## Follow-Up Order

The default next-step order is fixed as:

1. architecture cleanup first
2. target-band execution second

So Phase 1 only changes the optimization narrative and recommended reading order.
It does not rename runners, delete seed code, or rewrite the existing real GA logic.
