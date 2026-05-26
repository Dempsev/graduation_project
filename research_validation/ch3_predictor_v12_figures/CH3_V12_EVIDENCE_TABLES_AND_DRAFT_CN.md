# 第三章 v12 证据核对、图表路径与正文初稿

## 1. v12 数据集文件核对

| 文件路径 | 是否存在 | 行数或主要内容 | 可用于论文哪一节 | 备注 |
| --- | --- | --- | --- | --- |
| data/prediction_targetband_param_v1/v1/windows_dense_v12_all_history_ga20_clean_v1/targetband_parametric_v1.csv | 是 | 46,754 行 | 3.2 样本数据库构建；3.3 模型训练样本 | 清洗后的 v12 条件预测训练数据集 |
| data/prediction_targetband_param_v1/v1/windows_dense_v12_all_history_ga20_clean_v1/dataset_info.json | 是 | 清洗后 46,754 行；冲突物理键 57 个；GA20 有效源记录 651 条 | 3.2 数据来源与统计；图 3-1/3-2 | 数据规模、来源、清洗规则、频带统计 |
| data/prediction_targetband_param_v1/v1/windows_dense_v12_all_history_ga20_clean_v1/stacked_before_cleaning_v1.csv | 是 | 291,757 行 | 3.2 数据预处理 | 清洗前历史数据和 GA 数据堆叠记录 |
| data/prediction_targetband_param_v1/v1/windows_dense_v12_all_history_ga20_clean_v1/ga20_active_band_added_rows_v1.csv | 是 | 651 行 | 3.2 数据来源；3.5 高频段讨论 | 20 代 COMSOL 闭环 GA 的 active-band 真值 |
| data/prediction_targetband_param_v1/v1/windows_dense_v12_all_history_ga20_clean_v1/data_conflicts_resolved_v1.csv | 是 | 623 行 | 3.2 冲突处理 | 标签冲突样本审计记录 |
| data/prediction_targetband_param_v1/v1/windows_dense_v12_all_history_ga20_clean_v1/source_counts_v1.csv | 是 | 12 行 | 3.2 数据来源组成 | 各历史数据源堆叠行数 |

## 2. 字段定义核对

| 字段 | 是否存在 | 含义 | 证据位置 |
| --- | --- | --- | --- |
| physical_key | 是 | 由 point_id、shape_id、结构参数和目标频带上下限构成的物理去重键。 | 最终训练集、冲突表 |
| point_id | 是 | 结构参数采样点或设计点编号。 | 最终训练集、GA 历史 |
| shape_id | 是 | 形状轮廓或结构形状编号。 | 最终训练集、GA 历史 |
| shape_family | 是 | 形状族类别字段；未发现独立 `family` 字段。 | 最终训练集 |
| target_band_low_Hz | 是 | 目标频带下限。 | 最终训练集 |
| target_band_high_Hz | 是 | 目标频带上限。 | 最终训练集 |
| target_band_center_Hz | 是 | 目标频带中心频率。 | 最终训练集 |
| target_band_width_Hz | 是 | 目标频带宽度。 | 最终训练集 |
| target_gap_is_open | 是 | 分类标签，表示目标频带内是否存在正重叠带隙。 | 分类器训练标签 |
| target_gap_cover_ratio | 是 | 回归主标签，表示目标频带覆盖率。 | 回归器训练标签 |
| target_gap_overlap_Hz | 是 | 真实 overlap 字段；`target_overlap_Hz` 未发现。 | 用于解释覆盖率来源 |
| geometry_valid | 否/上游有 | 最终训练集未保留；原始 GA 历史 `ga_history_v1.csv` 中存在。 | GA 有效性筛选证据 |
| contact_valid | 否/上游有 | 最终训练集未保留；原始 GA 历史 `ga_history_v1.csv` 中存在。 | GA 有效性筛选证据 |
| solve_success | 否/上游有 | 最终训练集未保留；原始 GA 历史 `ga_history_v1.csv` 中存在。 | COMSOL 求解成功筛选证据 |
| source/provenance | 是 | 真实字段包括 source_dataset_version、source_record_kind、source_priority、source_dataset_versions、source_record_kinds、source_param_sample_ids、source_stage、active_learning_source_ga_history、ga20_candidate_id、data_cleaning_conflict_flag。 | 数据来源追踪与冲突审计 |


## 3.1 公式变量确认

根据真实训练标签，本章条件预测任务建议写为：

`(x, s, B) -> (p_open, c_hat)`

