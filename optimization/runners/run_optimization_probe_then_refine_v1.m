function run_optimization_probe_then_refine_v1()
%RUN_OPTIMIZATION_PROBE_THEN_REFINE_V1 Task-oriented entry point for the optimization pipeline.

cfgProbe = get_comsol_in_loop_ga_optimization_probe_config_v1();
if ~isfile(cfgProbe.seedScoredCsv)
    error('run_optimization_probe_then_refine_v1:MissingSeedScoredCsv', ...
        'Optimization seed scoring csv not found: %s', cfgProbe.seedScoredCsv);
end
run_comsol_in_loop_ga_v1(cfgProbe);

cfgRefine = get_comsol_in_loop_ga_optimization_refine_config_v1();
run_comsol_in_loop_ga_v1(cfgRefine);
end
