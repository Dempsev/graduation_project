function run_comsol_in_loop_champion_local_v3(cfg)
%RUN_COMSOL_IN_LOOP_CHAMPION_LOCAL_V3
% Local trust-region style champion stage with predictor-guided prescreening.

if nargin < 1 || isempty(cfg)
    cfg = get_comsol_in_loop_ga_optimization_champion_local_config_v3();
end

ensure_parent_dir(cfg.stateMat);
save_config_json_local(cfg);

seedTable = readtable(cfg.seedScoredCsv);
seedTable = normalize_seed_table_local(seedTable);
seedTable = select_seed_rows_local(seedTable, cfg);
seedTable.selection_rank = transpose((1:height(seedTable)));
writetable(seedTable, cfg.seedSelectionCsv);

pointTable = build_unique_point_manifest_local(seedTable);
writetable(pointTable, cfg.seedPointManifestCsv);
baselineByPoint = evaluate_stage2_harmonics_refine_baseline_points(cfg, pointTable);

state = load_or_init_local_state(cfg, seedTable);

fprintf('COMSOL-in-loop champion local search v3\n');
fprintf('  ga_id=%s\n', cfg.gaId);
fprintf('  seed_scored_csv=%s\n', cfg.seedScoredCsv);
fprintf('  out_dir=%s\n', cfg.outDir);
fprintf('  seeds=%d, evals_per_iteration=%d, iterations_per_seed=%d\n', height(seedTable), cfg.evalsPerIteration, cfg.iterationsPerSeed);
fprintf('  active_params=%s\n', strjoin(cfg.activeParamNames, ','));

for seedIdx = 1:height(seedTable)
    seedRow = seedTable(seedIdx, :);
    refPoint = lookup_reference_point_local(baselineByPoint, string(seedRow.point_id(1)));

    while state.nextIterationBySeed(seedIdx) <= cfg.iterationsPerSeed
        iteration = state.nextIterationBySeed(seedIdx);
        fprintf('\nSeed [%d/%d] %s iteration [%d/%d]\n', ...
            seedIdx, height(seedTable), char(string(seedRow.shape_id(1))), iteration, cfg.iterationsPerSeed);

        if ~state.centers(seedIdx).initialized
            state.centers(seedIdx) = make_center_from_seed(seedRow, cfg);
            save_local_state(cfg, state);
        end

        if isempty(state.iterationPlans{seedIdx, iteration})
            state.iterationPlans{seedIdx, iteration} = create_iteration_plan(cfg, seedRow, state.centers(seedIdx), seedIdx, iteration);
            save_local_state(cfg, state);
        end

        planTable = state.iterationPlans{seedIdx, iteration};
        doneIndices = completed_indices_for_iteration_local(state.history, seedIdx, iteration);
        pending = setdiff(1:height(planTable), doneIndices, 'stable');

        for idx = pending
            candidate = planTable(idx, :);
            resultRow = evaluate_iteration_candidate(cfg, seedRow, candidate, refPoint, seedIdx, iteration, idx, state.centers(seedIdx));
            state.history = append_row_local(state.history, resultRow);
            save_local_state(cfg, state);

            fprintf(['    [%d/%d] %s fitness=%s geometry=%s contact=%s solve=%s ' ...
                     'gain=%s dist_center=%.4f\n'], ...
                idx, height(planTable), char(string(resultRow.sample_id)), ...
                numeric_text_local(resultRow.fitness), logical_text_local(resultRow.geometry_valid), ...
                logical_text_local(resultRow.contact_valid), logical_text_local(resultRow.solve_success), ...
                numeric_text_local(resultRow.gap34_gain_Hz), resultRow.distance_from_center);
            if strlength(string(resultRow.error_message)) > 0
                fprintf('      note=%s\n', char(string(resultRow.error_message)));
            end
        end

        iterationRowsTable = iteration_rows_local(state.history, seedIdx, iteration);
        summaryRow = make_iteration_summary_local(seedRow, iterationRowsTable, seedIdx, iteration);
        state.iterationSummaries = upsert_summary_row_local(state.iterationSummaries, summaryRow);
        state.centers(seedIdx) = update_center_state(cfg, state.centers(seedIdx), iterationRowsTable);

        state.nextIterationBySeed(seedIdx) = iteration + 1;
        save_local_state(cfg, state);
        write_local_exports(cfg, state, seedTable);
    end
end

