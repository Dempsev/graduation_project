function cfg = get_comsol_in_loop_ga_optimization_probe_config_v1()
%GET_COMSOL_IN_LOOP_GA_OPTIMIZATION_PROBE_CONFIG_V1
% High-recall optimization probe over many seeds with a small real budget per basin.

cfg = get_comsol_in_loop_ga_config_v1();
cfg.gaId = 'comsol_in_loop_ga_optimization_probe_v1';
cfg.seedScoredCsv = fullfile(cfg.rootDir, 'data', 'ml_runs', 'candidate_pool_optimization_v1', 'optimization_seed_predictions.csv');
cfg.seedPointId = 'rf09_h00_center';
cfg.topKSeeds = 20;
cfg.seedSortFields = {'optimization_seed_score','historical_best_real_gain_Hz','contact_prob','positive_prob','surrogate_pred_gap34_gain_Hz','stage1_reference_gap_gain_Hz'};
cfg.seedSortDirections = {'descend','descend','descend','descend','descend','descend'};

cfg.activeParamNames = {'a1','b1','a2','b2','r0','a3','b3','a4','b4','a5','b5'};
cfg.populationSize = 8;
cfg.generations = 4;
cfg.eliteCount = 2;
cfg.mutationRate = 0.25;
cfg.mutationScale = 0.12;
cfg.topCandidatesPerSeedExport = 2;

cfg.globalBounds.b1 = [-0.05, 0.05];
cfg.globalBounds.a3 = [-0.04, 0.04];
cfg.globalBounds.b3 = [-0.04, 0.04];
cfg.globalBounds.a4 = [-0.03, 0.03];
cfg.globalBounds.b4 = [-0.03, 0.03];
cfg.globalBounds.a5 = [-0.02, 0.02];
cfg.globalBounds.b5 = [-0.02, 0.02];

cfg.localHalfWidths = struct( ...
    'a1', 0.0100, ...
    'a2', 0.0200, ...
    'b1', 0.0150, ...
    'b2', 0.0150, ...
    'a3', 0.0120, ...
    'b3', 0.0120, ...
    'a4', 0.0100, ...
    'b4', 0.0100, ...
    'a5', 0.0080, ...
    'b5', 0.0080, ...
    'r0', 0.00060 ...
);

cfg = apply_real_ga_output_layout_v1(cfg, fullfile(cfg.rootDir, 'data', 'comsol_batch', cfg.gaId));

signatureParts = [ ...
    get_real_ga_base_signature_parts_v1(cfg), ...
    { ...
    'optimization_mode=probe', ...
    ['seed_scored_csv=' file_signature_v1(cfg.seedScoredCsv)] ...
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