理由是正式回归器训练目标为 `target_gap_cover_ratio`，而不是 `target_overlap_Hz`。真实 overlap 字段名为 `target_gap_overlap_Hz`，数据集中未发现 `target_overlap_Hz`。二者关系为：

`target_gap_cover_ratio = target_gap_overlap_Hz / target_band_width_Hz`

其中 `target_band_width_Hz = target_band_high_Hz - target_band_low_Hz`。论文中可将 overlap 作为覆盖率的物理来源说明，但模型主回归输出建议记为 `c_hat`。


## 4. 模型训练、模型包与结果路径

| 文件路径 | 文件类型 | 作用 | 对应论文小节 | 备注 |
| --- | --- | --- | --- | --- |
| prediction_targetband_param_v1/tools/build_thesis_ga20_all_data_dataset_v12.py | 数据集构建脚本 | 合并历史数据与 20 代 GA active-band 真值，生成 v12 清洗数据集 | 3.2 | 已运行生成 v12 |
| prediction_targetband_param_v1/models/train_parametric_targetband_classifier_v1.py | 训练脚本 | HGB 分类器交叉验证训练入口 | 3.3/3.5 | 本次未重训 |
| prediction_targetband_param_v1/models/train_parametric_targetband_regressor_v1.py | 训练脚本 | HGB 覆盖率回归器交叉验证训练入口 | 3.3/3.5 | 本次未重训 |
| data/prediction_targetband_param_v1_runs/param_targetband_final_hgb_dense_v12_all_history_ga20_clean_v1/final_predictor_bundle.joblib | 模型包 | 全量 v12 final predictor bundle | 3.3 | 最终可调用模型 |
| data/prediction_targetband_param_v1_runs/param_targetband_cls_hgb_dense_v12_all_history_ga20_clean_v1/stratified_group_kfold | 分类器结果目录 | Family-CV 分类器 fold、预测和汇总结果 | 3.5 | 主验证依据之一 |
| data/prediction_targetband_param_v1_runs/param_targetband_cover_hgb_dense_v12_all_history_ga20_clean_v1/stratified_group_kfold | 回归器结果目录 | Family-CV 覆盖率回归 fold、预测和汇总结果 | 3.5 | 主验证依据之一 |
| data/analysis/predictor_readiness_v12_all_history_ga20_clean_v1 | readiness 汇总目录 | 六个论文目标频带过滤后的指标、Top-k 排序能力结果 | 3.5 | 第三章主表优先用这里 |
| research_validation/ch3_predictor_v12_figures/build_ch3_predictor_v12_figures.py | 绘图脚本 | 生成 7 张第三章 ch3_ PNG/SVG 图 | 3.2-3.5 | 未重训模型 |

## 5. 第三章图表路径与图题建议

| PNG 路径 | SVG 路径 | 论文图题建议 |
| --- | --- | --- |
| research_validation/ch3_predictor_v12_figures/ch3_dataset_construction_flow.png | research_validation/ch3_predictor_v12_figures/ch3_dataset_construction_flow.svg | v12 数据集构建与清洗流程示意图 |
| research_validation/ch3_predictor_v12_figures/ch3_target_band_sample_distribution.png | research_validation/ch3_predictor_v12_figures/ch3_target_band_sample_distribution.svg | 六个目标频带样本分布与平均覆盖率 |
| research_validation/ch3_predictor_v12_figures/ch3_model_structure.png | research_validation/ch3_predictor_v12_figures/ch3_model_structure.svg | 目标频带条件预测模型结构示意图 |
| research_validation/ch3_predictor_v12_figures/ch3_overall_validation_comparison.png | research_validation/ch3_predictor_v12_figures/ch3_overall_validation_comparison.svg | Family-CV 与 leave-one-band 总体验证结果对比 |
| research_validation/ch3_predictor_v12_figures/ch3_band_classification_metrics.png | research_validation/ch3_predictor_v12_figures/ch3_band_classification_metrics.svg | 六个目标频带分类性能对比 |
| research_validation/ch3_predictor_v12_figures/ch3_band_regression_mae.png | research_validation/ch3_predictor_v12_figures/ch3_band_regression_mae.svg | 六个目标频带覆盖率回归 MAE 对比 |
| research_validation/ch3_predictor_v12_figures/ch3_topk_shortlist_quality.png | research_validation/ch3_predictor_v12_figures/ch3_topk_shortlist_quality.svg | Top-k 候选排序能力对比 |

