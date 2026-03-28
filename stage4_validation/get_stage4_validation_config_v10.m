function cfg = get_stage4_validation_config_v10()
%GET_STAGE4_VALIDATION_CONFIG_V10 Config for targeted v10 COMSOL validation runs.

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
validationDir = fullfile(rootDir, 'data', 'ml_runs', 'candidate_pool_seed_discovery_v10', 'validation_manifest_v10');
outDir = fullfile(rootDir, 'data', 'comsol_batch', 'stage4_validation_ab_v10');
cfg = build_stage4_validation_config('stage4_validation_ab_v10', validationDir, 'comsol_validation_manifest_v10.csv', 'validation_manifest_summary.json', outDir);
end
