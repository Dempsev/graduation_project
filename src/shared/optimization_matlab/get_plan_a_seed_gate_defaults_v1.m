function gate = get_plan_a_seed_gate_defaults_v1()
%GET_PLAN_A_SEED_GATE_DEFAULTS_V1 Shared default thresholds for A->real-GA seed gating.

gate = struct();
gate.topKSeeds = 3;
gate.minMeanGainHz = 1.0;
gate.minPositiveRate = 1.0;
gate.minSolveSuccessCount = 2;
end