write_local_exports(cfg, state, seedTable);
fprintf('\nCOMSOL-in-loop champion local v3 completed.\n');
fprintf('  history_csv=%s\n', cfg.historyCsv);
fprintf('  generation_summary_csv=%s\n', cfg.generationSummaryCsv);
fprintf('  search_summary_csv=%s\n', cfg.searchSummaryCsv);
fprintf('  best_candidates_csv=%s\n', cfg.bestCandidatesCsv);
end

function seedTable = normalize_seed_table_local(seedTable)
textVars = {'sample_id','source_stage','source_role','pool_arm','point_strategy','family_prior_source', ...
    'seed_prior_source','seed_shape_id','seed_family','seed_tier','seed_source','shape_id','shape_family', ...
    'shape_role','candidate_id','main_id','point_id','prev_best_sample_id'};
for i = 1:numel(textVars)
    name = textVars{i};
    if ismember(name, seedTable.Properties.VariableNames)
        seedTable.(name) = string(seedTable.(name));
    end
end
end

function seedTable = select_seed_rows_local(seedTable, cfg)
if strlength(string(cfg.seedPointId)) > 0 && ismember('point_id', seedTable.Properties.VariableNames)
    seedTable = seedTable(string(seedTable.point_id) == string(cfg.seedPointId), :);
end
if ~isempty(cfg.forceSeedShapeIds)
    seedTable = seedTable(ismember(string(seedTable.shape_id), string(cfg.forceSeedShapeIds)), :);
end
if isempty(seedTable)
    error('run_comsol_in_loop_champion_local_v3:NoSeedRows', 'No seed rows available after filtering.');
end
if ismember('prev_best_gap34_gain_Hz', seedTable.Properties.VariableNames)
    seedTable = sortrows(seedTable, {'prev_best_gap34_gain_Hz','shape_id'}, {'descend','ascend'});
elseif ismember('optimization_seed_score', seedTable.Properties.VariableNames)
    seedTable = sortrows(seedTable, {'optimization_seed_score','shape_id'}, {'descend','ascend'});
end
shapeMask = ~duplicated_strings_local(string(seedTable.shape_id));
seedTable = seedTable(shapeMask, :);
seedTable = seedTable(1:min(height(seedTable), cfg.topKSeeds), :);
end

function mask = duplicated_strings_local(values)
seen = strings(0, 1);
mask = false(size(values));
for i = 1:numel(values)
    if any(seen == values(i))
        mask(i) = true;
    else
        seen(end + 1, 1) = values(i); %#ok<AGROW>
    end
end
end

function pointTable = build_unique_point_manifest_local(seedTable)
mask = false(height(seedTable), 1);
seen = strings(0, 1);
for i = 1:height(seedTable)
    pointId = string(seedTable.point_id(i));
    if any(seen == pointId)
        continue;
    end
    seen(end + 1, 1) = pointId; %#ok<AGROW>
    mask(i) = true;
end
pointTable = table();
pointTable.main_id = seedTable.main_id(mask);
pointTable.point_id = seedTable.point_id(mask);
pointTable.a1 = pick_reference_column_local(seedTable, mask, 'a1');
pointTable.a2 = pick_reference_column_local(seedTable, mask, 'a2');
pointTable.b1 = pick_reference_column_local(seedTable, mask, 'b1');
pointTable.b2 = pick_reference_column_local(seedTable, mask, 'b2');
pointTable.r0 = pick_reference_column_local(seedTable, mask, 'r0');
pointTable.a3 = pick_reference_column_local(seedTable, mask, 'a3');
pointTable.b3 = pick_reference_column_local(seedTable, mask, 'b3');
pointTable.a4 = pick_reference_column_local(seedTable, mask, 'a4');
pointTable.b4 = pick_reference_column_local(seedTable, mask, 'b4');
pointTable.a5 = pick_reference_column_local(seedTable, mask, 'a5');
pointTable.b5 = pick_reference_column_local(seedTable, mask, 'b5');
end

function values = pick_reference_column_local(seedTable, mask, name)
refName = ['reference_' name];
if ismember(refName, seedTable.Properties.VariableNames)
    values = seedTable.(refName)(mask);
else
    values = seedTable.(name)(mask);
end
end

