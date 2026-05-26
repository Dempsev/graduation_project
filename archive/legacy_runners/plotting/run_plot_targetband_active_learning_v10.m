function run_plot_targetband_active_learning_v10()
%RUN_PLOT_TARGETBAND_ACTIVE_LEARNING_V10 Runner for multiband active-learning plots.

rootDir = fileparts(fileparts(mfilename('fullpath')));
addpath(fullfile(rootDir, 'postprocess'));
plot_targetband_active_learning_v10();
end