## 6. Word 可复制制表符表格

```text
1）v12 数据集构成表
项目	数量	说明
历史数据堆叠行数	291,106	历史目标频带、补充真值和主动学习版本的堆叠记录
20 代 GA 有效 COMSOL 源记录	651	通过 geometry/contact/solve 筛选后的 active-band 记录
20 代 GA 追加 active-band 记录	651	仅追加真实优化频带，不做跨频带扩展
清洗前总行数	291,757	历史数据与 GA20 active-band 数据合并后
按 physical_key 去重后总行数	46,754	第三章模型训练使用的数据集规模
重复物理键数量	46,392	重复样本审计结果
标签冲突物理键	57	已按 origin-target 一致性和来源优先级处理
唯一结构设计数	3,363	清洗后 design_id 数量
唯一形状数	286	清洗后 shape_id 数量
唯一形状族数	81	清洗后 shape_family 数量
```

```text
2）六个目标频带样本统计表
目标频带	样本数	正样本数	正样本率	最大覆盖率	平均覆盖率
140-180 Hz	1,241	1,042	0.840	0.641	0.292
160-200 Hz	1,239	1,150	0.928	0.855	0.440
180-220 Hz	1,205	909	0.754	1.000	0.185
200-240 Hz	1,242	165	0.133	0.882	0.058
220-260 Hz	1,241	886	0.714	0.278	0.020
240-280 Hz	1,242	932	0.750	0.098	0.020
```

```text
3）条件预测模型输入特征表
特征类别	代表字段	含义	处理方式
结构参数	a1, a2, b1, b2, a3, b3, a4, b4, a5, b5, r0	描述结构轮廓和几何参数化形式	数值化后直接输入模型
结构族字段	shape_id, shape_family	表示结构形状编号和结构族类别	用于分组验证和结构族感知分析
形状统计特征	shape_area, shape_perimeter, shape_compactness, shape_solidity 等	描述结构轮廓面积、周长、紧致度、凸性等	作为数值特征输入
目标频带条件	target_band_low_Hz, target_band_high_Hz, target_band_center_Hz, target_band_width_Hz	定义条件预测中的目标频带 B	作为条件变量拼接到输入特征
来源与审计字段	source_dataset_version, source_record_kind, physical_key	用于数据追踪、去重和冲突审计	不作为物理输出标签
```

```text
4）两阶段预测模型任务分工表
模型	任务	训练样本	输出标签	作用
HGB Classifier	判断目标频带内是否存在带隙重叠	46,754	target_gap_is_open / p_open	用于候选初筛
HGB Regressor	在正样本上预测目标频带覆盖率	30,716	target_gap_cover_ratio / c_hat	用于候选排序
```

```text
5）模型总体验证结果表
验证方式	分类准确率	分类F1	分类平衡准确率	覆盖率MAE	覆盖率RMSE	覆盖率R²
形状族分组 5 折	0.913	0.939	0.878	0.0468	0.0785	0.898
留一频带	0.768	0.837	0.707	0.0857	0.1265	0.737
```

```text
6）六个目标频带分类结果表
目标频带	Family-CV F1	Family-CV平衡准确率	Band-LOO F1	Band-LOO平衡准确率
140-180 Hz	0.954	0.768	0.958	0.775
160-200 Hz	0.964	0.516	0.988	0.848
180-220 Hz	0.957	0.915	0.900	0.695
200-240 Hz	0.877	0.952	0.249	0.552
220-260 Hz	0.906	0.808	0.531	0.665
240-280 Hz	0.918	0.752	0.911	0.719
```

```text
7）六个目标频带回归结果表
目标频带	Family-CV MAE	Band-LOO MAE
140-180 Hz	0.0381	0.0687
160-200 Hz	0.0528	0.0983
180-220 Hz	0.0662	0.1447
200-240 Hz	0.1384	0.0838
220-260 Hz	0.0114	0.0111
240-280 Hz	0.0099	0.0099
```

```text
8）Top-k排序能力表
验证方式	Top-5命中率	Top-5平均真实覆盖率	Top-10命中率	Top-10平均真实覆盖率
形状族分组 5 折	1.000	0.731	1.000	0.732
留一频带	1.000	0.604	1.000	0.585
```


## 第三章正文初稿

### 3 基于机器学习的目标频带条件预测模型

