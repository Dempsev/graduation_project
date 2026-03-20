thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'train_mlp_regressor_v7.py');
if ~isfile(scriptPath)
    error('run_stage3_train_mlp_regressor_v7:MissingScript', 'Regressor v7 script not found: %s', scriptPath);
end
cmd = sprintf('python "%s"', scriptPath);
status = system(cmd);
if status ~= 0
    error('run_stage3_train_mlp_regressor_v7:TrainFailed', 'Regressor v7 exited with code %d', status);
end
