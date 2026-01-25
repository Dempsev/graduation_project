# Graduation Project
## K–Amplitude Dependent Band Structure Analysis (COMSOL + MATLAB + Python)

This repository supports an undergraduate thesis in Engineering Mechanics, focusing on **mechanical metamaterials** and **k–amplitude dependent band structures**. The workflow covers COMSOL modeling and parametric sweeps, MATLAB batch export, and Python post-processing/visualization.

---

## Project Background
Band-gap characteristics in mechanical metamaterials depend strongly on geometry and excitation amplitude. In this project, COMSOL is used to compute eigenfrequencies, and parametric sweeps are performed along k-paths and amplitude conditions. The resulting dispersion data are cleaned, organized, and plotted in Python.

---

## Recent Progress
- Split reusable COMSOL model steps into `model_core/` (00–07) and kept the entry script `create_open_00.m`.
- Batch sweep/export lives in `runners/` with `main_batch.m` as the primary entry.
- Python preprocessing and postprocessing scripts are organized into `preprocess/` and `postprocess/`.

---

## Repository Structure
```text
coad/
├─ model_core/                 # Core COMSOL MATLAB model functions (00–07)
├─ runners/                    # MATLAB scripts to run single/batch models
│  └─ legacy_run/              # Legacy runners (kept for reference)
├─ preprocess/                 # Python geometry preprocessing
├─ postprocess/                # Python result analysis/plots
├─ data/                       # Input/output models + CSVs
├─ README.md
└─ README_CN.md
```

---

## Requirements
- COMSOL Multiphysics 6.3 (modeling & solving)
- MATLAB (batch processing & export)
- Python 3.x (post-processing)
  - numpy
  - pandas
  - matplotlib

---

## Recommended Workflow
1. **COMSOL Modeling**
   - Run `model_core/create_open_00.m` to build and save the base model.
2. **Parametric Sweep + Export**
   - Run `runners/main_batch.m` (recommended).
   - Export frequency CSV files to `data/`.
3. **Python Post-Processing**
   - Use CSVs under `data/` and update paths if needed.
   - Run:
     ```bash
     python postprocess/k_amp_analyse.py
     ```

---

## Quick Start (Current Structure)
1. **Build the base model**
   - In MATLAB:
     ```matlab
     run('model_core/create_open_00.m')
     ```
   - This saves `mother_rebuild.mph` under `data/`.
2. **Run a sweep and export CSV**
   - In MATLAB:
     ```matlab
     run('runners/main_batch.m')
     ```
3. **Check outputs**
   - `data/batch_out/band_k_a1.csv`
4. **Post-process in Python**
   - Update the CSV path in `postprocess/k_amp_analyse*.py` if needed, then run:
     ```bash
     python postprocess/k_amp_analyse.py
     ```

---

## Troubleshooting
- **CSV is empty or all zeros**
  - Ensure the global evaluation (`gev`) is bound to the latest dataset (`dsetX`).
  - Clear table cache before export (`clearTableData`) and rerun `gev`.
- **Sweep results stuck at a fixed amplitude (e.g., 0.45)**
  - Update the sweep parameter list for both `k` and `amp`.
  - Confirm `gev` uses the latest dataset tag and is writing to the correct table.
- **No new dataset after a sweep**
  - Check that the study `std1` is actually executed and that the parametric feature is enabled.
  - Verify dataset tags via `model.result.dataset.tags()` in MATLAB.
- **Exported CSV has wrong columns**
  - Confirm the evaluation expression (e.g., `freq` or `solid.freq`) matches your model.
  - Recreate a temporary `gev` and `tbl` to avoid hidden GUI settings.
- **COMSOL server issues**
  - If using a server, call `mphstart()` before loading the model.

---

## Outputs
The Python scripts automatically:
- Clean raw COMSOL CSV files (including comment lines)
- Convert complex-frequency formats and extract real parts
- Organize band data by amplitude
- Plot band structures

Outputs are saved to `post_out/` (created automatically by the scripts).

---

## Author
- XuanCheng Su
- Engineering Mechanics, Undergraduate
