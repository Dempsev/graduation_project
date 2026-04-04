rootDir = fileparts(fileparts(mfilename('fullpath')));
addpath(genpath(fullfile(rootDir, 'model_core')));
addpath(genpath(fullfile(rootDir, 'stage2')));
addpath(genpath(fullfile(rootDir, 'stage2_harmonics')));
addpath(genpath(fullfile(rootDir, 'stage2_harmonics_refine')));
addpath(genpath(fullfile(rootDir, 'stage3_optimization_real_ga')));

cfg = get_comsol_in_loop_ga_plan_a_bridge_config_v1();
disp('Plan-A -> Real-GA bridge selected seeds:');
disp(string(cfg.forceSeedShapeIds(:)));

run_comsol_in_loop_ga_v1(cfg);
