# Real COMSOL-In-Loop GA Final Summary

This summary records the six-band real GA baseline used in the final thesis.
The source table is:

`research_validation/ch4_ga_real_optimization/ch4_ga_summary_20gen.csv`

Each band uses 20 generations with population size 6, for 120 expected COMSOL
evaluations per band.

| Target band | Evaluations | Solve success | Active overlap | Best overlap Hz | Best cover ratio | Best shape |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 140-180 Hz | 120 | 108 | 105 | 22.2665 | 0.5567 | `ep172_step75_contour_xy` |
| 160-200 Hz | 120 | 112 | 112 | 32.4455 | 0.8111 | `ep206_step33_contour_xy` |
| 180-220 Hz | 120 | 111 | 107 | 40.0000 | 1.0000 | `ep206_step33_contour_xy` |
| 200-240 Hz | 120 | 109 | 98 | 35.2829 | 0.8821 | `ep253_step54_contour_xy` |
| 220-260 Hz | 120 | 106 | 102 | 4.0976 | 0.1024 | `ep248_step27_contour_xy` |
| 240-280 Hz | 120 | 105 | 105 | 3.9345 | 0.0984 | `ep248_step27_contour_xy` |

## Interpretation

- 180-220 Hz reaches full target-band coverage.
- 160-200 Hz and 200-240 Hz have strong coverage.
- 220-260 Hz and 240-280 Hz remain weak even under real GA, which supports the
  thesis boundary claim that the current structure family and parameterization
  are limited at higher target bands.
- GA fitness is real COMSOL target-band overlap, not predictor output.
