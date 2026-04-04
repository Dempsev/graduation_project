thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_prediction', 'train_pure_bandgap_regressor_v1.py');
if ~isfile(scriptPath)
    error('run_stage3_train_pure_bandgap_regressor_v1:MissingScript', 'Pure prediction regressor script not found: %s', scriptPath);
end

cmd = sprintf('python "%s"', scriptPath);
status = system(cmd);
if status ~= 0
    error('run_stage3_train_pure_bandgap_regressor_v1:TrainFailed', 'Pure prediction regressor exited with code %d', status);
end
