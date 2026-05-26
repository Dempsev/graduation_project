function run_stage3_comsol_in_loop_thesis_band_overlap_ga_v1(bandTag, maxGenerations)
import com.comsol.model.*
import com.comsol.model.util.*

if nargin < 1 || strlength(string(bandTag)) == 0
    bandTag = "band180_220";
end
if nargin < 2 || isempty(maxGenerations)
    maxGenerations = 8;
end

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
addpath(genpath(fullfile(rootDir, 'model_core')));
addpath(genpath(fullfile(rootDir, 'stage2')));
addpath(genpath(fullfile(rootDir, 'stage2_harmonics')));
addpath(genpath(fullfile(rootDir, 'stage2_harmonics_refine')));
addpath(genpath(fullfile(rootDir, 'optimization')));
addpath(genpath(fullfile(rootDir, 'shared')));

cfg = get_comsol_in_loop_ga_thesis_band_overlap_config_v1(bandTag, maxGenerations);
run_comsol_in_loop_band_catalog_ga_v1(cfg);
end
