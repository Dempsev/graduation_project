repo_root = fileparts(fileparts(mfilename('fullpath')));
script_path = fullfile(repo_root, 'stage3_training', 'run_parametric_ga_seed_search_v1.py');
python_exe = 'python';
cmd = sprintf('"%s" "%s" --top-k-seeds 3 --only-point-id rf09_h00_center --population-size 32 --generations 18 --elite-k 6', python_exe, script_path);
status = system(cmd);
if status ~= 0
    error('run_stage3_parametric_ga_seed_search_v1 failed with exit code %d', status);
end
