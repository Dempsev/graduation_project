function run_comsol_in_loop_band_catalog_ga_v1(cfg)
%RUN_COMSOL_IN_LOOP_BAND_CATALOG_GA_V1
% One global COMSOL-in-loop GA run with rotating band objectives and
% per-band top-candidate archives.

if nargin < 1 || isempty(cfg)
    cfg = get_comsol_in_loop_ga_band_catalog_config_v1();
end
cfg = finalize_runtime_config(cfg);

ensure_parent_dir(cfg.stateMat);
save_config_json(cfg);

shapePools = load_shape_pools(cfg);
shapePool = shapePools.unionPool;
pointTable = build_point_manifest(cfg);
if cfg.cooperativeMode
    [state, refPoint, hyperspaceHistory] = prepare_cooperative_run(cfg, shapePool, pointTable, shapePools);
else
    writetable(shapePool, cfg.shapePoolResolvedCsv);
    writetable(pointTable, cfg.pointManifestCsv);
    baselineByPoint = evaluate_stage2_harmonics_refine_baseline_points(cfg, pointTable);
    refPoint = baselineByPoint(1);
    hyperspaceHistory = load_novelty_history(cfg);
    state = load_or_init_state(cfg, shapePool);
end

fprintf('Band-catalog COMSOL-in-loop GA run\n');
fprintf('  ga_id=%s\n', cfg.gaId);
fprintf('  out_dir=%s\n', cfg.outDir);
fprintf('  shape_pool=%d\n', height(shapePool));
fprintf('  population=%d, max_generations=%d\n', cfg.populationSize, cfg.maxGenerations);
fprintf('  active_params=%s\n', strjoin(cfg.activeParamNames, ','));
fprintf('  reference_point=%s\n', cfg.referencePointId);
fprintf('  band_selection_mode=%s\n', char(string(cfg.bandSelectionMode)));
fprintf('  band_catalog=%s\n', band_catalog_signature(cfg.bandCatalog));
fprintf('  band_aware_shape_pools=%s\n', logical_text(isfield(cfg, 'bandAwareShapePoolsEnabled') && cfg.bandAwareShapePoolsEnabled));
if cfg.cooperativeMode
    fprintf('  cooperative_mode=on worker_id=%s\n', cfg.cooperativeWorkerId);
else
    fprintf('  cooperative_mode=off\n');
end
if cfg.enableEarlyStop
    fprintf('  early_stop=on patience=%d min_delta=%g min_generations=%d\n', ...
        cfg.earlyStopPatience, cfg.earlyStopMinDeltaFitness, cfg.earlyStopMinGenerations);
else
    fprintf('  early_stop=off\n');
end

if cfg.cooperativeMode
    run_cooperative_loop(cfg, shapePool, shapePools, refPoint, hyperspaceHistory);
    finalState = load_existing_state(cfg);
    write_exports(cfg, finalState, shapePool);
    fprintf('\nBand-catalog COMSOL-in-loop GA completed.\n');
    fprintf('  worker_id=%s\n', cfg.cooperativeWorkerId);
    fprintf('  stop_reason=%s\n', char(string(finalState.stopReason)));
    fprintf('  history_csv=%s\n', cfg.historyCsv);
    fprintf('  generation_summary_csv=%s\n', cfg.generationSummaryCsv);
    fprintf('  search_summary_csv=%s\n', cfg.searchSummaryCsv);
    fprintf('  band_catalog_summary_csv=%s\n', cfg.bandCatalogSummaryCsv);
    fprintf('  band_catalog_best_candidates_csv=%s\n', cfg.bandCatalogBestCandidatesCsv);
    return;
end

while state.nextGeneration <= cfg.maxGenerations && ~state.stopped
    generation = state.nextGeneration;
    activeBand = resolve_active_band(cfg, generation);
    activeShapePool = resolve_shape_pool_for_band(shapePools, activeBand.bandTag);
    fprintf('\nGeneration [%d/%d] active_band=%s [%g,%g] Hz\n', ...
        generation, cfg.maxGenerations, char(string(activeBand.bandTag)), activeBand.bandLowHz, activeBand.bandHighHz);
    fprintf('  active_shape_pool=%d\n', height(activeShapePool));

    if isempty(state.populations{generation})
        noveltyRows = merge_novelty_rows(hyperspaceHistory, state.history);
        if generation == 1
            state.populations{generation} = create_initial_population(cfg, activeShapePool, generation, noveltyRows);
        else
            previousRows = generation_rows(state.history, generation - 1);
            state.populations{generation} = breed_next_population(cfg, activeShapePool, previousRows, generation, noveltyRows);
        end
        save_state(cfg, state);
    end

    popTable = state.populations{generation};
    doneIndices = completed_indices_for_generation(state.history, generation);
    pending = setdiff(1:height(popTable), doneIndices, 'stable');

    for idx = pending
        candidate = popTable(idx, :);
        resultRow = evaluate_individual(cfg, candidate, refPoint, generation, idx);
        state.history = append_row(state.history, resultRow);
        save_state(cfg, state);

        fprintf(['    [%d/%d] %s shape=%s band=%s fitness=%s geometry=%s contact=%s solve=%s ' ...
                 'cover=%s overlap=%s gain=%s tier=%s\n'], ...
            idx, height(popTable), char(string(resultRow.sample_id)), ...
            char(string(resultRow.shape_id)), char(string(resultRow.active_band_tag)), ...
            numeric_text(resultRow.fitness), logical_text(resultRow.geometry_valid), ...
            logical_text(resultRow.contact_valid), logical_text(resultRow.solve_success), ...
            numeric_text(resultRow.active_target_cover_ratio), numeric_text(resultRow.active_target_overlap_Hz), ...
            numeric_text(resultRow.gap34_gain_Hz), char(string(resultRow.shape_pool_tier)));
        if strlength(string(resultRow.error_message)) > 0
            fprintf('      note=%s\n', char(string(resultRow.error_message)));
        end
    end

    generationRowsTable = generation_rows(state.history, generation);
    summaryRow = make_generation_summary(generationRowsTable, generation);
    state.generationSummaries = upsert_summary_row(state.generationSummaries, summaryRow);

    [state, plateauStop] = update_plateau_state(cfg, state, summaryRow);
    if plateauStop
        state.stopped = true;
        state.stopReason = sprintf('plateau_after_gen_%d', generation);
    elseif generation >= cfg.maxGenerations
        state.stopped = true;
        state.stopReason = sprintf('max_generations_%d', cfg.maxGenerations);
    end

    if ~state.stopped && generation < cfg.maxGenerations
        nextBand = resolve_active_band(cfg, generation + 1);
        nextShapePool = resolve_shape_pool_for_band(shapePools, nextBand.bandTag);
        noveltyRows = merge_novelty_rows(hyperspaceHistory, state.history);
        state.populations{generation + 1} = breed_next_population(cfg, nextShapePool, generationRowsTable, generation + 1, noveltyRows);
    end

    state.nextGeneration = generation + 1;
    save_state(cfg, state);
    write_exports(cfg, state, shapePool);
