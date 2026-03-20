thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'build_validation_manifest_v4.py');
outDir = fullfile(rootDir, 'data', 'ml_runs', 'candidate_pool_cascade_v4', 'validation_manifest_v4');
scoredCsv = fullfile(rootDir, 'data', 'ml_runs', 'candidate_pool_cascade_v4', 'cascade_predictions.csv');
if ~isfile(scriptPath)
    error('run_stage3_build_validation_manifest_v4:MissingScript', 'Validation manifest builder not found: %s', scriptPath);
end
cmd = sprintf('python "%s" --scored-csv "%s" --out-dir "%s"', scriptPath, scoredCsv, outDir);
status = system(cmd);
if status ~= 0
    error('run_stage3_build_validation_manifest_v4:BuildFailed', 'Validation manifest builder exited with code %d', status);
end
