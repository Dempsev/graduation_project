function redraw_ch3_predictor_v12_polished()
%REDRAW_CH3_PREDICTOR_V12_POLISHED Replot Chapter 3 predictor figures.
% This script reads existing v12 CSV/JSON results only. It does not retrain
% models and does not modify project code.

rootDir = fileparts(fileparts(fileparts(fileparts(mfilename('fullpath')))));
outDir = fullfile(rootDir, 'research_validation', 'ch3_predictor_v12_figures', 'matlab_polished');
if ~exist(outDir, 'dir')
    mkdir(outDir);
end

readinessDir = fullfile(rootDir, 'data', 'analysis', 'predictor_readiness_v12_all_history_ga20_clean_v1');
datasetInfoPath = fullfile(rootDir, 'data', 'prediction_targetband_param_v1', 'v1', ...
    'windows_dense_v12_all_history_ga20_clean_v1', 'dataset_info.json');

src.familyCls = fullfile(readinessDir, 'family_cv_classifier_by_band.csv');
src.loboCls = fullfile(readinessDir, 'leave_one_band_classifier_by_band.csv');
src.familyReg = fullfile(readinessDir, 'family_cv_regressor_by_band.csv');
src.loboReg = fullfile(readinessDir, 'leave_one_band_regressor_by_band.csv');
src.familyTopk = fullfile(readinessDir, 'family_cv_topk_summary.csv');
src.loboTopk = fullfile(readinessDir, 'leave_one_band_topk_summary.csv');
src.datasetInfo = datasetInfoPath;

familyCls = readtable(src.familyCls, 'Delimiter', ',');
loboCls = readtable(src.loboCls, 'Delimiter', ',');
familyReg = readtable(src.familyReg, 'Delimiter', ',');
loboReg = readtable(src.loboReg, 'Delimiter', ',');
familyTopk = readtable(src.familyTopk, 'Delimiter', ',');
loboTopk = readtable(src.loboTopk, 'Delimiter', ',');
datasetInfo = jsondecode(fileread(src.datasetInfo));

bandTags = {'band140_180','band160_200','band180_220','band200_240','band220_260','band240_280'};
bandLabels = {'140-180','160-200','180-220','200-240','220-260','240-280'};

familyCls = orderByBand(familyCls, bandTags);
loboCls = orderByBand(loboCls, bandTags);
familyReg = orderByBand(familyReg, bandTags);
loboReg = orderByBand(loboReg, bandTags);
bandSummary = thesisBandSummaryTable(datasetInfo, bandTags);

style = plotStyle();
outputs = strings(0, 5);

[pngPath, pdfPath, svgPath] = plotClassification(familyCls, loboCls, bandLabels, style, outDir);
outputs(end + 1, :) = ["六个目标频带分类性能对比", string(src.familyCls) + newline + string(src.loboCls), ...
    string(mfilename('fullpath')) + ".m", string(pngPath), string(pdfPath) + newline + string(svgPath)];

[pngPath, pdfPath, svgPath] = plotRegressionMae(familyReg, loboReg, bandLabels, style, outDir);
outputs(end + 1, :) = ["六个目标频带覆盖率回归 MAE 对比", string(src.familyReg) + newline + string(src.loboReg), ...
    string(mfilename('fullpath')) + ".m", string(pngPath), string(pdfPath) + newline + string(svgPath)];

[pngPath, pdfPath, svgPath] = plotTopkCover(familyTopk, loboTopk, style, outDir);
outputs(end + 1, :) = ["Top-k 候选平均真实覆盖率对比", string(src.familyTopk) + newline + string(src.loboTopk), ...
    string(mfilename('fullpath')) + ".m", string(pngPath), string(pdfPath) + newline + string(svgPath)];

[pngPath, pdfPath, svgPath] = plotBandDistribution(bandSummary, bandLabels, style, outDir);
outputs(end + 1, :) = ["六个目标频带样本分布与平均覆盖率", string(src.datasetInfo), ...
    string(mfilename('fullpath')) + ".m", string(pngPath), string(pdfPath) + newline + string(svgPath)];

writeReadme(outDir, src, outputs);
disp('[DONE] MATLAB polished Chapter 3 figures exported:');
disp(outDir);
end

function style = plotStyle()
style.fontCn = 'Microsoft YaHei';
style.familyColor = [0.30, 0.46, 0.58];
style.loboColor = [0.54, 0.47, 0.37];
style.posColor = [0.48, 0.60, 0.68];
style.negColor = [0.82, 0.84, 0.86];
style.coverColor = [0.20, 0.23, 0.25];
style.gridColor = [0.84, 0.86, 0.88];
style.axisColor = [0.22, 0.24, 0.26];
style.figW = 14.0;
style.figH = 8.6;
style.titleSize = 13;
style.labelSize = 10.5;
style.tickSize = 9.5;
style.legendSize = 9.5;
style.lineWidth = 1.65;
style.markerSize = 5.8;
set(groot, 'defaultAxesFontName', style.fontCn);
set(groot, 'defaultTextFontName', style.fontCn);
set(groot, 'defaultAxesLineWidth', 0.85);
set(groot, 'defaultAxesXColor', style.axisColor);
set(groot, 'defaultAxesYColor', style.axisColor);
set(groot, 'defaultAxesGridColor', style.gridColor);
set(groot, 'defaultAxesGridAlpha', 0.35);
end

