function export_ep17_bilobe_witness_mode_shapes_v1()
%EXPORT_EP17_BILOBE_WITNESS_MODE_SHAPES_V1
% Export lower/upper edge mode shapes for the frozen snake-based bilobe
% witness case ep17_step156 on the validated band220_260 target-band run.

import com.comsol.model.*
import com.comsol.model.util.*

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
addpath(genpath(fullfile(rootDir, 'model_core')));
addpath(genpath(fullfile(rootDir, 'stage2_harmonics')));
addpath(genpath(fullfile(rootDir, 'stage2_harmonics_refine')));
addpath(genpath(fullfile(rootDir, 'stage4_validation')));

cfg = get_stage4_validation_config_bcatp_v2();
mergedCsv = fullfile(rootDir, 'data', 'analysis', 'bilobe_contact_aware_targetband_pilot_v2', ...
    'snake_based_archetype_targetband_pilot_merged_v1.csv');
outDir = fullfile(rootDir, 'data', 'analysis', 'ep17_bilobe_witness_case_v1', 'mode_shapes');
ensure_dir_local(outDir);

if ~isfile(mergedCsv)
    error('export_ep17_bilobe_witness_mode_shapes_v1:MissingMergedCsv', ...
        'Merged csv not found: %s', mergedCsv);
end

rows = readtable(mergedCsv);
targetSampleId = "stage4_validation_bilobe_contact_aware_targetband_pilot_v2_band220_260_ep17_step156_contour_xy_center";
rows = rows(strcmp(string(rows.sample_id), targetSampleId), :);
if isempty(rows)
    error('export_ep17_bilobe_witness_mode_shapes_v1:MissingRow', ...
        'Witness sample row not found in %s', mergedCsv);
end

row = rows(1, :);
sampleId = char(string(row.sample_id(1)));
shapeId = char(string(pick_text(row, {'shape_id', 'shape_id_x', 'shape_id_y'})));
caseLabel = 'ep17_bilobe_witness__band220_260';

fprintf('Exporting mode shapes for %s (%s)\n', caseLabel, shapeId);

pointSpec = build_point_spec_from_row(row);
shapeFile = fullfile(cfg.shapeDir, [shapeId '.csv']);
if ~isfile(shapeFile)
    error('export_ep17_bilobe_witness_mode_shapes_v1:MissingShapeFile', ...
        'Shape file missing: %s', shapeFile);
end

[report, model] = validate_stage2_harmonics_geometry(cfg, pointSpec, shapeFile, sampleId);
if ~report.geometry_valid || ~report.contact_valid || isempty(model)
    error('export_ep17_bilobe_witness_mode_shapes_v1:GeometryInvalid', ...
        'Geometry/contact invalid for %s: %s', caseLabel, char(string(report.error_message)));
end

