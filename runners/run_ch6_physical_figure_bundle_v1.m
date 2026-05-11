thisFile = mfilename('fullpath');
thisDir = fileparts(thisFile);
rootDir = fileparts(thisDir);

addpath(rootDir);
addpath(fullfile(rootDir, 'postprocess'));
addpath(fullfile(rootDir, 'model_core'));
addpath(fullfile(rootDir, 'stage2_harmonics'));
addpath(fullfile(rootDir, 'stage2_harmonics_refine'));
addpath(fullfile(rootDir, 'stage4_validation'));

jobs = {
    fullfile(rootDir, 'prediction_targetband_param_v1', 'tools', 'analyze_snake_based_archetype_targetband_pilot_v1.py')
    fullfile(rootDir, 'prediction_targetband_param_v1', 'tools', 'analyze_shape_archetype_targetband_pilot_v1.py')
    fullfile(rootDir, 'prediction_targetband_param_v1', 'tools', 'plot_ep17_bilobe_witness_dispersion_v1.py')
    fullfile(rootDir, 'prediction_targetband_param_v1', 'tools', 'plot_canonical_local_robustness_dispersion_v1.py')
    fullfile(rootDir, 'runners', 'run_export_canonical_mode_shapes_v1.m')
    fullfile(rootDir, 'runners', 'run_export_ep17_bilobe_witness_mode_shapes_v1.m')
    fullfile(rootDir, 'runners', 'run_export_shape_archetype_targetband_mode_shapes_v1.m')
    fullfile(rootDir, 'runners', 'run_export_ch6_mechanism_field_maps_v1.m')
    fullfile(rootDir, 'prediction_targetband_param_v1', 'tools', 'sync_ch6_physical_assets_v1.py')
};

for i = 1:numel(jobs)
    job = jobs{i};
    fprintf('[%d/%d] running %s\n', i, numel(jobs), job);
    try
        if endsWith(job, '.py')
            run_python_script(job);
        else
            run(job);
        end
    catch ME
        warning('run_ch6_physical_figure_bundle_v1:Failed', ...
            'Failed to run %s: %s', job, ME.message);
    end
end

fprintf('Chapter 6 physical-figure bundle finished.\n');

function run_python_script(scriptPath)
cmd = sprintf('python "%s"', scriptPath);
[status, output] = system(cmd);
if status ~= 0
    error('run_ch6_physical_figure_bundle_v1:PythonFailed', ...
        'Python script failed (%s): %s', scriptPath, output);
end
fprintf('%s\n', output);
end
