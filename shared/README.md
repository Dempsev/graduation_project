# Shared

This directory is reserved for the second-stage refactor.

Phase 1 intentionally avoids large code movement. The goal is to stabilize the task-oriented architecture first.

The planned future extractions are:

- shared objective definitions
- shared feature lists
- shared train / val / test split helpers
- shared CSV / JSON / manifest I/O
- shared plotting and reporting utilities

Likely future homes:

- `shared/objectives/`
- `shared/features/`
- `shared/splits/`
- `shared/io/`
- `shared/plotting/`