前两章建立了周期结构带隙分析的有限元计算基础，并明确了本文关注的目标频带优化问题。由于每一个候选结构均需要经过 COMSOL 频散计算才能获得可靠的带隙标签，若直接在大规模候选空间中反复调用有限元模型，将导致计算成本较高。为提高候选结构筛选效率，本章在 COMSOL 真实频散计算结果的基础上构建目标频带条件预测模型。需要强调的是，本章模型并不替代有限元分析，也不作为最终物理判据，而是用于在给定目标频带内对候选结构进行初步筛选和排序，为后续 COMSOL 复核及闭环遗传优化提供候选基础。

### 3.1 条件预测任务定义

本文将目标频带带隙预测写成条件预测问题。设结构参数为 x，结构族及形状描述为 s，目标频带为 B=[f_l, f_u]。模型输入由结构参数、形状统计特征和目标频带条件变量共同组成，输出包括目标频带内是否存在带隙重叠的概率 p_open，以及当带隙存在时的目标频带覆盖率预测值 c_hat。因此，本章采用的任务形式为：

    (x, s, B) -> (p_open, c_hat)

其中，p_open 对应分类标签 target_gap_is_open，c_hat 对应回归标签 target_gap_cover_ratio。数据集中同时保留 target_gap_overlap_Hz 字段，用于表示带隙与目标频带的真实重叠宽度。二者关系可理解为：target_gap_cover_ratio = target_gap_overlap_Hz / (target_band_high_Hz - target_band_low_Hz)。由于不同目标频带宽度可能不同，覆盖率能够更直接反映带隙对目标频带的相对覆盖程度，因此本文将 target_gap_cover_ratio 作为回归模型的主预测标签。

### 3.2 样本数据库构建与数据预处理

本章使用的样本数据库为 v12 版本数据集 windows_dense_v12_all_history_ga20_clean_v1。该数据集整合了历史目标频带数据、补充真值数据、主动学习数据以及 20 代 COMSOL 闭环遗传优化所得 active-band 真值。所有标签均来源于 COMSOL 频散计算或由其结果派生的目标频带重叠量，而不是由机器学习模型自行生成。

数据整理过程中，首先将不同阶段形成的历史数据集进行堆叠，并追加 20 代 GA 中通过 geometry_valid、contact_valid 和 solve_success 有效性筛选的 active-band 记录。清洗前共得到 291,757 行记录，其中 20 代 GA 有效 COMSOL 源记录为 651 条。随后，本文以 point_id、shape_id、结构参数以及目标频带上下限共同构造 physical_key，用于识别同一物理结构在不同数据版本中的重复记录。对于 physical_key 相同且标签一致的样本，仅保留一条代表记录；对于标签不一致的样本，优先保留优化来源频带与目标频带一致的 active-band 真值，并保留冲突审计记录。

经过物理键去重与冲突处理后，v12 数据集包含 46,754 条样本，覆盖 3,363 个结构设计、286 个形状以及 81 个形状族。六个论文目标频带中，160-200 Hz 的正样本率和平均覆盖率相对较高，而 220-260 Hz 与 240-280 Hz 虽然存在较多正样本，但平均覆盖率仅约 0.020，说明高频段样本多为窄带重叠，不能仅凭是否打开判断其工程可用性。

### 3.3 条件分类模型与条件回归模型构建

本章采用两阶段预测结构。第一阶段为 HGB 分类器，用于判断目标频带内是否存在带隙重叠，输出 p_open；第二阶段为 HGB 回归器，仅在 target_gap_is_open=1 的正样本上训练，用于预测目标频带覆盖率 c_hat。模型输入包括结构几何参数、形状统计特征以及目标频带条件变量，其中目标频带条件变量包括 target_band_low_Hz、target_band_high_Hz、target_band_center_Hz 和 target_band_width_Hz。

采用两阶段模型的原因在于，目标频带预测同时包含“是否存在带隙”和“带隙覆盖程度”两个层次。若直接对所有样本回归覆盖率，大量零覆盖样本会弱化模型对正样本覆盖程度差异的学习；而先分类再回归，可以分别刻画带隙打开概率和覆盖率大小。最终用于候选排序时，可将 p_open 与 c_hat 组合为候选评分，使模型优先推荐既可能打开目标带隙、又具有较高覆盖率的结构。

### 3.4 模型评价指标

分类模型采用准确率、F1 值和平衡准确率作为评价指标。其中，F1 值综合考虑精确率和召回率，适用于正负样本不完全均衡的目标频带预测；平衡准确率进一步降低类别比例差异对评价结果的影响。回归模型采用 MAE、RMSE 和 R2 评价覆盖率预测误差。

