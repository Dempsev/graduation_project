function write_stage2_summary_tables(resultsTable, cfg)
%WRITE_STAGE2_SUMMARY_TABLES Export stage-2 shape and point robustness summaries.

shapeSummary = build_shape_summary(resultsTable, cfg);
pointSummary = build_point_summary(resultsTable, cfg);

writetable(shapeSummary, cfg.shapeSummaryCsv);
writetable(pointSummary, cfg.pointSummaryCsv);
end

function shapeSummary = build_shape_summary(resultsTable, cfg)
if isempty(resultsTable)
    shapeSummary = empty_shape_summary();
    return;
end

candidateIds = unique(string(resultsTable.candidate_id), 'stable');
rows = repmat(make_shape_summary_row(), numel(candidateIds), 1);
for i = 1:numel(candidateIds)
    candidateId = candidateIds(i);
    sub = resultsTable(string(resultsTable.candidate_id) == candidateId, :);
    gapValues = sub.gap_gain_Hz(isfinite(sub.gap_gain_Hz));
    rows(i).candidate_id = candidateId;
    rows(i).shape_id = string(sub.shape_id(1));
    rows(i).candidate_role = string(sub.candidate_role(1));
    rows(i).shape_family = string(sub.shape_family(1));
    rows(i).points_total = height(sub);
    rows(i).points_solved = sum(sub.solve_success == true);
    rows(i).positive_gain_count = sum(isfinite(sub.gap_gain_Hz) & sub.gap_gain_Hz > cfg.positiveGapThresholdHz);
    if rows(i).points_total > 0
        rows(i).positive_gain_ratio = rows(i).positive_gain_count / rows(i).points_total;
    end
    if ~isempty(gapValues)
        rows(i).best_gap_gain_Hz = max(gapValues);
        rows(i).mean_gap_gain_Hz = mean(gapValues);
        rows(i).median_gap_gain_Hz = median(gapValues);
        rows(i).worst_gap_gain_Hz = min(gapValues);
    end
end

shapeSummary = struct2table(rows, 'AsArray', true);
shapeSummary = sortrows(shapeSummary, ...
    {'positive_gain_ratio', 'mean_gap_gain_Hz', 'best_gap_gain_Hz'}, ...
    {'descend', 'descend', 'descend'});
end

function pointSummary = build_point_summary(resultsTable, cfg)
if isempty(resultsTable)
    pointSummary = empty_point_summary();
    return;
end

pointIds = unique(string(resultsTable.point_id), 'stable');
rows = repmat(make_point_summary_row(), numel(pointIds), 1);
for i = 1:numel(pointIds)
    pointId = pointIds(i);
    sub = resultsTable(string(resultsTable.point_id) == pointId, :);
    gapValues = sub.gap_gain_Hz(isfinite(sub.gap_gain_Hz));
    rows(i).point_id = pointId;
    rows(i).a1 = double(sub.a1(1));
    rows(i).a2 = double(sub.a2(1));
    rows(i).b2 = double(sub.b2(1));
    rows(i).r0 = double(sub.r0(1));
    rows(i).shape_count = height(sub);
    rows(i).positive_gain_count = sum(isfinite(sub.gap_gain_Hz) & sub.gap_gain_Hz > cfg.positiveGapThresholdHz);
    if ~isempty(gapValues)
        rows(i).mean_gap_gain_Hz = mean(gapValues);
        rows(i).median_gap_gain_Hz = median(gapValues);
    end
end

pointSummary = struct2table(rows, 'AsArray', true);
pointSummary = sortrows(pointSummary, 'point_id', 'ascend');
end

function row = make_shape_summary_row()
row = struct( ...
    'candidate_id', string(""), ...
    'shape_id', string(""), ...
    'candidate_role', string(""), ...
    'shape_family', string(""), ...
    'points_total', 0, ...
    'points_solved', 0, ...
    'positive_gain_count', 0, ...
    'positive_gain_ratio', NaN, ...
    'best_gap_gain_Hz', NaN, ...
    'mean_gap_gain_Hz', NaN, ...
    'median_gap_gain_Hz', NaN, ...
    'worst_gap_gain_Hz', NaN ...
);
end

function row = make_point_summary_row()
row = struct( ...
    'point_id', string(""), ...
    'a1', NaN, ...
    'a2', NaN, ...
    'b2', NaN, ...
    'r0', NaN, ...
    'shape_count', 0, ...
    'positive_gain_count', 0, ...
    'mean_gap_gain_Hz', NaN, ...
    'median_gap_gain_Hz', NaN ...
);
end

function tableOut = empty_shape_summary()
prototype = make_shape_summary_row();
tableOut = struct2table(prototype, 'AsArray', true);
tableOut(1, :) = [];
end

function tableOut = empty_point_summary()
prototype = make_point_summary_row();
tableOut = struct2table(prototype, 'AsArray', true);
tableOut(1, :) = [];
end
