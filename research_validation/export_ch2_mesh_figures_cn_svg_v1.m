function outputs = export_ch2_mesh_figures_cn_svg_v1()
%EXPORT_CH2_MESH_FIGURES_CN_SVG_V1 Export Chinese SVG figures for Ch.2 mesh validation.

rootDir = fileparts(fileparts(mfilename('fullpath')));
outDir = fullfile(rootDir, 'data', 'research_validation', 'ch2_mesh_reliability_v1');
figDir = fullfile(outDir, 'figures');
resultCsv = fullfile(outDir, 'mesh_independence_results_v1.csv');
if ~isfile(resultCsv)
    error('export_ch2_mesh_figures_cn_svg_v1:MissingResults', 'Missing result CSV: %s', resultCsv);
end

tbl = readtable(resultCsv, 'TextType', 'string', 'Delimiter', ',', 'VariableNamingRule', 'preserve');
outputs = struct();
outputs.dispersion_svg = fullfile(figDir, 'mesh_dispersion_overlay_cn_v1.svg');
outputs.convergence_svg = fullfile(figDir, 'mesh_gap_convergence_cn_v1.svg');

export_dispersion_cn(tbl, outputs.dispersion_svg);
export_convergence_cn(tbl, outputs.convergence_svg);

fprintf('Chinese SVG figures exported:\n  %s\n  %s\n', outputs.dispersion_svg, outputs.convergence_svg);
end

function export_dispersion_cn(tbl, outPath)
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 1100 820]);
ax = axes(fig);
hold(ax, 'on');
colors = [0.1216 0.4667 0.7059; 0.8392 0.1529 0.1569; 0.1725 0.6275 0.1725];
lineStyles = {'-', '--', ':'};
labels = mesh_labels_cn(tbl.mesh_level);

for i = 1:height(tbl)
    [kVals, bandMatrix] = read_band_matrix(char(tbl.tbl1_csv(i)));
    maxBands = min(size(bandMatrix, 2), 8);
    for b = 1:maxBands
        if b == 1
            plot(ax, kVals, bandMatrix(:, b), lineStyles{i}, 'Color', colors(i, :), ...
                'LineWidth', 1.25, 'DisplayName', labels{i});
        else
            plot(ax, kVals, bandMatrix(:, b), lineStyles{i}, 'Color', colors(i, :), ...
                'LineWidth', 1.0, 'HandleVisibility', 'off');
        end
    end
end

fine = tbl(end, :);
yl = yline(ax, fine.gap34_lower_edge_Hz, '-.', '第3带上边界', ...
    'LabelHorizontalAlignment', 'left', 'LabelVerticalAlignment', 'bottom', ...
    'Color', [0.15 0.15 0.15], 'LineWidth', 1.0);
yu = yline(ax, fine.gap34_upper_edge_Hz, '-.', '第4带下边界', ...
    'LabelHorizontalAlignment', 'left', 'LabelVerticalAlignment', 'top', ...
    'Color', [0.15 0.15 0.15], 'LineWidth', 1.0);
try
    yl.FontName = 'Microsoft YaHei';
    yu.FontName = 'Microsoft YaHei';
catch
end

xlabel(ax, '波矢路径参数 k');
ylabel(ax, '频率 / Hz');
title(ax, '不同网格密度下的频散曲线对比');
legend(ax, 'Location', 'northeast');
grid(ax, 'on');
box(ax, 'on');
set_cn_axes(ax);
    print(fig, outPath, '-dsvg', '-painters');
close(fig);
end

function export_convergence_cn(tbl, outPath)
fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 1050 760]);
ax = axes(fig);
x = tbl.element_count;

yyaxis(ax, 'left');
plot(ax, x, tbl.gap34_Hz, '-o', 'LineWidth', 1.8, 'MarkerSize', 7);
ylabel(ax, '第3、4阶带隙宽度 / Hz');
ylim(ax, [floor(min(tbl.gap34_Hz) * 10) / 10, ceil(max(tbl.gap34_Hz) * 10) / 10]);

yyaxis(ax, 'right');
plot(ax, x, tbl.relative_error_percent, '-s', 'LineWidth', 1.8, 'MarkerSize', 7);
ylabel(ax, '相对误差 / %');
ylim(ax, [0, max(tbl.relative_error_percent) * 1.2 + eps]);

xlabel(ax, '网格单元数量');
title(ax, '第3、4阶带隙的网格收敛性');
grid(ax, 'on');
box(ax, 'on');
set_cn_axes(ax);

labels = mesh_labels_cn(tbl.mesh_level);
for i = 1:height(tbl)
    yyaxis(ax, 'left');
    text(ax, x(i), tbl.gap34_Hz(i), ['  ' labels{i}], ...
        'FontName', 'Microsoft YaHei', 'FontSize', 11, 'VerticalAlignment', 'bottom');
end
    print(fig, outPath, '-dsvg', '-painters');
close(fig);
end

function set_cn_axes(ax)
try
    set(ax, 'FontName', 'Microsoft YaHei', 'FontSize', 13, 'LineWidth', 1.0);
    ax.Title.FontName = 'Microsoft YaHei';
    ax.XLabel.FontName = 'Microsoft YaHei';
    ax.YLabel.FontName = 'Microsoft YaHei';
catch
end
end

function labels = mesh_labels_cn(meshLevel)
labels = cell(height(table(meshLevel)), 1);
for i = 1:numel(meshLevel)
    switch string(meshLevel(i))
        case "coarse"
            labels{i} = '粗网格';
        case "medium"
            labels{i} = '中等网格';
        case "fine"
            labels{i} = '细网格';
        otherwise
            labels{i} = char(string(meshLevel(i)));
    end
end
end

function [uniqueK, bandMatrix] = read_band_matrix(tbl1Path)
raw = readcell(tbl1Path, 'Delimiter', ',');
kVals = [];
freqVals = [];
for i = 1:size(raw, 1)
    if size(raw, 2) < 3
        continue;
    end
    k = numeric_cell(raw{i, 1});
    freq = numeric_cell(raw{i, end});
    if isfinite(k) && isfinite(freq)
        kVals(end + 1, 1) = k; %#ok<AGROW>
        freqVals(end + 1, 1) = freq; %#ok<AGROW>
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
if ismissing(x)
    return;
end
s = strtrim(char(string(x)));
if isempty(s) || startsWith(s, '%')
    return;
end
try
    parsed = str2num(s); %#ok<ST2NM>
    if ~isempty(parsed)
        value = double(real(parsed(1)));
    end
catch
end
end
