import com.comsol.model.*
import com.comsol.model.util.*

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
addpath(genpath(fullfile(rootDir, 'model_core')));
addpath(genpath(fullfile(rootDir, 'stage2')));
addpath(genpath(fullfile(rootDir, 'stage2_harmonics')));
addpath(genpath(fullfile(rootDir, 'stage2_harmonics_refine')));
addpath(genpath(fullfile(rootDir, 'stage4_validation')));

cfg = get_stage4_validation_config_v2();
startIndex = 1;
maxCount = 0; % set positive value to limit validation subset

if ~isfile(cfg.validationManifestCsv)
    error('run_stage4_validation_ab_v2:MissingManifest', 'Validation manifest not found: %s', cfg.validationManifestCsv);
end

manifestTable = readtable(cfg.validationManifestCsv);
manifestTable = normalize_manifest_table(manifestTable);
manifestEndIndex = resolve_end_index(height(manifestTable), startIndex, maxCount);
activeManifest = manifestTable(startIndex:manifestEndIndex, :);

pointTable = build_unique_point_table(manifestTable);
writetable(pointTable, cfg.pointManifestCsv);

results = load_saved_results(cfg.resultsMat, cfg);
processedIds = string(get_processed_ids(results));

fprintf('Stage-4 validation A/B run\n');
fprintf('Fourier model: %s\n', cfg.fourierId);
fprintf('Material case: %s\n', cfg.materialCase);
fprintf('Validation manifest: %s\n', cfg.validationManifestCsv);
fprintf('Output dir: %s\n', cfg.outDir);
fprintf('Manifest rows discovered: %d\n', height(manifestTable));
fprintf('Unique baseline points: %d\n', height(pointTable));
fprintf('Processing range: startIndex=%d, endIndex=%d\n', startIndex, manifestEndIndex);

baselineByPoint = evaluate_stage2_harmonics_refine_baseline_points(cfg, pointTable);
runResults = struct([]);
resumeSkipped = 0;

for i = 1:height(activeManifest)
    row = activeManifest(i, :);
    sampleMeta = validation_row_to_sample_meta(row, cfg);
    if any(processedIds == string(sampleMeta.sample_id))
        resumeSkipped = resumeSkipped + 1;
        fprintf('  [%d/%d] resume-skip %s\n', i, height(activeManifest), char(string(sampleMeta.sample_id)));
        continue;
    end

    pointSpec = validation_row_to_point_spec(row);
    refPoint = lookup_reference_point(baselineByPoint, pointSpec.point_id);
    fprintf(['[%d/%d] %s source=%s shape=%s point=%s ' ...
             'a1=%.3f a2=%.3f b2=%.3f a4=%.3f b5=%.3f\n'], ...
        i, height(activeManifest), char(string(row.validation_id(1))), char(string(row.selection_source(1))), ...
        char(string(row.shape_id(1))), char(string(row.point_id(1))), ...
        pointSpec.a1, pointSpec.a2, pointSpec.b2, pointSpec.a4, pointSpec.b5);

    result = evaluate_stage2_harmonics_refine_case_internal(cfg, sampleMeta, pointSpec, refPoint);
    result = attach_validation_metadata(result, row);

    results = append_result(results, result);
    runResults = append_result(runResults, result);
    processedIds(end + 1, 1) = string(result.sample_id); %#ok<AGROW>

    configSignature = cfg.configSignature; %#ok<NASGU>
    save(cfg.resultsMat, 'results', 'configSignature');
    resultsTable = results_to_table(results, cfg);
    writetable(resultsTable, cfg.resultsCsv);
    write_stage4_validation_summary_tables(resultsTable, cfg);

    fprintf('    geometry_valid=%s, contact_valid=%s, solve_success=%s, gap34_gain_Hz=%s\n', ...
        logical_text(result.geometry_valid), ...
        logical_text(result.contact_valid), ...
        logical_text(result.solve_success), ...
        numeric_text(result.gap34_gain_Hz));
    if ~isempty(result.error_message)
        fprintf('    note=%s\n', char(string(result.error_message)));
    end
end

summary = summarize_results(runResults, cfg);
allResultsTable = results_to_table(results, cfg);
write_stage4_validation_summary_tables(allResultsTable, cfg);