end

function cfg = finalize_runtime_config(cfg)
if ~isfield(cfg, 'cooperativeMode') || isempty(cfg.cooperativeMode)
    cfg.cooperativeMode = false;
end
if ~isfield(cfg, 'cooperativeWorkerId') || strlength(string(cfg.cooperativeWorkerId)) == 0
    cfg.cooperativeWorkerId = string(default_worker_id());
else
    cfg.cooperativeWorkerId = string(cfg.cooperativeWorkerId);
end
if ~isfield(cfg, 'cooperativePollSeconds') || isempty(cfg.cooperativePollSeconds)
    cfg.cooperativePollSeconds = 5;
end
if ~isfield(cfg, 'cooperativeLockTimeoutSeconds') || isempty(cfg.cooperativeLockTimeoutSeconds)
    cfg.cooperativeLockTimeoutSeconds = 300;
end
if ~isfield(cfg, 'cooperativeLockStaleSeconds') || isempty(cfg.cooperativeLockStaleSeconds)
    cfg.cooperativeLockStaleSeconds = 1800;
end
if ~isfield(cfg, 'cooperativeClaimTimeoutSeconds') || isempty(cfg.cooperativeClaimTimeoutSeconds)
    cfg.cooperativeClaimTimeoutSeconds = 21600;
end
if ~isfield(cfg, 'cooperativeStateLock') || strlength(string(cfg.cooperativeStateLock)) == 0
    cfg.cooperativeStateLock = fullfile(cfg.outDir, 'ga_state_v1.lock');
end
end

function workerId = default_worker_id()
host = getenv('COMPUTERNAME');
if isempty(host)
    host = getenv('HOSTNAME');
end
if isempty(host)
    host = 'matlab';
end
try
    pid = feature('getpid');
catch
    pid = 0;
end
workerId = sprintf('%s_pid%d', char(host), double(pid));
end

write_exports(cfg, state, shapePool);
fprintf('\nBand-catalog COMSOL-in-loop GA completed.\n');
fprintf('  stop_reason=%s\n', char(string(state.stopReason)));
fprintf('  history_csv=%s\n', cfg.historyCsv);
fprintf('  generation_summary_csv=%s\n', cfg.generationSummaryCsv);
fprintf('  search_summary_csv=%s\n', cfg.searchSummaryCsv);
fprintf('  band_catalog_summary_csv=%s\n', cfg.bandCatalogSummaryCsv);
fprintf('  band_catalog_best_candidates_csv=%s\n', cfg.bandCatalogBestCandidatesCsv);
end

function shapePools = load_shape_pools(cfg)
shapePools = struct();
shapePools.bandAware = false;
shapePools.unionPool = load_legacy_shape_pool(cfg);
shapePools.byBand = struct();

if ~(isfield(cfg, 'bandAwareShapePoolsEnabled') && cfg.bandAwareShapePoolsEnabled)
    return;
end

atlasDir = string(cfg.bandAwareShapePoolsDir);
if strlength(atlasDir) == 0 || ~isfolder(atlasDir)
    return;
end

bandStruct = struct();
poolFrames = cell(numel(cfg.bandCatalog), 1);
for i = 1:numel(cfg.bandCatalog)
    bandTag = string(cfg.bandCatalog(i).bandTag);
    poolPath = fullfile(char(atlasDir), char(bandTag), char(string(cfg.bandAwareShapePoolFilename)));
    if ~isfile(poolPath)
        warning('run_comsol_in_loop_band_catalog_ga_v1:MissingBandShapePool', ...
            'Band-aware shape pool missing for %s: %s. Falling back to legacy shape pool.', char(bandTag), poolPath);
        return;
    end
    bandPool = readtable(poolPath, 'TextType', 'string');
    bandPool = normalize_band_shape_pool(cfg, bandPool);
    if isempty(bandPool)
        warning('run_comsol_in_loop_band_catalog_ga_v1:EmptyBandShapePool', ...
            'Band-aware shape pool is empty for %s. Falling back to legacy shape pool.', char(bandTag));
        return;
    end
    key = matlab.lang.makeValidName(char(bandTag));
    bandStruct.(key) = bandPool;
    poolFrames{i} = bandPool;
end

shapePools.bandAware = true;
shapePools.byBand = bandStruct;
shapePools.unionPool = unique_shape_rows(vertcat(poolFrames{:}));
end

function shapePool = load_legacy_shape_pool(cfg)
shapePool = readtable(cfg.shapePoolCsv, 'TextType', 'string', 'Delimiter', ',', 'VariableNamingRule', 'preserve');
shapePool = normalize_legacy_shape_pool(cfg, shapePool);
if isempty(shapePool)
    error('run_comsol_in_loop_band_catalog_ga_v1:EmptyShapePool', 'Shape pool is empty after filtering.');
end
end

function shapePool = normalize_legacy_shape_pool(cfg, shapePool)
if isfield(cfg, 'useDiscretePerturbation') && ~cfg.useDiscretePerturbation
    shapePool = shapePool(1, :);
    shapePool.shape_id = "fourier_pure_boundary";
    shapePool.shape_family = "fourier";
    shapePool.shape_file = "";
    shapePool.shape_pool_tier = "fourier_only";
    return;
end
if ismember('geometry_valid', shapePool.Properties.VariableNames) && cfg.shapePoolRequireGeometryValid
    shapePool = shapePool(as_logical(shapePool.geometry_valid), :);
end
if ismember('contact_valid', shapePool.Properties.VariableNames) && cfg.shapePoolRequireContactValid
    shapePool = shapePool(as_logical(shapePool.contact_valid), :);
end
if ismember('solve_success', shapePool.Properties.VariableNames) && cfg.shapePoolRequireSolveSuccess
    shapePool = shapePool(as_logical(shapePool.solve_success), :);
end
if ismember('candidate_tier', shapePool.Properties.VariableNames) && ~isempty(cfg.shapePoolIncludeTiers)
    allowed = string(cfg.shapePoolIncludeTiers(:));
    shapePool = shapePool(ismember(string(shapePool.candidate_tier), allowed), :);
end
shapePool.shape_id = string(shapePool.shape_id);
shapePool.shape_family = string(arrayfun(@shape_family_from_id, shapePool.shape_id, 'UniformOutput', false));
shapePool.shape_file = string(fullfile(cfg.shapeDir, strcat(shapePool.shape_id, ".csv")));
shapePool.shape_pool_tier = string(shapePool.candidate_tier);
shapePool = sortrows(shapePool, {'gap_gain_Hz','shape_id'}, {'descend','ascend'});
shapePool = unique_shape_rows(shapePool);
shapePool = shapePool(isfile(cellstr(shapePool.shape_file)), :);
end

