function candidateTable = generate_stage2_candidate_manifest(cfg)
%GENERATE_STAGE2_CANDIDATE_MANIFEST Pick representative stage-2 candidates.
% The manifest is rebuilt from the current stage-1 summary so stage-2 always
% reflects the latest full screening results.

if ~isfile(cfg.stage1SummaryCsv)
    error('generate_stage2_candidate_manifest:MissingStage1Summary', ...
        'stage1 summary not found: %s', cfg.stage1SummaryCsv);
end

summary = readtable(cfg.stage1SummaryCsv);
if isempty(summary)
    error('generate_stage2_candidate_manifest:EmptyStage1Summary', ...
        'stage1 summary is empty: %s', cfg.stage1SummaryCsv);
end

shapeIds = string(summary.shape_id);
gapGain = double(summary.gap_gain_Hz);
gapTarget = double(summary.gap_target_Hz);
tiers = string(summary.candidate_tier);
families = strings(height(summary), 1);
for i = 1:height(summary)
    families(i) = extract_shape_family(shapeIds(i), cfg.familyPattern);
end
summary.shape_id = shapeIds;
summary.candidate_tier = tiers;
summary.shape_family = families;
summary.gap_gain_Hz = gapGain;
summary.gap_target_Hz = gapTarget;

selectedRows = struct([]);
selectedFamilies = strings(0, 1);
nextId = 1;

[selectedRows, selectedFamilies, nextId] = select_role_rows( ...
    summary, 'strong_positive', cfg.candidateRoleCounts.strong_positive, ...
    selectedRows, selectedFamilies, nextId, cfg, 'descend');
[selectedRows, selectedFamilies, nextId] = select_role_rows( ...
    summary, 'weak_positive', cfg.candidateRoleCounts.weak_positive, ...
    selectedRows, selectedFamilies, nextId, cfg, 'descend');
negativeSort = 'descend';
if strcmpi(cfg.negativeSelectionMode, 'most_negative')
    negativeSort = 'ascend';
end
[selectedRows, selectedFamilies, nextId] = select_role_rows( ...
    summary, 'negative', cfg.candidateRoleCounts.negative, ...
    selectedRows, selectedFamilies, nextId, cfg, negativeSort);

if isempty(selectedRows)
    candidateTable = struct2table(make_empty_candidate_row(), 'AsArray', true);
    candidateTable(1, :) = [];
else
    candidateTable = struct2table(selectedRows, 'AsArray', true);
end
candidateTable = candidateTable(:, cfg.candidateManifestFieldOrder);
writetable(candidateTable, cfg.candidateManifestCsv);
end

function [selectedRows, selectedFamilies, nextId] = select_role_rows(summary, roleName, countNeeded, selectedRows, selectedFamilies, nextId, cfg, sortDir)
roleMask = summary.candidate_tier == string(roleName);
roleTable = summary(roleMask, :);
if isempty(roleTable)
    return;
end

if strcmpi(sortDir, 'ascend')
    roleTable = sortrows(roleTable, {'gap_gain_Hz', 'gap_target_Hz'}, {'ascend', 'ascend'});
else
    roleTable = sortrows(roleTable, {'gap_gain_Hz', 'gap_target_Hz'}, {'descend', 'descend'});
end

selectedShapeIds = strings(0, 1);
if ~isempty(selectedRows)
    selectedShapeIds = string({selectedRows.shape_id})';
end
roleRows = table2struct(roleTable);
added = 0;

for pass = 1:2
    if added >= countNeeded
        break;
    end
    for i = 1:numel(roleRows)
        row = roleRows(i);
        shapeId = string(row.shape_id);
        family = string(row.shape_family);
        if any(selectedShapeIds == shapeId)
            continue;
        end
        if pass == 1 && any(selectedFamilies == family)
            continue;
        end

        newRow = make_candidate_row(row, roleName, nextId, cfg, any(selectedFamilies == family));
        if isempty(selectedRows)
            selectedRows = newRow;
        else
            selectedRows(end + 1) = newRow; %#ok<AGROW>
        end
        selectedFamilies(end + 1, 1) = family; %#ok<AGROW>
        selectedShapeIds(end + 1, 1) = shapeId; %#ok<AGROW>
        nextId = nextId + 1;
        added = added + 1;
        if added >= countNeeded
            break;
        end
    end
end
end

function row = make_candidate_row(sourceRow, roleName, nextId, cfg, isDuplicateFamily)
shapeId = string(sourceRow.shape_id);
row = struct( ...
    'candidate_id', string(sprintf('cand%02d', nextId)), ...
    'shape_id', shapeId, ...
    'shape_file', string(fullfile(cfg.shapeDir, sprintf('%s.csv', char(shapeId)))), ...
    'shape_family', string(sourceRow.shape_family), ...
    'candidate_role', string(roleName), ...
    'stage1_gap_gain_Hz', double(sourceRow.gap_gain_Hz), ...
    'stage1_gap_target_Hz', double(sourceRow.gap_target_Hz), ...
    'stage1_candidate_tier', string(sourceRow.candidate_tier), ...
    'family_duplicate', logical(isDuplicateFamily) ...
);
end

function family = extract_shape_family(shapeId, familyPattern)
shapeId = char(string(shapeId));
tokens = regexp(shapeId, familyPattern, 'tokens', 'once');
if isempty(tokens)
    family = string(shapeId);
else
    family = string(tokens{1});
end
end

function row = make_empty_candidate_row()
row = struct( ...
    'candidate_id', string(""), ...
    'shape_id', string(""), ...
    'shape_file', string(""), ...
    'shape_family', string(""), ...
    'candidate_role', string(""), ...
    'stage1_gap_gain_Hz', NaN, ...
    'stage1_gap_target_Hz', NaN, ...
    'stage1_candidate_tier', string(""), ...
    'family_duplicate', false ...
);
end

