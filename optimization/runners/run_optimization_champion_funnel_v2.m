function run_optimization_champion_funnel_v2()
%RUN_OPTIMIZATION_CHAMPION_FUNNEL_V2
% Adaptive v2 funnel:
% - reuse probe v1 and expansion v1
% - duel keeps a wildcard basin when still competitive
% - champion keeps two basins alive when duel leaders are near-tied

cfgProbe = get_comsol_in_loop_ga_optimization_funnel_probe_config_v1();
if ~isfile(cfgProbe.seedScoredCsv)
    error('run_optimization_champion_funnel_v2:MissingSeedScoredCsv', ...
        'Optimization seed scoring csv not found: %s', cfgProbe.seedScoredCsv);
end
run_stage_if_needed(cfgProbe, 'probe_v1');

cfgExpansion = get_comsol_in_loop_ga_optimization_expansion_config_v1();
run_stage_if_needed(cfgExpansion, 'expansion_v1');

cfgDuel = get_comsol_in_loop_ga_optimization_duel_config_v2();
fprintf('Adaptive duel seeds:\n');
disp(string(cfgDuel.forceSeedShapeIds(:)));
fprintf('  survivors=%d population=%d generations=%d\n', numel(cfgDuel.forceSeedShapeIds), cfgDuel.populationSize, cfgDuel.generations);
run_stage_if_needed(cfgDuel, 'duel_v2');

cfgChampion = get_comsol_in_loop_ga_optimization_champion_config_v2();
fprintf('Adaptive champion seeds:\n');
disp(string(cfgChampion.forceSeedShapeIds(:)));
fprintf('  survivors=%d population=%d generations=%d\n', numel(cfgChampion.forceSeedShapeIds), cfgChampion.populationSize, cfgChampion.generations);
run_stage_if_needed(cfgChampion, 'champion_v2');
end

function run_stage_if_needed(cfg, stageName)
if is_stage_complete(cfg)
    fprintf('Adaptive funnel %s already complete, reusing existing outputs.\n', stageName);
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
