function plot_targetband_four_arm_baseline_v1()
%PLOT_TARGETBAND_FOUR_ARM_BASELINE_V1 Plot thesis-facing target-band baseline figures.

rootDir = fileparts(fileparts(mfilename('fullpath')));
analysisDir = fullfile(rootDir, 'data', 'analysis', 'targetband_four_arm_baseline_v1');
summaryCsv = fullfile(analysisDir, 'targetband_four_arm_summary_v1.csv');
realGaCsv = fullfile(analysisDir, 'real_ga_best_so_far_v1.csv');
figDir = fullfile(analysisDir, 'figures');
if ~exist(figDir, 'dir')
    mkdir(figDir);
end

summary = readtable(summaryCsv, 'TextType', 'string', 'Delimiter', ',', 'VariableNamingRule', 'preserve');
realGa = readtable(realGaCsv, 'TextType', 'string', 'Delimiter', ',', 'VariableNamingRule', 'preserve');
summary = attach_display_labels(summary);
summary = keep_presentation_methods(summary);

set(groot, 'defaultAxesFontName', 'Microsoft YaHei');
set(groot, 'defaultTextFontName', 'Microsoft YaHei');
set(groot, 'defaultAxesFontSize', 10);

plot_overlap_bars(summary, figDir);
plot_validation_rates(summary, figDir);
plot_budget_curve(summary, realGa, figDir);
plot_budget_scatter(summary, figDir);

plotValuesCsv = fullfile(analysisDir, 'targetband_three_method_plot_values_v1.csv');
writetable(summary, plotValuesCsv);
fprintf('[DONE] Target-band baseline figures exported to %s\n', figDir);
end

function summary = keep_presentation_methods(summary)
orderedMethods = [
    "random_family_balanced_v1"
    "predictor_only_topk_v1"
    "real_comsol_in_loop_ga_v1"
];
methods = string(summary.method_arm);
kept = false(height(summary), 1);
order = zeros(height(summary), 1);
for i = 1:numel(orderedMethods)
    mask = methods == orderedMethods(i);
    kept = kept | mask;
    order(mask) = i;
end
summary = summary(kept, :);
[~, idx] = sort(order(kept));
summary = summary(idx, :);
end

function summary = attach_display_labels(summary)
methods = string(summary.method_arm);
labels = strings(height(summary), 1);
labels(methods == "random_family_balanced_v1") = "随机均衡";
labels(methods == "predictor_only_topk_v1") = "条件预测方法";
labels(methods == "predictor_local_ga_v1") = "预测+局部GA";
labels(methods == "real_comsol_in_loop_ga_v1") = "真实GA";
emptyMask = strlength(labels) == 0;
labels(emptyMask) = methods(emptyMask);
summary.display_label = labels;
summary.comsol_budget = summary.rows_total;
end

function plot_overlap_bars(summary, figDir)
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 980 560]);
values = [summary.mean_target_overlap_Hz, summary.best_target_overlap_Hz];
b = bar(values, 'grouped');
b(1).FaceColor = [0.30 0.55 0.78];
b(2).FaceColor = [0.90 0.55 0.25];
grid on;
box off;
xticks(1:height(summary));
xticklabels(summary.display_label);
ylabel('目标频带交叠长度 / Hz');
title('不同方法在 180-220 Hz 目标频带上的真实交叠表现');
legend({'平均 overlap', '最佳 overlap'}, 'Location', 'northwest');
ylim([0, max(values, [], 'all') * 1.20]);
add_grouped_bar_labels(values);
save_figure(fig, figDir, 'figure_5_6a_target_overlap_comparison');
end

function plot_validation_rates(summary, figDir)
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
xticklabels(summary.display_label);
ylabel('比例 / %');
title('不同方法的真实验证成功率与目标频带命中率');
legend({'求解成功率', '接触有效率', '目标频带打开率'}, 'Location', 'southoutside', 'Orientation', 'horizontal');
ylim([0, 115]);
add_grouped_bar_labels(values);
save_figure(fig, figDir, 'figure_5_6b_validation_hit_rates');
end