function state = load_or_init_local_state(cfg, seedTable)
if isfile(cfg.stateMat)
    loaded = load(cfg.stateMat, 'state', 'configSignature');
    if isfield(loaded, 'configSignature') && strcmp(string(loaded.configSignature), string(cfg.configSignature))
        state = loaded.state;
        if ~isequal(string(state.seedShapeIds(:)), string(seedTable.shape_id(:)))
            error('run_comsol_in_loop_champion_local_v3:SeedMismatch', ...
                'Existing local champion state was created with a different seed list. Remove %s to restart.', cfg.stateMat);
        end
        return;
    end
end

centerTemplate = make_empty_center();
state = struct();
state.seedShapeIds = string(seedTable.shape_id);
state.nextIterationBySeed = ones(height(seedTable), 1);
state.iterationPlans = cell(height(seedTable), cfg.iterationsPerSeed);
state.history = struct([]);
state.iterationSummaries = struct([]);
state.centers = repmat(centerTemplate, height(seedTable), 1);
save_local_state(cfg, state);
end

function center = make_empty_center()
center = struct();
center.initialized = false;
center.currentSampleId = "";
center.currentFitness = NaN;
center.currentGain = NaN;
center.stallCount = 0;
center.a1 = NaN; center.a2 = NaN; center.b1 = NaN; center.b2 = NaN;
center.a3 = NaN; center.b3 = NaN; center.a4 = NaN; center.b4 = NaN;
center.a5 = NaN; center.b5 = NaN; center.r0 = NaN;
center.radius_a1 = NaN; center.radius_a2 = NaN; center.radius_b1 = NaN; center.radius_b2 = NaN;
center.radius_a3 = NaN; center.radius_b3 = NaN; center.radius_a4 = NaN; center.radius_b4 = NaN;
center.radius_a5 = NaN; center.radius_b5 = NaN; center.radius_r0 = NaN;
end

function center = make_center_from_seed(seedRow, cfg)
center = make_empty_center();
center.initialized = true;
center.currentSampleId = string(get_text_or_default(seedRow, 'prev_best_sample_id', seedRow.sample_id(1)));
center.currentFitness = numeric_or_default(seedRow, 'prev_best_fitness', numeric_or_default(seedRow, 'prev_best_gap34_gain_Hz', 0.0));
center.currentGain = numeric_or_default(seedRow, 'prev_best_gap34_gain_Hz', center.currentFitness);
params = {'a1','a2','b1','b2','a3','b3','a4','b4','a5','b5','r0'};
for i = 1:numel(params)
    name = params{i};
    center.(name) = double(seedRow.(name)(1));
    center.(['radius_' name]) = cfg.localHalfWidths.(name);
end
end

function value = numeric_or_default(seedRow, fieldName, defaultValue)
if ismember(fieldName, seedRow.Properties.VariableNames)
    raw = seedRow.(fieldName)(1);
    value = double(raw);
    if ~isfinite(value)
        value = defaultValue;
    end
else
    value = defaultValue;
end
end

function value = get_text_or_default(seedRow, fieldName, defaultValue)
if ismember(fieldName, seedRow.Properties.VariableNames)
    value = string(seedRow.(fieldName)(1));
    if strlength(value) == 0
        value = string(defaultValue);
    end
else
    value = string(defaultValue);
end
end

function refPoint = lookup_reference_point_local(baselineByPoint, pointId)
ids = string({baselineByPoint.point_id});
idx = find(ids == string(pointId), 1, 'first');
if isempty(idx)
    error('run_comsol_in_loop_champion_local_v3:MissingRefPoint', 'Missing baseline reference for point %s.', pointId);
end
refPoint = baselineByPoint(idx);
end

function planTable = create_iteration_plan(cfg, seedRow, center, seedIdx, iteration)
proposals = generate_proposals_local(cfg, seedRow, center);
planFrame = proposals_to_seed_like_table(cfg, seedRow, proposals, center, seedIdx, iteration);
inputCsv = fullfile(cfg.prescreenInputDir, sprintf('seed_%02d_iter_%03d_candidates.csv', seedIdx, iteration));
outputCsv = fullfile(cfg.prescreenOutputDir, sprintf('seed_%02d_iter_%03d_scored.csv', seedIdx, iteration));
writetable(planFrame, inputCsv);
run_prescreen_local(cfg, inputCsv, outputCsv);
scored = readtable(outputCsv);
scored = normalize_seed_table_local(scored);
if ~ismember('prescreen_score', scored.Properties.VariableNames)
    error('run_comsol_in_loop_champion_local_v3:MissingPrescreenScore', 'Prescreen output missing prescreen_score: %s', outputCsv);
