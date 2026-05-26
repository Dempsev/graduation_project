function export_ch2_structure_construction_assets_v1()
%EXPORT_CH2_STRUCTURE_CONSTRUCTION_ASSETS_V1
% Export separate assets for the chapter-2 snake/Fourier construction figure:
% Fourier mother boundary, selected snake shape, COMSOL overlay geometry,
% and real COMSOL mesh.

import com.comsol.model.*
import com.comsol.model.util.*

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
addpath(genpath(fullfile(rootDir, 'model_core')));

shapeId = 'ep100_step18';
shapeCsv = fullfile(rootDir, 'data', 'shape_contours', [shapeId '_contour_xy.csv']);
shapePreview = fullfile(rootDir, 'data', 'shape_contour_previews', [shapeId '_preview.png']);
outDir = fullfile(rootDir, 'data', 'analysis', 'thesis_ch2_v1', ...
    ['structure_construction_assets_' shapeId]);
modelDir = fullfile(outDir, 'models');

if ~isfile(shapeCsv)
    error('export_ch2_structure_construction_assets_v1:MissingShapeCsv', ...
        'Missing shape CSV: %s', shapeCsv);
end
ensure_dir(outDir);
ensure_dir(modelDir);

fourierParams = struct( ...
    'r0', 0.012, ...
    'a1', 0.45, ...
    'b1', 0.0, ...
    'a2', 0.0, ...
    'b2', 0.0, ...
    'a3', 0.0, ...
    'b3', 0.0, ...
    'a4', 0.0, ...
    'b4', 0.0, ...
    'a5', 0.0, ...
    'b5', 0.0);

fprintf('[INFO] selected shape: %s\n', shapeId);
fprintf('[INFO] shape CSV: %s\n', shapeCsv);
if isfile(shapePreview)
    fprintf('[INFO] source preview: %s\n', shapePreview);
end

export_fourier_boundary_plot(outDir, fourierParams);
export_selected_shape_plot(outDir, shapeCsv, shapeId);

ModelUtil.clear;
ModelUtil.showProgress(true);

fourierModel = build_model_for_assets(modelDir, fourierParams, '', 'asset_fourier_mother_boundary', false);
export_comsol_geometry(fourierModel, outDir, '01_fourier_mother_boundary_comsol', ...
    '傅里叶母体边界（COMSOL 几何）');
mphsave(fourierModel, fullfile(modelDir, '01_fourier_mother_boundary.mph'));

overlayModel = build_model_for_assets(modelDir, fourierParams, shapeCsv, ...
    ['asset_overlay_' shapeId], true);
export_comsol_geometry(overlayModel, outDir, '03_overlay_model_geometry', ...
    '傅里叶母体边界与贪吃蛇扰动叠加后的模型');
overlayModel = set_mesh_05(overlayModel);
export_comsol_mesh(overlayModel, outDir, '04_overlay_comsol_mesh', ...
    '傅里叶母体边界与贪吃蛇扰动叠加后的 COMSOL 网格');
mphsave(overlayModel, fullfile(modelDir, ['03_04_overlay_model_mesh_' shapeId '.mph']));

write_asset_index(outDir, shapeId, shapeCsv, shapePreview);

fprintf('[OUT_DIR] %s\n', outDir);
end

function model = build_model_for_assets(modelDir, fourierParams, shapeCsv, caseId, useShape)
import com.comsol.model.util.*

assignin('base', 'shape_file', shapeCsv);
assignin('base', 'shape_export_name', caseId);
assignin('base', 'use_discrete_perturbation', logical(useShape));
assignin('base', 'shape_skip', false);
assignin('base', 'shape_skip_reason', '');
assignin('base', 'fourier_param_overrides', fourierParams);

model = ModelUtil.create(caseId);
model.modelPath(modelDir);
model.label(caseId);
model = set_params_01(model);
model = build_geom_02(model);

if useShape
    isSkipped = false;
    skipReason = '';
    try
        isSkipped = evalin('base', 'exist(''shape_skip'',''var'') && shape_skip');
        if isSkipped
            skipReason = evalin('base', 'shape_skip_reason');
        end
    catch
    end
    if isSkipped
        error('export_ch2_structure_construction_assets_v1:ShapeSkipped', ...
            'Selected shape was skipped during geometry build: %s', char(string(skipReason)));
    end
end
end

function export_fourier_boundary_plot(outDir, p)
t = linspace(0, 2*pi, 500);
amp = 1 + p.a1*cos(t) + p.b1*sin(t) + p.a2*cos(2*t) + p.b2*sin(2*t) + ...
    p.a3*cos(3*t) + p.b3*sin(3*t) + p.a4*cos(4*t) + p.b4*sin(4*t) + ...
    p.a5*cos(5*t) + p.b5*sin(5*t);
r = p.r0 * amp;
x = r .* cos(t);
y = r .* sin(t);

fig = figure('Visible', 'off', 'Color', 'white', 'Position', [100, 100, 760, 720]);
cleanup = onCleanup(@() close(fig)); %#ok<NASGU>
patch(x, y, [0.95, 0.72, 0.70], 'EdgeColor', [0.82, 0.22, 0.18], 'LineWidth', 2.0, 'FaceAlpha', 0.78);
hold on;
plot(x, y, 'Color', [0.82, 0.22, 0.18], 'LineWidth', 2.0);
draw_unit_cell_box();
axis equal off;
title('傅里叶母体边界', 'FontName', 'Microsoft YaHei', 'FontSize', 16);
export_both(fig, outDir, '01_fourier_mother_boundary');
end

