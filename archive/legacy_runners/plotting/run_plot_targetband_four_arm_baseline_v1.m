thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
addpath(fullfile(rootDir, 'postprocess'));

plot_targetband_four_arm_baseline_v1();
