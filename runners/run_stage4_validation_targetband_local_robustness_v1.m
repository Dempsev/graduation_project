import com.comsol.model.*
import com.comsol.model.util.*

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
addpath(genpath(fullfile(rootDir, 'model_core')));
addpath(genpath(fullfile(rootDir, 'stage2')));
addpath(genpath(fullfile(rootDir, 'stage2_harmonics')));
addpath(genpath(fullfile(rootDir, 'stage2_harmonics_refine')));
addpath(genpath(fullfile(rootDir, 'stage4_validation')));

run_stage3_build_canonical_local_robustness_manifest_v1;
cfg = get_stage4_validation_config_targetband_local_robustness_v1();
run_stage4_validation_from_manifest(cfg, 1, 0);
