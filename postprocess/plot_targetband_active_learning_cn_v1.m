function plot_targetband_active_learning_cn_v1()
%PLOT_TARGETBAND_ACTIVE_LEARNING_CN_V1 Export Chinese thesis figures for multiband active learning.

rootDir = fileparts(fileparts(mfilename('fullpath')));
analysisDir = fullfile(rootDir, 'data', 'analysis', 'targetband_active_learning_v10');
figDir = fullfile(analysisDir, 'figures');
if ~exist(figDir, 'dir')
    mkdir(figDir);
end

bands = [
    struct('tag', "band140_180", 'label', "140-180 Hz")
    struct('tag', "band160_200", 'label', "160-200 Hz")
    struct('tag', "band180_220", 'label', "180-220 Hz")
    struct('tag', "band200_240", 'label', "200-240 Hz")
    struct('tag', "band220_260", 'label', "220-260 Hz")
    struct('tag', "band240_280", 'label', "240-280 Hz")
];

set(groot, 'defaultAxesFontName', 'Microsoft YaHei');
set(groot, 'defaultTextFontName', 'Microsoft YaHei');
set(groot, 'defaultLegendFontName', 'Microsoft YaHei');
set(groot, 'defaultAxesFontSize', 10);

gaSummary = load_ga_generation_summary(rootDir, bands);
scoreSummary = load_candidate_score_summary(rootDir, bands);
holdoutSummary = readtable(fullfile(analysisDir, 'holdout_prediction_summary_v1.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');
holdoutSummary = holdoutSummary(holdoutSummary.model_run == "v10_multiband_active_ga", :);

plot_ga_convergence(gaSummary, bands, figDir);
plot_ga_final_best(gaSummary, bands, figDir);
plot_holdout_truth_vs_pred(holdoutSummary, bands, figDir);
plot_candidate_predicted_best(scoreSummary, bands, figDir);

fprintf('[DONE] Chinese active-learning figures exported to %s\n', figDir);
end

function gaSummary = load_ga_generation_summary(rootDir, bands)
out = table();
for i = 1:numel(bands)
    tag = bands(i).tag;
    csvPath = fullfile(rootDir, 'data', 'comsol_batch', ...
        "comsol_in_loop_thesis_" + tag + "_overlap_ga_v1", ...
        'ga_generation_summary_v1.csv');
    t = readtable(csvPath, 'TextType', 'string', 'VariableNamingRule', 'preserve');
    t.band_tag = repmat(tag, height(t), 1);
    t.band_label = repmat(bands(i).label, height(t), 1);
    out = [out; t]; %#ok<AGROW>
end
gaSummary = out;
end

function scoreSummary = load_candidate_score_summary(rootDir, bands)
bandTag = strings(numel(bands), 1);
bandLabel = strings(numel(bands), 1);
bestPred = zeros(numel(bands), 1);
for i = 1:numel(bands)
    metricsPath = fullfile(rootDir, 'data', 'ml_runs', ...
        'targetband_seed_scoring_v10_multiband_neighborhood_v1', ...
        bands(i).tag, 'targetband_seed_metrics.json');
    metrics = jsondecode(fileread(metricsPath));
    bandTag(i) = bands(i).tag;
    bandLabel(i) = bands(i).label;
    bestPred(i) = metrics.top_k_best_target_overlap_pred_Hz;
end
scoreSummary = table(bandTag, bandLabel, bestPred, ...
    'VariableNames', {'band_tag', 'band_label', 'topk_best_overlap_pred_Hz'});
end

function plot_ga_convergence(gaSummary, bands, figDir)
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 1080 620]);
hold on;
colors = band_colors();
for i = 1:numel(bands)
    t = gaSummary(gaSummary.band_tag == bands(i).tag, :);
    plot(t.generation, t.best_fitness, '-o', ...
        'Color', colors(i, :), 'MarkerFaceColor', colors(i, :), ...
        'LineWidth', 1.8, 'MarkerSize', 4);
end
grid on;
box off;
xlabel('GA 迭代代数');
ylabel('最优目标频带 overlap / Hz');
title('六个论文目标频带的真实 COMSOL-in-loop GA 收敛曲线');
legend({bands.label}, 'Location', 'northwest');
xlim([1, max(gaSummary.generation)]);
ylim([0, max(gaSummary.best_fitness) * 1.15]);
save_figure(fig, figDir, 'figure_5_7a_multiband_ga_convergence_v10_cn');
end

