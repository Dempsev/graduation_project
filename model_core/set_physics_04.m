function model = set_physics_04(model)
% Solid mechanics + Floquet periodic conditions.
% Boundary IDs vary by model, so pick periodic pairs by rectangle position.

if isempty(model.component.tags)
    model.component.create('comp1', true);
end

try
    model.component('comp1').common.create('mpf1', 'ParticipationFactors');
catch
end

try
    model.component('comp1').physics('solid');
catch
    model.component('comp1').physics.create('solid', 'SolidMechanics', 'geom1');
end

[leftBnd, rightBnd, bottomBnd, topBnd] = detect_outer_rect_boundaries(model);

try
    model.component('comp1').physics('solid').feature('pc1');
catch
    model.component('comp1').physics('solid').create('pc1', 'PeriodicCondition', 1);
end
model.component('comp1').physics('solid').feature('pc1').selection.set([leftBnd rightBnd]);
model.component('comp1').physics('solid').feature('pc1').set('PeriodicType', 'Floquet');
model.component('comp1').physics('solid').feature('pc1').set('kFloquet', {'kx' 'ky' '0'});
model.component('comp1').physics('solid').feature('pc1').label(['kx_' native2unicode(hex2dec({'54' '68'}), 'unicode')  native2unicode(hex2dec({'67' '1f'}), 'unicode')  native2unicode(hex2dec({'60' '27'}), 'unicode')  native2unicode(hex2dec({'67' '61'}), 'unicode')  native2unicode(hex2dec({'4e' 'f6'}), 'unicode') ]);

try
    model.component('comp1').physics('solid').feature('pc2');
catch
    model.component('comp1').physics('solid').create('pc2', 'PeriodicCondition', 1);
end
model.component('comp1').physics('solid').feature('pc2').selection.set([bottomBnd topBnd]);
model.component('comp1').physics('solid').feature('pc2').set('PeriodicType', 'Floquet');
model.component('comp1').physics('solid').feature('pc2').set('kFloquet', {'kx' 'ky' '0'});
model.component('comp1').physics('solid').feature('pc2').label(['ky_' native2unicode(hex2dec({'54' '68'}), 'unicode')  native2unicode(hex2dec({'67' '1f'}), 'unicode')  native2unicode(hex2dec({'60' '27'}), 'unicode')  native2unicode(hex2dec({'67' '61'}), 'unicode')  native2unicode(hex2dec({'4e' 'f6'}), 'unicode') ]);
end

function [leftBnd, rightBnd, bottomBnd, topBnd] = detect_outer_rect_boundaries(model)
% Pick outer rectangle boundaries by coordinates, not fixed IDs.
a = eval_param(model, 'a', 0.05);
halfA = a / 2;
tol = max(1e-4, 0.01 * a);
ext = halfA + tol;

leftCand = mph_select_box_boundary(model, [-halfA - tol, -halfA + tol, -ext, ext]);
rightCand = mph_select_box_boundary(model, [halfA - tol, halfA + tol, -ext, ext]);
bottomCand = mph_select_box_boundary(model, [-ext, ext, -halfA - tol, -halfA + tol]);
topCand = mph_select_box_boundary(model, [-ext, ext, halfA - tol, halfA + tol]);

leftBnd = choose_best_boundary(model, leftCand, 1, -halfA);
rightBnd = choose_best_boundary(model, rightCand, 1, halfA);
bottomBnd = choose_best_boundary(model, bottomCand, 2, -halfA);
topBnd = choose_best_boundary(model, topCand, 2, halfA);

if any([leftBnd rightBnd bottomBnd topBnd] <= 0)
    error('set_physics_04:BoundaryDetectFailed', ...
        'Failed to detect rectangle outer boundaries for periodic conditions.');
end
end

function ids = mph_select_box_boundary(model, b)
% b = [xmin xmax ymin ymax]
ids = [];
try
    ids = mphselectbox(model, 'geom1', [b(1) b(2); b(3) b(4)], 'boundary');
catch
    try
        ids = mphselectbox(model, 'geom1', [b(1) b(3); b(2) b(4)], 'boundary');
    catch
        ids = [];
    end
end
ids = unique(double(ids(:)'));
end

function bid = choose_best_boundary(model, candidates, axisIdx, targetVal)
% axisIdx: 1 for x, 2 for y
bid = -1;
if isempty(candidates)
    return;
end
if numel(candidates) == 1
    bid = candidates(1);
    return;
end

bestScore = inf;
for k = 1:numel(candidates)
    id = candidates(k);
    score = boundary_line_score(model, id, axisIdx, targetVal);
    if score < bestScore
        bestScore = score;
        bid = id;
    end
end
end

function s = boundary_line_score(model, bid, axisIdx, targetVal)
s = inf;
try
    p = mphgetcoords(model, 'geom1', 'boundary', bid);
catch
    return;
end
[x, y] = normalize_coords_2d(p);
if isempty(x)
    return;
end
if axisIdx == 1
    d = abs(x - targetVal);
else
    d = abs(y - targetVal);
end
s = mean(d) + max(d);
end

function [x, y] = normalize_coords_2d(p)
% Normalize mphgetcoords output to x/y vectors.
x = [];
y = [];
if isempty(p)
    return;
end
if iscell(p)
    try
        p = cell2mat(p);
    catch
        return;
    end
end
if size(p, 1) == 2
    x = p(1, :);
    y = p(2, :);
elseif size(p, 2) == 2
    x = p(:, 1)';
    y = p(:, 2)';
end
end

function v = eval_param(model, expr, fallback)
v = fallback;
try
    v = model.param.evaluate(expr);
    if ischar(v) || isstring(v)
        v = str2double(v);
    end
catch
    tmp = str2double(expr);
    if ~isnan(tmp)
        v = tmp;
    end
end
end