function tbl = orderByBand(tbl, bandTags)
[tf, loc] = ismember(bandTags, cellstr(tbl.target_band_tag));
if ~all(tf)
    missing = strjoin(bandTags(~tf), ', ');
    error('Missing target bands in table: %s', missing);
end
tbl = tbl(loc, :);
end

function tbl = thesisBandSummaryTable(datasetInfo, bandTags)
summary = datasetInfo.thesis_band_summary;
tags = strings(numel(summary), 1);
rows = zeros(numel(summary), 1);
positiveRows = zeros(numel(summary), 1);
positiveRate = zeros(numel(summary), 1);
maxCover = zeros(numel(summary), 1);
meanCover = zeros(numel(summary), 1);
for i = 1:numel(summary)
    tags(i) = string(summary(i).target_band_tag);
    rows(i) = summary(i).rows;
    positiveRows(i) = summary(i).positive_rows;
    positiveRate(i) = summary(i).positive_rate;
    maxCover(i) = summary(i).max_cover_ratio;
    meanCover(i) = summary(i).mean_cover_ratio;
end
tbl = table(tags, rows, positiveRows, positiveRate, maxCover, meanCover, ...
    'VariableNames', {'target_band_tag','rows','positive_rows','positive_rate','max_cover_ratio','mean_cover_ratio'});
[tf, loc] = ismember(string(bandTags), tbl.target_band_tag);
if ~all(tf)
    error('Missing target bands in dataset_info.json.');
end
tbl = tbl(loc, :);
end

function fig = newFigure(style)
fig = figure('Color', 'w', 'Units', 'centimeters', 'Position', [2, 2, style.figW, style.figH], ...
    'PaperUnits', 'centimeters', 'PaperPosition', [0, 0, style.figW, style.figH]);
end

function styleAxes(ax, style)
grid(ax, 'on');
box(ax, 'on');
ax.FontName = style.fontCn;
ax.FontSize = style.tickSize;
ax.LineWidth = 0.85;
ax.GridAlpha = 0.22;
ax.MinorGridAlpha = 0.12;
end

function [pngPath, pdfPath, svgPath] = plotClassification(familyCls, loboCls, bandLabels, style, outDir)
fig = newFigure(style);
t = tiledlayout(fig, 2, 1, 'TileSpacing', 'compact', 'Padding', 'compact');
title(t, '六个目标频带分类性能对比', 'FontSize', style.titleSize, 'FontWeight', 'bold');
x = 1:numel(bandLabels);

ax1 = nexttile(t, 1);
plot(ax1, x, familyCls.f1, '-o', 'Color', style.familyColor, 'LineWidth', style.lineWidth, ...
    'MarkerSize', style.markerSize, 'MarkerFaceColor', lighten(style.familyColor, 0.35), 'DisplayName', 'Family-CV');
hold(ax1, 'on');
plot(ax1, x, loboCls.f1, '-s', 'Color', style.loboColor, 'LineWidth', style.lineWidth, ...
    'MarkerSize', style.markerSize, 'MarkerFaceColor', lighten(style.loboColor, 0.35), 'DisplayName', 'leave-one-band');
ylabel(ax1, 'F1', 'FontSize', style.labelSize);
ylim(ax1, [0, 1]);
xlim(ax1, [0.7, numel(bandLabels) + 0.3]);
set(ax1, 'XTick', x, 'XTickLabel', []);
legend(ax1, 'Location', 'southwest', 'FontSize', style.legendSize, 'Box', 'off');
styleAxes(ax1, style);

ax2 = nexttile(t, 2);
plot(ax2, x, familyCls.balanced_accuracy, '-o', 'Color', style.familyColor, 'LineWidth', style.lineWidth, ...
    'MarkerSize', style.markerSize, 'MarkerFaceColor', lighten(style.familyColor, 0.35), 'DisplayName', 'Family-CV');
hold(ax2, 'on');
plot(ax2, x, loboCls.balanced_accuracy, '-s', 'Color', style.loboColor, 'LineWidth', style.lineWidth, ...
    'MarkerSize', style.markerSize, 'MarkerFaceColor', lighten(style.loboColor, 0.35), 'DisplayName', 'leave-one-band');
