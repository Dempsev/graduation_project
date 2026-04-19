# Prediction V7

`prediction_v7/` is the pure-structure mainline built around a new global target:

- scan all complete adjacent-band gaps above the acoustic branches
- keep only gaps whose upper edge stays below a chosen frequency cap
- choose the widest remaining gap as the training target

This keeps the label physically stable without pinning the task to a fixed band pair.

Default experiments in this folder compare two caps:

- `250 Hz`
- `300 Hz`

The dataset also records:

- the selected lower/upper band indices
- lower/upper gap edges
- gap center frequency
- whether the chosen gap overlaps current engineering windows
