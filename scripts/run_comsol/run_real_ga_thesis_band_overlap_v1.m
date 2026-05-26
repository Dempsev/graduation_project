scriptDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(fileparts(scriptDir));
run(fullfile(rootDir, 'runners', 'run_stage3_comsol_in_loop_thesis_band_overlap_ga_v1.m'));
