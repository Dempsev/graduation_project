function cfg = get_stage4_validation_config_targetband_v1()
%GET_STAGE4_VALIDATION_CONFIG_TARGETBAND_V1 Config for target-band GA COMSOL validation runs.

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
validationDir = fullfile(rootDir, 'data', 'ml_runs', 'targetband_local_ga_v1', 'band180_220', 'validation_manifest_v1');
outDir = fullfile(rootDir, 'data', 'comsol_batch', 'stage4_validation_targetband_v1');
cfg = build_stage4_validation_config('stage4_validation_targetband_v1', validationDir, 'targetband_ga_validation_manifest_v1.csv', 'targetband_ga_validation_manifest_summary.json', outDir);
end
