function model = build_geom_02(model)
% Build geometry: rectangle, param curve -> solid, difference, union.

if isempty(model.component.tags)
    model.component.create('comp1', true);
end
if isempty(model.component('comp1').geom.tags)
    model.component('comp1').geom.create('geom1', 2);
end
model.component('comp1').geom('geom1').lengthUnit('m');

% Rectangle 1 (r1): size a x a, centered at (0,0)
model.component('comp1').geom('geom1').create('r1', 'Rectangle');
model.component('comp1').geom('geom1').feature('r1').set('size', {'a' 'a'});
model.component('comp1').geom('geom1').feature('r1').set('base', 'center');
model.component('comp1').geom('geom1').feature('r1').set('pos', {'0' '0'});
model.component('comp1').geom('geom1').feature('r1').set('rot', '0');

% Parametric curve 1 (pc1)
model.component('comp1').geom('geom1').create('pc1', 'ParametricCurve');
model.component('comp1').geom('geom1').feature('pc1').set('parname', 't');
model.component('comp1').geom('geom1').feature('pc1').set('parmin', '0');
model.component('comp1').geom('geom1').feature('pc1').set('parmax', '2*pi');
model.component('comp1').geom('geom1').feature('pc1').set('coord', {
    'r0*(1+a1*cos(t)+b1*sin(t)+a2*cos(2*t)+b2*sin(2*t)+a3*cos(3*t)+b3*sin(3*t)+a4*cos(4*t)+b4*sin(4*t)+a5*cos(5*t)+b5*sin(5*t))*cos(t)'
    'r0*(1+a1*cos(t)+b1*sin(t)+a2*cos(2*t)+b2*sin(2*t)+a3*cos(3*t)+b3*sin(3*t)+a4*cos(4*t)+b4*sin(4*t)+a5*cos(5*t)+b5*sin(5*t))*sin(t)'
    });
try
    model.component('comp1').geom('geom1').feature('pc1').set('showinphys', 'all');
catch
    % Some versions do not support this property.
end
try
    model.component('comp1').geom('geom1').feature('pc1').set('selresult', true);
    model.component('comp1').geom('geom1').feature('pc1').set('selresultshow', 'all');
catch
    % Property names differ across versions.
end

% Convert to solid 1 (csol1)
model.component('comp1').geom('geom1').create('csol1', 'ConvertToSolid');
model.component('comp1').geom('geom1').feature('csol1').selection('input').set({'pc1'});
try
    model.component('comp1').geom('geom1').feature('csol1').set('merge', true);
catch
    % Property names differ across versions.
end
% repairtol uses numeric value in this version; leave default if unknown
try
    model.component('comp1').geom('geom1').feature('csol1').set('selresult', true);
    model.component('comp1').geom('geom1').feature('csol1').set('selresultshow', 'domain');
catch
end
try
    model.component('comp1').geom('geom1').feature('csol1').set('seldom', true);
catch
end

% Optional discrete perturbation (from preprocess CSV)
csvPath = get_shape_file('D:\graduation_project\coad\data\shape_points\ep1751_step21_contour_xy.csv');
tagPrefix = 'dp1';
perturb_scale = 1.0; % extra scale multiplier after auto-fit
perturb_dx = 0.0; % extra offset after auto-center
perturb_dy = 0.0; % extra offset after auto-center
perturb_mode = get_perturb_mode(); % 'union' or 'difference'

baseSolidTag = 'csol1';
dpOk = false;
dpSolidTag = '';
try
    [model, dpSolidTag, dpOk] = add_discrete_perturbation( ...
        model, csvPath, tagPrefix, perturb_scale, perturb_dx, perturb_dy);
catch ME
    warning('build_geom_02:DiscretePerturbation', 'Discrete perturbation skipped: %s', ME.message);
end

% Union defect with main boundary (if any)
if dpOk
    model.component('comp1').geom('geom1').create('uni1', 'Union');
    model.component('comp1').geom('geom1').feature('uni1').selection('input').set({baseSolidTag, dpSolidTag});
    baseSolidTag = 'uni1';
end

% Intersect with unit cell (inside domain)
model.component('comp1').geom('geom1').create('int1', 'Intersection');
model.component('comp1').geom('geom1').feature('int1').selection('input').set({baseSolidTag, 'r1'});
try
    model.component('comp1').geom('geom1').feature('int1').set('keep', true);
catch
end
try
    model.component('comp1').geom('geom1').feature('int1').set('intbnd', false);
catch
end
try
    model.component('comp1').geom('geom1').feature('int1').set('selresult', true);
    model.component('comp1').geom('geom1').feature('int1').set('selresultshow', 'domain');
catch
end

% Difference (outside domain)
model.component('comp1').geom('geom1').create('dif1', 'Difference');
model.component('comp1').geom('geom1').feature('dif1').selection('input').set({'r1'});
model.component('comp1').geom('geom1').feature('dif1').selection('input2').set({'int1'});
try
    model.component('comp1').geom('geom1').feature('dif1').set('keep', false);
catch
end
try
    model.component('comp1').geom('geom1').feature('dif1').set('keepsubtract', true);
