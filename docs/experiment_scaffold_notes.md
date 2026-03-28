# Experiment Scaffold Notes

## Entry

Run with:

```bash
python stage3_training/run_experiment_scaffold_v1.py --config configs/experiments/minimal_family_point_objective_compare.json
```

Outputs are written to:

- `data/ml_runs/experiment_scaffold_v1/<suite_name>/suite_summary.csv`
- `data/ml_runs/experiment_scaffold_v1/<suite_name>/suite_summary.json`
- `data/ml_runs/experiment_scaffold_v1/<suite_name>/combined_family_summary.csv`
- `data/ml_runs/experiment_scaffold_v1/<suite_name>/combined_point_summary.csv`
- `data/ml_runs/experiment_scaffold_v1/<suite_name>/combined_shape_summary.csv`

Each experiment also gets its own folder with:

- `filtered_input.csv`
- `scored_candidates.csv`
- `selected_candidates.csv`
- `family_summary.csv`
- `point_summary.csv`
- `shape_summary.csv`
- `experiment_summary.json`

## Minimal Config Schema

Each experiment entry currently supports:

- `experiment_name`
- `source_csv`
- `shape_family_list`
- `shape_id_list`
- `point_id_list`
- `objective_name`
- `scoring_setting`
- `validation_selection_rule`

## Supported Scoring Modes

### 1. `surrogate`

Use the current stage3 seed-discovery models.

Required practical fields inside `scoring_setting`:

- `contact_run_root`
- `positive_run_root`
- `reg_run_root`
- optional thresholds / weights / splits

Use this when the input is a candidate-pool csv and you want stage3-style model scoring.

### 2. `observed_objective`

Use an existing objective column from the input csv directly.

This works well on existing stage4 validation result tables because they already contain:

- `gap34_gain_Hz`
- `gap34_Hz`
- `gap34_rel`
- `max_gap_Hz`

Use this when you want a fast comparison across families / points / objectives without requiring a new surrogate checkpoint.

## Supported Validation Selection Rules

### 1. `top_k`

Simple rank-and-take selection.

Fields:

- `k`
- optional `max_per_shape`
- optional `max_per_family`

### 2. `primary_probe`

A lightweight version of the current validation-manifest logic.

Fields:

- `primary_k`
- `probe_k`
- `diversity_k`
- optional `max_per_shape`
- optional `max_per_family`

This rule is most meaningful when the source has stage1 tier context, such as current candidate-pool tables.

## Current Intended Scope

This scaffold is intentionally minimal.

Already covered:

- cross-family comparison
- cross-point comparison
- objective switching
- unified experiment summary output

Current TODOs:

- direct COMSOL manifest export for every rule variant
- profile-aware material sweep integration
- automatic stage4 summary back-merge after a new validation run finishes
