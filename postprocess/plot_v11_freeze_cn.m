thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
analysisDir = fullfile(rootDir, 'data', 'analysis', 'targetband_active_learning_v11_12gen_freeze_v1');
figDir = fullfile(analysisDir, 'figures');
if ~exist(figDir, 'dir')
    mkdir(figDir);
end

holdoutPath = fullfile(analysisDir, 'holdout_origin_band_top1_prediction_v11_12gen_freeze_v1.csv');
comparePath = fullfile(analysisDir, 'sixband_predictor_top1_comsol_vs_ga12_summary_v1.csv');

plotHoldout(holdoutPath, figDir);
plotPredictorVsGa(comparePath, figDir);

fprintf('[DONE] wrote figures to %s\n', figDir);

function labels = bandLabels(tags)
tags = string(tags);
labels = replace(extractAfter(tags, "band"), "_", "-") + " Hz";
end

function addBarLabels(bars)
for k = 1:numel(bars)
    xtips = bars(k).XEndPoints;
    ytips = bars(k).YEndPoints;
    labels = compose('%.1f', bars(k).YData);
    text(xtips, ytips + 0.45, labels, ...
        'HorizontalAlignment', 'center', ...
        'VerticalAlignment', 'bottom', ...
        'FontSize', 9);
end
end

function exportBoth(fig, figDir, stem)
exportgraphics(fig, fullfile(figDir, stem + ".png"), 'Resolution', 300);
savefig(fig, fullfile(figDir, stem + ".fig"));
close(fig);
end

function plotHoldout(csvPath, figDir)
T = readtable(csvPath, 'TextType', 'string');
values = [T.truth_overlap_Hz, T.pred_overlap_Hz];
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100, 100, 920, 480]);
bars = bar(values, 'grouped');
bars(1).FaceColor = [0.31, 0.51, 0.74];
bars(2).FaceColor = [0.88, 0.54, 0.24];
for k = 1:numel(bars)
    bars(k).EdgeColor = [0.12, 0.12, 0.12];
    bars(k).LineWidth = 0.7;
end
set(gca, 'XTickLabel', bandLabels(T.origin_band_tag), 'FontName', 'Microsoft YaHei');
xtickangle(25);
ylabel('目标频带 overlap / Hz', 'FontName', 'Microsoft YaHei');
legend({'holdout真实值', '模型预测值'}, 'Location', 'northwest', 'Box', 'on');
grid on;
ylim([0, max(values, [], 'all') + 6]);
addBarLabels(bars);
exportBoth(fig, figDir, "figure_5_7c_holdout_truth_vs_prediction_v11_12gen_freeze_cn_titleless");
end

function plotPredictorVsGa(csvPath, figDir)
T = readtable(csvPath, 'TextType', 'string');
values = [
    T.predictor_top1_pred_overlap_Hz, ...
    T.predictor_top1_comsol_truth_overlap_Hz, ...
    T.ga_12gen_holdout_truth_best_Hz ...
];
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100, 100, 980, 520]);
bars = bar(values, 'grouped');
bars(1).FaceColor = [0.21, 0.61, 0.51];
bars(2).FaceColor = [0.88, 0.54, 0.24];
bars(3).FaceColor = [0.23, 0.36, 0.57];
for k = 1:numel(bars)
    bars(k).EdgeColor = [0.12, 0.12, 0.12];
    bars(k).LineWidth = 0.7;
end
set(gca, 'XTickLabel', bandLabels(T.target_band_tag), 'FontName', 'Microsoft YaHei');
xtickangle(25);
ylabel('目标频带 overlap / Hz', 'FontName', 'Microsoft YaHei');
legend({'预测器最高预测值', '预测候选COMSOL真值', '12代GA真实最优值'}, ...
    'Location', 'northwest', 'Box', 'on');
grid on;
ylim([0, max(values, [], 'all') + 6]);
addBarLabels(bars);
exportBoth(fig, figDir, "figure_5_7e_sixband_predictor_vs_ga_v11_12gen_freeze_cn_titleless");
end
