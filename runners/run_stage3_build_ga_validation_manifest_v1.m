repo_root = fileparts(fileparts(mfilename('fullpath')));
script_path = fullfile(repo_root, 'stage3_training', 'build_ga_validation_manifest_v1.py');
python_exe = 'python';
cmd = sprintf('"%s" "%s" --total-k 6 --per-seed-k 2', python_exe, script_path);
status = system(cmd);
if status ~= 0
    error('run_stage3_build_ga_validation_manifest_v1 failed with exit code %d', status);
end
