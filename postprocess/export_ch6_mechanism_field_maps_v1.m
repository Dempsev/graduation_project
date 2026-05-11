function export_ch6_mechanism_field_maps_v1()
%EXPORT_CH6_MECHANISM_FIELD_MAPS_V1
% Export strain-energy-density and von-Mises-stress field maps for the
% Chapter 6 mechanism layer.

import com.comsol.model.*
import com.comsol.model.util.*

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
addpath(genpath(fullfile(rootDir, 'model_core')));
addpath(genpath(fullfile(rootDir, 'stage2_harmonics')));
addpath(genpath(fullfile(rootDir, 'stage2_harmonics_refine')));
addpath(genpath(fullfile(rootDir, 'stage4_validation')));

canonicalCfg = get_stage4_validation_config_targetband_local_robustness_v1();
ep17Cfg = get_stage4_validation_config_sbatp_v1();
archetypeCfg = get_stage4_validation_config_satbp_v1();

canonicalCsv = fullfile(rootDir, 'data', 'analysis', 'canonical_local_robustness_v1', 'canonical_local_robustness_merged_v1.csv');
ep17ResultsCsv = fullfile(rootDir, 'data', 'comsol_batch', 'stage4_validation_ep17_bilobe_family_targetband_probe_v1', 'stage4_validation_results.csv');
archetypeCsv = fullfile(rootDir, 'data', 'analysis', 'shape_archetype_targetband_pilot_v1', 'shape_archetype_targetband_pilot_merged_v1.csv');

outDir = fullfile(rootDir, 'data', 'analysis', 'ch6_mechanism_field_maps_v1');
ensure_dir_local(outDir);

fieldSpecs = [
    struct('field_tag', "strain_energy_density", 'expr', "solid.Ws", 'plot_tag', "pg_ch6_ws", 'display_name', "Strain energy density")
    struct('field_tag', "von_mises_stress", 'expr', "solid.mises", 'plot_tag', "pg_ch6_mises", 'display_name', "von Mises stress")
];

summaryRows = {};

if isfile(canonicalCsv)
    rows = readtable(canonicalCsv);
    rows = rows(strcmp(string(rows.canonical_variant), "center"), :);
    rows = sortrows(rows, {'target_band_low_Hz', 'canonical_case_id'}, {'ascend', 'ascend'});
    for i = 1:height(rows)
        row = rows(i, :);
        caseLabel = char(string(row.canonical_case_id(1)));
        sampleId = char(string(row.sample_id(1)));
        shapeId = char(string(row.shape_id(1)));
        fprintf('[canonical %d/%d] exporting field maps for %s (%s)\n', i, height(rows), caseLabel, shapeId);
        caseOutDir = fullfile(outDir, 'canonical_mode_shapes_v1', caseLabel);
        [summaryRows] = export_case_field_maps(summaryRows, canonicalCfg, row, sampleId, shapeId, caseLabel, caseOutDir, ...
            canonicalCsv, "canonical_mode_shapes_v1", "fixed_gap_band", canonicalCfg.fixedGapBand, fieldSpecs);
    end
else
    warning('export_ch6_mechanism_field_maps_v1:MissingCanonicalCsv', ...
        'Canonical robustness csv not found: %s', canonicalCsv);
end

if isfile(ep17ResultsCsv)
    rows = readtable(ep17ResultsCsv);
    targetSampleId = "stage4_validation_ep17_bilobe_family_targetband_probe_v1_band220_260_ep17_step156_contour_xy_center";
    rows = rows(strcmp(string(rows.sample_id), targetSampleId), :);
    if ~isempty(rows)
        row = rows(1, :);
        sampleId = char(string(row.sample_id(1)));
        shapeId = char(string(pick_text(row, {'shape_id', 'shape_id_x', 'shape_id_y'})));
        caseLabel = 'ep17_bilobe_witness__band220_260';
        fprintf('[ep17] exporting field maps for %s (%s)\n', caseLabel, shapeId);
        caseOutDir = fullfile(outDir, 'ep17_bilobe_witness_case_v1', caseLabel);
        [summaryRows] = export_case_field_maps(summaryRows, ep17Cfg, row, sampleId, shapeId, caseLabel, caseOutDir, ...
            ep17ResultsCsv, "ep17_bilobe_witness_case_v1", "validation_id", NaN, fieldSpecs);
    else
        warning('export_ch6_mechanism_field_maps_v1:MissingEp17Row', ...
            'Witness sample row not found in %s', ep17ResultsCsv);
    end
