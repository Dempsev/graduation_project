repo_root = fileparts(fileparts(mfilename('fullpath')));
script_path = fullfile(repo_root, 'stage3_training', 'run_parametric_ga_seed_search_v1.py');
whitelist_path = fullfile(repo_root, 'stage3_training', 'ga_shape_whitelist_v1.json');
python_exe = 'python';
cmd = sprintf('"%s" "%s" --whitelist-json "%s" --top-k-seeds 3 --only-point-id rf09_h00_center --population-size 20 --generations 12 --elite-k 4 --mutation-rate 0.20 --mutation-scale 0.08 --local-span-scale 1.0 --surrogate-delta-cap 3.0', python_exe, script_path, whitelist_path);
status = system(cmd);
if status ~= 0
    error('run_stage3_parametric_ga_seed_search_v1 failed with exit code %d', status);
end