fprintf('\nStage-4 validation run summary\n');
fprintf('  processed_new=%d\n', summary.total);
fprintf('  resume_skipped=%d\n', resumeSkipped);
fprintf('  geometry_invalid=%d\n', summary.geometry_invalid);
fprintf('  no_contact=%d\n', summary.no_contact);
fprintf('  solve_success=%d\n', summary.solve_success);
fprintf('  positive_gap34_gain=%d\n', summary.positive_gain);
fprintf('  results_csv=%s\n', cfg.resultsCsv);
fprintf('  arm_summary_csv=%s\n', cfg.armSummaryCsv);
fprintf('  point_summary_csv=%s\n', cfg.pointSummaryCsv);
fprintf('  shape_summary_csv=%s\n', cfg.shapeSummaryCsv);
fprintf('  baseline_by_point_csv=%s\n', cfg.baselineByPointCsv);

function manifestTable = normalize_manifest_table(manifestTable)
textVars = {'validation_id','selection_source','selection_label','sample_id','shape_id','shape_family','shape_role','candidate_id','main_id','point_id'};
for i = 1:numel(textVars)
    name = textVars{i};
    if ismember(name, manifestTable.Properties.VariableNames)
        manifestTable.(name) = string(manifestTable.(name));
    end
end
end

function pointTable = build_unique_point_table(manifestTable)
mask = false(height(manifestTable), 1);
seen = strings(0, 1);
for i = 1:height(manifestTable)
    pointId = string(manifestTable.point_id(i));
    if any(seen == pointId)
        continue;
    end
    seen(end + 1, 1) = pointId; %#ok<AGROW>
    mask(i) = true;
end
pointTable = manifestTable(mask, {'main_id','point_id','a1','a2','b2','r0','a3','b3','a4','b4','a5','b5'});
end

function idx = resolve_end_index(totalCount, startIndex, maxCount)
if maxCount <= 0
    idx = totalCount;
else
    idx = min(totalCount, startIndex + maxCount - 1);
end
end

function results = load_saved_results(resultsMat, cfg)
results = struct([]);
if ~isfile(resultsMat)
    return;
end
loaded = load(resultsMat, 'results', 'configSignature');
if isfield(loaded, 'configSignature') && ~strcmp(string(loaded.configSignature), string(cfg.configSignature))
    return;
end
if isfield(loaded, 'results')
    results = loaded.results;
end
end

function ids = get_processed_ids(results)
ids = {};
if isempty(results)
    return;
end
ids = {results.sample_id};
end

function sampleMeta = validation_row_to_sample_meta(row, cfg)
validationId = char(string(row.validation_id(1)));
shapeId = char(string(row.shape_id(1)));
sampleMeta = struct( ...
    'sample_id', string(sanitize_id([cfg.validationId '__' validationId])), ...
    'candidate_id', string(row.candidate_id(1)), ...
    'shape_id', string(shapeId), ...
    'shape_family', string(row.shape_family(1)), ...
    'shape_role', string(row.shape_role(1)), ...
    'shape_file', string(fullfile(cfg.shapeDir, [shapeId '.csv'])) ...
);
end

function pointSpec = validation_row_to_point_spec(row)
pointSpec = struct( ...
    'main_id', char(string(row.main_id(1))), ...
    'point_id', char(string(row.point_id(1))), ...
    'a1', double(row.a1(1)), 'a2', double(row.a2(1)), 'b2', double(row.b2(1)), 'r0', double(row.r0(1)), ...
    'a3', double(row.a3(1)), 'b3', double(row.b3(1)), 'a4', double(row.a4(1)), 'b4', double(row.b4(1)), 'a5', double(row.a5(1)), 'b5', double(row.b5(1)) ...
);
end

function refPoint = lookup_reference_point(baselineByPoint, pointId)
refPoint = struct();
if isempty(baselineByPoint)
    return;
end
ids = string({baselineByPoint.point_id});
idx = find(ids == string(pointId), 1, 'first');
if isempty(idx)
    error('run_stage4_validation_ab_v2:MissingBaselinePoint', 'No baseline reference found for point %s', pointId);
end
refPoint = baselineByPoint(idx);
end

