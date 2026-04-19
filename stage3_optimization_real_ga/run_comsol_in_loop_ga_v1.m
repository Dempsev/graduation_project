function run_comsol_in_loop_ga_v1(cfg)
%RUN_COMSOL_IN_LOOP_GA_V1 Direct COMSOL-in-the-loop GA on shortlisted seeds.

if nargin < 1 || isempty(cfg)
    cfg = get_comsol_in_loop_ga_config_v1();
end

ensure_parent_dir(cfg.stateMat);
save_config_json(cfg);

seedTable = readtable(cfg.seedScoredCsv);
seedTable = normalize_seed_table(seedTable);
seedTable = select_seed_rows(seedTable, cfg);
seedTable.selection_rank = transpose((1:height(seedTable)));
writetable(seedTable, cfg.seedSelectionCsv);

pointTable = build_unique_point_manifest(seedTable);
writetable(pointTable, cfg.seedPointManifestCsv);
baselineByPoint = evaluate_stage2_harmonics_refine_baseline_points(cfg, pointTable);

state = load_or_init_state(cfg, seedTable);

fprintf('COMSOL-in-loop GA run\n');
fprintf('  ga_id=%s\n', cfg.gaId);
fprintf('  seed_scored_csv=%s\n', cfg.seedScoredCsv);
fprintf('  out_dir=%s\n', cfg.outDir);
fprintf('  seeds=%d, population=%d, generations=%d\n', height(seedTable), cfg.populationSize, cfg.generations);
fprintf('  active_params=%s\n', strjoin(cfg.activeParamNames, ','));
fprintf('  search_bounds_mode=%s\n', char(string(cfg.searchBoundsMode)));

for seedIdx = 1:height(seedTable)
    seedRow = seedTable(seedIdx, :);
    refPoint = lookup_reference_point(baselineByPoint, string(seedRow.point_id(1)));

    while state.nextGenerationBySeed(seedIdx) <= cfg.generations
        generation = state.nextGenerationBySeed(seedIdx);
        fprintf('\nSeed [%d/%d] %s generation [%d/%d]\n', ...
            seedIdx, height(seedTable), char(string(seedRow.shape_id(1))), generation, cfg.generations);

        if isempty(state.populations{seedIdx, generation})
            if generation == 1
                state.populations{seedIdx, generation} = create_initial_population(cfg, seedRow, seedIdx, generation);
            else
                previousRows = generation_rows(state.history, seedIdx, generation - 1);
                state.populations{seedIdx, generation} = breed_next_population(cfg, seedRow, previousRows, seedIdx, generation);
            end
            save_state(cfg, state);
        end

        popTable = state.populations{seedIdx, generation};
        doneIndices = completed_indices_for_generation(state.history, seedIdx, generation);
        pending = setdiff(1:height(popTable), doneIndices, 'stable');

        for idx = pending
            candidate = popTable(idx, :);
            resultRow = evaluate_individual(cfg, seedRow, candidate, refPoint, seedIdx, generation, idx);
            state.history = append_row(state.history, resultRow);
            save_state(cfg, state);

            fprintf(['    [%d/%d] %s fitness=%s geometry=%s contact=%s solve=%s ' ...
                     'gain=%s dist=%.4f\n'], ...
                idx, height(popTable), char(string(resultRow.sample_id)), ...
                numeric_text(resultRow.fitness), logical_text(resultRow.geometry_valid), ...
                logical_text(resultRow.contact_valid), logical_text(resultRow.solve_success), ...
                numeric_text(resultRow.gap34_gain_Hz), resultRow.distance_from_seed);
            if strlength(string(resultRow.error_message)) > 0
                fprintf('      note=%s\n', char(string(resultRow.error_message)));
            end
        end

        generationRowsTable = generation_rows(state.history, seedIdx, generation);
        summaryRow = make_generation_summary(seedRow, generationRowsTable, seedIdx, generation);
        state.generationSummaries = upsert_summary_row(state.generationSummaries, summaryRow);

        if generation < cfg.generations
            state.populations{seedIdx, generation + 1} = breed_next_population(cfg, seedRow, generationRowsTable, seedIdx, generation + 1);
        end

        state.nextGenerationBySeed(seedIdx) = generation + 1;
        save_state(cfg, state);
        write_exports(cfg, state, seedTable);
    end
