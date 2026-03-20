thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'run_cascade_surrogate_v6.py');
contactThreshold = 0.50;
positiveThreshold = 0.95;
if ~isfile(scriptPath)
    error('run_stage3_run_cascade_surrogate_v6:MissingScript', 'Cascade script not found: %s', scriptPath);
end
cmd = sprintf('python "%s" --contact-threshold %.6f --positive-threshold %.6f', scriptPath, contactThreshold, positiveThreshold);
status = system(cmd);
if status ~= 0
    error('run_stage3_run_cascade_surrogate_v6:RunFailed', 'Cascade v6 exited with code %d', status);
end
