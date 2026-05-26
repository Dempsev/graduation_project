function plot_targetband_chinese_svg_bundle_v1()
%PLOT_TARGETBAND_CHINESE_SVG_BUNDLE_V1 Export Chinese SVG versions of target-band figures.

rootDir = fileparts(fileparts(mfilename('fullpath')));
set_chinese_style();

plot_baseline_cn(rootDir);
plot_active_learning_cn(rootDir);

fprintf('[DONE] Chinese target-band SVG bundle exported.\n');
end

function set_chinese_style()
set(groot, 'defaultAxesFontName', 'Microsoft YaHei');
set(groot, 'defaultTextFontName', 'Microsoft YaHei');
set(groot, 'defaultLegendFontName', 'Microsoft YaHei');
set(groot, 'defaultAxesFontSize', 10);
end

function plot_baseline_cn(rootDir)
analysisDir = fullfile(rootDir, 'data', 'analysis', 'targetband_four_arm_baseline_v1');
figDir = fullfile(analysisDir, 'figures');
if ~exist(figDir, 'dir')
    mkdir(figDir);
end

summaryCsv = fullfile(analysisDir, 'targetband_three_method_plot_values_v1.csv');
if ~exist(summaryCsv, 'file')
    summaryCsv = fullfile(analysisDir, 'targetband_four_arm_summary_v1.csv');
end
realGaCsv = fullfile(analysisDir, 'real_ga_best_so_far_v1.csv');
summary = readtable(summaryCsv, 'TextType', 'string', 'VariableNamingRule', 'preserve');
realGa = readtable(realGaCsv, 'TextType', 'string', 'Delimiter', ',', 'VariableNamingRule', 'preserve');
summary = attach_baseline_labels(summary);

plot_baseline_overlap_cn(summary, figDir);
plot_baseline_rates_cn(summary, figDir);
plot_baseline_budget_curve_cn(summary, realGa, figDir);
plot_baseline_budget_scatter_cn(summary, figDir);
end

function summary = attach_baseline_labels(summary)
methods = string(summary.method_arm);
labels = strings(height(summary), 1);
labels(methods == "random_family_balanced_v1") = "随机均衡";
labels(methods == "predictor_only_topk_v1") = "条件预测方法";
labels(methods == "predictor_local_ga_v1") = "预测+局部GA";
labels(methods == "real_comsol_in_loop_ga_v1") = "真实GA";
labels(strlength(labels) == 0) = methods(strlength(labels) == 0);
summary.display_label_cn = labels;
if ~ismember('comsol_budget', summary.Properties.VariableNames)
    summary.comsol_budget = summary.rows_total;
end
end

function plot_baseline_overlap_cn(summary, figDir)
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 980 560]);
values = [summary.mean_target_overlap_Hz, summary.best_target_overlap_Hz];
b = bar(values, 'grouped');
b(1).FaceColor = [0.30 0.55 0.78];
b(2).FaceColor = [0.90 0.55 0.25];
grid on;
box off;
xticks(1:height(summary));
xticklabels(summary.display_label_cn);
ylabel('目标频带交叠长度 / Hz');
title('不同方法在 180-220 Hz 目标频带上的真实交叠表现');
legend({'平均 overlap', '最佳 overlap'}, 'Location', 'northwest');
ylim([0, max(values, [], 'all') * 1.20]);
add_grouped_bar_labels(values);
save_svg(fig, figDir, 'figure_5_6a_target_overlap_comparison_cn');
end

function plot_baseline_rates_cn(summary, figDir)
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 980 560]);
solveRate = summary.solve_success_count ./ summary.rows_total;
contactRate = summary.contact_valid_count ./ summary.rows_total;
openRate = summary.target_open_rate;
values = [solveRate, contactRate, openRate] * 100;
b = bar(values, 'grouped');
b(1).FaceColor = [0.36 0.64 0.40];
b(2).FaceColor = [0.42 0.60 0.82];
b(3).FaceColor = [0.84 0.47 0.36];
grid on;
box off;
xticks(1:height(summary));
xticklabels(summary.display_label_cn);
ylabel('比例 / %');
title('不同方法的真实验证成功率与目标频带命中率');
legend({'求解成功率', '接触有效率', '目标频带打开率'}, 'Location', 'southoutside', 'Orientation', 'horizontal');
ylim([0, 115]);
add_grouped_bar_labels(values);
save_svg(fig, figDir, 'figure_5_6b_validation_hit_rates_cn');
end

function plot_baseline_budget_curve_cn(summary, realGa, figDir)
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 1020 600]);
hold on;
evalIndex = numeric_column(realGa, ["eval_index"], 1);
bestSoFar = numeric_column(realGa, ["best_so_far_target_overlap_Hz"], width(realGa));
valid = isfinite(evalIndex) & isfinite(bestSoFar);
evalIndex = evalIndex(valid);
bestSoFar = bestSoFar(valid);
plot(evalIndex, bestSoFar, '-o', ...
    'Color', [0.20 0.32 0.55], 'MarkerFaceColor', [0.20 0.32 0.55], ...
    'LineWidth', 1.8, 'MarkerSize', 4);

for i = 1:height(summary)
    method = string(summary.method_arm(i));
    if method == "real_comsol_in_loop_ga_v1"
        continue;
    end
    x = summary.rows_total(i);
    y = summary.best_target_overlap_Hz(i);
    if method == "predictor_only_topk_v1"
        color = [0.20 0.58 0.47];
        offset = [0.45, 0.82];
    else
        color = [0.55 0.55 0.55];
        offset = [0.45, -0.75];
    end
    scatter(x, y, 115, 'filled', 'MarkerFaceColor', color, 'MarkerEdgeColor', 'k');
    text(x + offset(1), y + offset(2), sprintf('%s %.1f Hz', summary.display_label_cn(i), y), ...
        'FontSize', 10, 'VerticalAlignment', 'middle');
