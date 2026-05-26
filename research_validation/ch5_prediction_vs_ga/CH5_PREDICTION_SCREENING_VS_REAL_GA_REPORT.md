# 第5章 预测筛选与真实遗传优化对比材料整理报告

## 5.1 对比实验设置与数据来源

第三章最终模型采用 v12 all-history + GA20 clean 数据集，数据文件为 `D:\graduation_project\coad\data\prediction_targetband_param_v1\v1\windows_dense_v12_all_history_ga20_clean_v1\targetband_parametric_v1.csv`，清洗后样本数为 46,754 行；最终模型包为 `D:\graduation_project\coad\data\prediction_targetband_param_v1_runs\param_targetband_final_hgb_dense_v12_all_history_ga20_clean_v1\final_predictor_bundle.joblib`。第5章比较对象包括：预测 Top-k 候选、随机候选和第4章20代真实 COMSOL-GA 基准。

本章统一采用覆盖率主线：分类标签为 `target_gap_is_open`，回归标签为 `target_gap_cover_ratio`，真实重叠宽度为 `target_gap_overlap_Hz`。输出表中统一映射为 `true_cover_ratio` 与 `true_overlap_Hz`。

## 5.2 数据独立性与 physical_key 重叠审计

审计表见 `ch5_physical_key_overlap_audit.csv/md`。预测 Top-k 与 v12 训练集 physical_key 重叠数量为 240，与 GA20 历史重叠数量为 170；随机候选与 v12 训练集重叠数量为 240。

由于本次 predicted_topk 与 random 均从 v12 已清洗候选池中整理，strict_holdout 口径下独立候选数量不足。第5章主要结果应采用 `engineering_screening` 口径，strict_holdout 仅作为数据独立性审计参考。

strict_holdout 各频带剩余样本数：

| target_band | strict_holdout_n |
| --- | ---: |
| 140–180 Hz | 0 |
| 160–200 Hz | 0 |
| 180–220 Hz | 0 |
| 200–240 Hz | 0 |
| 220–260 Hz | 0 |
| 240–280 Hz | 0 |

## 5.3 预测 Top-k 候选筛选结果分析

Top-k 统计表见 `ch5_topk_validation_summary.csv/md`。在 engineering_screening 口径下，预测候选按照 `predicted_score = predicted_open_prob × predicted_cover_ratio` 排序，并同时报告真实覆盖率与真实重叠宽度。

## 5.4 随机候选与预测候选对比

统一候选对比表见 `ch5_unified_candidate_comparison.csv/md`。图5-2比较预测 Top-k 与随机候选有效率，图5-3和图5-4分别比较最优重叠宽度与最优覆盖率。

## 5.5 预测候选与真实 GA 基准对比

真实 GA 基准严格采用第4章20代结果，不回退到12代。图5-5给出 Top-k 预算下预测候选达到 GA 最优的比例，分别按重叠宽度和覆盖率计算。

## 5.6 验证预算效率分析

图5-6与图5-7分别给出预算-历史最优重叠宽度曲线和预算-历史最优覆盖率曲线。由于 predicted_topk/random 的 v12 真值并非新独立验证，预算效率表述应限定为工程筛选复盘，不宜写成严格泛化验证。

## 5.7 典型目标频带案例分析

图5-9整理了 180–220 Hz、200–240 Hz、240–280 Hz 三个典型频带下 predicted_topk、random、real_ga 的最优结构轮廓对比；图5-10引用第4章真实 GA 代表频带频散曲线。

## 5.8 高频困难频带与方法边界分析

图5-11显示 220–260 Hz 与 240–280 Hz 在三类方法下的最优覆盖率均明显低于中频段，说明高频困难更可能来自当前结构族与参数空间的可达性限制，而不只是排序模型本身。

## 5.9 本章小结

1. v12 最终模型可用于工程筛选排序，但第5章必须显式标注候选是否已见于训练数据或GA20历史。
2. 本章统一采用 `true_cover_ratio` 与 `true_overlap_Hz` 双指标，避免只看重叠宽度造成解释偏差。
3. 第4章20代真实 GA 是本章真实优化基准，不能再使用旧12代结果。
4. strict_holdout 样本不足时，应把其作为审计结果，而不是伪造独立验证结论。
5. 高频目标频带的低覆盖率提示后续应优先扩展结构族或参数化机制。

## 图件清单

- `ch5_fig5_1_comparison_workflow`: `ch5_fig5_1_comparison_workflow.png`, `ch5_fig5_1_comparison_workflow.svg`, `ch5_fig5_1_comparison_workflow.pdf`
- `ch5_fig5_2_topk_random_active_rate`: `ch5_fig5_2_topk_random_active_rate.png`, `ch5_fig5_2_topk_random_active_rate.svg`, `ch5_fig5_2_topk_random_active_rate.pdf`
- `ch5_fig5_3_best_overlap_compare`: `ch5_fig5_3_best_overlap_compare.png`, `ch5_fig5_3_best_overlap_compare.svg`, `ch5_fig5_3_best_overlap_compare.pdf`
- `ch5_fig5_4_best_cover_compare`: `ch5_fig5_4_best_cover_compare.png`, `ch5_fig5_4_best_cover_compare.svg`, `ch5_fig5_4_best_cover_compare.pdf`
- `ch5_fig5_5_topk_to_ga_ratio`: `ch5_fig5_5_topk_to_ga_ratio.png`, `ch5_fig5_5_topk_to_ga_ratio.svg`, `ch5_fig5_5_topk_to_ga_ratio.pdf`
- `ch5_fig5_6_budget_best_overlap_curve`: `ch5_fig5_6_budget_best_overlap_curve.png`, `ch5_fig5_6_budget_best_overlap_curve.svg`, `ch5_fig5_6_budget_best_overlap_curve.pdf`
- `ch5_fig5_7_budget_best_cover_curve`: `ch5_fig5_7_budget_best_cover_curve.png`, `ch5_fig5_7_budget_best_cover_curve.svg`, `ch5_fig5_7_budget_best_cover_curve.pdf`
- `ch5_fig5_8_physical_key_overlap_audit`: `ch5_fig5_8_physical_key_overlap_audit.png`, `ch5_fig5_8_physical_key_overlap_audit.svg`, `ch5_fig5_8_physical_key_overlap_audit.pdf`
- `ch5_fig5_9_typical_unit_cell_compare`: `ch5_fig5_9_typical_unit_cell_compare.png`, `ch5_fig5_9_typical_unit_cell_compare.svg`, `ch5_fig5_9_typical_unit_cell_compare.pdf`
- `ch5_fig5_10_typical_dispersion_compare`: `ch5_fig5_10_typical_dispersion_compare.png`, `ch5_fig5_10_typical_dispersion_compare.svg`, `ch5_fig5_10_typical_dispersion_compare.pdf`
- `ch5_fig5_11_highfreq_boundary_analysis`: `ch5_fig5_11_highfreq_boundary_analysis.png`, `ch5_fig5_11_highfreq_boundary_analysis.svg`, `ch5_fig5_11_highfreq_boundary_analysis.pdf`