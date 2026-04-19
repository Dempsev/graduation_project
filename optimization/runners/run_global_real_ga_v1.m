rootDir = fileparts(fileparts(fileparts(mfilename('fullpath'))));
run(fullfile(rootDir, 'runners', 'run_stage3_comsol_in_loop_global_ga_v1.m'));
