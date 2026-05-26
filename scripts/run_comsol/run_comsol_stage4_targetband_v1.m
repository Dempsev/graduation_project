scriptDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(fileparts(scriptDir));
run(fullfile(rootDir, 'runners', 'run_stage4_validation_targetband_v1.m'));
