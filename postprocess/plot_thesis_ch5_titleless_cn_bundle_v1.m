function plot_thesis_ch5_titleless_cn_bundle_v1()
%PLOT_THESIS_CH5_TITLELESS_CN_BUNDLE_V1 Export titleless Chinese thesis figures for Chapter 5.

rootDir = fileparts(fileparts(mfilename('fullpath')));
outDir = fullfile(rootDir, 'data', 'analysis', 'thesis_ch5_titleless_cn_bundle_v1', 'figures');
if ~exist(outDir, 'dir')
    mkdir(outDir);
end

set(groot, 'defaultAxesFontName', 'Microsoft YaHei');
set(groot, 'defaultTextFontName', 'Microsoft YaHei');
set(groot, 'defaultLegendFontName', 'Microsoft YaHei');
set(groot, 'defaultAxesFontSize', 10);

export_method_comparison(rootDir, outDir);
export_active_learning(rootDir, outDir);

fprintf('[DONE] Titleless Chinese Chapter 5 figures exported to %s\n', outDir);
end

function export_method_comparison(rootDir, outDir)
analysisDir = fullfile(rootDir, 'data', 'analysis', 'targetband_four_arm_baseline_v10_fullpool_v1');
summary = readtable(fullfile(analysisDir, 'targetband_four_arm_summary_v1.csv'), ...
    'TextType', 'string', 'Delimiter', ',', 'VariableNamingRule', 'preserve');
realGa = readtable(fullfile(analysisDir, 'real_ga_best_so_far_v1.csv'), ...
    'TextType', 'string', 'Delimiter', ',', 'VariableNamingRule', 'preserve');

summary = attach_method_labels(summary);
summary = keep_method_rows(summary);

plot_56a_overlap(summary, outDir);
plot_56b_rates(summary, outDir);
plot_56c_budget_curve(summary, realGa, outDir);
plot_56d_budget_scatter(summary, outDir);
end

function summary = attach_method_labels(summary)
methods = string(summary.method_arm);
labels = strings(height(summary), 1);
labels(methods == "random_family_balanced_v1") = "随机均衡";
labels(methods == "predictor_only_topk_v10_v1") = "条件预测方法";
labels(methods == "real_comsol_in_loop_ga_v1") = "真实GA";
labels(strlength(labels) == 0) = methods(strlength(labels) == 0);
summary.display_label = labels;
summary.comsol_budget = summary.rows_total;
end

function summary = keep_method_rows(summary)
orderedMethods = [
    "random_family_balanced_v1"
    "predictor_only_topk_v10_v1"
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

function plot_56a_overlap(summary, outDir)
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 980 560]);
values = [summary.mean_target_overlap_Hz, summary.best_target_overlap_Hz];
b = bar(values, 'grouped');
b(1).FaceColor = [0.30 0.55 0.78];
b(2).FaceColor = [0.90 0.55 0.25];
grid on;
box off;
xticks(1:height(summary));
xticklabels(summary.display_label);
ylabel('目标频带重叠宽度 / Hz');
legend({'平均 overlap', '最优 overlap'}, 'Location', 'northwest');
ylim([0, max(values, [], 'all') * 1.20]);
add_grouped_bar_labels(values);
save_figure(fig, outDir, 'figure_5_6a_target_overlap_comparison_cn_titleless');
end

function plot_56b_rates(summary, outDir)
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
legend({'求解成功率', '接触有效率', '目标频带命中率'}, 'Location', 'southoutside', 'Orientation', 'horizontal');
ylim([0, 115]);
add_grouped_bar_labels(values);
save_figure(fig, outDir, 'figure_5_6b_validation_hit_rates_cn_titleless');
end

function plot_56c_budget_curve(summary, realGa, outDir)
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 1020 600]);
evalIndex = numeric_column(realGa, "eval_index", 1);
bestSoFar = numeric_column(realGa, "best_so_far_target_overlap_Hz", width(realGa));
valid = isfinite(evalIndex) & isfinite(bestSoFar);
evalIndex = evalIndex(valid);
bestSoFar = bestSoFar(valid);
hold on;
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
    if method == "predictor_only_topk_v10_v1"
        color = [0.20 0.58 0.47];
        offset = [0.45, 0.82];
    else
        color = [0.55 0.55 0.55];
        offset = [0.45, -0.75];
    end
    scatter(x, y, 115, 'filled', 'MarkerFaceColor', color, 'MarkerEdgeColor', 'k');
    text(x + offset(1), y + offset(2), sprintf('%s %.1f Hz', summary.display_label(i), y), ...
        'FontSize', 10, 'VerticalAlignment', 'middle');
