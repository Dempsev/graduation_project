function baselineRef = evaluate_baseline_reference(cfg)
%EVALUATE_BASELINE_REFERENCE Compute or reuse the trusted no-snake baseline.

if cfg.reuseBaseline && isfile(cfg.baselineMat)
    loaded = load(cfg.baselineMat, 'baselineRef');
    if isfield(loaded, 'baselineRef') && isstruct(loaded.baselineRef)
        candidate = loaded.baselineRef;
        if isfield(candidate, 'config_signature') && strcmp(candidate.config_signature, cfg.configSignature)
            if ~isfile(cfg.baselineCsv)
                baselineResult = evaluate_single_shape(cfg, '', struct());
                if baselineResult.solve_success
                    write_baseline_csv(cfg.baselineCsv, baselineResult);
                end
            end
            baselineRef = candidate;
            fprintf('Reusing baseline reference: %s\n', cfg.baselineMat);
            return;
        end
    end
end

fprintf('Computing baseline reference for %s\n', cfg.fourierId);
baselineResult = evaluate_single_shape(cfg, '', struct());
if ~baselineResult.solve_success
    error('evaluate_baseline_reference:BaselineFailed', ...
        'Baseline solve failed: %s', baselineResult.error_message);
end

baselineRef = struct( ...
    'config_signature', cfg.configSignature, ...
    'sample_id', baselineResult.sample_id, ...
    'fourier_id', baselineResult.fourier_id, ...
    'gap_target_Hz', baselineResult.gap_target_Hz, ...
    'gap_target_rel', baselineResult.gap_target_rel, ...
    'gap_lower_band', baselineResult.gap_lower_band, ...
    'gap_upper_band', baselineResult.gap_upper_band, ...
    'gap_center_freq', baselineResult.gap_center_freq ...
);

save(cfg.baselineMat, 'baselineRef');
write_baseline_csv(cfg.baselineCsv, baselineResult);
end

function write_baseline_csv(csvPath, baselineResult)
tableRow = struct2table(baselineResult, 'AsArray', true);
fields = tableRow.Properties.VariableNames;
preferred = { ...
    'sample_id', 'fourier_id', 'shape_id', 'a1', 'a2', 'b1', 'b2', ...
    'a3', 'b3', 'r0', 'shift', 'neigs', 'material_case', ...
    'geometry_valid', 'contact_valid', 'contact_length', 'n_domains', ...
    'has_tiny_fragments', 'solve_success', 'gap_target_Hz', ...
    'gap_target_rel', 'gap_lower_band', 'gap_upper_band', ...
    'gap_center_freq', 'gap_gain_Hz', 'gap_gain_rel', ...
    'is_positive_shape', 'error_message' ...
};
keep = preferred(ismember(preferred, fields));
tableRow = tableRow(:, keep);
writetable(tableRow, csvPath);
end


