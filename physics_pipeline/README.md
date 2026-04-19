# Physics Pipeline

This directory is the task-oriented entry layer for the **truth layer** of the project.

Phase 1 keeps the historical physical implementation in place, but reinterprets it
through one thesis-facing question:

> how is real physical truth produced before any prediction or optimization logic is applied?

## Role In The New Mainline

`physics_pipeline/` is the source of **physical truth production** for the whole repository.

It owns the part of the workflow that:

1. generates or screens shape families under trusted physical conditions
2. probes low-order and higher-order parameter directions
3. validates shortlisted designs back in COMSOL
4. feeds new real truth into later prediction and optimization work

This layer is shared by both:

- `prediction/` as the data source for model building
- `optimization/` as the source of real objective values and final validation

## Historical Directories That Belong To The Truth Layer

Phase 1 does **not** move these directories.

They remain the implementation roots for physical truth production:

- `stage1/`
- `stage2/`
- `stage2_refine/`
- `stage2_harmonics/`
- `stage2_harmonics_refine/`
- `stage4_validation/`

These directories should now be read as one connected physical pipeline rather than
as isolated historical stages.

## Recommended Reading Order

If the goal is to understand how the repository produces real truth, read:

1. `stage1/`
2. `stage2/`
3. `stage2_refine/`
4. `stage2_harmonics/`
5. `stage2_harmonics_refine/`
6. `stage4_validation/`

## Phase-1 Boundary

This phase is intentionally a **logic refactor**, not a directory merge.

It does **not**:

- move historical stage directories
- merge `stage1~stage4` into one new implementation root
- rewrite COMSOL-side solver logic

It **does**:

- define `physics_pipeline/` as the official truth-layer entry point
- unify the terminology used across the repository
- make the later prediction and optimization story easier to read

## Follow-Up Priority

Phase 1 fixes the architecture language first.

The default next-step order is:

1. architecture cleanup first
2. target-band execution second

That means the truth layer stays stable in this round while the prediction and
optimization layers are repositioned around it.
