# Profile Layer

This package holds reusable mainline profile definitions.

Use profiles for:

- candidate pool source / shape / stage4 exclusion mapping
- point-spec collections
- frozen research assumptions or route variants that keep the same pipeline shape

Do not use profiles for:

- thresholds or quotas
- output roots or resume behavior

Those belong to:

- `policy` for thresholds / quotas / ranking rules
- `run config` for paths / output roots / resume settings

Keep wrapper scripts stable and move variation into profile objects first.
