thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'train_mlp_regressor_v3.py');
if ~isfile(scriptPath)
    error('run_stage3_train_mlp_regressor_v3:MissingScript', 'Regressor v3 script not found: %s', scriptPath);
end
cmd = sprintf('python "%s"', scriptPath);
status = system(cmd);
if status ~= 0
    error('run_stage3_train_mlp_regressor_v3:TrainFailed', 'Regressor v3 exited with code %d', status);
end
