function manifestPath = export_ch4_best_unit_cell_comsol_geometry_v1(bandTags, workerName)
%EXPORT_CH4_BEST_UNIT_CELL_COMSOL_GEOMETRY_V1 Export complete COMSOL unit-cell geometry.
%
% This rebuilds only the geometry of the best GA candidate for each target
% band. It does not run the COMSOL eigenfrequency study.

if nargin < 1 || isempty(bandTags)
    bandTags = {'band140_180','band160_200','band180_220','band200_240','band220_260','band240_280'};
end
if nargin < 2 || isempty(workerName)
    workerName = 'single';
end
if isstring(bandTags)
    bandTags = cellstr(bandTags);
end

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(fileparts(thisDir));
addpath(fullfile(rootDir, 'model_core'));
addpath(fullfile(rootDir, 'stage2_harmonics'));
addpath(fullfile(rootDir, 'stage2_harmonics_refine'));
addpath(fullfile(rootDir, 'optimization', 'real_comsol_ga'));
addpath(fullfile(rootDir, 'shared', 'optimization_matlab'));

baseDir = fullfile(rootDir, 'research_validation', 'ch4_ga_real_optimization');
figDir = fullfile(baseDir, 'figures');
workDir = fullfile(baseDir, 'comsol_unit_cell_export_work');
if ~exist(figDir, 'dir'); mkdir(figDir); end
if ~exist(workDir, 'dir'); mkdir(workDir); end

summaryPath = fullfile(baseDir, 'ch4_ga_summary_20gen.csv');
summary = readtable(summaryPath, 'TextType', 'string', 'Delimiter', ',', 'VariableNamingRule', 'preserve');

n = numel(bandTags);
records = repmat(empty_record(), n, 1);

for i = 1:n
    tag = string(bandTags{i});
    fprintf('[%s] exporting %s\n', char(string(workerName)), char(tag));
    try
        records(i) = export_one_band(summary, tag, rootDir, figDir, workDir);
    catch ME
        rec = empty_record();
        rec.target_band_tag = tag;
        rec.status = "failed";
        rec.error_message = string(ME.message);
        records(i) = rec;
        warning('export_ch4_best_unit_cell_comsol_geometry_v1:Failed', ...
            'Failed to export %s: %s', char(tag), ME.message);
    end
end

manifest = struct2table(records);
manifestPath = fullfile(figDir, sprintf('ch4_fig4_6_comsol_unit_cell_export_manifest_%s.csv', sanitize_id(workerName)));
writetable(manifest, manifestPath);
fprintf('[MANIFEST] %s\n', manifestPath);
end

function rec = export_one_band(summary, tag, rootDir, figDir, workDir)
rec = empty_record();
rec.target_band_tag = tag;

idx = find(summary.target_band_tag == tag, 1);
if isempty(idx)
    error('Target band not found in summary: %s', char(tag));
end

summaryRow = summary(idx, :);
outDir = char(summaryRow.output_dir(1));
historyPath = fullfile(outDir, 'ga_history_v1.csv');
if ~isfile(historyPath)
    error('Missing GA history: %s', historyPath);
end

history = readtable(historyPath, 'TextType', 'string', 'Delimiter', ',', 'VariableNamingRule', 'preserve');
sampleId = string(summaryRow.best_sample_id(1));
rowIdx = find(history.sample_id == sampleId, 1);
if isempty(rowIdx)
    [~, rowIdx] = max(double(history.active_target_overlap_Hz));
end
row = history(rowIdx, :);

pointSpec = struct( ...
    'main_id', char(string(row.main_id(1))), ...
    'point_id', char(string(row.point_id(1))), ...
    'a1', double(row.a1(1)), ...
    'a2', double(row.a2(1)), ...
    'b1', get_numeric_field(row, 'b1', 0), ...
    'b2', double(row.b2(1)), ...
    'r0', double(row.r0(1)), ...
    'a3', double(row.a3(1)), ...
    'b3', double(row.b3(1)), ...
    'a4', double(row.a4(1)), ...
    'b4', double(row.b4(1)), ...
    'a5', double(row.a5(1)), ...
    'b5', double(row.b5(1)) ...
);

shapeFile = char(string(row.shape_file(1)));
cfg = get_comsol_in_loop_ga_config_v1();
cfg.outDir = fullfile(workDir, char(tag));
cfg.tbl1Dir = fullfile(cfg.outDir, 'tbl1_exports');
cfg.logsDir = fullfile(cfg.outDir, 'logs');
cfg.plotDir = fullfile(cfg.outDir, 'plots');
cfg.modelsDir = fullfile(cfg.outDir, 'models');
ensure_dir(cfg.outDir);
ensure_dir(cfg.tbl1Dir);
ensure_dir(cfg.logsDir);
ensure_dir(cfg.plotDir);

