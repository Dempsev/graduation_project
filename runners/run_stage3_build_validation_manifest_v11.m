thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'build_validation_manifest_v11.py');
scoredCsv = fullfile(rootDir, 'data', 'ml_runs', 'candidate_pool_seed_discovery_v11', 'seed_discovery_predictions.csv');
outDir = fullfile(rootDir, 'data', 'ml_runs', 'candidate_pool_seed_discovery_v11', 'validation_manifest_v11');
if ~isfile(scriptPath)
    error('run_stage3_build_validation_manifest_v11:MissingScript', 'Validation manifest script not found: %s', scriptPath);
end
cmd = sprintf('python "%s" --scored-csv "%s" --out-dir "%s" --primary-k 2 --probe-k 3 --max-per-family 1', scriptPath, scoredCsv, outDir);
status = system(cmd);
if status ~= 0
    error('run_stage3_build_validation_manifest_v11:BuildFailed', 'Validation manifest build exited with code %d', status);
end
