function seedIds = select_plan_a_validated_seed_ids_v1(shapeSummaryCsv, topK, minMeanGainHz, minPositiveRate, minSolveSuccessCount)
%SELECT_PLAN_A_VALIDATED_SEED_IDS_V1 Choose real-validated seeds from plan A.

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(fileparts(thisDir));
sharedOptDir = fullfile(rootDir, 'shared', 'optimization_matlab');
if exist(sharedOptDir, 'dir')
    addpath(sharedOptDir);
end

gate = get_plan_a_seed_gate_defaults_v1();
if nargin >= 2 && ~isempty(topK)
    gate.topKSeeds = topK;
end
if nargin >= 3 && ~isempty(minMeanGainHz)
    gate.minMeanGainHz = minMeanGainHz;
end
if nargin >= 4 && ~isempty(minPositiveRate)
    gate.minPositiveRate = minPositiveRate;
end
if nargin >= 5 && ~isempty(minSolveSuccessCount)
    gate.minSolveSuccessCount = minSolveSuccessCount;
end

seedIds = select_seed_ids_from_shape_summary_v1(shapeSummaryCsv, gate);
end
