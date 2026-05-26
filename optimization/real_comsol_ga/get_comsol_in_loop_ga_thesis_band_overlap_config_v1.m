function cfg = get_comsol_in_loop_ga_thesis_band_overlap_config_v1(bandTag, maxGenerations)
%GET_COMSOL_IN_LOOP_GA_THESIS_BAND_OVERLAP_CONFIG_V1
% Independent COMSOL-in-loop GA config for one thesis target-band window.
%
% Fitness is pure COMSOL truth:
%   fitness = active_target_overlap_Hz

if nargin < 1 || strlength(string(bandTag)) == 0
    bandTag = "band180_220";
end
if nargin < 2 || isempty(maxGenerations)
    maxGenerations = 8;
end

[bandLowHz, bandHighHz] = resolve_thesis_band(bandTag);
bandTag = string(bandTag);

cfg = get_comsol_in_loop_ga_band_catalog_config_v1();
cfg.gaId = char("comsol_in_loop_thesis_" + bandTag + "_overlap_ga_v1");
cfg = apply_real_ga_output_layout_v1(cfg, fullfile(cfg.rootDir, 'data', 'comsol_batch', cfg.gaId));

cfg.bandCatalog = struct('bandTag', bandTag, 'bandLowHz', double(bandLowHz), 'bandHighHz', double(bandHighHz));
cfg.bandSelectionMode = 'single_band';
cfg.fitnessMetric = 'target_overlap_Hz';

% Use the same broad shape pool as the teacher-facing 180-220 real-GA run.
cfg.shapePoolCsv = fullfile(cfg.rootDir, 'data', 'ml_runs', 'targetband_baseline_abc_v1', 'real_ga_shape_pool_v1.csv');
cfg.bandAwareShapePoolsEnabled = false;

cfg.populationSize = 6;
cfg.maxGenerations = double(maxGenerations);
cfg.generations = cfg.maxGenerations;
cfg.allowStateExtension = true;
cfg.eliteCount = 2;
cfg.topCandidatesExport = 18;
cfg.archiveTopCandidatesPerBand = 18;

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
    'thesis_band_active_learning=true', ...
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

function [lowHz, highHz] = resolve_thesis_band(bandTag)
tag = string(bandTag);
switch tag
    case "band140_180"
        lowHz = 140; highHz = 180;
    case "band160_200"
        lowHz = 160; highHz = 200;
    case "band180_220"
        lowHz = 180; highHz = 220;
    case "band200_240"
        lowHz = 200; highHz = 240;
    case "band220_260"
        lowHz = 220; highHz = 260;
    case "band240_280"
        lowHz = 240; highHz = 280;
    otherwise
        error('get_comsol_in_loop_ga_thesis_band_overlap_config_v1:UnknownBand', ...
            'Unsupported thesis band tag: %s', char(tag));
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
