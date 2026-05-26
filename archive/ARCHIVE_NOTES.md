# Archive Notes

The public refactor uses `archive/` for material that should remain
recoverable but should not distract from the final thesis mainline.

## Archive Categories

| Archive path | Intended contents |
| --- | --- |
| `archive/legacy_prediction/` | Historical prediction versions such as `prediction_v2` to `prediction_v7` |
| `archive/legacy_stage_pipelines/` | Historical `stage1`, `stage2`, and `stage3_*` workflows |
| `archive/legacy_runners/` | Old version-ladder wrappers and exploratory MATLAB/Python runners |
| `archive/baselines/` | Historical baseline notes and archived baseline scaffolds |
| `archive/oneoff_thesis_scripts/` | One-off PPT, thesis, or local debugging scripts |
| `archive/generated_reports/` | Generated reports or figure bundles if they are tracked later |

## Current Rule

P2 only creates archive targets and moves documentation. Source-code moves are
reserved for P3/P4 after imports and MATLAB paths are updated.

P3 update:

- `test_two_matlab.py` moved to `archive/oneoff_thesis_scripts/`.
- `tools/` moved to `archive/oneoff_thesis_scripts/tools/` because it contains
  defense/PPT builders rather than reusable public project tooling.
- Historical prediction routes moved to `archive/legacy_prediction/`:
  `prediction/`, `prediction_targetband_v1/`, and `prediction_v2/` through
  `prediction_v7/`. Root compatibility packages are kept for older imports.
- `baselines/` moved to `archive/baselines/`.
- Top-level legacy wrappers moved to `archive/legacy_runners/`:
  early `stage1`/`stage2` screening wrappers, stage3 training/scoring version
  ladders, old target-band plotting launchers, V11 freeze helper launchers, and
  exploratory pilot scripts.
- Unused stage3 route folders moved to `archive/legacy_stage_pipelines/`:
  `stage3_autoresearch/`, `stage3_optimization/`,
  `stage3_optimization_real_ga/`, and `stage3_prediction/`.

## Preserve

Do not delete or rewrite original local result roots:

- `data/`
- `output/`
- `research_validation/` final evidence roots

These directories can be indexed, but generated payload should not be blindly
committed to the public repository.
