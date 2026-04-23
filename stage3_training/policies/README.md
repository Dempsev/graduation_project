# Policy Layer

This directory is the preferred place for mainline strategy changes.

Use policy files for:

- scoring thresholds and weights
- validation manifest quotas and caps
- GA search bounds, whitelist, and search budget
- selection rules that do not change the pipeline shape

Do not use policies for:

- frozen research assumptions
- output roots or resume behavior

Those belong to:

- `profile` for frozen assumptions / candidate-construction choices
- `run config` for paths / output roots / resume settings

Do not create a new `vN` script when the only difference is policy.
