function cfg = apply_real_ga_output_layout_v1(cfg, outDir)
%APPLY_REAL_GA_OUTPUT_LAYOUT_V1 Populate standard output artifact paths for real GA.

cfg.outDir = outDir;
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
end
