# Original State Archive

This file records the repository state at the start of the final public
refactor.

## Snapshot Time

- Date: 2026-05-25
- Workspace: `D:\graduation_project\coad`
- Refactor branch: `codex/final-public-refactor`
- Baseline HEAD: `052db9ab3a4b6b092b75ba33e037387a844a1924`
- Baseline commit subject: `feat: add v11 targetband freeze workflow`
- Intended tag: `defense-final-snapshot-2026`

## Tag Status

The branch `codex/final-public-refactor` was created successfully from the
current mainline. The tag `defense-final-snapshot-2026` now points at the same
baseline commit:

```text
052db9ab3a4b6b092b75ba33e037387a844a1924
```

## Working Tree Supplement Inventory

At the start of the public refactor, the worktree contains additional thesis
and experiment-support material beyond the baseline commit. These files should
be treated as part of the final refactor pool and reviewed before moving,
archiving, or deleting anything.

Directory-level inventory from `git status --porcelain`:

| Path group | Changed / untracked entries |
| --- | ---: |
| `docs/` | 6 |
| `optimization/` | 12 |
| `postprocess/` | 14 |
| `prediction_targetband_param_v1/` | 11 |
| `research_validation/` | 1 |
| `runners/` | 18 |
| `stage4_validation/` | 6 |
| `test_two_matlab.py` | 1 |
| `tools/` | 1 |

## Known Modified Tracked Files

- `docs/THESIS_RUNBOOK.md`
- `optimization/real_comsol_ga/run_comsol_in_loop_band_catalog_ga_v1.m`
- `postprocess/plot_v11_freeze_cn.m`
- `prediction_targetband_param_v1/tools/analyze_predictor_readiness_v1.py`

## Public Refactor Intent

The final public version should turn the repository from a graduation-project
workbench into a readable research project. The public mainline should follow
the finished thesis narrative:

```text
COMSOL dispersion truth -> target-band conditional prediction
-> real COMSOL-in-loop GA -> Top5 / random / GA validation comparison
-> high-frequency weak-band boundary analysis
```

## Guardrails

- Preserve original experiment results and COMSOL outputs outside git history.
- Do not rerun large COMSOL jobs during refactor validation.
- Separate scripts that call COMSOL from postprocess-only scripts.
- Move historical routes to `archive/` only after their role is documented.
- Keep final claims bounded: prediction ranks and screens candidates; COMSOL
  dispersion validation remains the physical authority.

## Next Step

Proceed with P1: generate a full `REFACTOR_AUDIT.md` and a concrete movement
map before any large file relocation.
