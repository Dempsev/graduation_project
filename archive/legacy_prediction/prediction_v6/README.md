# Pure Prediction V6

`prediction_v6/` defines the pure-prediction target as:

- the first complete gap found above the configured number of acoustic branches

This line keeps the inputs purely structural:

- Fourier coefficients
- shape geometry
- local contour descriptors

Compared with the earlier fixed `gap34` lines, this target is intended to be:

- closer to the original low-order main-gap intuition
- less sensitive to band-index drift
- more physically consistent than a hard-coded `3-4` label

The dataset also records:

- the discovered band pair
- the gap center frequency
- whether the first gap overlaps the current engineering windows used by the target-band screening line
