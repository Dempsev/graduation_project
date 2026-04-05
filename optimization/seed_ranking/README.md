# Seed-Ranking Optimization

This directory is the task-oriented implementation root for the surrogate-assisted optimization layer.

It contains the lighter-weight optimization path that still relies on the historical candidate-discovery stack:

- candidate-pool construction
- classifier / surrogate-based candidate scoring
- validation-manifest generation
- optional local GA refinement on shortlisted seeds

The older `stage3_optimization/` directory is retained as a compatibility layer during the staged refactor.

## Main Files

- `common.py`
- `build_optimization_candidate_pool_v1.py`
- `score_optimization_candidates_v1.py`
- `build_optimization_manifest_v1.py`
- `run_optimization_local_ga_v1.py`
- `build_optimization_ga_manifest_v1.py`
- `run_optimization_pipeline_v1.py`

## Role In The New Thesis Structure

This layer is no longer treated as the final optimization definition.

Instead, it now plays the role of:

1. low-cost candidate discovery
2. seed-level pre-screening
3. front-end support for later real COMSOL-in-loop optimization