为了检验模型泛化能力，本文采用两类交叉验证方式。第一类为按形状族分组的 Family-CV，用于评价模型面对未见结构族时的预测稳定性，是本章主要可信度依据。第二类为 leave-one-band 验证，即每次留出一个目标频带进行测试，用于检验模型对目标频带条件变化的外推能力。由于 leave-one-band 比常规分组验证更严格，其性能下降不表示模型失效，而说明本文预测模型应限定在预定义目标频带设计域内使用，不应表述为任意频带的通用外推器。

### 3.5 条件预测结果与候选筛选能力分析

在六个论文目标频带上，Family-CV 分类准确率为 0.913，F1 值为 0.939，平衡准确率为 0.878；覆盖率回归 MAE 为 0.0468，R2 为 0.898。该结果表明，在当前结构族和目标频带目录内，模型能够较稳定地学习结构参数、形状特征与目标频带带隙响应之间的统计关系。

在 leave-one-band 验证中，分类 F1 为 0.837，平衡准确率为 0.707，覆盖率回归 MAE 为 0.0857，R2 为 0.737。与 Family-CV 相比，leave-one-band 结果有所下降，说明目标频带变化会增加预测难度。其中，200-240 Hz 的留一频带分类 F1 较低，220-260 Hz 和 240-280 Hz 的平均覆盖率也较低，因此这些频带的结论应结合第四章和第五章的 COMSOL 真值进一步验证。

候选排序能力方面，本文将分类概率与覆盖率预测值组合为候选评分。在 Family-CV 中，Top-5 与 Top-10 候选的命中率均为 1.000，平均真实覆盖率分别为 0.731 和 0.732；在 leave-one-band 中，Top-5 与 Top-10 候选命中率也均为 1.000，平均真实覆盖率分别为 0.604 和 0.585。该结果说明，预测模型能够在候选集中将较高覆盖率样本前置，适合作为后续有限元复核和遗传算法搜索的初筛工具。但该结果不应解释为机器学习模型可以替代 COMSOL，最终结构性能仍需通过频散计算确认。

### 3.6 本章小结

本章基于 COMSOL 频散计算结果构建了目标频带条件预测模型，并形成 v12 版本训练数据集。该数据集整合历史目标频带数据、补充真值数据、主动学习数据和 20 代 COMSOL 闭环遗传优化 active-band 真值，通过 physical_key 完成重复样本识别和冲突处理。模型采用 HGB 分类器与 HGB 回归器的两阶段结构，分别预测目标频带带隙打开概率和覆盖率。

验证结果表明，在预定义目标频带目录和当前结构参数化空间内，模型具有一定的候选筛选和排序能力，可为后续优化提供初始候选和缩小搜索空间。然而，模型本质上仍是基于已有 COMSOL 标签的统计预测器，不能替代有限元物理计算。对于高频段和留一频带性能较弱的频带，后续章节需要进一步结合 COMSOL-in-loop GA 和代表性候选结构验证结果进行分析。



## 第三章写作注意事项

### 可以作为第三章主结果

1. v12 数据集规模、数据来源整合、physical_key 去重和冲突处理结果。
2. HGB 分类器与 HGB 回归器的两阶段条件预测框架。
3. 六个论文目标频带上的 Family-CV 总体指标。
4. Top-k 候选排序能力，结论限定为“候选初筛和排序”。

### 只能作为补充说明

1. leave-one-band 结果：用于说明更严格外推检验，不宜作为模型强泛化主张。
2. 训练目录中的全 32 频带 metrics_summary：第三章主表应优先用 readiness 目录中过滤六个论文目标频带后的结果。
3. RF 900 棵树未完成全折训练的结果：只能说明曾尝试，不作为正式主结果。

### 需要避免的表述

1. 避免写“机器学习替代 COMSOL”。
2. 避免写“模型可任意预测连续频带”。
3. 避免只用 target_gap_is_open 宣称高频段优化成功。
4. 避免把 Top-k 命中率解释为最终结构真实性能。

### 需要第四章或第五章支撑的内容

1. 代表性结构的最终带隙覆盖范围和频散图。
2. 200-240 Hz、220-260 Hz、240-280 Hz 等困难频带的真实性能解释。
3. 预测器筛选候选与 COMSOL-in-loop GA 优化结果之间的对比。
4. 最终候选结构能否满足目标频带要求的物理验证。
