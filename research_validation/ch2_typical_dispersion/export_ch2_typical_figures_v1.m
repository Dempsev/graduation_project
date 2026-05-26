function outputs = export_ch2_typical_figures_v1()
%EXPORT_CH2_TYPICAL_FIGURES_V1 Export Chapter 2.6 figures as PNG/SVG.

rootDir = fileparts(fileparts(fileparts(mfilename('fullpath'))));
dataDir = fullfile(rootDir, 'data', 'research_validation', 'ch2_typical_dispersion');
figDir = fullfile(dataDir, 'figures');
if ~exist(figDir, 'dir'), mkdir(figDir); end

resultsCsv = fullfile(dataDir, 'ch2_local_perturb_variant_results.csv');
if ~isfile(resultsCsv)
    resultsCsv = fullfile(dataDir, 'ch2_typical_local_perturb_results_v1.csv');
end
tbl = readtable(resultsCsv, 'TextType', 'string', 'Delimiter', ',', 'VariableNamingRule', 'preserve');

outputs = struct();
outputs.dispersion_png = fullfile(figDir, 'ch2_typical_local_dispersion_compare.png');
outputs.dispersion_svg = fullfile(figDir, 'ch2_typical_local_dispersion_compare.svg');
outputs.heatmap_png = fullfile(figDir, 'ch2_local_perturb_cover_ratio_heatmap.png');
outputs.heatmap_svg = fullfile(figDir, 'ch2_local_perturb_cover_ratio_heatmap.svg');
outputs.edges_png = fullfile(figDir, 'ch2_local_perturb_band_edge_variation.png');
outputs.edges_svg = fullfile(figDir, 'ch2_local_perturb_band_edge_variation.svg');

plot_dispersion_compare(tbl, outputs.dispersion_png, outputs.dispersion_svg);
plot_cover_heatmap(tbl, outputs.heatmap_png, outputs.heatmap_svg);
plot_edge_variation(tbl, outputs.edges_png, outputs.edges_svg);

fprintf('Chapter 2.6 figures exported:\n');
fprintf('  %s\n  %s\n  %s\n', outputs.dispersion_png, outputs.heatmap_png, outputs.edges_png);
end

