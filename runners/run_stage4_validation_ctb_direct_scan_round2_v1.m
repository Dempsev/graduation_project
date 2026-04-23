rootDir = fileparts(fileparts(mfilename('fullpath')));
addpath(rootDir);
addpath(fullfile(rootDir, 'stage4_validation'));
addpath(fullfile(rootDir, 'stage2_harmonics_refine'));
addpath(fullfile(rootDir, 'stage2_harmonics'));
addpath(fullfile(rootDir, 'model_core'));
addpath(fullfile(rootDir, 'shared'));
addpath(genpath(fullfile(rootDir, 'shared', 'optimization_matlab')));

cfg = get_stage4_validation_config_ctb_direct_scan_round2_v1();
run_stage4_validation_from_manifest(cfg);
