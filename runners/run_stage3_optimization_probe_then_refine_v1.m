rootDir = fileparts(fileparts(mfilename('fullpath')));
addpath(genpath(fullfile(rootDir, 'model_core')));
addpath(genpath(fullfile(rootDir, 'stage2')));
addpath(genpath(fullfile(rootDir, 'stage2_harmonics')));
addpath(genpath(fullfile(rootDir, 'stage2_harmonics_refine')));
addpath(genpath(fullfile(rootDir, 'optimization', 'real_comsol_ga')));

probeCfg = get_comsol_in_loop_ga_optimization_probe_config_v1();
if ~isfile(probeCfg.seedScoredCsv)
    error('run_stage3_optimization_probe_then_refine_v1:MissingSeedScoredCsv', ...
        'Optimization seed scoring csv not found: %s', probeCfg.seedScoredCsv);
end

disp('Optimization probe config ready:');
fprintf('  seed_scored_csv=%s\n', probeCfg.seedScoredCsv);
fprintf('  top_k=%d population=%d generations=%d\n', probeCfg.topKSeeds, probeCfg.populationSize, probeCfg.generations);
run_comsol_in_loop_ga_v1(probeCfg);

refineCfg = get_comsol_in_loop_ga_optimization_refine_config_v1();
disp('Optimization refine survivor seeds:');
disp(string(refineCfg.forceSeedShapeIds(:)));
fprintf('  survivors=%d population=%d generations=%d\n', numel(refineCfg.forceSeedShapeIds), refineCfg.populationSize, refineCfg.generations);
run_comsol_in_loop_ga_v1(refineCfg);
