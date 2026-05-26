function run_ch2_typical_local_perturb_validation_v1(startIndex, maxCount)
%RUN_CH2_TYPICAL_LOCAL_PERTURB_VALIDATION_V1
% Run COMSOL truth evaluations for Chapter 2.6 typical local perturbations.

import com.comsol.model.*
import com.comsol.model.util.*

if nargin < 1 || isempty(startIndex)
    startIndex = 1;
end
if nargin < 2 || isempty(maxCount)
    maxCount = 0;
end

rootDir = fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(rootDir, 'model_core'));
addpath(fullfile(rootDir, 'stage2_harmonics'));
addpath(fullfile(rootDir, 'stage2_harmonics_refine'));
addpath(fullfile(rootDir, 'optimization', 'real_comsol_ga'));
addpath(fullfile(rootDir, 'shared', 'optimization_matlab'));

dataDir = fullfile(rootDir, 'data', 'research_validation', 'ch2_typical_dispersion');
manifestCsv = fullfile(dataDir, 'ch2_typical_local_perturb_manifest_v1.csv');
resultsCsv = fullfile(dataDir, 'ch2_typical_local_perturb_results_v1.csv');
resultsMat = fullfile(dataDir, 'ch2_typical_local_perturb_results_v1.mat');
if ~isfile(manifestCsv)
    error('run_ch2_typical_local_perturb_validation_v1:MissingManifest', 'Missing manifest: %s', manifestCsv);
end

cfg = get_stage2_harmonics_refine_config();
cfg.outDir = dataDir;
cfg.tbl1Dir = fullfile(dataDir, 'tbl1_exports');
cfg.logsDir = fullfile(dataDir, 'logs');
cfg.modelsDir = fullfile(dataDir, 'models');
cfg.plotDir = fullfile(dataDir, 'figures');
cfg.saveModel = false;
cfg.enableBandPlots = false;
ensure_dir(cfg.tbl1Dir);
ensure_dir(cfg.logsDir);
ensure_dir(cfg.plotDir);

manifest = readtable(manifestCsv, 'TextType', 'string', 'Delimiter', ',', 'VariableNamingRule', 'preserve');
endIndex = height(manifest);
if maxCount > 0
    endIndex = min(endIndex, startIndex + maxCount - 1);
end

results = struct([]);
if isfile(resultsMat)
    loaded = load(resultsMat, 'results');
    if isfield(loaded, 'results')
        results = loaded.results;
    end
end
processed = string({});
if ~isempty(results)
    processed = string({results.sample_id});
end

fprintf('Chapter 2.6 typical local perturbation validation\n');
fprintf('  manifest=%s\n', manifestCsv);
fprintf('  out_dir=%s\n', dataDir);
fprintf('  rows=%d, range=%d:%d\n', height(manifest), startIndex, endIndex);

for i = startIndex:endIndex
    row = manifest(i, :);
    sampleId = sanitize_sample_id(sprintf('ch2_typical__%s__%s', row.case_id(1), row.variant(1)));
    if any(processed == string(sampleId))
        fprintf('  [%d/%d] resume-skip %s\n', i, height(manifest), sampleId);
        continue;
    end

    pointSpec = table_row_to_point_spec(row);
    sampleMeta = struct( ...
        'sample_id', string(sampleId), ...
        'candidate_id', string(row.variant(1)), ...
        'shape_id', string(row.shape_id(1)), ...
        'shape_family', string(row.shape_family(1)), ...
        'shape_role', "global_shape_pool", ...
        'shape_file', string(row.shape_file(1)) ...
    );

    fprintf('  [%d/%d] %s band=%s shape=%s variant=%s\n', ...
        i, height(manifest), sampleId, row.target_band_tag(1), row.shape_id(1), row.variant(1));
    result = evaluate_stage2_harmonics_refine_case_internal(cfg, sampleMeta, pointSpec, struct());
    result = attach_ch2_metadata(result, row, sampleId, cfg);
    results = append_result(results, result);
    processed(end + 1, 1) = string(sampleId); %#ok<AGROW>

    save(resultsMat, 'results');
    writetable(struct2table(results, 'AsArray', true), resultsCsv);
    fprintf('      geometry=%d contact=%d solve=%d cover=%.6g overlap=%.6g gap=%.6g\n', ...
        result.geometry_valid, result.contact_valid, result.solve_success, ...
        result.cover_ratio, result.target_overlap_Hz, result.gap34_Hz);
    if strlength(string(result.failure_reason)) > 0
        fprintf('      note=%s\n', result.failure_reason);
    end
end
end

function pointSpec = table_row_to_point_spec(row)
pointSpec = struct( ...
    'main_id', char(string(row.main_id(1))), ...
    'point_id', char(string(row.point_id(1))), ...
    'a1', double(row.a1(1)), ...
    'a2', double(row.a2(1)), ...
    'b1', double(row.b1(1)), ...
    'b2', double(row.b2(1)), ...
    'r0', double(row.r0(1)), ...
    'a3', double(row.a3(1)), ...
    'b3', double(row.b3(1)), ...
    'a4', double(row.a4(1)), ...
    'b4', double(row.b4(1)), ...
    'a5', double(row.a5(1)), ...
    'b5', double(row.b5(1)) ...
);
end

function result = attach_ch2_metadata(result, row, sampleId, cfg)
targetLow = double(row.target_band_low_Hz(1));
targetHigh = double(row.target_band_high_Hz(1));
tbl1Path = fullfile(cfg.tbl1Dir, [sampleId '_tbl1.csv']);
target = extract_stage2_harmonics_refine_targetband_metrics_from_tbl1(tbl1Path, targetLow, targetHigh);

result.case_id = string(row.case_id(1));
result.target_band = string(row.target_band_tag(1));
result.target_band_low_Hz = targetLow;
result.target_band_high_Hz = targetHigh;
result.structure_id = string(row.structure_id(1));
result.variant = string(row.variant(1));
result.perturb_param = string(row.perturb_param(1));
result.perturb_direction = string(row.perturb_direction(1));
result.perturb_value = double(row.perturb_value(1));
result.band_lower_Hz = result.gap34_lower_edge_Hz;
result.band_upper_Hz = result.gap34_upper_edge_Hz;
result.target_overlap_Hz = target.target_gap_overlap_Hz;
result.cover_ratio = target.target_gap_cover_ratio;
result.target_gap_lower_band = target.target_gap_lower_band;
result.target_gap_upper_band = target.target_gap_upper_band;
result.tbl1_csv = string(tbl1Path);
result.shape_file = string(row.shape_file(1));
result.failure_reason = string(result.error_message);
if ~result.geometry_valid
    result.failure_reason = "geometry_invalid";
elseif ~result.contact_valid
    result.failure_reason = "contact_invalid";
elseif ~result.solve_success && strlength(result.failure_reason) == 0
    result.failure_reason = "solve_failed";
end
end

function results = append_result(results, result)
if isempty(results)
    results = result;
else
    results(end + 1) = result;
end
end

function id = sanitize_sample_id(raw)
id = regexprep(char(string(raw)), '[^a-zA-Z0-9_\-]', '_');
end

function ensure_dir(pathStr)
if ~exist(pathStr, 'dir')
    mkdir(pathStr);
end
end
