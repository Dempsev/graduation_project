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
shapeDir = fullfile('data', 'shape_points');
csvPath = get_shape_file(shapeDir);
tagPrefix = 'dp1';
ensure_perturb_skip_log();
set_perturb_skip_state(false, '', csvPath);

baseSolidTag = 'csol1';
dpOk = false;
dpSolidTag = '';
try
    [model, dpSolidTag, dpOk] = add_discrete_perturbation( ...
        model, csvPath, tagPrefix);
catch ME
    warning('build_geom_02:DiscretePerturbation', 'Discrete perturbation skipped: %s', ME.message);
end

% Union defect with main boundary (if any)
if dpOk
    model.component('comp1').geom('geom1').create('uni1', 'Union');
    model.component('comp1').geom('geom1').feature('uni1').selection('input').set({baseSolidTag, dpSolidTag});
    try
        model.component('comp1').geom('geom1').feature('uni1').set('keep', false);
    catch
    end
    try
        model.component('comp1').geom('geom1').feature('uni1').set('intbnd', false);
    catch
    end
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

function [model, solidTag, ok] = add_discrete_perturbation(model, csvPath, tagPrefix)
% Add discrete perturbation from CSV (x,y) as a closed polygon.
solidTag = '';
ok = false;

if nargin < 2 || isempty(csvPath) || ~isfile(csvPath)
    warning('Discrete perturbation CSV not found: %s', csvPath);
    append_perturb_skip_log(csvPath, 'csv_not_found', -1);
    set_perturb_skip_state(true, 'csv_not_found', csvPath);
    return;
end

xy = readmatrix(csvPath);
xy = xy(:, 1:2);
xy = xy(~any(isnan(xy), 2), :);
if size(xy, 1) < 3
    warning('Discrete perturbation points < 3, skip.');
    append_perturb_skip_log(csvPath, 'too_few_points', -1);
    set_perturb_skip_state(true, 'too_few_points', csvPath);
    return;
end

% Ensure closed polygon
if norm(xy(1, :) - xy(end, :)) > 1e-9
    xy = [xy; xy(1, :)];
end

% No move step: use original polygon position directly.
% Require actual contact with Fourier boundary; non-contact samples are skipped.
[contactOK, minDist] = check_discrete_contact_with_fourier_boundary(model, xy);
if ~contactOK
    warning('Discrete perturbation skipped (no contact with Fourier boundary): %s', csvPath);
    append_perturb_skip_log(csvPath, 'no_contact_with_fourier_boundary', minDist);
    set_perturb_skip_state(true, 'no_contact_with_fourier_boundary', csvPath);
    return;
end

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
ok = true;
set_perturb_skip_state(false, 'ok', csvPath);
end

function [ok, minDist] = check_discrete_contact_with_fourier_boundary(model, xy)
% Contact test against Fourier boundary curve.
ok = false;
minDist = inf;

params = get_fourier_params(model);
N = 1440;
t = linspace(0, 2*pi, N + 1)';
[fx, fy] = fourier_point(t, params);
fourierXY = [fx(:), fy(:)];
if size(fourierXY, 1) < 4 || size(xy, 1) < 4
    return;
end

% 1) Edge intersection => contact.
if has_polyline_intersection(xy, fourierXY)
    ok = true;
    minDist = 0;
    return;
end

% 2) Near-contact by sampled boundary distance.
minDist = min_polyline_distance(xy, fourierXY);
contactTol = 2e-4; % meters
if minDist <= contactTol
    ok = true;
end
end

function d = min_polyline_distance(poly1, poly2)
% Approximate symmetric minimum distance between sampled polyline points.
d = inf;
for i = 1:size(poly1, 1)
    d2 = (poly2(:, 1) - poly1(i, 1)).^2 + (poly2(:, 2) - poly1(i, 2)).^2;
    d = min(d, sqrt(min(d2)));
end
for j = 1:size(poly2, 1)
    d2 = (poly1(:, 1) - poly2(j, 1)).^2 + (poly1(:, 2) - poly2(j, 2)).^2;
    d = min(d, sqrt(min(d2)));
end
end

function tf = has_polyline_intersection(poly1, poly2)
% Check segment intersections between two closed polylines.
tf = false;
for i = 1:size(poly1, 1) - 1
    p1 = poly1(i, :);
    q1 = poly1(i + 1, :);
    for j = 1:size(poly2, 1) - 1
        p2 = poly2(j, :);
        q2 = poly2(j + 1, :);
        if segments_intersect(p1, q1, p2, q2)
            tf = true;
            return;
        end
    end
end
end

function tf = segments_intersect(p1, q1, p2, q2)
% Robust 2D segment intersection test with tolerance.
eps0 = 1e-12;
o1 = orient2d(p1, q1, p2);
o2 = orient2d(p1, q1, q2);
o3 = orient2d(p2, q2, p1);
o4 = orient2d(p2, q2, q1);

