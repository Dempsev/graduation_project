function cfg = get_comsol_in_loop_ga_band_catalog_config_v1()
%GET_COMSOL_IN_LOOP_GA_BAND_CATALOG_CONFIG_V1
% Config for one-run multi-band global GA with per-band archives.

cfg = get_comsol_in_loop_ga_global_config_v1();
cfg.gaId = 'comsol_in_loop_band_catalog_ga_v1';
cfg = apply_real_ga_output_layout_v1(cfg, fullfile(cfg.rootDir, 'data', 'comsol_batch', cfg.gaId));

cfg.bandCatalog = build_default_band_catalog();
cfg.bandSelectionMode = 'rotate_by_generation';
cfg.archiveTopCandidatesPerBand = 5;
cfg.topCandidatesExport = 24;
cfg.maxGenerations = 24;
cfg.generations = cfg.maxGenerations;
cfg.earlyStopMinDeltaFitness = 0.001;
cfg.earlyStopPatience = 8;
cfg.earlyStopMinGenerations = 12;

cfg.bandCatalogSummaryCsv = fullfile(cfg.outDir, 'ga_band_catalog_summary_v1.csv');
cfg.bandCatalogBestCandidatesCsv = fullfile(cfg.outDir, 'ga_band_catalog_best_candidates_v1.csv');
cfg.bandCatalogJson = fullfile(cfg.outDir, 'ga_band_catalog_v1.json');
cfg.bandAwareShapePoolsEnabled = true;
cfg.bandAwareShapePoolsDir = fullfile(cfg.rootDir, 'data', 'analysis', 'targetband_shape_atlas_v1');
cfg.bandAwareShapePoolFilename = 'shape_pool_v1.csv';

signatureParts = [ ...
    get_real_ga_base_signature_parts_v1(cfg), ...
    { ...
    'band_catalog_mode=true', ...
    ['band_selection_mode=' char(string(cfg.bandSelectionMode))], ...
    ['band_archive_top_k=' num2str(cfg.archiveTopCandidatesPerBand)], ...
    ['band_catalog=' band_catalog_signature(cfg.bandCatalog)], ...
    ['band_aware_shape_pools=' num2str(cfg.bandAwareShapePoolsEnabled)], ...
    ['band_aware_shape_pool_dir=' char(string(cfg.bandAwareShapePoolsDir))], ...
    ['band_aware_shape_pool_file=' char(string(cfg.bandAwareShapePoolFilename))] ...
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

function catalog = build_default_band_catalog()
catalog = repmat(struct('bandTag', '', 'bandLowHz', 0, 'bandHighHz', 0), 4, 1);
catalog(1) = make_band('band140_180', 140, 180);
catalog(2) = make_band('band160_200', 160, 200);
catalog(3) = make_band('band180_220', 180, 220);
catalog(4) = make_band('band200_240', 200, 240);
end

function band = make_band(tag, lowHz, highHz)
band = struct('bandTag', string(tag), 'bandLowHz', double(lowHz), 'bandHighHz', double(highHz));
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
