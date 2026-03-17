function assign_stage1_context(cfg, sampleId, shapeFile)
%ASSIGN_STAGE1_CONTEXT Push stage-1 overrides into MATLAB base workspace.

if nargin < 3
    shapeFile = '';
end

useDiscretePerturbation = ~isempty(shapeFile);
assignin('base', 'shape_file', char(shapeFile));
assignin('base', 'shape_export_name', char(sampleId));
assignin('base', 'fourier_param_overrides', cfg.paramOverrides);
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
