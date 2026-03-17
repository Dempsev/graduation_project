function [report, model] = validate_stage2_geometry(cfg, pointSpec, shapeFile, sampleId)
%VALIDATE_STAGE2_GEOMETRY Build one stage-2 geometry and return screening checks.
% The geometry gate matches stage-1 semantics: every random snake shape is kept
% in the dataset, but only contact-valid shapes proceed to expensive solves.

import com.comsol.model.*
import com.comsol.model.util.*

if nargin < 3
    shapeFile = '';
end
if nargin < 4 || isempty(sampleId)
    sampleId = 'stage2_sample';
end

report = struct( ...
    'geometry_valid', false, ...
    'contact_valid', isempty(shapeFile), ...
    'contact_length', NaN, ...
    'n_domains', NaN, ...
    'has_tiny_fragments', false, ...
    'error_message', '' ...
);
model = [];

shapeCheck = inspect_shape_contact(cfg, pointSpec, shapeFile);
report.contact_valid = shapeCheck.contact_valid;
report.contact_length = shapeCheck.contact_length;

if ~shapeCheck.file_valid
    report.error_message = shapeCheck.error_message;
    return;
end

try
    ModelUtil.clear;
    ModelUtil.showProgress(true);
    model = ModelUtil.create('Model');
    model.modelPath(cfg.outDir);
    model.label(char(sampleId));

    assign_stage2_context(cfg, pointSpec, sampleId, shapeFile);
    model = set_params_01(model);
    model = build_geom_02(model);
catch ME
    report.error_message = ['geometry_build_failed: ' char(string(ME.message))];
    model = [];
    return;
end

report.n_domains = get_total_domain_count(model);
report.has_tiny_fragments = isfinite(report.n_domains) && ...
    report.n_domains > cfg.tinyFragmentDomainThreshold;

skipReason = get_base_string('shape_skip_reason');
if isempty(shapeFile)
    skipReason = '';
end

if strcmp(skipReason, 'no_contact_with_fourier_boundary')
    report.contact_valid = false;
    if report.contact_length == 0
        report.contact_length = 0;
    end
    report.error_message = skipReason;
elseif ~isempty(skipReason) && ~strcmp(skipReason, 'ok') && ~strcmp(skipReason, 'disabled')
    report.error_message = skipReason;
end

if ~isfinite(report.n_domains) || report.n_domains < cfg.minExpectedDomains
    report.error_message = first_nonempty(report.error_message, 'unexpected_domain_count');
    report.geometry_valid = false;
    return;
end

if report.has_tiny_fragments
    report.error_message = first_nonempty(report.error_message, 'geometry_has_tiny_fragments');
    report.geometry_valid = false;
    return;
end

if ~isempty(shapeFile) && strcmp(skipReason, 'no_contact_with_fourier_boundary')
    report.geometry_valid = true;
    return;
end

if ~isempty(shapeFile) && ~report.contact_valid
    report.error_message = first_nonempty(report.error_message, 'no_contact_with_fourier_boundary');
    report.geometry_valid = true;
    return;
end

if ~isempty(report.error_message)
    report.geometry_valid = false;
    return;
end

report.geometry_valid = true;
end

function out = inspect_shape_contact(cfg, pointSpec, shapeFile)
out = struct( ...
    'file_valid', true, ...
    'contact_valid', isempty(shapeFile), ...
    'contact_length', NaN, ...
    'min_distance', NaN, ...
    'error_message', '' ...
);

if isempty(shapeFile)
    return;
end
if ~isfile(shapeFile)
    out.file_valid = false;
    out.contact_valid = false;
    out.contact_length = NaN;
    out.error_message = 'csv_not_found';
    return;
end

try
    xy = readmatrix(shapeFile);
catch
    out.file_valid = false;
    out.contact_valid = false;
    out.error_message = 'csv_read_failed';
    return;
end

if size(xy, 2) < 2
    out.file_valid = false;
    out.contact_valid = false;
    out.error_message = 'too_few_points';
    return;
end

xy = xy(:, 1:2);
xy = xy(~any(isnan(xy), 2), :);
if size(xy, 1) < 3
    out.file_valid = false;
    out.contact_valid = false;
    out.error_message = 'too_few_points';
    return;
end

