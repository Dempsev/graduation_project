function candidateTable = generate_stage2_harmonics_candidate_manifest(cfg)
%GENERATE_STAGE2_HARMONICS_CANDIDATE_MANIFEST Pick the strongest refined shapes.

if ~isfile(cfg.refineShapeSummaryCsv)
    error('generate_stage2_harmonics_candidate_manifest:MissingRefineSummary', ...
        'stage2_refine shape summary not found: %s', cfg.refineShapeSummaryCsv);
end

shapeSummary = readtable(cfg.refineShapeSummaryCsv);
if isempty(shapeSummary)
    error('generate_stage2_harmonics_candidate_manifest:EmptyRefineSummary', ...
        'stage2_refine shape summary is empty: %s', cfg.refineShapeSummaryCsv);
end

shapeSummary.shape_id = string(shapeSummary.shape_id);
shapeSummary.shape_family = string(shapeSummary.shape_family);
shapeSummary.candidate_role = string(shapeSummary.candidate_role);
shapeSummary.candidate_id = string(shapeSummary.candidate_id);
shapeSummary.shape_file = string(fullfile(cfg.shapeDir, strcat(shapeSummary.shape_id, ".csv")));

mask = shapeSummary.points_solved >= cfg.minSolvedPoints & ...
       shapeSummary.positive_gain_ratio >= cfg.minPositiveGainRatio & ...
       shapeSummary.mean_gap_gain_Hz >= cfg.minMeanGapGainHz;
filtered = shapeSummary(mask, :);
if isempty(filtered)
    error('generate_stage2_harmonics_candidate_manifest:NoEligibleCandidates', ...
        'No stage2_refine candidates satisfy the harmonic thresholds.');
end

filtered = sortrows(filtered, ...
    {'positive_gain_ratio', 'mean_gap_gain_Hz', 'best_gap_gain_Hz'}, ...
    {'descend', 'descend', 'descend'});

selectedRows = struct([]);
selectedFamilies = strings(0, 1);
selectedShapeIds = strings(0, 1);
nextId = 1;

for pass = 1:2
    if numel(selectedRows) >= cfg.harmonicCandidateCount
        break;
    end
    for i = 1:height(filtered)
        row = table2struct(filtered(i, :));
        shapeId = string(row.shape_id);
        family = string(row.shape_family);
        if any(selectedShapeIds == shapeId)
            continue;
        end
        if pass == 1 && any(selectedFamilies == family)
            continue;
        end

        newRow = make_candidate_row(row, nextId);
        if isempty(selectedRows)
            selectedRows = newRow;
        else
            selectedRows(end + 1) = newRow; %#ok<AGROW>
        end
        selectedFamilies(end + 1, 1) = family; %#ok<AGROW>
        selectedShapeIds(end + 1, 1) = shapeId; %#ok<AGROW>
        nextId = nextId + 1;
        if numel(selectedRows) >= cfg.harmonicCandidateCount
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

function row = make_candidate_row(sourceRow, nextId)
row = struct( ...
    'candidate_id', string(sprintf('harm%02d', nextId)), ...
    'shape_id', string(sourceRow.shape_id), ...
    'shape_file', string(sourceRow.shape_file), ...
    'shape_family', string(sourceRow.shape_family), ...
    'candidate_role', string(sourceRow.candidate_role), ...
    'source_refine_candidate_id', string(sourceRow.candidate_id), ...
    'source_positive_gain_ratio', double(sourceRow.positive_gain_ratio), ...
    'source_mean_gap_gain_Hz', double(sourceRow.mean_gap_gain_Hz), ...
    'source_best_gap_gain_Hz', double(sourceRow.best_gap_gain_Hz) ...
);
end

function row = make_empty_candidate_row()
row = struct( ...
    'candidate_id', string(""), ...
    'shape_id', string(""), ...
    'shape_file', string(""), ...
    'shape_family', string(""), ...
    'candidate_role', string(""), ...
    'source_refine_candidate_id', string(""), ...
    'source_positive_gain_ratio', NaN, ...
    'source_mean_gap_gain_Hz', NaN, ...
    'source_best_gap_gain_Hz', NaN ...
);
end
