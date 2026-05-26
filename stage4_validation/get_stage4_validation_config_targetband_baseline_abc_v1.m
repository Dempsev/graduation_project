function cfg = get_stage4_validation_config_targetband_baseline_abc_v1()
%GET_STAGE4_VALIDATION_CONFIG_TARGETBAND_BASELINE_ABC_V1
% Config for the shared Stage4 validation manifest covering:
% A. family-balanced random
% B. predictor-only top-6
% C. predictor + local-GA top-6

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
validationDir = fullfile(rootDir, 'data', 'ml_runs', 'targetband_baseline_abc_v1', 'validation_manifest_v1');
outDir = fullfile(rootDir, 'data', 'comsol_batch', 'stage4_validation_targetband_baseline_abc_v1');
cfg = build_stage4_validation_config('stage4_validation_targetband_baseline_abc_v1', validationDir, 'targetband_baseline_abc_manifest_v1.csv', 'targetband_baseline_abc_manifest_summary.json', outDir);
end