end

grid on;
box off;
xlabel('真实 COMSOL 评价次数');
ylabel('截至当前预算的最优 target overlap / Hz');
legend({'真实GA best-so-far', '6次验证方法'}, 'Location', 'southeast');
xlim([0, max(evalIndex) + 2]);
ylim([0, max([bestSoFar; summary.best_target_overlap_Hz]) * 1.15]);
save_figure(fig, outDir, 'figure_5_6c_budget_efficiency_curve_cn_titleless');
end

function plot_56d_budget_scatter(summary, outDir)
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 900 560]);
openRate = summary.target_open_rate;
sizes = 90 + 220 * openRate;
colors = [
    0.55 0.55 0.55
    0.20 0.58 0.47
    0.20 0.32 0.55
];
hold on;
for i = 1:height(summary)
    scatter(summary.rows_total(i), summary.best_target_overlap_Hz(i), sizes(i), ...
        'filled', 'MarkerFaceColor', colors(i, :), 'MarkerEdgeColor', 'k');
    text(summary.rows_total(i) + 0.45, summary.best_target_overlap_Hz(i), ...
        sprintf('%s %.1f Hz', summary.display_label(i), summary.best_target_overlap_Hz(i)), ...
        'FontSize', 10, 'VerticalAlignment', 'middle');
end
grid on;
box off;
xlabel('真实 COMSOL 评价次数');
ylabel('最优 target overlap / Hz');
xlim([0, max(summary.rows_total) + 7]);
ylim([min(summary.best_target_overlap_Hz) - 1, max(summary.best_target_overlap_Hz) + 2]);
save_figure(fig, outDir, 'figure_5_6d_budget_quality_scatter_cn_titleless');
end

function export_active_learning(rootDir, outDir)
analysisDir = fullfile(rootDir, 'data', 'analysis', 'targetband_active_learning_v10');
bands = [
    struct('tag', "band140_180", 'label', "140-180 Hz", 'low', 140, 'high', 180)
    struct('tag', "band160_200", 'label', "160-200 Hz", 'low', 160, 'high', 200)
    struct('tag', "band180_220", 'label', "180-220 Hz", 'low', 180, 'high', 220)
    struct('tag', "band200_240", 'label', "200-240 Hz", 'low', 200, 'high', 240)
    struct('tag', "band220_260", 'label', "220-260 Hz", 'low', 220, 'high', 260)
    struct('tag', "band240_280", 'label', "240-280 Hz", 'low', 240, 'high', 280)
];

gaSummary = load_ga_generation_summary(rootDir, bands);
scoreSummary = load_candidate_score_summary(rootDir, bands);
holdoutSummary = readtable(fullfile(analysisDir, 'holdout_prediction_summary_v1.csv'), ...
    'TextType', 'string', 'VariableNamingRule', 'preserve');
holdoutSummary = holdoutSummary(holdoutSummary.model_run == "v10_multiband_active_ga", :);

plot_57a_ga_convergence(gaSummary, bands, outDir);
plot_57b_ga_final_best(gaSummary, bands, outDir);
plot_57c_holdout_truth_vs_pred(holdoutSummary, bands, outDir);
plot_57d_candidate_predicted_best(scoreSummary, bands, outDir);
plot_57e_sixband_predictor_vs_ga(scoreSummary, gaSummary, bands, outDir);
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

function plot_57a_ga_convergence(gaSummary, bands, outDir)
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
legend({bands.label}, 'Location', 'northwest');
xlim([1, max(gaSummary.generation)]);
ylim([0, max(gaSummary.best_fitness) * 1.15]);
save_figure(fig, outDir, 'figure_5_7a_multiband_ga_convergence_cn_titleless');
end

function plot_57b_ga_final_best(gaSummary, bands, outDir)
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
ylim([0, max(values) * 1.20]);
add_bar_labels(values);
save_figure(fig, outDir, 'figure_5_7b_multiband_ga_final_best_cn_titleless');
end

