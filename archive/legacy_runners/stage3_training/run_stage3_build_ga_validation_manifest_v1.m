repo_root = fileparts(fileparts(mfilename('fullpath')));
script_path = fullfile(repo_root, 'stage3_training', 'build_ga_validation_manifest_v1.py');
policy_path = fullfile(repo_root, 'stage3_training', 'policies', 'ga_v1.json');
python_exe = 'python';
if ~isfile(policy_path)
    error('run_stage3_build_ga_validation_manifest_v1:MissingPolicy', 'GA policy JSON not found: %s', policy_path);
end
cmd = sprintf('"%s" "%s" --policy-json "%s"', python_exe, script_path, policy_path);
status = system(cmd);
if status ~= 0
    error('run_stage3_build_ga_validation_manifest_v1 failed with exit code %d', status);
end
