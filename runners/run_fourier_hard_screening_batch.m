import com.comsol.model.*
import com.comsol.model.util.*

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
addpath(genpath(fullfile(rootDir, 'model_core')));

shapeDir = fullfile(rootDir, 'data', 'shape_contours');
outDir = fullfile(rootDir, 'data', 'comsol_batch', 'fourier_hard_screening');
modelsDir = fullfile(outDir, 'models');
logDir = fullfile(outDir, 'logs');
tbl1Dir = fullfile(outDir, 'tbl1_exports');
errorLogCsv = fullfile(logDir, 'run_fourier_hard_screening_errors.csv');
manifestCsv = fullfile(outDir, 'case_manifest.csv');

defaultShapeFile = '';
startIndex = 1;
maxCount = 1; % run a single baseline case by default for physical diagnostics
doCompute = true;
saveModel = true;
runPostprocess = true;
pythonCmd = 'python';

if ~exist(shapeDir, 'dir')
    error("shape_contours dir not found: " + shapeDir);
end
if ~isfile(manifestCsv)
    error("case manifest not found: " + manifestCsv);
end

if ~exist(outDir, 'dir'); mkdir(outDir); end
if ~exist(modelsDir, 'dir'); mkdir(modelsDir); end
if ~exist(logDir, 'dir'); mkdir(logDir); end
if ~exist(tbl1Dir, 'dir'); mkdir(tbl1Dir); end
ensure_error_log_header(errorLogCsv);

cases = read_case_manifest(manifestCsv);
cases = cases(get_enabled_mask(cases), :);
if isempty(cases)
    error("no enabled case found in manifest: " + manifestCsv);
end

if maxCount <= 0
    endIndex = height(cases);
else
    endIndex = min(height(cases), startIndex + maxCount - 1);
end

ModelUtil.clear;
ModelUtil.showProgress(true);
exportedTbl1Paths = {};

for i = startIndex:endIndex
    caseRow = cases(i, :);
    caseId = char(caseRow.case_id);
    useDiscretePerturbation = resolve_use_discrete_shape(caseRow);
    shapeFile = '';
    if useDiscretePerturbation
        shapeFile = resolve_case_shape_file(caseRow, defaultShapeFile, shapeDir, rootDir);
    end
    paramOverrides = build_param_overrides(caseRow);
    [studyNeigs, studyShift] = resolve_study_overrides(caseRow);

    fprintf("=== [%d/%d] %s ===\n", i, endIndex, caseId);
    fprintf("mode=%s, shift=%s, neigs=%g\n", ternary(useDiscretePerturbation, 'fourier+shape', 'fourier_only'), studyShift, studyNeigs);
    if useDiscretePerturbation
        fprintf("shape=%s\n", shapeFile);
    end

    assign_hard_screening_context(shapeFile, caseId, paramOverrides, useDiscretePerturbation, studyNeigs, studyShift);

    try
        modelTag = ['hard' num2str(i)];
        model = ModelUtil.create(modelTag);
        model.modelPath(outDir);
        model.label(['fourier_hard_' caseId]);

        model = set_params_01(model);
        model = build_geom_02(model);

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
            fprintf("SKIP model output for %s (reason=%s)\n", caseId, char(skipReason));
            continue;
        end

        model = set_material_03(model);
        model = set_physics_04(model);
        model = set_mesh_05(model);
        model = set_study_06(model);

        if doCompute
            try
                model.batch('p2').run('compute');
            catch MEComp
                warning("batch compute failed for %s, fallback to study.run: %s", caseId, MEComp.message);
                model.study('std1').run;
            end
        end

        model = set_results_07(model);
        tbl1Path = fullfile(tbl1Dir, [caseId '_tbl1.csv']);
        if isfile(tbl1Path)
            exportedTbl1Paths{end+1} = tbl1Path; %#ok<AGROW>
        end

        if saveModel
            modelPath = fullfile(modelsDir, [caseId '.mph']);
            mphsave(model, modelPath);
        end
    catch ME
        fprintf(2, "ERROR on %s: %s\n", caseId, ME.message);
        append_error_log(errorLogCsv, i, caseId, shapeFile, ME);
        continue;
    end
