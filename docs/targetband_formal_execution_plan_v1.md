# Target-Band Inverse Design Formal Execution Plan

## 1. Current Position

The project is no longer at the stage of asking whether target-band optimization can start.

That question has already been answered by the current codebase and recent real-COMSOL results:

- the truth pipeline is complete
- the target-band conditional predictor is already usable
- the shape front-end has been upgraded from old `gap34` selection to band-aware shape selection
- exploratory real search has already opened weak bands that conservative search could not reach
- the new truth has already been folded back into the learning pipeline as `v8`

So the project should now be positioned as:

**a thesis-band-catalog target-band conditional prediction and inverse-design mainline**

with a carefully controlled scope:

- current 2D phononic crystal workflow
- current parameterized shape family space
- current thesis band catalog
- generalization across unseen shape families
- partial transfer across catalog bands

and with clear non-claims:

- not arbitrary continuous-frequency generalization
- not arbitrary material-system generalization
- not universal optimization for all phononic crystal representations

## 2. Formal Thesis Claim

The main claim should now be fixed as:

**We establish a target-band-conditioned prediction and inverse-design workflow for the thesis band catalog, where a conditional predictor proposes promising candidates for a specified band, band-aware search/refinement improves them under real COMSOL evaluation, and the resulting structures are validated as usable target-band designs.**

This claim should be supported by four subclaims:

1. The predictor learns useful target-band structure-response relationships.
2. The predictor is useful as a search front-end, not just as an offline regressor/classifier.
3. Band-aware shape selection matters and materially changes weak-band search performance.
4. Weak-band inverse design becomes feasible once search is upgraded from the old conservative `gap34 / 200Hz` basin to band-aware exploratory real search.

## 3. Mainline Architecture

The current project should be written and explained as a five-layer system:

1. **Truth Production**
   - real COMSOL truth generation and validation
   - stage1/stage2/stage4 lines

2. **Conditional Prediction**
   - target-band fixed-window and parametric predictors
   - current main dataset: `windows_dense_v8_truth_plus_exploratory_aug_v1`

3. **Band-Aware Shape Selection**
   - shape atlas
   - family-balanced, band-aware shape pools
   - strong / near-miss / weak-band contributor / hard-negative roles

4. **Prediction-Guided Search and Refinement**
   - RF classification for likely-open screening
   - HGB regression for cover-ratio ranking
   - target-band shortlist generation
   - real exploratory search/refinement

5. **Validation and Truth Harvesting**
   - COMSOL verification
   - harvested truth returned to the training set
   - co-evolution of model and search

This is the real current system. It is no longer accurate to describe the project as only a small optimization prototype.

## 4. What Is Already Established

The following points should now be treated as established results, not open questions.

### 4.1 Predictor mainline exists

The current main model stack is fixed as:

- classifier: RF
- regressor: HGB
- dataset: `windows_dense_v8_truth_plus_exploratory_aug_v1`

This stack should remain the default unless a clearly stronger replacement is demonstrated.

### 4.2 Shape is now a first-class task variable

The project has already moved beyond only tuning Fourier parameters.

The shape front-end is now explicitly band-aware via:

- `prediction_targetband_param_v1/tools/build_targetband_shape_atlas_v1.py`
- `data/analysis/targetband_shape_atlas_v1/`

This is an important conceptual upgrade and should be presented as such.

### 4.3 Weak-band search has been materially improved

The exploratory supplement search has already shown that weak bands were not fundamentally impossible; they were underexplored under the previous search setup.

Representative current best results from:

- `data/comsol_batch/comsol_in_loop_band_supplement_exploratory_v2/ga_band_catalog_summary_v1.csv`

include:

- `band200_240`: cover `1.000`
- `band220_260`: cover `1.000`
- `band240_280`: cover `0.898`
- `band180_220`: cover `1.000`

This is a major shift from the earlier conservative supplement behavior.

### 4.4 Truth harvesting loop is real

The project already has a functioning loop:

- search produces new weak-band truth
- truth is harvested back into the fixed-window data
- stacked again into the parametric dataset
- models are retrained on the new distribution

This loop should be highlighted as one of the project's strongest features.

## 5. Main Evidence Structure

The core evidence in the thesis should now be organized around three questions.

### Question A: Is the predictor useful for shortlist formation?

This should be answered using:

- family-CV
- leave-one-band-tag-out
- top-k / shortlist quality
- probability calibration / monotonicity checks

The key interpretation is:

The predictor does not need to perfectly predict every sample; it needs to put promising candidates near the front of the ranking.

### Question B: Can the predictor actually drive real search?

This should be answered using:

- predictor-guided candidate proposal
- real search/refinement under COMSOL
- validation of final candidates
- comparison against baselines

The important message is:

The predictor is not replacing physics; it is turning inverse design into guided search.

### Question C: Can weak bands be opened or improved under the new workflow?

This should be answered using:

