# Legacy Runners

This directory holds top-level runner wrappers that are useful for history but
are no longer the public command surface.

Current groups:

- `stage1_stage2/`: early MATLAB screening wrappers.
- `stage3_training/`: version-ladder stage3 dataset, training, scoring, and
  manifest wrappers.
- `plotting/`: older target-band plotting wrappers replaced by
  `scripts/make_figures/` public wrappers.
- `pilot_scripts/`: exploratory local pilot launchers.
- `shared_matlab_v11/`: V11 freeze helper launchers kept for traceability.

Use `scripts/` for public commands and `docs/project/COMSOL_SCRIPT_INDEX.md`
before running anything that can start COMSOL.
