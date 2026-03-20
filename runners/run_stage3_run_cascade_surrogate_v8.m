thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'run_cascade_surrogate_v8.py');
if ~isfile(scriptPath)
    error('run_stage3_run_cascade_surrogate_v8:MissingScript', 'Cascade scoring script not found: %s', scriptPath);
end
cmd = sprintf('python "%s"', scriptPath);
status = system(cmd);
if status ~= 0
    error('run_stage3_run_cascade_surrogate_v8:ScoreFailed', 'Cascade scoring exited with code %d', status);
end
