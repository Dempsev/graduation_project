function manifestPath = export_fourier_only_ablation_unit_cells_v1(caseCsv)
%EXPORT_FOURIER_ONLY_ABLATION_UNIT_CELLS_V1 Export COMSOL unit-cell geometry.
%
% The input CSV is built from the best GA candidates of the Fourier-only
% ablation and the current combined shape-library/Fourier workflow. This
% function rebuilds geometry only; it does not rerun eigenfrequency solves.

if nargin < 1 || strlength(string(caseCsv)) == 0
    caseCsv = fullfile('D:\graduation_project\coad', 'research_validation', ...
        'ch5_fourier_only_ablation', 'fourier_only_ablation_geometry_cases.csv');
end

rootDir = 'D:\graduation_project\coad';
addpath(rootDir);
addpath(fullfile(rootDir, 'model_core'));
addpath(fullfile(rootDir, 'stage2_harmonics'));
addpath(fullfile(rootDir, 'stage2_harmonics_refine'));
addpath(fullfile(rootDir, 'optimization', 'real_comsol_ga'));
addpath(fullfile(rootDir, 'shared', 'optimization_matlab'));

outDir = fullfile(rootDir, 'research_validation', 'ch5_fourier_only_ablation');
figDir = fullfile(outDir, 'figures', 'geometry_exports');
workDir = fullfile(outDir, 'comsol_unit_cell_export_work');
ensure_dir(figDir);
ensure_dir(workDir);

cases = readtable(caseCsv, 'TextType', 'string', 'Delimiter', ',', 'VariableNamingRule', 'preserve');
records = repmat(empty_record(), height(cases), 1);

for i = 1:height(cases)
    row = cases(i, :);
    fprintf('[GEOMETRY] %d/%d %s %s %s\n', i, height(cases), ...
        char(string(row.target_band_tag(1))), char(string(row.method(1))), char(string(row.sample_id(1))));
    try
        records(i) = export_one_case(row, rootDir, figDir, workDir);
    catch ME
        rec = empty_record();
        rec.target_band = string(row.target_band(1));
        rec.target_band_tag = string(row.target_band_tag(1));
        rec.method = string(row.method(1));
        rec.method_label = string(row.method_label(1));
        rec.sample_id = string(row.sample_id(1));
        rec.candidate_id = string(row.candidate_id(1));
        rec.shape_id = string(row.shape_id(1));
        rec.shape_family = string(row.shape_family(1));
        rec.overlap_Hz = double(row.overlap_Hz(1));
        rec.status = "failed";
        rec.error_message = string(ME.message);
        records(i) = rec;
        warning('export_fourier_only_ablation_unit_cells_v1:Failed', ...
            'Failed to export %s: %s', char(string(row.sample_id(1))), ME.message);
    end
end

manifest = struct2table(records);
manifestPath = fullfile(outDir, 'fourier_only_ablation_geometry_export_manifest.csv');
writetable(manifest, manifestPath);
make_comparison_montage(manifest, outDir);
fprintf('[MANIFEST] %s\n', manifestPath);
end

function rec = export_one_case(row, rootDir, figDir, workDir)
tag = string(row.target_band_tag(1));
method = string(row.method(1));
sampleId = sanitize_id(string(row.sample_id(1)));

cfg = get_comsol_in_loop_ga_config_v1();
cfg.outDir = fullfile(workDir, char(tag), char(method));
cfg.tbl1Dir = fullfile(cfg.outDir, 'tbl1_exports');
cfg.logsDir = fullfile(cfg.outDir, 'logs');
cfg.plotDir = fullfile(cfg.outDir, 'plots');
cfg.modelsDir = fullfile(cfg.outDir, 'models');
cfg.saveModel = false;
ensure_dir(cfg.outDir);
ensure_dir(cfg.tbl1Dir);
ensure_dir(cfg.logsDir);
ensure_dir(cfg.plotDir);

shapeFile = string(row.shape_file(1));
if startsWith(string(row.method(1)), "fourier_only")
    shapeFile = "";
elseif strlength(shapeFile) == 0 || ~isfile(shapeFile)
    shapeFile = string(fullfile(rootDir, 'data', 'shape_contours', char(string(row.shape_id(1)) + ".csv")));
end

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

[report, model] = validate_stage2_harmonics_geometry(cfg, pointSpec, char(shapeFile), char(sampleId));
if isempty(model)
    error('COMSOL geometry model was not created: %s', char(string(report.error_message)));
end

stem = sprintf('ch5_fourier_ablation_unit_cell_%s_%s', char(tag), char(method));
pngPath = fullfile(figDir, [stem '.png']);
svgPath = fullfile(figDir, [stem '.svg']);
pdfPath = fullfile(figDir, [stem '.pdf']);
export_geometry_figure(model, pngPath, svgPath, pdfPath);