function shapePool = normalize_band_shape_pool(cfg, shapePool)
shapePool.shape_id = string(shapePool.shape_id);
if ~ismember('shape_family', shapePool.Properties.VariableNames)
    shapePool.shape_family = string(arrayfun(@shape_family_from_id, shapePool.shape_id, 'UniformOutput', false));
else
    shapePool.shape_family = string(shapePool.shape_family);
end
shapePool.shape_file = string(fullfile(cfg.shapeDir, strcat(shapePool.shape_id, ".csv")));
if ismember('selection_bucket', shapePool.Properties.VariableNames)
    shapePool.shape_pool_tier = string(shapePool.selection_bucket);
elseif ismember('shape_role_band', shapePool.Properties.VariableNames)
    shapePool.shape_pool_tier = string(shapePool.shape_role_band);
else
    shapePool.shape_pool_tier = repmat("band_aware_pool", height(shapePool), 1);
end
if ~ismember('shape_band_score', shapePool.Properties.VariableNames)
    shapePool.shape_band_score = zeros(height(shapePool), 1);
end
if ~ismember('best_cover_ratio', shapePool.Properties.VariableNames)
    shapePool.best_cover_ratio = zeros(height(shapePool), 1);
end
shapePool = shapePool(isfile(cellstr(shapePool.shape_file)), :);
shapePool = sortrows(shapePool, {'shape_band_score','best_cover_ratio','shape_id'}, {'descend','descend','ascend'});
shapePool = unique_shape_rows(shapePool);
end

function shapePool = resolve_shape_pool_for_band(shapePools, bandTag)
if shapePools.bandAware
    key = matlab.lang.makeValidName(char(string(bandTag)));
    if isfield(shapePools.byBand, key)
        shapePool = shapePools.byBand.(key);
        return;
    end
end
shapePool = shapePools.unionPool;
end

function tf = as_logical(values)
if islogical(values)
    tf = values;
    return;
end
if isnumeric(values)
    tf = values ~= 0;
    return;
end
text = lower(strtrim(string(values)));
tf = text == "1" | text == "true";
end

function family = shape_family_from_id(shapeId)
parts = split(string(shapeId), '_');
family = char(parts(1));
end

function shapePool = unique_shape_rows(shapePool)
[~, keepIdx] = unique(string(shapePool.shape_id), 'stable');
shapePool = shapePool(sort(keepIdx), :);
end

function pointTable = build_point_manifest(cfg)
spec = cfg.referencePointSpec;
pointTable = table( ...
    string(spec.main_id), string(spec.point_id), ...
    double(spec.a1), double(spec.a2), double(spec.b1), double(spec.b2), double(spec.r0), ...
    double(spec.a3), double(spec.b3), double(spec.a4), double(spec.b4), double(spec.a5), double(spec.b5), ...
    'VariableNames', {'main_id','point_id','a1','a2','b1','b2','r0','a3','b3','a4','b4','a5','b5'});
end

function state = load_or_init_state(cfg, shapePool)
if isfile(cfg.stateMat)
    loaded = load(cfg.stateMat, 'state', 'configSignature');
    if isfield(loaded, 'configSignature') && strcmp(string(loaded.configSignature), string(cfg.configSignature))
        state = loaded.state;
        if ~isequal(string(state.shapePoolIds(:)), string(shapePool.shape_id(:)))
            error('run_comsol_in_loop_band_catalog_ga_v1:ShapePoolMismatch', ...
                'Existing band-catalog GA state was created with a different shape pool. Remove %s to restart.', cfg.stateMat);
        end
        return;
    elseif isfield(loaded, 'state') && isfield(cfg, 'allowStateExtension') && cfg.allowStateExtension
        state = loaded.state;
        if ~isequal(string(state.shapePoolIds(:)), string(shapePool.shape_id(:)))
            error('run_comsol_in_loop_band_catalog_ga_v1:ShapePoolMismatch', ...
                'Existing band-catalog GA state was created with a different shape pool. Remove %s to restart.', cfg.stateMat);
        end
        if numel(state.populations) < cfg.maxGenerations
            state.populations{cfg.maxGenerations} = [];
        end
        if state.nextGeneration <= cfg.maxGenerations
            state.stopped = false;
            state.stopReason = "";
        end
        save_state(cfg, state);
        return;
    end
end

state = struct();
state.shapePoolIds = string(shapePool.shape_id);
state.nextGeneration = 1;
state.populations = cell(1, cfg.maxGenerations);
state.history = struct([]);
state.generationSummaries = struct([]);
state.bestFitnessSoFar = -inf;
state.noImproveCount = 0;
state.stopped = false;
state.stopReason = "";
save_state(cfg, state);
end

function [state, refPoint, hyperspaceHistory] = prepare_cooperative_run(cfg, shapePool, pointTable, ~)
lockHandle = acquire_state_lock(cfg);
cleanup = onCleanup(@() release_state_lock(lockHandle));
writetable(shapePool, cfg.shapePoolResolvedCsv);
writetable(pointTable, cfg.pointManifestCsv);
baselineByPoint = evaluate_stage2_harmonics_refine_baseline_points(cfg, pointTable);
refPoint = baselineByPoint(1);
hyperspaceHistory = load_novelty_history(cfg);
state = load_or_init_state(cfg, shapePool);
write_exports(cfg, state, shapePool);
clear cleanup;
release_state_lock(lockHandle);
end

function run_cooperative_loop(cfg, shapePool, shapePools, refPoint, hyperspaceHistory)
while true
    [action, payload] = claim_or_advance_work(cfg, shapePool, shapePools, hyperspaceHistory);
    switch action
        case "stop"
            return;
        case "wait"
            pause(cfg.cooperativePollSeconds);
        case "advance"
            continue;
        case "evaluate"
            generation = payload.generation;
            individualIdx = payload.individual_index;
            candidate = payload.candidate;
            resultRow = evaluate_individual(cfg, candidate, refPoint, generation, individualIdx);

            lockHandle = acquire_state_lock(cfg);
            cleanup = onCleanup(@() release_state_lock(lockHandle));
            state = load_existing_state(cfg);
            state = normalize_state(state);
            state.claims = prune_stale_claims(cfg, state.claims, state.nextGeneration);
            state = clear_claim(state, generation, individualIdx);
            if ~history_has_row(state.history, generation, individualIdx)
                state.history = append_row(state.history, resultRow);
                save_state(cfg, state);
                write_exports(cfg, state, shapePool);
            else
                save_state(cfg, state);
            end

            fprintf(['[%s] g%02d [%d/%d] %s shape=%s band=%s fitness=%s geometry=%s ' ...
                     'contact=%s solve=%s cover=%s overlap=%s tier=%s\n'], ...
                char(cfg.cooperativeWorkerId), generation, individualIdx, height(state.populations{generation}), ...
                char(string(resultRow.sample_id)), char(string(resultRow.shape_id)), char(string(resultRow.active_band_tag)), ...
                numeric_text(resultRow.fitness), logical_text(resultRow.geometry_valid), ...
                logical_text(resultRow.contact_valid), logical_text(resultRow.solve_success), ...
                numeric_text(resultRow.active_target_cover_ratio), numeric_text(resultRow.active_target_overlap_Hz), ...
                char(string(resultRow.shape_pool_tier)));
            if strlength(string(resultRow.error_message)) > 0
                fprintf('  note=%s\n', char(string(resultRow.error_message)));
            end

            clear cleanup;
            release_state_lock(lockHandle);
    end