- conservative weak-band search vs exploratory weak-band search
- old shape pool vs band-aware shape pool
- weak-band data coverage before and after exploratory harvesting
- final best weak-band structures and their real overlaps/covers

This is where the recent `exploratory v2` result becomes central.

## 6. Updated Research Strategy

The project should now be run as two coupled but unequal lines:

### A Line: predictor strengthening

Goal:

- make the target-band predictor more reliable as a shortlist engine
- improve catalog-internal transfer
- stabilize weak-band ranking

### B Line: inverse-design demonstration

Goal:

- produce strong real-COMSOL target-band cases
- show the value of band-aware search and refinement
- build the thesis result tables and figures

These lines are coupled:

- search yields difficult and weak-band truth
- truth improves the predictor
- predictor improves future shortlist quality

But they are no longer equal in urgency.

At the current stage, **inverse-design demonstration and evidence consolidation** should take priority over large new model-architecture exploration.

## 7. Immediate Execution Order

The next execution order should be fixed as follows.

### Step 1. Freeze the current mainline definition

Lock the following:

- thesis main claim
- thesis band catalog
- current default model pair: RF + HGB
- current default dataset: `v8`
- current shape-aware front-end

Do not reopen model-family debates unless new evidence clearly requires it.

### Step 2. Build a predictor-readiness report

Create one concise report that answers:

- how good is family-CV?
- how good is leave-one-band?
- how good are top-k shortlisted candidates?
- are scores/probabilities at least basically monotonic and useful?

This becomes the formal justification for using the predictor in inverse design.

### Step 3. Formalize inverse-design case studies

The first canonical cases should now be:

1. `band200_240`
   - `ep193_step51_contour_xy`
2. `band220_260`
   - `ep253_step54_contour_xy`
3. `band240_280`
   - `ep253_step54_contour_xy`
4. `band180_220`
   - `ep248_step27_contour_xy`

Each case should be documented with:

- shape identity
- optimized parameters
- target band
- real lower/upper edges
- overlap Hz
- cover ratio
- comparison against earlier baseline behavior

### Step 4. Run structured baseline comparisons

The comparison set should now be standardized.

For each target band, compare against as many of the following as budget allows:

- random or generic candidate baseline
- old seed/local line
- old conservative supplement line
- old band-catalog real-GA line
- predictor-guided / shape-aware / exploratory line

The key metrics are:

- real open rate
- real overlap Hz
- real cover ratio
- top-k hit count
- best candidate quality
- family diversity
- budget efficiency

### Step 5. Consolidate weak-band coverage analysis

Do not evaluate progress only by aggregate model scores.

Track:

- positive sample count by weak band
- positive family count by weak band
- mean positive cover ratio by weak band
- top-k shortlist quality by weak band
- final inverse-design usefulness by weak band

This should become a standing analysis table.

### Step 6. Add robustness only after the above is stable

Robustness is valuable, but it is not the very next blocker.

After the main evidence package above is stable, add:

- threshold sensitivity
- ranking stability
- local parameter perturbation stability
- candidate neighborhood stability

## 8. What Should Not Be the Main Focus Right Now

The following should not become the next mainline unless there is a strong reason:

- large material-profile expansion
- arbitrary continuous-band claims
- replacing RF/HGB with an entirely different predictor family
- rerunning old conservative search lines
- returning to a shape pool sorted only by `gap34_gain_Hz`

These are either secondary or already superseded.

## 9. Writing Strategy for the Thesis

The thesis should now be written in the following progression.

### Chapter logic

1. **Truth generation and data accumulation**
2. **Target-band conditional prediction**
3. **Why shape-aware selection is needed**
4. **Prediction-guided inverse design workflow**
5. **Weak-band search breakthrough via exploratory real search**
6. **Validation, comparison, and limitations**

### Key narrative shift

Do not frame the project as:

- “we searched for the structure with the widest gap”

Frame it as:

- “we built a target-band-conditioned prediction and inverse-design workflow”
- “the predictor acts as a shortlist engine”
- “shape-aware and exploratory real search are necessary to escape the old `gap34 / 200Hz` basin”
- “the workflow is validated on a fixed thesis band catalog”

### Claim wording guidance

Preferred wording:

- “catalog-internal target-band conditional prediction”
- “target-band inverse design”
- “predictor-guided shortlist and real refinement”
- “band-aware shape selection”
- “weak-band truth harvesting”

Avoid overclaiming wording such as:

- “arbitrary-frequency universal prediction”
- “fully general inverse design”
- “complete unseen-band generalization”

## 10. Final Operational Conclusion

The project should now proceed under this operational judgment:

**The core question is no longer whether prediction-driven optimization can begin. The core question is how to consolidate the existing target-band conditional prediction, band-aware shape selection, and exploratory real-search results into a clean, well-compared, thesis-grade inverse-design mainline.**

That means the next work should focus on:

- stronger evidence packaging
- better comparison structure
- stronger case-study presentation
- stable weak-band coverage accounting

not on reopening the basic direction.