try
    model = set_material_03(model, cfg);
    model = set_physics_04(model);
    model = set_mesh_05(model);
    model = set_study_06(model);
    try
        model.batch('p2').run('compute');
    catch MEComp
        warning('export_ep17_bilobe_witness_mode_shapes_v1:BatchFallback', ...
            'batch compute failed, fallback to study.run: %s', MEComp.message);
        model.study('std1').run;
    end
    model = set_results_07(model);

    tbl1Path = fullfile(cfg.tbl1Dir, [sampleId '_tbl1.csv']);
    if ~isfile(tbl1Path)
        error('export_ep17_bilobe_witness_mode_shapes_v1:MissingTbl1', ...
            'tbl1 export missing: %s', tbl1Path);
    end

    lowerBand = round(double(pick_numeric(row, {'target_gap_lower_band'})));
    if ~isfinite(lowerBand) || lowerBand < 1
        error('export_ep17_bilobe_witness_mode_shapes_v1:MissingBandPair', ...
            'target_gap_lower_band missing for witness case');
    end

    selectors = locate_gap_edge_selectors_from_tbl1(tbl1Path, lowerBand);
    lowerOut = fullfile(outDir, [sampleId '_lower_edge.png']);
    upperOut = fullfile(outDir, [sampleId '_upper_edge.png']);

    export_mode_shape_image(model, selectors.lower, lowerOut, sprintf('%s lower edge', caseLabel));
    export_mode_shape_image(model, selectors.upper, upperOut, sprintf('%s upper edge', caseLabel));

    summaryTable = struct2table(struct( ...
        'case_label', string(caseLabel), ...
        'sample_id', string(sampleId), ...
        'shape_id', string(shapeId), ...
        'target_band_tag', string(row.target_band_tag(1)), ...
        'target_gap_cover_ratio', double(pick_numeric(row, {'target_gap_cover_ratio'})), ...
        'target_gap_overlap_Hz', double(pick_numeric(row, {'target_gap_overlap_Hz'})), ...
        'target_gap_lower_band', selectors.lower.band_index, ...
        'target_gap_upper_band', selectors.upper.band_index, ...
        'lower_edge_k', selectors.lower.k_value, ...
        'lower_edge_freq_Hz', selectors.lower.freq_value, ...
        'lower_edge_outer_index', selectors.lower.outer_index, ...
        'lower_edge_solnum', selectors.lower.solnum, ...
        'upper_edge_k', selectors.upper.k_value, ...
        'upper_edge_freq_Hz', selectors.upper.freq_value, ...
        'upper_edge_outer_index', selectors.upper.outer_index, ...
        'upper_edge_solnum', selectors.upper.solnum, ...
        'lower_png', string(lowerOut), ...
        'upper_png', string(upperOut) ...
    ), 'AsArray', true);
    writetable(summaryTable, fullfile(outDir, 'ep17_bilobe_witness_mode_shapes_summary_v1.csv'));
finally
    try
        ModelUtil.clear;
    catch
    end
end
end

function pointSpec = build_point_spec_from_row(row)
pointSpec = struct( ...
    'main_id', char(string(pick_text(row, {'main_id'}))), ...
    'point_id', char(string(pick_text(row, {'point_id'}))), ...
    'a1', pick_numeric(row, {'a1'}), ...
    'a2', pick_numeric(row, {'a2'}), ...
    'b1', pick_numeric(row, {'b1'}), ...
    'b2', pick_numeric(row, {'b2'}), ...
    'r0', pick_numeric(row, {'r0'}), ...
    'a3', pick_numeric(row, {'a3'}), ...
    'b3', pick_numeric(row, {'b3'}), ...
    'a4', pick_numeric(row, {'a4'}), ...
    'b4', pick_numeric(row, {'b4'}), ...
    'a5', pick_numeric(row, {'a5'}), ...
    'b5', pick_numeric(row, {'b5'}) ...
);
end

function value = pick_numeric(row, fieldNames)
value = NaN;
for i = 1:numel(fieldNames)
    name = fieldNames{i};
    if ismember(name, row.Properties.VariableNames)
        raw = row.(name)(1);
        num = double(raw);
        if isfinite(num)
            value = num;
            return;
        end
    end
end
end

function value = pick_text(row, fieldNames)
value = "";
for i = 1:numel(fieldNames)
    name = fieldNames{i};
    if ismember(name, row.Properties.VariableNames)
        value = string(row.(name)(1));
        return;
    end
end
end

function selectors = locate_gap_edge_selectors_from_tbl1(tbl1Path, lowerBandIndex)
[kVals, freqVals] = read_tbl1_numeric(tbl1Path);
if isempty(kVals)
    error('locate_gap_edge_selectors_from_tbl1:EmptyData', 'No numeric rows in %s', tbl1Path);
end

[uniqueK, ~, kIdx] = unique(kVals, 'stable');
bandsByK = cell(numel(uniqueK), 1);
maxBands = 0;
for i = 1:numel(uniqueK)
    freq = sort(freqVals(kIdx == i), 'ascend');
    bandsByK{i} = freq(:);
    maxBands = max(maxBands, numel(freq));
