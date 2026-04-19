function cfg = get_comsol_in_loop_ga_optimization_funnel_probe_config_v1()
%GET_COMSOL_IN_LOOP_GA_OPTIMIZATION_FUNNEL_PROBE_CONFIG_V1
% Champion-funnel stage 1: wide-recall seed probe with a deliberately small
% per-basin budget so later stages can spend more truth budget on winners.

cfg = get_comsol_in_loop_ga_config_v1();
cfg.gaId = 'comsol_in_loop_ga_optimization_funnel_probe_v1';
cfg.seedScoredCsv = fullfile(cfg.rootDir, 'data', 'ml_runs', 'candidate_pool_optimization_v1', 'optimization_seed_predictions.csv');
cfg.seedPointId = 'rf09_h00_center';
cfg.topKSeeds = 20;
cfg.seedSortFields = {'optimization_seed_score','historical_best_real_gain_Hz','contact_prob','positive_prob','surrogate_pred_gap34_gain_Hz','stage1_reference_gap_gain_Hz'};
cfg.seedSortDirections = {'descend','descend','descend','descend','descend','descend'};

cfg.activeParamNames = {'a1','b1','a2','b2','r0','a3','b3','a4','b4','a5','b5'};
cfg.populationSize = 6;
cfg.generations = 3;
cfg.eliteCount = 2;
cfg.mutationRate = 0.26;
cfg.mutationScale = 0.14;
cfg.topCandidatesPerSeedExport = 2;

cfg.globalBounds.b1 = [-0.05, 0.05];
cfg.globalBounds.a3 = [-0.04, 0.04];
cfg.globalBounds.b3 = [-0.04, 0.04];
cfg.globalBounds.a4 = [-0.03, 0.03];
cfg.globalBounds.b4 = [-0.03, 0.03];
cfg.globalBounds.a5 = [-0.02, 0.02];
cfg.globalBounds.b5 = [-0.02, 0.02];

cfg.localHalfWidths = struct( ...
    'a1', 0.0120, ...
    'a2', 0.0220, ...
    'b1', 0.0180, ...
    'b2', 0.0180, ...
    'a3', 0.0140, ...
    'b3', 0.0140, ...
    'a4', 0.0120, ...
    'b4', 0.0120, ...
    'a5', 0.0100, ...
    'b5', 0.0100, ...
    'r0', 0.00070 ...
);

cfg = apply_real_ga_output_layout_v1(cfg, fullfile(cfg.rootDir, 'data', 'comsol_batch', cfg.gaId));

signatureParts = [ ...
    get_real_ga_base_signature_parts_v1(cfg), ...
    { ...
    'optimization_mode=funnel_probe', ...
    ['seed_scored_csv=' file_signature_v1(cfg.seedScoredCsv)], ...
    'funnel_budget=20x6x3' ...
    } ...
];
cfg.configSignature = join_signature_parts_v1(signatureParts);

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
