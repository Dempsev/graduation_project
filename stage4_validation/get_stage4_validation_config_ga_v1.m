function cfg = get_stage4_validation_config_ga_v1()
%GET_STAGE4_VALIDATION_CONFIG_GA_V1 Config for GA-guided COMSOL validation runs.

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
validationDir = fullfile(rootDir, 'data', 'ml_runs', 'candidate_pool_seed_discovery_v10', 'ga_parametric_search_v1', 'validation_manifest_v1');
outDir = fullfile(rootDir, 'data', 'comsol_batch', 'stage4_validation_ab_ga_v1');
cfg = build_stage4_validation_config('stage4_validation_ab_ga_v1', validationDir, 'ga_validation_manifest_v1.csv', 'ga_validation_manifest_summary.json', outDir);
end
