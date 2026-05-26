# 第5章 strict_holdout 小规模独立验证补充报告

## 1. 实验目的

原第5章 engineering_screening 结果中，预测候选和随机候选均来自 v12 已清洗候选池，strict_holdout 样本不足。因此本补充实验重新构建未见候选集，并用第三章最终 v12 模型进行排序，再以 COMSOL 真实频散计算给出独立验证结果。

## 2. 独立候选构建方法

候选池构建时同时排除了 v12 训练集、第4章 GA20 历史记录以及已有第5章 predicted_topk/random 使用过的 physical_key。为避免仅更换 point_id 造成伪独立，脚本还检查了不含 point_id 的 shape-parameter-band key。候选结构使用已有可重建的 shape_id/shape_family，连续参数限定在论文使用的参数化设计域内。

## 3. 预测排序与验证清单

排序模型未重新训练，直接加载第三章最终模型包 `final_predictor_bundle.joblib`。综合评分定义为 `predicted_score = predicted_open_prob × predicted_cover_ratio`，每个目标频带选取预测最高的 Top-5，并从同一 strict_holdout 候选池中随机抽取 random5，形成 60 次 COMSOL 验证清单。

## 4. COMSOL 验证结果

统计表见 `ch5_strict_holdout_summary.csv/md`。

| target_band | method | n_candidates | n_solve_success | active_rate | best_true_overlap_Hz | best_true_cover_ratio | best_candidate_id |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 140–180 Hz | predicted_top5 | 5 | 5 | 1.000 | 25.962 | 0.649 | strict_band140_180_c0055 |
| 140–180 Hz | random5 | 5 | 4 | 1.000 | 20.027 | 0.501 | strict_band140_180_c0028 |
| 160–200 Hz | predicted_top5 | 5 | 5 | 1.000 | 35.972 | 0.899 | strict_band160_200_c0025 |
| 160–200 Hz | random5 | 5 | 5 | 1.000 | 28.762 | 0.719 | strict_band160_200_c0537 |
| 180–220 Hz | predicted_top5 | 5 | 5 | 1.000 | 39.968 | 0.999 | strict_band180_220_c0436 |
| 180–220 Hz | random5 | 5 | 3 | 0.667 | 11.855 | 0.296 | strict_band180_220_c0097 |
| 200–240 Hz | predicted_top5 | 5 | 5 | 1.000 | 34.798 | 0.870 | strict_band200_240_c0136 |
| 200–240 Hz | random5 | 5 | 5 | 0.200 | 20.818 | 0.520 | strict_band200_240_c0178 |
| 220–260 Hz | predicted_top5 | 5 | 4 | 0.750 | 9.964 | 0.249 | strict_band220_260_c0519 |
| 220–260 Hz | random5 | 5 | 4 | 0.500 | 1.942 | 0.049 | strict_band220_260_c0099 |
| 240–280 Hz | predicted_top5 | 5 | 5 | 1.000 | 1.205 | 0.030 | strict_band240_280_c0459 |
| 240–280 Hz | random5 | 5 | 4 | 1.000 | 1.230 | 0.031 | strict_band240_280_c0113 |

## 5. 与真实 GA20 基准对比

对比表见 `ch5_strict_holdout_vs_ga20.csv/md`。

| target_band | pred_top5/GA overlap | random5/GA overlap | pred_minus_random_overlap | conclusion_tag |
| --- | ---: | ---: | ---: | --- |
| 140–180 Hz | 1.166 | 0.899 | 5.935 | pred_better |
| 160–200 Hz | 1.109 | 0.886 | 7.210 | pred_better |
| 180–220 Hz | 0.999 | 0.296 | 28.113 | pred_better |
| 200–240 Hz | 0.986 | 0.590 | 13.980 | pred_better |
| 220–260 Hz | 2.432 | 0.474 | 8.021 | pred_better |
| 240–280 Hz | 0.306 | 0.313 | -0.025 | random_not_worse |

## 6. 结论与论文写法建议

1. 该补充实验可以作为第5章 strict_holdout 独立验证材料，优先用于支撑“有限预算下预测 Top-k 相比随机候选具有一定筛选优势”这一谨慎表述。
2. 若某些目标频带中 random5 不弱于 predicted_top5，应在正文中如实说明，避免写成预测模型稳定替代真实 GA。
3. 第4章 GA20 仍是完整真实优化基准；本实验只说明预测模型在小预算候选筛选中的作用。
4. 高频频带若仍表现较弱，应归入结构族与参数空间可达性边界分析，而不是简单归咎于排序模型。

## 图件清单

