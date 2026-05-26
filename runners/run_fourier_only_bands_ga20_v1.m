function run_fourier_only_bands_ga20_v1()
bands = ["band140_180", "band160_200", "band180_220", "band200_240", "band220_260", "band240_280"];
for i = 1:numel(bands)
    fprintf('\n=== Fourier-only GA20 ablation %s (%d/%d) ===\n', char(bands(i)), i, numel(bands));
    run_fourier_only_band_ga_v1(bands(i), 20);
end
end