sampleId = char(string(row.sample_id(1)));
[report, model] = validate_stage2_harmonics_geometry(cfg, pointSpec, shapeFile, sampleId);
if isempty(model)
    error('COMSOL geometry model was not created: %s', char(string(report.error_message)));
end

label = band_label_from_tag(tag);
overlapHz = double(summaryRow.best_target_overlap_Hz(1));
shapeId = string(row.shape_id(1));
stem = sprintf('ch4_fig4_6_unit_cell_%s_comsol', char(tag));

pngPath = fullfile(figDir, [stem '.png']);
svgPath = fullfile(figDir, [stem '.svg']);
pdfPath = fullfile(figDir, [stem '.pdf']);
export_geometry_figure(model, pngPath, svgPath, pdfPath);

rec.target_band = label;
rec.sample_id = string(row.sample_id(1));
rec.candidate_id = string(row.candidate_id(1));
rec.shape_id = shapeId;
rec.generation = double(row.generation(1));
rec.individual_index = double(row.individual_index(1));
rec.best_target_overlap_Hz = overlapHz;
rec.geometry_valid = logical(report.geometry_valid);
rec.contact_valid = logical(report.contact_valid);
rec.n_domains = double(report.n_domains);
rec.png_path = string(pngPath);
rec.svg_path = string(svgPath);
rec.pdf_path = string(pdfPath);
rec.status = "ok";
rec.error_message = string(report.error_message);

fprintf('[PNG] %s\n', pngPath);
fprintf('[SVG] %s\n', svgPath);
fprintf('[PDF] %s\n', pdfPath);
end

function export_geometry_figure(model, pngPath, svgPath, pdfPath)
fig = figure('Visible', 'off', 'Color', 'white', 'Position', [100, 100, 980, 920]);
cleanup = onCleanup(@() close(fig)); %#ok<NASGU>

try
    mphgeom(model, 'geom1', 'facemode', 'on', 'edgemode', 'on');
catch ME
    error('COMSOL geometry plotting failed: %s', ME.message);
end

ax = gca;
axis(ax, 'equal');
axis(ax, 'off');
xlim(ax, [-0.026, 0.026]);
ylim(ax, [-0.026, 0.026]);
title(ax, '');
set(ax, 'Units', 'normalized', 'Position', [0.035, 0.035, 0.93, 0.93]);
set(ax, 'LooseInset', [0, 0, 0, 0]);
set(findall(fig, '-property', 'FontName'), 'FontName', 'Microsoft YaHei');

exportgraphics(fig, pngPath, 'Resolution', 450, 'BackgroundColor', 'white');
try
    print(fig, svgPath, '-dsvg');
catch ME
    warning('export_ch4_best_unit_cell_comsol_geometry_v1:SvgFailed', ...
        'SVG export failed: %s', ME.message);
end
try
    exportgraphics(fig, pdfPath, 'ContentType', 'vector', 'BackgroundColor', 'white');
catch ME
    warning('export_ch4_best_unit_cell_comsol_geometry_v1:PdfFailed', ...
        'PDF export failed: %s', ME.message);
end
end

function rec = empty_record()
rec = struct( ...
    'target_band', "", ...
    'target_band_tag', "", ...
    'sample_id', "", ...
    'candidate_id', "", ...
    'shape_id', "", ...
    'generation', NaN, ...
    'individual_index', NaN, ...
    'best_target_overlap_Hz', NaN, ...
    'geometry_valid', false, ...
    'contact_valid', false, ...
    'n_domains', NaN, ...
    'png_path', "", ...
    'svg_path', "", ...
    'pdf_path', "", ...
    'status', "", ...
    'error_message', "" ...
);
end

function value = get_numeric_field(row, name, fallback)
value = fallback;
if ismember(name, row.Properties.VariableNames)
    raw = row.(name)(1);
    value = double(raw);
end
end

function label = band_label_from_tag(tag)
switch string(tag)
    case "band140_180"
        label = "140-180 Hz";
    case "band160_200"
        label = "160-200 Hz";
    case "band180_220"
        label = "180-220 Hz";
    case "band200_240"
        label = "200-240 Hz";
    case "band220_260"
        label = "220-260 Hz";
    case "band240_280"
        label = "240-280 Hz";
    otherwise
        label = string(tag);
end
end

function id = sanitize_id(value)
id = regexprep(char(string(value)), '[^A-Za-z0-9_]+', '_');
end

function ensure_dir(pathStr)
if ~exist(pathStr, 'dir')
    mkdir(pathStr);
end
end
