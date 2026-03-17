import com.comsol.model.*
import com.comsol.model.util.*

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
addpath(genpath(fullfile(rootDir, 'model_core')));
addpath(genpath(fullfile(rootDir, 'stage2')));

cfg = get_stage2_config();
startCandidateIndex = 1;
maxCandidateCount = 0; % set positive value to limit the candidate subset
startPointIndex = 1;
maxPointCount = 0; % set positive value to limit the DOE subset

candidateTable = generate_stage2_candidate_manifest(cfg);
doeTable = get_stage2_doe_points(cfg);

if isempty(candidateTable)
    error('run_stage2_fourier_robustness_screening:EmptyCandidates', ...
        'No stage-2 candidates were generated from %s', cfg.stage1SummaryCsv);
end
if isempty(doeTable)
    error('run_stage2_fourier_robustness_screening:EmptyDoe', 'Stage-2 DOE is empty.');
end

candidateEndIndex = resolve_end_index(height(candidateTable), startCandidateIndex, maxCandidateCount);
pointEndIndex = resolve_end_index(height(doeTable), startPointIndex, maxPointCount);
activeCandidates = candidateTable(startCandidateIndex:candidateEndIndex, :);
activePoints = doeTable(startPointIndex:pointEndIndex, :);

results = load_saved_results(cfg.resultsMat, cfg);
processedIds = string(get_processed_ids(results));

fprintf('Stage-2 Fourier robustness screening\n');
fprintf('Fourier mother: %s\n', cfg.fourierId);
fprintf('Material case: %s\n', cfg.materialCase);
fprintf('Stage-1 summary: %s\n', cfg.stage1SummaryCsv);
fprintf('Output dir: %s\n', cfg.outDir);
fprintf('Candidates discovered: %d\n', height(candidateTable));
fprintf('DOE points discovered: %d\n', height(doeTable));
fprintf('Candidate range: startIndex=%d, endIndex=%d\n', startCandidateIndex, candidateEndIndex);
fprintf('DOE range: startIndex=%d, endIndex=%d\n', startPointIndex, pointEndIndex);

baselineByPoint = evaluate_stage2_baseline_points(cfg, doeTable);
runResults = struct([]);
resumeSkipped = 0;
totalTasks = height(activeCandidates) * height(activePoints);
taskCounter = 0;

for i = 1:height(activeCandidates)
    candidateRow = activeCandidates(i, :);
    candidateStruct = candidate_row_to_struct(candidateRow);
    fprintf('\nCandidate [%d/%d] %s (%s, family=%s)\n', ...
        i, height(activeCandidates), char(string(candidateStruct.shape_id)), ...
        char(string(candidateStruct.candidate_role)), char(string(candidateStruct.shape_family)));

    for j = 1:height(activePoints)
        taskCounter = taskCounter + 1;
        pointSpec = point_row_to_struct(activePoints(j, :));
        sampleId = build_sample_id(cfg, candidateStruct, pointSpec);
        if any(processedIds == string(sampleId))
            resumeSkipped = resumeSkipped + 1;
            fprintf('  [%d/%d] resume-skip %s\n', taskCounter, totalTasks, sampleId);
            continue;
        end

        refPoint = lookup_reference_point(baselineByPoint, pointSpec.point_id);
        fprintf('  [%d/%d] point=%s a1=%.3f a2=%.3f b2=%.3f r0=%.4f\n', ...
            taskCounter, totalTasks, pointSpec.point_id, pointSpec.a1, pointSpec.a2, pointSpec.b2, pointSpec.r0);
        result = evaluate_stage2_single_sample(cfg, candidateStruct, pointSpec, refPoint);
        results = append_result(results, result);
        runResults = append_result(runResults, result);
        processedIds(end + 1, 1) = string(result.sample_id); %#ok<AGROW>

        configSignature = cfg.configSignature; %#ok<NASGU>
        save(cfg.resultsMat, 'results', 'configSignature');
        resultsTable = results_to_table(results, cfg);
        writetable(resultsTable, cfg.resultsCsv);
        write_stage2_summary_tables(resultsTable, cfg);

        fprintf('    geometry_valid=%s, contact_valid=%s, solve_success=%s, gap_gain_Hz=%s\n', ...
            logical_text(result.geometry_valid), ...
            logical_text(result.contact_valid), ...
            logical_text(result.solve_success), ...
            numeric_text(result.gap_gain_Hz));
        if ~isempty(result.error_message)
            fprintf('    note=%s\n', result.error_message);
        end
    end
