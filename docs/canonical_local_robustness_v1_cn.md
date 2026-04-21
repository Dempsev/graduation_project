# Canonical Inverse-Design Local Robustness V1

## 目的

这一步用来回答一个很关键的问题：

- 当前 canonical inverse-design case 是不是一个非常尖的偶然点？
- 还是说，在最优参数点附近存在一个小范围的稳定盆地？

如果局部微扰之后：

- `cover ratio` 还能维持较高水平
- `overlap Hz` 只是小幅波动
- `gap edge` 没有剧烈崩塌

那么我们就可以更有把握地说，这些 target-band 设计不是“碰巧撞中”，而是具有一定局部稳健性。

## 固定案例

本轮固定 4 个 canonical case：

1. `band200_240` -> `ep193_step51_contour_xy`
2. `band220_260` -> `ep253_step54_contour_xy`
3. `band240_280` -> `ep253_step54_contour_xy`
4. `band180_220` -> `ep248_step27_contour_xy`

中心点来自：

- [ga_band_catalog_best_candidates_v1.csv](/d:/graduation_project/coad/data/comsol_batch/comsol_in_loop_band_supplement_exploratory_v2/ga_band_catalog_best_candidates_v1.csv)

中心点摘要在：

- [canonical_local_robustness_centers_v1.csv](/d:/graduation_project/coad/data/ml_runs/canonical_inverse_design_local_robustness_v1/validation_manifest_v1/canonical_local_robustness_centers_v1.csv)

## 扰动设计

每个 canonical case 采用 1 个中心点 + 8 个单变量微扰点，共 `9` 个点。

本轮扰动变量固定为：

- `a1`: `+/- 0.01`
- `a2`: `+/- 0.01`
- `b2`: `+/- 0.01`
- `r0`: `+/- 0.0008`

因此总 manifest 行数为：

- `4 cases x 9 variants = 36 rows`

manifest 在：

- [canonical_local_robustness_manifest_v1.csv](/d:/graduation_project/coad/data/ml_runs/canonical_inverse_design_local_robustness_v1/validation_manifest_v1/canonical_local_robustness_manifest_v1.csv)

summary 在：

- [canonical_local_robustness_manifest_summary_v1.json](/d:/graduation_project/coad/data/ml_runs/canonical_inverse_design_local_robustness_v1/validation_manifest_v1/canonical_local_robustness_manifest_summary_v1.json)

## 运行方式

### 1. 只重建 manifest

如果只想更新中心点和扰动表，可以在 MATLAB 里运行：

```matlab
run('D:\graduation_project\coad\runners\run_stage3_build_canonical_local_robustness_manifest_v1.m')
```

### 2. 直接做 COMSOL 验证

推荐直接运行：

```matlab
run('D:\graduation_project\coad\runners\run_stage4_validation_targetband_local_robustness_v1.m')
```

这个入口会自动：

1. 重建 manifest
2. 加载 stage4 validation 配置
3. 对 36 个局部扰动样本做 COMSOL 验证

对应配置文件：

- [get_stage4_validation_config_targetband_local_robustness_v1.m](/d:/graduation_project/coad/stage4_validation/get_stage4_validation_config_targetband_local_robustness_v1.m)

输出目录：

- [stage4_validation_targetband_local_robustness_v1](/d:/graduation_project/coad/data/comsol_batch/stage4_validation_targetband_local_robustness_v1)

## 跑完后如何分析

COMSOL 跑完之后，在 PowerShell 里执行：

```powershell
python D:\graduation_project\coad\prediction_targetband_param_v1\tools\analyze_canonical_local_robustness_v1.py
```

分析脚本：

- [analyze_canonical_local_robustness_v1.py](/d:/graduation_project/coad/prediction_targetband_param_v1/tools/analyze_canonical_local_robustness_v1.py)

输出目录：

- [canonical_local_robustness_v1](/d:/graduation_project/coad/data/analysis/canonical_local_robustness_v1)

核心输出包括：

- `canonical_local_robustness_merged_v1.csv`
- `canonical_local_robustness_case_summary_v1.csv`
- `canonical_local_robustness_variant_summary_v1.csv`
- `canonical_local_robustness_info_v1.json`

## 重点看什么

建议重点看下面这几类指标：

### 1. 中心点保真度

- 中心点真实 `overlap Hz`
- 中心点真实 `cover ratio`
- 中心点真实 `gap lower / upper edge`

这一步是确认 manifest 中心点在独立 validation 里是否仍然站得住。

### 2. 局部保持率

对每个 case，重点看：

- 有多少扰动点仍然保持 `>= 90%` 的中心点 cover
- 有多少扰动点仍然保持 `>= 80%` 的中心点 cover

如果这两个比例不低，就说明更像“小盆地”。

### 3. 边界漂移

看扰动后：

- `gap lower edge` 漂多少
- `gap upper edge` 漂多少

如果只是小幅平移，说明结构有局部稳定性；
如果某一个变量一动就让边界大幅崩掉，说明那个方向比较敏感。

### 4. 敏感变量

按变量拆开看：

- `a1` 扰动是否比 `a2` 更敏感
- `b2` 扰动是否会明显改变带隙位置
- `r0` 微调是否主要影响宽度或边界

这一步会帮助后面把“预测 + 优化 + 精修”的关系讲得更清楚。

## 结果解释口径

如果结果显示大部分扰动点还能保持较高 cover，可以这样表述：

- canonical inverse-design solution 并非单点偶然命中
- 在最优参数点附近存在局部稳定邻域
- 当前 target-band inverse-design line 不只是找到一个点，还找到了一个可局部微调的可用区域

如果结果显示某个 case 极其敏感，也不用回避，建议这样表述：

- 该 case 在目标 band 上可达到很高覆盖，但局部参数敏感性较强
- 后续可将该 case 作为 refinement / robustness-aware optimization 的重点对象

## 当前状态

目前 manifest 已经生成完成：

- `4` 个 canonical cases
- `36` 个 stage4 validation rows

下一步就是：

1. 跑 `run_stage4_validation_targetband_local_robustness_v1.m`
2. 跑 `analyze_canonical_local_robustness_v1.py`
3. 再根据结果判断每个案例更像“尖点”还是“小盆地”
