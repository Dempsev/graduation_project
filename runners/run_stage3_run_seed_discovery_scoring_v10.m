thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'run_seed_discovery_scoring_v7.py');
datasetPath = fullfile(rootDir, 'data', 'ml_dataset', 'v10', 'candidate_pool_v10_seed_only_refined', 'candidate_pool_v10.csv');
calibrationPath = fullfile(rootDir, 'stage3_training', 'seed_discovery_scoring_calibration_v1.json');
if ~isfile(scriptPath)
    error('run_stage3_run_seed_discovery_scoring_v10:MissingScript', 'Seed discovery scoring script not found: %s', scriptPath);
end
if ~isfile(datasetPath)
    error('run_stage3_run_seed_discovery_scoring_v10:MissingDataset', 'Candidate pool dataset not found: %s', datasetPath);
end
if ~isfile(calibrationPath)
    error('run_stage3_run_seed_discovery_scoring_v10:MissingCalibration', 'Calibration JSON not found: %s', calibrationPath);
end
cmd = sprintf('python "%s" --dataset "%s" --run-name candidate_pool_seed_discovery_v10 --calibration-json "%s"', scriptPath, datasetPath, calibrationPath);
status = system(cmd);
if status ~= 0
    error('run_stage3_run_seed_discovery_scoring_v10:RunFailed', 'Seed discovery scoring exited with code %d', status);
end