end

write_exports(cfg, state, seedTable);
fprintf('\nCOMSOL-in-loop GA completed.\n');
fprintf('  history_csv=%s\n', cfg.historyCsv);
fprintf('  generation_summary_csv=%s\n', cfg.generationSummaryCsv);
fprintf('  search_summary_csv=%s\n', cfg.searchSummaryCsv);
fprintf('  best_candidates_csv=%s\n', cfg.bestCandidatesCsv);
end

function seedTable = normalize_seed_table(seedTable)
textVars = {'sample_id','source_stage','source_role','pool_arm','point_strategy','family_prior_source', ...
    'seed_prior_source','seed_shape_id','seed_family','seed_tier','seed_source','shape_id','shape_family', ...
    'shape_role','candidate_id','main_id','point_id'};
for i = 1:numel(textVars)
    name = textVars{i};
    if ismember(name, seedTable.Properties.VariableNames)
        seedTable.(name) = string(seedTable.(name));
    end
end
end

function seedTable = select_seed_rows(seedTable, cfg)
if strlength(string(cfg.seedPointId)) > 0
    seedTable = seedTable(string(seedTable.point_id) == string(cfg.seedPointId), :);
end

whitelistIds = load_enabled_shape_ids(cfg.seedWhitelistJson);
if ~isempty(cfg.forceSeedShapeIds)
    whitelistIds = unique([whitelistIds(:); string(cfg.forceSeedShapeIds(:))], 'stable');
end
if ~isempty(whitelistIds)
    seedTable = seedTable(ismember(string(seedTable.shape_id), whitelistIds), :);
end
if isempty(seedTable)
    error('run_comsol_in_loop_ga_v1:NoSeedRows', 'No seed rows available after point/whitelist filtering.');
end

sortFields = cellstr(string(cfg.seedSortFields));
sortDirections = cellstr(string(cfg.seedSortDirections));
if numel(sortFields) ~= numel(sortDirections)
    error('run_comsol_in_loop_ga_v1:InvalidSeedSortConfig', ...
        'seedSortFields and seedSortDirections must have the same length.');
end
missingFields = setdiff(sortFields, seedTable.Properties.VariableNames, 'stable');
if ~isempty(missingFields)
    error('run_comsol_in_loop_ga_v1:MissingSeedSortFields', ...
        'Seed scored csv missing sort fields: %s', strjoin(missingFields, ', '));
end

seedTable = sortrows(seedTable, sortFields, sortDirections);
shapeMask = ~duplicated_strings(string(seedTable.shape_id));
seedTable = seedTable(shapeMask, :);
seedTable = seedTable(1:min(height(seedTable), cfg.topKSeeds), :);
end

function ids = load_enabled_shape_ids(pathStr)
ids = strings(0, 1);
if isempty(pathStr) || ~isfile(pathStr)
    return;
end
payload = jsondecode(fileread(pathStr));
if isfield(payload, 'enabled_shape_ids')
    ids = string(payload.enabled_shape_ids(:));
end
ids = ids(strlength(ids) > 0);
end

function mask = duplicated_strings(values)
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

function pointTable = build_unique_point_manifest(seedTable)
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
pointTable.a1 = pick_reference_column(seedTable, mask, 'a1');
pointTable.a2 = pick_reference_column(seedTable, mask, 'a2');
pointTable.b1 = pick_reference_column(seedTable, mask, 'b1');
pointTable.b2 = pick_reference_column(seedTable, mask, 'b2');
pointTable.r0 = pick_reference_column(seedTable, mask, 'r0');
pointTable.a3 = pick_reference_column(seedTable, mask, 'a3');
pointTable.b3 = pick_reference_column(seedTable, mask, 'b3');
pointTable.a4 = pick_reference_column(seedTable, mask, 'a4');
pointTable.b4 = pick_reference_column(seedTable, mask, 'b4');
pointTable.a5 = pick_reference_column(seedTable, mask, 'a5');
pointTable.b5 = pick_reference_column(seedTable, mask, 'b5');
end

