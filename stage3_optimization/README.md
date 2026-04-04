# Optimization Branch

This directory isolates the optimization-side workflow from the pure prediction branch.

## Scope

The optimization branch is responsible for:

- building candidate pools
- applying model-assisted scoring
- selecting shortlist / validation manifests
- optional local GA refinement on whitelisted seeds

This branch intentionally treats the models as optimization tools rather than as the thesis prediction task itself.

## Pipeline Stages

1. Candidate pool generation
2. Seed-discovery scoring
3. Validation manifest generation
4. Optional local GA refinement
5. Optional GA validation manifest generation

## Scripts

- `build_optimization_candidate_pool_v1.py`
- `score_optimization_candidates_v1.py`
- `build_optimization_manifest_v1.py`
- `run_optimization_local_ga_v1.py`
- `build_optimization_ga_manifest_v1.py`
- `run_optimization_pipeline_v1.py`

## Default Mainline

The default optimization path currently maps to the repository's refined seed-only mainline:

- candidate pool profile: `candidate_pool_v10_seed_only_refined`
- scoring script: `stage3_training/run_seed_discovery_scoring_v7.py`
- manifest builder: `stage3_training/build_validation_manifest_v10.py`

The optional GA path remains a post-ranking local refinement branch.

## Separation From Prediction

- Prediction branch: direct bandgap regression with geometry-only admissible inputs
- Optimization branch: uses contact / positive / surrogate model outputs to rank, filter, and refine candidates

This split is intended to match the advisor's requested thesis structure.
