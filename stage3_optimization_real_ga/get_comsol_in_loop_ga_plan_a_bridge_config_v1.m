function cfg = get_comsol_in_loop_ga_plan_a_bridge_config_v1()
%GET_COMSOL_IN_LOOP_GA_PLAN_A_BRIDGE_CONFIG_V1
% Build the real-GA config by using plan-A real validation as the seed gate.

cfg = get_comsol_in_loop_ga_config_v1();

cfg.gaId = 'comsol_in_loop_ga_plan_a_bridge_v1';
cfg.planAWorktreeDir = fullfile(cfg.rootDir, '.worktrees', 'optimization-plan-a');
cfg.planAValidationShapeSummaryCsv = fullfile( ...
    cfg.planAWorktreeDir, ...
    'data', 'comsol_batch', 'stage4_validation_ab_ga_plan_a_expanded_v1', ...
    'stage4_validation_shape_summary.csv');
cfg.planATopKSeeds = 3;
cfg.planAMinMeanGainHz = 1.0;
cfg.planAMinPositiveRate = 1.0;
cfg.planAMinSolveSuccessCount = 2;

cfg.forceSeedShapeIds = cellstr(select_plan_a_validated_seed_ids_v1( ...
    cfg.planAValidationShapeSummaryCsv, ...
    cfg.planATopKSeeds, ...
    cfg.planAMinMeanGainHz, ...
    cfg.planAMinPositiveRate, ...
    cfg.planAMinSolveSuccessCount));
cfg.topKSeeds = numel(cfg.forceSeedShapeIds);

cfg.outDir = fullfile(cfg.rootDir, 'data', 'comsol_batch', cfg.gaId);
cfg.tbl1Dir = fullfile(cfg.outDir, 'tbl1_exports');
cfg.modelsDir = fullfile(cfg.outDir, 'models');
cfg.logsDir = fullfile(cfg.outDir, 'logs');
cfg.plotDir = fullfile(cfg.outDir, 'plots');
cfg.bandPlotDir = fullfile(cfg.plotDir, 'band_diagrams');
cfg.baselineByPointMat = fullfile(cfg.outDir, 'baseline_by_point.mat');
cfg.baselineByPointCsv = fullfile(cfg.outDir, 'baseline_by_point.csv');
cfg.resultsMat = fullfile(cfg.outDir, 'comsol_in_loop_ga_results.mat');
cfg.resultsCsv = fullfile(cfg.outDir, 'comsol_in_loop_ga_results.csv');
cfg.shapeSummaryCsv = fullfile(cfg.outDir, 'comsol_in_loop_ga_shape_summary.csv');
cfg.pointSummaryCsv = fullfile(cfg.outDir, 'comsol_in_loop_ga_point_summary.csv');
cfg.stateMat = fullfile(cfg.outDir, 'ga_state_v1.mat');
cfg.historyCsv = fullfile(cfg.outDir, 'ga_history_v1.csv');
cfg.generationSummaryCsv = fullfile(cfg.outDir, 'ga_generation_summary_v1.csv');
cfg.searchSummaryCsv = fullfile(cfg.outDir, 'ga_search_summary_v1.csv');
cfg.bestCandidatesCsv = fullfile(cfg.outDir, 'ga_best_candidates_v1.csv');
cfg.configJson = fullfile(cfg.outDir, 'ga_config_v1.json');
cfg.seedPointManifestCsv = fullfile(cfg.outDir, 'ga_seed_point_manifest_v1.csv');
cfg.seedSelectionCsv = fullfile(cfg.outDir, 'ga_seed_selection_v1.csv');
cfg.fourierId = cfg.gaId;

signatureParts = { ...
    cfg.gaId, ...
    ['seed_scored_csv=' file_signature(cfg.seedScoredCsv)], ...
    ['seed_point=' cfg.seedPointId], ...
    ['seed_whitelist=' file_signature(cfg.seedWhitelistJson)], ...
    ['force_seed_shapes=' strjoin(string(cfg.forceSeedShapeIds), ',')], ...
    ['top_k=' num2str(cfg.topKSeeds)], ...
    ['population=' num2str(cfg.populationSize)], ...
    ['generations=' num2str(cfg.generations)], ...
    ['elite=' num2str(cfg.eliteCount)], ...
    ['mutation_rate=' num2str(cfg.mutationRate, '%.12g')], ...
    ['mutation_scale=' num2str(cfg.mutationScale, '%.12g')], ...
    ['distance_penalty=' num2str(cfg.distancePenaltyWeight, '%.12g')], ...
    ['random_seed=' num2str(cfg.randomSeed)], ...
    ['active_params=' strjoin(cfg.activeParamNames, ',')], ...
    ['fixed_gap_band=' num2str(cfg.fixedGapBand)], ...
    ['material_case=' cfg.materialCase], ...
    ['plan_a_shape_summary=' file_signature(cfg.planAValidationShapeSummaryCsv)], ...
    ['plan_a_min_mean=' num2str(cfg.planAMinMeanGainHz, '%.12g')], ...
    ['plan_a_min_rate=' num2str(cfg.planAMinPositiveRate, '%.12g')], ...
    ['plan_a_min_solve=' num2str(cfg.planAMinSolveSuccessCount)], ...
    ['plan_a_top_k=' num2str(cfg.planATopKSeeds)] ...
};
cfg.configSignature = join_signature_parts(signatureParts);

ensure_dir(cfg.outDir);
ensure_dir(cfg.tbl1Dir);
ensure_dir(cfg.logsDir);
ensure_dir(cfg.plotDir);
if cfg.saveModel
    ensure_dir(cfg.modelsDir);
end
end

function ensure_dir(pathStr)
if ~exist(pathStr, 'dir')
    mkdir(pathStr);
end
end

function sig = file_signature(pathStr)
if isempty(pathStr) || ~isfile(pathStr)
    sig = 'missing';
    return;
end
info = dir(pathStr);
sig = sprintf('%s|%d|%s', pathStr, info.bytes, info.date);
end

function out = join_signature_parts(parts)
textParts = cell(size(parts));
for i = 1:numel(parts)
    textParts{i} = normalize_signature_item(parts{i});
end
out = '';
for i = 1:numel(textParts)
    if i == 1
        out = textParts{i};
    else
        out = [out ';' textParts{i}]; %#ok<AGROW>
    end
end
end

function text = normalize_signature_item(item)
if isstring(item)
    if numel(item) == 0
        text = '';
    else
        text = strjoin(cellstr(item(:)), ',');
    end
elseif iscell(item)
    if isempty(item)
        text = '';
    else
        text = strjoin(cellfun(@normalize_signature_item, item, 'UniformOutput', false), ',');
    end
elseif isnumeric(item) || islogical(item)
    if isempty(item)
        text = '';
    elseif isscalar(item)
        text = char(string(item));
    else
        text = strjoin(cellstr(string(item(:))), ',');
    end
else
    text = char(string(item));
end
end
