import com.comsol.model.*
import com.comsol.model.util.*

% Ensure this folder is on the path so dependencies resolve from any CWD.
thisDir = fileparts(mfilename('fullpath'));
if ~isempty(thisDir)
    addpath(thisDir);
end
rootDir = fileparts(thisDir);
dataDir = fullfile(rootDir, 'data');
if ~exist(dataDir, 'dir'); mkdir(dataDir); end

ModelUtil.clear;
ModelUtil.showProgress(true);

model = ModelUtil.create('Model');

% Model path and label
model.modelPath(dataDir);
model.label('mother_rebuild');

% Parameters
model = set_params_01(model);

% Geometry
model = build_geom_02(model);

% Materials
model = set_material_03(model);

% Physics
model = set_physics_04(model);

% Mesh
model = set_mesh_05(model);

% Run compute before results (ensure parametric solution exists)
model = set_study_06(model);
model.batch('p2').run('compute');

% Results (create after compute)
model = set_results_07(model);

% Save only; open manually if needed
mpath = char(model.modelPath());
mphfile = fullfile(mpath, 'mother_rebuild.mph');
mphsave(model, mphfile);
