# Material Profile Plan

## Goal

This round implements a minimal "material profile" entry so the current
"soft matrix + hard inclusion" setup is no longer scattered across multiple
MATLAB scripts.

The priority is:

1. Keep the current default behavior unchanged.
2. Make profile switching possible from MATLAB without rewriting runners.
3. Avoid changing current train / scoring / manifest outputs.
4. Leave older historical scripts mostly untouched unless they are on the
   active execution path.

## New Unified Entry

The new material profile entry lives in `model_core/`:

- `model_core/get_material_profile.m`
- `model_core/resolve_material_profile_name.m`
- `model_core/apply_material_profile_to_config.m`
- `model_core/set_material_03.m`

### Supported Profiles

| Profile | Role | Matrix `(rho, E, nu)` | Inclusion `(rho, E, nu)` |
| --- | --- | --- | --- |
| `baseline_soft_hard` | default mainline | `1050, 3e5, 0.49` | `7850, 2.1e10, 0.30` |
| `alt_soft_hard_1` | exploratory alt | `1120, 5e5, 0.47` | `7600, 1.5e10, 0.29` |
| `alt_soft_hard_2` | exploratory alt | `980, 2e5, 0.495` | `8900, 3.0e10, 0.33` |

All three profiles currently map to the same research-level material case:
`soft_matrix_hard_inclusion`.

That means:

- existing CSV/result schemas that only store `material_case` stay intact
- default downstream behavior does not break
- profile switching happens inside COMSOL material constants, not by changing
  current manifest/train/scoring logic

## How Switching Works

### Default Behavior

If you do nothing, the repository still uses:

```matlab
baseline_soft_hard
```

This reproduces the previous hard-coded `set_material_03` behavior.

### MATLAB-side Switch Entry

The lightweight switch entry is a base-workspace variable:

```matlab
assignin('base', 'material_profile_name', 'alt_soft_hard_1');
run(fullfile(pwd, 'runners', 'run_stage4_validation_ab_v10.m'));
```

Reset back to default:

```matlab
assignin('base', 'material_profile_name', 'baseline_soft_hard');
```

This works because:

- stage configs call `apply_material_profile_to_config`
- direct batch runners call `resolve_material_profile_name`
- `set_material_03` now accepts either:
  - no explicit profile
  - a profile name
  - a config struct containing `materialProfile`
  - a full material profile struct

## Files Already Wired

### Core model entry

- `model_core/set_material_03.m`
- `model_core/create_open_00.m`

What changed:

- `set_material_03` is now the single COMSOL material application point.
- default call path still resolves to `baseline_soft_hard`.
- `create_open_00.m` also uses the same profile entry, so manual model rebuild
  and stage runners no longer diverge.

### Stage configs already wired

- `stage1/get_stage1_config.m`
- `stage2/get_stage2_config.m`
- `stage2_refine/get_stage2_refine_config.m`
- `stage2_harmonics/get_stage2_harmonics_config.m`
- `stage2_harmonics_refine/get_stage2_harmonics_refine_config.m`

What changed:

- each config now sets `cfg.materialProfile = 'baseline_soft_hard'`
- then calls `apply_material_profile_to_config(cfg)`
- config signatures now include `material_profile=...`

### Stage evaluators already wired

- `stage1/evaluate_single_shape.m`
- `stage2/evaluate_stage2_case_internal.m`
- `stage2_harmonics/evaluate_stage2_harmonics_case_internal.m`
- `stage2_harmonics_refine/evaluate_stage2_harmonics_refine_case_internal.m`

What changed:

- material application is now `set_material_03(model, cfg)`
- the active profile follows the stage config automatically

### Runners already wired

Direct material-entry runners:

- `runners/run_shape_batch.m`
- `runners/run_fourier_screening_batch.m`
- `runners/run_fourier_shape_overlay_batch.m`
- `runners/run_fourier_hard_screening_batch.m`

Mainline stage runners with profile banner:

- `runners/run_stage1_shape_screening.m`
- `runners/run_stage2_fourier_robustness_screening.m`
- `runners/run_stage2_refine_screening.m`
- `runners/run_stage2_harmonics_screening.m`
- `runners/run_stage2_harmonics_refine_screening.m`
- `runners/run_stage4_validation_ab_v10.m`
- `runners/run_stage4_validation_ab_v11.m`
- `runners/run_stage4_validation_ab_ga_v1.m`

### Stage4 configs already wired

- `stage4_validation/get_stage4_validation_config.m`
- `stage4_validation/get_stage4_validation_config_v10.m`
- `stage4_validation/get_stage4_validation_config_v11.m`
- `stage4_validation/get_stage4_validation_config_ga_v1.m`

What changed:

- `cfg.materialProfile` now participates in `configSignature`
- this prevents silent resume/reuse collisions between different profiles on
  the current mainline validation routes

## Not Fully Wired Yet

These are intentionally left as TODO for now to keep this round minimal.

