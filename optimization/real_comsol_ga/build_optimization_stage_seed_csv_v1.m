function outCsv = build_optimization_stage_seed_csv_v1(baseSeedCsv, previousBestCandidatesCsv, survivorIds, outCsv)
%BUILD_OPTIMIZATION_STAGE_SEED_CSV_V1
% Build a follow-up-stage seed csv by replacing the incoming seed parameters with
% the best real candidate parameters found in the previous stage.

if ~isfile(baseSeedCsv)
    error('build_optimization_stage_seed_csv_v1:MissingBaseSeedCsv', ...
        'Base seed csv not found: %s', baseSeedCsv);
end
if ~isfile(previousBestCandidatesCsv)
    error('build_optimization_stage_seed_csv_v1:MissingPreviousBestCandidatesCsv', ...
        'Previous-stage best candidates csv not found: %s', previousBestCandidatesCsv);
end

survivorIds = string(survivorIds(:));
survivorIds = survivorIds(strlength(survivorIds) > 0);
if isempty(survivorIds)
    error('build_optimization_stage_seed_csv_v1:NoSurvivorIds', ...
        'No survivor ids were provided for follow-up stage seed csv construction.');
end

baseTbl = readtable(baseSeedCsv);
prevTbl = readtable(previousBestCandidatesCsv);

baseTbl.shape_id = string(baseTbl.shape_id);
prevTbl.shape_id = string(prevTbl.shape_id);
prevTbl.point_id = string(prevTbl.point_id);
prevTbl.sample_id = string(prevTbl.sample_id);

baseTbl = baseTbl(ismember(baseTbl.shape_id, survivorIds), :);
if isempty(baseTbl)
    error('build_optimization_stage_seed_csv_v1:NoBaseRows', ...
        'No base seed rows matched the survivor ids.');
end

paramNames = {'a1','a2','b1','b2','a3','b3','a4','b4','a5','b5','r0'};
prevTbl = sortrows(prevTbl, {'fitness','gap34_gain_Hz'}, {'descend','descend'});

for j = 1:numel(paramNames)
    refName = ['reference_' paramNames{j}];
    if ~ismember(refName, baseTbl.Properties.VariableNames)
        baseTbl.(refName) = baseTbl.(paramNames{j});
    end
end

baseTbl = ensure_stage_metadata_columns(baseTbl);

for i = 1:height(baseTbl)
    shapeId = string(baseTbl.shape_id(i));
    pointId = string(baseTbl.point_id(i));
    match = prevTbl(prevTbl.shape_id == shapeId & prevTbl.point_id == pointId, :);
    if isempty(match)
        match = prevTbl(prevTbl.shape_id == shapeId, :);
    end
    if isempty(match)
        error('build_optimization_stage_seed_csv_v1:MissingPreviousCandidate', ...
            'No previous-stage best candidate found for survivor %s.', shapeId);
    end
    best = match(1, :);

    for j = 1:numel(paramNames)
        name = paramNames{j};
        if ismember(name, baseTbl.Properties.VariableNames) && ismember(name, best.Properties.VariableNames)
            baseTbl.(name)(i) = best.(name)(1);
        end
    end

    baseTbl = assign_table_text_value(baseTbl, 'prev_best_sample_id', i, string(best.sample_id(1)));
    baseTbl.prev_best_gap34_gain_Hz(i) = double(best.gap34_gain_Hz(1));
    baseTbl.prev_best_fitness(i) = double(best.fitness(1));
    if ismember('generation', best.Properties.VariableNames)
        baseTbl.prev_best_generation(i) = double(best.generation(1));
    end
    if ismember('individual_index', best.Properties.VariableNames)
        baseTbl.prev_best_individual_index(i) = double(best.individual_index(1));
    end
end

baseTbl = sortrows(baseTbl, {'prev_best_gap34_gain_Hz','shape_id'}, {'descend','ascend'});
writetable(baseTbl, outCsv);
end

function tbl = ensure_stage_metadata_columns(tbl)
if ~ismember('prev_best_sample_id', tbl.Properties.VariableNames)
    tbl.prev_best_sample_id = strings(height(tbl), 1);
end
if ~ismember('prev_best_gap34_gain_Hz', tbl.Properties.VariableNames)
    tbl.prev_best_gap34_gain_Hz = nan(height(tbl), 1);
end
if ~ismember('prev_best_fitness', tbl.Properties.VariableNames)
    tbl.prev_best_fitness = nan(height(tbl), 1);
end
if ~ismember('prev_best_generation', tbl.Properties.VariableNames)
    tbl.prev_best_generation = nan(height(tbl), 1);
end
if ~ismember('prev_best_individual_index', tbl.Properties.VariableNames)
    tbl.prev_best_individual_index = nan(height(tbl), 1);
end
end

function tbl = assign_table_text_value(tbl, columnName, rowIdx, value)
if ~ismember(columnName, tbl.Properties.VariableNames)
    tbl.(columnName) = strings(height(tbl), 1);
end

col = tbl.(columnName);
if isstring(col)
    col(rowIdx) = value;
elseif iscell(col)
    col{rowIdx} = char(value);
else
    col = string(col);
    col(rowIdx) = value;
end
tbl.(columnName) = col;
end