else
    warning('export_ch6_mechanism_field_maps_v1:MissingEp17Csv', ...
        'Ep17 results csv not found: %s', ep17ResultsCsv);
end

if isfile(archetypeCsv)
    rows = readtable(archetypeCsv);
    selectedIds = [ ...
        "stage4_validation_shape_archetype_targetband_pilot_v1_band220_260_pbi195_center"; ...
        "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pas130_center"; ...
        "stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pne253_center" ...
    ];
    rows = rows(ismember(string(rows.sample_id), selectedIds), :);
    for i = 1:height(rows)
        row = rows(i, :);
        sampleId = char(string(row.sample_id(1)));
        shapeId = char(string(pick_text(row, {'shape_id', 'shape_id_x', 'shape_id_y'})));
        caseLabel = sprintf('%s__%s__%s', ...
            char(string(row.target_band_tag(1))), ...
            char(string(row.pilot_archetype_tag(1))), ...
            char(string(row.pilot_seed_family(1))));
        fprintf('[archetype %d/%d] exporting field maps for %s (%s)\n', i, height(rows), caseLabel, shapeId);
        caseOutDir = fullfile(outDir, 'shape_archetype_targetband_mode_shapes_v1', caseLabel);
        [summaryRows] = export_case_field_maps(summaryRows, archetypeCfg, row, sampleId, shapeId, caseLabel, caseOutDir, ...
            archetypeCsv, "shape_archetype_targetband_mode_shapes_v1", "target_gap_lower_band", NaN, fieldSpecs);
    end
else
    warning('export_ch6_mechanism_field_maps_v1:MissingArchetypeCsv', ...
        'Shape archetype csv not found: %s', archetypeCsv);
end

if ~isempty(summaryRows)
    summaryTable = struct2table([summaryRows{:}], 'AsArray', true);
    writetable(summaryTable, fullfile(outDir, 'ch6_mechanism_field_maps_summary_v1.csv'));
end
end

function summaryRows = export_case_field_maps(summaryRows, cfg, row, sampleId, shapeId, caseLabel, caseOutDir, sourceCsv, sourceGroup, bandFieldName, fixedBandIndex, fieldSpecs)
ensure_dir_local(caseOutDir);

pointSpec = build_point_spec_from_row(row);
shapeFile = fullfile(cfg.shapeDir, [shapeId '.csv']);
if ~isfile(shapeFile)
    warning('export_ch6_mechanism_field_maps_v1:MissingShapeFile', ...
        'Shape file missing for %s: %s', caseLabel, shapeFile);
    return;
end

