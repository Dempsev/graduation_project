function result = evaluate_single_shape(cfg, shapeFile, baselineRef)
%EVALUATE_SINGLE_SHAPE Evaluate one stage-1 sample against the trusted mother.
% Returns a single structured result row. Invalid geometry / no-contact /
% solve failures are returned as non-crashing records so the batch can keep
% producing a clean screening table.

if nargin < 2
    shapeFile = '';
end
if nargin < 3
    baselineRef = struct();
end

[shapeId, sampleId] = resolve_ids(cfg, shapeFile);
result = build_empty_result(cfg, sampleId, shapeId);

[geometryReport, model] = validate_geometry(cfg, shapeFile, sampleId);
result.geometry_valid = geometryReport.geometry_valid;
result.contact_valid = geometryReport.contact_valid;
result.contact_length = geometryReport.contact_length;
result.n_domains = geometryReport.n_domains;
result.has_tiny_fragments = geometryReport.has_tiny_fragments;
result.error_message = geometryReport.error_message;

if ~result.geometry_valid || ~result.contact_valid
    result.is_positive_shape = false;
    return;
end

try
    model = set_material_03(model);
    model = set_physics_04(model);
    model = set_mesh_05(model);
    model = set_study_06(model);

    try
        model.batch('p2').run('compute');
    catch MEComp
        warning('evaluate_single_shape:BatchFallback', ...
            'batch compute failed for %s, fallback to study.run: %s', ...
            sampleId, MEComp.message);
        model.study('std1').run;
    end

    model = set_results_07(model);

    if cfg.saveModel
        if ~exist(cfg.modelsDir, 'dir')
            mkdir(cfg.modelsDir);
        end
        mphsave(model, fullfile(cfg.modelsDir, [sampleId '.mph']));
    end

    tbl1Path = fullfile(cfg.tbl1Dir, [sampleId '_tbl1.csv']);
    if ~isfile(tbl1Path)
        error('evaluate_single_shape:MissingTbl1', 'Expected tbl1 export not found: %s', tbl1Path);
    end

    gapMetrics = extract_gap_metrics_from_tbl1(tbl1Path);
    result.solve_success = true;
    result.gap_target_Hz = gapMetrics.gap_target_Hz;
    result.gap_target_rel = gapMetrics.gap_target_rel;
    result.gap_lower_band = gapMetrics.gap_lower_band;
    result.gap_upper_band = gapMetrics.gap_upper_band;
    result.gap_center_freq = gapMetrics.gap_center_freq;
    result.error_message = '';
catch ME
    result.solve_success = false;
    result.error_message = ['solve_failed: ' char(string(ME.message))];
    result.is_positive_shape = false;
    return;
end

if isstruct(baselineRef) && isfield(baselineRef, 'gap_target_Hz') && isfinite(baselineRef.gap_target_Hz)
    result.gap_gain_Hz = result.gap_target_Hz - baselineRef.gap_target_Hz;
    if isfield(baselineRef, 'gap_target_rel') && isfinite(baselineRef.gap_target_rel)
        result.gap_gain_rel = result.gap_target_rel - baselineRef.gap_target_rel;
    end
end

result.is_positive_shape = result.geometry_valid && result.solve_success && ...
    isfinite(result.gap_gain_Hz) && result.gap_gain_Hz > cfg.positiveGapThresholdHz;
end

function [shapeId, sampleId] = resolve_ids(cfg, shapeFile)
if isempty(shapeFile)
    shapeId = cfg.baselineShapeId;
    sampleId = cfg.baselineSampleId;
    return;
end

[~, name, ~] = fileparts(shapeFile);
shapeId = sanitize_id(name);
sampleId = sanitize_id([cfg.fourierId '__' shapeId]);
end

function s = sanitize_id(s)
s = char(string(s));
s = regexprep(s, '[^a-zA-Z0-9_\-]', '_');
s = regexprep(s, '_+', '_');
s = regexprep(s, '^_+|_+$', '');
if isempty(s)
    s = 'stage1_sample';
end
end

function result = build_empty_result(cfg, sampleId, shapeId)
result = struct();
for i = 1:numel(cfg.resultFieldOrder)
    fieldName = cfg.resultFieldOrder{i};
    result.(fieldName) = default_value_for_field(fieldName);
end

result.sample_id = sampleId;
result.fourier_id = cfg.fourierId;
result.shape_id = shapeId;
result.a1 = cfg.paramNumeric.a1;
result.a2 = cfg.paramNumeric.a2;
result.b1 = cfg.paramNumeric.b1;
result.b2 = cfg.paramNumeric.b2;
result.a3 = cfg.paramNumeric.a3;
result.b3 = cfg.paramNumeric.b3;
result.r0 = cfg.paramNumeric.r0;
result.shift = cfg.studyShiftHz;
result.neigs = cfg.studyNeigs;
result.material_case = cfg.materialCase;
end

function value = default_value_for_field(fieldName)
switch fieldName
    case {'sample_id', 'fourier_id', 'shape_id', 'material_case', 'error_message'}
        value = '';
    case {'geometry_valid', 'contact_valid', 'has_tiny_fragments', 'solve_success', 'is_positive_shape'}
        value = false;
    otherwise
        value = NaN;
end
end
