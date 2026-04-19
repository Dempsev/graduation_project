function write_stage2_gapdiversity_summary_tables(resultsTable, cfg)
%WRITE_STAGE2_GAPDIVERSITY_SUMMARY_TABLES Export exploration summaries by shape and by point.

shapeSummary = build_shape_summary(resultsTable, cfg);
pointSummary = build_point_summary(resultsTable, cfg);

writetable(shapeSummary, cfg.shapeSummaryCsv);
writetable(pointSummary, cfg.pointSummaryCsv);
end

function shapeSummary = build_shape_summary(resultsTable, cfg)
if isempty(resultsTable)
    shapeSummary = struct2table(make_shape_summary_row(), 'AsArray', true);
    shapeSummary(1, :) = [];
    return;
end

candidateIds = unique(string(resultsTable.candidate_id), 'stable');
rows = repmat(make_shape_summary_row(), numel(candidateIds), 1);
for i = 1:numel(candidateIds)
    candidateId = candidateIds(i);
    sub = resultsTable(string(resultsTable.candidate_id) == candidateId, :);
    gapValues = sub.gap_gain_Hz(isfinite(sub.gap_gain_Hz));
    pairText = pair_mode_string(sub);

    rows(i).candidate_id = candidateId;
    rows(i).shape_id = string(sub.shape_id(1));
    rows(i).candidate_role = string(sub.candidate_role(1));
    rows(i).shape_family = string(sub.shape_family(1));
    rows(i).points_total = height(sub);
    rows(i).points_guardrail_valid = sum(sub.guardrail_pass == true);
    rows(i).points_solved = sum(sub.solve_success == true);
    rows(i).positive_gain_count = sum(isfinite(sub.gap_gain_Hz) & sub.gap_gain_Hz > cfg.positiveGapThresholdHz);
    rows(i).dominant_gap_pair = pairText;
    if rows(i).points_total > 0
        rows(i).positive_gain_ratio = rows(i).positive_gain_count / rows(i).points_total;
    end
    if ~isempty(gapValues)
        rows(i).best_gap_gain_Hz = max(gapValues);
        rows(i).mean_gap_gain_Hz = mean(gapValues);
        rows(i).median_gap_gain_Hz = median(gapValues);
    end
end

shapeSummary = struct2table(rows, 'AsArray', true);
shapeSummary = sortrows(shapeSummary, {'positive_gain_ratio', 'mean_gap_gain_Hz', 'best_gap_gain_Hz'}, {'descend', 'descend', 'descend'});
end

function pointSummary = build_point_summary(resultsTable, cfg)
if isempty(resultsTable)
    pointSummary = struct2table(make_point_summary_row(), 'AsArray', true);
    pointSummary(1, :) = [];
    return;
end

pointIds = unique(string(resultsTable.point_id), 'stable');
rows = repmat(make_point_summary_row(), numel(pointIds), 1);
for i = 1:numel(pointIds)
    pointId = pointIds(i);
    sub = resultsTable(string(resultsTable.point_id) == pointId, :);
    gapValues = sub.gap_gain_Hz(isfinite(sub.gap_gain_Hz));
    pairText = pair_mode_string(sub);

    rows(i).point_id = pointId;
    for name = {'r0','A1','phi1','A2','phi2','A3','phi3','A4','phi4','A5','phi5','a1','b1','a2','b2','a3','b3','a4','b4','a5','b5','sumA','deriv_budget','min_radius_est','max_radius_est','max_abs_amp_slope'}
        key = char(name{1});
        rows(i).(key) = double(sub.(key)(1));
    end
    rows(i).shape_count = height(sub);
    rows(i).solved_count = sum(sub.solve_success == true);
    rows(i).positive_gain_count = sum(isfinite(sub.gap_gain_Hz) & sub.gap_gain_Hz > cfg.positiveGapThresholdHz);
    rows(i).dominant_gap_pair = pairText;
    if ~isempty(gapValues)
        rows(i).mean_gap_gain_Hz = mean(gapValues);
        rows(i).median_gap_gain_Hz = median(gapValues);
        rows(i).best_gap_gain_Hz = max(gapValues);
    end
end

pointSummary = struct2table(rows, 'AsArray', true);
pointSummary = sortrows(pointSummary, 'point_id', 'ascend');
end

function text = pair_mode_string(sub)
mask = isfinite(sub.gap_lower_band) & isfinite(sub.gap_upper_band);
if ~any(mask)
    text = "";
    return;
end
pairs = strcat(string(int32(sub.gap_lower_band(mask))), "-", string(int32(sub.gap_upper_band(mask))));
uniquePairs = unique(pairs, 'stable');
counts = zeros(numel(uniquePairs), 1);
for i = 1:numel(uniquePairs)
    counts(i) = sum(pairs == uniquePairs(i));
end
[bestCount, idx] = max(counts);
text = string(sprintf('%s (%d)', uniquePairs(idx), bestCount));
end

function row = make_shape_summary_row()
row = struct( ...
    'candidate_id', string(""), ...
    'shape_id', string(""), ...
    'candidate_role', string(""), ...
    'shape_family', string(""), ...
    'points_total', 0, ...
    'points_guardrail_valid', 0, ...
    'points_solved', 0, ...
    'positive_gain_count', 0, ...
    'positive_gain_ratio', NaN, ...
    'best_gap_gain_Hz', NaN, ...
    'mean_gap_gain_Hz', NaN, ...
    'median_gap_gain_Hz', NaN, ...
    'dominant_gap_pair', string("") ...
);
end

function row = make_point_summary_row()
row = struct( ...
    'point_id', string(""), ...
    'r0', NaN, ...
    'A1', NaN, 'phi1', NaN, ...
    'A2', NaN, 'phi2', NaN, ...
    'A3', NaN, 'phi3', NaN, ...
    'A4', NaN, 'phi4', NaN, ...
    'A5', NaN, 'phi5', NaN, ...
    'a1', NaN, 'b1', NaN, ...
    'a2', NaN, 'b2', NaN, ...
    'a3', NaN, 'b3', NaN, ...
    'a4', NaN, 'b4', NaN, ...
    'a5', NaN, 'b5', NaN, ...
    'sumA', NaN, ...
    'deriv_budget', NaN, ...
    'min_radius_est', NaN, ...
    'max_radius_est', NaN, ...
    'max_abs_amp_slope', NaN, ...
    'shape_count', 0, ...
    'solved_count', 0, ...
    'positive_gain_count', 0, ...
    'mean_gap_gain_Hz', NaN, ...
    'median_gap_gain_Hz', NaN, ...
    'best_gap_gain_Hz', NaN, ...
    'dominant_gap_pair', string("") ...
);
end