try
    [report, model] = validate_stage2_harmonics_geometry(cfg, pointSpec, shapeFile, sampleId);
    if ~report.geometry_valid || ~report.contact_valid || isempty(model)
        warning('export_ch6_mechanism_field_maps_v1:GeometryInvalid', ...
            'Geometry/contact invalid for %s: %s', caseLabel, char(string(report.error_message)));
        return;
    end

    try
        model = set_material_03(model, cfg);
        model = set_physics_04(model);
        model = set_mesh_05(model);
        model = set_study_06(model);
        try
            model.batch('p2').run('compute');
        catch MEComp
            warning('export_ch6_mechanism_field_maps_v1:BatchFallback', ...
                'batch compute failed for %s, fallback to study.run: %s', caseLabel, MEComp.message);
            model.study('std1').run;
        end
        model = set_results_07(model);

        tbl1Path = fullfile(cfg.tbl1Dir, [sampleId '_tbl1.csv']);
        if ~isfile(tbl1Path)
            warning('export_ch6_mechanism_field_maps_v1:MissingTbl1', ...
                'tbl1 export missing: %s', tbl1Path);
            return;
        end

        selectors = select_gap_edges_from_case(row, tbl1Path, bandFieldName, fixedBandIndex);
        fieldPlotTags = create_scalar_field_plot_groups(model, fieldSpecs);

        for edgeName = {'lower', 'upper'}
            selector = selectors.(char(edgeName{1}));
            for f = 1:numel(fieldSpecs)
                spec = fieldSpecs(f);
                fieldOut = fullfile(caseOutDir, sprintf('%s_%s_%s.png', sampleId, char(edgeName{1}), char(spec.field_tag)));
                export_scalar_field_image(model, char(spec.plot_tag), selector, fieldOut, sprintf('%s %s %s', caseLabel, char(edgeName{1}), char(spec.display_name)));
                summaryRows{end + 1} = struct( ...
                    'source_group', string(sourceGroup), ...
                    'source_csv', string(sourceCsv), ...
                    'case_label', string(caseLabel), ...
                    'sample_id', string(sampleId), ...
                    'shape_id', string(shapeId), ...
                    'edge_name', string(edgeName{1}), ...
                    'field_tag', string(spec.field_tag), ...
                    'field_expr', string(spec.expr), ...
                    'field_plot_tag', string(fieldPlotTags.(char(spec.field_tag))), ...
                    'target_band_tag', string(pick_text(row, {'target_band_tag'})), ...
                    'band_field_name', string(bandFieldName), ...
                    'band_index', double(selector.band_index), ...
                    'k_value', double(selector.k_value), ...
                    'freq_value_Hz', double(selector.freq_value), ...
                    'outer_index', double(selector.outer_index), ...
                    'solnum', double(selector.solnum), ...
                    'png_path', string(fieldOut) ...
                ); %#ok<AGROW>
            end
        end
    catch ME
        warning('export_ch6_mechanism_field_maps_v1:CaseFailed', ...
            'Case %s failed: %s', caseLabel, ME.message);
    end
finally
    try
        ModelUtil.clear;
    catch
    end
end
end

function fieldPlotTags = create_scalar_field_plot_groups(model, fieldSpecs)
fieldPlotTags = struct();
for i = 1:numel(fieldSpecs)
    spec = fieldSpecs(i);
    tag = char(spec.plot_tag);
    label = char(spec.display_name);
    expr = char(spec.expr);
    plotExpr = sprintf('max(0,gpeval(4,%s))', expr);
    try
        model.result.create(tag, 'PlotGroup2D');
    catch
        try
            model.result.remove(tag);
            model.result.create(tag, 'PlotGroup2D');
        catch ME
            error('create_scalar_field_plot_groups:CreateFailed', ...
                'Failed to create plot group %s: %s', tag, ME.message);
        end
    end
    model.result(tag).set('data', 'dset2');
    model.result(tag).label(label);
    model.result(tag).create('surf1', 'Surface');
    try
        model.result(tag).feature('surf1').set('expr', {plotExpr});
    catch
        model.result(tag).feature('surf1').set('expr', {expr});
    end
    try
        model.result(tag).feature('surf1').create('def', 'Deform');
    catch
    end
    fieldPlotTags.(char(spec.field_tag)) = tag;
end
end

function export_scalar_field_image(model, plotTag, selector, outPath, figTitle)
fig = figure('Visible', 'off', 'Color', 'white', 'Position', [100, 100, 900, 700]);
cleanupFig = onCleanup(@() close(fig)); %#ok<NASGU>

try
    try
        model.result(plotTag).set('outerinput', 'manual');
    catch
    end
    try
        model.result(plotTag).set('outersolnum', selector.outer_index);
    catch
    end
    try
        model.result(plotTag).set('solnum', selector.solnum);
    catch
    end
    try
        model.result(plotTag).run;
    catch
    end
    mphplot(model, plotTag);
catch ME
    error('export_scalar_field_image:MphplotFailed', ...
        'mphplot failed for %s edge (outer=%d, sol=%d): %s', ...
        char(selector.edge_name), selector.outer_index, selector.solnum, ME.message);
end

ax = gca;
title(ax, sprintf('%s  |  k=%.3f  |  band=%d  |  %.2f Hz', ...
    figTitle, selector.k_value, selector.band_index, selector.freq_value), ...
    'Interpreter', 'none');
axis(ax, 'equal');
axis(ax, 'tight');
set(ax, 'FontName', 'Times New Roman', 'FontSize', 12);
exportgraphics(fig, outPath, 'Resolution', 240);
end