end

summary = summarize_results(runResults, cfg);
allResultsTable = results_to_table(results, cfg);
write_stage2_summary_tables(allResultsTable, cfg);

fprintf('\nStage-2 run summary\n');
fprintf('  processed_new=%d\n', summary.total);
fprintf('  resume_skipped=%d\n', resumeSkipped);
fprintf('  geometry_invalid=%d\n', summary.geometry_invalid);
fprintf('  no_contact=%d\n', summary.no_contact);
fprintf('  solve_success=%d\n', summary.solve_success);
fprintf('  positive_gain=%d\n', summary.positive_gain);
fprintf('  results_csv=%s\n', cfg.resultsCsv);
fprintf('  shape_summary_csv=%s\n', cfg.shapeSummaryCsv);
fprintf('  point_summary_csv=%s\n', cfg.pointSummaryCsv);
fprintf('  candidate_manifest_csv=%s\n', cfg.candidateManifestCsv);
fprintf('  doe_manifest_csv=%s\n', cfg.doeManifestCsv);
fprintf('  baseline_by_point_csv=%s\n', cfg.baselineByPointCsv);
fprintf('  band_plots=disabled\n');

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

function candidate = candidate_row_to_struct(row)
candidate = struct( ...
    'candidate_id', string(row.candidate_id(1)), ...
    'shape_id', string(row.shape_id(1)), ...
    'shape_file', string(row.shape_file(1)), ...
    'shape_family', string(row.shape_family(1)), ...
    'candidate_role', string(row.candidate_role(1)) ...
);
end

function pointSpec = point_row_to_struct(row)
pointSpec = struct( ...
    'point_id', char(string(row.point_id(1))), ...
    'a1', double(row.a1(1)), ...
    'a2', double(row.a2(1)), ...
    'b2', double(row.b2(1)), ...
    'r0', double(row.r0(1)) ...
);
end

function sampleId = build_sample_id(cfg, candidateStruct, pointSpec)
sampleId = sanitize_id([cfg.fourierId '__' char(string(candidateStruct.candidate_id)) '__' pointSpec.point_id]);
end

function refPoint = lookup_reference_point(baselineByPoint, pointId)
refPoint = struct();
if isempty(baselineByPoint)
    return;
end
ids = string({baselineByPoint.point_id});
idx = find(ids == string(pointId), 1, 'first');
if isempty(idx)
    error('run_stage2_fourier_robustness_screening:MissingBaselinePoint', ...
        'No baseline reference found for point %s', pointId);
end
refPoint = baselineByPoint(idx);
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
out = struct();
for i = 1:numel(cfg.resultFieldOrder)
    fieldName = cfg.resultFieldOrder{i};
    switch fieldName
        case {'sample_id', 'candidate_id', 'shape_id', 'shape_family', 'candidate_role', 'point_id', 'material_case', 'error_message'}
            out.(fieldName) = "";
        case {'geometry_valid', 'contact_valid', 'has_tiny_fragments', 'solve_success'}
            out.(fieldName) = false;
        otherwise
            out.(fieldName) = NaN;
    end
end
end

function summary = summarize_results(results, cfg)
summary = struct( ...
    'total', numel(results), ...
    'geometry_invalid', 0, ...
    'no_contact', 0, ...
    'solve_success', 0, ...
    'positive_gain', 0 ...
);
if isempty(results)
    return;
end

geometryValid = [results.geometry_valid];
contactValid = [results.contact_valid];
solveSuccess = [results.solve_success];
gapGain = [results.gap_gain_Hz];

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
    s = 'stage2_sample';
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



