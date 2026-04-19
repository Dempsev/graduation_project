function run_optimization_champion_funnel_v3()
%RUN_OPTIMIZATION_CHAMPION_FUNNEL_V3
% Champion funnel v3:
% - reuse completed probe v1 and expansion v1
% - reuse adaptive duel v2
% - replace the last-stage GA with a local trust-region style champion
%   search that uses predictor-guided prescreening.

cfgProbe = get_comsol_in_loop_ga_optimization_funnel_probe_config_v1();
if ~isfile(cfgProbe.seedScoredCsv)
    error('run_optimization_champion_funnel_v3:MissingSeedScoredCsv', ...
        'Optimization seed scoring csv not found: %s', cfgProbe.seedScoredCsv);
end
run_standard_stage_if_needed(cfgProbe, 'probe_v1');

cfgExpansion = get_comsol_in_loop_ga_optimization_expansion_config_v1();
run_standard_stage_if_needed(cfgExpansion, 'expansion_v1');

cfgDuel = get_comsol_in_loop_ga_optimization_duel_config_v2();
fprintf('Adaptive duel seeds for v3 champion route:\n');
disp(string(cfgDuel.forceSeedShapeIds(:)));
fprintf('  survivors=%d population=%d generations=%d\n', numel(cfgDuel.forceSeedShapeIds), cfgDuel.populationSize, cfgDuel.generations);
run_standard_stage_if_needed(cfgDuel, 'duel_v2');

cfgChampion = get_comsol_in_loop_ga_optimization_champion_local_config_v3();
fprintf('Champion local v3 seeds:\n');
disp(string(cfgChampion.forceSeedShapeIds(:)));
fprintf('  survivors=%d evals_per_iteration=%d iterations_per_seed=%d proposals_per_iteration=%d\n', ...
    numel(cfgChampion.forceSeedShapeIds), cfgChampion.evalsPerIteration, cfgChampion.iterationsPerSeed, cfgChampion.proposalsPerIteration);
run_local_stage_if_needed(cfgChampion, 'champion_local_v3');
end

function run_standard_stage_if_needed(cfg, stageName)
if is_standard_stage_complete(cfg)
    fprintf('Champion funnel v3 %s already complete, reusing existing outputs.\n', stageName);
    fprintf('  history_csv=%s\n', cfg.historyCsv);
    fprintf('  search_summary_csv=%s\n', cfg.searchSummaryCsv);
    return;
end
run_comsol_in_loop_ga_v1(cfg);
end

function tf = is_standard_stage_complete(cfg)
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

function run_local_stage_if_needed(cfg, stageName)
if is_local_stage_complete(cfg)
    fprintf('Champion funnel v3 %s already complete, reusing existing outputs.\n', stageName);
    fprintf('  history_csv=%s\n', cfg.historyCsv);
    fprintf('  search_summary_csv=%s\n', cfg.searchSummaryCsv);
    return;
end
run_comsol_in_loop_champion_local_v3(cfg);
end

function tf = is_local_stage_complete(cfg)
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

expectedHistoryRows = cfg.topKSeeds * cfg.evalsPerIteration * cfg.iterationsPerSeed;
expectedSearchRows = cfg.topKSeeds;
tf = height(historyTbl) >= expectedHistoryRows && height(searchTbl) >= expectedSearchRows;
end
