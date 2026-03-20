thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
buildScript = fullfile(rootDir, 'stage3_training', 'build_candidate_pool_v1.py');
scoreScript = fullfile(rootDir, 'stage3_training', 'run_cascade_surrogate_v1.py');
poolCsv = fullfile(rootDir, 'data', 'ml_dataset', 'v1', 'candidate_pool_v1', 'candidate_pool_v1.csv');
if ~isfile(buildScript)
    error('run_stage3_build_and_score_candidate_pool_v1:MissingBuildScript', 'Candidate pool builder not found: %s', buildScript);
end
if ~isfile(scoreScript)
    error('run_stage3_build_and_score_candidate_pool_v1:MissingScoreScript', 'Cascade scorer not found: %s', scoreScript);
end
status = system(sprintf('python "%s"', buildScript));
if status ~= 0
    error('run_stage3_build_and_score_candidate_pool_v1:BuildFailed', 'Candidate pool builder exited with code %d', status);
end
status = system(sprintf('python "%s" --dataset "%s" --run-name candidate_pool_cascade_v1', scoreScript, poolCsv));
if status ~= 0
    error('run_stage3_build_and_score_candidate_pool_v1:ScoreFailed', 'Cascade scorer exited with code %d', status);
end
