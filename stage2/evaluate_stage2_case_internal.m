function result = evaluate_stage2_case_internal(cfg, sampleMeta, pointSpec, refPoint)
%EVALUATE_STAGE2_CASE_INTERNAL Shared worker for stage-2 baseline and shape cases.

if nargin < 4
    refPoint = struct();
end

shapeFile = '';
if isfield(sampleMeta, 'shape_file')
    shapeFile = char(string(sampleMeta.shape_file));
end

result = build_empty_result(cfg, sampleMeta, pointSpec);
[geometryReport, model] = validate_stage2_geometry(cfg, pointSpec, shapeFile, result.sample_id);
result.geometry_valid = geometryReport.geometry_valid;
result.contact_valid = geometryReport.contact_valid;
result.contact_length = geometryReport.contact_length;
result.n_domains = geometryReport.n_domains;
result.has_tiny_fragments = geometryReport.has_tiny_fragments;
result.error_message = geometryReport.error_message;

if ~result.geometry_valid || ~result.contact_valid
    result = apply_reference(result, refPoint);
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
        warning('evaluate_stage2_case_internal:BatchFallback', ...
            'batch compute failed for %s, fallback to study.run: %s', ...
            result.sample_id, MEComp.message);
        model.study('std1').run;
    end

    model = set_results_07(model);

    if cfg.saveModel
        if ~exist(cfg.modelsDir, 'dir')
            mkdir(cfg.modelsDir);
        end
        mphsave(model, fullfile(cfg.modelsDir, [char(result.sample_id) '.mph']));
    end

    tbl1Path = fullfile(cfg.tbl1Dir, [char(result.sample_id) '_tbl1.csv']);
    if ~isfile(tbl1Path)
        error('evaluate_stage2_case_internal:MissingTbl1', 'Expected tbl1 export not found: %s', tbl1Path);
    end

    gapMetrics = extract_stage2_gap_metrics_from_tbl1(tbl1Path);
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
    result = apply_reference(result, refPoint);
    return;
end

result = apply_reference(result, refPoint);
end

function result = build_empty_result(cfg, sampleMeta, pointSpec)
result = struct();
for i = 1:numel(cfg.resultFieldOrder)
    fieldName = cfg.resultFieldOrder{i};
    result.(fieldName) = default_value_for_field(fieldName);
end

result.sample_id = string(sampleMeta.sample_id);
result.candidate_id = string(sampleMeta.candidate_id);
result.shape_id = string(sampleMeta.shape_id);
result.shape_family = string(sampleMeta.shape_family);
result.candidate_role = string(sampleMeta.candidate_role);
result.point_id = string(pointSpec.point_id);
result.a1 = pointSpec.a1;
result.a2 = pointSpec.a2;
result.b2 = pointSpec.b2;
result.r0 = pointSpec.r0;
result.shift = cfg.studyShiftHz;
result.neigs = cfg.studyNeigs;
result.material_case = cfg.materialCase;
end

function value = default_value_for_field(fieldName)
switch fieldName
    case {'sample_id', 'candidate_id', 'shape_id', 'shape_family', 'candidate_role', 'point_id', 'material_case', 'error_message'}
        value = '';
    case {'geometry_valid', 'contact_valid', 'has_tiny_fragments', 'solve_success'}
        value = false;
    otherwise
        value = NaN;
end
end

function result = apply_reference(result, refPoint)
if ~isstruct(refPoint) || isempty(fieldnames(refPoint))
    return;
end
if isfield(refPoint, 'ref_gap_Hz') && isfinite(refPoint.ref_gap_Hz)
    result.ref_gap_Hz = refPoint.ref_gap_Hz;
elseif isfield(refPoint, 'gap_target_Hz') && isfinite(refPoint.gap_target_Hz)
    result.ref_gap_Hz = refPoint.gap_target_Hz;
end
if isfield(refPoint, 'ref_gap_rel') && isfinite(refPoint.ref_gap_rel)
    result.ref_gap_rel = refPoint.ref_gap_rel;
elseif isfield(refPoint, 'gap_target_rel') && isfinite(refPoint.gap_target_rel)
    result.ref_gap_rel = refPoint.gap_target_rel;
end

if result.solve_success && isfinite(result.ref_gap_Hz)
    result.gap_gain_Hz = result.gap_target_Hz - result.ref_gap_Hz;
end
if result.solve_success && isfinite(result.ref_gap_rel)
    result.gap_gain_rel = result.gap_target_rel - result.ref_gap_rel;
end
end
