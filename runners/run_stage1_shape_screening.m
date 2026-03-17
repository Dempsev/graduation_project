import com.comsol.model.*
import com.comsol.model.util.*

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
addpath(genpath(fullfile(rootDir, 'model_core')));
addpath(genpath(fullfile(rootDir, 'stage1')));

cfg = get_stage1_config();
startIndex = 1;
maxCount = 0; % full screening run; set positive value to limit batch size

if ~exist(cfg.shapeDir, 'dir')
    error('shape_contours dir not found: %s', cfg.shapeDir);
end

shapeFiles = list_shape_files(cfg.shapeDir);
if isempty(shapeFiles)
    error('No *_contour_xy.csv found in: %s', cfg.shapeDir);
end

if maxCount <= 0
    endIndex = numel(shapeFiles);
else
    endIndex = min(numel(shapeFiles), startIndex + maxCount - 1);
end

results = load_saved_results(cfg.resultsMat);
processedIds = string(get_processed_ids(results));

fprintf('Stage-1 shape screening\n');
fprintf('Trusted mother: %s\n', cfg.fourierId);
fprintf('Material case: %s\n', cfg.materialCase);
fprintf('Shape source: %s\n', cfg.shapeDir);
fprintf('Output dir: %s\n', cfg.outDir);
fprintf('Shapes discovered: %d\n', numel(shapeFiles));
fprintf('Processing range: startIndex=%d, endIndex=%d\n', startIndex, endIndex);

baselineRef = evaluate_baseline_reference(cfg);
fprintf('Baseline gap: %.6f Hz, bands %g-%g\n', ...
    baselineRef.gap_target_Hz, baselineRef.gap_lower_band, baselineRef.gap_upper_band);

runResults = struct([]);
resumeSkipped = 0;

for i = startIndex:endIndex
    shapeFile = shapeFiles{i};
    sampleId = build_sample_id(cfg, shapeFile);
    if any(processedIds == string(sampleId))
        resumeSkipped = resumeSkipped + 1;
        fprintf('[%d/%d] resume-skip %s\n', i, endIndex, sampleId);
        continue;
    end

    fprintf('[%d/%d] evaluating %s\n', i, endIndex, shapeFile);
    result = evaluate_single_shape(cfg, shapeFile, baselineRef);
    results = append_result(results, result);
    runResults = append_result(runResults, result);

    save(cfg.resultsMat, 'results');
    resultsTable = results_to_table(results, cfg);
    writetable(resultsTable, cfg.resultsCsv);
    write_summary_tables(resultsTable, cfg);

    fprintf('  geometry_valid=%s, contact_valid=%s, solve_success=%s, gap_gain_Hz=%s\n', ...
        logical_text(result.geometry_valid), ...
        logical_text(result.contact_valid), ...
        logical_text(result.solve_success), ...
        numeric_text(result.gap_gain_Hz));
    if ~isempty(result.error_message)
        fprintf('  note=%s\n', result.error_message);
    end
end

summary = summarize_results(runResults);
allResultsTable = results_to_table(results, cfg);
write_summary_tables(allResultsTable, cfg);
generatedBandPlots = 0;
if cfg.enableBandPlots
    generatedBandPlots = generate_band_plots(allResultsTable, cfg);
end

fprintf('\nStage-1 run summary\n');
fprintf('  processed_new=%d\n', summary.total);
fprintf('  resume_skipped=%d\n', resumeSkipped);
fprintf('  geometry_invalid=%d\n', summary.geometry_invalid);
fprintf('  no_contact=%d\n', summary.no_contact);
fprintf('  solve_success=%d\n', summary.solve_success);
fprintf('  positive_shapes=%d\n', summary.positive_shapes);
fprintf('  results_csv=%s\n', cfg.resultsCsv);
fprintf('  summary_csv=%s\n', cfg.summaryByGainCsv);
fprintf('  positive_summary_csv=%s\n', cfg.positiveSummaryCsv);
fprintf('  baseline_csv=%s\n', cfg.baselineCsv);
if cfg.enableBandPlots
    fprintf('  band_plots=%d\n', generatedBandPlots);
    fprintf('  band_plot_dir=%s\n', cfg.bandPlotDir);
else
    fprintf('  band_plots=disabled\n');
end

function files = list_shape_files(shapeDir)
d = dir(fullfile(shapeDir, '*_contour_xy.csv'));
names = sort({d.name});
files = cell(size(names));
for i = 1:numel(names)
    files{i} = fullfile(shapeDir, names{i});
end
end

function results = load_saved_results(resultsMat)
results = struct([]);
if ~isfile(resultsMat)
    return;
