function run_optimization_champion_funnel_v4()
%RUN_OPTIMIZATION_CHAMPION_FUNNEL_V4
% Efficiency-first v4 funnel:
% - keep v1's strong probe and expansion budgets
% - keep v2's robust duel/champion promotion logic
% - use the updated optimization-memory-aware seed ranking
% - evaluate against budget-efficiency metrics instead of only final best.

cfgProbe = get_comsol_in_loop_ga_optimization_funnel_probe_config_v4();
if ~isfile(cfgProbe.seedScoredCsv)
    error('run_optimization_champion_funnel_v4:MissingSeedScoredCsv', ...
        'Optimization seed scoring csv not found: %s', cfgProbe.seedScoredCsv);
end
run_stage_if_needed(cfgProbe, 'probe_v4');

cfgExpansion = get_comsol_in_loop_ga_optimization_expansion_config_v4();
run_stage_if_needed(cfgExpansion, 'expansion_v4');

cfgDuel = get_comsol_in_loop_ga_optimization_duel_config_v4();
fprintf('Efficiency-first duel seeds:\n');
disp(string(cfgDuel.forceSeedShapeIds(:)));
fprintf('  survivors=%d population=%d generations=%d\n', numel(cfgDuel.forceSeedShapeIds), cfgDuel.populationSize, cfgDuel.generations);
run_stage_if_needed(cfgDuel, 'duel_v4');

cfgChampion = get_comsol_in_loop_ga_optimization_champion_config_v4();
fprintf('Efficiency-first champion seeds:\n');
disp(string(cfgChampion.forceSeedShapeIds(:)));
fprintf('  survivors=%d population=%d generations=%d\n', numel(cfgChampion.forceSeedShapeIds), cfgChampion.populationSize, cfgChampion.generations);
run_stage_if_needed(cfgChampion, 'champion_v4');
end

function run_stage_if_needed(cfg, stageName)
if is_stage_complete(cfg)
    fprintf('Efficiency-first funnel %s already complete, reusing existing outputs.\n', stageName);
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
