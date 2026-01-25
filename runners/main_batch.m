import com.comsol.model.*
import com.comsol.model.util.*

thisDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(thisDir);
addpath(genpath(fullfile(rootDir, 'model_core')));
dataDir = fullfile(rootDir, 'data');
if ~exist(dataDir, 'dir'); mkdir(dataDir); end

ModelUtil.clear;
ModelUtil.showProgress(true);

% ========= 路径（建议用可写�?work 副本�?========
mph_src = fullfile(dataDir, "mother.mph");
out_dir = fullfile(dataDir, "batch_out");
if ~exist(out_dir,'dir'); mkdir(out_dir); end
mph_in = fullfile(out_dir, "mother_work.mph");
if ~exist(mph_in, 'file'); copyfile(mph_src, mph_in); end

model = mphload(mph_in);

% ========= 你需要确认的 4 �?tag =========
stdTag  = "std1";     % 研究
gevTag  = "gev1";     % 全局计算 (Global Evaluation)
tblTag  = "tbl1";     % 表格
dsetTag = "dset4";    % 数据集：参数化解 (solxx) 对应�?Data Set

% ========= �?try-catch 检�?tag 是否存在（别�?.has�?========
try model.study(stdTag);  catch, error("找不�?study: "+stdTag); end
try model.result.numerical(gevTag); catch, error("找不�?全局计算: "+gevTag); end
try model.result.table(tblTag);     catch, error("找不�?表格: "+tblTag); end
try model.result.dataset(dsetTag);  catch, error("找不�?数据�? "+dsetTag); end

% ========= 强制绑定：gev -> tbl + 指定数据�?=========
model.result.numerical(gevTag).set("table", tblTag);
model.result.numerical(gevTag).set("data",  dsetTag);

% ========= Parametric sweep in study (k + a1) =========
fprintf("=== Running parametric sweep (k + a1) ===\n");

% Run study once; sweep handles k and a1
model.study(stdTag).run;

% Keep dataset parameter/eigenmode selection intact; only update solution tag if needed
try
    solTags = cell(model.sol.tags);
    solTags = cellfun(@char, solTags, "UniformOutput", false);
    lastSol = solTags{end};
    curSol = model.result.dataset(dsetTag).getString("solution");
    if ~strcmp(curSol, lastSol)
        model.result.dataset(dsetTag).set("solution", lastSol);
    end
catch
end

% Clear table data (optional)
try
    model.result.table(tblTag).clearTableData();
catch
    try
        model.result.table(tblTag).clearTable();
    catch
    end
end

% Build a fresh global evaluation/table to avoid hidden GUI settings
tmpGev = "gev_tmp";
tmpTbl = "tbl_tmp";
try model.result.numerical.remove(tmpGev); catch, end
try model.result.table.remove(tmpTbl); catch, end
model.result.table.create(tmpTbl, "Table");
model.result.numerical.create(tmpGev, "EvalGlobal");
exprArr = javaArray("java.lang.String", 1);
exprArr(1) = java.lang.String("freq");
model.result.numerical(tmpGev).set("expr", exprArr);
model.result.numerical(tmpGev).set("data", dsetTag);
model.result.numerical(tmpGev).set("table", tmpTbl);

model.result.numerical(tmpGev).run;
T = mphtable(model, tmpTbl);
csv_name = fullfile(out_dir, "band_k_a1.csv");

if isempty(T) || ~isfield(T,"data") || isempty(T.data)
    warning("table is still empty. Check expression and dataset binding.");
    writematrix([], csv_name);
else
    writematrix(T.data, csv_name);
end

fprintf("Saved: %s  (rows=%d, cols=%d)\n", csv_name, size(T.data,1), size(T.data,2));

% Optional: save a temp model for inspection
mphsave(model, fullfile(out_dir, "tmp.mph"));

disp("Batch finished.");
