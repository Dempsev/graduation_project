function seedIds = select_plan_a_validated_seed_ids_v1(shapeSummaryCsv, topK, minMeanGainHz, minPositiveRate, minSolveSuccessCount)
%SELECT_PLAN_A_VALIDATED_SEED_IDS_V1 Choose real-validated seeds from plan A.

if nargin < 2 || isempty(topK)
    topK = 3;
end
if nargin < 3 || isempty(minMeanGainHz)
    minMeanGainHz = 0.0;
end
if nargin < 4 || isempty(minPositiveRate)
    minPositiveRate = 0.50;
end
if nargin < 5 || isempty(minSolveSuccessCount)
    minSolveSuccessCount = 1;
end

if ~isfile(shapeSummaryCsv)
    error('select_plan_a_validated_seed_ids_v1:MissingSummary', ...
        'Plan-A validation shape summary not found: %s', shapeSummaryCsv);
end

tbl = readtable(shapeSummaryCsv);
required = {'shape_id', 'solve_success_count', 'positive_gap34_gain_rate', 'mean_gap34_gain_Hz', 'best_gap34_gain_Hz'};
missing = setdiff(required, tbl.Properties.VariableNames, 'stable');
if ~isempty(missing)
    error('select_plan_a_validated_seed_ids_v1:MissingColumns', ...
        'Plan-A validation shape summary missing required columns: %s', strjoin(missing, ', '));
end

shapeId = string(tbl.shape_id);
solveSuccess = double(tbl.solve_success_count);
positiveRate = double(tbl.positive_gap34_gain_rate);
meanGain = double(tbl.mean_gap34_gain_Hz);
bestGain = double(tbl.best_gap34_gain_Hz);

mask = strlength(shapeId) > 0 & ...
    solveSuccess >= minSolveSuccessCount & ...
    positiveRate >= minPositiveRate & ...
    isfinite(meanGain) & ...
    meanGain >= minMeanGainHz;

work = tbl(mask, :);
if isempty(work)
    error('select_plan_a_validated_seed_ids_v1:NoEligibleSeeds', ...
        'No plan-A seeds satisfy the real-validation thresholds.');
end

work = sortrows(work, ...
    {'mean_gap34_gain_Hz', 'best_gap34_gain_Hz', 'positive_gap34_gain_rate', 'solve_success_count', 'shape_id'}, ...
    {'descend', 'descend', 'descend', 'descend', 'ascend'});

limit = min(height(work), topK);
seedIds = string(work.shape_id(1:limit));
end
