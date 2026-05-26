thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'build_candidate_pool_v11.py');
if ~isfile(scriptPath)
    error('run_stage3_build_score_and_manifest_candidate_pool_v11:MissingScript', 'Candidate pool script not found: %s', scriptPath);
end
cmd = sprintf('python "%s"', scriptPath);
status = system(cmd);
if status ~= 0
    error('run_stage3_build_score_and_manifest_candidate_pool_v11:BuildFailed', 'Candidate pool build exited with code %d', status);
end
run_stage3_run_seed_discovery_scoring_v11;
run_stage3_build_validation_manifest_v11;
