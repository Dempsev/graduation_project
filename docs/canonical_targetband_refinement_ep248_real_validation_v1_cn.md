# `band180_220_ep248` refinement 真验证结论 v1

## 1. 验证对象

本次只验证 `band180_220_ep248` 的 refinement probe top-2 候选：

- `band180_220_ep248__refine_01`
- `band180_220_ep248__refine_02`

来源：

- [canonical_targetband_refinement_ep248_probe_manifest_v1.csv](/d:/graduation_project/coad/data/ml_runs/canonical_targetband_refinement_ep248_probe_v1/validation_manifest_v1/canonical_targetband_refinement_ep248_probe_manifest_v1.csv)

真实 COMSOL stage4 输出：

- [stage4_validation_results.csv](/d:/graduation_project/coad/data/comsol_batch/stage4_validation_canonical_targetband_refinement_ep248_probe_v1/stage4_validation_results.csv)

## 2. 基准 canonical center

canonical center 来自：

- [canonical_local_robustness_merged_v1.csv](/d:/graduation_project/coad/data/analysis/canonical_local_robustness_v1/canonical_local_robustness_merged_v1.csv)

对应 `band180_220_ep248` center 的真实结果：

- `gap34_Hz = 46.672305`
- `gap34_lower_edge_Hz = 179.770299`
- `gap34_upper_edge_Hz = 226.442603`
- `target_overlap_Hz_actual = 40.0`
- `target_cover_ratio_actual = 1.0`
- `gap34_gain_Hz = 11.292824`

## 3. refinement 候选真实结果

### `refine_01`

- `gap34_Hz = 46.648774`
- `gap34_lower_edge_Hz = 179.745357`
- `gap34_upper_edge_Hz = 226.394131`
- `gap34_gain_Hz = 10.944647`

### `refine_02`

- `gap34_Hz = 46.642187`
- `gap34_lower_edge_Hz = 179.740533`
- `gap34_upper_edge_Hz = 226.382719`
- `gap34_gain_Hz = 10.938061`

## 4. 结论

两点都成立：

- 两个 refinement candidate 都几何有效、接触有效、求解成功
- 两个 refinement candidate 都没有超过原始 canonical center

相对 canonical center：

- `gap34_Hz` 小幅下降
- `gap34_gain_Hz` 下降约 `0.35 Hz`
- gap 边界也略微退化

因此，这次真验证支持的结论是：

> 对 `band180_220_ep248` 而言，当前轻量 surrogate-guided local refinement 没有带来真实增益。至少在这一例上，原始 canonical real-GA solution 已经比 refinement probe 候选更优。

## 5. 这件事说明了什么

这次结果能支持下面这句更稳的判断：

> 当前 thesis 主线下的 post-design refinement 不是必要项。即使在唯一一个 surrogate 层面出现轻微正向信号的案例中，真实 COMSOL 验证也没有确认该提升。

但它**不能**直接证明：

- 所有可能的 refinement 方向都失败了
- canonical point 已被严格证明为数学意义上的局部最优

它只说明：

- 当前这条 refinement 路线
- 当前这个局部信号
- 当前这组候选

在真实验证里没有超过原始 canonical center。