end
scored = sortrows(scored, {'prescreen_score','optimization_seed_score','contact_prob','positive_prob'}, {'descend','descend','descend','descend'});
keepN = min(height(scored), cfg.evalsPerIteration);
planTable = scored(1:keepN, :);
planTable.individual_index = transpose((1:keepN));
end

function proposals = generate_proposals_local(cfg, seedRow, center)
params = cfg.activeParamNames;
proposals = repmat(empty_proposal_struct_local(seedRow), 0, 1);
seen = containers.Map('KeyType', 'char', 'ValueType', 'logical');

for i = 1:numel(params)
    name = params{i};
    step = center.(['radius_' name]);
    if step <= 0
        continue;
    end
    proposals = add_proposal_local(proposals, seen, perturb_center(center, cfg, seedRow, name, step), 1.0);
    proposals = add_proposal_local(proposals, seen, perturb_center(center, cfg, seedRow, name, -step), 1.0);
    proposals = add_proposal_local(proposals, seen, perturb_center(center, cfg, seedRow, name, 0.5 * step), 0.5);
    proposals = add_proposal_local(proposals, seen, perturb_center(center, cfg, seedRow, name, -0.5 * step), 0.5);
end

rng(cfg.randomSeed + 10000 * double(sum(double(char(string(seedRow.shape_id(1)))))) + 97 * center.stallCount + numel(proposals), 'twister');
while numel(proposals) < cfg.proposalsPerIteration
    candidate = seed_gene_struct_local(seedRow);
    for i = 1:numel(params)
        name = params{i};
        step = center.(['radius_' name]);
        if step <= 0
            candidate.(name) = center.(name);
            continue;
        end
        if rand < 0.85
            value = center.(name) + randn * step * 0.85;
        else
            value = center.(name) + (2 * rand - 1) * step;
        end
        candidate.(name) = clip_to_basin_bounds_local(cfg, seedRow, name, value);
    end
    proposals = add_proposal_local(proposals, seen, candidate, 0.0);
end
end

function proposals = add_proposal_local(proposals, seen, candidate, directionBonus)
key = proposal_key_local(candidate);
if isKey(seen, key)
    return;
end
seen(key) = true;
candidate.direction_bonus = directionBonus;
proposals(end + 1) = candidate; %#ok<AGROW>
end

function candidate = perturb_center(center, cfg, seedRow, name, delta)
candidate = seed_gene_struct_local(seedRow);
params = fieldnames(candidate);
for i = 1:numel(params)
    field = params{i};
    if isfield(center, field)
        candidate.(field) = center.(field);
    end
end
candidate.(name) = clip_to_basin_bounds_local(cfg, seedRow, name, center.(name) + delta);
end

function key = proposal_key_local(candidate)
key = sprintf('%.8f|%.8f|%.8f|%.8f|%.8f|%.8f|%.8f|%.8f|%.8f|%.8f|%.8f', ...
    candidate.a1, candidate.a2, candidate.b1, candidate.b2, candidate.a3, candidate.b3, ...
    candidate.a4, candidate.b4, candidate.a5, candidate.b5, candidate.r0);
end

function candidate = empty_proposal_struct_local(seedRow)
candidate = seed_gene_struct_local(seedRow);
candidate.direction_bonus = 0.0;
end

function candidate = seed_gene_struct_local(seedRow)
candidate = struct();
params = {'a1','a2','b1','b2','a3','b3','a4','b4','a5','b5','r0'};
for i = 1:numel(params)
    name = params{i};
    candidate.(name) = double(seedRow.(name)(1));
end
end

function value = clip_to_basin_bounds_local(cfg, seedRow, name, value)
globalBounds = cfg.globalBounds.(name);
baseValue = double(seedRow.(name)(1));
basinHalfWidth = cfg.basinHalfWidths.(name);
lo = max(globalBounds(1), baseValue - basinHalfWidth);
hi = min(globalBounds(2), baseValue + basinHalfWidth);
value = min(max(value, lo), hi);
end