rec = empty_record();
rec.target_band = string(row.target_band(1));
rec.target_band_tag = tag;
rec.method = method;
rec.method_label = string(row.method_label(1));
rec.sample_id = string(row.sample_id(1));
rec.candidate_id = string(row.candidate_id(1));
rec.shape_id = string(row.shape_id(1));
rec.shape_family = string(row.shape_family(1));
rec.generation = double(row.generation(1));
rec.individual_index = double(row.individual_index(1));
rec.overlap_Hz = double(row.overlap_Hz(1));
rec.cover_ratio = double(row.cover_ratio(1));
rec.geometry_valid = logical(report.geometry_valid);
rec.contact_valid = logical(report.contact_valid);
rec.n_domains = double(report.n_domains);
rec.png_path = string(pngPath);
rec.svg_path = string(svgPath);
rec.pdf_path = string(pdfPath);
rec.status = "ok";
rec.error_message = string(report.error_message);
fprintf('[PNG] %s\n', pngPath);
end

function export_geometry_figure(model, pngPath, svgPath, pdfPath)
fig = figure('Visible', 'off', 'Color', 'white', 'Position', [100, 100, 980, 920]);
cleanup = onCleanup(@() close(fig)); %#ok<NASGU>
mphgeom(model, 'geom1', 'facemode', 'on', 'edgemode', 'on');
ax = gca;
axis(ax, 'equal');
axis(ax, 'off');
xlim(ax, [-0.026, 0.026]);
ylim(ax, [-0.026, 0.026]);
title(ax, '');
set(ax, 'Units', 'normalized', 'Position', [0.02, 0.02, 0.96, 0.96]);
set(ax, 'LooseInset', [0, 0, 0, 0]);
set(findall(fig, '-property', 'FontName'), 'FontName', 'Microsoft YaHei');
exportgraphics(fig, pngPath, 'Resolution', 450, 'BackgroundColor', 'white');
try
    print(fig, svgPath, '-dsvg');
catch ME
    warning('export_fourier_only_ablation_unit_cells_v1:SvgFailed', 'SVG export failed: %s', ME.message);
end
try
    exportgraphics(fig, pdfPath, 'ContentType', 'vector', 'BackgroundColor', 'white');
catch ME
    warning('export_fourier_only_ablation_unit_cells_v1:PdfFailed', 'PDF export failed: %s', ME.message);
end
end

function make_comparison_montage(manifest, outDir)
figDir = fullfile(outDir, 'figures');
bandTags = ["band200_240", "band220_260", "band240_280"];
methods = ["fourier_only_ga20", "combined_ga20"];

fig = figure('Visible', 'off', 'Color', 'white', 'Position', [80, 80, 1300, 1580]);
cleanup = onCleanup(@() close(fig)); %#ok<NASGU>
t = tiledlayout(fig, 3, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
title(t, '最终优化结果几何模型对比', 'FontName', 'Microsoft YaHei', 'FontSize', 18, 'FontWeight', 'bold');

for i = 1:numel(bandTags)
    for j = 1:numel(methods)
        ax = nexttile(t);
        idx = find(manifest.target_band_tag == bandTags(i) & manifest.method == methods(j) & manifest.status == "ok", 1);
        if isempty(idx)
            axis(ax, 'off');
            title(ax, sprintf('%s / %s export failed', bandTags(i), methods(j)), 'Interpreter', 'none');
            continue;
        end
        row = manifest(idx, :);
        img = imread(char(row.png_path(1)));
        image(ax, img);
        axis(ax, 'image');
        axis(ax, 'off');
        title(ax, sprintf('%s | %s\n%s | overlap=%.2f Hz', ...
            char(row.target_band(1)), char(row.method_label(1)), char(row.shape_id(1)), double(row.overlap_Hz(1))), ...
            'FontName', 'Microsoft YaHei', 'FontSize', 10, 'Interpreter', 'none');
    end
end

pngPath = fullfile(figDir, 'ch5_fourier_only_ablation_final_geometry_compare.png');
svgPath = fullfile(figDir, 'ch5_fourier_only_ablation_final_geometry_compare.svg');
pdfPath = fullfile(figDir, 'ch5_fourier_only_ablation_final_geometry_compare.pdf');
exportgraphics(fig, pngPath, 'Resolution', 300, 'BackgroundColor', 'white');
try
    print(fig, svgPath, '-dsvg');
catch ME
    warning('export_fourier_only_ablation_unit_cells_v1:MontageSvgFailed', 'SVG montage export failed: %s', ME.message);
end
try
    exportgraphics(fig, pdfPath, 'ContentType', 'vector', 'BackgroundColor', 'white');
catch ME
    warning('export_fourier_only_ablation_unit_cells_v1:MontagePdfFailed', 'PDF montage export failed: %s', ME.message);
end
fprintf('[MONTAGE] %s\n', pngPath);
end

function rec = empty_record()
rec = struct( ...
    'target_band', "", ...
    'target_band_tag', "", ...
    'method', "", ...
    'method_label', "", ...
    'sample_id', "", ...
    'candidate_id', "", ...
    'shape_id', "", ...
    'shape_family', "", ...
    'generation', NaN, ...
    'individual_index', NaN, ...
    'overlap_Hz', NaN, ...
    'cover_ratio', NaN, ...
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
    value = double(row.(name)(1));
end
end

function out = sanitize_id(value)
out = regexprep(string(value), '[^A-Za-z0-9_]+', '_');
out = regexprep(out, '_+', '_');
if strlength(out) > 79
    out = extractBefore(out, 80);
end
if strlength(out) == 0
    out = "ch5_fourier_ablation_sample";
end
end

function ensure_dir(pathStr)
if ~exist(pathStr, 'dir')
    mkdir(pathStr);
end
end
