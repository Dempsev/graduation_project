% 1) 启动 COMSOL server（有的版本需要，有的可以省略）
%mphstart();

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
dataDir = fullfile(rootDir, "data");
if ~exist(dataDir, "dir"); mkdir(dataDir); end

% 2) 读入模型（把路径改成你自己的 .mph）
model = mphload(fullfile(dataDir, "amp.mph"));

% 3) 改一个参数（例如 amp）
model.param.set("amp", "0.2");

% 4) 运行研究
model.study("std1").run;

% 5) 保存（可选）
mphsave(model, fullfile(dataDir, "amp_run.mph"));