function planFrame = proposals_to_seed_like_table(cfg, seedRow, proposals, center, seedIdx, iteration)
planFrame = repmat(seedRow, numel(proposals), 1);
for i = 1:numel(proposals)
    proposal = proposals(i);
    params = {'a1','a2','b1','b2','a3','b3','a4','b4','a5','b5','r0'};
    for j = 1:numel(params)
        name = params{j};
        if ismember(name, planFrame.Properties.VariableNames)
            planFrame.(name)(i) = proposal.(name);
        end
    end
    planFrame.sample_id(i) = string(sprintf('%s__s%02d__it%03d__p%03d__%s', cfg.gaId, seedIdx, iteration, i, char(string(seedRow.shape_id(1)))));
    planFrame.candidate_id(i) = string(sprintf('local_s%02d_it%03d_p%03d', seedIdx, iteration, i));
    if ismember('pool_arm', planFrame.Properties.VariableNames)
        planFrame.pool_arm(i) = "champion_local_v3";
    end
    if ismember('point_strategy', planFrame.Properties.VariableNames)
        planFrame.point_strategy(i) = "local_trust_region_prescreen";
    end
    planFrame.current_best_gap34_gain_Hz(i) = center.currentGain;
    planFrame.current_best_fitness(i) = center.currentFitness;
    planFrame.direction_bonus(i) = proposal.direction_bonus;
    planFrame.distance_from_center(i) = normalized_distance_from_center_local(center, proposal, cfg);
end
end

function dist = normalized_distance_from_center_local(center, proposal, cfg)
parts = [];
for i = 1:numel(cfg.activeParamNames)
    name = cfg.activeParamNames{i};
    step = center.(['radius_' name]);
    if step <= 0
        continue;
    end
    parts(end + 1) = abs(proposal.(name) - center.(name)) / max(step, eps); %#ok<AGROW>
end
if isempty(parts)
    dist = 0.0;
else
    dist = mean(parts);
end
end

function run_prescreen_local(cfg, inputCsv, outputCsv)
cmd = sprintf('%s "%s" --input-csv "%s" --output-csv "%s"', ...
    cfg.prescreenPython, cfg.prescreenScript, inputCsv, outputCsv);
[status, cmdout] = system(cmd);
if status ~= 0
    error('run_comsol_in_loop_champion_local_v3:PrescreenFailed', ...
        'Prescreen command failed (%d): %s', status, cmdout);
end
end

function resultRow = evaluate_iteration_candidate(cfg, seedRow, candidate, refPoint, seedIdx, iteration, individualIdx, center)
pointSpec = point_spec_from_candidate_local(seedRow, candidate);
sampleMeta = sample_meta_from_candidate_local(cfg, seedRow, candidate, seedIdx, iteration, individualIdx);
result = evaluate_stage2_harmonics_refine_case_internal(cfg, sampleMeta, pointSpec, refPoint);

resultRow = result;
resultRow.seed_index = seedIdx;
resultRow.seed_rank = double(seedRow.selection_rank(1));
resultRow.seed_shape_id = string(seedRow.shape_id(1));
resultRow.seed_family = string(seedRow.shape_family(1));
resultRow.seed_candidate_id = string(seedRow.candidate_id(1));
resultRow.seed_source_sample_id = string(seedRow.sample_id(1));
resultRow.generation = iteration;
resultRow.individual_index = individualIdx;
resultRow.b1 = double(candidate.b1(1));
resultRow.base_a1 = center.a1;
resultRow.base_a2 = center.a2;
resultRow.base_b1 = center.b1;
resultRow.base_b2 = center.b2;
resultRow.base_a3 = center.a3;
resultRow.base_b3 = center.b3;
resultRow.base_a4 = center.a4;
resultRow.base_b4 = center.b4;
resultRow.base_a5 = center.a5;
resultRow.base_b5 = center.b5;
resultRow.base_r0 = center.r0;
resultRow.base_cascade_score = numeric_or_nan_from_seed_local(candidate, 'cascade_score');
resultRow.base_contact_prob = numeric_or_nan_from_seed_local(candidate, 'contact_prob');
resultRow.base_positive_prob = numeric_or_nan_from_seed_local(candidate, 'positive_prob');
resultRow.base_surrogate_pred_gap34_gain_Hz = numeric_or_nan_from_seed_local(candidate, 'surrogate_pred_gap34_gain_Hz');
resultRow.prescreen_score = numeric_or_nan_from_seed_local(candidate, 'prescreen_score');
resultRow.distance_from_center = numeric_or_nan_from_seed_local(candidate, 'distance_from_center');
resultRow.direction_bonus = numeric_or_nan_from_seed_local(candidate, 'direction_bonus');
resultRow.fitness = compute_fitness_local(cfg, resultRow);
end

