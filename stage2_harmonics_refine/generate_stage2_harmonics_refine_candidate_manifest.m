function candidateTable = generate_stage2_harmonics_refine_candidate_manifest(cfg)
%GENERATE_STAGE2_HARMONICS_REFINE_CANDIDATE_MANIFEST Build the lightweight shape set.

if ~isfile(cfg.stage2HarmonicsShapeSummaryCsv)
    error('generate_stage2_harmonics_refine_candidate_manifest:MissingShapeSummary', ...
        'stage2_harmonics shape summary not found: %s', cfg.stage2HarmonicsShapeSummaryCsv);
end
if ~isfile(cfg.stage2HarmonicsCandidateManifestCsv)
    error('generate_stage2_harmonics_refine_candidate_manifest:MissingCandidateManifest', ...
        'stage2_harmonics candidate manifest not found: %s', cfg.stage2HarmonicsCandidateManifestCsv);
end

shapeSummary = readtable(cfg.stage2HarmonicsShapeSummaryCsv);
sourceManifest = readtable(cfg.stage2HarmonicsCandidateManifestCsv);
shapeSummary.shape_id = string(shapeSummary.shape_id);
shapeSummary.shape_family = string(shapeSummary.shape_family);
shapeSummary.candidate_id = string(shapeSummary.candidate_id);
sourceManifest.shape_id = string(sourceManifest.shape_id);
sourceManifest.candidate_id = string(sourceManifest.candidate_id);

rows = struct([]);
nextId = 1;
for i = 1:numel(cfg.mainlineShapeIds)
    shapeId = string(cfg.mainlineShapeIds{i});
    rows = append_candidate(rows, shapeId, "mainline", cfg.mainlineMainIds, nextId, shapeSummary, sourceManifest, cfg); %#ok<AGROW>
    nextId = nextId + 1;
end
for i = 1:numel(cfg.specialCaseShapeIds)
    shapeId = string(cfg.specialCaseShapeIds{i});
    rows = append_candidate(rows, shapeId, "special_case", cfg.specialCaseMainIds, nextId, shapeSummary, sourceManifest, cfg); %#ok<AGROW>
    nextId = nextId + 1;
end

candidateTable = struct2table(rows, 'AsArray', true);
candidateTable = candidateTable(:, cfg.candidateManifestFieldOrder);
writetable(candidateTable, cfg.candidateManifestCsv);
end

function rows = append_candidate(rows, shapeId, shapeRole, mainIds, nextId, shapeSummary, sourceManifest, cfg)
summaryMask = shapeSummary.shape_id == shapeId;
if ~any(summaryMask)
    error('generate_stage2_harmonics_refine_candidate_manifest:MissingShape', ...
        'Requested shape %s not found in %s', shapeId, cfg.stage2HarmonicsShapeSummaryCsv);
end
manifestMask = sourceManifest.shape_id == shapeId;
if ~any(manifestMask)
    error('generate_stage2_harmonics_refine_candidate_manifest:MissingSourceCandidate', ...
        'Requested shape %s not found in %s', shapeId, cfg.stage2HarmonicsCandidateManifestCsv);
end
summaryRow = table2struct(shapeSummary(find(summaryMask, 1, 'first'), :));
manifestRow = table2struct(sourceManifest(find(manifestMask, 1, 'first'), :));
row = struct( ...
    'candidate_id', string(sprintf('href%02d', nextId)), ...
    'shape_id', string(shapeId), ...
    'shape_file', string(fullfile(cfg.shapeDir, sprintf('%s.csv', char(shapeId)))), ...
    'shape_family', string(summaryRow.shape_family), ...
    'shape_role', string(shapeRole), ...
    'allowed_main_ids', string(strjoin(string(mainIds), ',')), ...
    'source_candidate_id', string(manifestRow.candidate_id), ...
    'source_positive_gain_ratio', double(summaryRow.positive_gain_ratio), ...
    'source_mean_gap_gain_Hz', double(summaryRow.mean_gap_gain_Hz), ...
    'source_best_gap_gain_Hz', double(summaryRow.best_gap_gain_Hz) ...
);
if isempty(rows)
    rows = row;
else
    rows(end + 1) = row;
end
end

