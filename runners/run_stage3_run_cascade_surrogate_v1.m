thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'run_cascade_surrogate_v1.py');
if ~isfile(scriptPath)
    error('run_stage3_run_cascade_surrogate_v1:MissingScript', 'Cascade script not found: %s', scriptPath);
end
cmd = sprintf('python "%s"', scriptPath);
status = system(cmd);
if status ~= 0
    error('run_stage3_run_cascade_surrogate_v1:CascadeFailed', 'Cascade script exited with code %d', status);
end
