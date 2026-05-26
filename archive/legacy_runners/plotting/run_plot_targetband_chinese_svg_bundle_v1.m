function run_plot_targetband_chinese_svg_bundle_v1()
%RUN_PLOT_TARGETBAND_CHINESE_SVG_BUNDLE_V1 Runner for Chinese SVG target-band figures.

rootDir = fileparts(fileparts(mfilename('fullpath')));
addpath(fullfile(rootDir, 'postprocess'));
plot_targetband_chinese_svg_bundle_v1();
end
