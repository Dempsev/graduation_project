function run_sweep_export_eig_v2()
    clc; clear;

    tAll = tic;

    % ====== 0) 基本配置 ======
    mphFile = "D:\graduation_project\model\amp.mph";

    stdTag   = "std1";      % 研究 tag（和中文界面“研究1”无关，tag 一般仍是 std1）
    paramTag = "param";     % 参数化扫描节点 tag（通常叫 param）
    evalTag  = "gev1";      % Derived Values / 全局评估（你显示的就是 gev1）
    tblTag   = "tbl2";      % 你要导出的特征频率表

    % 你想要的扫描范围（按需改这里）
    k_list   = "range(0, 3/(N-1), 3)";
    amp_list = "range(0.15, 0.05, 0.55)";

    outDir = "D:\graduation_project\post";
    if ~exist(outDir, "dir"); mkdir(outDir); end

    % 用时间戳防止“旧文件覆盖/没刷新”
    stamp  = string(datetime("now","Format","yyyyMMdd_HHmmss"));
    outCsv = fullfile(outDir, "eig_table_" + tblTag + "_" + stamp + ".csv");

    % ====== 1) 读模型 ======
    model = mphload(mphFile);

    % ====== 2) 修改参数扫描（关键：改 study->param 的 pname / plistarr） ======
    p = model.study(stdTag).feature(paramTag);

    % pname 必须是 Java String[]
    j_pname = toJavaStringArray({"k","amp"});

    % plistarr 必须是 Java String[]（对应 pname 的顺序）
    j_plist = toJavaStringArray({char(k_list), char(amp_list)});

    % 写回去
    p.set("pname",   j_pname);
    p.set("plistarr", j_plist);

    % （可选）确保是“所有组合”（你界面里是“所有组合”就不用动）
    % 有些模型是 p.set("pdistrib","all"); 但不同版本字段可能不同，所以不强行写

    % 打印一下，确认写进去的是 0.55
    disp("=== Sweep now set to ===");
    disp(p.getStringArray("pname"));
    disp(p.getStringArray("plistarr"));

    % ====== 3) 运行研究（计时） ======
    disp("Running parametric sweep...");
    tRun = tic;
    model.study(stdTag).run;
    fprintf("Sweep finished. run time = %.1f s\n", toc(tRun));

    % ====== 4) 强制刷新派生值/表格 ======
    % 你的日志里出现过 “Updating derived values (eig) ...”
    % 我们这里直接让 gev1 再跑一遍（如果存在）
    try
        disp("Updating derived values (gev1) ...");
        model.result.numerical(evalTag).run;
    catch
        disp("No numerical eval tag 'gev1' (or cannot run). Skip.");
    end

    % ====== 5) 导出表格 tbl2 ======
    disp("Exporting table: " + tblTag);

    % 有些版本表格需要先清空再保存（避免缓存旧内容）
    try
        model.result.table(tblTag).clearTableData;
    catch
        % 没这个方法也没关系
    end

    tExp = tic;
    model.result.table(tblTag).save(outCsv);
    fprintf("Export finished. export time = %.1f s\n", toc(tExp));
    disp("CSV saved to: " + outCsv);

    % ====== 6) 立刻验真：读回 CSV 看 amp 最大值 ======
    try
        M = readmatrix(outCsv);
        ampMax = max(M(:,2));   % 你的 CSV 前两列一般是 k, amp
        fprintf("Check: max amp in CSV = %.4f\n", ampMax);
    catch
        disp("Could not read back CSV to check ampMax. (CSV format may be non-numeric in some rows.)");
        disp("You can open CSV and check 2nd column manually.");
    end

    fprintf("ALL DONE. total time = %.1f s\n", toc(tAll));
end

% ====== 小工具：cellstr -> java.lang.String[] ======
function jArr = toJavaStringArray(c)
    jArr = javaArray("java.lang.String", numel(c));
    for i = 1:numel(c)
        jArr(i) = java.lang.String(c{i});
    end
end