function selectors = select_gap_edges_from_case(row, tbl1Path, bandFieldName, fixedBandIndex)
if strcmpi(bandFieldName, 'fixed_gap_band')
    if ~isfinite(fixedBandIndex) || fixedBandIndex < 1
        error('select_gap_edges_from_case:MissingFixedBand', 'Missing fixed band index for %s', char(string(row.sample_id(1))));
    end
    selectors = locate_fixed_gap_edge_selectors_from_tbl1(tbl1Path, round(double(fixedBandIndex)));
    return;
end

if strcmpi(bandFieldName, 'validation_id')
    [targetLowHz, targetHighHz] = parse_band_tag_from_validation_id(string(row.validation_id(1)));
    lowerBand = locate_target_gap_band_index_from_tbl1(tbl1Path, targetLowHz, targetHighHz);
    selectors = locate_gap_edge_selectors_from_tbl1(tbl1Path, lowerBand);
    return;
end

if strcmpi(bandFieldName, 'target_gap_lower_band')
    lowerBand = round(double(pick_numeric(row, {'target_gap_lower_band'})));
    if ~isfinite(lowerBand) || lowerBand < 1
        lowerBand = infer_lower_band_from_row(row, tbl1Path);
    end
    selectors = locate_gap_edge_selectors_from_tbl1(tbl1Path, lowerBand);
    return;
end

error('select_gap_edges_from_case:UnsupportedBandField', 'Unsupported band field name: %s', bandFieldName);
end

function lowerBand = infer_lower_band_from_row(row, tbl1Path)
if ismember('validation_id', row.Properties.VariableNames)
    try
        [targetLowHz, targetHighHz] = parse_band_tag_from_validation_id(string(row.validation_id(1)));
        lowerBand = locate_target_gap_band_index_from_tbl1(tbl1Path, targetLowHz, targetHighHz);
        return;
    catch
    end
end
if ismember('target_band_tag', row.Properties.VariableNames)
    tag = char(string(row.target_band_tag(1)));
    tokens = regexp(tag, 'band(\d+)_(\d+)', 'tokens', 'once');
    if ~isempty(tokens)
        targetLowHz = str2double(tokens{1});
        targetHighHz = str2double(tokens{2});
        lowerBand = locate_target_gap_band_index_from_tbl1(tbl1Path, targetLowHz, targetHighHz);
        return;
    end
end
error('infer_lower_band_from_row:NoBandInfo', ...
    'Could not infer target gap band from row %s', char(string(row.sample_id(1))));
end

function selectors = locate_fixed_gap_edge_selectors_from_tbl1(tbl1Path, lowerBandIndex)
[kVals, freqVals] = read_tbl1_numeric(tbl1Path);
if isempty(kVals)
    error('locate_fixed_gap_edge_selectors_from_tbl1:EmptyData', 'No numeric rows in %s', tbl1Path);
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
    error('locate_fixed_gap_edge_selectors_from_tbl1:TooFewBands', ...
        'Need at least %d bands in %s', lowerBandIndex + 1, tbl1Path);
end
bandMatrix = nan(numel(uniqueK), maxBands);
for i = 1:numel(uniqueK)
    freq = bandsByK{i};
    bandMatrix(i, 1:numel(freq)) = freq;
end
lowerBand = bandMatrix(:, lowerBandIndex);
upperBand = bandMatrix(:, lowerBandIndex + 1);
[lowerEdgeFreq, lowerOuterIdx] = max(lowerBand);
[upperEdgeFreq, upperOuterIdx] = min(upperBand);
if ~isfinite(lowerEdgeFreq) || ~isfinite(upperEdgeFreq)
    error('locate_fixed_gap_edge_selectors_from_tbl1:InvalidEdges', 'Failed to locate finite gap edges from %s', tbl1Path);
