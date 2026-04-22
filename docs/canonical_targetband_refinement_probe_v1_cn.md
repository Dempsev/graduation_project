# canonical target-band 局部精修试点 v1

## 1. 这次做了什么

这次没有重新开一轮大规模真实 GA，而是按前面约定的轻量方案，围绕 canonical case 做了一个 **surrogate-guided local refinement probe**。

实现位置：

- [run_canonical_targetband_refinement_v1.py](/d:/graduation_project/coad/optimization/seed_ranking/run_canonical_targetband_refinement_v1.py)
- [run_canonical_targetband_refinement_v1.py](/d:/graduation_project/coad/optimization/runners/run_canonical_targetband_refinement_v1.py)
- [get_stage4_validation_config_canonical_targetband_refinement_v1.m](/d:/graduation_project/coad/stage4_validation/get_stage4_validation_config_canonical_targetband_refinement_v1.m)

这版试点的约束是：

- 只围绕 canonical centers
- 只开放 `a1 / a2 / b2 / r0`
- 使用 local trust-region，而不是旧版 local GA 的老边界
- `r0` 采用更窄的局部范围，并在初始化/变异中偏向更安全的 inward direction

当前采用的全局边界参考了 exploratory weak-band real GA：

- `a1`: `[0.42, 0.58]`
- `a2`: `[-0.24, 0.00]`
- `b2`: `[-0.04, 0.12]`
- `r0`: `[0.008, 0.016]`

当前局部半宽度：

- `a1`: `0.0030`
- `a2`: `0.0040`
- `b2`: `0.0040`
- `r0`: `0.00018`

## 2. 打分逻辑

这次不是回到“最大总带隙”，而是用了一个偏 target-band 的轻量复合分数：

`0.58*targetband_score`
`+ 0.08*contact_gate`
`+ 0.08*target_open_gate`
`+ 0.12*cover_preservation`
`+ 0.06*overlap_preservation`
`+ 0.08*r0_safety_gain`
`- 0.18*distance_from_base`
`- 0.12*r0_distance_from_base`

其中：

- `targetband_score` 仍复用现有 predictor/contact 链
- `cover_preservation` / `overlap_preservation` 用来鼓励 target-band 不退化
- `r0_safety_gain` 用来轻度鼓励从当前点向更安全的 `r0` 方向回收
- `distance_from_base` 与 `r0_distance_from_base` 控制这一步保持为局部精修，而不是重新大范围搜索

## 3. 输出位置

### A. 默认高优先级双 case 试点

- [canonical_targetband_refinement_v1](/d:/graduation_project/coad/data/ml_runs/canonical_targetband_refinement_v1)

主要文件：

- [canonical_targetband_refinement_candidate_manifest_v1.csv](/d:/graduation_project/coad/data/ml_runs/canonical_targetband_refinement_v1/canonical_targetband_refinement_candidate_manifest_v1.csv)
- [canonical_targetband_refinement_summary_v1.csv](/d:/graduation_project/coad/data/ml_runs/canonical_targetband_refinement_v1/canonical_targetband_refinement_summary_v1.csv)
- [canonical_targetband_refinement_config_v1.json](/d:/graduation_project/coad/data/ml_runs/canonical_targetband_refinement_v1/canonical_targetband_refinement_config_v1.json)
- [validation_manifest_v1](/d:/graduation_project/coad/data/ml_runs/canonical_targetband_refinement_v1/validation_manifest_v1)

### B. 四个 canonical cases 的诊断版

- [canonical_targetband_refinement_v1_allcases](/d:/graduation_project/coad/data/ml_runs/canonical_targetband_refinement_v1_allcases)

主要文件：

- [canonical_targetband_refinement_candidate_manifest_v1.csv](/d:/graduation_project/coad/data/ml_runs/canonical_targetband_refinement_v1_allcases/canonical_targetband_refinement_candidate_manifest_v1.csv)
- [canonical_targetband_refinement_summary_v1.csv](/d:/graduation_project/coad/data/ml_runs/canonical_targetband_refinement_v1_allcases/canonical_targetband_refinement_summary_v1.csv)
- [canonical_targetband_refinement_validation_manifest_v1.csv](/d:/graduation_project/coad/data/ml_runs/canonical_targetband_refinement_v1_allcases/validation_manifest_v1/canonical_targetband_refinement_validation_manifest_v1.csv)