end

grid on;
box off;
xlabel('真实 COMSOL 评价次数');
ylabel('截至当前预算的最佳 target overlap / Hz');
title('样本效率对比：条件预测方法与真实 GA 的预算-效果关系');
legend({'真实GA best-so-far', '6次验证方法'}, 'Location', 'southeast');
xlim([0, max(evalIndex) + 2]);
ylim([0, max([bestSoFar; summary.best_target_overlap_Hz]) * 1.15]);
save_svg(fig, figDir, 'figure_5_6c_budget_efficiency_curve_cn');
end

function plot_baseline_budget_scatter_cn(summary, figDir)
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 900 560]);
openRate = summary.target_open_rate;
sizes = 90 + 220 * openRate;
colors = [
    0.55 0.55 0.55
    0.20 0.58 0.47
    0.20 0.32 0.55
];
plotX = summary.rows_total;
plotY = summary.best_target_overlap_Hz;
hold on;
for i = 1:height(summary)
    scatter(plotX(i), plotY(i), sizes(i), 'filled', ...
        'MarkerFaceColor', colors(i, :), 'MarkerEdgeColor', 'k');
    text(plotX(i) + 0.45, plotY(i), sprintf('%s %.1f Hz', summary.display_label_cn(i), plotY(i)), ...
        'FontSize', 10, 'VerticalAlignment', 'middle');
end
grid on;
box off;
xlabel('真实 COMSOL 评价次数');
ylabel('最佳 target overlap / Hz');
title('预算与最优候选质量对比');
xlim([0, max(summary.rows_total) + 7]);
ylim([min(summary.best_target_overlap_Hz) - 1, max(summary.best_target_overlap_Hz) + 2]);
save_svg(fig, figDir, 'figure_5_6d_budget_quality_scatter_cn');
end

function plot_active_learning_cn(rootDir)
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
gaSummary = load_ga_generation_summary(rootDir, bands);
scoreSummary = load_candidate_score_summary(rootDir, bands);
holdoutSummary = readtable(fullfile(analysisDir, 'holdout_prediction_summary_v1.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');
holdoutSummary = holdoutSummary(holdoutSummary.model_run == "v10_multiband_active_ga", :);

plot_ga_convergence_cn(gaSummary, bands, figDir);
plot_ga_final_best_cn(gaSummary, bands, figDir);
plot_holdout_truth_vs_pred_cn(holdoutSummary, bands, figDir);
plot_candidate_predicted_best_cn(scoreSummary, bands, figDir);
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

function plot_ga_convergence_cn(gaSummary, bands, figDir)
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 1080 620]);
hold on;
colors = band_colors();
for i = 1:numel(bands)
    t = gaSummary(gaSummary.band_tag == bands(i).tag, :);
    plot(t.generation, t.best_fitness, '-o', 'Color', colors(i, :), ...
        'MarkerFaceColor', colors(i, :), 'LineWidth', 1.8, 'MarkerSize', 4);
end
grid on;
box off;
xlabel('GA 迭代代数');
ylabel('最佳目标频带 overlap / Hz');
title('六个论文目标频带的真实 COMSOL-in-loop GA 收敛曲线');
legend({bands.label}, 'Location', 'northwest');
xlim([1, max(gaSummary.generation)]);
ylim([0, max(gaSummary.best_fitness) * 1.15]);
save_svg(fig, figDir, 'figure_5_7a_multiband_ga_convergence_v10_cn');
end

function plot_ga_final_best_cn(gaSummary, bands, figDir)
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
ylabel('12代后最佳目标频带 overlap / Hz');
title('多频带真实 GA 的最终最佳结果');
ylim([0, max(values) * 1.20]);
add_bar_labels(values);
save_svg(fig, figDir, 'figure_5_7b_multiband_ga_final_best_v10_cn');
end

function plot_holdout_truth_vs_pred_cn(holdoutSummary, bands, figDir)
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
title('近最优 holdout 样本的 COMSOL 真值与 v10 预测结果');
legend({'COMSOL 真值', 'v10 预测'}, 'Location', 'northwest');
ylim([0, max(values, [], 'all') * 1.20]);
add_grouped_bar_labels(values);
save_svg(fig, figDir, 'figure_5_7c_holdout_truth_vs_prediction_v10_cn');
end

function plot_candidate_predicted_best_cn(scoreSummary, bands, figDir)
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
ylabel('扩展候选池中的最佳预测 overlap / Hz');
title('多频带候选池扩展后的预测筛选结果');
ylim([0, max(values) * 1.20]);
add_bar_labels(values);
save_svg(fig, figDir, 'figure_5_7d_candidate_pool_predicted_best_v10_cn');
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

function values = numeric_column(t, candidateNames, fallbackIndex)
varNames = string(t.Properties.VariableNames);
cleanNames = erase(varNames, char(65279));
idx = [];
for i = 1:numel(candidateNames)
    hit = find(cleanNames == candidateNames(i), 1);
    if ~isempty(hit)
        idx = hit;
        break;
    end
end
if isempty(idx)
    idx = fallbackIndex;
end
raw = t{:, idx};
if isnumeric(raw)
    values = raw;
else
    values = str2double(string(raw));
end
values = values(:);
end

function save_svg(fig, figDir, stem)
svgPath = fullfile(figDir, [stem '.svg']);
print(fig, svgPath, '-dsvg');
close(fig);
fprintf('[SVG] %s\n', svgPath);
end
