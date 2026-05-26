scriptDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(fileparts(scriptDir));
run(fullfile(rootDir, 'runners', 'run_fourier_only_band_ga_v1.m'));
