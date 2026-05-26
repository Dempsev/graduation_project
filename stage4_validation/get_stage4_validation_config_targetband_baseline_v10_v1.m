function cfg = get_stage4_validation_config_targetband_baseline_v10_v1()
%GET_STAGE4_VALIDATION_CONFIG_TARGETBAND_BASELINE_V10_V1
% Config for v10 predictor-only target-band baseline validation.

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
validationDir = fullfile(rootDir, 'data', 'ml_runs', 'targetband_baseline_v10_v1', 'validation_manifest_v1');
outDir = fullfile(rootDir, 'data', 'comsol_batch', 'stage4_validation_targetband_baseline_v10_v1');
cfg = build_stage4_validation_config('stage4_validation_targetband_baseline_v10_v1', validationDir, 'targetband_baseline_v10_manifest_v1.csv', 'targetband_baseline_v10_manifest_summary.json', outDir);
end
