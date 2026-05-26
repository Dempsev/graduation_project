# Moved Package

`optimization/seed_ranking` has been migrated to
`src/optimization/seed_ranking` as part of the final public refactor.

The root package is kept only as an import-compatibility shim. Use
`scripts/run_ga/` for the public target-band scoring, refinement, and
validation-manifest commands.