function state = load_or_init_state(cfg, seedTable)
if isfile(cfg.stateMat)
    loaded = load(cfg.stateMat, 'state', 'configSignature');
    if isfield(loaded, 'configSignature') && strcmp(string(loaded.configSignature), string(cfg.configSignature))
        state = loaded.state;
        if ~isfield(state, 'generationSummaries')
            state.generationSummaries = struct([]);
        end
        if ~isequal(string(state.seedShapeIds(:)), string(seedTable.shape_id(:)))
            error('run_comsol_in_loop_ga_v1:SeedMismatch', ...
                'Existing GA state was created with a different seed list. Remove %s to restart.', cfg.stateMat);
        end
        return;
    end
end

state = struct();
state.seedShapeIds = string(seedTable.shape_id);
state.nextGenerationBySeed = ones(height(seedTable), 1);
state.populations = cell(height(seedTable), cfg.generations);
state.history = struct([]);
state.generationSummaries = struct([]);
save_state(cfg, state);
end

function population = create_initial_population(cfg, seedRow, seedIdx, generation)
rng(cfg.randomSeed + seedIdx * 1000 + generation, 'twister');
population = repmat(seed_gene_row(seedRow), cfg.populationSize, 1);
population.individual_index = transpose((1:cfg.populationSize));

for i = 2:cfg.populationSize
    for j = 1:numel(cfg.activeParamNames)
        name = cfg.activeParamNames{j};
        bounds = search_bounds_for_param(cfg, seedRow, name);
        baseValue = double(seedRow.(name)(1));
        if bounds(1) == bounds(2)
            population.(name)(i) = baseValue;
            continue;
        end
        if strcmpi(string(cfg.searchBoundsMode), "global")
            value = bounds(1) + rand * (bounds(2) - bounds(1));
        elseif rand < 0.85
            span = bounds(2) - bounds(1);
            value = baseValue + randn * span * 0.18;
        else
            value = bounds(1) + rand * (bounds(2) - bounds(1));
        end
        population.(name)(i) = clip_to_bounds(value, bounds);
    end
end
end

function population = breed_next_population(cfg, seedRow, previousRows, seedIdx, generation)
rng(cfg.randomSeed + seedIdx * 1000 + generation, 'twister');
sortedRows = sortrows(previousRows, {'fitness','gap34_gain_Hz','solve_success','contact_valid','geometry_valid'}, ...
    {'descend','descend','descend','descend','descend'});

population = repmat(seed_gene_row(seedRow), cfg.populationSize, 1);
population.individual_index = transpose((1:cfg.populationSize));

eliteCount = min(cfg.eliteCount, height(sortedRows));
for i = 1:eliteCount
    population{i, cfg.paramNames} = sortedRows{i, cfg.paramNames};
end

for i = eliteCount + 1:cfg.populationSize
    parentA = tournament_pick(sortedRows);
    parentB = tournament_pick(sortedRows);
    for j = 1:numel(cfg.paramNames)
        name = cfg.paramNames{j};
        if ~ismember(name, cfg.activeParamNames)
            population.(name)(i) = double(seedRow.(name)(1));
            continue;
        end
        bounds = search_bounds_for_param(cfg, seedRow, name);
        alpha = rand;
        value = alpha * double(parentA.(name)(1)) + (1 - alpha) * double(parentB.(name)(1));
        if rand <= cfg.mutationRate && bounds(1) < bounds(2)
            span = bounds(2) - bounds(1);
            value = value + randn * span * cfg.mutationScale;
        end
        population.(name)(i) = clip_to_bounds(value, bounds);
    end
end
end

function row = tournament_pick(sortedRows)
if height(sortedRows) == 1
    row = sortedRows(1, :);
    return;
