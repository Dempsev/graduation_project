function seedIds = select_seed_ids_from_shape_summary_v1(shapeSummaryCsv, gate)
%SELECT_SEED_IDS_FROM_SHAPE_SUMMARY_V1 Generic selector for real-validated seed shapes.

if nargin < 2 || isempty(gate)
    gate = get_plan_a_seed_gate_defaults_v1();
end

defs = get_real_ga_summary_fields_v1();

if ~isfile(shapeSummaryCsv)
    error('select_seed_ids_from_shape_summary_v1:MissingSummary', ...
        'Shape summary not found: %s', shapeSummaryCsv);
end

tbl = readtable(shapeSummaryCsv);
required = defs.planARequiredShapeSummaryColumns;
missing = setdiff(required, tbl.Properties.VariableNames, 'stable');
if ~isempty(missing)
    error('select_seed_ids_from_shape_summary_v1:MissingColumns', ...
        'Shape summary missing required columns: %s', strjoin(missing, ', '));
end

shapeId = string(tbl.shape_id);
solveSuccess = double(tbl.solve_success_count);
positiveRate = double(tbl.positive_gap34_gain_rate);
meanGain = double(tbl.mean_gap34_gain_Hz);

mask = strlength(shapeId) > 0 & ...
    solveSuccess >= gate.minSolveSuccessCount & ...
    positiveRate >= gate.minPositiveRate & ...
    isfinite(meanGain) & ...
    meanGain >= gate.minMeanGainHz;

work = tbl(mask, :);
if isempty(work)
    error('select_seed_ids_from_shape_summary_v1:NoEligibleSeeds', ...
        'No seeds satisfy the real-validation thresholds.');
end

work = sortrows(work, defs.planASeedSortFields, defs.planASeedSortDirections);
limit = min(height(work), gate.topKSeeds);
seedIds = string(work.shape_id(1:limit));
end
