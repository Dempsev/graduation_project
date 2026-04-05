function cfg = get_comsol_in_loop_ga_config_v1()
%GET_COMSOL_IN_LOOP_GA_CONFIG_V1 Config for direct COMSOL-in-the-loop GA.

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(fileparts(thisDir));
add_shared_optimization_paths(rootDir);
baseCfg = get_stage2_harmonics_refine_config();

cfg = baseCfg;
cfg.gaId = 'comsol_in_loop_ga_v1';
cfg.rootDir = rootDir;
cfg = apply_real_ga_output_layout_v1(cfg, fullfile(rootDir, 'data', 'comsol_batch', cfg.gaId));
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

signatureParts = get_real_ga_base_signature_parts_v1(cfg);
cfg.configSignature = join_signature_parts_v1(signatureParts);

ensure_dir(cfg.outDir);
ensure_dir(cfg.tbl1Dir);
ensure_dir(cfg.logsDir);
ensure_dir(cfg.plotDir);
if cfg.saveModel
    ensure_dir(cfg.modelsDir);
end
end

function add_shared_optimization_paths(rootDir)
sharedOptDir = fullfile(rootDir, 'shared', 'optimization_matlab');
if exist(sharedOptDir, 'dir')
    addpath(sharedOptDir);
end
end

function ensure_dir(pathStr)
if ~exist(pathStr, 'dir')
    mkdir(pathStr);
end
end
