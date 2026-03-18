function write_stage2_harmonics_refine_summary_tables(resultsTable, cfg)
%WRITE_STAGE2_HARMONICS_REFINE_SUMMARY_TABLES Export fixed-band refine summaries.

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
    gainValues = sub.gap34_gain_Hz(isfinite(sub.gap34_gain_Hz));
    rows(i).candidate_id = candidateId;
    rows(i).shape_id = string(sub.shape_id(1));
    rows(i).shape_role = string(sub.shape_role(1));
    rows(i).shape_family = string(sub.shape_family(1));
    rows(i).points_total = height(sub);
    rows(i).points_solved = sum(sub.solve_success == true);
    rows(i).positive_gain_count_34 = sum(isfinite(sub.gap34_gain_Hz) & sub.gap34_gain_Hz > cfg.positiveGapThresholdHz);
    if rows(i).points_total > 0
        rows(i).positive_gain_ratio_34 = rows(i).positive_gain_count_34 / rows(i).points_total;
    end
    if ~isempty(gainValues)
        rows(i).best_gap34_gain_Hz = max(gainValues);
        rows(i).mean_gap34_gain_Hz = mean(gainValues);
        rows(i).median_gap34_gain_Hz = median(gainValues);
        rows(i).worst_gap34_gain_Hz = min(gainValues);
    end
end
shapeSummary = struct2table(rows, 'AsArray', true);
shapeSummary = sortrows(shapeSummary, {'positive_gain_ratio_34','mean_gap34_gain_Hz','best_gap34_gain_Hz'}, {'descend','descend','descend'});
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
    gainValues = sub.gap34_gain_Hz(isfinite(sub.gap34_gain_Hz));
    rows(i).main_id = string(sub.main_id(1));
    rows(i).point_id = pointId;
    rows(i).a1 = double(sub.a1(1)); rows(i).a2 = double(sub.a2(1)); rows(i).b2 = double(sub.b2(1)); rows(i).r0 = double(sub.r0(1));
    rows(i).a3 = double(sub.a3(1)); rows(i).b3 = double(sub.b3(1)); rows(i).a4 = double(sub.a4(1)); rows(i).b4 = double(sub.b4(1)); rows(i).a5 = double(sub.a5(1)); rows(i).b5 = double(sub.b5(1));
    rows(i).shape_count = height(sub);
    rows(i).positive_gain_count_34 = sum(isfinite(sub.gap34_gain_Hz) & sub.gap34_gain_Hz > cfg.positiveGapThresholdHz);
    if rows(i).shape_count > 0
        rows(i).positive_gain_ratio_34 = rows(i).positive_gain_count_34 / rows(i).shape_count;
    end
    if ~isempty(gainValues)
        rows(i).mean_gap34_gain_Hz = mean(gainValues);
        rows(i).median_gap34_gain_Hz = median(gainValues);
    end
end
pointSummary = struct2table(rows, 'AsArray', true);
pointSummary = sortrows(pointSummary, {'positive_gain_ratio_34','mean_gap34_gain_Hz','median_gap34_gain_Hz'}, {'descend','descend','descend'});
end

function row = make_shape_summary_row()
row = struct('candidate_id',string(""),'shape_id',string(""),'shape_role',string(""),'shape_family',string(""), ...
    'points_total',0,'points_solved',0,'positive_gain_count_34',0,'positive_gain_ratio_34',NaN, ...
    'best_gap34_gain_Hz',NaN,'mean_gap34_gain_Hz',NaN,'median_gap34_gain_Hz',NaN,'worst_gap34_gain_Hz',NaN);
end

function row = make_point_summary_row()
row = struct('main_id',string(""),'point_id',string(""), ...
    'a1',NaN,'a2',NaN,'b2',NaN,'r0',NaN,'a3',NaN,'b3',NaN,'a4',NaN,'b4',NaN,'a5',NaN,'b5',NaN, ...
    'shape_count',0,'positive_gain_count_34',0,'positive_gain_ratio_34',NaN,'mean_gap34_gain_Hz',NaN,'median_gap34_gain_Hz',NaN);
end

function tableOut = empty_shape_summary()
prototype = make_shape_summary_row();
tableOut = struct2table(prototype, 'AsArray', true);
tableOut(1,:) = [];
end

function tableOut = empty_point_summary()
prototype = make_point_summary_row();
tableOut = struct2table(prototype, 'AsArray', true);
tableOut(1,:) = [];
end