end

disp("Hard screening batch finished.");
fprintf("Processed range: startIndex=%d, endIndex=%d\n", startIndex, endIndex);
fprintf("tbl1 exports generated in this run: %d\n", numel(exportedTbl1Paths));

if runPostprocess && doCompute
    run_postprocess(rootDir, outDir, pythonCmd, manifestCsv);
end

function cases = read_case_manifest(manifestCsv)
opts = detectImportOptions(manifestCsv, 'TextType', 'string');
cases = readtable(manifestCsv, opts);
required = {'case_id', 'neigs', 'shift_Hz'};
for i = 1:numel(required)
    name = required{i};
    if ~any(strcmp(cases.Properties.VariableNames, name))
        error("missing required column in manifest: " + name);
    end
end

cases.case_id = strtrim(string(cases.case_id));
for name = {'neigs', 'shift_Hz'}
    col = name{1};
    if ~isnumeric(cases.(col))
        cases.(col) = str2double(string(cases.(col)));
    end
end

if any(strlength(cases.case_id) == 0)
    error("manifest contains empty case_id");
end
if any(~isfinite(cases.neigs)) || any(~isfinite(cases.shift_Hz))
    error("manifest contains non-numeric neigs/shift_Hz values");
end
end

function mask = get_enabled_mask(cases)
mask = true(height(cases), 1);
if ~any(strcmp(cases.Properties.VariableNames, 'enabled'))
    return;
end

raw = cases.enabled;
if isnumeric(raw) || islogical(raw)
    mask = logical(raw);
    return;
end

vals = lower(strtrim(string(raw)));
mask = vals == "1" | vals == "true" | vals == "yes" | vals == "y";
end

function tf = resolve_use_discrete_shape(caseRow)
tf = false;
if ~ismember('use_discrete_shape', caseRow.Properties.VariableNames)
    return;
end

value = caseRow.use_discrete_shape(1);
if isnumeric(value) || islogical(value)
    tf = logical(value);
    return;
end

s = lower(strtrim(string(value)));
tf = any(strcmp(s, {'1', 'true', 'yes', 'y', 'on'}));
end

function shapeFile = resolve_case_shape_file(caseRow, defaultShapeFile, shapeDir, rootDir)
shapeFile = '';

if ismember('shape_file', caseRow.Properties.VariableNames)
    candidate = strtrim(string(caseRow.shape_file(1)));
    if strlength(candidate) > 0
        shapeFile = resolve_path(char(candidate), rootDir, shapeDir);
    end
end

if isempty(shapeFile) && ~isempty(defaultShapeFile)
    shapeFile = resolve_path(defaultShapeFile, rootDir, shapeDir);
end

if isempty(shapeFile)
    files = dir(fullfile(shapeDir, '*_contour_xy.csv'));
    if isempty(files)
        files = dir(fullfile(shapeDir, '*.csv'));
    end
    if isempty(files)
        error("no shape csv found in: " + shapeDir);
    end
    names = sort({files.name});
    shapeFile = fullfile(shapeDir, names{1});
end

if ~isfile(shapeFile)
    error("shape file not found: " + shapeFile);
end
end

function p = resolve_path(candidate, rootDir, shapeDir)
p = candidate;
if isempty(p)
    return;
end
if isstring(p)
    p = char(p);
end
if numel(p) >= 2 && p(2) == ':'
    return;
end
if startsWith(p, filesep)
    return;
end

shapePath = fullfile(shapeDir, p);
if isfile(shapePath)
    p = shapePath;
    return;
end

p = fullfile(rootDir, p);
end

