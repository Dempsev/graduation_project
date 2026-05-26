function summary = run_ch2_mesh_independence_validation_v1()
%RUN_CH2_MESH_INDEPENDENCE_VALIDATION_V1
% Reproducible Chapter 2 mesh-independence validation for the COAD thesis.

import com.comsol.model.*
import com.comsol.model.util.*

rootDir = fileparts(fileparts(mfilename('fullpath')));
addpath(fullfile(rootDir, 'model_core'));
addpath(fullfile(rootDir, 'stage2_harmonics'));
addpath(fullfile(rootDir, 'stage2_harmonics_refine'));
addpath(fullfile(rootDir, 'optimization', 'real_comsol_ga'));
addpath(fullfile(rootDir, 'shared', 'optimization_matlab'));

outDir = fullfile(rootDir, 'data', 'research_validation', 'ch2_mesh_reliability_v1');
plotDir = fullfile(outDir, 'figures');
meshDir = fullfile(plotDir, 'mesh');
ensure_dir(outDir);
ensure_dir(plotDir);
ensure_dir(meshDir);

cfg = get_stage2_harmonics_refine_config();
cfg.outDir = outDir;
cfg.tbl1Dir = fullfile(outDir, 'tbl1_exports');
cfg.modelsDir = fullfile(outDir, 'models');
cfg.logsDir = fullfile(outDir, 'logs');
cfg.plotDir = plotDir;
cfg.bandPlotDir = plotDir;
cfg.saveModel = false;
cfg.enableBandPlots = false;
ensure_dir(cfg.tbl1Dir);
ensure_dir(cfg.logsDir);

sample = select_validation_sample(rootDir);
meshSpecs = [
    make_mesh_spec("coarse", "Coarse", 7)
    make_mesh_spec("medium", "Normal", 5)
    make_mesh_spec("fine", "Finer", 3)
];

rows = struct([]);
for i = 1:numel(meshSpecs)
    rows = append_struct(rows, run_one_mesh_case(cfg, sample, meshSpecs(i), meshDir));
end

fineGap = rows(end).gap34_Hz;
for i = 1:numel(rows)
    if isfinite(fineGap) && fineGap ~= 0
        rows(i).relative_error_percent = abs(rows(i).gap34_Hz - fineGap) ./ abs(fineGap) .* 100;
    else
        rows(i).relative_error_percent = NaN;
    end
end

resultTable = struct2table(rows, 'AsArray', true);
resultCsv = fullfile(outDir, 'mesh_independence_results_v1.csv');
writetable(resultTable, resultCsv);

sampleTable = struct2table(sample, 'AsArray', true);
sampleCsv = fullfile(outDir, 'mesh_validation_sample_v1.csv');
writetable(sampleTable, sampleCsv);

dispersionPath = fullfile(plotDir, 'mesh_dispersion_overlay_v1.png');
convergencePath = fullfile(plotDir, 'mesh_gap_convergence_v1.png');
plot_dispersion_overlay(resultTable, dispersionPath);
plot_convergence(resultTable, convergencePath);

summary = struct();
summary.output_dir = outDir;
summary.sample_csv = sampleCsv;
summary.result_csv = resultCsv;
summary.dispersion_plot = dispersionPath;
summary.convergence_plot = convergencePath;
summary.sample = sample;
summary.rows = rows;

summaryJson = fullfile(outDir, 'mesh_independence_summary_v1.json');
write_json(summaryJson, summary);
fprintf('Mesh-independence validation complete:\n  %s\n', outDir);
end

function spec = make_mesh_spec(tag, label, autoMeshSize)
spec = struct();
spec.mesh_level = char(tag);
spec.mesh_label = char(label);
spec.auto_mesh_size = double(autoMeshSize);
end

function sample = select_validation_sample(rootDir)
historyFiles = dir(fullfile(rootDir, 'data', 'comsol_batch', 'comsol_in_loop_thesis_*_overlap_ga_v1', 'ga_history_v1.csv'));
best = struct();
bestScore = -inf;
for i = 1:numel(historyFiles)
    path = fullfile(historyFiles(i).folder, historyFiles(i).name);
    t = readtable(path, 'TextType', 'string', 'Delimiter', ',', 'VariableNamingRule', 'preserve');
    if isempty(t)
        continue;
    end
    for r = 1:height(t)
        if ~is_good_history_row(t(r, :))
            continue;
        end
        score = value_or_nan(t.gap34_Hz(r));
        if score > bestScore
            bestScore = score;
            best = table_row_to_sample(t(r, :), path);
        end
    end
