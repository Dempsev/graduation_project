scriptDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(fileparts(scriptDir));
run(fullfile(rootDir, 'runners', 'run_fourier_only_bands_ga20_v1.m'));
