# Public Scripts

This directory contains the public command surface for the refactored project.

Naming convention:

- `build_*`: create datasets, manifests, reports, or indexes.
- `train_*`: train or evaluate prediction models.
- `make_*`: postprocess-only figure/table generation.
- `run_comsol_*`: may start COMSOL.
- `run_real_ga_*`: may start COMSOL-in-loop GA.
- `check_*`: lightweight validation that should not start COMSOL.

Safe first check:

```powershell
python scripts\check_project\check_public_layout.py
```

P3 adds wrapper entrypoints for the final thesis evidence scripts and for the
moved target-band prediction package. The wrappers make the public workflow
easy to find while keeping generated figures, CSVs, and model artifacts in
their established output roots.
