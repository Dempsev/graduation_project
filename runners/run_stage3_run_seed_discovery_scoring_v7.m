thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'run_seed_discovery_scoring_v7.py');
if ~isfile(scriptPath)
    error('run_stage3_run_seed_discovery_scoring_v7:MissingScript', 'Seed discovery scoring script not found: %s', scriptPath);
end
cmd = sprintf('python "%s"', scriptPath);
status = system(cmd);
if status ~= 0
    error('run_stage3_run_seed_discovery_scoring_v7:RunFailed', 'Seed discovery scoring exited with code %d', status);
end
