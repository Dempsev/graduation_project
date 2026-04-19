function assign_stage2_gapdiversity_context(cfg, pointSpec, sampleId, shapeFile)
%ASSIGN_STAGE2_GAPDIVERSITY_CONTEXT Push exploration overrides into MATLAB base workspace.

if nargin < 4
    shapeFile = '';
end

paramOverrides = cfg.baseParamOverrides;
paramOverrides.r0 = sprintf('%.12g[m]', pointSpec.r0);
for k = 1:5
    paramOverrides.(sprintf('a%d', k)) = pointSpec.(sprintf('a%d', k));
    paramOverrides.(sprintf('b%d', k)) = pointSpec.(sprintf('b%d', k));
end

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
