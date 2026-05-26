function cfg = get_comsol_in_loop_ga_targetband180_220_overlap_config_v1()
%GET_COMSOL_IN_LOOP_GA_TARGETBAND180_220_OVERLAP_CONFIG_V1
% Teacher-facing real-GA baseline for the 180-220 Hz target-band case.
%
% Fitness is computed only from COMSOL truth:
%   fitness = active_target_overlap_Hz
%
% The budget is intentionally small enough for a thesis comparison run while
% still giving the baseline multiple generations of selection pressure.

cfg = get_comsol_in_loop_ga_band_catalog_config_v1();
cfg.gaId = 'comsol_in_loop_targetband180_220_overlap_ga_v1';
cfg = apply_real_ga_output_layout_v1(cfg, fullfile(cfg.rootDir, 'data', 'comsol_batch', cfg.gaId));

cfg.bandCatalog = make_single_band_catalog();
cfg.bandSelectionMode = 'single_band';
cfg.fitnessMetric = 'target_overlap_Hz';
cfg.shapePoolCsv = fullfile(cfg.rootDir, 'data', 'ml_runs', 'targetband_baseline_abc_v1', 'real_ga_shape_pool_v1.csv');
cfg.bandAwareShapePoolsEnabled = false;

cfg.populationSize = 6;
cfg.maxGenerations = 20;
cfg.generations = cfg.maxGenerations;
cfg.allowStateExtension = true;
cfg.eliteCount = 2;
cfg.topCandidatesExport = 12;
cfg.archiveTopCandidatesPerBand = 12;

cfg.enableEarlyStop = false;
cfg.earlyStopMinDeltaFitness = 0;
cfg.earlyStopPatience = cfg.maxGenerations;
cfg.earlyStopMinGenerations = cfg.maxGenerations;

cfg.bandCatalogSummaryCsv = fullfile(cfg.outDir, 'ga_band_catalog_summary_v1.csv');
cfg.bandCatalogBestCandidatesCsv = fullfile(cfg.outDir, 'ga_band_catalog_best_candidates_v1.csv');
cfg.bandCatalogJson = fullfile(cfg.outDir, 'ga_band_catalog_v1.json');

signatureParts = [ ...
    get_real_ga_base_signature_parts_v1(cfg), ...
    { ...
    'targetband_overlap_baseline=true', ...
    'fitness_metric=target_overlap_Hz', ...
    ['band_catalog=' band_catalog_signature(cfg.bandCatalog)], ...
    ['population=' num2str(cfg.populationSize)], ...
    ['max_generations=' num2str(cfg.maxGenerations)] ...
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

function catalog = make_single_band_catalog()
catalog = struct('bandTag', 'band180_220', 'bandLowHz', 180, 'bandHighHz', 220);
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