end
idx = randperm(height(sortedRows), min(3, height(sortedRows)));
subset = sortedRows(idx, :);
subset = sortrows(subset, {'fitness','gap34_gain_Hz'}, {'descend','descend'});
row = subset(1, :);
end

function resultRow = evaluate_individual(cfg, seedRow, candidate, refPoint, seedIdx, generation, individualIdx)
pointSpec = point_spec_from_candidate(seedRow, candidate);
sampleMeta = sample_meta_from_seed(cfg, seedRow, seedIdx, generation, individualIdx);
result = evaluate_stage2_harmonics_refine_case_internal(cfg, sampleMeta, pointSpec, refPoint);

resultRow = result;
resultRow.seed_index = seedIdx;
resultRow.seed_rank = double(seedRow.selection_rank(1));
resultRow.seed_shape_id = string(seedRow.shape_id(1));
resultRow.seed_family = string(seedRow.shape_family(1));
resultRow.seed_candidate_id = string(seedRow.candidate_id(1));
resultRow.seed_source_sample_id = string(seedRow.sample_id(1));
resultRow.generation = generation;
resultRow.individual_index = individualIdx;
resultRow.b1 = double(candidate.b1(1));
resultRow.base_a1 = double(seedRow.a1(1));
resultRow.base_a2 = double(seedRow.a2(1));
resultRow.base_b1 = double(seedRow.b1(1));
resultRow.base_b2 = double(seedRow.b2(1));
resultRow.base_a3 = double(seedRow.a3(1));
resultRow.base_b3 = double(seedRow.b3(1));
resultRow.base_a4 = double(seedRow.a4(1));
resultRow.base_b4 = double(seedRow.b4(1));
resultRow.base_a5 = double(seedRow.a5(1));
resultRow.base_b5 = double(seedRow.b5(1));
resultRow.base_r0 = double(seedRow.r0(1));
resultRow.base_cascade_score = numeric_or_nan_from_seed(seedRow, 'cascade_score');
resultRow.base_contact_prob = numeric_or_nan_from_seed(seedRow, 'contact_prob');
resultRow.base_positive_prob = numeric_or_nan_from_seed(seedRow, 'positive_prob');
resultRow.base_surrogate_pred_gap34_gain_Hz = numeric_or_nan_from_seed(seedRow, 'surrogate_pred_gap34_gain_Hz');
resultRow.distance_from_seed = normalized_distance_from_seed(cfg, seedRow, candidate);
resultRow.fitness = compute_fitness(cfg, resultRow);
end

function value = numeric_or_nan_from_seed(seedRow, fieldName)
if ismember(fieldName, seedRow.Properties.VariableNames)
    value = double(seedRow.(fieldName)(1));
else
    value = NaN;
end
end

function pointSpec = point_spec_from_candidate(seedRow, candidate)
pointSpec = struct( ...
    'main_id', char(string(seedRow.main_id(1))), ...
    'point_id', char(string(seedRow.point_id(1))), ...
    'a1', double(candidate.a1(1)), 'a2', double(candidate.a2(1)), 'b1', double(candidate.b1(1)), 'b2', double(candidate.b2(1)), 'r0', double(candidate.r0(1)), ...
    'a3', double(candidate.a3(1)), 'b3', double(candidate.b3(1)), 'a4', double(candidate.a4(1)), 'b4', double(candidate.b4(1)), ...
    'a5', double(candidate.a5(1)), 'b5', double(candidate.b5(1)) ...
);
end

function values = pick_reference_column(seedTable, mask, name)
refName = ['reference_' name];
if ismember(refName, seedTable.Properties.VariableNames)
    values = seedTable.(refName)(mask);
else
    values = seedTable.(name)(mask);
end
end