ylabel(ax2, '平衡准确率', 'FontSize', style.labelSize);
xlabel(ax2, '目标频带 / Hz', 'FontSize', style.labelSize);
ylim(ax2, [0, 1]);
xlim(ax2, [0.7, numel(bandLabels) + 0.3]);
set(ax2, 'XTick', x, 'XTickLabel', bandLabels);
legend(ax2, 'Location', 'southwest', 'FontSize', style.legendSize, 'Box', 'off');
styleAxes(ax2, style);

[pngPath, pdfPath, svgPath] = exportFigure(fig, outDir, 'ch3_matlab_band_classification_lines');
end

function [pngPath, pdfPath, svgPath] = plotRegressionMae(familyReg, loboReg, bandLabels, style, outDir)
fig = newFigure(style);
ax = axes(fig);
x = 1:numel(bandLabels);
plot(ax, x, familyReg.mae, '-o', 'Color', style.familyColor, 'LineWidth', style.lineWidth, ...
    'MarkerSize', style.markerSize, 'MarkerFaceColor', lighten(style.familyColor, 0.35), 'DisplayName', 'Family-CV MAE');
hold(ax, 'on');
plot(ax, x, loboReg.mae, '-s', 'Color', style.loboColor, 'LineWidth', style.lineWidth, ...
    'MarkerSize', style.markerSize, 'MarkerFaceColor', lighten(style.loboColor, 0.35), 'DisplayName', 'leave-one-band MAE');
title(ax, '六个目标频带覆盖率回归 MAE 对比', 'FontSize', style.titleSize, 'FontWeight', 'bold');
xlabel(ax, '目标频带 / Hz', 'FontSize', style.labelSize);
ylabel(ax, '覆盖率 MAE', 'FontSize', style.labelSize);
xlim(ax, [0.7, numel(bandLabels) + 0.3]);
ylim(ax, [0, max([familyReg.mae; loboReg.mae]) * 1.25]);
set(ax, 'XTick', x, 'XTickLabel', bandLabels);
legend(ax, 'Location', 'northwest', 'FontSize', style.legendSize, 'Box', 'off');
styleAxes(ax, style);
[pngPath, pdfPath, svgPath] = exportFigure(fig, outDir, 'ch3_matlab_band_regression_mae_lines');
end

function [pngPath, pdfPath, svgPath] = plotTopkCover(familyTopk, loboTopk, style, outDir)
fig = newFigure(style);
ax = axes(fig);
familyTopk = familyTopk(ismember(familyTopk.k, [5; 10]), :);
loboTopk = loboTopk(ismember(loboTopk.k, [5; 10]), :);
x = 1:height(familyTopk);
labels = compose('Top-%d', familyTopk.k);
plot(ax, x, familyTopk.mean_topk_cover, '-o', 'Color', style.familyColor, 'LineWidth', style.lineWidth, ...
    'MarkerSize', style.markerSize, 'MarkerFaceColor', lighten(style.familyColor, 0.35), 'DisplayName', 'Family-CV');
hold(ax, 'on');
plot(ax, x, loboTopk.mean_topk_cover, '-s', 'Color', style.loboColor, 'LineWidth', style.lineWidth, ...
    'MarkerSize', style.markerSize, 'MarkerFaceColor', lighten(style.loboColor, 0.35), 'DisplayName', 'leave-one-band');
title(ax, 'Top-k 候选平均真实覆盖率对比', 'FontSize', style.titleSize, 'FontWeight', 'bold');
xlabel(ax, '候选数量', 'FontSize', style.labelSize);
ylabel(ax, '平均真实覆盖率', 'FontSize', style.labelSize);
xlim(ax, [0.75, height(familyTopk) + 0.25]);
ylim(ax, [0, max([familyTopk.mean_topk_cover; loboTopk.mean_topk_cover]) * 1.20]);
set(ax, 'XTick', x, 'XTickLabel', labels);
legend(ax, 'Location', 'southwest', 'FontSize', style.legendSize, 'Box', 'off');
styleAxes(ax, style);
[pngPath, pdfPath, svgPath] = exportFigure(fig, outDir, 'ch3_matlab_topk_mean_cover_lines');
end

function [pngPath, pdfPath, svgPath] = plotBandDistribution(tbl, bandLabels, style, outDir)
fig = newFigure(style);
ax = axes(fig);
x = 1:height(tbl);
negRows = tbl.rows - tbl.positive_rows;
barData = [tbl.positive_rows, negRows];
b = bar(ax, x, barData, 'stacked', 'BarWidth', 0.68);
b(1).FaceColor = style.posColor;
b(1).EdgeColor = 'none';
b(2).FaceColor = style.negColor;
b(2).EdgeColor = 'none';
hold(ax, 'on');
for i = 1:height(tbl)
    text(ax, x(i), tbl.rows(i) + 28, sprintf('%.2f', tbl.positive_rate(i)), ...
        'HorizontalAlignment', 'center', 'VerticalAlignment', 'bottom', ...
        'FontSize', style.tickSize, 'FontName', style.fontCn, 'Color', style.axisColor);