end
selectors = struct();
selectors.lower = struct('edge_name', "lower", 'outer_index', double(lowerOuterIdx), 'solnum', double(lowerBandIndex), 'k_value', double(uniqueK(lowerOuterIdx)), 'band_index', double(lowerBandIndex), 'freq_value', double(lowerEdgeFreq));
selectors.upper = struct('edge_name', "upper", 'outer_index', double(upperOuterIdx), 'solnum', double(lowerBandIndex + 1), 'k_value', double(uniqueK(upperOuterIdx)), 'band_index', double(lowerBandIndex + 1), 'freq_value', double(upperEdgeFreq));
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
selectors.lower = struct('edge_name', "lower", 'outer_index', double(lowerOuterIdx), 'solnum', double(lowerBandIndex), 'k_value', double(uniqueK(lowerOuterIdx)), 'band_index', double(lowerBandIndex), 'freq_value', double(lowerEdgeFreq));
selectors.upper = struct('edge_name', "upper", 'outer_index', double(upperOuterIdx), 'solnum', double(lowerBandIndex + 1), 'k_value', double(uniqueK(upperOuterIdx)), 'band_index', double(lowerBandIndex + 1), 'freq_value', double(upperEdgeFreq));
end

function [targetLowHz, targetHighHz] = parse_band_tag_from_validation_id(validationId)
tokens = regexp(char(validationId), 'band(\d+)_(\d+)', 'tokens', 'once');
if isempty(tokens)
    error('parse_band_tag_from_validation_id:InvalidValidationId', ...
        'Could not parse target band from validation id: %s', char(validationId));
end
targetLowHz = str2double(tokens{1});
targetHighHz = str2double(tokens{2});
end

function lowerBandIndex = locate_target_gap_band_index_from_tbl1(tbl1Path, targetLowHz, targetHighHz)
[kVals, freqVals] = read_tbl1_numeric(tbl1Path);
if isempty(kVals)
    error('locate_target_gap_band_index_from_tbl1:EmptyData', 'No numeric rows in %s', tbl1Path);
end
[uniqueK, ~, kIdx] = unique(kVals, 'stable');
bandsByK = cell(numel(uniqueK), 1);
maxBands = 0;
for i = 1:numel(uniqueK)
    freq = sort(freqVals(kIdx == i), 'ascend');
    bandsByK{i} = freq(:);
    maxBands = max(maxBands, numel(freq));
end
if maxBands < 2
    error('locate_target_gap_band_index_from_tbl1:TooFewBands', 'Need at least two bands in %s', tbl1Path);
end
bandMatrix = nan(numel(uniqueK), maxBands);
for i = 1:numel(uniqueK)
    freq = bandsByK{i};
    bandMatrix(i, 1:numel(freq)) = freq;
end
bestOverlap = -inf;
bestWidth = -inf;
bestLowerBand = NaN;
for bandIdx = 1:(maxBands - 1)
    lowerBand = bandMatrix(:, bandIdx);
    upperBand = bandMatrix(:, bandIdx + 1);
    if ~any(isfinite(lowerBand)) || ~any(isfinite(upperBand))
        continue;
    end
    lowerEdge = max(lowerBand(isfinite(lowerBand)));
    upperEdge = min(upperBand(isfinite(upperBand)));
    gapWidth = upperEdge - lowerEdge;
    if gapWidth <= 0
        continue;
    end
    overlap = max(0.0, min(upperEdge, targetHighHz) - max(lowerEdge, targetLowHz));
    if overlap > bestOverlap + 1e-12 || (abs(overlap - bestOverlap) <= 1e-12 && gapWidth > bestWidth)
        bestOverlap = overlap;
        bestWidth = gapWidth;
        bestLowerBand = bandIdx;
    end
end
if ~isfinite(bestLowerBand)
    error('locate_target_gap_band_index_from_tbl1:NoOverlap', ...
        'Could not determine target gap index from %s for band %.1f-%.1f', tbl1Path, targetLowHz, targetHighHz);
end
lowerBandIndex = round(bestLowerBand);
end

function pointSpec = build_point_spec_from_row(row)
pointSpec = struct( ...
    'main_id', char(string(pick_text(row, {'main_id'}))), ...
    'point_id', char(string(pick_text(row, {'point_id'}))), ...
    'a1', pick_numeric(row, {'a1_y', 'a1_x', 'a1'}), ...
    'a2', pick_numeric(row, {'a2_y', 'a2_x', 'a2'}), ...
    'b1', pick_numeric(row, {'b1'}), ...
    'b2', pick_numeric(row, {'b2_y', 'b2_x', 'b2'}), ...
    'r0', pick_numeric(row, {'r0_y', 'r0_x', 'r0'}), ...
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
