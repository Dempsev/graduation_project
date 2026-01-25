% LEGACY: retained for reference; not part of current runner workflow.
%% run_sweep_export_eig.m
clear; clc;

% 如果你已经启动并连接了 server（控制台显示已登录），这里可以注释
% mphstart();

tAll = tic;

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(fileparts(thisDir));
dataDir = fullfile(rootDir, "data");
if ~exist(dataDir, "dir"); mkdir(dataDir); end

model = mphload(fullfile(dataDir, "amp.mph"));

% ===== 1) 设置参数化扫描列表（改 study->param）=====
stdTag   = "std1";
paramTag = "param";

k_list   = "range(0, 3/(N-1), 3)";
amp_list = "range(0.15, 0.05, 0.25)";

p = model.study(stdTag).feature(paramTag);

% --- 读出 Java String[] ---
j_pname = p.getStringArray("pname");
j_plist = p.getStringArray("plistarr");

pname = cell(1, length(j_pname));
plist = cell(1, length(j_plist));

for i = 1:length(j_pname)
    pname{i} = char(j_pname(i));
    plist{i} = char(j_plist(i));
end

% 找到 k 和 amp 位置
ik   = find(strcmp(pname, "k"), 1);
iamp = find(strcmp(pname, "amp"), 1);

plist{ik}   = k_list;
plist{iamp} = amp_list;

% --- 写回：cell -> Java String[] ---
j_new = javaArray('java.lang.String', numel(plist));
for i = 1:numel(plist)
    j_new(i) = java.lang.String(plist{i});
end
p.set("plistarr", j_new);

% ===== 2) 运行 study（计时）=====
disp("Running parametric sweep...");
tRun = tic;
model.study(stdTag).run;
fprintf("Sweep finished. run time = %.1f s\n", toc(tRun));
% ===== 2.5) 刷新派生值，更新 tbl2 内容（关键！）=====
disp("Updating derived values (eig) ...");
model.result.numerical("gev1").run;   % 如果你的 tag 不是 eig，看下面怎么查


% ===== 3) 导出特征频率表（只导 CSV）=====
outDir = fullfile(dataDir, "post");
if ~exist(outDir, 'dir'); mkdir(outDir); end

tblTag = "tbl2"; % 需要的话换 tbl1
outCsv = fullfile(outDir, "eig_table_" + tblTag + ".csv");

disp("Exporting table: " + tblTag);
tExp = tic;
model.result.table(tblTag).save(outCsv);
fprintf("Export finished. export time = %.1f s\n", toc(tExp));

fprintf("ALL DONE. total time = %.1f s\n", toc(tAll));
disp("CSV saved to: " + outCsv);

