function metrics = extract_stage2_gap_metrics_from_tbl1(tbl1Path)
%EXTRACT_STAGE2_GAP_METRICS_FROM_TBL1 Compute stage-2 gap labels from COMSOL tbl1.
% The gap definition matches stage-1 and the current project postprocess:
% 1) For each k-point, frequencies are sorted in ascending order.
% 2) For adjacent bands n and n+1:
%    lower edge = max_k band_n(k)
%    upper edge = min_k band_{n+1}(k)
% 3) A positive gap exists when upper edge > lower edge.
% 4) The target gap is the largest positive gap among all adjacent pairs.

if ~isfile(tbl1Path)
    error('extract_stage2_gap_metrics_from_tbl1:MissingFile', 'tbl1 csv not found: %s', tbl1Path);
end

[kVals, freqVals] = read_tbl1_numeric(tbl1Path);
if isempty(kVals)
    error('extract_stage2_gap_metrics_from_tbl1:EmptyData', 'No numeric rows found in: %s', tbl1Path);
end

[uniqueK, ~, kIdx] = unique(kVals, 'sorted');
bandsByK = cell(numel(uniqueK), 1);
maxBands = 0;
for i = 1:numel(uniqueK)
    freq = sort(freqVals(kIdx == i), 'ascend');
    bandsByK{i} = freq(:);
    maxBands = max(maxBands, numel(freq));
end

bandMatrix = nan(numel(uniqueK), maxBands);
for i = 1:numel(uniqueK)
    freq = bandsByK{i};
    bandMatrix(i, 1:numel(freq)) = freq;
end

metrics = struct( ...
    'has_gap', false, ...
    'gap_target_Hz', 0, ...
    'gap_target_rel', NaN, ...
    'gap_lower_band', NaN, ...
    'gap_upper_band', NaN, ...
    'gap_center_freq', NaN, ...
    'gap_lower_edge_Hz', NaN, ...
    'gap_upper_edge_Hz', NaN ...
);

bestGap = -inf;
bestBand = NaN;
bestLower = NaN;
bestUpper = NaN;
for bandIdx = 1:(size(bandMatrix, 2) - 1)
    lower = bandMatrix(:, bandIdx);
    upper = bandMatrix(:, bandIdx + 1);
    if all(isnan(lower)) || all(isnan(upper))
        continue;
    end

    lower = lower(~isnan(lower));
    upper = upper(~isnan(upper));
    if isempty(lower) || isempty(upper)
        continue;
    end
    lowerEdge = max(lower);
    upperEdge = min(upper);
    gap = upperEdge - lowerEdge;
    if ~isfinite(gap) || gap <= 0 || gap <= bestGap
        continue;
    end

    bestGap = gap;
    bestBand = bandIdx;
    bestLower = lowerEdge;
    bestUpper = upperEdge;
end

if ~isfinite(bestGap) || bestGap <= 0
    return;
end

center = 0.5 * (bestLower + bestUpper);
metrics.has_gap = true;
metrics.gap_target_Hz = bestGap;
metrics.gap_lower_band = bestBand;
metrics.gap_upper_band = bestBand + 1;
metrics.gap_center_freq = center;
metrics.gap_lower_edge_Hz = bestLower;
metrics.gap_upper_edge_Hz = bestUpper;
if center ~= 0
    metrics.gap_target_rel = bestGap / center;
end
end

function [kVals, freqVals] = read_tbl1_numeric(tbl1Path)
kVals = [];
freqVals = [];

fid = fopen(tbl1Path, 'r');
if fid < 0
    error('extract_stage2_gap_metrics_from_tbl1:OpenFailed', 'Failed to open: %s', tbl1Path);
end
cleanupObj = onCleanup(@() fclose(fid)); %#ok<NASGU>

while true
    line = fgetl(fid);
    if ~ischar(line)
        break;
    end

    line = strtrim(line);
    if isempty(line) || startsWith(line, '%')
        continue;
    end

    parts = regexp(line, '\s*,\s*', 'split');
    if numel(parts) < 3
        continue;
    end

    k = str2double(parts{1});
    freq = parse_real_scalar(parts{end});
    if ~isfinite(k) || ~isfinite(freq)
        continue;
    end

    kVals(end + 1, 1) = k; %#ok<AGROW>
    freqVals(end + 1, 1) = freq; %#ok<AGROW>
end
end

function value = parse_real_scalar(raw)
value = NaN;
if isempty(raw)
    return;
end
if isnumeric(raw) && isscalar(raw)
    value = double(real(raw));
    return;
end

s = char(string(raw));
try
    parsed = str2num(s); %#ok<ST2NM>
    if ~isempty(parsed)
        value = double(real(parsed(1)));
        return;
    end
catch
end
end
