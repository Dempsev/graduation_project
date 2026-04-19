# Prediction V5

`prediction_v5/` is the corrected-label pure prediction line.

It keeps the inputs pure:

- Fourier parameters
- shape geometry
- local contour descriptors

It changes only the targets:

- `gap34_*` and `max_gap_*` are reparsed from the raw `tbl1` exports with a robust parser
- complex-valued frequencies are kept via their real part instead of being silently dropped

This line is intended to answer a narrow question:

- how far can the pure-structural predictor go once the target definition is made physically consistent?
