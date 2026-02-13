# COAD Workflow (COMSOL + MATLAB + Python)

This project generates geometry from RL snake states, builds COMSOL models in batch, and exports `tbl1` results.

## Current Pipeline
1. Generate states: `snake/`
2. Convert states to contour points: `preprocess/`
3. Batch build + solve COMSOL models: `runners/run_shape_batch.m`
4. Analyze exports: `postprocess/`

## Key Folders
```text
coad/
  model_core/
    create_open_00.m
    build_geom_02.m
    set_material_03.m
    set_physics_04.m
    set_mesh_05.m
    set_study_06.m
    set_results_07.m
  runners/
    run_shape_batch.m
    legacy_run/
      main_batch.m
      run_comsol_once.m
      run_sweep_export_eig*.m
  snake/
  preprocess/
  postprocess/
  data/
    shape_points/
    shape_batch/
      models/
      tbl1_exports/
      logs/
        run_shape_batch_errors.csv
      perturb_skip_log.csv
    snake_states/
    snake_checkpoints/
    shape_previews/
```

## Batch Run (Main Entry)
```matlab
cd('d:\graduation_project\coad\runners');
run('run_shape_batch.m');
```

## Batch Behavior
- Non-contact discrete perturbation samples are skipped.
- Skipped samples are recorded in `data/shape_batch/perturb_skip_log.csv`.
- Runtime failures are recorded in `data/shape_batch/logs/run_shape_batch_errors.csv` and batch continues.
- Valid model files are saved to `data/shape_batch/models/`.
- `tbl1` CSV is exported to `data/shape_batch/tbl1_exports/`.
- `tbl1` file name follows shape stem, e.g. `ep1084_step120_tbl1.csv`.

## Notes
- Periodic boundary pairs are selected by rectangle position (left/right for `kx`, bottom/top for `ky`), not by fixed boundary IDs.
- Legacy scripts are kept under `runners/legacy_run/` for reference.
