# 论文图表整理索引

本索引用于配合 `docs/THESIS_RESCUE_REVISION_PLAN_CN.md` 修改论文。当前已将分散图表复制到统一目录：

`D:\graduation_project\论文图表\2026-05-05_论文急救整理`

该目录下主要包含：

- `by_chapter/`：从 `data/analysis/thesis_ch*_v1` 复制出的章节图表。
- `output_doc_thesis_figures/`：从 `output/doc/thesis_figures` 复制出的增强版图表。
- `ch6_core_from_output_thesis_charts/`：从 `output/thesis_charts/chapter6` 复制出的第六章核心图。
- `pdf_inventory/current_pdf_figure_table_mentions.txt`：从当前 PDF 抽取出的图表标题和引用片段。
- `asset_file_manifest.csv`：本次归档目录下全部文件清单。

## 一、当前 PDF 图表问题

从 `output/doc/total (5).pdf` 抽取到的问题：

- 当前 PDF 共 70 页。
- 第一章到第八章都有图表，整体数量偏多。
- 存在图名缺失或过空：`图 1-1`、`图 6-14`。
- 第六章存在旧编号引用残留：正文仍提到 `图 6-3`、`图 6-4`、`图 6-5`，但附近实际图号已变成 `图 6-8`、`图 6-10`、`图 6-12`。
- 当前表 `6-2(a)`、`6-2(b)`、`6-2(c)` 建议拆成独立表号。

## 二、建议正文保留图表

按六章重构后，正文图表建议控制如下。

### 第一章

保留 1 张图、1 张表以内：

- 图 1-1 目标频带条件预测与预测驱动逆向设计总体流程
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch1_v1\figures\figure_1_1_overall_framework.png`
- 表 1-1 研究问题与验证证据对应关系
  可由当前 `table_1_1_contribution_map.md` 改写，不建议保留“章节支撑”式表述。

### 第二章

保留 2 张图、2 张表：

- 图 2-1 目标频带逆向设计问题定义与边界
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch2_v1\figures\figure_2_1_problem_boundary.png`
- 图 2-2 物理真值生成与目标频带标签构建流程
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch3_v1\figures\图3-2_物理真值生产与Stage4验证回流流程.pptx` 或当前 PDF 中对应图重画。
- 表 2-1 目标频带目录
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch3_v1\tables\table_3_1_thesis_band_catalog_stats.md`
- 表 2-2 监督标签与评价指标定义
  由当前第三章 `表 3-4` 改写。

### 第三章

保留 4 张图、2 张表：

- 图 3-1 条件预测任务定义
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch4_v1\figures\figure_4_1_conditional_prediction_task.png`
- 图 3-2 family-CV 条件预测结果
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch4_v1\figures\figure_4_3_family_cv_bandwise_detail.png`
- 图 3-3 leave-one-band 条件预测结果
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch4_v1\figures\figure_4_5_leave_one_band_detail.png`
- 图 3-4 top-k 候选质量与校准关系
  推荐从 `figure_4_6_family_cv_shortlist_quality.png`、`figure_4_9_leave_one_band_shortlist_quality.png` 和校准图中合并重画。
- 表 3-1 模型训练配置
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch4_v1\tables\table_4_1_training_config.md`
- 表 3-2 条件预测核心指标汇总
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch4_v1\tables\table_4_2_predictor_readiness_core_metrics.md`

### 第四章

保留 3 张图、1 张表：

- 图 4-1 预测驱动目标频带逆向设计流程
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch5_v1\figures\figure_5_1_inverse_design_workflow.png`
- 图 4-2 候选评分与局部精修流程
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch5_v2\figures\figure_5_5_seed_scoring_rank_curve_v2.png` 与 `figure_5_6_local_refinement_improvement_v2.png`
- 图 4-3 验证清单与 COMSOL 数据交接
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch5_v1\figures\figure_5_4_validation_manifest_contract.png`
- 表 4-1 预测驱动逆向设计流程步骤
  可由当前 `table_5_2_workflow_artifacts.md` 改写，删除代码路径列或移入附录。

### 第五章

保留 7-9 张图、4-5 张表：

