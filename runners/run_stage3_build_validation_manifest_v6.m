thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'build_validation_manifest_v6.py');
outDir = fullfile(rootDir, 'data', 'ml_runs', 'candidate_pool_cascade_v6', 'validation_manifest_v6');
scoredCsv = fullfile(rootDir, 'data', 'ml_runs', 'candidate_pool_cascade_v6', 'cascade_predictions.csv');
topK = 0;
if ~isfile(scriptPath)
    error('run_stage3_build_validation_manifest_v6:MissingScript', 'Validation manifest builder not found: %s', scriptPath);
end
cmd = sprintf('python "%s" --scored-csv "%s" --out-dir "%s" --top-k %d', scriptPath, scoredCsv, outDir, topK);
status = system(cmd);
if status ~= 0
    error('run_stage3_build_validation_manifest_v6:BuildFailed', 'Validation manifest builder exited with code %d', status);
end
