rootDir = fileparts(fileparts(fileparts(mfilename('fullpath'))));
run(fullfile(rootDir, 'runners', 'run_stage3_a_then_comsol_in_loop_ga_v1.m'));
