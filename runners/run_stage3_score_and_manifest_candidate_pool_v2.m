thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'run_cascade_surrogate_v2.py');
manifestScript = fullfile(rootDir, 'stage3_training', 'build_validation_manifest_v1.py');
outDir = fullfile(rootDir, 'data', 'ml_runs', 'candidate_pool_cascade_v2', 'validation_manifest_v2');
scoredCsv = fullfile(rootDir, 'data', 'ml_runs', 'candidate_pool_cascade_v2', 'cascade_predictions.csv');
if ~isfile(scriptPath)
    error('run_stage3_score_and_manifest_candidate_pool_v2:MissingCascadeScript', 'Cascade script not found: %s', scriptPath);
end
if ~isfile(manifestScript)
    error('run_stage3_score_and_manifest_candidate_pool_v2:MissingManifestScript', 'Validation manifest builder not found: %s', manifestScript);
end
status = system(sprintf('python "%s"', scriptPath));
if status ~= 0
    error('run_stage3_score_and_manifest_candidate_pool_v2:CascadeFailed', 'Cascade v2 exited with code %d', status);
end
status = system(sprintf('python "%s" --scored-csv "%s" --out-dir "%s"', manifestScript, scoredCsv, outDir));
if status ~= 0
    error('run_stage3_score_and_manifest_candidate_pool_v2:ManifestFailed', 'Validation manifest builder exited with code %d', status);
end
