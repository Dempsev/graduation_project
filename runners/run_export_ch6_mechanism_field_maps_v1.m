thisFile = mfilename('fullpath');
thisDir = fileparts(thisFile);
rootDir = fileparts(thisDir);
addpath(rootDir);
addpath(fullfile(rootDir, 'postprocess'));
addpath(fullfile(rootDir, 'model_core'));
addpath(fullfile(rootDir, 'stage2_harmonics'));
addpath(fullfile(rootDir, 'stage2_harmonics_refine'));
addpath(fullfile(rootDir, 'stage4_validation'));

export_ch6_mechanism_field_maps_v1();