function sampleMeta = sample_meta_from_seed(cfg, seedRow, seedIdx, generation, individualIdx)
shapeId = char(string(seedRow.shape_id(1)));
sampleMeta = struct( ...
    'sample_id', string(sanitize_id(sprintf('%s__s%02d__g%02d__i%03d__%s', cfg.gaId, seedIdx, generation, individualIdx, shapeId))), ...
    'candidate_id', string(sprintf('ga_s%02d_g%02d_i%03d', seedIdx, generation, individualIdx)), ...
    'shape_id', string(shapeId), ...
    'shape_family', string(seedRow.shape_family(1)), ...
    'shape_role', string(seedRow.shape_role(1)), ...
    'shape_file', string(fullfile(cfg.shapeDir, [shapeId '.csv'])) ...
);
end

function fitness = compute_fitness(cfg, row)
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
fitness = row.gap34_gain_Hz - cfg.distancePenaltyWeight * row.distance_from_seed;
end

function completed = completed_indices_for_generation(history, seedIdx, generation)
completed = [];
if isempty(history)
    return;
end
mask = [history.seed_index] == seedIdx & [history.generation] == generation;
if any(mask)
    completed = [history(mask).individual_index];
end
end

function rows = generation_rows(history, seedIdx, generation)
if isempty(history)
    rows = table();
    return;
end
mask = [history.seed_index] == seedIdx & [history.generation] == generation;
subset = history(mask);
if isempty(subset)
    rows = table();
    return;
end
rows = struct2table(subset, 'AsArray', true);
end

function summary = make_generation_summary(seedRow, rows, seedIdx, generation)
summary = struct();
summary.seed_index = seedIdx;
summary.seed_shape_id = string(seedRow.shape_id(1));
summary.seed_family = string(seedRow.shape_family(1));
summary.generation = generation;
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
summary.best_distance_from_seed = bestRow.distance_from_seed(1);
summary.best_a1 = bestRow.a1(1);
summary.best_a2 = bestRow.a2(1);
summary.best_b2 = bestRow.b2(1);
summary.best_a4 = bestRow.a4(1);
summary.best_b5 = bestRow.b5(1);
summary.best_r0 = bestRow.r0(1);
end

function summaries = upsert_summary_row(summaries, row)
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

function save_state(cfg, state)
configSignature = cfg.configSignature; %#ok<NASGU>
save(cfg.stateMat, 'state', 'configSignature');
end

function write_exports(cfg, state, seedTable)
write_history_table(cfg, state.history);
write_generation_summary_table(cfg, state.generationSummaries);
write_search_summary_table(cfg, state.history, seedTable);
write_best_candidates_table(cfg, state.history, seedTable);
end

function write_history_table(cfg, history)
if isempty(history)
    writetable(table(), cfg.historyCsv);
    return;
end
tbl = struct2table(history, 'AsArray', true);
writetable(tbl, cfg.historyCsv);
end

function write_generation_summary_table(cfg, generationSummaries)
if isempty(generationSummaries)
    writetable(table(), cfg.generationSummaryCsv);
    return;
end
tbl = struct2table(generationSummaries, 'AsArray', true);
writetable(tbl, cfg.generationSummaryCsv);
end

function write_search_summary_table(cfg, history, seedTable)
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
    best = sub(1, :);
    base = sub(sub.generation == 1 & sub.individual_index == 1, :);
    if isempty(base)
        base = best;
    else
        base = base(1, :);
    end
    row = struct( ...
        'seed_index', seedIdx, ...
        'seed_shape_id', string(seedTable.shape_id(seedIdx)), ...
        'seed_family', string(seedTable.shape_family(seedIdx)), ...
        'base_sample_id', string(base.sample_id(1)), ...
        'best_sample_id', string(best.sample_id(1)), ...
        'base_fitness', base.fitness(1), ...
        'best_fitness', best.fitness(1), ...
        'delta_fitness', best.fitness(1) - base.fitness(1), ...
        'base_gap34_gain_Hz', base.gap34_gain_Hz(1), ...
        'best_gap34_gain_Hz', best.gap34_gain_Hz(1), ...
        'delta_gap34_gain_Hz', best.gap34_gain_Hz(1) - base.gap34_gain_Hz(1), ...
        'best_generation', best.generation(1), ...
        'best_individual_index', best.individual_index(1), ...
        'best_a1', best.a1(1), 'best_a2', best.a2(1), 'best_b2', best.b2(1), ...
        'best_a4', best.a4(1), 'best_b5', best.b5(1), 'best_r0', best.r0(1), ...
        'solve_success_count', sum(sub.solve_success), ...
        'positive_gain_count', sum(sub.solve_success & sub.gap34_gain_Hz > 0) ...
    );
    rows = append_row(rows, row);