end
if maxBands < lowerBandIndex + 1
    error('locate_gap_edge_selectors_from_tbl1:TooFewBands', ...
        'Need at least %d bands in %s', lowerBandIndex + 1, tbl1Path);
end

bandMatrix = nan(numel(uniqueK), maxBands);
for i = 1:numel(uniqueK)
    freq = bandsByK{i};
    bandMatrix(i, 1:numel(freq)) = freq;
end

lowerBand = bandMatrix(:, lowerBandIndex);
upperBand = bandMatrix(:, lowerBandIndex + 1);
if ~any(isfinite(lowerBand)) || ~any(isfinite(upperBand))
    error('locate_gap_edge_selectors_from_tbl1:InvalidEdges', 'Failed to locate finite edges from %s', tbl1Path);
end

[lowerEdgeFreq, lowerOuterIdx] = max(lowerBand);
[upperEdgeFreq, upperOuterIdx] = min(upperBand);

selectors = struct();
selectors.lower = struct( ...
    'edge_name', "lower", ...
    'outer_index', double(lowerOuterIdx), ...
    'solnum', double(lowerBandIndex), ...
    'k_value', double(uniqueK(lowerOuterIdx)), ...
    'band_index', double(lowerBandIndex), ...
    'freq_value', double(lowerEdgeFreq) ...
);
selectors.upper = struct( ...
    'edge_name', "upper", ...
    'outer_index', double(upperOuterIdx), ...
    'solnum', double(lowerBandIndex + 1), ...
    'k_value', double(uniqueK(upperOuterIdx)), ...
    'band_index', double(lowerBandIndex + 1), ...
    'freq_value', double(upperEdgeFreq) ...
);
end

function export_mode_shape_image(model, selector, outPath, figTitle)
fig = figure('Visible', 'off', 'Color', 'white', 'Position', [100, 100, 900, 700]);
cleanupFig = onCleanup(@() close(fig)); %#ok<NASGU>

try
    try
        model.result('pg1').set('outerinput', 'manual');
    catch
    end
    try
        model.result('pg1').set('outersolnum', selector.outer_index);
    catch
    end
    try
        model.result('pg1').set('solnum', selector.solnum);
    catch
    end
    try
        model.result('pg1').run;
    catch
    end
    mphplot(model, 'pg1');
catch ME
    error('export_mode_shape_image:MphplotFailed', ...
        'mphplot failed for %s edge (outer=%d, sol=%d): %s', ...
        char(selector.edge_name), selector.outer_index, selector.solnum, ME.message);
end

ax = gca;
title(ax, sprintf('%s  |  k=%.3f  |  band=%d  |  %.2f Hz', ...
    figTitle, selector.k_value, selector.band_index, selector.freq_value), ...
    'Interpreter', 'none');
axis(ax, 'equal');
axis(ax, 'tight');
set(ax, 'FontSize', 11);
exportgraphics(fig, outPath, 'Resolution', 220);
end

function [kVals, freqVals] = read_tbl1_numeric(tbl1Path)
tbl = readtable(tbl1Path, 'VariableNamingRule', 'preserve');
if width(tbl) < 2
    error('read_tbl1_numeric:TooFewColumns', 'Expected at least 2 columns in %s', tbl1Path);
end

kVals = nan(height(tbl), 1);
freqVals = nan(height(tbl), 1);
for i = 1:height(tbl)
    kVals(i) = parse_numeric_cell(tbl{i, 1});
    freqVals(i) = parse_numeric_cell(tbl{i, 2});
end
mask = isfinite(kVals) & isfinite(freqVals);
kVals = kVals(mask);
freqVals = freqVals(mask);
end

function value = parse_numeric_cell(cellValue)
if isnumeric(cellValue)
    value = double(cellValue(1));
    return;
end
if iscell(cellValue)
    cellValue = cellValue{1};
end
if isstring(cellValue) || ischar(cellValue)
    value = str2double(string(cellValue));
else
    value = NaN;
end
end

function ensure_dir_local(dirPath)
if ~exist(dirPath, 'dir')
    mkdir(dirPath);
end
end
