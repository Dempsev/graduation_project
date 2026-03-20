thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'run_cascade_surrogate_v2.py');
if ~isfile(scriptPath)
    error('run_stage3_run_cascade_surrogate_v2:MissingScript', 'Cascade script not found: %s', scriptPath);
end
cmd = sprintf('python "%s"', scriptPath);
status = system(cmd);
if status ~= 0
    error('run_stage3_run_cascade_surrogate_v2:RunFailed', 'Cascade v2 exited with code %d', status);
end