end
end

function [action, payload] = claim_or_advance_work(cfg, shapePool, shapePools, hyperspaceHistory)
payload = struct();
lockHandle = acquire_state_lock(cfg);
cleanup = onCleanup(@() release_state_lock(lockHandle));
state = load_existing_state(cfg);
state = normalize_state(state);
state.claims = prune_stale_claims(cfg, state.claims, state.nextGeneration);

if state.stopped || state.nextGeneration > cfg.maxGenerations
    save_state(cfg, state);
    action = "stop";
    clear cleanup;
    release_state_lock(lockHandle);
    return;
end

generation = state.nextGeneration;
state = ensure_generation_population(cfg, state, shapePools, generation, hyperspaceHistory);
popTable = state.populations{generation};

doneIndices = completed_indices_for_generation(state.history, generation);
claimedIndices = claimed_indices_for_generation(state.claims, generation);
pending = setdiff(1:height(popTable), union(doneIndices, claimedIndices), 'stable');

if ~isempty(pending)
    individualIdx = pending(1);
    claim = struct( ...
        'generation', generation, ...
        'individual_index', individualIdx, ...
        'worker_id', string(cfg.cooperativeWorkerId), ...
        'claimed_at_posix', current_posix_time() ...
    );
    state.claims = append_claim(state.claims, claim);
    save_state(cfg, state);

    payload.generation = generation;
    payload.individual_index = individualIdx;
    payload.candidate = popTable(individualIdx, :);
    action = "evaluate";
    clear cleanup;
    release_state_lock(lockHandle);
    return;
end

if ~isempty(claimedIndices)
    save_state(cfg, state);
    action = "wait";
    clear cleanup;
    release_state_lock(lockHandle);
    return;
end

generationRowsTable = generation_rows(state.history, generation);
if height(generationRowsTable) < height(popTable)
    save_state(cfg, state);
    action = "wait";
    clear cleanup;
    release_state_lock(lockHandle);
    return;
end

summaryRow = make_generation_summary(generationRowsTable, generation);
state.generationSummaries = upsert_summary_row(state.generationSummaries, summaryRow);
state.claims = clear_generation_claims(state.claims, generation);

[state, plateauStop] = update_plateau_state(cfg, state, summaryRow);
if plateauStop
    state.stopped = true;
    state.stopReason = sprintf('plateau_after_gen_%d', generation);
elseif generation >= cfg.maxGenerations
    state.stopped = true;
    state.stopReason = sprintf('max_generations_%d', cfg.maxGenerations);
end

if ~state.stopped && generation < cfg.maxGenerations
    state = ensure_generation_population(cfg, state, shapePools, generation + 1, hyperspaceHistory);
end

state.nextGeneration = generation + 1;
save_state(cfg, state);
write_exports(cfg, state, shapePool);
fprintf('[%s] generation %d finalized\n', char(cfg.cooperativeWorkerId), generation);

action = "advance";
clear cleanup;
release_state_lock(lockHandle);
end

function state = ensure_generation_population(cfg, state, shapePools, generation, hyperspaceHistory)
if ~isempty(state.populations{generation})
    return;
end
activeBand = resolve_active_band(cfg, generation);
activeShapePool = resolve_shape_pool_for_band(shapePools, activeBand.bandTag);
noveltyRows = merge_novelty_rows(hyperspaceHistory, state.history);
if generation == 1
    state.populations{generation} = create_initial_population(cfg, activeShapePool, generation, noveltyRows);
else
    previousRows = generation_rows(state.history, generation - 1);
    state.populations{generation} = breed_next_population(cfg, activeShapePool, previousRows, generation, noveltyRows);
end
save_state(cfg, state);
end

function state = normalize_state(state)
if ~isfield(state, 'claims') || isempty(state.claims)
    state.claims = struct([]);
end
end

function state = load_existing_state(cfg)
loaded = load(cfg.stateMat, 'state');
state = loaded.state;
end

function claims = append_claim(claims, claim)
if isempty(claims)
    claims = claim;
else
    claims(end + 1) = claim; %#ok<AGROW>
end
end

function claims = prune_stale_claims(cfg, claims, currentGeneration)
if isempty(claims)
    return;
end
nowPosix = current_posix_time();
keep = true(1, numel(claims));
for i = 1:numel(claims)
    ageSeconds = nowPosix - double(claims(i).claimed_at_posix);
    if claims(i).generation < currentGeneration
        keep(i) = false;
    elseif ageSeconds > cfg.cooperativeClaimTimeoutSeconds
        fprintf('[%s] dropping stale claim g%02d i%03d from %s age=%.1fs\n', ...
            char(cfg.cooperativeWorkerId), claims(i).generation, claims(i).individual_index, ...
            char(string(claims(i).worker_id)), ageSeconds);
        keep(i) = false;
    end
end
claims = claims(keep);
end

function indices = claimed_indices_for_generation(claims, generation)
indices = [];
if isempty(claims)
    return;
end
mask = [claims.generation] == generation;
if any(mask)
    indices = [claims(mask).individual_index];
end
end

function state = clear_claim(state, generation, individualIdx)
if isempty(state.claims)
    return;
end
mask = ~(([state.claims.generation] == generation) & ([state.claims.individual_index] == individualIdx));
state.claims = state.claims(mask);
end

function claims = clear_generation_claims(claims, generation)
if isempty(claims)
    return;
end
mask = [claims.generation] ~= generation;
claims = claims(mask);
end

function tf = history_has_row(history, generation, individualIdx)
tf = false;
if isempty(history)
    return;
end
tf = any(([history.generation] == generation) & ([history.individual_index] == individualIdx));
end

function posix = current_posix_time()
posix = posixtime(datetime('now', 'TimeZone', 'UTC'));
end

function lockHandle = acquire_state_lock(cfg)
ensure_parent_dir(cfg.cooperativeStateLock);
startTic = tic;
while true
    stale_lock_cleanup(cfg);
    if try_create_lock_file(cfg.cooperativeStateLock, cfg.cooperativeWorkerId)
        lockHandle = struct('path', cfg.cooperativeStateLock, 'worker_id', string(cfg.cooperativeWorkerId));
        return;
    end
    if toc(startTic) > cfg.cooperativeLockTimeoutSeconds
        error('run_comsol_in_loop_band_catalog_ga_v1:LockTimeout', ...
            'Timed out waiting for state lock: %s', cfg.cooperativeStateLock);
    end
    pause(0.5);
