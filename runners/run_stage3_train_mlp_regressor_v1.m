thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'train_mlp_regressor_v1.py');
if ~isfile(scriptPath)
    error('run_stage3_train_mlp_regressor_v1:MissingScript', 'Training script not found: %s', scriptPath);
end
cmd = sprintf('python "%s"', scriptPath);
status = system(cmd);
if status ~= 0
    error('run_stage3_train_mlp_regressor_v1:TrainFailed', 'MLP training exited with code %d', status);
end