function value = numeric_or_nan_from_seed_local(seedRow, fieldName)
if ismember(fieldName, seedRow.Properties.VariableNames)
    value = double(seedRow.(fieldName)(1));
else
    value = NaN;
end
end

function pointSpec = point_spec_from_candidate_local(seedRow, candidate)
pointSpec = struct( ...
    'main_id', char(string(seedRow.main_id(1))), ...
    'point_id', char(string(seedRow.point_id(1))), ...
    'a1', double(candidate.a1(1)), 'a2', double(candidate.a2(1)), 'b1', double(candidate.b1(1)), 'b2', double(candidate.b2(1)), 'r0', double(candidate.r0(1)), ...
    'a3', double(candidate.a3(1)), 'b3', double(candidate.b3(1)), 'a4', double(candidate.a4(1)), 'b4', double(candidate.b4(1)), ...
    'a5', double(candidate.a5(1)), 'b5', double(candidate.b5(1)) ...
);
end

function sampleMeta = sample_meta_from_candidate_local(cfg, seedRow, candidate, seedIdx, iteration, individualIdx)
shapeId = char(string(seedRow.shape_id(1)));
sampleMeta = struct( ...
    'sample_id', string(sanitize_id_local(sprintf('%s__s%02d__it%03d__i%03d__%s', cfg.gaId, seedIdx, iteration, individualIdx, shapeId))), ...
    'candidate_id', string(candidate.candidate_id(1)), ...
    'shape_id', string(shapeId), ...
    'shape_family', string(seedRow.shape_family(1)), ...
    'shape_role', string(seedRow.shape_role(1)), ...
    'shape_file', string(fullfile(cfg.shapeDir, [shapeId '.csv'])) ...
);
end

function fitness = compute_fitness_local(cfg, row)
if ~row.geometry_valid
    fitness = cfg.failurePenaltyGeometry;
    return;
end
if ~row.contact_valid
    fitness = cfg.failurePenaltyContact;
    return;
end
if ~row.solve_success || ~isfinite(row.gap34_gain_Hz)
    fitness = cfg.failurePenaltySolve;
    return;
end
fitness = row.gap34_gain_Hz - 0.10 * row.distance_from_center;
end

function rows = iteration_rows_local(history, seedIdx, iteration)
if isempty(history)
    rows = table();
    return;
end
mask = [history.seed_index] == seedIdx & [history.generation] == iteration;
subset = history(mask);
if isempty(subset)
    rows = table();
    return;
end
rows = struct2table(subset, 'AsArray', true);
end

function completed = completed_indices_for_iteration_local(history, seedIdx, iteration)
completed = [];
if isempty(history)
    return;
end
mask = [history.seed_index] == seedIdx & [history.generation] == iteration;
if any(mask)
    completed = [history(mask).individual_index];
end
end

function summary = make_iteration_summary_local(seedRow, rows, seedIdx, iteration)
summary = struct();
summary.seed_index = seedIdx;
summary.seed_shape_id = string(seedRow.shape_id(1));
summary.seed_family = string(seedRow.shape_family(1));
summary.generation = iteration;
summary.population_size = height(rows);
summary.solve_success_count = sum(rows.solve_success);
summary.positive_gain_count = sum(rows.solve_success & rows.gap34_gain_Hz > 0);
summary.best_fitness = max(rows.fitness);
summary.mean_fitness = mean(rows.fitness);
bestRow = sortrows(rows, {'fitness','gap34_gain_Hz'}, {'descend','descend'});
bestRow = bestRow(1, :);
summary.best_sample_id = string(bestRow.sample_id(1));
summary.best_gap34_gain_Hz = bestRow.gap34_gain_Hz(1);
summary.best_gap34_Hz = bestRow.gap34_Hz(1);
summary.best_distance_from_seed = bestRow.distance_from_center(1);
summary.best_a1 = bestRow.a1(1);
summary.best_a2 = bestRow.a2(1);
summary.best_b2 = bestRow.b2(1);
summary.best_a4 = bestRow.a4(1);
summary.best_b5 = bestRow.b5(1);
summary.best_r0 = bestRow.r0(1);
end

function summaries = upsert_summary_row_local(summaries, row)
if isempty(summaries)
    summaries = row;
    return;
end
mask = arrayfun(@(s) s.seed_index == row.seed_index && s.generation == row.generation, summaries);
if any(mask)
    summaries(find(mask, 1, 'first')) = row;
else
    summaries(end + 1) = row; %#ok<AGROW>
end
end

