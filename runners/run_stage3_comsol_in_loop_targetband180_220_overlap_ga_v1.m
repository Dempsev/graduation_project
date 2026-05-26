import com.comsol.model.*
import com.comsol.model.util.*

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
addpath(genpath(fullfile(rootDir, 'model_core')));
addpath(genpath(fullfile(rootDir, 'stage2')));
addpath(genpath(fullfile(rootDir, 'stage2_harmonics')));
addpath(genpath(fullfile(rootDir, 'stage2_harmonics_refine')));
addpath(genpath(fullfile(rootDir, 'optimization')));
addpath(genpath(fullfile(rootDir, 'shared')));

cfg = get_comsol_in_loop_ga_targetband180_220_overlap_config_v1();
run_comsol_in_loop_band_catalog_ga_v1(cfg);
