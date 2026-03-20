thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_training', 'build_validation_manifest_v9.py');
if ~isfile(scriptPath)
    error('run_stage3_build_validation_manifest_v9:MissingScript', 'Validation manifest script not found: %s', scriptPath);
end
cmd = sprintf('python "%s"', scriptPath);
status = system(cmd);
if status ~= 0
    error('run_stage3_build_validation_manifest_v9:BuildFailed', 'Validation manifest build exited with code %d', status);
end
