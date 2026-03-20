thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'build_candidate_pool_v1.py');
if ~isfile(scriptPath)
    error('run_stage3_build_candidate_pool_v1:MissingScript', 'Candidate pool builder not found: %s', scriptPath);
end
cmd = sprintf('python "%s"', scriptPath);
status = system(cmd);
if status ~= 0
    error('run_stage3_build_candidate_pool_v1:BuildFailed', 'Candidate pool builder exited with code %d', status);
end
