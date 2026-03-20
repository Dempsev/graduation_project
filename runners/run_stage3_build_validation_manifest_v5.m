thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'build_validation_manifest_v5.py');
outDir = fullfile(rootDir, 'data', 'ml_runs', 'candidate_pool_cascade_v5', 'validation_manifest_v5');
scoredCsv = fullfile(rootDir, 'data', 'ml_runs', 'candidate_pool_cascade_v5', 'cascade_predictions.csv');
gatedTopK = 0;
probeTopK = 0;
if ~isfile(scriptPath)
    error('run_stage3_build_validation_manifest_v5:MissingScript', 'Validation manifest builder not found: %s', scriptPath);
end
cmd = sprintf('python "%s" --scored-csv "%s" --out-dir "%s" --gated-top-k %d --probe-top-k %d', ...
    scriptPath, scoredCsv, outDir, gatedTopK, probeTopK);
status = system(cmd);
if status ~= 0
    error('run_stage3_build_validation_manifest_v5:BuildFailed', 'Validation manifest builder exited with code %d', status);
end
