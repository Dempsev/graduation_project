repo_root = fileparts(fileparts(mfilename('fullpath')));
script_path = fullfile(repo_root, 'stage3_training', 'build_ga_validation_manifest_v1.py');
ga_csv = fullfile(repo_root, 'data', 'ml_runs', 'candidate_pool_seed_discovery_v10', 'ga_parametric_search_v1', 'ga_candidate_manifest_v1.csv');
out_dir = fullfile(repo_root, 'data', 'ml_runs', 'candidate_pool_seed_discovery_v10', 'ga_parametric_search_v1', 'validation_manifest_v1');
python_exe = 'python';
cmd = sprintf('"%s" "%s" --ga-csv "%s" --out-dir "%s" --total-k 6 --per-seed-k 2', python_exe, script_path, ga_csv, out_dir);
status = system(cmd);
if status ~= 0
    error('run_stage3_build_ga_validation_manifest_v1 failed with exit code %d', status);
end
