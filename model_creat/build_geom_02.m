function model = build_geom_02(model)
% Build geometry: rectangle, param curve -> solid, difference, union.

if isempty(model.geom.tags)
    model.geom.create('geom1', 2);
end
model.geom('geom1').lengthUnit('m');

% Rectangle 1 (r1): size a x a, centered at (0,0)
model.geom('geom1').create('r1', 'Rectangle');
model.geom('geom1').feature('r1').set('size', {'a' 'a'});
model.geom('geom1').feature('r1').set('base', 'center');
model.geom('geom1').feature('r1').set('pos', {'0' '0'});
model.geom('geom1').feature('r1').set('rot', '0');

% Parametric curve 1 (pc1)
model.geom('geom1').create('pc1', 'ParametricCurve');
model.geom('geom1').feature('pc1').set('parname', 't');
model.geom('geom1').feature('pc1').set('parmin', '0');
model.geom('geom1').feature('pc1').set('parmax', '2*pi');
model.geom('geom1').feature('pc1').set('coord', {
    'r0*(1+a1*cos(t)+b1*sin(t)+a2*cos(2*t)+b2*sin(2*t)+a3*cos(3*t)+b3*sin(3*t)+a4*cos(4*t)+b4*sin(4*t)+a5*cos(5*t)+b5*sin(5*t))*cos(t)'
    'r0*(1+a1*cos(t)+b1*sin(t)+a2*cos(2*t)+b2*sin(2*t)+a3*cos(3*t)+b3*sin(3*t)+a4*cos(4*t)+b4*sin(4*t)+a5*cos(5*t)+b5*sin(5*t))*sin(t)'
    });
try
    model.geom('geom1').feature('pc1').set('showinphys', 'all');
catch
    % Some versions do not support this property.
end
try
    model.geom('geom1').feature('pc1').set('selresult', true);
    model.geom('geom1').feature('pc1').set('selresultshow', 'all');
catch
    % Property names differ across versions.
end

% Convert to solid 1 (csol1)
model.geom('geom1').create('csol1', 'ConvertToSolid');
model.geom('geom1').feature('csol1').selection('input').set({'pc1'});
try
    model.geom('geom1').feature('csol1').set('merge', true);
catch
    % Property names differ across versions.
end
% repairtol uses numeric value in this version; leave default if unknown
try
    model.geom('geom1').feature('csol1').set('selresult', true);
    model.geom('geom1').feature('csol1').set('selresultshow', 'domain');
catch
end
try
    model.geom('geom1').feature('csol1').set('seldom', true);
catch
end

% Difference 1 (dif1): r1 - csol1
model.geom('geom1').create('dif1', 'Difference');
model.geom('geom1').feature('dif1').selection('input').set({'r1'});
model.geom('geom1').feature('dif1').selection('input2').set({'csol1'});
try
    model.geom('geom1').feature('dif1').set('keep', false);
catch
end
try
    model.geom('geom1').feature('dif1').set('keep2', true);
catch
end
try
    model.geom('geom1').feature('dif1').set('intbnd', true);
catch
end

model.geom('geom1').run;
end
