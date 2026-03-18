function doeTable = get_stage2_harmonics_refine_doe_points(cfg)
%GET_STAGE2_HARMONICS_REFINE_DOE_POINTS Build the lightweight harmonic DOE.
% Each main point gets 10 cases: center, b5 ladder, b3 ladder, a4 ladder,
% and three compact combinations.

rows = struct([]);
for i = 1:numel(cfg.mainPointSpecs)
    main = cfg.mainPointSpecs(i);
    base = struct( ...
        'main_id', string(main.main_id), ...
        'a1', main.a1, 'a2', main.a2, 'b2', main.b2, 'r0', main.r0, ...
        'a3', 0, 'b3', 0, 'a4', 0, 'b4', 0, 'a5', 0, 'b5', 0 ...
    );
    rows = append_row(rows, build_row(base, 'h00_center')); %#ok<AGROW>
    rows = append_row(rows, build_row(set_field(base, 'b5', cfg.b5Values(1)), 'h01_b5_001')); %#ok<AGROW>
    rows = append_row(rows, build_row(set_field(base, 'b5', cfg.b5Values(2)), 'h02_b5_002')); %#ok<AGROW>
    rows = append_row(rows, build_row(set_field(base, 'b5', cfg.b5Values(3)), 'h03_b5_003')); %#ok<AGROW>
    rows = append_row(rows, build_row(set_field(base, 'b3', cfg.b3Values(1)), 'h04_b3_002')); %#ok<AGROW>
    rows = append_row(rows, build_row(set_field(base, 'b3', cfg.b3Values(2)), 'h05_b3_004')); %#ok<AGROW>
    rows = append_row(rows, build_row(set_field(base, 'a4', cfg.a4Values(1)), 'h06_a4_0015')); %#ok<AGROW>
    rows = append_row(rows, build_row(set_field(base, 'a4', cfg.a4Values(2)), 'h07_a4_003')); %#ok<AGROW>
    rows = append_row(rows, build_row(apply_combo(base, struct('b5', cfg.b5Values(2), 'b3', cfg.b3Values(1))), 'h08_b5_002_b3_002')); %#ok<AGROW>
    rows = append_row(rows, build_row(apply_combo(base, struct('b5', cfg.b5Values(2), 'a4', cfg.a4Values(1))), 'h09_b5_002_a4_0015')); %#ok<AGROW>
    rows = append_row(rows, build_row(apply_combo(base, struct('b3', cfg.b3Values(1), 'a4', cfg.a4Values(1))), 'h10_b3_002_a4_0015')); %#ok<AGROW>
end

doeTable = struct2table(rows, 'AsArray', true);
doeTable = doeTable(:, cfg.doeFieldOrder);
writetable(doeTable, cfg.doeManifestCsv);
end

function out = set_field(base, fieldName, value)
out = base;
out.(fieldName) = value;
end

function out = apply_combo(base, values)
out = base;
fields = fieldnames(values);
for i = 1:numel(fields)
    fieldName = fields{i};
    out.(fieldName) = values.(fieldName);
end
end

function row = build_row(base, suffix)
row = struct( ...
    'main_id', string(base.main_id), ...
    'point_id', string(sprintf('%s_%s', char(string(base.main_id)), suffix)), ...
    'a1', base.a1, 'a2', base.a2, 'b2', base.b2, 'r0', base.r0, ...
    'a3', base.a3, 'b3', base.b3, 'a4', base.a4, 'b4', base.b4, 'a5', base.a5, 'b5', base.b5 ...
);
end

function rows = append_row(rows, row)
if isempty(rows)
    rows = row;
else
    rows(end + 1) = row;
end
end
