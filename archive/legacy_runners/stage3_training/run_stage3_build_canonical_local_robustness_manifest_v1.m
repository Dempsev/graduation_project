repo_root = fileparts(fileparts(mfilename('fullpath')));
script_path = fullfile(repo_root, 'prediction_targetband_param_v1', 'tools', 'build_canonical_local_robustness_manifest_v1.py');
python_exe = 'python';
if ~isfile(script_path)
    error('run_stage3_build_canonical_local_robustness_manifest_v1:MissingScript', 'Canonical local robustness manifest script not found: %s', script_path);
end
cmd = sprintf('"%s" "%s"', python_exe, script_path);
status = system(cmd);
if status ~= 0
    error('run_stage3_build_canonical_local_robustness_manifest_v1 failed with exit code %d', status);
end
