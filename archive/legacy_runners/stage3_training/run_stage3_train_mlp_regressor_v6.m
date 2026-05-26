thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'train_mlp_regressor_v6.py');
if ~isfile(scriptPath)
    error('run_stage3_train_mlp_regressor_v6:MissingScript', 'Regressor v6 script not found: %s', scriptPath);
end
cmd = sprintf('python "%s"', scriptPath);
status = system(cmd);
if status ~= 0
    error('run_stage3_train_mlp_regressor_v6:TrainFailed', 'Regressor v6 exited with code %d', status);
end