function center = update_center_state(cfg, center, rows)
if isempty(rows)
    return;
end
rows = sortrows(rows, {'fitness','gap34_gain_Hz'}, {'descend','descend'});
bestRow = rows(1, :);
if bestRow.fitness(1) > center.currentFitness + cfg.minImprovementHz
    params = {'a1','a2','b1','b2','a3','b3','a4','b4','a5','b5','r0'};
    for i = 1:numel(params)
        name = params{i};
        center.(name) = bestRow.(name)(1);
        radiusName = ['radius_' name];
        center.(radiusName) = min(cfg.basinHalfWidths.(name), center.(radiusName) * cfg.expandFactor);
    end
    center.currentSampleId = string(bestRow.sample_id(1));
    center.currentFitness = bestRow.fitness(1);
    center.currentGain = bestRow.gap34_gain_Hz(1);
    center.stallCount = 0;
else
    params = {'a1','a2','b1','b2','a3','b3','a4','b4','a5','b5','r0'};
    for i = 1:numel(params)
        name = params{i};
        radiusName = ['radius_' name];
        center.(radiusName) = max(cfg.localHalfWidths.(name) * 0.35, center.(radiusName) * cfg.shrinkFactor);
    end
    center.stallCount = center.stallCount + 1;
    if mod(center.stallCount, cfg.stallIterationsBeforeReexpand) == 0
        for i = 1:numel(params)
            name = params{i};
            radiusName = ['radius_' name];
            center.(radiusName) = min(cfg.basinHalfWidths.(name), center.(radiusName) * cfg.reexpandFactor);
        end
    end
end
end

function save_local_state(cfg, state)
configSignature = cfg.configSignature; %#ok<NASGU>
save(cfg.stateMat, 'state', 'configSignature');
end

function write_local_exports(cfg, state, seedTable)
write_local_history_table(cfg, state.history);
write_local_generation_summary_table(cfg, state.iterationSummaries);
write_local_search_summary_table(cfg, state.history, seedTable);
write_local_best_candidates_table(cfg, state.history, seedTable);
end

function write_local_history_table(cfg, history)
if isempty(history)
    writetable(table(), cfg.historyCsv);
    return;
end
tbl = struct2table(history, 'AsArray', true);
writetable(tbl, cfg.historyCsv);
end

function write_local_generation_summary_table(cfg, generationSummaries)
if isempty(generationSummaries)
    writetable(table(), cfg.generationSummaryCsv);
    return;
end
tbl = struct2table(generationSummaries, 'AsArray', true);
writetable(tbl, cfg.generationSummaryCsv);
end

function write_local_search_summary_table(cfg, history, seedTable)
if isempty(history)
    writetable(table(), cfg.searchSummaryCsv);
    return;
end
historyTable = struct2table(history, 'AsArray', true);
rows = struct([]);
for seedIdx = 1:height(seedTable)
    sub = historyTable(historyTable.seed_index == seedIdx, :);
    if isempty(sub)
        continue;
    end
    sub = sortrows(sub, {'fitness','gap34_gain_Hz'}, {'descend','descend'});
    stageBest = sub(1, :);
    baseFitness = numeric_or_default(seedTable(seedIdx, :), 'prev_best_fitness', numeric_or_default(seedTable(seedIdx, :), 'prev_best_gap34_gain_Hz', NaN));
    baseGain = numeric_or_default(seedTable(seedIdx, :), 'prev_best_gap34_gain_Hz', baseFitness);
    if isfinite(baseFitness) && baseFitness >= stageBest.fitness(1)
        bestSampleId = string(get_text_or_default(seedTable(seedIdx, :), 'prev_best_sample_id', ""));
        bestFitness = baseFitness;
        bestGain = baseGain;
        bestGeneration = 0;
        bestIndividualIndex = 0;
        bestA1 = seedTable.a1(seedIdx); bestA2 = seedTable.a2(seedIdx); bestB2 = seedTable.b2(seedIdx);
        bestA4 = seedTable.a4(seedIdx); bestB5 = seedTable.b5(seedIdx); bestR0 = seedTable.r0(seedIdx);
    else
        bestSampleId = string(stageBest.sample_id(1));
        bestFitness = stageBest.fitness(1);
        bestGain = stageBest.gap34_gain_Hz(1);
        bestGeneration = stageBest.generation(1);
        bestIndividualIndex = stageBest.individual_index(1);
        bestA1 = stageBest.a1(1); bestA2 = stageBest.a2(1); bestB2 = stageBest.b2(1);
        bestA4 = stageBest.a4(1); bestB5 = stageBest.b5(1); bestR0 = stageBest.r0(1);
    end
    row = struct( ...
        'seed_index', seedIdx, ...
        'seed_shape_id', string(seedTable.shape_id(seedIdx)), ...
        'seed_family', string(seedTable.shape_family(seedIdx)), ...
        'base_sample_id', string(get_text_or_default(seedTable(seedIdx, :), 'prev_best_sample_id', "")), ...
        'best_sample_id', bestSampleId, ...
        'base_fitness', baseFitness, ...
        'best_fitness', bestFitness, ...
        'delta_fitness', bestFitness - baseFitness, ...
        'base_gap34_gain_Hz', baseGain, ...
        'best_gap34_gain_Hz', bestGain, ...
        'delta_gap34_gain_Hz', bestGain - baseGain, ...
        'best_generation', bestGeneration, ...
        'best_individual_index', bestIndividualIndex, ...
        'best_a1', bestA1, 'best_a2', bestA2, 'best_b2', bestB2, ...
        'best_a4', bestA4, 'best_b5', bestB5, 'best_r0', bestR0, ...
        'solve_success_count', sum(sub.solve_success), ...
        'positive_gain_count', sum(sub.solve_success & sub.gap34_gain_Hz > 0) ...
    );
    rows = append_row_local(rows, row);