### Older validation config signatures

Not yet explicitly updated:

- `stage4_validation/get_stage4_validation_config_v2.m`
- `stage4_validation/get_stage4_validation_config_v3.m`
- `stage4_validation/get_stage4_validation_config_v4.m`
- `stage4_validation/get_stage4_validation_config_v5.m`
- `stage4_validation/get_stage4_validation_config_v6.m`
- `stage4_validation/get_stage4_validation_config_v7.m`
- `stage4_validation/get_stage4_validation_config_v8.m`
- `stage4_validation/get_stage4_validation_config_v9.m`

Current state:

- they still inherit the runtime material profile through
  `get_stage2_harmonics_refine_config()`
- but their local `configSignature` strings have not yet been extended with
  `materialProfile`

So:

- they are "switchable at runtime"
- but not yet fully protected against same-output-path resume confusion

### Historical validation runner banners

Not all older `run_stage4_validation_ab_v*.m` files were updated to print the
profile name in their headers.

This is cosmetic, not functional.

### Output schema is intentionally unchanged

We did **not** add a new `material_profile` column into current results CSVs.

Reason:

- many existing scripts expect current column sets
- the user request explicitly asked not to break default outputs

TODO:

- if later needed, add `material_profile` as an optional new column in a
  versioned result schema, not as a silent in-place schema mutation

### No automatic per-profile output-directory split yet

Current behavior:

- switching the profile changes the physics constants
- it does **not** automatically create a new `outDir` suffix

This is deliberate for minimal intrusion.

TODO:

- add a tiny helper later to derive `outDir/resultsMat/resultsCsv/tbl1Dir`
  from `cfg.materialProfile` when running comparative studies

## Minimal Same-Shape / Same-Point Comparison Example

This is the smallest current comparison flow without changing MATLAB/COMSOL
templates or historical runners.

```matlab
addpath(genpath(fullfile(pwd, 'model_core')));
addpath(genpath(fullfile(pwd, 'stage2_harmonics_refine')));

cfgA = get_stage2_harmonics_refine_config();
cfgA = apply_material_profile_to_config(cfgA, 'baseline_soft_hard');

cfgB = get_stage2_harmonics_refine_config();
cfgB = apply_material_profile_to_config(cfgB, 'alt_soft_hard_1');

shapeId = 'ep249_step33_contour_xy';
shapeFile = fullfile(cfgA.shapeDir, [shapeId '.csv']);

sampleMetaA = struct( ...
    'sample_id', "matcmp__baseline", ...
    'candidate_id', "matcmp", ...
    'shape_id', string(shapeId), ...
    'shape_family', "ep249", ...
    'shape_role', "manual_compare", ...
    'shape_file', string(shapeFile) ...
);

sampleMetaB = sampleMetaA;
sampleMetaB.sample_id = "matcmp__alt1";

pointSpec = struct( ...
    'main_id', 'rf09', ...
    'point_id', 'rf09_h00_center', ...
    'a1', 0.50, ...
    'a2', -0.12, ...
    'b2', 0.04, ...
    'r0', 0.0120, ...
    'a3', 0.0, ...
    'b3', 0.0, ...
    'a4', 0.015, ...
    'b4', 0.0, ...
    'a5', 0.0, ...
    'b5', 0.02 ...
);

refPoint = struct();

resA = evaluate_stage2_harmonics_refine_case_internal(cfgA, sampleMetaA, pointSpec, refPoint);
resB = evaluate_stage2_harmonics_refine_case_internal(cfgB, sampleMetaB, pointSpec, refPoint);

cmp = struct2table([resA; resB], 'AsArray', true);
cmp.material_profile = [string(cfgA.materialProfile); string(cfgB.materialProfile)];

cmp(:, { ...
    'sample_id', ...
    'material_profile', ...
    'material_case', ...
    'solve_success', ...
    'gap34_Hz', ...
    'gap34_gain_Hz', ...
    'max_gap_Hz' ...
})
```

Notes:

- use different `sample_id` values so exported `tbl1` filenames do not collide
- this example keeps current output layout unchanged
- if you want persistent side-by-side batch outputs, the next step should be a
  tiny profile-aware output-dir helper, not a runner rewrite

## Why This Is Safe

Rollback is simple because:

- default callers still resolve to `baseline_soft_hard`
- material changes are centralized in `set_material_03`
- train/scoring/manifest Python code was not touched
- existing `material_case` output semantics stay the same
- runner names and directory layout stay the same

If needed, rollback can be done by:

1. restoring `model_core/set_material_03.m`
2. removing the three new helper files in `model_core/`
3. removing `cfg.materialProfile` initialization from the wired config files

## Next Recommended TODO

If we continue from here, the lowest-risk next step is:

1. extend `materialProfile` into older `stage4_validation_config_v2~v9` signatures
2. add an optional profile-aware output-dir helper for comparative experiments
3. only after that, consider whether result CSVs need an explicit
   `material_profile` column