function result = attach_validation_metadata(result, row)
result.validation_id = string(row.validation_id(1));
result.selection_source = string(row.selection_source(1));
result.selection_label = string(row.selection_label(1));
result.rank_within_source = double(row.rank_within_source(1));
result.source_sample_id = string(row.sample_id(1));
result.b1 = double(row.b1(1));
result.contact_prob = double(row.contact_prob(1));
result.positive_prob = double(row.positive_prob(1));
result.surrogate_pred_gap34_gain_Hz = double(row.surrogate_pred_gap34_gain_Hz(1));
result.cascade_score = double(row.cascade_score(1));
result.contact_gate = to_logical(row.contact_gate(1));
result.positive_gate = to_logical(row.positive_gate(1));
result.reg_positive_gate = to_logical(row.reg_positive_gate(1));
result.cascade_gate = to_logical(row.cascade_gate(1));
result.rank_cascade = numeric_or_nan(row.rank_cascade(1));
result.rank_surrogate = numeric_or_nan(row.rank_surrogate(1));
end

function value = to_logical(raw)
if islogical(raw)
    value = logical(raw);
elseif isnumeric(raw)
    value = raw ~= 0;
else
    text = lower(strtrim(char(string(raw))));
    value = any(strcmp(text, {'true','1','yes'}));
end
end

function value = numeric_or_nan(raw)
value = double(raw);
if isempty(value)
    value = NaN;
end
end

function results = append_result(results, result)
if isempty(results)
    results = result;
else
    results(end + 1) = result; %#ok<AGROW>
end
end

function tableOut = results_to_table(results, cfg)
if isempty(results)
    prototype = make_empty_result_struct(cfg);
    tableOut = struct2table(prototype, 'AsArray', true);
    tableOut(1, :) = [];
else
    tableOut = struct2table(results, 'AsArray', true);
end
missing = setdiff(cfg.resultFieldOrder, tableOut.Properties.VariableNames, 'stable');
prototype = make_empty_result_struct(cfg);
for i = 1:numel(missing)
    fieldName = missing{i};
    defaultValue = prototype.(fieldName);
    if islogical(defaultValue)
        tableOut.(fieldName) = false(height(tableOut), 1);
    elseif isnumeric(defaultValue)
        tableOut.(fieldName) = nan(height(tableOut), 1);
    else
        tableOut.(fieldName) = repmat(string(""), height(tableOut), 1);
    end
end
tableOut = tableOut(:, cfg.resultFieldOrder);
end

function out = make_empty_result_struct(cfg)
stringFields = { ...
    'sample_id','validation_id','selection_source','selection_label','source_sample_id', ...
    'shape_id','shape_family','shape_role','candidate_id','main_id','point_id','material_case','error_message' ...
};
logicalFields = {'contact_gate','positive_gate','reg_positive_gate','cascade_gate','geometry_valid','contact_valid','has_tiny_fragments','solve_success'};
out = struct();
for i = 1:numel(cfg.resultFieldOrder)
    fieldName = cfg.resultFieldOrder{i};
    if any(strcmp(fieldName, stringFields))
        out.(fieldName) = "";
    elseif any(strcmp(fieldName, logicalFields))
        out.(fieldName) = false;
    else
        out.(fieldName) = NaN;
    end
end
end

function summary = summarize_results(results, cfg)
summary = struct('total', numel(results), 'geometry_invalid', 0, 'no_contact', 0, 'solve_success', 0, 'positive_gain', 0);
if isempty(results)
    return;
end
geometryValid = [results.geometry_valid];
contactValid = [results.contact_valid];
solveSuccess = [results.solve_success];
gapGain = [results.gap34_gain_Hz];
summary.geometry_invalid = sum(~geometryValid);
summary.no_contact = sum(geometryValid & ~contactValid);
summary.solve_success = sum(solveSuccess);
summary.positive_gain = sum(isfinite(gapGain) & gapGain > cfg.positiveGapThresholdHz);
end

function s = sanitize_id(s)
s = char(string(s));
s = regexprep(s, '[^a-zA-Z0-9_\-]', '_');
s = regexprep(s, '_+', '_');
s = regexprep(s, '^_+|_+$', '');
if isempty(s)
    s = 'stage4_validation_sample';
end
end

function s = logical_text(v)
if v
    s = 'true';
else
    s = 'false';
end
end

function s = numeric_text(v)
if isnan(v)
    s = 'NaN';
else
    s = sprintf('%.6g', v);
end
end
