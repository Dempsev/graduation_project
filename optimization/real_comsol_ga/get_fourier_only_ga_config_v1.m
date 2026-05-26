function cfg = get_fourier_only_ga_config_v1(bandTag, maxGenerations)
%GET_FOURIER_ONLY_GA_CONFIG_V1
% Fourier-boundary-only COMSOL-in-loop GA config for the snake/Fourier
% geometry-space ablation.

if nargin < 1 || strlength(string(bandTag)) == 0
    bandTag = "band180_220";
end
if nargin < 2 || isempty(maxGenerations)
    maxGenerations = 20;
end

cfg = get_comsol_in_loop_ga_thesis_band_overlap_config_v1(bandTag, maxGenerations);
bandTag = string(bandTag);

cfg.gaId = char("comsol_in_loop_fourier_pure_boundary_" + bandTag + "_ga_v1");
cfg = apply_real_ga_output_layout_v1(cfg, fullfile(cfg.rootDir, 'data', 'comsol_batch', cfg.gaId));

cfg.shapePoolMode = 'fourier_pure_boundary';
cfg.shapePoolCsv = fullfile(cfg.rootDir, 'data', 'ml_runs', 'fourier_only_real_ga_v1', 'fourier_only_real_ga_shape_pool_v1.csv');
cfg.useDiscretePerturbation = false;
cfg.shapeMutationRate = 0.0;
cfg.bandAwareShapePoolsEnabled = false;
cfg.shapePoolRequireGeometryValid = false;
cfg.shapePoolRequireContactValid = false;
cfg.shapePoolRequireSolveSuccess = false;
cfg.shapePoolIncludeTiers = {};

cfg.bandCatalogSummaryCsv = fullfile(cfg.outDir, 'ga_band_catalog_summary_v1.csv');
cfg.bandCatalogBestCandidatesCsv = fullfile(cfg.outDir, 'ga_band_catalog_best_candidates_v1.csv');
cfg.bandCatalogJson = fullfile(cfg.outDir, 'ga_band_catalog_v1.json');

signatureParts = [ ...
    get_real_ga_base_signature_parts_v1(cfg), ...
    { ...
    'fourier_only_ablation=true', ...
    'use_discrete_perturbation=false', ...
    'fitness_metric=target_overlap_Hz', ...
    ['shape_pool_mode=' cfg.shapePoolMode], ...
    ['shape_pool_csv=' file_signature_v1(cfg.shapePoolCsv)], ...
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