end
end

function created = try_create_lock_file(lockPath, workerId)
created = false;
javaFile = java.io.File(lockPath);
try
    created = javaFile.createNewFile();
catch
    created = false;
end
if ~created
    return;
end
fid = fopen(lockPath, 'w');
if fid >= 0
    cleaner = onCleanup(@() fclose(fid));
    fprintf(fid, '%s\n', char(string(workerId)));
    clear cleaner;
end
end

function stale_lock_cleanup(cfg)
if ~isfile(cfg.cooperativeStateLock)
    return;
end
info = dir(cfg.cooperativeStateLock);
ageSeconds = seconds(datetime('now') - datetime(info.date));
if ageSeconds <= cfg.cooperativeLockStaleSeconds
    return;
end
fprintf('[%s] removing stale lock %s age=%.1fs\n', ...
    char(cfg.cooperativeWorkerId), cfg.cooperativeStateLock, ageSeconds);
delete(cfg.cooperativeStateLock);
end

function release_state_lock(lockHandle)
if isstruct(lockHandle) && isfield(lockHandle, 'path') && isfile(lockHandle.path)
    delete(lockHandle.path);
end
end

function population = create_initial_population(cfg, shapePool, generation, noveltyRows)
rng(cfg.randomSeed + generation, 'twister');
population = repmat(candidate_gene_row(cfg, shapePool(1, :)), cfg.populationSize, 1);
population.individual_index = transpose((1:cfg.populationSize));

for i = 1:cfg.populationSize
    shapeRow = random_shape_row(shapePool);
    population.shape_id(i) = string(shapeRow.shape_id(1));
    population.shape_family(i) = string(shapeRow.shape_family(1));
    population.shape_file(i) = string(shapeRow.shape_file(1));
    population.shape_pool_tier(i) = string(shapeRow.shape_pool_tier(1));
    for j = 1:numel(cfg.activeParamNames)
        name = cfg.activeParamNames{j};
        bounds = cfg.globalBounds.(name);
        if bounds(1) == bounds(2)
            population.(name)(i) = bounds(1);
        else
            population.(name)(i) = bounds(1) + rand * (bounds(2) - bounds(1));
        end
    end
    population(i, :) = enforce_novelty_on_row(cfg, population(i, :), shapePool, noveltyRows);
end
end

function population = breed_next_population(cfg, shapePool, previousRows, generation, noveltyRows)
rng(cfg.randomSeed + generation, 'twister');
sortedRows = sortrows(previousRows, {'fitness','active_target_cover_ratio','active_target_overlap_Hz','solve_success','contact_valid','geometry_valid'}, ...
    {'descend','descend','descend','descend','descend','descend'});
sortedRows = ensure_population_gene_columns(sortedRows, shapePool);

population = repmat(candidate_gene_row(cfg, shapePool(1, :)), cfg.populationSize, 1);
population.individual_index = transpose((1:cfg.populationSize));

eliteCount = min(cfg.eliteCount, height(sortedRows));
for i = 1:eliteCount
    population{i, population_gene_fields()} = sortedRows{i, population_gene_fields()};
end

for i = eliteCount + 1:cfg.populationSize
    parentA = tournament_pick(sortedRows);
    parentB = tournament_pick(sortedRows);

    shapeRow = inherit_shape_gene(parentA, parentB, shapePool, cfg.shapeMutationRate);
    population.shape_id(i) = string(shapeRow.shape_id(1));
    population.shape_family(i) = string(shapeRow.shape_family(1));
    population.shape_file(i) = string(shapeRow.shape_file(1));
    population.shape_pool_tier(i) = string(shapeRow.shape_pool_tier(1));

    for j = 1:numel(cfg.paramNames)
        name = cfg.paramNames{j};
        if ~ismember(name, cfg.activeParamNames)
            population.(name)(i) = cfg.referencePointSpec.(name);
            continue;
        end
        bounds = cfg.globalBounds.(name);
        alpha = rand;
        value = alpha * double(parentA.(name)(1)) + (1 - alpha) * double(parentB.(name)(1));
        if rand <= cfg.continuousMutationRate && bounds(1) < bounds(2)
            span = bounds(2) - bounds(1);
            value = value + randn * span * cfg.continuousMutationScale;
        end
        population.(name)(i) = clip_to_bounds(value, bounds);
    end
    population(i, :) = enforce_novelty_on_row(cfg, population(i, :), shapePool, noveltyRows);
end
end

function row = random_shape_row(shapePool)
idx = randi(height(shapePool));
row = shapePool(idx, :);
end

function row = inherit_shape_gene(parentA, parentB, shapePool, mutationRate)
if rand <= mutationRate
    row = random_shape_row(shapePool);
    return;
end
if rand < 0.5
    row = parentA(:, {'shape_id','shape_family','shape_file','shape_pool_tier'});
else
    row = parentB(:, {'shape_id','shape_family','shape_file','shape_pool_tier'});
end
end

function row = enforce_novelty_on_row(cfg, row, shapePool, noveltyRows)
if ~(isfield(cfg, 'noveltyEnabled') && cfg.noveltyEnabled)
    return;
end

if isempty(noveltyRows)
    return;
end

maxAttempts = 1;
if isfield(cfg, 'noveltyMaxResampleAttempts')
    maxAttempts = max(1, double(cfg.noveltyMaxResampleAttempts));
end

for attempt = 1:maxAttempts
    [isNovel, ~] = candidate_is_novel(cfg, row, noveltyRows);
    if isNovel
        return;
    end

    if mod(attempt, 4) == 0
        shapeRow = random_shape_row(shapePool);
        row.shape_id(1) = string(shapeRow.shape_id(1));
        row.shape_family(1) = string(shapeRow.shape_family(1));
        row.shape_file(1) = string(shapeRow.shape_file(1));
        row.shape_pool_tier(1) = string(shapeRow.shape_pool_tier(1));
    end

    for j = 1:numel(cfg.activeParamNames)
        name = cfg.activeParamNames{j};
        bounds = cfg.globalBounds.(name);
        if bounds(1) == bounds(2)
            row.(name)(1) = bounds(1);
        else
            row.(name)(1) = bounds(1) + rand * (bounds(2) - bounds(1));
        end
    end
end
end

function [isNovel, minDistance] = candidate_is_novel(cfg, row, noveltyRows)
shapeId = string(row.shape_id(1));
sameShape = noveltyRows(noveltyRows.shape_id == shapeId, :);
if isempty(sameShape)
    isNovel = true;
    minDistance = inf;
    return;
end

