import com.comsol.model.*
import com.comsol.model.util.*

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
addpath(genpath(fullfile(rootDir, 'model_core')));

shapeDir = fullfile(rootDir, 'data', 'shape_points');
outDir = fullfile(rootDir, 'data', 'shape_batch');
modelsDir = fullfile(outDir, 'models');
tablesDir = fullfile(outDir, 'tables');

if ~exist(shapeDir, 'dir')
    error("shape_points dir not found: " + shapeDir);
end
if ~exist(outDir, 'dir'); mkdir(outDir); end
if ~exist(modelsDir, 'dir'); mkdir(modelsDir); end
if ~exist(tablesDir, 'dir'); mkdir(tablesDir); end

files = dir(fullfile(shapeDir, '*_contour_xy.csv'));
if isempty(files)
    files = dir(fullfile(shapeDir, '*.csv'));
end
if isempty(files)
    error("no shape csv found in: " + shapeDir);
end

startIndex = 1;
maxCount = 9; % 0 = all
buildOnly = true;
doCompute = false;
doExportTable = false;

if maxCount <= 0
    endIndex = numel(files);
else
    endIndex = min(numel(files), startIndex + maxCount - 1);
end

ModelUtil.clear;
ModelUtil.showProgress(true);

for i = startIndex:endIndex
    shapeFile = fullfile(shapeDir, files(i).name);
    [~, baseName, ~] = fileparts(files(i).name);
    fprintf("=== [%d/%d] %s ===\n", i, endIndex, baseName);

    assignin('base', 'shape_file', shapeFile);

    modelTag = ['m' num2str(i)];
    model = ModelUtil.create(modelTag);
    model.modelPath(outDir);
    model.label(['snake_' baseName]);

    model = set_params_01(model);
    model = build_geom_02(model);
    if ~buildOnly
        model = set_material_03(model);
        model = set_physics_04(model);
        model = set_mesh_05(model);
        model = set_study_06(model);
    end

    if doCompute && ~buildOnly
        try
            model.batch('p2').run('compute');
        catch
            model.study('std1').run;
        end
    end

    if ~buildOnly
        model = set_results_07(model);
    end

    if doExportTable && ~buildOnly
        try
            try
                model.result.numerical('gev1').setResult;
            catch
                model.result.numerical('gev1').run;
            end
            T = mphtable(model, 'tbl1');
            outCsv = fullfile(tablesDir, [baseName '_tbl1.csv']);
            if isempty(T) || ~isfield(T, 'data') || isempty(T.data)
                writematrix([], outCsv);
            else
                writematrix(T.data, outCsv);
            end
        catch ME
            warning("table export failed for %s: %s", baseName, ME.message);
        end
    end

    mphsave(model, fullfile(modelsDir, [baseName '.mph']));
end

disp("Batch finished.");