- 图 5-1 实验设置与验证逻辑
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch6_v1\figures\figure_6_1_predictor_readiness.png` 或重新绘制证据链图。
- 图 5-2 典型案例局部精修前后覆盖率对比
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch6_v1\figures\figure_6_2_canonical_cases.png`
- 图 5-3 基线方法对比结果
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch6_v1\figures\figure_6_3_baseline_comparison.png`
- 图 5-4 典型结构原型的物理场分布
  推荐源文件：`D:\graduation_project\coad\data\analysis\ch6_mechanism_field_maps_v1\ch6_field_maps_contact_sheet_v1.png`
- 图 5-5 弱频带候选筛选与覆盖能力
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch6_v1\figures\figure_6_4_weak_band_dashboard.png`
- 图 5-6 Stage4 真实验证漏斗
  推荐源文件：`D:\graduation_project\coad\output\doc\thesis_figures\fig6_stage4_validation_funnel.png`
- 图 5-7 Stage4 真实验证结果汇总
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch6_v1\figures\figure_6_5_stage4_validation.png`
- 图 5-8 局部鲁棒性分析
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch6_v1\figures\figure_6_6_local_robustness.png`

表格：

- 表 5-1 实验线与对照方法设置
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch6_v1\tables\table_6_1_experiment_lines.md`
- 表 5-2 典型案例结构信息
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch6_v1\tables\table_6_2_canonical_cases.md`
- 表 5-3 基线方法对比汇总
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch6_v1\tables\table_6_3_baseline_comparison.md`
- 表 5-4 Stage4 真实验证汇总
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch6_v1\tables\table_6_4_stage4_validation.md`
- 表 5-5 局部鲁棒性汇总
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch6_v1\tables\table_6_5_local_robustness_summary.md`

### 第六章

不建议放太多图表。最多保留 1 张总结图或 1 张展望表：

- 图 6-1 全文工作总结与后续扩展方向
  推荐源文件：`D:\graduation_project\coad\data\analysis\thesis_ch8_v1\figures\figure_8_1_conclusion_roadmap.png`
- 表 6-1 工作不足与后续改进方向
  可由 `table_7_1_scope_and_limitations.md` 和 `table_8_1_conclusion_and_future_work.md` 合并。

## 三、建议删除或移入附录的图表

以下图表更像内部工程记录，正文不宜过多出现：

- 代码入口与路径对应表。
- validation manifest 字段全量表。
- 每个历史阶段的完整路径表。
- 过细的 family-CV/leave-one-band 分图。
- 深层原始场图、单个扰动样本图。
- 旧版 v10/v11/ga_v1 路线细节图。

附录可以保留：

- 运行入口和输出路径。
- manifest 字段契约。
- 详细逐 band 指标。
- 典型案例更多场图。

## 四、当前归档目录说明

归档目录：

`D:\graduation_project\论文图表\2026-05-05_论文急救整理`

建议使用方式：

1. 写正文时优先从 `by_chapter/` 找对应章节图表。
2. 如果需要更像论文图的重画版，先看 `output_doc_thesis_figures/`。
3. 第五章结果图优先看 `by_chapter/thesis_ch6_v1/figures/` 和 `ch6_core_from_output_thesis_charts/`。
4. 不要直接从深层 `data/ml_runs/`、`data/comsol_batch/` 插图，除非确实需要补充原始证据。

## 五、待重画清单

优先重画：

1. 图 1-1 总体流程图：去掉英文模块堆叠，改成中文五步流程。
2. 图 2-1 问题定义图：明确输入、预测输出、验证输出。
3. 图 3-4 top-k 与校准图：合并 family-CV 和 leave-one-band，减少图数。
4. 图 4-2 候选评分与局部精修图：不要只放分数曲线，补充流程含义。
5. 图 5-1 实验设置与验证逻辑图：从“证据链口号”改成“实验问题-指标-证据”。
6. 图 5-6/5-7 Stage4 验证图：坐标和标签全部中文化，说明 submitted、geometry-valid、contact-valid、solved、positive gain 的含义。

可以暂不重画：

- 典型案例覆盖率对比图。
- baseline comparison 汇总图。
- weak-band dashboard。
- local robustness overview。
