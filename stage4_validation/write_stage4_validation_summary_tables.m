function write_stage4_validation_summary_tables(resultsTable, cfg)
%WRITE_STAGE4_VALIDATION_SUMMARY_TABLES Export A/B validation summaries.

armSummary = build_arm_summary(resultsTable, cfg);
pointSummary = build_point_summary(resultsTable, cfg);
shapeSummary = build_shape_summary(resultsTable, cfg);

writetable(armSummary, cfg.armSummaryCsv);
writetable(pointSummary, cfg.pointSummaryCsv);
writetable(shapeSummary, cfg.shapeSummaryCsv);
end

function armSummary = build_arm_summary(resultsTable, cfg)
if isempty(resultsTable)
    armSummary = empty_arm_summary();
    return;
end
keys = strcat(string(resultsTable.selection_source), "||", string(resultsTable.selection_label));
uniqueKeys = unique(keys, 'stable');
rows = repmat(make_arm_row(), numel(uniqueKeys), 1);
for i = 1:numel(uniqueKeys)
    sub = resultsTable(keys == uniqueKeys(i), :);
    gainValues = sub.gap34_gain_Hz(isfinite(sub.gap34_gain_Hz));
    rows(i).selection_source = string(sub.selection_source(1));
    rows(i).selection_label = string(sub.selection_label(1));
    rows(i).rows_total = height(sub);
    rows(i).geometry_invalid_count = sum(sub.geometry_valid == false);
    rows(i).no_contact_count = sum(sub.geometry_valid == true & sub.contact_valid == false);
    rows(i).solve_success_count = sum(sub.solve_success == true);
    rows(i).positive_gap34_gain_count = sum(isfinite(sub.gap34_gain_Hz) & sub.gap34_gain_Hz > cfg.positiveGapThresholdHz);
    if rows(i).rows_total > 0
        rows(i).positive_gap34_gain_rate = rows(i).positive_gap34_gain_count / rows(i).rows_total;
    end
    if ~isempty(gainValues)
        rows(i).mean_gap34_gain_Hz = mean(gainValues);
        rows(i).median_gap34_gain_Hz = median(gainValues);
        rows(i).best_gap34_gain_Hz = max(gainValues);
    end
end
armSummary = struct2table(rows, 'AsArray', true);
armSummary = sortrows(armSummary, {'positive_gap34_gain_rate', 'mean_gap34_gain_Hz'}, {'descend', 'descend'});
end

function pointSummary = build_point_summary(resultsTable, cfg)
if isempty(resultsTable)
    pointSummary = empty_point_summary();
    return;
end
keys = strcat(string(resultsTable.main_id), "||", string(resultsTable.point_id));
uniqueKeys = unique(keys, 'stable');
rows = repmat(make_point_row(), numel(uniqueKeys), 1);
for i = 1:numel(uniqueKeys)
    sub = resultsTable(keys == uniqueKeys(i), :);
    gainValues = sub.gap34_gain_Hz(isfinite(sub.gap34_gain_Hz));
    rows(i).main_id = string(sub.main_id(1));
    rows(i).point_id = string(sub.point_id(1));
    rows(i).a1 = double(sub.a1(1));
    rows(i).a2 = double(sub.a2(1));
    rows(i).b2 = double(sub.b2(1));
    rows(i).r0 = double(sub.r0(1));
    rows(i).a3 = double(sub.a3(1));
    rows(i).b3 = double(sub.b3(1));
    rows(i).a4 = double(sub.a4(1));
    rows(i).b4 = double(sub.b4(1));
    rows(i).a5 = double(sub.a5(1));
    rows(i).b5 = double(sub.b5(1));
    rows(i).rows_total = height(sub);
    rows(i).solve_success_count = sum(sub.solve_success == true);
    rows(i).positive_gap34_gain_count = sum(isfinite(sub.gap34_gain_Hz) & sub.gap34_gain_Hz > cfg.positiveGapThresholdHz);
    if rows(i).rows_total > 0
        rows(i).positive_gap34_gain_rate = rows(i).positive_gap34_gain_count / rows(i).rows_total;
    end
    if ~isempty(gainValues)
        rows(i).mean_gap34_gain_Hz = mean(gainValues);
        rows(i).median_gap34_gain_Hz = median(gainValues);
        rows(i).best_gap34_gain_Hz = max(gainValues);
    end