end
if isempty(rows)
    writetable(table(), cfg.searchSummaryCsv);
else
    writetable(struct2table(rows, 'AsArray', true), cfg.searchSummaryCsv);
end
end

function write_local_best_candidates_table(cfg, history, seedTable)
if isempty(history)
    writetable(table(), cfg.bestCandidatesCsv);
    return;
end
historyTable = struct2table(history, 'AsArray', true);
rows = struct([]);
for seedIdx = 1:height(seedTable)
    sub = historyTable(historyTable.seed_index == seedIdx, :);
    if isempty(sub)
        continue;
    end
    sub = sortrows(sub, {'fitness','gap34_gain_Hz'}, {'descend','descend'});
    keepN = min(height(sub), cfg.topCandidatesPerSeedExport);
    for i = 1:keepN
        rows = append_row_local(rows, table2struct(sub(i, :))); %#ok<AGROW>
    end
end
if isempty(rows)
    writetable(table(), cfg.bestCandidatesCsv);
else
    writetable(struct2table(rows, 'AsArray', true), cfg.bestCandidatesCsv);
end
end

function s = sanitize_id_local(s)
s = regexprep(char(string(s)), '[^A-Za-z0-9_.-]+', '_');
end

function value = logical_text_local(raw)
if raw
    value = 'true';
else
    value = 'false';
end
end

function value = numeric_text_local(raw)
if ~isfinite(raw)
    value = 'NaN';
else
    value = num2str(raw, '%.6g');
end
end

function rows = append_row_local(rows, row)
if isempty(rows)
    rows = row;
else
    rows(end + 1) = row; %#ok<AGROW>
end
end

function ensure_parent_dir(pathStr)
parentDir = fileparts(pathStr);
if ~exist(parentDir, 'dir')
    mkdir(parentDir);
end
end

function save_config_json_local(cfg)
try
    payload = struct();
    fields = {'gaId','seedScoredCsv','seedPointId','seedWhitelistJson','topKSeeds','searchBoundsMode','populationSize','generations', ...
        'eliteCount','distancePenaltyWeight','randomSeed','topCandidatesPerSeedExport','failurePenaltyGeometry','failurePenaltyContact', ...
        'failurePenaltySolve','paramNames','activeParamNames','globalBounds','localHalfWidths','materialCase','fixedGapBand', ...
        'configSignature','totalEvalBudget','evalsPerIteration','proposalsPerIteration','iterationsPerSeed','minImprovementHz', ...
        'expandFactor','shrinkFactor','reexpandFactor','stallIterationsBeforeReexpand','basinHalfWidths','prescreenPython','prescreenScript'};
    for i = 1:numel(fields)
        name = fields{i};
        payload.(name) = cfg.(name);
    end
    fid = fopen(cfg.configJson, 'w');
    cleaner = onCleanup(@() fclose(fid));
    fwrite(fid, jsonencode(payload, 'PrettyPrint', true), 'char');
    clear cleaner;
catch
end
end
