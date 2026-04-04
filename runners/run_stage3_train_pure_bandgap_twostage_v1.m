rootDir = fileparts(fileparts(mfilename('fullpath')));
scriptPath = fullfile(rootDir, 'stage3_prediction', 'train_pure_bandgap_twostage_v1.py');

cmd = sprintf('"%s" "%s" --target gap34_width_Hz --split-mode stage_holdout --run-name pure_gap34widthhz_twostage_v1_stageholdout', ...
    'python', scriptPath);

status = system(cmd);
if status ~= 0
    error('run_stage3_train_pure_bandgap_twostage_v1:PythonFailed', ...
        'Python command failed with status %d', status);
end
