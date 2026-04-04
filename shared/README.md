# Shared

This directory is the home for shared abstractions extracted during the refactor.

Phase 2 has started with the first safe extraction set:

- `shared/features/`
  - prediction feature presets and reusable feature groups
- `shared/objectives/`
  - prediction target / label definitions
- `shared/splits/`
  - prediction split helpers such as external stage holdout

Planned future extractions:

- shared CSV / JSON / manifest I/O
- shared plotting and reporting utilities
- shared optimization-side feature and target definitions

Likely future homes:

- `shared/io/`
- `shared/plotting/`
