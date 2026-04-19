rootDir = fileparts(fileparts(mfilename('fullpath')));
addpath(genpath(fullfile(rootDir, 'model_core')));
addpath(genpath(fullfile(rootDir, 'stage2')));
addpath(genpath(fullfile(rootDir, 'stage2_harmonics')));
addpath(genpath(fullfile(rootDir, 'stage2_harmonics_refine')));
addpath(genpath(fullfile(rootDir, 'optimization', 'real_comsol_ga')));
addpath(genpath(fullfile(rootDir, 'optimization', 'runners')));

probeCfg = get_comsol_in_loop_ga_optimization_funnel_probe_config_v1();
if ~isfile(probeCfg.seedScoredCsv)
    error('run_stage3_optimization_champion_funnel_v2:MissingSeedScoredCsv', ...
        'Optimization seed scoring csv not found: %s', probeCfg.seedScoredCsv);
end

run_optimization_champion_funnel_v2();
