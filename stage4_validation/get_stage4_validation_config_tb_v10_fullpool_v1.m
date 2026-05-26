function cfg = get_stage4_validation_config_tb_v10_fullpool_v1()
%GET_STAGE4_VALIDATION_CONFIG_TB_V10_FULLPOOL_V1
% Config for v10 expanded-pool predictor baseline validation.

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
validationDir = fullfile(rootDir, 'data', 'ml_runs', 'targetband_baseline_v10_fullpool_v1', 'validation_manifest_v1');
outDir = fullfile(rootDir, 'data', 'comsol_batch', 'stage4_validation_targetband_baseline_v10_fullpool_v1');
cfg = build_stage4_validation_config('stage4_validation_targetband_baseline_v10_fullpool_v1', validationDir, 'targetband_baseline_v10_manifest_v1.csv', 'targetband_baseline_v10_manifest_summary.json', outDir);
end