function plot_57c_holdout_truth_vs_pred(holdoutSummary, bands, outDir)
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
ylabel('holdout 集合 overlap / Hz');
legend({'COMSOL 真值上限', '模型预测上限'}, 'Location', 'northwest');
ylim([0, max(values, [], 'all') * 1.20]);
add_grouped_bar_labels(values);
save_figure(fig, outDir, 'figure_5_7c_holdout_truth_vs_prediction_cn_titleless');
end

function plot_57d_candidate_predicted_best(scoreSummary, bands, outDir)
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
ylim([0, max(values) * 1.20]);
add_bar_labels(values);
save_figure(fig, outDir, 'figure_5_7d_candidate_pool_predicted_best_cn_titleless');
end

function plot_57e_sixband_predictor_vs_ga(scoreSummary, gaSummary, bands, outDir)
predictorBest = zeros(numel(bands), 1);
predictorTruth = nan(numel(bands), 1);
gaBest = zeros(numel(bands), 1);
bandLabel = strings(numel(bands), 1);
rootDir = fileparts(fileparts(fileparts(fileparts(outDir))));
truthPath = fullfile(rootDir, 'data', 'comsol_batch', ...
    'stage4_validation_multiband_predictor_top1_v1', 'stage4_validation_results.csv');
if isfile(truthPath)
    truthTable = readtable(truthPath, 'TextType', 'string', 'VariableNamingRule', 'preserve');
else
    truthTable = table();
end
for i = 1:numel(bands)
    scoreRow = scoreSummary(scoreSummary.band_tag == bands(i).tag, :);
    gaRows = gaSummary(gaSummary.band_tag == bands(i).tag, :);
    predictorBest(i) = scoreRow.topk_best_overlap_pred_Hz(1);
    gaBest(i) = max(gaRows.best_fitness);
    bandLabel(i) = bands(i).label;
    if ~isempty(truthTable)
        label = "predictor_top1_" + erase(bands(i).label, " ");
        row = truthTable(truthTable.selection_label == label, :);
        if ~isempty(row) && row.solve_success(1) == 1 && row.geometry_valid(1) == 1 && row.contact_valid(1) == 1
            lowerEdge = row.gap34_lower_edge_Hz(1);
            upperEdge = row.gap34_upper_edge_Hz(1);
            predictorTruth(i) = max(0, min(upperEdge, bands(i).high) - max(lowerEdge, bands(i).low));
        else
            predictorTruth(i) = 0;
        end
    end
end

compareTable = table( ...
    bandLabel, predictorBest, predictorTruth, gaBest, gaBest - predictorTruth, predictorTruth ./ gaBest, ...
    'VariableNames', { ...
        'band_label', ...
        'predictor_candidate_pool_best_pred_overlap_Hz', ...
        'predictor_top1_comsol_truth_overlap_Hz', ...
        'real_ga_12gen_best_comsol_overlap_Hz', ...
        'ga_minus_predictor_truth_Hz', ...
        'predictor_truth_to_ga_ratio' ...
    });
writetable(compareTable, fullfile(fileparts(outDir), 'sixband_predictor_vs_ga_summary_v1.csv'));

fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 1040 580]);
values = [predictorBest, predictorTruth, gaBest];
b = bar(values, 'grouped');
b(1).FaceColor = [0.20 0.58 0.47];
b(2).FaceColor = [0.86 0.52 0.24];
b(3).FaceColor = [0.20 0.32 0.55];
grid on;
box off;
xticks(1:numel(bands));
xticklabels({bands.label});
xtickangle(25);
ylabel('目标频带 overlap / Hz');
legend({'预测器最高预测值', '预测候选COMSOL真值', '真实GA第12代COMSOL最优值'}, ...
    'Location', 'northwest');
ylim([0, max(values, [], 'all') * 1.20]);
add_grouped_bar_labels(values);
save_figure(fig, outDir, 'figure_5_7e_sixband_predictor_vs_ga_cn_titleless');
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

function values = numeric_column(t, candidateName, fallbackIndex)
names = string(t.Properties.VariableNames);
names = erase(names, char(65279));
idx = find(names == candidateName, 1);
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

function save_figure(fig, outDir, stem)
svgPath = fullfile(outDir, [stem '.svg']);
pngPath = fullfile(outDir, [stem '.png']);
print(fig, svgPath, '-dsvg');
exportgraphics(fig, pngPath, 'Resolution', 300);
close(fig);
fprintf('[SVG] %s\n', svgPath);
fprintf('[PNG] %s\n', pngPath);
end