if norm(xy(1, :) - xy(end, :)) > 1e-9
    xy = [xy; xy(1, :)];
end

fourierXY = sample_fourier_boundary(cfg, pointSpec);
if size(fourierXY, 1) < 4
    out.file_valid = false;
    out.contact_valid = false;
    out.error_message = 'fourier_boundary_sampling_failed';
    return;
end

if has_polyline_intersection(xy, fourierXY)
    out.contact_valid = true;
else
    d = point_to_polyline_distances(fourierXY, xy);
    out.min_distance = min(d);
    out.contact_valid = out.min_distance <= cfg.contactTol;
end

if isnan(out.min_distance)
    d = point_to_polyline_distances(fourierXY, xy);
    out.min_distance = min(d);
end

out.contact_length = estimate_contact_length(fourierXY, xy, cfg.contactTol);
if ~out.contact_valid
    out.contact_length = 0;
end
end

function xy = sample_fourier_boundary(cfg, pointSpec)
t = linspace(0, 2 * pi, cfg.contactSampleCount + 1)';
params = cfg.baseParamNumeric;
params.a1 = pointSpec.a1;
params.a2 = pointSpec.a2;
params.b2 = pointSpec.b2;
params.r0 = pointSpec.r0;

a = zeros(1, 5);
b = zeros(1, 5);
a(1) = params.a1;
a(2) = params.a2;
a(3) = params.a3;
a(4) = params.a4;
a(5) = params.a5;
b(1) = params.b1;
b(2) = params.b2;
b(3) = params.b3;
b(4) = params.b4;
b(5) = params.b5;

amp = ones(size(t));
for k = 1:5
    amp = amp + a(k) .* cos(k * t) + b(k) .* sin(k * t);
end
r = params.r0 .* amp;
xy = [r .* cos(t), r .* sin(t)];
end

function d = point_to_polyline_distances(points, polyline)
nPts = size(points, 1);
d = inf(nPts, 1);
for i = 1:nPts
    p = points(i, :);
    for j = 1:size(polyline, 1) - 1
        d(i) = min(d(i), point_segment_distance(p, polyline(j, :), polyline(j + 1, :)));
    end
end
end

function d = point_segment_distance(p, a, b)
ab = b - a;
den = dot(ab, ab);
if den <= eps
    d = norm(p - a);
    return;
end
t = dot(p - a, ab) / den;
t = max(0, min(1, t));
proj = a + t .* ab;
d = norm(p - proj);
end

function L = estimate_contact_length(fourierXY, shapeXY, tol)
mask = point_to_polyline_distances(fourierXY, shapeXY) <= tol;
seg = sqrt(sum(diff(fourierXY, 1, 1) .^ 2, 2));
weights = 0.5 * (double(mask(1:end-1)) + double(mask(2:end)));
L = sum(seg .* weights);
end

function tf = has_polyline_intersection(poly1, poly2)
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
    tf = true;
    return;
end
if abs(o2) < eps0 && on_segment(p1, q1, q2, eps0)
    tf = true;
    return;
end
if abs(o3) < eps0 && on_segment(p2, q2, p1, eps0)
    tf = true;
    return;
end
if abs(o4) < eps0 && on_segment(p2, q2, q1, eps0)
    tf = true;
    return;
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

function n = get_total_domain_count(model)
n = NaN;
try
    n = double(model.component('comp1').geom('geom1').getNDom);
    if isfinite(n) && n > 0
        return;
    end
catch
end
try
    intSel = mphgetselection(model.selection('geom1_int1_dom'));
    difSel = mphgetselection(model.selection('geom1_dif1_dom'));
    entities = [];
    if isfield(intSel, 'entities')
        entities = [entities; double(intSel.entities(:))];
    end
    if isfield(difSel, 'entities')
        entities = [entities; double(difSel.entities(:))];
    end
    if ~isempty(entities)
        n = numel(unique(entities));
    end
catch
end
end

function s = get_base_string(varName)
s = '';
try
    if evalin('base', sprintf('exist(''%s'',''var'')', varName))
        value = evalin('base', varName);
        if isstring(value) || ischar(value)
            s = char(string(value));
        end
    end
catch
end
end

function out = first_nonempty(a, b)
out = a;
if isempty(out)
    out = b;
end
end
