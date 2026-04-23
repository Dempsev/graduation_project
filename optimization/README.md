# Optimization

This directory is the task-oriented entry layer for the **search layer** of the project.

## Official Thesis Mainline

The official thesis-facing search line is the **frozen target-band prediction-guided
inverse-design workflow** inside the thesis band catalog.

Its intended flow is:

1. score candidates under a target-band condition
2. run conservative local refinement around shortlisted seeds
3. build a real-validation manifest
4. send shortlisted cases to stage4 / COMSOL validation

The mainline should now be described as:

- prediction-guided target-band shortlist generation
- conservative local refinement
- real validation under COMSOL

not as seed-first gap34 optimization.

## Stable Entrypoints

The preferred thesis-facing search entrypoints are:

- `optimization/runners/run_targetband_seed_scoring_v1.py`
- `optimization/runners/run_targetband_local_ga_v1.py`
- `optimization/runners/run_targetband_validation_manifest_v1.py`
- `optimization/runners/run_canonical_targetband_refinement_v1.py`
- `runners/run_stage4_validation_targetband_v1.m`

## Baselines And Historical Bridge Lines

These routes remain useful, but they are baseline or bridge logic:

- `optimization/runners/run_surrogate_pipeline_v1.py`
- `optimization/runners/run_real_ga_v1.m`
- `optimization/runners/run_global_real_ga_v1.m`
- `optimization/runners/run_a_then_real_ga_v1.m`
- `optimization/runners/run_band_catalog_real_ga_v1.m`
- `stage3_training/build_candidate_pool_v10.py`
- `stage3_training/build_candidate_pool_v11.py`
- `stage3_training/build_ga_validation_manifest_v1.py`

Interpret them as:

- low-cost baselines
- historical gap34 comparison lines
- bridge routes for reproducibility

## Config Semantics

Use the following boundary when changing optimization behavior:

- `profile`:
  - frozen candidate-construction choices, shape-pool choices, and thesis mainline assumptions
- `policy`:
  - ranking rules, quotas, GA limits, whitelist rules, and validation allocation
- `run config`:
  - paths, output roots, resume behavior, and per-run execution arguments

The stage4 validation handoff is now protected by:

- `shared/contracts/stage4_validation_manifest_contract_v1.json`
- `stage4_validation/build_stage4_validation_config.m`
- `stage4_validation/run_stage4_validation_from_manifest.m`

## Practical Positioning

The optimization layer should now be read as three roles:

1. target-band prediction-guided search as the thesis mainline
2. band-catalog / real-GA routes as strong baselines
3. older seed / gap34 routes as baseline or bridge logic
