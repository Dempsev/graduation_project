import com.comsol.model.*
import com.comsol.model.util.*

ModelUtil.clear;
ModelUtil.showProgress(true);

model = ModelUtil.create('Model');

% 设定路径（setter）
model.modelPath('D:/graduation_project/model');
model.label('mother_rebuild');

% 设置参数
model = set_params_01(model);

% 几何
model = build_geom_02(model);

% 材料
model = set_material_03(model);

% 固体力学
model = set_physics_04(model);

% 网格
model = set_mesh_05(model);

% 研究
model = set_study_06(model);

% 结果
model = set_results_07(model);

% Get model path
mpath = char(model.modelPath());

mphfile = fullfile(mpath, 'mother_rebuild.mph');

mphsave(model, mphfile);
mphopen(mphfile);   % 在GUI里打开
