function assign_stage2_harmonics_context(cfg, pointSpec, sampleId, shapeFile)
%ASSIGN_STAGE2_HARMONICS_CONTEXT Push harmonic-screen overrides into base workspace.

if nargin < 4
    shapeFile = '';
end

paramOverrides = cfg.baseParamOverrides;
paramOverrides.a1 = pointSpec.a1;
paramOverrides.a2 = pointSpec.a2;
paramOverrides.b2 = pointSpec.b2;
paramOverrides.r0 = sprintf('%.12g[m]', pointSpec.r0);
paramOverrides.a3 = pointSpec.a3;
paramOverrides.b3 = pointSpec.b3;
paramOverrides.a4 = pointSpec.a4;
paramOverrides.b4 = pointSpec.b4;
paramOverrides.a5 = pointSpec.a5;
paramOverrides.b5 = pointSpec.b5;

useDiscretePerturbation = ~isempty(shapeFile);
assignin('base', 'shape_file', char(shapeFile));
assignin('base', 'shape_export_name', char(sampleId));
assignin('base', 'fourier_param_overrides', paramOverrides);
assignin('base', 'use_discrete_perturbation', useDiscretePerturbation);
assignin('base', 'study_pname', cfg.studyPName);
assignin('base', 'study_plistarr', cfg.studyPListArr);
assignin('base', 'study_punit', cfg.studyPUnit);
assignin('base', 'study_sweeptype', cfg.studySweepType);
assignin('base', 'study_neigs', cfg.studyNeigs);
assignin('base', 'study_shift', cfg.studyShiftExpr);
assignin('base', 'shape_skip', false);
assignin('base', 'shape_skip_reason', '');
assignin('base', 'shape_skip_file', '');
end