end
if isempty(fieldnames(best))
    error('run_ch2_mesh_independence_validation_v1:NoSample', ...
        'No valid sample with positive gap34_Hz was found in thesis GA history files.');
end
sample = best;
end

function tf = is_good_history_row(row)
tf = logical_value(row.geometry_valid(1)) && logical_value(row.contact_valid(1)) && logical_value(row.solve_success(1));
if ~tf
    return;
end
gap = value_or_nan(row.gap34_Hz(1));
tf = isfinite(gap) && gap > 0;
if tf && ismember('shape_file', row.Properties.VariableNames)
    tf = isfile(char(string(row.shape_file(1))));
end
end

function sample = table_row_to_sample(row, sourcePath)
sample = struct();
names = {'sample_id','shape_id','shape_family','shape_role','main_id','point_id','shape_file','active_band_tag'};
for i = 1:numel(names)
    name = names{i};
    if ismember(name, row.Properties.VariableNames)
        sample.(name) = string(row.(name)(1));
    else
        sample.(name) = "";
    end
end
sample.source_history_csv = string(sourcePath);
sample.a1 = value_or_nan(row.a1(1));
sample.a2 = value_or_nan(row.a2(1));
sample.b1 = value_or_nan(row.b1(1));
sample.b2 = value_or_nan(row.b2(1));
sample.r0 = value_or_nan(row.r0(1));
sample.a3 = value_or_nan(row.a3(1));
sample.b3 = value_or_nan(row.b3(1));
sample.a4 = value_or_nan(row.a4(1));
sample.b4 = value_or_nan(row.b4(1));
sample.a5 = value_or_nan(row.a5(1));
sample.b5 = value_or_nan(row.b5(1));
sample.original_gap34_Hz = value_or_nan(row.gap34_Hz(1));
sample.original_gap34_rel = value_or_nan(row.gap34_rel(1));
sample.target_band_low_Hz = value_or_nan(row.active_band_low_Hz(1));
sample.target_band_high_Hz = value_or_nan(row.active_band_high_Hz(1));
end

function row = run_one_mesh_case(cfg, sample, meshSpec, meshDir)
import com.comsol.model.util.*
ModelUtil.clear;
sampleId = sprintf('ch2_mesh_%s__%s', meshSpec.mesh_level, char(sample.shape_id));
pointSpec = struct( ...
    'main_id', char(sample.main_id), ...
    'point_id', char(sample.point_id), ...
    'a1', sample.a1, 'a2', sample.a2, 'b1', sample.b1, 'b2', sample.b2, 'r0', sample.r0, ...
    'a3', sample.a3, 'b3', sample.b3, 'a4', sample.a4, 'b4', sample.b4, ...
    'a5', sample.a5, 'b5', sample.b5);

[geometryReport, model] = validate_stage2_harmonics_geometry(cfg, pointSpec, char(sample.shape_file), sampleId);
if ~geometryReport.geometry_valid || ~geometryReport.contact_valid
    error('run_ch2_mesh_independence_validation_v1:InvalidGeometry', ...
        'Selected sample became invalid during mesh validation: %s', geometryReport.error_message);
end

model = set_material_03(model, cfg);
model = set_physics_04(model);
model = apply_mesh_control(model, meshSpec);
meshStats = safe_mesh_stats(model);

model = set_study_06(model);
solveTimer = tic;
try
    model.batch('p2').run('compute');
catch MEComp
    warning('run_ch2_mesh_independence_validation_v1:BatchFallback', ...
        'batch compute failed for %s, fallback to study.run: %s', sampleId, MEComp.message);
    model.study('std1').run;
end
solveSeconds = toc(solveTimer);

model = set_results_07(model);
tbl1Path = fullfile(cfg.tbl1Dir, [sampleId '_tbl1.csv']);
if ~isfile(tbl1Path)
    error('run_ch2_mesh_independence_validation_v1:MissingTbl1', 'Expected tbl1 export not found: %s', tbl1Path);
end

gapMetrics = extract_stage2_harmonics_refine_gap_metrics_from_tbl1(tbl1Path, cfg.fixedGapBand);
targetMetrics = extract_stage2_harmonics_refine_targetband_metrics_from_tbl1( ...
    tbl1Path, sample.target_band_low_Hz, sample.target_band_high_Hz);
