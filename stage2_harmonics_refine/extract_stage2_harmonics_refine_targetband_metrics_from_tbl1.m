function metrics = extract_stage2_harmonics_refine_targetband_metrics_from_tbl1(tbl1Path, bandLowHz, bandHighHz)
%EXTRACT_STAGE2_HARMONICS_REFINE_TARGETBAND_METRICS_FROM_TBL1
% Compute the best-overlap gap metrics for an arbitrary target band.

metrics = struct( ...
    'target_band_low_Hz', double(bandLowHz), ...
    'target_band_high_Hz', double(bandHighHz), ...
    'target_gap_is_open', 0, ...
    'target_gap_overlap_Hz', 0, ...
    'target_gap_cover_ratio', 0, ...
    'target_gap_best_width_Hz', NaN, ...
    'target_gap_lower_edge_Hz', NaN, ...
    'target_gap_upper_edge_Hz', NaN, ...
    'target_gap_center_freq', NaN, ...
    'target_gap_lower_band', NaN, ...
    'target_gap_upper_band', NaN ...
);

if nargin < 3
    error('extract_stage2_harmonics_refine_targetband_metrics_from_tbl1:MissingBand', ...
        'bandLowHz and bandHighHz are required.');
end
if ~isfile(tbl1Path)
    return;
end

[kVals, freqVals] = read_tbl1_numeric(tbl1Path);
if isempty(kVals)
    return;
end

[uniqueK, ~, kIdx] = unique(kVals, 'sorted');
bandsByK = cell(numel(uniqueK), 1);
maxBands = 0;
for i = 1:numel(uniqueK)
    freq = sort(freqVals(kIdx == i), 'ascend');
    bandsByK{i} = freq(:);
    maxBands = max(maxBands, numel(freq));
end

bestOverlap = 0.0;
bestWidth = -inf;
bestLower = NaN;
bestUpper = NaN;
bestLowerBand = NaN;
bestUpperBand = NaN;

for bandIdx = 1:(maxBands - 1)
    lowerVals = [];
    upperVals = [];
    for i = 1:numel(bandsByK)
        bands = bandsByK{i};
        if numel(bands) > bandIdx
            lowerVals(end + 1, 1) = bands(bandIdx); %#ok<AGROW>
            upperVals(end + 1, 1) = bands(bandIdx + 1); %#ok<AGROW>
        end
    end
    if isempty(lowerVals) || isempty(upperVals)
        continue;
    end

    lowerEdge = max(lowerVals);
    upperEdge = min(upperVals);
    gapWidth = upperEdge - lowerEdge;
    if ~isfinite(gapWidth) || gapWidth <= 0
        continue;
    end

    overlap = max(0.0, min(upperEdge, bandHighHz) - max(lowerEdge, bandLowHz));
    if overlap > bestOverlap + 1e-12 || (abs(overlap - bestOverlap) <= 1e-12 && gapWidth > bestWidth)
        bestOverlap = overlap;
        bestWidth = gapWidth;
        bestLower = lowerEdge;
        bestUpper = upperEdge;
        bestLowerBand = bandIdx;
        bestUpperBand = bandIdx + 1;
    end
end

if bestOverlap <= 0
    return;
end

metrics.target_gap_is_open = 1;
metrics.target_gap_overlap_Hz = bestOverlap;
metrics.target_gap_cover_ratio = bestOverlap / max(1e-12, bandHighHz - bandLowHz);
metrics.target_gap_best_width_Hz = bestWidth;
metrics.target_gap_lower_edge_Hz = bestLower;
metrics.target_gap_upper_edge_Hz = bestUpper;
metrics.target_gap_center_freq = 0.5 * (bestLower + bestUpper);
metrics.target_gap_lower_band = bestLowerBand;
metrics.target_gap_upper_band = bestUpperBand;
end

function [kVals, freqVals] = read_tbl1_numeric(tbl1Path)
kVals = [];
freqVals = [];

fid = fopen(tbl1Path, 'r');
if fid < 0
    error('extract_stage2_harmonics_refine_targetband_metrics_from_tbl1:OpenFailed', ...
        'Failed to open: %s', tbl1Path);
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
    kVal = str2double(parts{1});
    freqVal = parse_real_scalar(parts{end});
    if ~isfinite(kVal) || ~isfinite(freqVal)
        continue;
    end
    kVals(end + 1, 1) = kVal; %#ok<AGROW>
    freqVals(end + 1, 1) = freqVal; %#ok<AGROW>
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
