thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
scriptPath = fullfile(rootDir, 'stage3_optimization', 'run_optimization_pipeline_v1.py');
if ~isfile(scriptPath)
    error('run_stage3_optimization_pipeline_with_ga_v1:MissingScript', 'Optimization pipeline script not found: %s', scriptPath);
end

cmd = sprintf('python "%s" --with-ga', scriptPath);
status = system(cmd);
if status ~= 0
    error('run_stage3_optimization_pipeline_with_ga_v1:RunFailed', 'Optimization pipeline with GA exited with code %d', status);
end