- `ch5_strict_fig1_holdout_pipeline`: `ch5_strict_fig1_holdout_pipeline.png`, `ch5_strict_fig1_holdout_pipeline.svg`, `ch5_strict_fig1_holdout_pipeline.pdf`
- `ch5_strict_fig2_pred_vs_random_active_rate`: `ch5_strict_fig2_pred_vs_random_active_rate.png`, `ch5_strict_fig2_pred_vs_random_active_rate.svg`, `ch5_strict_fig2_pred_vs_random_active_rate.pdf`
- `ch5_strict_fig3_pred_vs_random_best_overlap`: `ch5_strict_fig3_pred_vs_random_best_overlap.png`, `ch5_strict_fig3_pred_vs_random_best_overlap.svg`, `ch5_strict_fig3_pred_vs_random_best_overlap.pdf`
- `ch5_strict_fig4_pred_vs_random_best_cover`: `ch5_strict_fig4_pred_vs_random_best_cover.png`, `ch5_strict_fig4_pred_vs_random_best_cover.svg`, `ch5_strict_fig4_pred_vs_random_best_cover.pdf`
- `ch5_strict_fig5_vs_ga20_ratio`: `ch5_strict_fig5_vs_ga20_ratio.png`, `ch5_strict_fig5_vs_ga20_ratio.svg`, `ch5_strict_fig5_vs_ga20_ratio.pdf`
- `ch5_strict_fig6_typical_unit_cells`: `ch5_strict_fig6_typical_unit_cells.png`, `ch5_strict_fig6_typical_unit_cells.svg`, `ch5_strict_fig6_typical_unit_cells.pdf`
- `ch5_strict_fig7_typical_dispersion`: `ch5_strict_fig7_typical_dispersion.png`, `ch5_strict_fig7_typical_dispersion.svg`, `ch5_strict_fig7_typical_dispersion.pdf`

## 终端清单

```json
{
  "candidate_pool_per_band": {
    "140–180 Hz": 600,
    "160–200 Hz": 600,
    "180–220 Hz": 600,
    "200–240 Hz": 600,
    "220–260 Hz": 600,
    "240–280 Hz": 600
  },
  "manifest_count": 60,
  "solve_success_count": 54,
  "predicted_top5_better_than_random5_by_band": {
    "140–180 Hz": true,
    "160–200 Hz": true,
    "180–220 Hz": true,
    "200–240 Hz": true,
    "220–260 Hz": true,
    "240–280 Hz": false
  },
  "predicted_top5_to_ga20_overlap_ratio": {
    "140–180 Hz": 1.1659657271678874,
    "160–200 Hz": 1.1086938536585398,
    "180–220 Hz": 0.9992018739986426,
    "200–240 Hz": 0.9862441959798552,
    "220–260 Hz": 2.4316431655903274,
    "240–280 Hz": 0.3061793307933205
  },
  "generated_files": [
    "CH5_STRICT_HOLDOUT_PREPARE_CHECKLIST.json",
    "build_ch5_strict_holdout_validation_v1.py",
    "ch5_strict_holdout_candidate_pool.csv",
    "ch5_strict_holdout_candidate_pool.md",
    "ch5_strict_holdout_comsol_manifest_top5_random5.csv",
    "ch5_strict_holdout_comsol_manifest_top5_random5.md",
    "ch5_strict_holdout_comsol_results_top5_random5.csv",
    "ch5_strict_holdout_comsol_results_top5_random5.md",
    "ch5_strict_holdout_comsol_results_top5_random5_smoke.csv",
    "ch5_strict_holdout_comsol_results_top5_random5_worker0.csv",
    "ch5_strict_holdout_comsol_results_top5_random5_worker1.csv",
    "ch5_strict_holdout_comsol_results_top5_random5_worker2.csv",
    "ch5_strict_holdout_predictions.csv",
    "ch5_strict_holdout_predictions.md",
    "ch5_strict_holdout_summary.csv",
    "ch5_strict_holdout_summary.md",
    "ch5_strict_holdout_vs_ga20.csv",
    "ch5_strict_holdout_vs_ga20.md",
    "figures/ch5_strict_fig1_holdout_pipeline.pdf",
    "figures/ch5_strict_fig1_holdout_pipeline.png",
    "figures/ch5_strict_fig1_holdout_pipeline.svg",
    "figures/ch5_strict_fig2_pred_vs_random_active_rate.pdf",
    "figures/ch5_strict_fig2_pred_vs_random_active_rate.png",
    "figures/ch5_strict_fig2_pred_vs_random_active_rate.svg",
    "figures/ch5_strict_fig3_pred_vs_random_best_overlap.pdf",
    "figures/ch5_strict_fig3_pred_vs_random_best_overlap.png",
    "figures/ch5_strict_fig3_pred_vs_random_best_overlap.svg",
    "figures/ch5_strict_fig4_pred_vs_random_best_cover.pdf",
    "figures/ch5_strict_fig4_pred_vs_random_best_cover.png",
    "figures/ch5_strict_fig4_pred_vs_random_best_cover.svg",
    "figures/ch5_strict_fig5_vs_ga20_ratio.pdf",
    "figures/ch5_strict_fig5_vs_ga20_ratio.png",
    "figures/ch5_strict_fig5_vs_ga20_ratio.svg",
    "figures/ch5_strict_fig6_typical_unit_cells.pdf",
    "figures/ch5_strict_fig6_typical_unit_cells.png",
    "figures/ch5_strict_fig6_typical_unit_cells.svg",
    "figures/ch5_strict_fig7_typical_dispersion.pdf",
    "figures/ch5_strict_fig7_typical_dispersion.png",
    "figures/ch5_strict_fig7_typical_dispersion.svg",
    "run_ch5_strict_holdout_comsol_manifest_v1.m",
    "run_ch5_strict_holdout_comsol_via_matlab_engine.py"
  ],
  "recommend_extend_top10_random10": "根据Top5结果，若predicted_top5在多数频带优于random5且COMSOL成功率稳定，建议扩展；若高频仍明显失败，优先改结构族候选池。"
}
```