end
if isempty(rows)
    writetable(table(), cfg.searchSummaryCsv);
else
    writetable(struct2table(rows, 'AsArray', true), cfg.searchSummaryCsv);
end
end

function write_best_candidates_table(cfg, history, seedTable)
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
        rows = append_row(rows, table2struct(sub(i, :))); %#ok<AGROW>
    end
end
if isempty(rows)
    writetable(table(), cfg.bestCandidatesCsv);
else
    writetable(struct2table(rows, 'AsArray', true), cfg.bestCandidatesCsv);
end
end

function refPoint = lookup_reference_point(baselineByPoint, pointId)
ids = string({baselineByPoint.point_id});
idx = find(ids == string(pointId), 1, 'first');
if isempty(idx)
    error('run_comsol_in_loop_ga_v1:MissingRefPoint', 'Missing baseline reference for point %s.', pointId);
end
refPoint = baselineByPoint(idx);
end

function row = seed_gene_row(seedRow)
row = table();
for i = 1:numel(seedRow.Properties.VariableNames)
    name = seedRow.Properties.VariableNames{i};
    if ismember(name, {'a1','a2','b1','b2','a3','b3','a4','b4','a5','b5','r0'})
        row.(name) = double(seedRow.(name)(1));
    end
end
end

function bounds = search_bounds_for_param(cfg, seedRow, name)
globalBounds = cfg.globalBounds.(name);
if strcmpi(string(cfg.searchBoundsMode), "global")
    bounds = globalBounds;
    return;
end

halfWidth = cfg.localHalfWidths.(name);
baseValue = double(seedRow.(name)(1));
if globalBounds(1) == globalBounds(2) || halfWidth <= 0
    bounds = [baseValue, baseValue];
else
    bounds = [max(globalBounds(1), baseValue - halfWidth), min(globalBounds(2), baseValue + halfWidth)];
end
end

function value = clip_to_bounds(value, bounds)
value = min(max(value, bounds(1)), bounds(2));
end

function dist = normalized_distance_from_seed(cfg, seedRow, candidate)
parts = [];
for i = 1:numel(cfg.activeParamNames)
    name = cfg.activeParamNames{i};
    bounds = search_bounds_for_param(cfg, seedRow, name);
    span = bounds(2) - bounds(1);
    if span <= 0
        continue;
    end
    baseValue = double(seedRow.(name)(1));
    candidateValue = double(candidate.(name)(1));
    parts(end + 1) = abs(candidateValue - baseValue) / span; %#ok<AGROW>
end
if isempty(parts)
    dist = 0;
else
    dist = mean(parts);
end
end

function s = sanitize_id(s)
s = regexprep(char(string(s)), '[^A-Za-z0-9_.-]+', '_');
end

function value = logical_text(raw)
if raw
    value = 'true';
else
    value = 'false';
end
end

function value = numeric_text(raw)
if ~isfinite(raw)
    value = 'NaN';
else
    value = num2str(raw, '%.6g');
end
end

function rows = append_row(rows, row)
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

function save_config_json(cfg)
try
    payload = struct();
    fields = {'gaId','seedScoredCsv','seedPointId','seedWhitelistJson','topKSeeds','searchBoundsMode','populationSize','generations', ...
        'eliteCount','mutationRate','mutationScale','distancePenaltyWeight','randomSeed','topCandidatesPerSeedExport', ...
        'failurePenaltyGeometry','failurePenaltyContact','failurePenaltySolve','paramNames','activeParamNames', ...
        'globalBounds','localHalfWidths','materialCase','fixedGapBand','configSignature'};
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