meshPng = fullfile(meshDir, [sampleId '_mesh.png']);
export_mesh_png(model, meshPng, meshSpec);

row = struct();
row.sample_id = string(sampleId);
row.source_sample_id = sample.sample_id;
row.shape_id = sample.shape_id;
row.shape_file = sample.shape_file;
row.mesh_level = string(meshSpec.mesh_level);
row.mesh_label = string(meshSpec.mesh_label);
row.auto_mesh_size = meshSpec.auto_mesh_size;
row.element_count = meshStats.element_count;
row.vertex_count = meshStats.vertex_count;
row.dof_count = meshStats.dof_count;
row.solve_time_s = solveSeconds;
row.total_time_s = solveSeconds;
row.memory_mb = NaN;
row.gap34_lower_edge_Hz = gapMetrics.gap34_lower_edge_Hz;
row.gap34_upper_edge_Hz = gapMetrics.gap34_upper_edge_Hz;
row.gap34_Hz = gapMetrics.gap34_Hz;
row.gap34_rel = gapMetrics.gap34_rel;
row.target_overlap_Hz = targetMetrics.target_gap_overlap_Hz;
row.cover_ratio = targetMetrics.target_gap_cover_ratio;
row.target_gap_lower_edge_Hz = targetMetrics.target_gap_lower_edge_Hz;
row.target_gap_upper_edge_Hz = targetMetrics.target_gap_upper_edge_Hz;
row.relative_error_percent = NaN;
row.tbl1_csv = string(tbl1Path);
row.mesh_png = string(meshPng);
row.error_message = "";
fprintf('  mesh=%s elements=%g gap34=%.9g rel=%.9g time=%.2fs\n', ...
    meshSpec.mesh_level, row.element_count, row.gap34_Hz, row.gap34_rel, solveSeconds);
end

function model = apply_mesh_control(model, meshSpec)
if isempty(model.component('comp1').mesh.tags)
    model.component('comp1').mesh.create('mesh1');
end
mesh = model.component('comp1').mesh('mesh1');
try
    mesh.autoMeshSize(meshSpec.auto_mesh_size);
catch
end
try
    mesh.run;
catch
    model.component('comp1').mesh('mesh1').run;
end
end

function statsOut = safe_mesh_stats(model)
statsOut = struct('element_count', NaN, 'vertex_count', NaN, 'dof_count', NaN);
try
    s = mphmeshstats(model, 'mesh1');
    statsOut.element_count = first_numeric_field(s, {'numelem','nelem','numElem','elements','numtri','numtet'});
    statsOut.vertex_count = first_numeric_field(s, {'numvertex','numvertices','numVert','vertices','numNode','numnode'});
catch
end
try
    info = mphsolinfo(model, 'soltag', 'sol2');
    statsOut.dof_count = first_numeric_field(info, {'ndofs','nDofs','numdofs','sizes'});
catch
end
end

function value = first_numeric_field(s, candidates)
value = NaN;
for i = 1:numel(candidates)
    name = candidates{i};
    if isfield(s, name) && isnumeric(s.(name)) && ~isempty(s.(name))
        vals = double(s.(name)(:));
        vals = vals(isfinite(vals));
        if ~isempty(vals)
            value = sum(vals);
            return;
        end
    end
end
fields = fieldnames(s);
for i = 1:numel(fields)
    v = s.(fields{i});
    if isnumeric(v) && ~isempty(v)
        vals = double(v(:));
        vals = vals(isfinite(vals));
        if ~isempty(vals) && max(vals) > 10
            value = sum(vals);
            return;
        end
    end
end
end

function export_mesh_png(model, outPath, meshSpec)
try
    fig = figure('Visible', 'off', 'Color', 'w');
    mphmesh(model, 'mesh1');
    axis equal tight;
    title(sprintf('%s mesh', meshSpec.mesh_label), 'Interpreter', 'none');
    exportgraphics(fig, outPath, 'Resolution', 220);
    close(fig);
catch ME
    warning('run_ch2_mesh_independence_validation_v1:MeshPngFailed', ...
        'Failed to export mesh PNG: %s', ME.message);
end
end

