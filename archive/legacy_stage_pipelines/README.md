# Legacy Stage Pipelines

This folder holds historical stage directories that are no longer the public
mainline.

Archived in P4:

- `stage3_autoresearch/`
- `stage3_optimization/`
- `stage3_optimization_real_ga/`
- `stage3_prediction/`

Still intentionally kept at the repository root:

- `stage3_training/`: shared legacy training helpers still used by current
  target-band prediction and smoke tests.
- `stage3_dataset/`: dataset-profile helpers still used by archived
  `prediction_v3` feature compatibility.
- `stage2_harmonics/` and `stage2_harmonics_refine/`: MATLAB/COMSOL helpers
  still referenced by remaining validation and real-GA runners.