catch
end
try
    model.component('comp1').geom('geom1').feature('dif1').set('intbnd', false);
catch
end
try
    model.component('comp1').geom('geom1').feature('dif1').set('selresult', true);
    model.component('comp1').geom('geom1').feature('dif1').set('selresultshow', 'domain');
catch
end

% Form union happens at the geometry level in this version.

model.component('comp1').geom('geom1').runPre('dif1');
ensure_finalize(model);
model.component('comp1').geom('geom1').run('fin');

% Print domain counts if available
print_domain_counts(model, 'int1', 'dif1');
end

function [model, solidTag, ok] = add_discrete_perturbation(model, csvPath, tagPrefix, scale, dx, dy)
% Add discrete perturbation from CSV (x,y) as a closed polygon.
solidTag = '';
ok = false;

if nargin < 2 || isempty(csvPath) || ~isfile(csvPath)
    warning('Discrete perturbation CSV not found: %s', csvPath);
    return;
end

xy = readmatrix(csvPath);
xy = xy(:, 1:2);
xy = xy(~any(isnan(xy), 2), :);
if size(xy, 1) < 3
    warning('Discrete perturbation points < 3, skip.');
    return;
end

% Ensure closed polygon
if norm(xy(1, :) - xy(end, :)) > 1e-9
    xy = [xy; xy(1, :)];
end

% Compute max radius and auto scale to target radius
xmin = min(xy(:, 1));
xmax = max(xy(:, 1));
ymin = min(xy(:, 2));
ymax = max(xy(:, 2));
W = xmax - xmin;
H = ymax - ymin;
if W <= 0 || H <= 0
    warning('Discrete perturbation bbox invalid, skip.');
    return;
end
cx = 0.5 * (xmin + xmax);
cy = 0.5 * (ymin + ymax);

r = max([max(abs(xy(:, 1))), max(abs(xy(:, 2)))]);
if ~isfinite(r) || r <= 0
    warning('Discrete perturbation radius invalid, skip.');
    return;
end
rt = 0.006;
s_auto = rt / r;
if ~isfinite(s_auto) || s_auto <= 0
    warning('Auto scale invalid, skip.');
    return;
end
s = s_auto;
if nargin >= 4 && ~isempty(scale) && isfinite(scale) && scale > 0
    s = s_auto * scale; % optional extra multiplier
end

% Scaled bbox for debug
xmin_s = xmin * s;
xmax_s = xmax * s;
ymin_s = ymin * s;
ymax_s = ymax * s;

% Random point on Fourier boundary for placement (sampled)
rng('shuffle');
params = get_fourier_params(model);
N = 300;
t = linspace(0, 2*pi, N + 1);
t(end) = [];
[xs, ys] = fourier_point(t, params);
P = [xs(:), ys(:)];

maxTries = 30;
curvThresh = 0.7;
i = 1;
okPick = false;
for attempt = 1:maxTries
    i = randi(N);
    ip = mod(i - 2, N) + 1;
    in = mod(i, N) + 1;
    p_prev = P(ip, :);
    p = P(i, :);
    p_next = P(in, :);
    u1 = p - p_prev;
    u2 = p_next - p;
    l1 = hypot(u1(1), u1(2));
    l2 = hypot(u2(1), u2(2));
    if l1 <= 0 || l2 <= 0
        continue;
    end
    u1 = u1 / l1;
    u2 = u2 / l2;
    curv = 1 - dot(u1, u2);
    if curv <= curvThresh
        okPick = true;
        break;
    end
end
if ~okPick
    warning('High curvature everywhere, using last pick.');
end

p_prev = P(mod(i - 2, N) + 1, :);
p = P(i, :);
p_next = P(mod(i, N) + 1, :);
tvec = p_next - p_prev;
tlen = hypot(tvec(1), tvec(2));
if tlen <= 0
    warning('Boundary tangent invalid, skip.');
    return;
end
tvec = tvec / tlen;
n = [-tvec(2), tvec(1)];
if dot(n, -p) < 0
    n = -n; % ensure inward
end
delta = 0.0008;
p_target = p + delta * n;

% Anchor defect center after scaling
cx_s = cx * s;
cy_s = cy * s;
dx0 = p_target(1) - cx_s;
dy0 = p_target(2) - cy_s;
if nargin >= 5 && ~isempty(dx) && isfinite(dx)
    dx0 = dx0 + dx;
end
if nargin >= 6 && ~isempty(dy) && isfinite(dy)
    dy0 = dy0 + dy;
end

fprintf('[dp1] i=%d, p=(%.6g,%.6g), n=(%.6g,%.6g), dx=%.6g, dy=%.6g, r=%.6g, s=%.6g, bbox_s=[%.6g %.6g %.6g %.6g]\n', ...
    i, p(1), p(2), n(1), n(2), dx0, dy0, r, s, xmin_s, xmax_s, ymin_s, ymax_s);

geom = model.component('comp1').geom('geom1');
polyTag = [tagPrefix '_poly'];
geom.create(polyTag, 'Polygon');
try
    geom.feature(polyTag).set('source', 'file');
    geom.feature(polyTag).set('filename', csvPath);
