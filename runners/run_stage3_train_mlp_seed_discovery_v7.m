thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'train_mlp_classifier_v7.py');
if ~isfile(scriptPath)
    error('run_stage3_train_mlp_seed_discovery_v7:MissingScript', 'Classifier v7 script not found: %s', scriptPath);
end

tasks = {'contact_valid', 'is_positive_shape'};
for i = 1:numel(tasks)
    cmd = sprintf('python "%s" --task %s --feature-preset parametric_seed_discovery', scriptPath, tasks{i});
    status = system(cmd);
    if status ~= 0
        error('run_stage3_train_mlp_seed_discovery_v7:TrainFailed', 'Seed discovery classifier task %s exited with code %d', tasks{i}, status);
    end
end
