thisFile = mfilename('fullpath');
thisDir = fileparts(thisFile);
rootDir = fileparts(thisDir);
addpath(rootDir);
addpath(fullfile(rootDir, 'stage4_validation'));
addpath(fullfile(rootDir, 'stage2_harmonics_refine'));
addpath(fullfile(rootDir, 'model_core'));
addpath(fullfile(rootDir, 'stage2_harmonics'));

cfg = get_stage4_validation_config_sbatp_v1();
run_stage4_validation_from_manifest(cfg, 19, 18);
