# COAD: Target-Band Phononic Crystal Design

COAD is a graduation-project research codebase for target-band design of
two-dimensional phononic crystal unit cells.

The final thesis workflow is:

```text
COMSOL dispersion truth
-> target-band conditional prediction
-> real COMSOL-in-loop genetic optimization
-> predictor Top5 / random / GA validation comparison
-> high-frequency weak-band boundary analysis
```

The project is not a packaged end-user library. It is a reproducible research
workspace that preserves the code, configs, and evidence chain behind the
thesis.

## Final Research Story

The thesis does not claim that machine learning replaces finite-element
calculation. The boundary is stricter:

- COMSOL dispersion calculation is the physical authority.
- The prediction model screens and ranks candidates for a specified target
  band.
- Real COMSOL-in-loop GA provides the optimization baseline.
- Final claims use COMSOL-validated overlap width and coverage ratio.
- Weak performance at 220-260 Hz and 240-280 Hz is treated as a limitation of
  the current structure family and parameterized design space.

The six final target bands are:

```text
140-180 Hz
160-200 Hz
180-220 Hz
200-240 Hz
220-260 Hz
240-280 Hz
```

## Public Refactor Status

This branch has completed the main public-refactor pass through P5. The current
layout is ready for final staging review: public docs, source wrappers,
archive notes, reproducibility indexes, and chapter-evidence tracking policy
are all in place.

Important starting points:

- [Project Structure](docs/project/PROJECT_STRUCTURE.md)
- [COMSOL Script Index](docs/project/COMSOL_SCRIPT_INDEX.md)
- [Runner Risk Index](docs/project/RUNNER_RISK_INDEX.md)
- [GitHub Publish Checklist](docs/project/GITHUB_PUBLISH_CHECKLIST.md)
- [Final Runbook](docs/reproducibility/FINAL_RUNBOOK.md)
- [Final Results Index](docs/reproducibility/FINAL_RESULTS_INDEX.md)
- [Dataset Manifest](docs/reproducibility/DATASET_MANIFEST.md)
- [Thesis Result Map](docs/thesis/THESIS_RESULT_MAP.md)
- [Refactor Audit](REFACTOR_AUDIT.md)
- [Refactor Plan](FINAL_REFACTOR_PLAN.md)
- [P4 Refactor Report](P4_REFACTOR_REPORT.md)
- [P5 Publish Readiness Report](P5_PUBLISH_READINESS_REPORT.md)

Public wrappers now live under `scripts/`, including dataset building, model
training, result export, and figure/report generation.

## Current Code Areas

| Area | Current path | Role |
| --- | --- | --- |
| Geometry | `snake/`, `preprocess/` | Snake-inspired and parameterized geometry construction |
| COMSOL pipeline | `model_core/`, `physics_pipeline/` | COMSOL model construction and truth-layer workflow |
| Dataset | `src/prediction/targetband_param/dataset/` | Target-band dataset construction |
| Prediction | `src/prediction/targetband_param/` | Conditional classifier/regressor and inference tools |
| Optimization | `optimization/real_comsol_ga/` | Real COMSOL-in-loop GA |
| Candidate ranking | `src/optimization/seed_ranking/` | Candidate pools, Top-k selection, validation manifests |
| Validation | `stage4_validation/`, `src/shared/` | Shared validation configs and contracts |
| Figures and reports | `postprocess/`, `research_validation/` | Thesis figures, tables, and chapter-specific evidence |

The target public module layout is staged under `src/`. The old
`prediction_targetband_param_v1/`, `prediction_v*`, `shared/`, and
`optimization/seed_ranking/` roots are kept as lightweight compatibility shims
or archived historical routes.

Historical prediction routes such as `prediction_v2` to `prediction_v7`, older
stage pipelines, and many old `runners/` wrappers have moved into `archive/`.

## Data And Artifact Policy

The repository tracks workflow definitions, scripts, configs, and lightweight
reports. It does not track full generated results.

Ignored local roots:

- `data/`: COMSOL outputs, datasets, model runs, validation manifests.
- `output/`: thesis PDFs, exported figures, defense assets.
- `tmp/`, `tmp_ppt_rebuild/`, `tmp_ppt_render/`: temporary build products.
- generated `research_validation/` tables, figures, JSON checklists, and text
  exports.

Use the reproducibility docs to locate data roots instead of committing large
artifacts.

## Environment

Typical local environment:

- Windows / PowerShell
- Python 3.12 or compatible Python 3
- MATLAB
- COMSOL with MATLAB LiveLink
- Python packages used across scripts: `numpy`, `pandas`, `matplotlib`,
  `scikit-learn`, `joblib`

Copy `configs/local.example.json` to a local, ignored config file before
running machine-specific MATLAB/COMSOL wrappers.

## Safe First Checks

These commands do not start large COMSOL jobs:

```powershell
python scripts\check_project\check_public_layout.py
python -m unittest tests.test_thesis_mainline_smoke
```

The smoke test allows generated data under ignored `data/` roots to be absent
where practical, while still checking public paths, contracts, and lightweight
wrapper behavior.

Before running any script that may start COMSOL, read:

- [COMSOL Script Index](docs/project/COMSOL_SCRIPT_INDEX.md)

## License

No public license has been selected yet. Until a `LICENSE` file is added by the
project author, the code and thesis materials should be treated as all rights
reserved.

## Defense Snapshot

The pre-public-refactor baseline is preserved as:

- branch: `codex/final-public-refactor`
- tag: `defense-final-snapshot-2026`
- state record: [Original State Archive](ARCHIVE_ORIGINAL_STATE.md)
