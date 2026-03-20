thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'build_validation_manifest_v10.py');
if ~isfile(scriptPath)
    error('run_stage3_build_validation_manifest_v10:MissingScript', 'Validation manifest script not found: %s', scriptPath);
end
cmd = sprintf('python "%s"', scriptPath);
status = system(cmd);
if status ~= 0
    error('run_stage3_build_validation_manifest_v10:BuildFailed', 'Validation manifest build exited with code %d', status);
end