catch
    geom.feature(polyTag).set('x', xy(:, 1));
    geom.feature(polyTag).set('y', xy(:, 2));
end
try
    geom.feature(polyTag).set('type', 'closed');
catch
end

solidTag = [tagPrefix '_csol'];
geom.create(solidTag, 'ConvertToSolid');
geom.feature(solidTag).selection('input').set({polyTag});

scaTag = [tagPrefix '_sca'];
geom.create(scaTag, 'Scale');
geom.feature(scaTag).selection('input').set({solidTag});
geom.feature(scaTag).set('factor', s);
try
    geom.feature(scaTag).set('center', {'0' '0'});
catch
    try
        geom.feature(scaTag).set('pos', {'0' '0'});
    catch
    end
end

movTag = [tagPrefix '_mov'];
geom.create(movTag, 'Move');
geom.feature(movTag).selection('input').set({scaTag});
geom.feature(movTag).set('displ', {num2str(dx0) num2str(dy0)});
solidTag = movTag;
ok = true;
end

function ensure_finalize(model)
% Ensure geometry has a finalize feature tagged 'fin'.
geom = model.component('comp1').geom('geom1');
try
    geom.feature('fin');
    return;
catch
end

try
    geom.create('fin', 'Finalize');
catch
    try
        geom.create('fin', 'FormUnion');
    catch
    end
end
end

function mode = get_perturb_mode()
% Helper to avoid constant-condition warnings in the editor.
mode = 'union';
end

function v = eval_param(model, expr, fallback)
% Evaluate a parameter/expression safely.
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

function s = get_shape_file(fallback)
% Read shape_file from MATLAB base workspace if provided; otherwise fallback.
s = fallback;
try
    if evalin('base', 'exist(''shape_file'',''var'')')
        v = evalin('base', 'shape_file');
        if ischar(v) || isstring(v)
            s = char(v);
        end
    end
catch
end
end

function params = get_fourier_params(model)
% Collect Fourier boundary parameters.
params.r0 = eval_param(model, 'r0', 0.012);
params.a = zeros(1, 5);
params.b = zeros(1, 5);
for k = 1:5
    params.a(k) = eval_param(model, sprintf('a%d', k), 0);
    params.b(k) = eval_param(model, sprintf('b%d', k), 0);
end
end

function [x, y] = fourier_point(t, params)
% Evaluate Fourier boundary point.
amp = 1.0;
for k = 1:5
    amp = amp + params.a(k) * cos(k * t) + params.b(k) * sin(k * t);
end
r = params.r0 * amp;
x = r .* cos(t);
y = r .* sin(t);
end

function print_domain_counts(model, intTag, difTag)
% Best-effort domain counts for geometry features.
ni = get_feature_ndom(model, intTag);
nd = get_feature_ndom(model, difTag);
fprintf('[geom] %s domains=%d, %s domains=%d\n', intTag, ni, difTag, nd);
end

function n = get_feature_ndom(model, tag)
% Try to get domain count for a feature; returns -1 if unavailable.
n = -1;
try
    geom = model.component('comp1').geom('geom1');
    n = geom.feature(tag).getNDom;
    return;
catch
end
try
    sel = mphgetselection(model.selection(['geom1_' tag '_dom']));
    if isfield(sel, 'entities')
        n = numel(sel.entities);
    end
catch
end
end

function [cx, cy] = get_rect_center(model, rectTag)
% Get rectangle center; falls back to origin if unknown.
cx = 0;
cy = 0;
try
    geom = model.component('comp1').geom('geom1');
    feat = geom.feature(rectTag);
catch
    return;
end

base = 'center';
try
    base = char(feat.getString('base'));
catch
end

[px, py, okPos] = get_vec_param(model, feat, 'pos', 0);
[sx, sy, okSize] = get_vec_param(model, feat, 'size', 0);
if ~okPos
    px = 0; py = 0;
end
if ~okSize
    sx = 0; sy = 0;
end

if strcmpi(base, 'center')
    cx = px; cy = py;
else
    cx = px + sx / 2;
    cy = py + sy / 2;
end
end

function [x, y, ok] = get_vec_param(model, feat, key, a_fallback)
% Read 2D vector-like feature property and evaluate.
x = 0; y = 0; ok = false;
vals = {};
try
    vals = feat.getStringArray(key);
catch
end
vals = normalize_to_cellstr(vals);
if isempty(vals)
    try
        v = feat.getString(key);
        vals = normalize_to_cellstr(v);
    catch
    end
end
if numel(vals) >= 2
    x = eval_param(model, vals{1}, a_fallback);
    y = eval_param(model, vals{2}, a_fallback);
    ok = true;
end
end

function out = normalize_to_cellstr(v)
% Normalize strings / arrays to cellstr.
out = {};
if isempty(v)
    return;
end

if iscell(v)
    out = v;
    return;
end
if isstring(v)
    out = cellstr(v);
    return;
end
if ischar(v)
    out = strsplit(v);
    return;
end
try
    out = cellstr(string(v));
catch
end
end
