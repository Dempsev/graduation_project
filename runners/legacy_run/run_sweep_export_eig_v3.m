% LEGACY: retained for reference; not part of current runner workflow.
%% run_sweep_export_eig_fix.m
clear; clc;

% 如果你已经连上 server（控制台显示已登录），mphstart() 继续注释
% mphstart();

tAll = tic;

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(fileparts(thisDir));
dataDir = fullfile(rootDir, "data");
if ~exist(dataDir, "dir"); mkdir(dataDir); end

model = mphload(fullfile(dataDir, "amp.mph"));

% ===== 1) 改参数化扫描（study->param）=====
stdTag   = "std1";
paramTag = "param";

k_list   = "range(0, 3/(N-1), 3)";
amp_list = "range(0.15, 0.05, 0.25)";   % <<< 先用 0.25 验证，之后再改 0.55

p = model.study(stdTag).feature(paramTag);

% 读出 Java String[]
j_pname = p.getStringArray("pname");
j_plist = p.getStringArray("plistarr");

pname = cell(1, length(j_pname));
plist = cell(1, length(j_plist));
for i = 1:length(j_pname)
    pname{i} = char(j_pname(i));
    plist{i} = char(j_plist(i));
end

ik   = find(strcmp(pname, "k"), 1);
iamp = find(strcmp(pname, "amp"), 1);

plist{ik}   = k_list;
plist{iamp} = amp_list;

% 写回：cell -> Java String[]
j_new = javaArray('java.lang.String', numel(plist));
for i = 1:numel(plist)
    j_new(i) = java.lang.String(plist{i});
end
p.set("plistarr", j_new);

% 打印确认（你截图里那段）
disp("=== Sweep now set to ===");
disp(p.getStringArray("pname"));
disp(p.getStringArray("plistarr"));

% ===== 2) 跑 study（计时）=====
disp("Running parametric sweep...");
tRun = tic;
model.study(stdTag).run;
fprintf("Sweep finished. run time = %.1f s\n", toc(tRun));

% ===== 3) 找“最新的数据集 dsetX”，强制 gev1 / tbl2 用它 =====
% 关键：你的 tbl2 很可能还挂在旧 dset 上，所以永远是 0.45
j_dset = model.result.dataset.tags();
dsetTags = cell(1, length(j_dset));
for i = 1:length(j_dset)
    dsetTags{i} = char(j_dset(i));
end

% 一般“最后一个”就是刚算完生成/更新的那个（最稳的通用策略）
latestDset = dsetTags{end};
disp("Latest dataset tag guess = " + string(latestDset));

% ===== 4) 刷新派生值：让 gev1 重新把结果写进 tbl2 =====
gevTag = "gev1";
tblTag = "tbl2";

disp("Updating derived values (gev1) and refreshing tbl2 ...");

% 4.1 清空 tbl2 的旧缓存（非常关键！）
try
    model.result.table(tblTag).clearTableData();
catch
    % 有些版本方法名略不同，没关系，继续往下
end

% 4.2 强制 gev1 指向最新 dataset，并把输出表指定为 tbl2
gev = model.result.numerical(gevTag);

% gev.set('solnum','all') 你之前报错“只支持常量表达式”，所以这里不碰它
% 我们只把 dataset/data 指到最新的
try
    gev.set("data", latestDset);
catch
    try
        gev.set("dataset", latestDset);
    catch
        % 如果两个都不支持，就先不设（少数模型），但大多数 6.3 是支持 data 的
    end
end

try
    gev.set("table", tblTag);
catch
    % 如果 gev1 本来就绑定 tbl2，这句失败也不影响
end

% 4.3 运行 gev1，把新 sweep 的结果真正写进 tbl2
tG = tic;
gev.run;
fprintf("Derived values updated. time = %.1f s\n", toc(tG));

% ===== 5) 导出 tbl2 =====
outDir = fullfile(dataDir, "post");
if ~exist(outDir, 'dir'); mkdir(outDir); end

stamp = string(datetime('now','Format','yyyyMMdd_HHmmss'));
outCsv = fullfile(outDir, "eig_table_" + tblTag + "_" + stamp + ".csv");

disp("Exporting table: " + tblTag);
tExp = tic;
model.result.table(tblTag).save(outCsv);
fprintf("Export finished. export time = %.1f s\n", toc(tExp));

fprintf("ALL DONE. total time = %.1f s\n", toc(tAll));
disp("CSV saved to: " + outCsv);

% ===== 6) 小自检：读 CSV 第二列最大值（你现在就是卡在这里）=====
try
    T = readtable(outCsv, 'VariableNamingRule','preserve');
    col2 = T{:,2};
    col2 = col2(isfinite(col2));
    if isempty(col2)
        disp("Check: max amp in CSV (col2) = NaN (empty/invalid col2)");
    else
        fprintf("Check: max amp in CSV (col2) = %.4f\n", max(col2));
    end
catch ME
    disp("CSV check skipped: " + string(ME.message));
end
