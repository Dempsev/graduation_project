thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_prediction', 'build_pure_prediction_dataset_v1.py');
if ~isfile(scriptPath)
    error('run_stage3_build_pure_prediction_dataset_v1:MissingScript', 'Pure prediction dataset script not found: %s', scriptPath);
end

cmd = sprintf('python "%s"', scriptPath);
status = system(cmd);
if status ~= 0
    error('run_stage3_build_pure_prediction_dataset_v1:BuildFailed', 'Pure prediction dataset builder exited with code %d', status);
end