function plot_dispersion_compare(tbl, pngPath, svgPath)
cases = unique(tbl.case_id, 'stable');
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [80 80 1450 950]);
tiledlayout(2, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
for i = 1:numel(cases)
    ax = nexttile;
    caseRows = tbl(tbl.case_id == cases(i), :);
    center = caseRows(caseRows.variant == "center", :);
    variants = ["center", "b2_plus", "r0_plus", "r0_minus"];
    labels = ["中心结构", "b2+", "r0+", "r0-"];
    colors = [0 0 0; 0.10 0.35 0.78; 0.80 0.18 0.12; 0.92 0.45 0.18];
    targetLow = center.target_band_low_Hz(1);
    targetHigh = center.target_band_high_Hz(1);
    hold(ax, 'on');
    yspan(ax, targetLow, targetHigh, [1.0 0.86 0.25], 0.22);
    for v = 1:numel(variants)
        row = caseRows(caseRows.variant == variants(v), :);
        if isempty(row) || row.solve_success(1) ~= 1 || ~isfile(row.tbl1_csv(1))
            continue;
        end
        [kVals, bandMatrix] = read_band_matrix(char(row.tbl1_csv(1)));
        if size(bandMatrix, 2) >= 4
            plot(ax, kVals, bandMatrix(:, 3), '-', 'Color', colors(v, :), 'LineWidth', 1.35, 'DisplayName', labels(v));
            plot(ax, kVals, bandMatrix(:, 4), '--', 'Color', colors(v, :), 'LineWidth', 1.35, 'HandleVisibility', 'off');
        end
    end
    title(ax, sprintf('%s  %s', center.case_id(1), center.target_band(1)), 'Interpreter', 'none');
    xlabel(ax, '波矢路径参数 k');
    ylabel(ax, '频率 / Hz');
    ylim(ax, [max(0, targetLow - 70), targetHigh + 80]);
    xlim(ax, [0 3]);
    grid(ax, 'on');
    box(ax, 'on');
    if i == 1
        legend(ax, 'Location', 'northwest');
    end
    set_cn_axes(ax);
end
sgtitle('典型结构局部参数扰动下的频散曲线对比', 'FontName', 'Microsoft YaHei', 'FontSize', 18);
export_both(fig, pngPath, svgPath);
end

function plot_cover_heatmap(tbl, pngPath, svgPath)
cases = unique(tbl.case_id, 'stable');
variants = ["a1_plus","a1_minus","a2_plus","a2_minus","b2_plus","b2_minus","r0_plus","r0_minus"];
labels = ["a1+","a1-","a2+","a2-","b2+","b2-","r0+","r0-"];
Z = nan(numel(cases), numel(variants));
for i = 1:numel(cases)
    caseRows = tbl(tbl.case_id == cases(i), :);
    for j = 1:numel(variants)
        row = caseRows(caseRows.variant == variants(j), :);
        if ~isempty(row) && row.solve_success(1) == 1
            Z(i, j) = row.cover_ratio(1);
        end
    end
end
    fig = figure('Visible', 'off', 'Color', 'w', 'Position', [80 80 1450 820]);
ax = axes(fig);
imagesc(ax, Z, [0 1]);
colormap(ax, parula(256));
cb = colorbar(ax);
cb.Label.String = '目标频带覆盖率';
    set(ax, 'XTick', 1:numel(labels), 'XTickLabel', labels, 'YTick', 1:numel(cases), 'YTickLabel', cases, 'TickLabelInterpreter', 'none');
xtickangle(ax, 0);
title(ax, '典型结构局部参数扰动下的目标频带覆盖率');
for i = 1:numel(cases)
    for j = 1:numel(variants)
        if isnan(Z(i, j))
            text(ax, j, i, '失败', 'HorizontalAlignment', 'center', ...
                'Color', [0.05 0.05 0.05], 'FontSize', 14, 'FontWeight', 'bold', ...
                'BackgroundColor', [1 1 1], 'Margin', 2);
        else
            text(ax, j, i, sprintf('%.3f', Z(i, j)), 'HorizontalAlignment', 'center', ...
                'Color', [0.02 0.02 0.02], 'FontSize', 14, 'FontWeight', 'bold', ...
                'BackgroundColor', [1 1 1], 'Margin', 2);
        end
    end
end
set_cn_axes(ax);
export_both(fig, pngPath, svgPath);
end

function plot_edge_variation(tbl, pngPath, svgPath)
cases = unique(tbl.case_id, 'stable');
variantOrder = ["center","a1_plus","a1_minus","a2_plus","a2_minus","b2_plus","b2_minus","r0_plus","r0_minus"];
variantLabels = ["中心","a1+","a1-","a2+","a2-","b2+","b2-","r0+","r0-"];
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [80 80 1450 900]);
tiledlayout(2, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
for i = 1:numel(cases)
    ax = nexttile;
    caseRows = tbl(tbl.case_id == cases(i), :);
    center = caseRows(caseRows.variant == "center", :);
    targetLow = center.target_band_low_Hz(1);
    targetHigh = center.target_band_high_Hz(1);
    hold(ax, 'on');
    xBand = [0.4 numel(variantOrder)+0.6];
    yspan(ax, targetLow, targetHigh, [1.0 0.86 0.25], 0.24, xBand);
    for j = 1:numel(variantOrder)
        row = caseRows(caseRows.variant == variantOrder(j), :);
        if isempty(row) || row.solve_success(1) ~= 1
            plot(ax, j, targetLow, 'x', 'Color', [0.8 0.1 0.1], 'LineWidth', 1.2);
            continue;
        end
        c = color_for_variant(variantOrder(j));
        plot(ax, [j j], [row.band_lower_Hz(1), row.band_upper_Hz(1)], '-', 'Color', c, 'LineWidth', 2.1);
        plot(ax, j, row.band_lower_Hz(1), 'o', 'Color', c, 'MarkerFaceColor', c, 'MarkerSize', 4.5);
        plot(ax, j, row.band_upper_Hz(1), 's', 'Color', c, 'MarkerFaceColor', c, 'MarkerSize', 4.5);
    end
    xlim(ax, xBand);
    set(ax, 'XTick', 1:numel(variantLabels), 'XTickLabel', variantLabels, 'TickLabelInterpreter', 'none');
    xtickangle(ax, 30);
    finiteEdges = [caseRows.band_lower_Hz; caseRows.band_upper_Hz; targetLow; targetHigh];
    finiteEdges = finiteEdges(isfinite(finiteEdges));
    yPad = max(5, 0.08 * (max(finiteEdges) - min(finiteEdges)));
    ylim(ax, [max(0, min(finiteEdges) - yPad), max(finiteEdges) + yPad]);
    ylabel(ax, '带隙边界 / Hz');
    title(ax, sprintf('%s  %s', center.case_id(1), center.target_band(1)), 'Interpreter', 'none');
    grid(ax, 'on');
    box(ax, 'on');
    set_cn_axes(ax);
end
sgtitle('典型结构局部参数扰动下的带隙边界变化', 'FontName', 'Microsoft YaHei', 'FontSize', 18);
export_both(fig, pngPath, svgPath);
end

function [uniqueK, bandMatrix] = read_band_matrix(tbl1Path)
raw = readcell(tbl1Path, 'Delimiter', ',');
kVals = [];
freqVals = [];
for i = 1:size(raw, 1)
    if size(raw, 2) < 3, continue; end
    k = numeric_cell(raw{i, 1});
    f = numeric_cell(raw{i, end});
    if isfinite(k) && isfinite(f)
        kVals(end+1, 1) = k; %#ok<AGROW>
        freqVals(end+1, 1) = f; %#ok<AGROW>
    end
end
[uniqueK, ~, idx] = unique(kVals, 'sorted');
maxBands = 0;
bands = cell(numel(uniqueK), 1);
for i = 1:numel(uniqueK)
    f = sort(freqVals(idx == i));
    bands{i} = f(:);
    maxBands = max(maxBands, numel(f));
end
bandMatrix = nan(numel(uniqueK), maxBands);
for i = 1:numel(uniqueK)
    f = bands{i};
    bandMatrix(i, 1:numel(f)) = f;
end
end

function value = numeric_cell(x)
value = NaN;
if isnumeric(x) && isscalar(x)
    value = double(real(x));
    return;
end
if ismissing(x), return; end
s = strtrim(char(string(x)));
if isempty(s) || startsWith(s, '%'), return; end
try
    parsed = str2num(s); %#ok<ST2NM>
    if ~isempty(parsed)
        value = double(real(parsed(1)));
    end
catch
end
end

function yspan(ax, y1, y2, color, alphaVal, xLimits)
if nargin < 6 || isempty(xLimits)
    xLimits = [0 3];
end
xl = xLimits;
patch(ax, [xl(1) xl(2) xl(2) xl(1)], [y1 y1 y2 y2], color, ...
    'FaceAlpha', alphaVal, 'EdgeColor', 'none', 'HandleVisibility', 'off');
end

function c = color_for_variant(v)
if v == "center"
    c = [0 0 0];
elseif startsWith(v, "a1")
    c = [0.10 0.35 0.78];
elseif startsWith(v, "a2")
    c = [0.18 0.56 0.25];
elseif startsWith(v, "b2")
    c = [0.90 0.45 0.10];
else
    c = [0.80 0.18 0.12];
end
end

function c = text_color(v)
if v > 0.55
    c = [1 1 1];
else
    c = [0.1 0.1 0.1];
end
end

function set_cn_axes(ax)
try
    set(ax, 'FontName', 'Microsoft YaHei', 'FontSize', 11, 'LineWidth', 1.0, 'TickLabelInterpreter', 'none');
    ax.Title.FontName = 'Microsoft YaHei';
    ax.XLabel.FontName = 'Microsoft YaHei';
    ax.YLabel.FontName = 'Microsoft YaHei';
catch
end
end

function export_both(fig, pngPath, svgPath)
exportgraphics(fig, pngPath, 'Resolution', 240);
print(fig, svgPath, '-dsvg', '-painters');
close(fig);
end
