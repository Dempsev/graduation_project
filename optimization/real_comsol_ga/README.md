# COMSOL-In-Loop GA

This module implements a real COMSOL-in-the-loop genetic algorithm for the optimization side of the project.

It is now the task-oriented implementation root for the real-GA branch.

The older `stage3_optimization_real_ga/` directory is retained as a compatibility copy during the refactor.

## Why this exists

The earlier GA branches in `stage3_optimization/` optimize surrogate-model scores.

That is fast, but it can overfit model bias when the search drifts outside the historical training distribution.

This module replaces surrogate fitness with direct COMSOL truth:

- geometry-valid / contact-valid / solve-success checks come from real evaluation
- fitness is based on real `gap34_gain_Hz`
- failed samples receive explicit penalties

## Search Modes

Two GA baselines are now supported:

- `local`
  - default thesis mainline
  - start from shortlisted seed shapes and optimize only inside a conservative half-width window around each seed point
- `true global`
  - teacher-facing baseline
  - use one unified population over the stage1-screened shape pool plus the active continuous parameters
  - shape identity is treated as a discrete gene and mutates during evolution
  - continuous parameters evolve inside the configured global bounds
  - stop when either the max generation budget is exhausted or best-fitness improvement becomes too small for several generations

## Champion Funnel

To maximize the chance of beating the true global GA under the same real COMSOL
budget, there is now a more aggressive optimization mainline:

- `funnel probe`
  - high-recall seed probe
  - `20` basins, `6 x 3` budget each
- `expansion`
  - medium-scale basin expansion
  - top `4` basins, `10 x 5` budget each
- `duel`
  - head-to-head competition
  - top `2` basins, `12 x 7` budget each
- `champion`
  - all-in exploitation
  - top `1` basin, `16 x 17` budget

This keeps the total real evaluation budget at exactly `1000`, matching the
default true-global-GA budget while concentrating much more of the later budget
on the strongest basin.

## First-Version Scope

The first version intentionally keeps the workflow tractable:

- active parameters: `a1`, `b1`, `a2`, `b2`, `r0`, `a3`, `b3`, `a4`, `b4`, `a5`, `b5`
- global shape pool: the stage1-screened shape summary (`285` shapes in the current workspace)
- reference point: `rf09_h00_center`
- search mode: real COMSOL evaluation over shape + parameter genes
- resume support: state is checkpointed after every evaluated individual

## Main Files

- `get_comsol_in_loop_ga_config_v1.m`
- `get_comsol_in_loop_ga_global_config_v1.m`
- `get_comsol_in_loop_ga_optimization_funnel_probe_config_v1.m`
- `get_comsol_in_loop_ga_optimization_expansion_config_v1.m`
- `get_comsol_in_loop_ga_optimization_duel_config_v1.m`
- `get_comsol_in_loop_ga_optimization_champion_config_v1.m`
- `get_comsol_in_loop_ga_plan_a_bridge_config_v1.m`
- `run_comsol_in_loop_ga_v1.m`
- `run_comsol_in_loop_global_ga_v1.m`
- `runners/run_stage3_comsol_in_loop_ga_v1.m`
- `runners/run_stage3_comsol_in_loop_global_ga_v1.m`
- `runners/run_stage3_a_then_comsol_in_loop_ga_v1.m`
- `runners/run_stage3_optimization_champion_funnel_v1.m`

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

For a direct teacher-facing global baseline, run:

- `get_comsol_in_loop_ga_global_config_v1.m`
- `run_comsol_in_loop_global_ga_v1.m`
- `runners/run_stage3_comsol_in_loop_global_ga_v1.m`

That run uses a single unified population over the stage1-screened shape pool and the continuous parameter bounds, with plateau-based early stopping.
The current default global budget is intentionally larger than the local-GA budget because the search now includes both a discrete shape gene and `11` continuous genes.

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

## Recommended Winner-Take-Most Run

If the goal is to challenge the true global baseline instead of just providing
stable local refinement, run:

- `get_comsol_in_loop_ga_optimization_funnel_probe_config_v1.m`
- `get_comsol_in_loop_ga_optimization_expansion_config_v1.m`
- `get_comsol_in_loop_ga_optimization_duel_config_v1.m`
- `get_comsol_in_loop_ga_optimization_champion_config_v1.m`
- `runners/run_stage3_optimization_champion_funnel_v1.m`

This funnel keeps the optimization-oriented seed selector, keeps `b1` active in
all stages, and reallocates most of the late-stage truth budget onto the best
basin instead of spreading it across many survivors.

## Adaptive Funnel V2

The first champion funnel still made one aggressive assumption:

- once the top basin was ahead by even a small margin, the remaining budget was
  pushed entirely into that single basin

That is efficient, but it can prematurely eliminate a slower-rising basin whose
final ceiling is actually higher.

The adaptive `v2` funnel keeps the same general idea but makes the elimination
logic more robust:

- `expansion -> duel`
  - keep the top `2` basins
  - allow `1` wildcard basin to survive if it stays within a competitive band
- `duel -> champion`
  - if the top `2` duel basins are still near-tied, keep both instead of
    forcing a single winner immediately

Run:

- `optimization/real_comsol_ga/get_comsol_in_loop_ga_optimization_duel_config_v2.m`
- `optimization/real_comsol_ga/get_comsol_in_loop_ga_optimization_champion_config_v2.m`
- `runners/run_stage3_optimization_champion_funnel_v2.m`

The expected use is:

- reuse `funnel_probe_v1`
- reuse `expansion_v1`
- start new adaptive `duel_v2`
- continue to adaptive `champion_v2`

## Budget Competition Analysis

To compare methods by *sample efficiency* instead of only final best value, use:

- `optimization/real_comsol_ga/analyze_budget_competition_v1.py`

This prints:

- final best gain
- total evaluated samples
- solve-success count
- positive-gain count
- best-so-far checkpoints at matched real-evaluation budgets
