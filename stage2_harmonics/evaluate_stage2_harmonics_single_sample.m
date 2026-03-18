function result = evaluate_stage2_harmonics_single_sample(cfg, candidateRow, pointSpec, refPoint)
%EVALUATE_STAGE2_HARMONICS_SINGLE_SAMPLE Evaluate one shape on one harmonic point.

candidateId = char(string(candidateRow.candidate_id));
pointId = char(string(pointSpec.point_id));
sampleMeta = struct( ...
    'sample_id', string(sanitize_id([cfg.fourierId '__' candidateId '__' pointId])), ...
    'candidate_id', string(candidateRow.candidate_id), ...
    'shape_id', string(candidateRow.shape_id), ...
    'shape_family', string(candidateRow.shape_family), ...
    'candidate_role', string(candidateRow.candidate_role), ...
    'shape_file', string(candidateRow.shape_file) ...
);
result = evaluate_stage2_harmonics_case_internal(cfg, sampleMeta, pointSpec, refPoint);
end

function s = sanitize_id(s)
s = char(string(s));
s = regexprep(s, '[^a-zA-Z0-9_\-]', '_');
s = regexprep(s, '_+', '_');
s = regexprep(s, '^_+|_+$', '');
if isempty(s)
    s = 'stage2_harmonics_sample';
end
end