## 4. 这次实际看到的效果

四个 canonical cases 的 surrogate-level probe 结果如下：

### `band240_280_ep253`

- base real archive cover: `0.8982`
- base predicted cover: `0.0345`
- best predicted cover: `0.0345`
- best candidate 仍然回到 center，本轮没有出现明确正向 refinement 信号

### `band220_260_ep253`

- base real archive cover: `1.0000`
- base predicted cover: `0.0344`
- best predicted cover: `0.0344`
- best candidate 仍然回到 center，本轮没有出现明确正向 refinement signal

### `band200_240_ep193`

- base real archive cover: `1.0000`
- base predicted cover: `0.0999`
- best predicted cover: `0.0999`
- 结果基本是平 plateau，没有观察到可利用的局部提升

### `band180_220_ep248`

- base real archive cover: `1.0000`
- base predicted cover: `0.3474`
- best predicted cover: `0.3575`
- best predicted overlap: `13.90 Hz -> 14.30 Hz`
- best candidate 相对 center 有一个很小但方向一致的 inward refinement：
  - `a1`: `0.556440 -> 0.556342`
  - `a2`: `0 -> 0`
  - `b2`: `0.067982 -> 0.067478`
  - `r0`: `0.014240 -> 0.014239`

## 5. 这次结果说明了什么

### 结论 1：脚本链路是通的

这一步最先证明的是：

- canonical center 选取没有问题
- local trust-region refinement 的代码链路已经打通
- predictor/contact 打分可以直接服务于 canonical 局部精修
- 输出也已经能直接接 stage4 validation

所以从工程角度看，这一步已经落地了。

### 结论 2：高 band `ep253` 两个 case 上，surrogate 在 canonical 邻域里几乎不给增益信号

`band240_280_ep253` 和 `band220_260_ep253` 的表现非常一致：

- predictor 对它们的 target-band cover 预测极低
- 即使真实 archive cover 很高，surrogate 仍把它们视作低覆盖点
- 在当前 trust-region 里，最优解直接退回 center

这更像是在说明：

**当前 surrogate 对这两个高 band canonical neighborhood 的分辨率不足，或者它们已经处于 predictor 看来几乎不可区分的 plateau。**

### 结论 3：`band180_220_ep248` 至少给出了一个小的正向 refinement 信号

虽然提升不大，但 `band180_220_ep248` 的 probe 结果是有方向性的：

- predicted cover 和 overlap 都有小幅上升
- 参数变化也符合“局部微调”而不是“重找新点”
- `r0` 方向没有被往危险侧推

因此它是当前最适合继续做真实验证的一例。

## 6. 当前最合理的下一步

按本轮 probe 的信息量，我建议下一步按下面顺序推进：

1. 先拿 `band180_220_ep248` 的 top-1 / top-2 refinement 候选做一次真实 COMSOL validation。
2. 对 `band240_280_ep253` 和 `band220_260_ep253` 暂时不要继续盲目扩大局部搜索。
3. 如果还要继续碰 `ep253`，更合理的是：
   - 进一步缩小 `r0` trust-region
   - 或改用更直接面向真实 edge / cover 的局部扫描，而不是完全依赖当前 surrogate

## 7. 一个很重要的判断

这次 probe 的结论不是“精修没有价值”，而是：

**在当前 surrogate 能力下，精修价值具有明显 case dependence。**

更具体地说：

- 对 `ep248 / band180_220`，局部精修已经出现了可追踪的候选增益
- 对 `ep253` 的高 band cases，当前 predictor 更像是在提醒我们：真实 canonical success 尚未被 surrogate 很好刻画

因此，后面如果要把 refinement 写进 thesis，最稳的表述不是“所有 canonical cases 都能明显进一步提升”，而是：

> A lightweight local refinement probe was implemented around the canonical solutions. Clear positive refinement signals were observed only for selected cases (most notably `band180_220_ep248`), while the high-band `ep253` cases appeared to lie in a predictor-flat neighborhood, suggesting that surrogate resolution rather than search budget became the main bottleneck.
