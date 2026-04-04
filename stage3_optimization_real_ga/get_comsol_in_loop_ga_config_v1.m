function cfg = get_comsol_in_loop_ga_config_v1()
%GET_COMSOL_IN_LOOP_GA_CONFIG_V1 Config for direct COMSOL-in-the-loop GA.

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
baseCfg = get_stage2_harmonics_refine_config();

cfg = baseCfg;
cfg.gaId = 'comsol_in_loop_ga_v1';
cfg.rootDir = rootDir;
cfg.outDir = fullfile(rootDir, 'data', 'comsol_batch', cfg.gaId);
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
cfg.saveModel = false;
cfg.enableBandPlots = false;

cfg.seedScoredCsv = fullfile(rootDir, 'data', 'ml_runs', 'candidate_pool_seed_discovery_v10', 'seed_discovery_predictions.csv');
cfg.seedPointId = 'rf09_h00_center';
cfg.seedWhitelistJson = '';
cfg.forceSeedShapeIds = {};
cfg.topKSeeds = 3;

cfg.paramNames = {'a1','a2','b1','b2','a3','b3','a4','b4','a5','b5','r0'};
cfg.activeParamNames = {'a1','a2','b2','a4','b5','r0'};
cfg.populationSize = 12;
cfg.generations = 6;
cfg.eliteCount = 2;
cfg.mutationRate = 0.20;
cfg.mutationScale = 0.08;
cfg.distancePenaltyWeight = 0.0;
cfg.randomSeed = 20260404;
cfg.topCandidatesPerSeedExport = 3;

cfg.failurePenaltyGeometry = -1e6;
cfg.failurePenaltyContact = -1e5;
cfg.failurePenaltySolve = -1e4;

cfg.globalBounds = struct( ...
    'a1', [0.46, 0.54], ...
    'a2', [-0.18, -0.06], ...
    'b1', [0.0, 0.0], ...
    'b2', [0.0, 0.08], ...
    'a3', [0.0, 0.0], ...
    'b3', [0.0, 0.0], ...
    'a4', [0.0, 0.03], ...
    'b4', [0.0, 0.0], ...
    'a5', [0.0, 0.0], ...
    'b5', [0.0, 0.03], ...
    'r0', [0.010, 0.014] ...
);

cfg.localHalfWidths = struct( ...
    'a1', 0.0030, ...
    'a2', 0.0040, ...
    'b1', 0.0, ...
    'b2', 0.0035, ...
    'a3', 0.0, ...
    'b3', 0.0, ...
    'a4', 0.0020, ...
    'b4', 0.0, ...
    'a5', 0.0, ...
    'b5', 0.0020, ...
    'r0', 0.00025 ...
);

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
    ['material_case=' cfg.materialCase] ...
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
if ~isfile(pathStr)
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
