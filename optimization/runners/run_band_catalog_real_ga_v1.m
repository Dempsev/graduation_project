rootDir = fileparts(fileparts(fileparts(mfilename('fullpath'))));
run(fullfile(rootDir, 'runners', 'run_stage3_comsol_in_loop_band_catalog_ga_v1.m'));
