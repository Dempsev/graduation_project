rootDir = fileparts(fileparts(mfilename('fullpath')));
addpath(genpath(fullfile(rootDir, 'model_core')));
addpath(genpath(fullfile(rootDir, 'stage2')));
addpath(genpath(fullfile(rootDir, 'stage2_harmonics')));
addpath(genpath(fullfile(rootDir, 'stage2_harmonics_refine')));
addpath(genpath(fullfile(rootDir, 'optimization', 'real_comsol_ga')));

cfg = get_comsol_in_loop_ga_band_supplement_exploratory_v2();
cfg.cooperativeMode = true;

workerId = getenv('COAD_COOP_WORKER_ID');
if strlength(string(workerId)) == 0
    workerId = sprintf('manual_pid%d', feature('getpid'));
end
cfg.cooperativeWorkerId = string(workerId);

run_comsol_in_loop_band_catalog_ga_v1(cfg);
