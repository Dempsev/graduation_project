function run_plot_targetband_four_arm_baseline_v10_cn()
%RUN_PLOT_TARGETBAND_FOUR_ARM_BASELINE_V10_CN Runner for v10 Chinese baseline SVGs.

rootDir = fileparts(fileparts(mfilename('fullpath')));
addpath(fullfile(rootDir, 'postprocess'));
plot_targetband_four_arm_baseline_v10_cn();
end