end
pointSummary = struct2table(rows, 'AsArray', true);
pointSummary = sortrows(pointSummary, {'positive_gap34_gain_rate', 'mean_gap34_gain_Hz'}, {'descend', 'descend'});
end

function shapeSummary = build_shape_summary(resultsTable, cfg)
if isempty(resultsTable)
    shapeSummary = empty_shape_summary();
    return;
end
keys = strcat(string(resultsTable.shape_id), "||", string(resultsTable.selection_source));
uniqueKeys = unique(keys, 'stable');
rows = repmat(make_shape_row(), numel(uniqueKeys), 1);
for i = 1:numel(uniqueKeys)
    sub = resultsTable(keys == uniqueKeys(i), :);
    gainValues = sub.gap34_gain_Hz(isfinite(sub.gap34_gain_Hz));
    rows(i).shape_id = string(sub.shape_id(1));
    rows(i).shape_family = string(sub.shape_family(1));
    rows(i).shape_role = string(sub.shape_role(1));
    rows(i).selection_source = string(sub.selection_source(1));
    rows(i).rows_total = height(sub);
    rows(i).solve_success_count = sum(sub.solve_success == true);
    rows(i).positive_gap34_gain_count = sum(isfinite(sub.gap34_gain_Hz) & sub.gap34_gain_Hz > cfg.positiveGapThresholdHz);
    if rows(i).rows_total > 0
        rows(i).positive_gap34_gain_rate = rows(i).positive_gap34_gain_count / rows(i).rows_total;
    end
    if ~isempty(gainValues)
        rows(i).mean_gap34_gain_Hz = mean(gainValues);
        rows(i).median_gap34_gain_Hz = median(gainValues);
        rows(i).best_gap34_gain_Hz = max(gainValues);
    end
end
shapeSummary = struct2table(rows, 'AsArray', true);
shapeSummary = sortrows(shapeSummary, {'selection_source', 'positive_gap34_gain_rate', 'mean_gap34_gain_Hz'}, {'ascend', 'descend', 'descend'});
end

function row = make_arm_row()
row = struct( ...
    'selection_source', string(""), ...
    'selection_label', string(""), ...
    'rows_total', 0, ...
    'geometry_invalid_count', 0, ...
    'no_contact_count', 0, ...
    'solve_success_count', 0, ...
    'positive_gap34_gain_count', 0, ...
    'positive_gap34_gain_rate', NaN, ...
    'mean_gap34_gain_Hz', NaN, ...
    'median_gap34_gain_Hz', NaN, ...
    'best_gap34_gain_Hz', NaN ...
);
end

function row = make_point_row()
row = struct( ...
    'main_id', string(""), 'point_id', string(""), ...
    'a1', NaN, 'a2', NaN, 'b2', NaN, 'r0', NaN, ...
    'a3', NaN, 'b3', NaN, 'a4', NaN, 'b4', NaN, 'a5', NaN, 'b5', NaN, ...
    'rows_total', 0, 'solve_success_count', 0, ...
    'positive_gap34_gain_count', 0, 'positive_gap34_gain_rate', NaN, ...
    'mean_gap34_gain_Hz', NaN, 'median_gap34_gain_Hz', NaN, 'best_gap34_gain_Hz', NaN ...
);
end

function row = make_shape_row()
row = struct( ...
    'shape_id', string(""), 'shape_family', string(""), 'shape_role', string(""), 'selection_source', string(""), ...
    'rows_total', 0, 'solve_success_count', 0, ...
    'positive_gap34_gain_count', 0, 'positive_gap34_gain_rate', NaN, ...
    'mean_gap34_gain_Hz', NaN, 'median_gap34_gain_Hz', NaN, 'best_gap34_gain_Hz', NaN ...
);
end

function tableOut = empty_arm_summary()
prototype = make_arm_row();
tableOut = struct2table(prototype, 'AsArray', true);
tableOut(1, :) = [];
end

function tableOut = empty_point_summary()
prototype = make_point_row();
tableOut = struct2table(prototype, 'AsArray', true);
tableOut(1, :) = [];
end

function tableOut = empty_shape_summary()
prototype = make_shape_row();
tableOut = struct2table(prototype, 'AsArray', true);
tableOut(1, :) = [];
end
