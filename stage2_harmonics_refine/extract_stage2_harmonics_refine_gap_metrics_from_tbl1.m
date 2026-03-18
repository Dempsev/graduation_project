function metrics = extract_stage2_harmonics_refine_gap_metrics_from_tbl1(tbl1Path, fixedGapBand)
%EXTRACT_STAGE2_HARMONICS_REFINE_GAP_METRICS_FROM_TBL1 Compute fixed-band and max-gap labels.
% The primary label is the gap between band n and n+1 for fixedGapBand=n.
% The legacy max-gap label is still exported for diagnostics.

if nargin < 2
    fixedGapBand = 3;
end
if ~isfile(tbl1Path)
    error('extract_stage2_harmonics_refine_gap_metrics_from_tbl1:MissingFile', 'tbl1 csv not found: %s', tbl1Path);
end

[kVals, freqVals] = read_tbl1_numeric(tbl1Path);
if isempty(kVals)
    error('extract_stage2_harmonics_refine_gap_metrics_from_tbl1:EmptyData', 'No numeric rows found in: %s', tbl1Path);
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
    'gap34_Hz', NaN, ...
    'gap34_rel', NaN, ...
    'gap34_lower_edge_Hz', NaN, ...
    'gap34_upper_edge_Hz', NaN, ...
    'gap34_center_freq', NaN, ...
    'max_gap_Hz', 0, ...
    'max_gap_rel', NaN, ...
    'max_gap_lower_band', NaN, ...
    'max_gap_upper_band', NaN, ...
    'max_gap_center_freq', NaN ...
);

if size(bandMatrix, 2) >= fixedGapBand + 1
    lower = bandMatrix(:, fixedGapBand);
    upper = bandMatrix(:, fixedGapBand + 1);
    lower = lower(~isnan(lower));
    upper = upper(~isnan(upper));
    if ~isempty(lower) && ~isempty(upper)
        lowerEdge = max(lower);
        upperEdge = min(upper);
        gap = upperEdge - lowerEdge;
        center = 0.5 * (lowerEdge + upperEdge);
        metrics.gap34_Hz = gap;
        metrics.gap34_lower_edge_Hz = lowerEdge;
        metrics.gap34_upper_edge_Hz = upperEdge;
        metrics.gap34_center_freq = center;
        if isfinite(center) && center ~= 0
            metrics.gap34_rel = gap / center;
        end
    end
end

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
if isfinite(bestGap) && bestGap > 0
    center = 0.5 * (bestLower + bestUpper);
    metrics.max_gap_Hz = bestGap;
    metrics.max_gap_lower_band = bestBand;
    metrics.max_gap_upper_band = bestBand + 1;
    metrics.max_gap_center_freq = center;
    if center ~= 0
        metrics.max_gap_rel = bestGap / center;
    end
end
end

function [kVals, freqVals] = read_tbl1_numeric(tbl1Path)
kVals = [];
freqVals = [];

fid = fopen(tbl1Path, 'r');
if fid < 0
    error('extract_stage2_harmonics_refine_gap_metrics_from_tbl1:OpenFailed', 'Failed to open: %s', tbl1Path);
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
