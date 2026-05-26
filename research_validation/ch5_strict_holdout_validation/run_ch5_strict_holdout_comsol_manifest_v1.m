function run_ch5_strict_holdout_comsol_manifest_v1(manifestCsv, resultCsv, startIndex, endIndex)
%RUN_CH5_STRICT_HOLDOUT_COMSOL_MANIFEST_V1
% Evaluate a strict-holdout manifest with real COMSOL dispersion solves.

if nargin < 1 || strlength(string(manifestCsv)) == 0
    manifestCsv = fullfile('D:\graduation_project\coad', 'research_validation', ...
        'ch5_strict_holdout_validation', 'ch5_strict_holdout_comsol_manifest_top5_random5.csv');
end
if nargin < 2 || strlength(string(resultCsv)) == 0
    resultCsv = fullfile('D:\graduation_project\coad', 'research_validation', ...
        'ch5_strict_holdout_validation', 'ch5_strict_holdout_comsol_results_top5_random5.csv');
end
if nargin < 3 || isempty(startIndex)
    startIndex = 1;
end
if nargin < 4 || isempty(endIndex)
    endIndex = inf;
end

rootDir = 'D:\graduation_project\coad';
addpath(rootDir);
addpath(fullfile(rootDir, 'model_core'));
addpath(fullfile(rootDir, 'stage2_harmonics'));
addpath(fullfile(rootDir, 'stage2_harmonics_refine'));
addpath(fullfile(rootDir, 'optimization', 'real_comsol_ga'));
addpath(fullfile(rootDir, 'shared', 'optimization_matlab'));

manifest = readtable(manifestCsv, 'TextType', 'string', 'Delimiter', ',', 'VariableNamingRule', 'preserve');
if isinf(endIndex)
    endIndex = height(manifest);
else
    endIndex = min(double(endIndex), height(manifest));
end
startIndex = max(1, double(startIndex));

existing = table();
doneKeys = strings(0, 1);
if isfile(resultCsv)
    existing = readtable(resultCsv, 'TextType', 'string', 'Delimiter', ',', 'VariableNamingRule', 'preserve');
    if all(ismember(["candidate_id", "method"], string(existing.Properties.VariableNames)))
        doneKeys = string(existing.candidate_id) + "|" + string(existing.method);
    end
end

fprintf('CH5 strict-holdout COMSOL validation\n');
fprintf('  manifest=%s\n', manifestCsv);
fprintf('  result=%s\n', resultCsv);
fprintf('  rows=%d:%d of %d\n', startIndex, endIndex, height(manifest));

rows = existing;
for rowIndex = startIndex:endIndex
    item = manifest(rowIndex, :);
    rowKey = string(item.candidate_id(1)) + "|" + string(item.method(1));
    if any(doneKeys == rowKey)
        fprintf('[SKIP] %d %s already done\n', rowIndex, char(rowKey));
        continue;
    end

    fprintf('[RUN] %d/%d %s %s %s\n', rowIndex, height(manifest), ...
        char(string(item.target_band(1))), char(string(item.method(1))), char(string(item.candidate_id(1))));

    outRow = evaluate_one_manifest_row(rootDir, item);
    rows = append_result_row(rows, outRow);
    ensure_parent_dir(resultCsv);
    writetable(rows, resultCsv);
    doneKeys(end + 1, 1) = rowKey; %#ok<AGROW>

    fprintf('  geometry=%s contact=%s solve=%s overlap=%.6g cover=%.6g\n', ...
        logical_text(outRow.geometry_valid), logical_text(outRow.contact_valid), ...
        logical_text(outRow.solve_success), outRow.true_overlap_Hz, outRow.true_cover_ratio);
    if strlength(string(outRow.error_message)) > 0
        fprintf('  error=%s\n', char(string(outRow.error_message)));
    end
end
end

function out = evaluate_one_manifest_row(rootDir, item)
bandTag = string(item.target_band_tag(1));
bandLow = double(item.target_band_low_Hz(1));
bandHigh = double(item.target_band_high_Hz(1));

cfg = get_comsol_in_loop_ga_thesis_band_overlap_config_v1(bandTag, 1);
cfg.gaId = 'ch5_strict_holdout_validation_top5_random5';
cfg = apply_real_ga_output_layout_v1(cfg, fullfile(rootDir, 'data', 'comsol_batch', cfg.gaId));
cfg.bandCatalog = struct('bandTag', bandTag, 'bandLowHz', bandLow, 'bandHighHz', bandHigh);
cfg.bandSelectionMode = 'single_band';
cfg.fitnessMetric = 'target_overlap_Hz';
cfg.saveModel = false;
cfg.enableBandPlots = false;
ensure_dir(cfg.outDir);
ensure_dir(cfg.tbl1Dir);
ensure_dir(cfg.logsDir);
ensure_dir(cfg.plotDir);

