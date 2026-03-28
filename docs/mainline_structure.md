# Mainline Structure Map

## Current Mainline

The repository mainline is now centered on these routes:

- stage2 harmonics refine baseline
- stage3 v10 / v11 seed discovery
- stage3 ga_v1 local parametric search
- stage4 validation for v10 / v11 / ga_v1
- post-hoc experiment and robustness analysis

## Mainline Python Layers

### Stable entrypoints

These are the user-facing scripts and runners that should stay stable:

- `stage3_training/build_candidate_pool_v10.py`
- `stage3_training/build_candidate_pool_v11.py`
- `stage3_training/run_seed_discovery_scoring_v7.py`
- `stage3_training/build_validation_manifest_v10.py`
- `stage3_training/build_validation_manifest_v11.py`
- `stage3_training/run_parametric_ga_seed_search_v1.py`
- `stage3_training/build_ga_validation_manifest_v1.py`
- `stage3_training/run_experiment_scaffold_v1.py`
- `stage3_training/run_robustness_analysis_v1.py`

### Shared policy/profile/helper layer

These now hold the real mainline variation points:

- `stage3_training/policies/`
- `stage3_training/profiles/`
- `stage3_training/seed_discovery_pipeline.py`
- `stage3_training/policy_resolution.py`
- `stage3_dataset/dataset_stage_registry.py`
- `stage3_dataset/dataset_profiles.py`

## Mainline MATLAB Layers

### Shared config/helper layer

- `stage2_harmonics_refine/get_physics_profile.m`
- `stage2_harmonics_refine/get_target_profile.m`
- `stage4_validation/build_stage4_validation_config.m`
- `stage4_validation/run_stage4_validation_from_manifest.m`

### Stable wrappers

- `stage4_validation/get_stage4_validation_config_v10.m`
- `stage4_validation/get_stage4_validation_config_v11.m`
- `stage4_validation/get_stage4_validation_config_ga_v1.m`
- `runners/run_stage4_validation_ab_v10.m`
- `runners/run_stage4_validation_ab_v11.m`
- `runners/run_stage4_validation_ab_ga_v1.m`

## Legacy Area

These still exist for reproducibility and history, but are not the preferred extension path:

- `stage3_training/build_candidate_pool_v1~v9.py`
- `stage3_training/build_validation_manifest_v1~v9.py`
- `stage4_validation/get_stage4_validation_config_v1~v9.m`
- older `run_stage4_validation_ab_v*.m`
- older cascade surrogate scripts

## Extension Rule

When adding a new mainline variation, prefer this order:

1. add or update a policy file
2. add or update a profile file
3. reuse an existing wrapper script
4. only add a new `vN` script if the workflow shape truly changes

That means:

- new thresholds or quotas -> policy
- new candidate family/point route -> profile
- new analysis slice -> experiment config
- new material/objective flavor -> profile/registry
- only genuinely new pipeline topology -> new script version
