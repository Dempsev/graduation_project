import com.comsol.model.*
import com.comsol.model.util.*

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
addpath(genpath(fullfile(rootDir, 'model_core')));

shapeDir = fullfile(rootDir, 'data', 'shape_contours');
outDir = fullfile(rootDir, 'data', 'comsol_batch');
modelsDir = fullfile(outDir, 'models');
logDir = fullfile(outDir, 'logs');
errorLogCsv = fullfile(logDir, 'run_shape_batch_errors.csv');
tbl1Dir = fullfile(outDir, 'tbl1_exports');

if ~exist(shapeDir, 'dir')
    error("shape_contours dir not found: " + shapeDir);
end
if ~exist(outDir, 'dir'); mkdir(outDir); end
if ~exist(modelsDir, 'dir'); mkdir(modelsDir); end
if ~exist(logDir, 'dir'); mkdir(logDir); end
ensure_error_log_header(errorLogCsv);

files = dir(fullfile(shapeDir, '*_contour_xy.csv'));
if isempty(files)
    files = dir(fullfile(shapeDir, '*.csv'));
end
if isempty(files)
    error("no shape csv found in: " + shapeDir);
end

startIndex = 1;
maxCount = 8; % run 8 cases by default; set to 0 to process all available shapes
buildOnly = false;
doCompute = true;
saveModel = true; % true: save .mph; false: delete/skip .mph after tbl1 export to save disk
runPostprocess = true;
plotLatestManual = true;
pythonCmd = 'python';

if maxCount <= 0
    endIndex = numel(files);
else
    endIndex = min(numel(files), startIndex + maxCount - 1);
end

ModelUtil.clear;
ModelUtil.showProgress(true);
exportedTbl1Paths = {};

for i = startIndex:endIndex
    shapeFile = fullfile(shapeDir, files(i).name);
    [~, baseName, ~] = fileparts(files(i).name);
    exportStem = regexprep(baseName, '_contour_xy$', '');
    fprintf("=== [%d/%d] %s ===\n", i, endIndex, baseName);

    assignin('base', 'shape_file', shapeFile);
    assignin('base', 'shape_export_name', exportStem);

    try
        modelTag = ['m' num2str(i)];
        model = ModelUtil.create(modelTag);
        model.modelPath(outDir);
        model.label(['snake_' baseName]);

        model = set_params_01(model);
        model = build_geom_02(model);

        % Skip output when perturbation is marked as invalid/non-contact.
        isSkipped = false;
        skipReason = '';
        try
            isSkipped = evalin('base', 'exist(''shape_skip'',''var'') && shape_skip');
        catch
        end
        if isSkipped
            try
                skipReason = evalin('base', 'shape_skip_reason');
            catch
            end
            fprintf("SKIP model output for %s (reason=%s)\n", baseName, char(skipReason));
            continue;
        end

        if ~buildOnly
            model = set_material_03(model);
            model = set_physics_04(model);
            model = set_mesh_05(model);
            model = set_study_06(model);
        end

        if doCompute && ~buildOnly
            try
                model.batch('p2').run('compute');
            catch MEComp
                warning("batch compute failed for %s, fallback to study.run: %s", baseName, MEComp.message);
                model.study('std1').run;
            end
        end

        if ~buildOnly
            model = set_results_07(model);
            tbl1Path = fullfile(tbl1Dir, [exportStem '_tbl1.csv']);
            if isfile(tbl1Path)
                exportedTbl1Paths{end+1} = tbl1Path; %#ok<AGROW>
            end
        end

        modelPath = fullfile(modelsDir, [baseName '.mph']);
        if saveModel
            mphsave(model, modelPath);
        else
            % Keep only exported CSV; remove stale/previous model file if present.
            if isfile(modelPath)
                delete(modelPath);
            end
        end
    catch ME
        fprintf(2, "ERROR on %s: %s\n", baseName, ME.message);
        append_error_log(errorLogCsv, i, baseName, shapeFile, ME);
        continue;
    end
end

disp("Batch finished.");
fprintf("Processed range: startIndex=%d, endIndex=%d, requested=%d\n", startIndex, endIndex, endIndex - startIndex + 1);
fprintf("tbl1 exports generated in this run: %d\n", numel(exportedTbl1Paths));

if runPostprocess && ~buildOnly && doCompute
    run_postprocess(rootDir, pythonCmd, exportedTbl1Paths, plotLatestManual);
end

function ensure_error_log_header(logPath)
if isfile(logPath)
    return;
end
fid = fopen(logPath, 'w');
if fid < 0
    return;
end
cleanupObj = onCleanup(@() fclose(fid));
fprintf(fid, 'timestamp,index,shape_name,shape_file,error_id,error_message\n');
end

function append_error_log(logPath, idx, shapeName, shapeFile, ME)
fid = fopen(logPath, 'a');
if fid < 0
    return;
end
cleanupObj = onCleanup(@() fclose(fid));
ts = datestr(now, 'yyyy-mm-dd HH:MM:SS');
msg = char(string(ME.message));
msg = strrep(msg, '"', '""');
sid = char(string(ME.identifier));
sid = strrep(sid, '"', '""');
sname = strrep(char(string(shapeName)), '"', '""');
sfile = strrep(char(string(shapeFile)), '"', '""');
fprintf(fid, '%s,%d,"%s","%s","%s","%s"\n', ts, idx, sname, sfile, sid, msg);
end

function run_postprocess(rootDir, pythonCmd, exportedTbl1Paths, plotLatestManual)
postDir = fullfile(rootDir, 'postprocess');
analyzeCmd = sprintf('"%s" "%s"', pythonCmd, fullfile(postDir, 'analyze_bandgaps.py'));
plotSummaryCmd = sprintf('"%s" "%s"', pythonCmd, fullfile(postDir, 'plot_bandgap_summary.py'));

fprintf("Running postprocess: analyze_bandgaps.py\n");
[statusAnalyze, outAnalyze] = system(analyzeCmd);
fprintf("%s", outAnalyze);
if statusAnalyze ~= 0
    warning("postprocess analyze failed with exit code %d", statusAnalyze);
    return;
end

fprintf("Running postprocess: plot_bandgap_summary.py\n");
[statusPlot, outPlot] = system(plotSummaryCmd);
fprintf("%s", outPlot);
if statusPlot ~= 0
    warning("postprocess plotting failed with exit code %d", statusPlot);
    return;
end

if plotLatestManual && ~isempty(exportedTbl1Paths)
    for i = 1:numel(exportedTbl1Paths)
        tbl1Path = exportedTbl1Paths{i};
        manualCmd = sprintf('"%s" "%s" "%s"', pythonCmd, fullfile(postDir, 'plot_tbl1_bands.py'), tbl1Path);
        fprintf("Running postprocess: plot_tbl1_bands.py for %s\n", tbl1Path);
        [statusManual, outManual] = system(manualCmd);
        fprintf("%s", outManual);
        if statusManual ~= 0
            warning("manual band plot failed with exit code %d for %s", statusManual, tbl1Path);
        end
    end
end
end