end
loaded = load(resultsMat, 'results');
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

function sampleId = build_sample_id(cfg, shapeFile)
[~, name, ~] = fileparts(shapeFile);
sampleId = sanitize_id([cfg.fourierId '__' name]);
end

function s = sanitize_id(s)
s = char(string(s));
s = regexprep(s, '[^a-zA-Z0-9_\-]', '_');
s = regexprep(s, '_+', '_');
s = regexprep(s, '^_+|_+$', '');
if isempty(s)
    s = 'stage1_sample';
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
    tableOut = struct2table(prototype);
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
        case {'sample_id', 'fourier_id', 'shape_id', 'material_case', 'error_message'}
            out.(fieldName) = "";
        case {'geometry_valid', 'contact_valid', 'has_tiny_fragments', 'solve_success', 'is_positive_shape'}
            out.(fieldName) = false;
        otherwise
            out.(fieldName) = NaN;
    end
end
end

function write_summary_tables(resultsTable, cfg)
if isempty(resultsTable)
    writetable(resultsTable, cfg.summaryByGainCsv);
    writetable(resultsTable, cfg.positiveSummaryCsv);
    return;
end

solved = resultsTable(resultsTable.solve_success == true, :);
if isempty(solved)
    writetable(solved, cfg.summaryByGainCsv);
else
    solved.candidate_tier = classify_candidate_tier(solved, cfg);
    solved = sortrows(solved, {'gap_gain_Hz', 'gap_target_Hz'}, {'descend', 'descend'});
    writetable(solved, cfg.summaryByGainCsv);
end

positive = solved(solved.is_positive_shape == true, :);
if isempty(positive)
    writetable(positive, cfg.positiveSummaryCsv);
else
    positive = sortrows(positive, {'gap_gain_Hz', 'gap_target_Hz'}, {'descend', 'descend'});
    writetable(positive, cfg.positiveSummaryCsv);
end
end

function tiers = classify_candidate_tier(resultsTable, cfg)
n = height(resultsTable);
tiers = strings(n, 1);
for i = 1:n
    gapGain = resultsTable.gap_gain_Hz(i);
    if isnan(gapGain)
        tiers(i) = "unsolved";
    elseif gapGain >= cfg.strongPositiveGapGainHz
        tiers(i) = "strong_positive";
    elseif gapGain > cfg.weakPositiveGapGainHz
        tiers(i) = "weak_positive";
    elseif abs(gapGain) <= cfg.baselineLikeGapAbsHz
        tiers(i) = "neutral_or_baseline_like";
    else
        tiers(i) = "negative";
    end
end
end

function count = generate_band_plots(resultsTable, cfg)
count = 0;
if ~exist(cfg.bandPlotDir, 'dir')
    mkdir(cfg.bandPlotDir);
end

plotRows = resultsTable;
if cfg.bandPlotSuccessOnly
    plotRows = plotRows(plotRows.solve_success == true, :);
end
if isempty(plotRows)
    return;
end

plotScript = fullfile(cfg.rootDir, 'postprocess', 'plot_tbl1_bands.py');
for i = 1:height(plotRows)
    sampleId = char(string(plotRows.sample_id(i)));
    tbl1Path = fullfile(cfg.tbl1Dir, [sampleId '_tbl1.csv']);
    if ~isfile(tbl1Path)
        continue;
    end
    outPng = fullfile(cfg.bandPlotDir, [sampleId '_bands_all_case.png']);
    if isfile(outPng)
        continue;
    end

    cmd = sprintf('"%s" "%s" "%s" --out-dir "%s"', ...
        cfg.pythonCmd, plotScript, tbl1Path, cfg.bandPlotDir);
    [status, outText] = system(cmd);
    if status ~= 0
        warning('run_stage1_shape_screening:BandPlotFailed', ...
            'band plot failed for %s: %s', sampleId, strtrim(outText));
        continue;
    end
    count = count + 1;
end
end

function summary = summarize_results(results)
summary = struct( ...
    'total', numel(results), ...
    'geometry_invalid', 0, ...
    'no_contact', 0, ...
    'solve_success', 0, ...
    'positive_shapes', 0 ...
);
if isempty(results)
    return;
end

geometryValid = [results.geometry_valid];
contactValid = [results.contact_valid];
solveSuccess = [results.solve_success];
positive = [results.is_positive_shape];

summary.geometry_invalid = sum(~geometryValid);
summary.no_contact = sum(geometryValid & ~contactValid);
summary.solve_success = sum(solveSuccess);
summary.positive_shapes = sum(positive);
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
