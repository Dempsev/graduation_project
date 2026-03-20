thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'train_mlp_classifier_v3.py');
if ~isfile(scriptPath)
    error('run_stage3_train_mlp_classifier_v3:MissingScript', 'Classifier script not found: %s', scriptPath);
end

tasks = {'contact_valid', 'is_positive_shape'};
for i = 1:numel(tasks)
    cmd = sprintf('python "%s" --task %s', scriptPath, tasks{i});
    status = system(cmd);
    if status ~= 0
        error('run_stage3_train_mlp_classifier_v3:TrainFailed', 'Classifier task %s exited with code %d', tasks{i}, status);
    end
end
