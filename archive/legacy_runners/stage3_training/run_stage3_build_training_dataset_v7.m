thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_dataset', 'build_v7_training_dataset.py');
if ~isfile(scriptPath)
    error('run_stage3_build_training_dataset_v7:MissingScript', 'Dataset builder not found: %s', scriptPath);
end
cmd = sprintf('python "%s"', scriptPath);
status = system(cmd);
if status ~= 0
    error('run_stage3_build_training_dataset_v7:BuildFailed', 'Dataset builder exited with code %d', status);
end