distances = inf(height(sameShape), 1);
for i = 1:height(sameShape)
    accum = 0.0;
    count = 0;
    for j = 1:numel(cfg.activeParamNames)
        name = cfg.activeParamNames{j};
        if ~ismember(name, sameShape.Properties.VariableNames)
            continue;
        end
        bounds = cfg.globalBounds.(name);
        span = bounds(2) - bounds(1);
        if span <= 0
            span = 1.0;
        end
        diffVal = double(row.(name)(1)) - double(sameShape.(name)(i));
        accum = accum + (diffVal / span) ^ 2;
        count = count + 1;
    end
    if count > 0
        distances(i) = sqrt(accum / count);
    end
end

minDistance = min(distances);
threshold = 0.0;
if isfield(cfg, 'noveltyMinDistanceNormalized')
    threshold = double(cfg.noveltyMinDistanceNormalized);
end
isNovel = ~isfinite(minDistance) || minDistance >= threshold;
end

function noveltyRows = load_novelty_history(cfg)
noveltyRows = table();
if ~(isfield(cfg, 'noveltyEnabled') && cfg.noveltyEnabled)
    return;
end
if ~(isfield(cfg, 'noveltyHistoryCsvs') && ~isempty(cfg.noveltyHistoryCsvs))
    return;
end

paramNames = {'a1','a2','b1','b2','a3','b3','a4','b4','a5','b5','r0'};
frames = cell(0, 1);
for i = 1:numel(cfg.noveltyHistoryCsvs)
    pathStr = string(cfg.noveltyHistoryCsvs{i});
    if strlength(pathStr) == 0 || ~isfile(pathStr)
        continue;
    end
    try
        tbl = readtable(char(pathStr), 'TextType', 'string');
    catch
        continue;
    end
    if ~ismember('shape_id', tbl.Properties.VariableNames)
        continue;
    end
    keepVars = [{'shape_id'}, cfg.paramNames];
    keepVars = keepVars(ismember(keepVars, tbl.Properties.VariableNames));
    if numel(keepVars) < 2
        continue;
    end
    tbl = tbl(:, keepVars);
    for j = 1:numel(paramNames)
        name = paramNames{j};
        if ~ismember(name, tbl.Properties.VariableNames)
            tbl.(name) = nan(height(tbl), 1);
        end
    end
    tbl = tbl(:, [{'shape_id'}, paramNames]);
    tbl.shape_id = string(tbl.shape_id);
    for j = 1:numel(paramNames)
        name = paramNames{j};
        tbl.(name) = str2double(string(tbl.(name)));
    end
    frames{end + 1, 1} = tbl; %#ok<AGROW>
end

if isempty(frames)
    return;
end

noveltyRows = vertcat(frames{:});
noveltyRows = unique(noveltyRows, 'rows');
end

function noveltyRows = merge_novelty_rows(historicalRows, history)
noveltyRows = historicalRows;
if isempty(history)
    return;
end
paramNames = {'a1','a2','b1','b2','a3','b3','a4','b4','a5','b5','r0'};
historyTable = struct2table(history, 'AsArray', true);
keepVars = intersect([{'shape_id'}, paramNames], historyTable.Properties.VariableNames, 'stable');
currentRows = historyTable(:, keepVars);
for j = 1:numel(paramNames)
    name = paramNames{j};
    if ~ismember(name, currentRows.Properties.VariableNames)
        currentRows.(name) = nan(height(currentRows), 1);
    end
end
currentRows = currentRows(:, [{'shape_id'}, paramNames]);
currentRows.shape_id = string(currentRows.shape_id);
if isempty(noveltyRows)
    noveltyRows = currentRows;
else
    noveltyRows = unique(vertcat(noveltyRows, currentRows), 'rows');
end
end

function row = tournament_pick(sortedRows)
if height(sortedRows) == 1
    row = sortedRows(1, :);
    return;
end
idx = randperm(height(sortedRows), min(3, height(sortedRows)));
subset = sortedRows(idx, :);
subset = sortrows(subset, {'fitness','active_target_cover_ratio','active_target_overlap_Hz'}, {'descend','descend','descend'});
row = subset(1, :);
end

function resultRow = evaluate_individual(cfg, candidate, refPoint, generation, individualIdx)
pointSpec = struct( ...
    'main_id', cfg.referencePointSpec.main_id, ...
    'point_id', cfg.referencePointSpec.point_id, ...
    'a1', double(candidate.a1(1)), 'a2', double(candidate.a2(1)), 'b1', double(candidate.b1(1)), 'b2', double(candidate.b2(1)), 'r0', double(candidate.r0(1)), ...
    'a3', double(candidate.a3(1)), 'b3', double(candidate.b3(1)), 'a4', double(candidate.a4(1)), 'b4', double(candidate.b4(1)), ...
    'a5', double(candidate.a5(1)), 'b5', double(candidate.b5(1)) ...
);
sampleMeta = struct( ...
    'sample_id', string(sanitize_id(sprintf('%s__g%02d__i%03d__%s', cfg.gaId, generation, individualIdx, char(string(candidate.shape_id(1)))))), ...
    'candidate_id', string(sprintf('band_catalog_ga_g%02d_i%03d', generation, individualIdx)), ...
    'shape_id', string(candidate.shape_id(1)), ...
    'shape_family', string(candidate.shape_family(1)), ...
    'shape_role', "global_shape_pool", ...
    'shape_file', string(candidate.shape_file(1)) ...
);

result = evaluate_stage2_harmonics_refine_case_internal(cfg, sampleMeta, pointSpec, refPoint);
result.generation = generation;
result.individual_index = individualIdx;
result.shape_file = string(candidate.shape_file(1));
result.shape_pool_tier = string(candidate.shape_pool_tier(1));
result.b1 = double(candidate.b1(1));

resultRow = attach_band_catalog_metrics(cfg, result);
resultRow.fitness = compute_fitness(cfg, resultRow);
resultRow.distance_from_seed = NaN;
end

function row = attach_band_catalog_metrics(cfg, row)
activeBand = resolve_active_band(cfg, row.generation);
row.active_band_tag = string(activeBand.bandTag);
row.active_band_low_Hz = activeBand.bandLowHz;
row.active_band_high_Hz = activeBand.bandHighHz;
row.active_target_is_open = 0;
row.active_target_overlap_Hz = 0.0;
row.active_target_cover_ratio = 0.0;
row.active_target_best_width_Hz = NaN;
row.active_target_lower_edge_Hz = NaN;
row.active_target_upper_edge_Hz = NaN;

