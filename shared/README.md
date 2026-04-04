# Shared

This directory is the home for shared abstractions extracted during the refactor.

Phase 2 has started with the first safe extraction set:

- `shared/features/`
  - prediction feature presets and reusable feature groups
- `shared/objectives/`
  - prediction target / label definitions
- `shared/splits/`
  - prediction split helpers such as external stage holdout
- `shared/io/`
  - shared Python runner helpers
- `shared/optimization/`
  - shared optimization-side script and policy definitions

Planned future extractions:

- shared CSV / JSON / manifest I/O beyond the current Python runner helper
- shared plotting and reporting utilities
- shared optimization-side feature and target definitions
- shared MATLAB helpers for real-GA config and artifact paths

Likely future homes:

- `shared/io/`
- `shared/plotting/`