function plot_dispersion_overlay(resultTable, outPath)
fig = figure('Visible', 'off', 'Color', 'w');
hold on;
colors = lines(height(resultTable));
for i = 1:height(resultTable)
    [kVals, bandMatrix] = read_band_matrix(char(resultTable.tbl1_csv(i)));
    maxBands = min(size(bandMatrix, 2), 8);
    for b = 1:maxBands
        plot(kVals, bandMatrix(:, b), '-', 'Color', colors(i, :), 'LineWidth', 0.7);
    end
end
fine = resultTable(end, :);
if isfinite(fine.gap34_lower_edge_Hz) && isfinite(fine.gap34_upper_edge_Hz)
    yline(fine.gap34_lower_edge_Hz, '--k', 'gap34 lower', 'LabelHorizontalAlignment', 'left');
    yline(fine.gap34_upper_edge_Hz, '--k', 'gap34 upper', 'LabelHorizontalAlignment', 'left');
end
xlabel('k path parameter');
ylabel('Frequency (Hz)');
title('Mesh dispersion comparison', 'Interpreter', 'none');
legend(cellstr(resultTable.mesh_level), 'Location', 'best');
grid on;
exportgraphics(fig, outPath, 'Resolution', 220);
close(fig);
end

function plot_convergence(resultTable, outPath)
fig = figure('Visible', 'off', 'Color', 'w');
x = resultTable.element_count;
if any(~isfinite(x))
    x = (1:height(resultTable))';
    xLabel = 'Mesh level';
else
    xLabel = 'Element count';
end
yyaxis left;
plot(x, resultTable.gap34_Hz, '-o', 'LineWidth', 1.2);
ylabel('gap34 (Hz)');
yyaxis right;
plot(x, resultTable.relative_error_percent, '-s', 'LineWidth', 1.2);
ylabel('Relative error (%)');
xlabel(xLabel);
title('Mesh convergence of gap34', 'Interpreter', 'none');
grid on;
exportgraphics(fig, outPath, 'Resolution', 220);
close(fig);
end

function [uniqueK, bandMatrix] = read_band_matrix(tbl1Path)
raw = readcell(tbl1Path, 'Delimiter', ',');
kVals = [];
freqVals = [];
for i = 1:size(raw, 1)
    if size(raw, 2) < 3
        continue;
    end
    k = numeric_cell(raw{i, 1});
    freq = numeric_cell(raw{i, end});
    if isfinite(k) && isfinite(freq)
        kVals(end + 1, 1) = k; %#ok<AGROW>
        freqVals(end + 1, 1) = freq; %#ok<AGROW>
    end
end
[uniqueK, ~, idx] = unique(kVals, 'sorted');
maxBands = 0;
bands = cell(numel(uniqueK), 1);
for i = 1:numel(uniqueK)
    f = sort(freqVals(idx == i));
    bands{i} = f(:);
    maxBands = max(maxBands, numel(f));
end
bandMatrix = nan(numel(uniqueK), maxBands);
for i = 1:numel(uniqueK)
    f = bands{i};
    bandMatrix(i, 1:numel(f)) = f;
end
end

function value = numeric_cell(x)
value = NaN;
if isnumeric(x) && isscalar(x)
    value = double(real(x));
    return;
end
if ismissing(x)
    return;
end
s = char(string(x));
if startsWith(strtrim(s), '%')
    return;
end
try
    parsed = str2num(s); %#ok<ST2NM>
    if ~isempty(parsed)
        value = double(real(parsed(1)));
    end
catch
end
end

function tf = logical_value(v)
if islogical(v)
    tf = logical(v);
elseif isnumeric(v)
    tf = isfinite(v) && v ~= 0;
else
    s = lower(strtrim(string(v)));
    tf = s == "1" || s == "true";
end
end

function value = value_or_nan(v)
if isnumeric(v)
    value = double(v(1));
else
    value = str2double(string(v(1)));
end
if isempty(value) || ~isfinite(value)
    value = NaN;
end
end

function rows = append_struct(rows, row)
if isempty(rows)
    rows = row;
else
    rows(end + 1) = row;
end
end

function ensure_dir(pathStr)
if ~exist(pathStr, 'dir')
    mkdir(pathStr);
end
end

function write_json(pathStr, payload)
fid = fopen(pathStr, 'w');
if fid < 0
    error('run_ch2_mesh_independence_validation_v1:JsonOpenFailed', 'Cannot write %s', pathStr);
end
cleanupObj = onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid, '%s', jsonencode(payload, 'PrettyPrint', true));
end