function export_selected_shape_plot(outDir, shapeCsv, shapeId)
xy = readmatrix(shapeCsv);
xy = xy(:, 1:2);
xy = xy(~any(isnan(xy), 2), :);
if norm(xy(1, :) - xy(end, :)) > 1e-12
    xy = [xy; xy(1, :)];
end

fig = figure('Visible', 'off', 'Color', 'white', 'Position', [100, 100, 760, 720]);
cleanup = onCleanup(@() close(fig)); %#ok<NASGU>
patch(xy(:, 1), xy(:, 2), [0.97, 0.78, 0.22], 'EdgeColor', [0.07, 0.34, 0.62], ...
    'LineWidth', 2.0, 'FaceAlpha', 0.95);
axis equal off;
pad_axis(xy(:, 1), xy(:, 2), 0.35);
title(sprintf('贪吃蛇离散扰动形状：%s', shapeId), 'Interpreter', 'none', ...
    'FontName', 'Microsoft YaHei', 'FontSize', 16);
export_both(fig, outDir, '02_selected_snake_shape');
end

function export_comsol_geometry(model, outDir, stem, titleText)
fig = figure('Visible', 'off', 'Color', 'white', 'Position', [100, 100, 860, 780]);
cleanup = onCleanup(@() close(fig)); %#ok<NASGU>
try
    mphgeom(model, 'geom1', 'facemode', 'on', 'edgemode', 'on');
catch ME
    error('export_ch2_structure_construction_assets_v1:GeometryPlotFailed', ...
        'Failed to export geometry image: %s', ME.message);
end
ax = gca;
axis(ax, 'equal');
axis(ax, 'off');
title(ax, titleText, 'Interpreter', 'none', 'FontName', 'Microsoft YaHei', 'FontSize', 15);
export_both(fig, outDir, stem);
end

function export_comsol_mesh(model, outDir, stem, titleText)
fig = figure('Visible', 'off', 'Color', 'white', 'Position', [100, 100, 900, 820]);
cleanup = onCleanup(@() close(fig)); %#ok<NASGU>
plotted = false;
try
    mphmesh(model, 'mesh1');
    plotted = true;
catch
end
if ~plotted
    try
        mphmesh(model);
        plotted = true;
    catch ME
        error('export_ch2_structure_construction_assets_v1:MeshPlotFailed', ...
            'Failed to export mesh image: %s', ME.message);
    end
end
ax = gca;
axis(ax, 'equal');
axis(ax, 'off');
title(ax, titleText, 'Interpreter', 'none', 'FontName', 'Microsoft YaHei', 'FontSize', 15);
export_both(fig, outDir, stem);
end

function draw_unit_cell_box()
a = 0.05;
rectangle('Position', [-a/2, -a/2, a, a], 'EdgeColor', [0.35, 0.38, 0.43], 'LineWidth', 1.2);
xlim([-a/2, a/2]);
ylim([-a/2, a/2]);
end

function pad_axis(x, y, ratio)
xmin = min(x); xmax = max(x);
ymin = min(y); ymax = max(y);
dx = max(xmax - xmin, 1e-9);
dy = max(ymax - ymin, 1e-9);
d = max(dx, dy);
cx = 0.5 * (xmin + xmax);
cy = 0.5 * (ymin + ymax);
half = 0.5 * d * (1 + ratio);
xlim([cx - half, cx + half]);
ylim([cy - half, cy + half]);
end

function export_both(fig, outDir, stem)
pngPath = fullfile(outDir, [stem '.png']);
svgPath = fullfile(outDir, [stem '.svg']);
exportgraphics(fig, pngPath, 'Resolution', 300);
try
    print(fig, svgPath, '-dsvg');
catch
end
fprintf('[PNG] %s\n', pngPath);
fprintf('[SVG] %s\n', svgPath);
end

function write_asset_index(outDir, shapeId, shapeCsv, shapePreview)
indexPath = fullfile(outDir, 'asset_index.txt');
fid = fopen(indexPath, 'w');
if fid < 0
    warning('Could not write asset index: %s', indexPath);
    return;
end
cleanup = onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid, 'Chapter 2 structure construction assets\n');
fprintf(fid, 'Selected shape: %s\n', shapeId);
fprintf(fid, 'Shape CSV: %s\n', shapeCsv);
if isfile(shapePreview)
    fprintf(fid, 'Source preview: %s\n', shapePreview);
end
fprintf(fid, '\nAssets:\n');
fprintf(fid, '01_fourier_mother_boundary.png/.svg\n');
fprintf(fid, '01_fourier_mother_boundary_comsol.png/.svg\n');
fprintf(fid, '02_selected_snake_shape.png/.svg\n');
fprintf(fid, '03_overlay_model_geometry.png/.svg\n');
fprintf(fid, '04_overlay_comsol_mesh.png/.svg\n');
fprintf(fid, 'models/01_fourier_mother_boundary.mph\n');
fprintf(fid, 'models/03_04_overlay_model_mesh_%s.mph\n', shapeId);
fprintf('[INDEX] %s\n', indexPath);
end

function ensure_dir(pathIn)
if ~exist(pathIn, 'dir')
    mkdir(pathIn);
end
end
