scriptDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(fileparts(scriptDir));
run(fullfile(rootDir, 'runners', 'run_stage3_comsol_in_loop_targetband180_220_overlap_ga_v1.m'));