end
ylabel(ax, '样本数', 'FontSize', style.labelSize);
xlabel(ax, '目标频带 / Hz', 'FontSize', style.labelSize);
set(ax, 'XTick', x, 'XTickLabel', bandLabels);
xlim(ax, [0.55, height(tbl) + 0.45]);
ylim(ax, [0, max(tbl.rows) * 1.18]);
styleAxes(ax, style);

yyaxis(ax, 'right');
plot(ax, x, tbl.mean_cover_ratio, '-d', 'Color', style.coverColor, 'LineWidth', style.lineWidth, ...
    'MarkerSize', style.markerSize, 'MarkerFaceColor', lighten(style.coverColor, 0.45), 'DisplayName', '平均覆盖率');
ylabel(ax, '平均覆盖率', 'FontSize', style.labelSize);
ylim(ax, [0, max(tbl.mean_cover_ratio) * 1.35]);
ax.YColor = style.coverColor;

yyaxis(ax, 'left');
title(ax, '六个目标频带样本分布与平均覆盖率', 'FontSize', style.titleSize, 'FontWeight', 'bold');
legend(ax, {'正样本数','非正样本数','平均覆盖率'}, 'Location', 'northoutside', ...
    'Orientation', 'horizontal', 'FontSize', style.legendSize, 'Box', 'off');
[pngPath, pdfPath, svgPath] = exportFigure(fig, outDir, 'ch3_matlab_band_sample_distribution');
end

function colorOut = lighten(colorIn, amount)
colorOut = colorIn + (1 - colorIn) * amount;
end

function [pngPath, pdfPath, svgPath] = exportFigure(fig, outDir, stem)
pngPath = fullfile(outDir, [stem, '.png']);
pdfPath = fullfile(outDir, [stem, '.pdf']);
svgPath = fullfile(outDir, [stem, '.svg']);
exportgraphics(fig, pngPath, 'Resolution', 600);
exportgraphics(fig, pdfPath, 'ContentType', 'vector');
try
    exportgraphics(fig, svgPath, 'ContentType', 'vector');
catch
    try
        print(fig, svgPath, '-dsvg');
    catch
        svgPath = "";
    end
end
close(fig);
end

function writeReadme(outDir, src, outputs)
readmePath = fullfile(outDir, 'README.md');
fid = fopen(readmePath, 'w', 'n', 'UTF-8');
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, '# 第三章 MATLAB 精修图表说明\n\n');
fprintf(fid, '本目录中的图表由 `redraw_ch3_predictor_v12_polished.m` 生成，只读取既有第三章 v12 结果文件，不重新训练模型。\n\n');
fprintf(fid, '## 源数据文件\n\n');
fprintf(fid, '- Family-CV 分类结果：`%s`\n', src.familyCls);
fprintf(fid, '- Band-LOO 分类结果：`%s`\n', src.loboCls);
fprintf(fid, '- Family-CV 回归结果：`%s`\n', src.familyReg);
fprintf(fid, '- Band-LOO 回归结果：`%s`\n', src.loboReg);
fprintf(fid, '- Family-CV Top-k 结果：`%s`\n', src.familyTopk);
fprintf(fid, '- Band-LOO Top-k 结果：`%s`\n', src.loboTopk);
fprintf(fid, '- v12 数据集统计：`%s`\n\n', src.datasetInfo);
fprintf(fid, '## 图表清单\n\n');
fprintf(fid, '| 图题建议 | 源数据文件 | MATLAB 脚本 | PNG | 矢量文件 |\n');
fprintf(fid, '| --- | --- | --- | --- | --- |\n');
for i = 1:size(outputs, 1)
    fprintf(fid, '| %s | %s | `%s` | `%s` | `%s` |\n', ...
        outputs(i, 1), inlineBreaks(outputs(i, 2)), outputs(i, 3), outputs(i, 4), inlineBreaks(outputs(i, 5)));
end
fprintf(fid, '\n## 版式约定\n\n');
fprintf(fid, '- MATLAB 图宽约 14 cm，高约 8.6 cm。\n');
fprintf(fid, '- PNG 按 600 dpi 导出。\n');
fprintf(fid, '- PDF/SVG 按矢量格式导出，便于插入 Word 后继续排版。\n');
fprintf(fid, '- 配色采用低饱和蓝灰、棕灰和浅灰，避免 MATLAB 默认高饱和配色。\n');
fprintf(fid, '- 字体优先使用 Microsoft YaHei；如系统字体不可用，由 MATLAB 自动回退。\n');
end

function textOut = inlineBreaks(textIn)
textOut = replace(string(textIn), newline, '<br>');
end
