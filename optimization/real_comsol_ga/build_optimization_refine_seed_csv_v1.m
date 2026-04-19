function outCsv = build_optimization_refine_seed_csv_v1(baseSeedCsv, probeBestCandidatesCsv, survivorIds, outCsv)
%BUILD_OPTIMIZATION_REFINE_SEED_CSV_V1
% Build a refine-stage seed csv by replacing the original seed parameters with
% the best real probe candidate parameters for each survivor shape.
outCsv = build_optimization_stage_seed_csv_v1( ...
    baseSeedCsv, probeBestCandidatesCsv, survivorIds, outCsv);
end
