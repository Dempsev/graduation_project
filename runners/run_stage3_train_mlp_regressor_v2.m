thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'train_mlp_regressor_v2.py');
if ~isfile(scriptPath)
    error('run_stage3_train_mlp_regressor_v2:MissingScript', 'Regressor v2 script not found: %s', scriptPath);
end
cmd = sprintf('python "%s"', scriptPath);
status = system(cmd);
if status ~= 0
    error('run_stage3_train_mlp_regressor_v2:TrainFailed', 'Regressor v2 exited with code %d', status);
end
