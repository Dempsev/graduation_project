function model = set_study_06(model)
% Study, solver, and job config based on mother.m format.

try
    model.study.create('std1');
catch
end
try
    model.study('std1').create('param', 'Parametric');
catch
end
try
    model.study('std1').create('eig', 'Eigenfrequency');
catch
end

% Parametric sweep (k and a1), all combinations
try
    model.study('std1').feature('param').set('pname', {'k' 'a1'});
    model.study('std1').feature('param').set('plistarr', {'range(0,3/(N-1),3)' 'range(0.15,0.05,0.30)'});
    model.study('std1').feature('param').set('punit', {'', ''});
    model.study('std1').feature('param').set('sweeptype', 'filled');
catch
end

% Eigenfrequency settings
try
    model.study('std1').feature('eig').set('geometricNonlinearity', true);
    model.study('std1').feature('eig').set('neigs', 12);
    model.study('std1').feature('eig').set('neigsactive', true);
    try
        model.study('std1').feature('eig').set('shift', '200[Hz]');
        model.study('std1').feature('eig').set('shiftactive', true);
    catch
    end
    model.study('std1').feature('eig').set('filtereigdescription', {'Damped' 'natural' 'frequency'});
catch
end

% Solver configuration (auto sequences may reset sol tags)
try
    model.study('std1').createAutoSequences('all');
catch
end
try
    model.study('std1').showAutoSequences('all');
catch
end
% Ensure sol1 exists
try
    model.sol('sol1');
catch
    model.sol.create('sol1');
end
model.sol('sol1').study('std1');

% Parametric solution (for plotting)
try
    model.sol('sol2');
catch
    model.sol.create('sol2');
end
model.sol('sol2').study('std1');

% Job configuration (batch)
try
    model.batch.create('p1', 'Parametric');
catch
end
try
    model.batch('p1').create('so1', 'Solutionseq');
catch
end
try
    model.batch('p1').study('std1');
catch
end
try
    % Job param sweep 1: specified combinations, k only
    model.batch('p1').set('pname', {'k'});
    model.batch('p1').set('plistarr', {'range(0,3/(N-1),3)'});
    model.batch('p1').set('punit', {''});
    model.batch('p1').set('sweeptype', 'spec');
    model.batch('p1').set('err', true);
catch
end
try
    model.batch('p1').feature('so1').set('seq', 'sol1');
    model.batch('p1').feature('so1').set('store', true);
    model.batch('p1').feature('so1').set('psol', 'sol2');
    model.batch('p1').feature('so1').set('keeprom', true);
catch
end
try
    model.batch('p1').attach('std1');
catch
end
try
    model.batch.create('p2', 'Parametric');
    model.batch('p2').create('so1', 'Solutionseq');
    model.batch('p2').study('std1');
    model.batch('p2').feature('so1').set('psol', 'sol2');
catch
end
try
    % Job param sweep 2: all combinations, k + a1
    model.batch('p2').set('pname', {'k' 'a1'});
    model.batch('p2').set('plistarr', {'range(0,3/(N-1),3)' 'range(0.15,0.05,0.30)'});
    model.batch('p2').set('punit', {'', ''});
    model.batch('p2').set('sweeptype', 'filled');
    model.batch('p2').set('err', true);
catch
end
try
    model.batch('p2').feature('so1').set('seq', 'sol1');
    model.batch('p2').feature('so1').set('store', true);
    model.batch('p2').feature('so1').set('psol', 'sol2');
    model.batch('p2').feature('so1').set('keeprom', true);
catch
end

apply_eigen_solver_settings(model, 'sol1');
apply_eigen_solver_settings(model, 'sol2');
end

function apply_eigen_solver_settings(model, solTag)
try
    sol = model.sol(solTag);
catch
    return;
end

try
    topTags = cell(sol.feature.tags);
catch
    return;
end

for i = 1:numel(topTags)
    apply_feature_settings_recursive(sol.feature(topTags{i}));
end
end

function apply_feature_settings_recursive(featureNode)
try
    featureNode.set('neigs', 12);
catch
end
try
    featureNode.set('shift', '200[Hz]');
catch
end
try
    featureNode.set('shiftactive', true);
catch
end

try
    childTags = cell(featureNode.feature.tags);
catch
    return;
end

for i = 1:numel(childTags)
    apply_feature_settings_recursive(featureNode.feature(childTags{i}));
end
end
