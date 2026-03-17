function candidateTable = generate_stage2_refine_candidate_manifest(cfg)
%GENERATE_STAGE2_REFINE_CANDIDATE_MANIFEST Pick the most robust stage-2 shapes.

if ~isfile(cfg.stage2ShapeSummaryCsv)
    error('generate_stage2_refine_candidate_manifest:MissingStage2Summary', ...
        'stage2 shape summary not found: %s', cfg.stage2ShapeSummaryCsv);
end

shapeSummary = readtable(cfg.stage2ShapeSummaryCsv);
if isempty(shapeSummary)
    error('generate_stage2_refine_candidate_manifest:EmptyStage2Summary', ...
        'stage2 shape summary is empty: %s', cfg.stage2ShapeSummaryCsv);
end

shapeSummary.shape_id = string(shapeSummary.shape_id);
shapeSummary.shape_family = string(shapeSummary.shape_family);
shapeSummary.candidate_role = string(shapeSummary.candidate_role);
shapeSummary.candidate_id = string(shapeSummary.candidate_id);
shapeSummary.shape_file = string(fullfile(cfg.shapeDir, strcat(shapeSummary.shape_id, ".csv")));

mask = shapeSummary.points_solved >= cfg.minSolvedPoints & ...
       shapeSummary.positive_gain_ratio >= cfg.minPositiveGainRatio & ...
       shapeSummary.mean_gap_gain_Hz >= cfg.minMeanGapGainHz & ...
       shapeSummary.candidate_role ~= "negative";
filtered = shapeSummary(mask, :);
if isempty(filtered)
    error('generate_stage2_refine_candidate_manifest:NoEligibleCandidates', ...
        'No stage2 candidates satisfy the refine thresholds.');
end

filtered = sortrows(filtered, ...
    {'positive_gain_ratio', 'mean_gap_gain_Hz', 'best_gap_gain_Hz'}, ...
    {'descend', 'descend', 'descend'});

selectedRows = struct([]);
selectedFamilies = strings(0, 1);
selectedShapeIds = strings(0, 1);
nextId = 1;

for pass = 1:2
    if numel(selectedRows) >= cfg.refineCandidateCount
        break;
    end
    for i = 1:height(filtered)
        row = table2struct(filtered(i, :));
        shapeId = string(row.shape_id);
        family = string(row.shape_family);
        if any(selectedShapeIds == shapeId)
            continue;
        end
        if cfg.refineFamilyDedup && pass == 1 && any(selectedFamilies == family)
            continue;
        end

        newRow = make_candidate_row(row, nextId, any(selectedFamilies == family));
        if isempty(selectedRows)
            selectedRows = newRow;
        else
            selectedRows(end + 1) = newRow; %#ok<AGROW>
        end
        selectedFamilies(end + 1, 1) = family; %#ok<AGROW>
        selectedShapeIds(end + 1, 1) = shapeId; %#ok<AGROW>
        nextId = nextId + 1;
        if numel(selectedRows) >= cfg.refineCandidateCount
            break;
        end
    end
end

if isempty(selectedRows)
    candidateTable = struct2table(make_empty_candidate_row(), 'AsArray', true);
    candidateTable(1, :) = [];
else
    candidateTable = struct2table(selectedRows, 'AsArray', true);
end
candidateTable = candidateTable(:, cfg.candidateManifestFieldOrder);
writetable(candidateTable, cfg.candidateManifestCsv);
end

function row = make_candidate_row(sourceRow, nextId, isDuplicateFamily)
row = struct( ...
    'candidate_id', string(sprintf('refine%02d', nextId)), ...
    'shape_id', string(sourceRow.shape_id), ...
    'shape_file', string(sourceRow.shape_file), ...
    'shape_family', string(sourceRow.shape_family), ...
    'candidate_role', string(sourceRow.candidate_role), ...
    'source_candidate_id', string(sourceRow.candidate_id), ...
    'source_positive_gain_ratio', double(sourceRow.positive_gain_ratio), ...
    'source_mean_gap_gain_Hz', double(sourceRow.mean_gap_gain_Hz), ...
    'source_best_gap_gain_Hz', double(sourceRow.best_gap_gain_Hz), ...
    'family_duplicate', logical(isDuplicateFamily) ...
);
end

function row = make_empty_candidate_row()
row = struct( ...
    'candidate_id', string(""), ...
    'shape_id', string(""), ...
    'shape_file', string(""), ...
    'shape_family', string(""), ...
    'candidate_role', string(""), ...
    'source_candidate_id', string(""), ...
    'source_positive_gain_ratio', NaN, ...
    'source_mean_gap_gain_Hz', NaN, ...
    'source_best_gap_gain_Hz', NaN, ...
    'family_duplicate', false ...
);
end
