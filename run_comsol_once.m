% 1) 启动 COMSOL server（有的版本需要，有的可以省略）
%mphstart();   

% 2) 读入模型（把路径改成你自己的 .mph）
model = mphload("D:\graduation_project\model\amp.mph");

% 3) 改一个参数（例如 amp）
model.param.set("amp", "0.2");

% 4) 运行研究
model.study("std1").run;

% 5) 保存（可选）
mphsave(model, "D:\graduation_project\model\amp_run.mph");