# Prediction V4

`prediction_v4/` is a diagnostic enriched prediction line.

It keeps the design-point aggregation and stricter evaluation protocol from `prediction_v2/`, then adds:

- existing COMSOL context scalars already present in the unified dataset (`shift`, `neigs`, `contact_length`, `n_domains`, `has_tiny_fragments`)
- dispersion-level features derived from the raw `tbl1` exports

This line is intentionally kept separate from `prediction/`, `prediction_v2/`, and `prediction_v3/`.

Important scope note:

- `v4` is not a strict pre-solve surrogate because it consumes post-solve `tbl1` band-structure signals
- its main purpose is diagnostic: measure how much predictive signal we were leaving on the table by collapsing COMSOL outputs too aggressively
