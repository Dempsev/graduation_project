function seedIds = select_optimization_stage_seed_ids_v2(summaryCsv, gate)
%SELECT_OPTIMIZATION_STAGE_SEED_IDS_V2
% Stage survivor selector with two robustness features:
% 1) wildcard retention when the next basin is still within a competitive band
% 2) near-tie promotion so the top-1 stage can keep two basins alive

if nargin < 2 || isempty(gate)
    gate = struct();
end

gate = normalize_gate(gate);
work = load_stage_search_summary(summaryCsv, gate);
survivorIdx = select_survivor_indices(work, gate);
seedIds = string(work.seed_shape_id(survivorIdx));
end

function gate = normalize_gate(gate)
if ~isfield(gate, 'topKSeeds') || isempty(gate.topKSeeds)
    gate.topKSeeds = 1;
end
if ~isfield(gate, 'minMeanGainHz') || isempty(gate.minMeanGainHz)
    gate.minMeanGainHz = 0.0;
end
if ~isfield(gate, 'minPositiveRate') || isempty(gate.minPositiveRate)
    gate.minPositiveRate = 0.0;
end
if ~isfield(gate, 'minSolveSuccessCount') || isempty(gate.minSolveSuccessCount)
    gate.minSolveSuccessCount = 1;
end
if ~isfield(gate, 'wildcardMaxCount') || isempty(gate.wildcardMaxCount)
    gate.wildcardMaxCount = 0;
end
if ~isfield(gate, 'wildcardReferenceRank') || isempty(gate.wildcardReferenceRank)
    gate.wildcardReferenceRank = gate.topKSeeds;
end
if ~isfield(gate, 'wildcardGapHz') || isempty(gate.wildcardGapHz)
    gate.wildcardGapHz = inf;
end
if ~isfield(gate, 'wildcardGapRel') || isempty(gate.wildcardGapRel)
    gate.wildcardGapRel = inf;
end
if ~isfield(gate, 'enableNearTiePromotion') || isempty(gate.enableNearTiePromotion)
    gate.enableNearTiePromotion = false;
end
if ~isfield(gate, 'nearTieKeepCount') || isempty(gate.nearTieKeepCount)
    gate.nearTieKeepCount = 2;
end
if ~isfield(gate, 'nearTieGapHz') || isempty(gate.nearTieGapHz)
    gate.nearTieGapHz = 0.5;
end
if ~isfield(gate, 'nearTieGapRel') || isempty(gate.nearTieGapRel)
    gate.nearTieGapRel = 0.02;
end
end

function work = load_stage_search_summary(summaryCsv, gate)
if isfile(summaryCsv)
    work = try_load_supported_summary(summaryCsv, gate);
    return;
end

[summaryDir, ~, ~] = fileparts(summaryCsv);
fallbackSearchSummary = fullfile(summaryDir, 'ga_search_summary_v1.csv');
if isfile(fallbackSearchSummary)
    work = load_search_summary_table(fallbackSearchSummary, gate);
    return;
end

error('select_optimization_stage_seed_ids_v2:MissingSummary', ...
    'Neither stage summary nor fallback search summary exists: %s', summaryCsv);
end

function work = try_load_supported_summary(summaryCsv, gate)
tbl = readtable(summaryCsv);
vars = tbl.Properties.VariableNames;

if ismember('seed_shape_id', vars) && ismember('best_gap34_gain_Hz', vars)
    work = load_search_summary_table(summaryCsv, gate);
    return;
end

if ismember('shape_id', vars) && ismember('mean_gap34_gain_Hz', vars)
    error('select_optimization_stage_seed_ids_v2:ShapeSummaryUnsupported', ...
        ['Shape-level summary selection is not supported in v2 because the adaptive ', ...
         'wildcard and tie rules require per-seed best/delta metrics.']);
end

error('select_optimization_stage_seed_ids_v2:UnsupportedSummary', ...
    'Unsupported stage summary format: %s', summaryCsv);
end

function work = load_search_summary_table(searchSummaryCsv, gate)
tbl = readtable(searchSummaryCsv);
required = {'seed_shape_id','solve_success_count','positive_gain_count','best_gap34_gain_Hz','delta_gap34_gain_Hz'};
missing = setdiff(required, tbl.Properties.VariableNames, 'stable');
if ~isempty(missing)
    error('select_optimization_stage_seed_ids_v2:MissingColumns', ...
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
    error('select_optimization_stage_seed_ids_v2:NoEligibleSeeds', ...
        'No stage survivors satisfy the refinement thresholds.');
end

% Score stable high-performing basins above one-off spikes.
work.top3_proxy = work.best_gap34_gain_Hz - max(0, 0.35 * abs(work.delta_gap34_gain_Hz));
work.composite_score = ...
    0.50 * work.best_gap34_gain_Hz + ...
    0.30 * work.top3_proxy + ...
    0.20 * (work.best_gap34_gain_Hz - work.delta_gap34_gain_Hz);

work = sortrows(work, ...
    {'composite_score','best_gap34_gain_Hz','delta_gap34_gain_Hz','positive_gain_rate','solve_success_count','seed_shape_id'}, ...
    {'descend','descend','descend','descend','descend','ascend'});
end

function survivorIdx = select_survivor_indices(work, gate)
baseCount = min(height(work), gate.topKSeeds);
survivorIdx = transpose(1:baseCount);

if gate.enableNearTiePromotion && gate.topKSeeds == 1 && height(work) >= 2
    if within_competitive_band(work.best_gap34_gain_Hz(1), work.best_gap34_gain_Hz(2), ...
            gate.nearTieGapHz, gate.nearTieGapRel)
        survivorIdx = transpose(1:min(height(work), gate.nearTieKeepCount));
    end
end

if gate.wildcardMaxCount > 0 && height(work) > baseCount
    referenceRank = min(max(1, gate.wildcardReferenceRank), height(work));
    referenceValue = double(work.best_gap34_gain_Hz(referenceRank));
    added = 0;
    for idx = baseCount + 1:height(work)
        candidateValue = double(work.best_gap34_gain_Hz(idx));
        if within_competitive_band(referenceValue, candidateValue, gate.wildcardGapHz, gate.wildcardGapRel)
            survivorIdx(end + 1, 1) = idx; %#ok<AGROW>
            added = added + 1;
            if added >= gate.wildcardMaxCount
                break;
            end
        end
    end
end
end

function tf = within_competitive_band(referenceValue, candidateValue, gapHz, gapRel)
gap = max(0, double(referenceValue) - double(candidateValue));
denom = max(abs(double(referenceValue)), eps);
relGap = gap / denom;
tf = gap <= gapHz || relGap <= gapRel;
end
