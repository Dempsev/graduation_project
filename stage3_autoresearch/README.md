# Stage-3 Autoresearch Prototype

This folder contains a small, repo-local prototype inspired by Andrej Karpathy's `autoresearch`, but adapted to this project's actual constraints.

Instead of letting an LLM rewrite arbitrary research code, this prototype focuses on a safer inner loop:

1. sample a compact hyperparameter proposal
2. run an existing stage-3 training script unchanged
3. read the saved validation metrics
4. rank trials and keep the best configuration

The goal is to automate the fast ML side of the workflow without touching the COMSOL validation loop.

For `scoring`, the loop is slightly different:

1. sample thresholds and weights for seed-discovery scoring
2. run the existing scoring script on the current candidate pool
3. read the saved summary files
4. rank trials using a heuristic shortlist objective

## Supported Modes

- `classifier`: searches over `train_mlp_classifier_v7.py`
- `regressor`: searches over `train_mlp_regressor_v7.py`
- `scoring`: searches over `run_seed_discovery_scoring_v7.py`

## Why Validation Metrics

Trial ranking uses the validation split metric, not the test split metric:

- classifier objective: validation `f1`
- regressor objective: negative validation `rmse`

This keeps the prototype closer to a real research loop and avoids using test scores as the search target.

For `scoring`, there is no held-out physical truth inside the candidate pool itself, so the ranking objective is heuristic:

- primary: `top_k_gate_count`
- tie-breakers: `top_k_strong_positive_count`, `top_k_weak_positive_count`
- soft bonus: mean `stage1_reference_gap_gain_Hz` among top-ranked rows

This is useful for shortlist shaping, but it is not a substitute for Stage-4 COMSOL validation.

## Example Commands

Run a lightweight classifier search:

```powershell
python stage3_autoresearch\run_stage3_autoresearch.py --mode classifier --task contact_valid --trials 4 --epochs 80
```

Run a lightweight regressor search:

```powershell
python stage3_autoresearch\run_stage3_autoresearch.py --mode regressor --target gap34_gain_Hz --trials 4 --epochs 100
```

Run a lightweight seed-discovery scoring search on the current v10 candidate pool:

```powershell
python stage3_autoresearch\run_stage3_autoresearch.py --mode scoring --trials 6
```

Run scoring search directly on the current v11 candidate pool:

```powershell
python stage3_autoresearch\run_stage3_autoresearch.py --mode scoring --dataset data\ml_dataset\v11\candidate_pool_v11_seed_only_refined\candidate_pool_v11.csv --trials 8
```

Preview the proposed trials without running training:

```powershell
python stage3_autoresearch\run_stage3_autoresearch.py --mode classifier --dry-run
```

## Outputs

Each session writes under:

`data/ml_runs/stage3_autoresearch/<session_name>/`

Key files:

- `session_config.json`
- `planned_trials.json`
- `leaderboard.csv`
- `best_trial.json`
- `recommended_presets.json`

The full model artifacts for each trial are written to:

`data/ml_runs/stage3_autoresearch/<session_name>/trials/<trial_name>/`

## Recommended Presets

Current repo-local recommendations are summarized in:

`stage3_autoresearch/recommended_presets.json`

At the moment the most useful entries are:

- `classifier_contact_valid`
- `classifier_is_positive_shape`
- `regressor_gap34_gain_Hz`
- `seed_discovery_scoring_v10`
- `seed_discovery_scoring_v11`

The scoring preset should still be treated as a shortlist-shaping recommendation, not a physically validated conclusion.

You can also execute a recommended preset directly:

```powershell
python stage3_autoresearch\apply_recommended_preset.py --preset classifier_contact_valid
python stage3_autoresearch\apply_recommended_preset.py --preset seed_discovery_scoring_v11 --dry-run
```

## Current Scope

This is intentionally a conservative prototype. It does not:

- modify existing training code
- invoke COMSOL or MATLAB
- self-edit scripts with an LLM

That makes it a good fit for the fast inner loop in `stage3_training/`, while keeping the thesis-critical physical validation workflow unchanged.
