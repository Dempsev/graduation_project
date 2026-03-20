thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'build_candidate_pool_v9.py');
if ~isfile(scriptPath)
    error('run_stage3_build_candidate_pool_v9:MissingScript', 'Candidate pool script not found: %s', scriptPath);
end
cmd = sprintf('python "%s"', scriptPath);
status = system(cmd);
if status ~= 0
    error('run_stage3_build_candidate_pool_v9:BuildFailed', 'Candidate pool build exited with code %d', status);
end
