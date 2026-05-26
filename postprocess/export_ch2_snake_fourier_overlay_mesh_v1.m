function export_ch2_snake_fourier_overlay_mesh_v1()
%EXPORT_CH2_SNAKE_FOURIER_OVERLAY_MESH_V1 Export a real COMSOL mesh image
% for the chapter-2 snake/Fourier overlay schematic.

import com.comsol.model.*
import com.comsol.model.util.*

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
addpath(genpath(fullfile(rootDir, 'model_core')));

shapeId = 'ep100_step18';
caseId = ['ch2_snake_fourier_overlay_mesh_' shapeId];
shapeFile = fullfile(rootDir, 'data', 'shape_contours', [shapeId '_contour_xy.csv']);
outDir = fullfile(rootDir, 'data', 'analysis', 'thesis_ch2_v1', 'figures');
modelDir = fullfile(rootDir, 'data', 'analysis', 'thesis_ch2_v1', 'models');
outPng = fullfile(outDir, [caseId '.png']);
outSvg = fullfile(outDir, [caseId '.svg']);
modelPath = fullfile(modelDir, [caseId '.mph']);

if ~isfile(shapeFile)
    error('export_ch2_snake_fourier_overlay_mesh_v1:MissingShape', ...
        'Shape file not found: %s', shapeFile);
end
ensure_dir(outDir);
ensure_dir(modelDir);

ModelUtil.clear;
ModelUtil.showProgress(true);

assignin('base', 'shape_file', shapeFile);
assignin('base', 'shape_export_name', caseId);
assignin('base', 'use_discrete_perturbation', true);
assignin('base', 'shape_skip', false);
assignin('base', 'shape_skip_reason', '');
assignin('base', 'fourier_param_overrides', struct( ...
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
    'b5', 0.0));

model = ModelUtil.create('ch2mesh');
model.modelPath(modelDir);
model.label(caseId);

model = set_params_01(model);
model = build_geom_02(model);

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
    error('export_ch2_snake_fourier_overlay_mesh_v1:ShapeSkipped', ...
        'Discrete shape was skipped during geometry build: %s', char(string(skipReason)));
end

model = set_mesh_05(model);
mphsave(model, modelPath);

fig = figure('Visible', 'off', 'Color', 'white', 'Position', [100, 100, 900, 760]);
cleanupFig = onCleanup(@() close(fig)); %#ok<NASGU>

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
    catch
    end
end
if ~plotted
    try
        mphgeom(model, 'geom1', 'facemode', 'on', 'edgemode', 'on');
        plotted = true;
    catch ME
        error('export_ch2_snake_fourier_overlay_mesh_v1:PlotFailed', ...
            'Failed to plot mesh or geometry: %s', ME.message);
    end
end

ax = gca;
axis(ax, 'equal');
axis(ax, 'off');
title(ax, '傅里叶母体边界与贪吃蛇扰动叠加后的 COMSOL 网格', ...
    'Interpreter', 'none', 'FontSize', 12);
set(ax, 'FontName', 'Microsoft YaHei');

exportgraphics(fig, outPng, 'Resolution', 300);
try
    print(fig, outSvg, '-dsvg');
catch
end

fprintf('[PNG] %s\n', outPng);
fprintf('[SVG] %s\n', outSvg);
fprintf('[MPH] %s\n', modelPath);
end

function ensure_dir(pathIn)
if ~exist(pathIn, 'dir')
    mkdir(pathIn);
end
end
