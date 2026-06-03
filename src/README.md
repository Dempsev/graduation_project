# Source Layout

This directory contains the public source layout. The final target-band
prediction and pure-Python seed-ranking paths live under `src/`, while
historical prediction lines live under `archive/legacy_prediction/`.

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

See `docs/project/PROJECT_STRUCTURE.md` for the current repository map.