tbl1Path = fullfile(cfg.tbl1Dir, [char(string(row.sample_id)) '_tbl1.csv']);
for i = 1:numel(cfg.bandCatalog)
    band = cfg.bandCatalog(i);
    metrics = extract_stage2_harmonics_refine_targetband_metrics_from_tbl1(tbl1Path, band.bandLowHz, band.bandHighHz);
    prefix = char(string(band.bandTag));
    row.([prefix '_is_open']) = metrics.target_gap_is_open;
    row.([prefix '_overlap_Hz']) = metrics.target_gap_overlap_Hz;
    row.([prefix '_cover_ratio']) = metrics.target_gap_cover_ratio;
    row.([prefix '_best_width_Hz']) = metrics.target_gap_best_width_Hz;
    row.([prefix '_lower_edge_Hz']) = metrics.target_gap_lower_edge_Hz;
    row.([prefix '_upper_edge_Hz']) = metrics.target_gap_upper_edge_Hz;

    if string(band.bandTag) == string(activeBand.bandTag)
        row.active_target_is_open = metrics.target_gap_is_open;
        row.active_target_overlap_Hz = metrics.target_gap_overlap_Hz;
        row.active_target_cover_ratio = metrics.target_gap_cover_ratio;
        row.active_target_best_width_Hz = metrics.target_gap_best_width_Hz;
        row.active_target_lower_edge_Hz = metrics.target_gap_lower_edge_Hz;
        row.active_target_upper_edge_Hz = metrics.target_gap_upper_edge_Hz;
    end
end
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
if ~row.solve_success
    fitness = cfg.failurePenaltySolve;
    return;
end
coverRatio = row.active_target_cover_ratio;
if ~isfinite(coverRatio)
    coverRatio = 0;
end
overlapHz = row.active_target_overlap_Hz;
if ~isfinite(overlapHz)
    overlapHz = 0;
end
bestWidthHz = row.active_target_best_width_Hz;
if ~isfinite(bestWidthHz)
    bestWidthHz = 0;
end
fitnessMetric = "cover_overlap_width";
if isfield(cfg, 'fitnessMetric') && strlength(string(cfg.fitnessMetric)) > 0
    fitnessMetric = string(cfg.fitnessMetric);
end

switch fitnessMetric
    case "target_overlap_Hz"
        fitness = overlapHz;
    case "target_cover_ratio"
        fitness = coverRatio;
    otherwise
        fitness = coverRatio + 0.0005 * overlapHz + 0.0001 * max(0, bestWidthHz);
end
end

function band = resolve_active_band(cfg, generation)
idx = mod(generation - 1, numel(cfg.bandCatalog)) + 1;
band = cfg.bandCatalog(idx);
end

function [state, shouldStop] = update_plateau_state(cfg, state, summaryRow)
shouldStop = false;
if summaryRow.best_fitness > state.bestFitnessSoFar + cfg.earlyStopMinDeltaFitness
    state.bestFitnessSoFar = summaryRow.best_fitness;
    state.noImproveCount = 0;
else
    state.noImproveCount = state.noImproveCount + 1;
end

if cfg.enableEarlyStop && summaryRow.generation >= cfg.earlyStopMinGenerations && state.noImproveCount >= cfg.earlyStopPatience
    shouldStop = true;
end
end

function completed = completed_indices_for_generation(history, generation)
completed = [];
if isempty(history)
    return;
end
mask = [history.generation] == generation;
if any(mask)
    completed = [history(mask).individual_index];
end
end

function rows = generation_rows(history, generation)
if isempty(history)
    rows = table();
    return;
end
mask = [history.generation] == generation;
subset = history(mask);
if isempty(subset)
    rows = table();
    return;
end
rows = struct2table(subset, 'AsArray', true);
end

function summary = make_generation_summary(rows, generation)
summary = struct();
summary.generation = generation;
summary.population_size = height(rows);
summary.solve_success_count = sum(rows.solve_success);
summary.active_open_count = sum(rows.solve_success & rows.active_target_is_open > 0);
summary.best_fitness = max(rows.fitness);
summary.mean_fitness = mean(rows.fitness);
bestRow = sortrows(rows, {'fitness','active_target_cover_ratio','active_target_overlap_Hz'}, {'descend','descend','descend'});
bestRow = bestRow(1, :);
summary.active_band_tag = string(bestRow.active_band_tag(1));
summary.best_sample_id = string(bestRow.sample_id(1));
summary.best_shape_id = string(bestRow.shape_id(1));
summary.best_shape_family = string(bestRow.shape_family(1));
summary.best_shape_pool_tier = string(bestRow.shape_pool_tier(1));
summary.best_active_cover_ratio = bestRow.active_target_cover_ratio(1);
summary.best_active_overlap_Hz = bestRow.active_target_overlap_Hz(1);
summary.best_gap34_gain_Hz = bestRow.gap34_gain_Hz(1);
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
mask = arrayfun(@(s) s.generation == row.generation, summaries);
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

function write_exports(cfg, state, shapePool)
write_history_table(cfg, state.history);
write_generation_summary_table(cfg, state.generationSummaries);
write_search_summary_table(cfg, state.history, shapePool, state.stopReason);
write_best_candidates_table(cfg, state.history);
write_band_catalog_exports(cfg, state.history);
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

function write_search_summary_table(cfg, history, shapePool, stopReason)
if isempty(history)
    writetable(table(), cfg.searchSummaryCsv);
    return;
end
historyTable = struct2table(history, 'AsArray', true);
historyTable = sortrows(historyTable, {'fitness','active_target_cover_ratio','active_target_overlap_Hz'}, {'descend','descend','descend'});
best = historyTable(1, :);

row = table( ...
    string(stopReason), ...
    height(shapePool), ...
    height(historyTable), ...
    max(historyTable.generation), ...
    sum(historyTable.solve_success), ...
    sum(historyTable.solve_success & historyTable.active_target_is_open > 0), ...
    string(best.sample_id(1)), ...
    string(best.shape_id(1)), ...
    string(best.shape_family(1)), ...
    string(best.shape_pool_tier(1)), ...
    string(best.active_band_tag(1)), ...
    best.fitness(1), ...
    best.active_target_cover_ratio(1), ...
    best.active_target_overlap_Hz(1), ...
    best.gap34_gain_Hz(1), ...
    best.a1(1), best.a2(1), best.b2(1), best.a4(1), best.b5(1), best.r0(1), ...
    'VariableNames', {'stop_reason','shape_pool_count','evaluated_count','generation_count','solve_success_count','active_open_count', ...
    'best_sample_id','best_shape_id','best_shape_family','best_shape_pool_tier','best_active_band_tag','best_fitness', ...
    'best_active_cover_ratio','best_active_overlap_Hz','best_gap34_gain_Hz', ...
    'best_a1','best_a2','best_b2','best_a4','best_b5','best_r0'});
writetable(row, cfg.searchSummaryCsv);
end

function write_best_candidates_table(cfg, history)
if isempty(history)
    writetable(table(), cfg.bestCandidatesCsv);
    return;
end
historyTable = struct2table(history, 'AsArray', true);
historyTable = sortrows(historyTable, {'fitness','active_target_cover_ratio','active_target_overlap_Hz'}, {'descend','descend','descend'});
keepN = min(height(historyTable), cfg.topCandidatesExport);
writetable(historyTable(1:keepN, :), cfg.bestCandidatesCsv);
end

function write_band_catalog_exports(cfg, history)
if isempty(history)
    writetable(table(), cfg.bandCatalogSummaryCsv);
    writetable(table(), cfg.bandCatalogBestCandidatesCsv);
    return;
