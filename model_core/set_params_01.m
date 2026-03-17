function model = set_params_01(model)
% Parameter groups: par1 / par2 (GUI only). Falls back to flat params.

% Group 1
try
    model.param.group('par1');
catch
    model.param.group.create('par1');
end
try
    model.param.group('par1').set('a',  '0.05[m]');
    model.param.group('par1').set('N',  '41');
    model.param.group('par1').set('k',  '0');
    model.param.group('par1').set('kx', 'if(k<1,(1-k)*pi/a,if(k<2,(k-1)*pi/a,pi/a))');
    model.param.group('par1').set('ky', 'if(k<1,(1-k)*pi/a,if(k<2,0,(k-2)*pi/a))');
catch
    model.param.set('a',  '0.05[m]');
    model.param.set('N',  '41');
    model.param.set('k',  '0');
    model.param.set('kx', 'if(k<1,(1-k)*pi/a,if(k<2,(k-1)*pi/a,pi/a))');
    model.param.set('ky', 'if(k<1,(1-k)*pi/a,if(k<2,0,(k-2)*pi/a))');
end

% Group 2
try
    model.param.group('par2');
catch
    model.param.group.create('par2');
end
try
    model.param.group('par2').set('r0',  '0.012[m]');
    model.param.group('par2').set('n',   '8');
    model.param.group('par2').set('phi', '0[rad]');
    model.param.group('par2').set('amp', '0.2');
    model.param.group('par2').set('a1', '0.18');
    model.param.group('par2').set('b1', '0.05');
    model.param.group('par2').set('a2', '0.14');
    model.param.group('par2').set('b2', '-0.06');
    model.param.group('par2').set('a3', '0.06');
    model.param.group('par2').set('b3', '-0.05');
    model.param.group('par2').set('a4', '0.04');
    model.param.group('par2').set('b4', '-0.02');
    model.param.group('par2').set('a5', '0.03');
    model.param.group('par2').set('b5', '0.01');
catch
    model.param.set('r0',  '0.012[m]');
    model.param.set('n',   '8');
    model.param.set('phi', '0[rad]');
    model.param.set('amp', '0.2');
    model.param.set('a1', '0.18');
    model.param.set('b1', '0.05');
    model.param.set('a2', '0.14');
    model.param.set('b2', '-0.06');
    model.param.set('a3', '0.06');
    model.param.set('b3', '-0.05');
    model.param.set('a4', '0.04');
    model.param.set('b4', '-0.02');
    model.param.set('a5', '0.03');
    model.param.set('b5', '0.01');
end

model = apply_base_param_overrides(model);
end

function model = apply_base_param_overrides(model)
% Allow runners to override Fourier-related parameters from base workspace.
overrides = get_base_struct('fourier_param_overrides');
if isempty(overrides)
    return;
end

names = fieldnames(overrides);
for i = 1:numel(names)
    name = char(names{i});
    value = format_param_value(overrides.(name));
    if isempty(name) || isempty(value)
        continue;
    end

    groupTag = resolve_param_group(name);
    if ~isempty(groupTag)
        try
            model.param.group(groupTag).set(name, value);
        catch
        end
    end

    try
        model.param.set(name, value);
    catch
    end
end
end

function s = get_base_struct(varName)
s = struct();
try
    if evalin('base', sprintf('exist(''%s'',''var'')', varName))
        candidate = evalin('base', varName);
        if isstruct(candidate)
            s = candidate;
        end
    end
catch
end
end

function groupTag = resolve_param_group(name)
groupTag = '';
par1 = {'a', 'N', 'k', 'kx', 'ky'};
if any(strcmp(name, par1))
    groupTag = 'par1';
    return;
end

par2 = {'r0', 'n', 'phi', 'amp', 'a1', 'b1', 'a2', 'b2', 'a3', 'b3', 'a4', 'b4', 'a5', 'b5'};
if any(strcmp(name, par2))
    groupTag = 'par2';
end
end

function value = format_param_value(raw)
value = '';
if isempty(raw)
    return;
end
if isstring(raw) || ischar(raw)
    value = char(string(raw));
    return;
end
if isnumeric(raw) && isscalar(raw) && isfinite(raw)
    value = sprintf('%.12g', raw);
end
end
