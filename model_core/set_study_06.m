function model = set_study_06(model)
% Study, solver, and job config based on mother.m format.

[sweepPName, sweepPListArr, sweepPUnit, sweepType] = resolve_param_sweep();
[eigenNeigs, eigenShift] = resolve_eigen_settings();

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
    model.study('std1').feature('param').set('pname', sweepPName);
    model.study('std1').feature('param').set('plistarr', sweepPListArr);
    model.study('std1').feature('param').set('punit', sweepPUnit);
    model.study('std1').feature('param').set('sweeptype', sweepType);
catch
end

% Eigenfrequency settings
try
    model.study('std1').feature('eig').set('geometricNonlinearity', true);
    model.study('std1').feature('eig').set('neigs', eigenNeigs);
    model.study('std1').feature('eig').set('neigsactive', true);
    try
        model.study('std1').feature('eig').set('shift', eigenShift);
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
    model.batch('p2').set('pname', sweepPName);
    model.batch('p2').set('plistarr', sweepPListArr);
    model.batch('p2').set('punit', sweepPUnit);
    model.batch('p2').set('sweeptype', sweepType);
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

apply_eigen_solver_settings(model, 'sol1', eigenNeigs, eigenShift);
apply_eigen_solver_settings(model, 'sol2', eigenNeigs, eigenShift);
end

function apply_eigen_solver_settings(model, solTag, eigenNeigs, eigenShift)
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
    apply_feature_settings_recursive(sol.feature(topTags{i}), eigenNeigs, eigenShift);
end
end

function apply_feature_settings_recursive(featureNode, eigenNeigs, eigenShift)
try
    featureNode.set('neigs', eigenNeigs);
catch
end
try
    featureNode.set('shift', eigenShift);
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
    apply_feature_settings_recursive(featureNode.feature(childTags{i}), eigenNeigs, eigenShift);
end
end

function [pname, plistarr, punit, sweeptype] = resolve_param_sweep()
% Allow runners to override the study sweep without changing the default path.
pname = {'k', 'a1'};
plistarr = {'range(0,3/(N-1),3)', 'range(0.15,0.05,0.30)'};
punit = {'', ''};
sweeptype = 'filled';

try
    if evalin('base', 'exist(''study_pname'',''var'')')
        candidate = evalin('base', 'study_pname');
        pname = normalize_cellstr(candidate);
    end
catch
end

try
    if evalin('base', 'exist(''study_plistarr'',''var'')')
        candidate = evalin('base', 'study_plistarr');
        plistarr = normalize_cellstr(candidate);
    end
catch
end

try
    if evalin('base', 'exist(''study_punit'',''var'')')
        candidate = evalin('base', 'study_punit');
        punit = normalize_cellstr(candidate);
    end
catch
end

try
    if evalin('base', 'exist(''study_sweeptype'',''var'')')
        candidate = evalin('base', 'study_sweeptype');
        if ischar(candidate) || isstring(candidate)
            sweeptype = char(string(candidate));
        end
    end
catch
end

if isempty(pname) || isempty(plistarr) || numel(pname) ~= numel(plistarr)
    pname = {'k', 'a1'};
    plistarr = {'range(0,3/(N-1),3)', 'range(0.15,0.05,0.30)'};
end
if isempty(punit) || numel(punit) ~= numel(pname)
    punit = repmat({''}, 1, numel(pname));
end
end

function out = normalize_cellstr(v)
out = {};
if isempty(v)
    return;
end
if iscell(v)
    out = cellfun(@char, v, 'UniformOutput', false);
    return;
end
if isstring(v)
    out = cellstr(v);
    return;
end
if ischar(v)
    out = {v};
end
end

function [neigs, shift] = resolve_eigen_settings()
% Allow runners to override eigen solver settings for diagnostic sweeps.
neigs = 12;
shift = '200[Hz]';

try
    if evalin('base', 'exist(''study_neigs'',''var'')')
        candidate = evalin('base', 'study_neigs');
        if isnumeric(candidate) && isscalar(candidate) && isfinite(candidate)
            neigs = double(candidate);
        end
    end
catch
end

try
    if evalin('base', 'exist(''study_shift'',''var'')')
        candidate = evalin('base', 'study_shift');
        if ischar(candidate) || isstring(candidate)
            shift = char(string(candidate));
        elseif isnumeric(candidate) && isscalar(candidate) && isfinite(candidate)
            shift = sprintf('%.12g[Hz]', double(candidate));
        end
    end
catch
end
end