if (o1 * o2 < 0) && (o3 * o4 < 0)
    tf = true;
    return;
end
if abs(o1) < eps0 && on_segment(p1, q1, p2, eps0)
    tf = true; return;
end
if abs(o2) < eps0 && on_segment(p1, q1, q2, eps0)
    tf = true; return;
end
if abs(o3) < eps0 && on_segment(p2, q2, p1, eps0)
    tf = true; return;
end
if abs(o4) < eps0 && on_segment(p2, q2, q1, eps0)
    tf = true; return;
end
tf = false;
end

function v = orient2d(a, b, c)
v = (b(1) - a(1)) * (c(2) - a(2)) - (b(2) - a(2)) * (c(1) - a(1));
end

function tf = on_segment(a, b, p, eps0)
tf = p(1) >= min(a(1), b(1)) - eps0 && p(1) <= max(a(1), b(1)) + eps0 && ...
     p(2) >= min(a(2), b(2)) - eps0 && p(2) <= max(a(2), b(2)) + eps0;
end

function append_perturb_skip_log(shapePath, reason, value)
% Append skipped perturbation records for batch traceability.
logPath = resolve_path(fullfile('data', 'shape_batch', 'perturb_skip_log.csv'));
prepare_perturb_skip_log_file(logPath);
needHeader = ~isfile(logPath);
fid = fopen(logPath, 'a');
if fid < 0
    return;
end
cleanupObj = onCleanup(@() fclose(fid));
if needHeader
    fprintf(fid, 'timestamp,shape_file,reason,min_distance\n');
end
ts = datestr(now, 'yyyy-mm-dd HH:MM:SS');
shapePath = strrep(shapePath, '\', '/');
fprintf(fid, '%s,"%s",%s,%.12g\n', ts, shapePath, reason, value);
end

function ensure_perturb_skip_log()
% Ensure skip log file exists so users can always find it.
logPath = resolve_path(fullfile('data', 'shape_batch', 'perturb_skip_log.csv'));
prepare_perturb_skip_log_file(logPath);
if ~isfile(logPath)
    fid = fopen(logPath, 'w');
    if fid < 0
        return;
    end
    cleanupObj = onCleanup(@() fclose(fid));
    fprintf(fid, 'timestamp,shape_file,reason,min_distance\n');
end
end

function prepare_perturb_skip_log_file(logPath)
% Ensure parent directory for skip log exists.
[logDir, ~, ~] = fileparts(logPath);
if ~exist(logDir, 'dir')
    mkdir(logDir);
end
end

function set_perturb_skip_state(isSkipped, reason, shapePath)
% Expose perturbation skip state for batch scripts.
try
    assignin('base', 'shape_skip', logical(isSkipped));
    assignin('base', 'shape_skip_reason', char(reason));
    assignin('base', 'shape_skip_file', char(shapePath));
catch
end
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

function s = get_shape_file(fallback)
% Read shape_file from MATLAB base workspace if provided; otherwise fallback.
% fallback can be a directory or a file path (absolute or relative).

s = '';
baseDir = '';

fallbackAbs = resolve_path(fallback);
if isfolder(fallbackAbs)
    baseDir = fallbackAbs;
else
    s = fallbackAbs;
    baseDir = fileparts(fallbackAbs);
end

try
    if evalin('base', 'exist(''shape_file'',''var'')')
        v = evalin('base', 'shape_file');
        if ischar(v) || isstring(v)
            candRaw = char(v);
            if is_absolute_path(candRaw)
                cand = candRaw;
            else
                cand = fullfile(baseDir, candRaw);
                if ~isfile(cand) && ~isfolder(cand)
                    cand = resolve_path(candRaw);
                end
            end
            if isfolder(cand)
                baseDir = cand;
                s = '';
            elseif isfile(cand)
                s = cand;
            end
        end
    end
catch
end

if isempty(s) && ~isempty(baseDir)
    files = dir(fullfile(baseDir, '*_contour_xy.csv'));
    if isempty(files)
        files = dir(fullfile(baseDir, '*.csv'));
    end
    if ~isempty(files)
        names = sort({files.name});
        s = fullfile(baseDir, names{1});
    end
end
end

function p = resolve_path(p)
% Resolve relative paths from project root.
if isempty(p)
    return;
end
if isstring(p)
    p = char(p);
end
if ~ischar(p)
    return;
end
if ~is_absolute_path(p)
    [thisDir, ~, ~] = fileparts(mfilename('fullpath'));
    projectRoot = fileparts(thisDir);
    p = fullfile(projectRoot, p);
end
end

function tf = is_absolute_path(p)
tf = false;
if isempty(p)
    return;
end
if isstring(p)
    p = char(p);
end
if ~ischar(p)
    return;
end
if numel(p) >= 2 && p(2) == ':'
    tf = true;
    return;
end
if startsWith(p, filesep)
    tf = true;
end
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
