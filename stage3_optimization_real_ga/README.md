# COMSOL-In-Loop GA

This module implements a real COMSOL-in-the-loop genetic algorithm for the optimization side of the project.

## Why this exists

The earlier GA branches in `stage3_optimization/` optimize surrogate-model scores.

That is fast, but it can overfit model bias when the search drifts outside the historical training distribution.

This module replaces surrogate fitness with direct COMSOL truth:

- geometry-valid / contact-valid / solve-success checks come from real evaluation
- fitness is based on real `gap34_gain_Hz`
- failed samples receive explicit penalties

## First-Version Scope

The first version intentionally keeps the search conservative and tractable:

- active parameters: `a1`, `a2`, `b2`, `a4`, `b5`, `r0`
- starting seeds: top scored seed-discovery shapes at `rf09_h00_center`
- search mode: per-seed local GA with direct COMSOL evaluation
- resume support: state is checkpointed after every evaluated individual

## Main Files

- `get_comsol_in_loop_ga_config_v1.m`
- `get_comsol_in_loop_ga_plan_a_bridge_config_v1.m`
- `run_comsol_in_loop_ga_v1.m`
- `runners/run_stage3_comsol_in_loop_ga_v1.m`
- `runners/run_stage3_a_then_comsol_in_loop_ga_v1.m`

## Outputs

The run writes to:

- `data/comsol_batch/comsol_in_loop_ga_v1/`

Key outputs:

- `ga_state_v1.mat`
- `ga_history_v1.csv`
- `ga_generation_summary_v1.csv`
- `ga_search_summary_v1.csv`
- `ga_best_candidates_v1.csv`

## Recommended First Run

Start with the default budget in `get_comsol_in_loop_ga_config_v1.m`:

- top seeds: `3`
- population size: `12`
- generations: `6`
- elites: `2`

This keeps the first real-GA experiment small enough to validate the workflow before scaling to lab machines.

## A + Real-GA Mainline

The recommended optimization mainline is now:

1. use plan-A real validation to identify strong seed shapes
2. pass those real-validated seeds into direct COMSOL-in-the-loop GA
3. perform final high-confidence parameter optimization only on that filtered seed set

The bridge entry point is:

- `get_comsol_in_loop_ga_plan_a_bridge_config_v1.m`
- `runners/run_stage3_a_then_comsol_in_loop_ga_v1.m`

By default this bridge reads the expanded plan-A validation summary and keeps only seeds that:

- have full positive-rate physical validation
- have enough successful validation rows
- exceed a minimum real mean gain threshold

This makes the real-GA branch depend on **real plan-A truth**, not on surrogate ranking alone.
