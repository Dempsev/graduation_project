thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'build_validation_manifest_v11.py');
policyPath = fullfile(rootDir, 'stage3_training', 'policies', 'manifest_v11.json');
if ~isfile(scriptPath)
    error('run_stage3_build_validation_manifest_v11:MissingScript', 'Validation manifest script not found: %s', scriptPath);
end
if ~isfile(policyPath)
    error('run_stage3_build_validation_manifest_v11:MissingPolicy', 'Manifest policy JSON not found: %s', policyPath);
end
cmd = sprintf('python "%s" --policy-json "%s"', scriptPath, policyPath);
status = system(cmd);
if status ~= 0
    error('run_stage3_build_validation_manifest_v11:BuildFailed', 'Validation manifest build exited with code %d', status);
end
