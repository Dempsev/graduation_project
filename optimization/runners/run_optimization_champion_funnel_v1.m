function run_optimization_champion_funnel_v1()
%RUN_OPTIMIZATION_CHAMPION_FUNNEL_V1 Task-oriented entry point for the
% aggressive 20 -> 4 -> 2 -> 1 champion-funnel optimization pipeline.

cfgProbe = get_comsol_in_loop_ga_optimization_funnel_probe_config_v1();
if ~isfile(cfgProbe.seedScoredCsv)
    error('run_optimization_champion_funnel_v1:MissingSeedScoredCsv', ...
        'Optimization seed scoring csv not found: %s', cfgProbe.seedScoredCsv);
end
run_stage_if_needed(cfgProbe, 'probe');

cfgExpansion = get_comsol_in_loop_ga_optimization_expansion_config_v1();
run_stage_if_needed(cfgExpansion, 'expansion');

cfgDuel = get_comsol_in_loop_ga_optimization_duel_config_v1();
run_stage_if_needed(cfgDuel, 'duel');

cfgChampion = get_comsol_in_loop_ga_optimization_champion_config_v1();
run_stage_if_needed(cfgChampion, 'champion');
end

function run_stage_if_needed(cfg, stageName)
if is_stage_complete(cfg)
    fprintf('Champion funnel %s already complete, reusing existing outputs.\n', stageName);
    fprintf('  history_csv=%s\n', cfg.historyCsv);
    fprintf('  search_summary_csv=%s\n', cfg.searchSummaryCsv);
    return;
end
run_comsol_in_loop_ga_v1(cfg);
end

function tf = is_stage_complete(cfg)
tf = false;
requiredFiles = {cfg.historyCsv, cfg.searchSummaryCsv};
for i = 1:numel(requiredFiles)
    if ~isfile(requiredFiles{i})
        return;
    end
end

try
    historyTbl = readtable(cfg.historyCsv);
    searchTbl = readtable(cfg.searchSummaryCsv);
catch
    return;
end

expectedHistoryRows = cfg.topKSeeds * cfg.populationSize * cfg.generations;
expectedSearchRows = cfg.topKSeeds;
tf = height(historyTbl) >= expectedHistoryRows && height(searchTbl) >= expectedSearchRows;
end
