# Source Layout

This directory is the target source layout for the final public refactor.

P3 started by creating the public module map and safe entrypoints. The final
target-band prediction and pure-Python seed-ranking paths have now moved under
`src/`, while historical prediction lines live under `archive/legacy_prediction/`.

Target modules:

| Module | Purpose | Current source before full move |
| --- | --- | --- |
| `geometry/` | Snake/Fourier geometry generation and validity checks | `snake/`, `preprocess/` |
| `comsol_pipeline/` | COMSOL model construction and dispersion truth production | `model_core/`, `physics_pipeline/` |
| `dataset/` | Reserved for shared dataset code | target-band builders currently live in `src/prediction/targetband_param/dataset/` |
| `prediction/` | Conditional target-band classifier/regressor/inference | `src/prediction/targetband_param/` |
| `optimization/` | Candidate ranking and real COMSOL-in-loop GA | `src/optimization/seed_ranking/`, `optimization/real_comsol_ga/` |
| `validation/` | Stage4/holdout validation contracts and configs | `stage4_validation/`, `src/shared/` |
| `plotting/` | Plotting and figure-export helpers | `postprocess/`, `research_validation/` |
| `shared/` | Shared contracts, IO, features, objectives | `src/shared/` |

See `FINAL_REFACTOR_PLAN.md` for the full movement map.
