# Target-Band Prediction V1

`prediction_targetband_v1/` is the first fixed-frequency companion line.

It keeps the inputs purely structural:

- Fourier parameters
- shape geometry
- local contour descriptors

It changes the target:

- choose a fixed frequency window `[f_low, f_high]`
- scan robust complete gaps from the COMSOL band structure
- label whether any complete gap overlaps the target window
- record the best overlap width and the corresponding band pair

The first intended use is design-oriented screening:

- given a target band, rank structures by the probability that they open a useful gap in that window

## Evaluation Protocol

This line uses the same pure-structure inputs as the main prediction line, but its primary benchmark is:

- `family CV` (`StratifiedGroupKFold` grouped by `shape_family`)

This is the main metric because it best reflects the intended use case:

- generalize to unseen structure families
- avoid optimistic leakage between near-duplicate shapes inside the same family

`leave-one-stage-out` is still kept as a secondary stability check, but it is not the main score because some fixed windows become highly stage-skewed.

## Current Fixed Windows

Three windows have been validated so far:

- `120-160 Hz`: a discriminative low-frequency task with positive rate around `21.7%`
- `180-220 Hz`: a transition-band task with positive rate around `79.3%`
- `220-260 Hz`: a mostly-open mid-frequency task with positive rate around `83.3%`

Together they already show that the fixed-band setup can express meaningfully different screening tasks:

- one sparse, precision-oriented window
- one transition window with stronger structure-frequency interaction
- one dense, high-recall window

## Companion Regression

The fixed-band line now has a positive-only regression companion:

- classifier target: `target_gap_is_open`
- regressor target: `target_gap_cover_ratio` or `target_gap_overlap_Hz`

The intended workflow is:

1. predict whether the target band opens at all
2. for predicted-open candidates, estimate how much of the target band is actually covered

This keeps the regression task from being dominated by the large mass of zeros.
