function cfg = get_stage4_validation_config_v4()
%GET_STAGE4_VALIDATION_CONFIG Config for A/B COMSOL validation runs.
% Reuses the stable harmonics-refine physics chain, but replaces candidate
% generation with a fixed validation manifest exported from the cascade
% versus surrogate-only ranking comparison.

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
baseCfg = get_stage2_harmonics_refine_config();

cfg = baseCfg;
cfg.validationId = 'stage4_validation_ab_v4';
cfg.outDir = fullfile(rootDir, 'data', 'comsol_batch', 'stage4_validation_ab_v4');
cfg.tbl1Dir = fullfile(cfg.outDir, 'tbl1_exports');
cfg.modelsDir = fullfile(cfg.outDir, 'models');
cfg.logsDir = fullfile(cfg.outDir, 'logs');
cfg.plotDir = fullfile(cfg.outDir, 'plots');
cfg.bandPlotDir = fullfile(cfg.plotDir, 'band_diagrams');

validationDir = fullfile(rootDir, 'data', 'ml_runs', 'candidate_pool_cascade_v4', 'validation_manifest_v4');
cfg.validationDir = validationDir;
cfg.validationManifestCsv = fullfile(validationDir, 'comsol_validation_manifest_v4.csv');
cfg.validationSummaryJson = fullfile(validationDir, 'validation_manifest_summary.json');

cfg.pointManifestCsv = fullfile(cfg.outDir, 'stage4_validation_point_manifest.csv');
cfg.baselineByPointMat = fullfile(cfg.outDir, 'baseline_by_point.mat');
cfg.baselineByPointCsv = fullfile(cfg.outDir, 'baseline_by_point.csv');
cfg.resultsMat = fullfile(cfg.outDir, 'stage4_validation_results.mat');
cfg.resultsCsv = fullfile(cfg.outDir, 'stage4_validation_results.csv');
cfg.armSummaryCsv = fullfile(cfg.outDir, 'stage4_validation_arm_summary.csv');
cfg.pointSummaryCsv = fullfile(cfg.outDir, 'stage4_validation_point_summary.csv');
cfg.shapeSummaryCsv = fullfile(cfg.outDir, 'stage4_validation_shape_summary.csv');

cfg.fourierId = cfg.validationId;
cfg.saveModel = false;
cfg.enableBandPlots = false;

cfg.resultFieldOrder = { ...
    'sample_id', 'validation_id', 'selection_source', 'selection_label', 'rank_within_source', ...
    'source_sample_id', ...
    'shape_id', 'shape_family', 'shape_role', 'candidate_id', 'main_id', 'point_id', ...
    'pool_arm', 'point_strategy', 'family_prior_source', ...
    'a1', 'a2', 'b1', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5', 'r0', ...
    'shift', 'neigs', 'material_case', ...
    'contact_prob', 'positive_prob', 'surrogate_pred_gap34_gain_Hz', 'class_score', 'cascade_score', ...
    'contact_gate', 'positive_gate', 'reg_positive_gate', 'cascade_gate', ...
    'rank_cascade', 'rank_surrogate', ...
    'geometry_valid', 'contact_valid', 'contact_length', 'n_domains', 'has_tiny_fragments', ...
    'solve_success', ...
    'gap34_Hz', 'gap34_rel', 'gap34_lower_edge_Hz', 'gap34_upper_edge_Hz', 'gap34_center_freq', ...
    'ref_gap34_Hz', 'ref_gap34_rel', 'gap34_gain_Hz', 'gap34_gain_rel', ...
    'max_gap_Hz', 'max_gap_rel', 'max_gap_lower_band', 'max_gap_upper_band', 'max_gap_center_freq', ...
    'error_message' ...
};

manifestSig = file_signature(cfg.validationManifestCsv);
summarySig = file_signature(cfg.validationSummaryJson);
cfg.configSignature = strjoin({ ...
    cfg.validationId, ...
    sprintf('fixed_gap_band=%d', cfg.fixedGapBand), ...
    sprintf('shift=%.12g', cfg.studyShiftHz), ...
    sprintf('neigs=%d', cfg.studyNeigs), ...
    cfg.materialCase, ...
    ['manifest=' manifestSig], ...
    ['summary=' summarySig] ...
}, ';');

ensure_dir(cfg.outDir);
ensure_dir(cfg.tbl1Dir);
ensure_dir(cfg.logsDir);
ensure_dir(cfg.plotDir);
if cfg.saveModel
    ensure_dir(cfg.modelsDir);
end
end

function ensure_dir(pathStr)
if ~exist(pathStr, 'dir')
    mkdir(pathStr);
end
end

function sig = file_signature(pathStr)
if ~isfile(pathStr)
    sig = 'missing';
    return;
end
info = dir(pathStr);
sig = sprintf('%s|%d|%s', pathStr, info.bytes, info.date);
end