sampleId = sanitize_id_for_ch5(string(item.candidate_id(1)));
shapeFile = string(item.shape_file(1));
if strlength(shapeFile) == 0 || ~isfile(shapeFile)
    shapeFile = string(fullfile(rootDir, 'data', 'shape_contours', char(string(item.shape_id(1)) + ".csv")));
end

sampleMeta = struct( ...
    'sample_id', sampleId, ...
    'candidate_id', string(item.candidate_id(1)), ...
    'shape_id', string(item.shape_id(1)), ...
    'shape_family', string(item.shape_family(1)), ...
    'shape_role', "strict_holdout", ...
    'shape_file', shapeFile ...
);

pointSpec = struct( ...
    'main_id', 'strict_holdout', ...
    'point_id', string(item.point_id(1)), ...
    'a1', double(item.a1(1)), 'a2', double(item.a2(1)), 'b1', double(item.b1(1)), 'b2', double(item.b2(1)), ...
    'r0', double(item.r0(1)), 'a3', double(item.a3(1)), 'b3', double(item.b3(1)), ...
    'a4', double(item.a4(1)), 'b4', double(item.b4(1)), 'a5', double(item.a5(1)), 'b5', double(item.b5(1)) ...
);

try
    result = evaluate_stage2_harmonics_refine_case_internal(cfg, sampleMeta, pointSpec, struct());
catch ME
    result = struct();
    result.geometry_valid = false;
    result.contact_valid = false;
    result.solve_success = false;
    result.error_message = "evaluate_failed: " + string(ME.message);
end

tbl1Path = fullfile(cfg.tbl1Dir, char(sampleId + "_tbl1.csv"));
metrics = extract_stage2_harmonics_refine_targetband_metrics_from_tbl1(tbl1Path, bandLow, bandHigh);

out = struct();
out.target_band = string(item.target_band(1));
out.target_band_tag = bandTag;
out.target_band_low_Hz = bandLow;
out.target_band_high_Hz = bandHigh;
out.target_band_width_Hz = double(item.target_band_width_Hz(1));
out.method = string(item.method(1));
out.validation_rank = double(item.validation_rank(1));
out.candidate_id = string(item.candidate_id(1));
out.point_id = string(item.point_id(1));
out.physical_key = string(item.physical_key(1));
out.shape_id = string(item.shape_id(1));
out.shape_family = string(item.shape_family(1));
out.a1 = double(item.a1(1));
out.a2 = double(item.a2(1));
out.b1 = double(item.b1(1));
out.b2 = double(item.b2(1));
out.a3 = double(item.a3(1));
out.b3 = double(item.b3(1));
out.a4 = double(item.a4(1));
out.b4 = double(item.b4(1));
out.a5 = double(item.a5(1));
out.b5 = double(item.b5(1));
out.r0 = double(item.r0(1));
out.predicted_open_prob = double(item.predicted_open_prob(1));
out.predicted_cover_ratio = double(item.predicted_cover_ratio(1));
out.predicted_overlap_Hz = double(item.predicted_overlap_Hz(1));
out.predicted_score = double(item.predicted_score(1));
out.geometry_valid = logical(get_result_field(result, 'geometry_valid', false));
out.contact_valid = logical(get_result_field(result, 'contact_valid', false));
out.solve_success = logical(get_result_field(result, 'solve_success', false));
out.true_gap_lower_Hz = metrics.target_gap_lower_edge_Hz;
out.true_gap_upper_Hz = metrics.target_gap_upper_edge_Hz;
out.true_overlap_Hz = metrics.target_gap_overlap_Hz;
out.true_cover_ratio = metrics.target_gap_cover_ratio;
out.active_open = metrics.target_gap_overlap_Hz > 0;
out.comsol_output_path = string(cfg.outDir);
out.tbl1_path = string(tbl1Path);
out.error_message = string(get_result_field(result, 'error_message', ""));
out.note = "";
end

function rows = append_result_row(rows, outRow)
newRow = struct2table(outRow, 'AsArray', true);
if isempty(rows)
    rows = newRow;
else
    rows = [rows; newRow]; %#ok<AGROW>
end
end

function value = get_result_field(result, fieldName, defaultValue)
if isstruct(result) && isfield(result, fieldName)
    value = result.(fieldName);
else
    value = defaultValue;
end
end

function out = sanitize_id_for_ch5(value)
out = regexprep(string(value), '[^A-Za-z0-9_]+', '_');
out = regexprep(out, '_+', '_');
if strlength(out) > 79
    out = extractBefore(out, 80);
end
if strlength(out) == 0
    out = "ch5_strict_sample";
end
end

function ensure_dir(pathStr)
if ~exist(pathStr, 'dir')
    mkdir(pathStr);
end
end

function ensure_parent_dir(pathStr)
parent = fileparts(pathStr);
if ~exist(parent, 'dir')
    mkdir(parent);
end
end

function out = logical_text(value)
if islogical(value)
    tf = value;
elseif isnumeric(value)
    tf = value ~= 0;
else
    tf = any(strcmpi(string(value), ["true", "1"]));
end
if tf
    out = 'true';
else
    out = 'false';
end
end