function plot_budget_curve(summary, realGa, figDir)
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 1020 600]);
hold on;
plot(realGa.eval_index, realGa.best_so_far_target_overlap_Hz, '-o', ...
    'Color', [0.20 0.32 0.55], 'MarkerFaceColor', [0.20 0.32 0.55], ...
    'LineWidth', 1.8, 'MarkerSize', 4);

markerColors = containers.Map( ...
    {'random_family_balanced_v1','predictor_only_topk_v1'}, ...
    {[0.55 0.55 0.55], [0.20 0.58 0.47]} ...
);
labelOffsets = containers.Map( ...
    {'random_family_balanced_v1','predictor_only_topk_v1'}, ...
    {[0.45, -0.75], [0.45, 0.82]} ...
);
for i = 1:height(summary)
    method = char(summary.method_arm(i));
    if strcmp(method, 'real_comsol_in_loop_ga_v1')
        continue;
    end
    x = summary.rows_total(i);
    y = summary.best_target_overlap_Hz(i);
    color = markerColors(method);
    scatter(x, y, 115, 'filled', 'MarkerFaceColor', color, 'MarkerEdgeColor', 'k');
    offset = labelOffsets(method);
    text(x + offset(1), y + offset(2), sprintf('%s %.1f Hz', summary.display_label(i), y), ...
        'FontSize', 10, 'VerticalAlignment', 'middle');
end

grid on;
box off;
xlabel('真实 COMSOL 评价次数');
ylabel('截至当前预算的最佳 target overlap / Hz');
title('样本效率对比：条件预测方法与真实 GA 的预算-效果关系');
legend({'真实GA best-so-far', '6次验证方法'}, 'Location', 'southeast');
xlim([0, max(realGa.eval_index) + 2]);
ylim([0, max([realGa.best_so_far_target_overlap_Hz; summary.best_target_overlap_Hz]) * 1.15]);
save_figure(fig, figDir, 'figure_5_6c_budget_efficiency_curve');
end

function plot_budget_scatter(summary, figDir)
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
labelDx = repmat(0.45, height(summary), 1);
labelDy = zeros(height(summary), 1);
for i = 1:height(summary)
    method = string(summary.method_arm(i));
    if method == "predictor_only_topk_v1"
        plotX(i) = plotX(i) + 0.22;
        labelDy(i) = 0.20;
    elseif method == "random_family_balanced_v1"
        labelDy(i) = -0.04;
    end
end
hold on;
for i = 1:height(summary)
    scatter(plotX(i), plotY(i), sizes(i), ...
        'filled', 'MarkerFaceColor', colors(i, :), 'MarkerEdgeColor', 'k');
    text(plotX(i) + labelDx(i), plotY(i) + labelDy(i), ...
        sprintf('%s  %.1f Hz', summary.display_label(i), plotY(i)), ...
        'FontSize', 10, 'VerticalAlignment', 'middle');
end
grid on;
box off;
xlabel('真实 COMSOL 评价次数');
ylabel('最佳 target overlap / Hz');
title('预算与最优候选质量对比（圆点大小表示目标频带打开率）');
xlim([0, max(summary.rows_total) + 7]);
ylim([min(summary.best_target_overlap_Hz) - 1, max(summary.best_target_overlap_Hz) + 2]);
save_figure(fig, figDir, 'figure_5_6d_budget_quality_scatter');
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
pngPath = fullfile(figDir, [stem '.png']);
figPath = fullfile(figDir, [stem '.fig']);
svgPath = fullfile(figDir, [stem '.svg']);
exportgraphics(fig, pngPath, 'Resolution', 300);
print(fig, svgPath, '-dsvg');
savefig(fig, figPath);
close(fig);
fprintf('[FIG] %s\n', pngPath);
fprintf('[SVG] %s\n', svgPath);
end