function plot_ga_final_best(gaSummary, bands, figDir)
values = zeros(numel(bands), 1);
for i = 1:numel(bands)
    t = gaSummary(gaSummary.band_tag == bands(i).tag, :);
    values(i) = t.best_fitness(end);
end
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 960 560]);
bar(values, 'FaceColor', 'flat', 'CData', band_colors());
grid on;
box off;
xticks(1:numel(bands));
xticklabels({bands.label});
xtickangle(25);
ylabel('12代后最优目标频带 overlap / Hz');
title('多频带真实 GA 的最终最优结果');
ylim([0, max(values) * 1.20]);
add_bar_labels(values);
save_figure(fig, figDir, 'figure_5_7b_multiband_ga_final_best_v10_cn');
end

function plot_holdout_truth_vs_pred(holdoutSummary, bands, figDir)
truth = zeros(numel(bands), 1);
pred = zeros(numel(bands), 1);
for i = 1:numel(bands)
    row = holdoutSummary(holdoutSummary.target_band_tag == bands(i).tag, :);
    truth(i) = row.truth_max_overlap_Hz(1);
    pred(i) = row.pred_max_overlap_Hz(1);
end
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 980 560]);
values = [truth, pred];
b = bar(values, 'grouped');
b(1).FaceColor = [0.28 0.48 0.72];
b(2).FaceColor = [0.86 0.52 0.24];
grid on;
box off;
xticks(1:numel(bands));
xticklabels({bands.label});
xtickangle(25);
ylabel('holdout overlap / Hz');
title('近最优 holdout 样本的 COMSOL 真值与模型预测结果');
legend({'COMSOL 真值', '模型预测'}, 'Location', 'northwest');
ylim([0, max(values, [], 'all') * 1.20]);
add_grouped_bar_labels(values);
save_figure(fig, figDir, 'figure_5_7c_holdout_truth_vs_prediction_v10_cn');
end

function plot_candidate_predicted_best(scoreSummary, bands, figDir)
values = zeros(numel(bands), 1);
for i = 1:numel(bands)
    row = scoreSummary(scoreSummary.band_tag == bands(i).tag, :);
    values(i) = row.topk_best_overlap_pred_Hz(1);
end
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 960 560]);
bar(values, 'FaceColor', 'flat', 'CData', band_colors());
grid on;
box off;
xticks(1:numel(bands));
xticklabels({bands.label});
xtickangle(25);
ylabel('扩展候选池中的最优预测 overlap / Hz');
title('多频带候选池扩展后的预测筛选结果');
ylim([0, max(values) * 1.20]);
add_bar_labels(values);
save_figure(fig, figDir, 'figure_5_7d_candidate_pool_predicted_best_v10_cn');
end

function colors = band_colors()
colors = [
    0.34 0.58 0.74
    0.35 0.65 0.47
    0.86 0.57 0.28
    0.68 0.46 0.72
    0.78 0.43 0.40
    0.40 0.40 0.40
];
end

function add_bar_labels(values)
for i = 1:numel(values)
    text(i, values(i) + max(values) * 0.025, sprintf('%.1f', values(i)), ...
        'HorizontalAlignment', 'center', 'FontSize', 9);
end
end

function add_grouped_bar_labels(values)
[nGroups, nBars] = size(values);
groupWidth = min(0.8, nBars / (nBars + 1.5));
for i = 1:nBars
    x = (1:nGroups) - groupWidth / 2 + (2 * i - 1) * groupWidth / (2 * nBars);
    for j = 1:nGroups
        text(x(j), values(j, i) + max(values, [], 'all') * 0.025, ...
            sprintf('%.1f', values(j, i)), ...
            'HorizontalAlignment', 'center', 'FontSize', 9);
    end
end
end

function save_figure(fig, figDir, stem)
svgPath = fullfile(figDir, [stem '.svg']);
pngPath = fullfile(figDir, [stem '.png']);
print(fig, svgPath, '-dsvg');
exportgraphics(fig, pngPath, 'Resolution', 300);
close(fig);
fprintf('[SVG] %s\n', svgPath);
fprintf('[PNG] %s\n', pngPath);
end
