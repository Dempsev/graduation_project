thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'train_mlp_regressor_v5.py');
if ~isfile(scriptPath)
    error('run_stage3_train_mlp_regressor_v5:MissingScript', 'Regressor v5 script not found: %s', scriptPath);
end
cmd = sprintf('python "%s"', scriptPath);
status = system(cmd);
if status ~= 0
    error('run_stage3_train_mlp_regressor_v5:TrainFailed', 'Regressor v5 exited with code %d', status);
end
