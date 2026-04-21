function cfg = get_comsol_in_loop_ga_band_supplement_exploratory_v2()
%GET_COMSOL_IN_LOOP_GA_BAND_SUPPLEMENT_EXPLORATORY_V2
% Exploratory weak-band supplementation with wider bounds, band-aware shape
% pools, and historical novelty avoidance.

cfg = get_comsol_in_loop_ga_band_supplement_config_v1();
cfg.gaId = 'comsol_in_loop_band_supplement_exploratory_v2';
cfg = apply_real_ga_output_layout_v1(cfg, fullfile(cfg.rootDir, 'data', 'comsol_batch', cfg.gaId));

% Keep the weak-band priority order but explore more aggressively.
cfg.populationSize = 44;
cfg.maxGenerations = 32;
cfg.generations = cfg.maxGenerations;
cfg.eliteCount = 4;
cfg.shapeMutationRate = 0.30;
cfg.continuousMutationRate = 0.32;
cfg.continuousMutationScale = 0.16;

cfg.globalBounds.a1 = [0.42, 0.58];
cfg.globalBounds.a2 = [-0.24, 0.00];
cfg.globalBounds.b1 = [-0.08, 0.08];
cfg.globalBounds.b2 = [-0.04, 0.12];
cfg.globalBounds.a3 = [-0.06, 0.06];
cfg.globalBounds.b3 = [-0.06, 0.06];
cfg.globalBounds.a4 = [-0.05, 0.05];
cfg.globalBounds.b4 = [-0.05, 0.05];
cfg.globalBounds.a5 = [-0.04, 0.04];
cfg.globalBounds.b5 = [-0.04, 0.04];
cfg.globalBounds.r0 = [0.008, 0.016];

cfg.archiveTopCandidatesPerBand = 10;
cfg.topCandidatesExport = 40;
cfg.earlyStopMinDeltaFitness = 0.0005;
cfg.earlyStopPatience = 12;
cfg.earlyStopMinGenerations = 20;

cfg.noveltyEnabled = true;
cfg.noveltyMinDistanceNormalized = 0.10;
cfg.noveltyMaxResampleAttempts = 24;
cfg.noveltyHistoryCsvs = build_novelty_history_csvs(cfg.rootDir);

cfg.bandCatalogSummaryCsv = fullfile(cfg.outDir, 'ga_band_catalog_summary_v1.csv');
cfg.bandCatalogBestCandidatesCsv = fullfile(cfg.outDir, 'ga_band_catalog_best_candidates_v1.csv');
cfg.bandCatalogJson = fullfile(cfg.outDir, 'ga_band_catalog_v1.json');

signatureParts = [ ...
    get_real_ga_base_signature_parts_v1(cfg), ...
    { ...
    'band_catalog_mode=true', ...
    'band_catalog_role=targeted_supplementation_exploratory', ...
    ['band_selection_mode=' char(string(cfg.bandSelectionMode))], ...
    ['band_archive_top_k=' num2str(cfg.archiveTopCandidatesPerBand)], ...
    ['band_catalog=' band_catalog_signature(cfg.bandCatalog)], ...
    ['band_aware_shape_pools=' num2str(cfg.bandAwareShapePoolsEnabled)], ...
    ['band_aware_shape_pool_dir=' char(string(cfg.bandAwareShapePoolsDir))], ...
    ['band_aware_shape_pool_file=' char(string(cfg.bandAwareShapePoolFilename))], ...
    ['novelty_enabled=' num2str(cfg.noveltyEnabled)], ...
    ['novelty_min_distance=' num2str(cfg.noveltyMinDistanceNormalized, '%.12g')], ...
    ['novelty_history_count=' num2str(numel(cfg.noveltyHistoryCsvs))] ...
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

function paths = build_novelty_history_csvs(rootDir)
paths = { ...
    fullfile(rootDir, 'data', 'comsol_batch', 'comsol_in_loop_true_global_ga_v1', 'ga_history_v1.csv'), ...
    fullfile(rootDir, 'data', 'comsol_batch', 'comsol_in_loop_band_catalog_ga_v1', 'ga_history_v1.csv'), ...
    fullfile(rootDir, 'data', 'comsol_batch', 'comsol_in_loop_band_supplement_ga_v1', 'ga_history_v1.csv'), ...
    fullfile(rootDir, 'data', 'comsol_batch', 'stage4_validation_targetband_v1', 'stage4_validation_results.csv'), ...
    fullfile(rootDir, 'data', 'comsol_batch', 'stage4_validation_targetband_top6_v1', 'stage4_validation_results.csv'), ...
    fullfile(rootDir, 'data', 'comsol_batch', 'stage2_gapdiversity_exploration_v1', 'stage2_gapdiversity_results.csv') ...
    };
end

function out = band_catalog_signature(catalog)
parts = strings(numel(catalog), 1);
for i = 1:numel(catalog)
    parts(i) = sprintf('%s:%g-%g', char(string(catalog(i).bandTag)), catalog(i).bandLowHz, catalog(i).bandHighHz);
end
out = strjoin(cellstr(parts), ',');
end

function ensure_dir(pathStr)
if ~exist(pathStr, 'dir')
    mkdir(pathStr);
end
end
