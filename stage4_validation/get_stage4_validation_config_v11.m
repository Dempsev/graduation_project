function cfg = get_stage4_validation_config_v11()
%GET_STAGE4_VALIDATION_CONFIG_V11 Config for targeted v11 COMSOL validation runs.

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
validationDir = fullfile(rootDir, 'data', 'ml_runs', 'candidate_pool_seed_discovery_v11', 'validation_manifest_v11');
outDir = fullfile(rootDir, 'data', 'comsol_batch', 'stage4_validation_ab_v11');
cfg = build_stage4_validation_config('stage4_validation_ab_v11', validationDir, 'comsol_validation_manifest_v11.csv', 'validation_manifest_summary.json', outDir);
end