end

historyTable = struct2table(history, 'AsArray', true);
summaryRows = struct([]);
bestRows = struct([]);
for i = 1:numel(cfg.bandCatalog)
    band = cfg.bandCatalog(i);
    prefix = char(string(band.bandTag));
    coverField = [prefix '_cover_ratio'];
    overlapField = [prefix '_overlap_Hz'];
    openField = [prefix '_is_open'];
    lowerField = [prefix '_lower_edge_Hz'];
    upperField = [prefix '_upper_edge_Hz'];
    widthField = [prefix '_best_width_Hz'];
    if ~ismember(coverField, historyTable.Properties.VariableNames)
        continue;
    end

    valid = historyTable(historyTable.solve_success == true, :);
    if isempty(valid)
        continue;
    end
    valid = sortrows(valid, {coverField, overlapField, 'gap34_gain_Hz'}, {'descend','descend','descend'});
    best = valid(1, :);

    summaryRows = append_row(summaryRows, struct( ...
        'band_tag', string(band.bandTag), ...
        'band_low_Hz', band.bandLowHz, ...
        'band_high_Hz', band.bandHighHz, ...
        'evaluated_count', height(valid), ...
        'open_count', sum(valid.(openField) > 0), ...
        'best_sample_id', string(best.sample_id(1)), ...
        'best_shape_id', string(best.shape_id(1)), ...
        'best_shape_family', string(best.shape_family(1)), ...
        'best_cover_ratio', best.(coverField)(1), ...
        'best_overlap_Hz', best.(overlapField)(1), ...
        'best_gap_width_Hz', best.(widthField)(1), ...
        'best_gap_lower_edge_Hz', best.(lowerField)(1), ...
        'best_gap_upper_edge_Hz', best.(upperField)(1), ...
        'best_gap34_gain_Hz', best.gap34_gain_Hz(1), ...
        'best_a1', best.a1(1), 'best_a2', best.a2(1), 'best_b2', best.b2(1), 'best_a4', best.a4(1), 'best_b5', best.b5(1), 'best_r0', best.r0(1) ...
    ));

    keepN = min(height(valid), cfg.archiveTopCandidatesPerBand);
    for j = 1:keepN
        row = table2struct(valid(j, :));
        row.archive_band_tag = string(band.bandTag);
        row.archive_band_low_Hz = band.bandLowHz;
        row.archive_band_high_Hz = band.bandHighHz;
        row.archive_cover_ratio = valid.(coverField)(j);
        row.archive_overlap_Hz = valid.(overlapField)(j);
        row.archive_gap_width_Hz = valid.(widthField)(j);
        bestRows = append_row(bestRows, row);
    end
end

if isempty(summaryRows)
    writetable(table(), cfg.bandCatalogSummaryCsv);
else
    writetable(struct2table(summaryRows, 'AsArray', true), cfg.bandCatalogSummaryCsv);
end
if isempty(bestRows)
    writetable(table(), cfg.bandCatalogBestCandidatesCsv);
else
    writetable(struct2table(bestRows, 'AsArray', true), cfg.bandCatalogBestCandidatesCsv);
end
end

function row = candidate_gene_row(cfg, shapeRow)
row = table();
row.shape_id = string(shapeRow.shape_id(1));
row.shape_family = string(shapeRow.shape_family(1));
row.shape_file = string(shapeRow.shape_file(1));
row.shape_pool_tier = string(shapeRow.shape_pool_tier(1));
for i = 1:numel(cfg.paramNames)
    name = cfg.paramNames{i};
    row.(name) = cfg.referencePointSpec.(name);
end
end

function rows = ensure_population_gene_columns(rows, shapePool)
if isempty(rows)
    return;
end
if ~ismember('shape_file', rows.Properties.VariableNames)
    rows.shape_file = strings(height(rows), 1);
end
if ~ismember('shape_family', rows.Properties.VariableNames)
    rows.shape_family = strings(height(rows), 1);
end
if ~ismember('shape_pool_tier', rows.Properties.VariableNames)
    rows.shape_pool_tier = strings(height(rows), 1);
end

shapeIds = string(rows.shape_id);
poolIds = string(shapePool.shape_id);
[isKnown, loc] = ismember(shapeIds, poolIds);
for i = 1:height(rows)
    if isKnown(i)
        if strlength(string(rows.shape_file(i))) == 0
            rows.shape_file(i) = string(shapePool.shape_file(loc(i)));
        end
        if strlength(string(rows.shape_family(i))) == 0
            rows.shape_family(i) = string(shapePool.shape_family(loc(i)));
        end
        if strlength(string(rows.shape_pool_tier(i))) == 0
            rows.shape_pool_tier(i) = string(shapePool.shape_pool_tier(loc(i)));
        end
    end
end
end

function names = population_gene_fields()
names = {'shape_id','shape_family','shape_file','shape_pool_tier','a1','a2','b1','b2','a3','b3','a4','b4','a5','b5','r0'};
end

function value = clip_to_bounds(value, bounds)
value = min(max(value, bounds(1)), bounds(2));
end

function out = band_catalog_signature(catalog)
parts = strings(numel(catalog), 1);
for i = 1:numel(catalog)
    parts(i) = sprintf('%s:%g-%g', char(string(catalog(i).bandTag)), catalog(i).bandLowHz, catalog(i).bandHighHz);
end
out = strjoin(cellstr(parts), ',');
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
    fields = { ...
        'gaId','shapePoolMode','shapePoolCsv','shapePoolRequireGeometryValid','shapePoolRequireContactValid','shapePoolRequireSolveSuccess', ...
        'shapePoolIncludeTiers','referenceMainId','referencePointId','referencePointSpec','populationSize','maxGenerations', ...
        'eliteCount','shapeMutationRate','continuousMutationRate','continuousMutationScale','randomSeed','paramNames', ...
        'activeParamNames','globalBounds','failurePenaltyGeometry','failurePenaltyContact','failurePenaltySolve', ...
        'enableEarlyStop','earlyStopPatience','earlyStopMinDeltaFitness','earlyStopMinGenerations','topCandidatesExport', ...
        'bandCatalog','bandSelectionMode','archiveTopCandidatesPerBand','bandAwareShapePoolsEnabled','bandAwareShapePoolsDir','bandAwareShapePoolFilename', ...
        'noveltyEnabled','noveltyMinDistanceNormalized','noveltyMaxResampleAttempts','noveltyHistoryCsvs','configSignature' ...
    };
    for i = 1:numel(fields)
        name = fields{i};
        if isfield(cfg, name)
            payload.(name) = cfg.(name);
        end
    end
    fid = fopen(cfg.configJson, 'w');
    cleaner = onCleanup(@() fclose(fid));
    fwrite(fid, jsonencode(payload, 'PrettyPrint', true), 'char');
    clear cleaner;
catch
end
end
