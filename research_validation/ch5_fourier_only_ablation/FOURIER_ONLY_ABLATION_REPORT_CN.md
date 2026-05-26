# 傅里叶边界模型 GA 优化与当前结合模型 GA 优化对比实验

## 实验目的

本实验用于回应“没有贪吃蛇结构族，仅采用傅里叶边界模型时，经过同样 GA 优化后的结果如何”的问题。对比口径为：

- 傅里叶-only GA：形状池仅使用傅里叶边界原型 `fourier_only_real_ga_shape_pool_v1.csv`，优化过程仍采用 COMSOL-in-loop GA。
- 当前结合模型 GA：使用第 4 章当前 20 代真实 GA 结果，即现有贪吃蛇/傅里叶结合候选空间下的 COMSOL-in-loop GA 基准。
- 二者均采用 `target_overlap_Hz` 作为适应度函数；每个频带均为 20 代、种群规模 6，共 120 次真实 COMSOL 评价。

## 数据来源

- 傅里叶-only shape pool：`data/ml_runs/fourier_only_real_ga_v1/fourier_only_real_ga_shape_pool_v1.csv`。
- 当前结合模型 shape pool：`data/ml_runs/targetband_baseline_abc_v1/real_ga_shape_pool_v1.csv`。
- 傅里叶-only GA 输出目录：`data/comsol_batch/comsol_in_loop_fourier_only_<band>_ga_v1/`。
- 当前结合模型 GA20 汇总：`research_validation/ch4_ga_real_optimization/ch4_ga_summary_20gen.csv`。

## 结果汇总

| 目标频带 | 傅里叶-only GA20 最佳 overlap/Hz | 当前结合模型 GA20 最佳 overlap/Hz | 差值/Hz | 傅里叶-only / 当前 | 结论 |
| --- | ---: | ---: | ---: | ---: | --- |
| 200-240 Hz | 34.364 | 35.283 | -0.919 | 0.974 | 当前结合模型略优 |
| 220-260 Hz | 7.783 | 4.098 | 3.685 | 1.899 | 傅里叶-only 略优 |
| 240-280 Hz | 2.922 | 3.934 | -1.012 | 0.743 | 当前结合模型略优 |

## 主要观察

1. 在 200-240 Hz 频带，傅里叶-only GA20 获得 34.364 Hz，接近当前结合模型 GA20 的 35.283 Hz，但仍略低，说明当前结合候选空间在该频带保留了小幅优势。
2. 在 220-260 Hz 频带，傅里叶-only GA20 获得 7.783 Hz，高于当前结合模型 GA20 的 4.098 Hz，说明该高频目标并不完全依赖贪吃蛇形态来源，傅里叶边界模型经 GA 搜索后也能找到更好的局部解。
3. 在 240-280 Hz 频带，傅里叶-only GA20 获得 2.922 Hz，低于当前结合模型 GA20 的 3.934 Hz，说明更高频段中结合候选空间仍有一定优势，但两者都属于较低 overlap，仍应作为困难频带讨论。
4. 因此，这组消融实验不支持“贪吃蛇结构族单独决定优化效果”的说法。更稳妥的论文结论是：傅里叶边界模型本身具备可优化性，贪吃蛇结构族的价值主要体现在扩充形态来源和改善部分频带的搜索机会；最终效果随目标频带变化，并由 COMSOL-in-loop GA 真值决定。

## 论文可用表述

为检验贪吃蛇路径结构族对优化结果的影响，本文进一步构建了傅里叶边界模型的 GA 消融实验。在该实验中，形状池仅保留傅里叶边界原型，连续设计变量、适应度函数和 COMSOL-in-loop GA 设置均与当前优化流程保持一致。每个目标频带执行 20 代、种群规模为 6 的真实 GA 搜索，并与现有贪吃蛇/傅里叶结合候选空间下的 GA20 结果进行比较。结果表明，在 200-240 Hz 频带，傅里叶-only GA20 的最佳重叠宽度为 34.364 Hz，略低于当前结合模型的 35.283 Hz；在 220-260 Hz 频带，傅里叶-only GA20 达到 7.783 Hz，高于当前结合模型的 4.098 Hz；在 240-280 Hz 频带，傅里叶-only GA20 为 2.922 Hz，低于当前结合模型的 3.934 Hz。该结果说明，傅里叶边界模型本身具有可优化性，贪吃蛇结构族并不是获得目标带隙的唯一来源；其主要作用是扩展候选形态空间，并在部分频带中提高搜索到有效结构的机会。不同频带下两类候选空间的优劣并不完全一致，因此最终结论仍需以 COMSOL 频散计算和真实 GA 搜索结果为准。

## 输出文件

- `fourier_only_ablation_summary.csv`：傅里叶-only GA20 与当前结合模型 GA20 的数值对比。
- `figures/ch5_fourier_only_ga20_vs_current_ga20_overlap.svg`：同口径 overlap 柱状图。
- `thesis_insert_fourier_only_ablation_cn.md`：可粘贴入论文的段落。
