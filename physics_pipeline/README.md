# Physics Pipeline

This directory is the task-oriented entry layer for the physical data-production side of the project.

During the phase-1 refactor, the physical implementation remains in the historical stage-based directories:

- `stage1/`
- `stage2/`
- `stage2_refine/`
- `stage2_harmonics/`
- `stage2_harmonics_refine/`
- `stage4_validation/`

## Role

The physical pipeline is responsible for producing real COMSOL truth:

1. screen snake-generated shapes under trusted baseline conditions
2. scan and refine low-order Fourier parameters
3. probe higher-order harmonics directions
4. validate shortlisted candidates back in COMSOL

This layer is shared by both the prediction line and the optimization line.

## Reading Order

1. `stage1/`
2. `stage2/`
3. `stage2_refine/`
4. `stage2_harmonics/`
5. `stage2_harmonics_refine/`
6. `stage4_validation/`

## Refactor Note

Phase 1 does not move the physical implementation. It only adds a cleaner top-level architecture view so the codebase can be read by research task instead of only by historical stage name.
