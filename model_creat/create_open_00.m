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

% 取出路径（getter 要加括号）
mpath = char(model.modelPath());   % 关键：括号 + char

mphfile = fullfile(mpath, 'mother_rebuild.mph');

mphsave(model, mphfile);
mphopen(mphfile);   % 在GUI里打开
