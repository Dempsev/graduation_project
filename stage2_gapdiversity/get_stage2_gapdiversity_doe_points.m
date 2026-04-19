function doeTable = get_stage2_gapdiversity_doe_points(cfg)
%GET_STAGE2_GAPDIVERSITY_DOE_POINTS Random exploration in amplitude/phase space with guardrails.

rng(cfg.randomSeed, 'twister');
rows = struct([]);
accepted = 0;
attempt = 0;

while accepted < cfg.sampleTarget && attempt < cfg.maxAttempts
    attempt = attempt + 1;
    point = sample_point(cfg, attempt);
    if ~point.guardrail_pass
        continue;
    end
    accepted = accepted + 1;
    point.point_id = string(sprintf('pt%04d', accepted));
    if isempty(rows)
        rows = point;
    else
        rows(end + 1) = point; %#ok<AGROW>
    end
end

if accepted < cfg.sampleTarget
    warning('get_stage2_gapdiversity_doe_points:Underfilled', ...
        'Accepted %d/%d guardrail-valid points after %d attempts.', ...
        accepted, cfg.sampleTarget, attempt);
end

if isempty(rows)
    doeTable = struct2table(make_empty_row(cfg), 'AsArray', true);
    doeTable(1, :) = [];
else
    doeTable = struct2table(rows, 'AsArray', true);
end

doeTable = doeTable(:, cfg.doeFieldOrder);
writetable(doeTable, cfg.doeManifestCsv);
end

function row = sample_point(cfg, attempt)
phis = 2 * pi * rand(1, 5);
amps = zeros(1, 5);
for k = 1:5
    lo = cfg.AmplitudeRanges(k, 1);
    hi = cfg.AmplitudeRanges(k, 2);
    amps(k) = lo + (hi - lo) * rand();
end
r0 = cfg.r0Range(1) + (cfg.r0Range(2) - cfg.r0Range(1)) * rand();

[aVals, bVals] = amplitude_phase_to_coeffs(amps, phis);
[sumA, derivBudget, minRadius, maxRadius, maxAbsAmpSlope, minAmp, guardrailPass] = evaluate_guardrails(cfg, r0, aVals, bVals, amps);

row = struct( ...
    'point_id', string(sprintf('attempt%05d', attempt)), ...
    'r0', r0, ...
    'A1', amps(1), 'phi1', phis(1), ...
    'A2', amps(2), 'phi2', phis(2), ...
    'A3', amps(3), 'phi3', phis(3), ...
    'A4', amps(4), 'phi4', phis(4), ...
    'A5', amps(5), 'phi5', phis(5), ...
    'a1', aVals(1), 'b1', bVals(1), ...
    'a2', aVals(2), 'b2', bVals(2), ...
    'a3', aVals(3), 'b3', bVals(3), ...
    'a4', aVals(4), 'b4', bVals(4), ...
    'a5', aVals(5), 'b5', bVals(5), ...
    'sumA', sumA, ...
    'deriv_budget', derivBudget, ...
    'min_radius_est', minRadius, ...
    'max_radius_est', maxRadius, ...
    'max_abs_amp_slope', maxAbsAmpSlope, ...
    'guardrail_pass', logical(guardrailPass && minAmp >= cfg.guardrails.minAmp) ...
);
end

function [aVals, bVals] = amplitude_phase_to_coeffs(amps, phis)
aVals = amps .* cos(phis);
bVals = amps .* sin(phis);
end

function [sumA, derivBudget, minRadius, maxRadius, maxAbsAmpSlope, minAmp, ok] = evaluate_guardrails(cfg, r0, aVals, bVals, amps)
t = linspace(0, 2 * pi, cfg.thetaSampleCount + 1)';
amp = ones(size(t));
ampSlope = zeros(size(t));
for k = 1:5
    amp = amp + aVals(k) .* cos(k * t) + bVals(k) .* sin(k * t);
    ampSlope = ampSlope + (-k * aVals(k)) .* sin(k * t) + (k * bVals(k)) .* cos(k * t);
end

sumA = sum(amps);
derivBudget = sum((1:5) .* amps);
minAmp = min(amp);
minRadius = r0 * minAmp;
maxRadius = r0 * max(amp);
maxAbsAmpSlope = max(abs(ampSlope));

ok = sumA <= cfg.guardrails.maxAmpBudget && ...
    minRadius >= cfg.guardrails.minRadius && ...
    maxRadius <= cfg.guardrails.maxRadius && ...
    maxAbsAmpSlope <= cfg.guardrails.maxAbsAmpSlope;
end

function row = make_empty_row(cfg)
row = struct();
for i = 1:numel(cfg.doeFieldOrder)
    fieldName = cfg.doeFieldOrder{i};
    switch fieldName
        case {'point_id'}
            row.(fieldName) = string("");
        case {'guardrail_pass'}
            row.(fieldName) = false;
        otherwise
            row.(fieldName) = NaN;
    end
end
end
