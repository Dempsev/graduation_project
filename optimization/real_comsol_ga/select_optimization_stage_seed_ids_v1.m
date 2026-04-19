function seedIds = select_optimization_stage_seed_ids_v1(summaryCsv, topK, minMeanGainHz, minPositiveRate, minSolveSuccessCount)
%SELECT_OPTIMIZATION_STAGE_SEED_IDS_V1 Choose survivor basins from a previous stage.
% Prefer shape-level summaries when available, but fall back to ga_search_summary_v1
% when a stage only exports per-seed search summaries.

if nargin < 2 || isempty(topK)
    topK = 5;
end
if nargin < 3 || isempty(minMeanGainHz)
    minMeanGainHz = 0.0;
end
if nargin < 4 || isempty(minPositiveRate)
    minPositiveRate = 0.0;
end
if nargin < 5 || isempty(minSolveSuccessCount)
    minSolveSuccessCount = 1;
end

gate = struct();
gate.topKSeeds = topK;
gate.minMeanGainHz = minMeanGainHz;
gate.minPositiveRate = minPositiveRate;
gate.minSolveSuccessCount = minSolveSuccessCount;

if isfile(summaryCsv)
    seedIds = select_from_supported_summary(summaryCsv, gate);
    return;
end

[summaryDir, ~, ~] = fileparts(summaryCsv);
fallbackSearchSummary = fullfile(summaryDir, 'ga_search_summary_v1.csv');
if isfile(fallbackSearchSummary)
    seedIds = select_from_search_summary(fallbackSearchSummary, gate);
    return;
end

error('select_optimization_stage_seed_ids_v1:MissingSummary', ...
    'Neither stage summary nor fallback search summary exists: %s', summaryCsv);
end

function seedIds = select_from_supported_summary(summaryCsv, gate)
tbl = readtable(summaryCsv);
vars = tbl.Properties.VariableNames;

if ismember('shape_id', vars) && ismember('mean_gap34_gain_Hz', vars)
    seedIds = select_seed_ids_from_shape_summary_v1(summaryCsv, gate);
    return;
end

if ismember('seed_shape_id', vars) && ismember('best_gap34_gain_Hz', vars)
    seedIds = select_from_search_summary(summaryCsv, gate);
    return;
end

error('select_optimization_stage_seed_ids_v1:UnsupportedSummary', ...
    'Unsupported stage summary format: %s', summaryCsv);
end

function seedIds = select_from_search_summary(searchSummaryCsv, gate)
tbl = readtable(searchSummaryCsv);
required = {'seed_shape_id','solve_success_count','positive_gain_count','best_gap34_gain_Hz','delta_gap34_gain_Hz'};
missing = setdiff(required, tbl.Properties.VariableNames, 'stable');
if ~isempty(missing)
    error('select_optimization_stage_seed_ids_v1:MissingColumns', ...
        'Stage search summary missing required columns: %s', strjoin(missing, ', '));
end

work = tbl(:, required);
work.seed_shape_id = string(work.seed_shape_id);
work.solve_success_count = double(work.solve_success_count);
work.positive_gain_count = double(work.positive_gain_count);
work.best_gap34_gain_Hz = double(work.best_gap34_gain_Hz);
work.delta_gap34_gain_Hz = double(work.delta_gap34_gain_Hz);
work.positive_gain_rate = zeros(height(work), 1);

validSolve = work.solve_success_count > 0;
work.positive_gain_rate(validSolve) = work.positive_gain_count(validSolve) ./ work.solve_success_count(validSolve);

mask = strlength(work.seed_shape_id) > 0 & ...
    work.solve_success_count >= gate.minSolveSuccessCount & ...
    work.positive_gain_rate >= gate.minPositiveRate & ...
    isfinite(work.best_gap34_gain_Hz) & ...
    work.best_gap34_gain_Hz >= gate.minMeanGainHz;

work = work(mask, :);
if isempty(work)
    error('select_optimization_stage_seed_ids_v1:NoEligibleSeeds', ...
        'No stage survivors satisfy the refinement thresholds.');
end

work = sortrows(work, ...
    {'best_gap34_gain_Hz','delta_gap34_gain_Hz','positive_gain_rate','solve_success_count','seed_shape_id'}, ...
    {'descend','descend','descend','descend','ascend'});

limit = min(height(work), gate.topKSeeds);
seedIds = string(work.seed_shape_id(1:limit));
end