function overrides = build_param_overrides(caseRow)
overrides = struct();
allowed = {'r0', 'n', 'phi', 'amp', 'a1', 'b1', 'a2', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5'};
for i = 1:numel(allowed)
    name = allowed{i};
    if ~ismember(name, caseRow.Properties.VariableNames)
        continue;
    end

    value = caseRow.(name)(1);
    if ismissing(value)
        continue;
    end

    if isnumeric(value)
        if ~isfinite(value)
            continue;
        end
        overrides.(name) = double(value);
        continue;
    end

    s = strtrim(string(value));
    if strlength(s) > 0
        overrides.(name) = char(s);
    end
end
end

function [studyNeigs, studyShift] = resolve_study_overrides(caseRow)
studyNeigs = double(caseRow.neigs(1));
studyShift = sprintf('%.12g[Hz]', double(caseRow.shift_Hz(1)));
end

function assign_hard_screening_context(shapeFile, caseId, paramOverrides, useDiscretePerturbation, studyNeigs, studyShift)
assignin('base', 'shape_file', shapeFile);
assignin('base', 'shape_export_name', caseId);
assignin('base', 'screening_case_id', caseId);
assignin('base', 'fourier_param_overrides', paramOverrides);
assignin('base', 'use_discrete_perturbation', useDiscretePerturbation);
assignin('base', 'study_pname', {'k'});
assignin('base', 'study_plistarr', {'range(0,3/(N-1),3)'});
assignin('base', 'study_punit', {''});
assignin('base', 'study_sweeptype', 'filled');
assignin('base', 'study_neigs', studyNeigs);
assignin('base', 'study_shift', studyShift);
assignin('base', 'shape_skip', false);
assignin('base', 'shape_skip_reason', '');
end

function ensure_error_log_header(logPath)
if isfile(logPath)
    return;
end
fid = fopen(logPath, 'w');
if fid < 0
    return;
end
cleanupObj = onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid, 'timestamp,index,case_id,shape_file,error_id,error_message\n');
end

function append_error_log(logPath, idx, caseId, shapeFile, ME)
fid = fopen(logPath, 'a');
if fid < 0
    return;
end
cleanupObj = onCleanup(@() fclose(fid)); %#ok<NASGU>
ts = datestr(now, 'yyyy-mm-dd HH:MM:SS');
msg = strrep(char(string(ME.message)), '"', '""');
sid = strrep(char(string(ME.identifier)), '"', '""');
caseId = strrep(char(string(caseId)), '"', '""');
shapeFile = strrep(char(string(shapeFile)), '"', '""');
fprintf(fid, '%s,%d,"%s","%s","%s","%s"\n', ts, idx, caseId, shapeFile, sid, msg);
end

function run_postprocess(rootDir, outDir, pythonCmd, manifestCsv)
postDir = fullfile(rootDir, 'postprocess');
analyzeCmd = sprintf('"%s" "%s" --tbl1-dir "%s" --out-dir "%s" --manifest "%s"', ...
    pythonCmd, fullfile(postDir, 'analyze_bandgaps.py'), fullfile(outDir, 'tbl1_exports'), outDir, manifestCsv);
plotCmd = sprintf('"%s" "%s" --out-dir "%s"', ...
    pythonCmd, fullfile(postDir, 'plot_bandgap_summary.py'), outDir);

fprintf("Running postprocess: analyze_bandgaps.py\n");
[statusAnalyze, outAnalyze] = system(analyzeCmd);
fprintf("%s", outAnalyze);
if statusAnalyze ~= 0
    warning("postprocess analyze failed with exit code %d", statusAnalyze);
    return;
end

fprintf("Running postprocess: plot_bandgap_summary.py\n");
[statusPlot, outPlot] = system(plotCmd);
fprintf("%s", outPlot);
if statusPlot ~= 0
    warning("postprocess plotting failed with exit code %d", statusPlot);
end
end

function out = ternary(cond, a, b)
if cond
    out = a;
else
    out = b;
end
end
