# Weak-Band Dashboard V1

## 1. 目的

本文件用于把“弱 band 进展”从临时口头解释，固定成当前 target-band 主线下的常规分析项。

以后不再只看平均模型指标，而是每轮都固定跟踪：

- 各弱 band 的正样本数
- 各弱 band 的正样本 family 数
- 各弱 band 的 mean positive cover ratio
- 各弱 band 的 shortlist 质量
- 各弱 band 的最终 inverse-design usefulness

这一套指标比单纯看总体 `f1 / R²` 更能解释：

**项目到底有没有在我们真正关心的 band 上取得实质推进。**

本轮 dashboard 输出目录：

- [weak_band_dashboard_v1](/d:/graduation_project/coad/data/analysis/weak_band_dashboard_v1)

核心文件：

- [weak_band_dashboard_summary_v1.csv](/d:/graduation_project/coad/data/analysis/weak_band_dashboard_v1/weak_band_dashboard_summary_v1.csv)
- [weak_band_tracking_priority_v1.csv](/d:/graduation_project/coad/data/analysis/weak_band_dashboard_v1/weak_band_tracking_priority_v1.csv)
- [weak_band_dashboard_info_v1.json](/d:/graduation_project/coad/data/analysis/weak_band_dashboard_v1/weak_band_dashboard_info_v1.json)

## 2. 当前纳入的弱 Band

当前 dashboard 固定追踪 4 个弱 band：

- `band180_220`
- `band200_240`
- `band220_260`
- `band240_280`

这四个 band 覆盖了：

- thesis 主线中的中频核心 band
- 历史上最稀缺、最难的弱 band
- 当前 inverse-design 最有论文价值的 band

## 3. Dashboard 的指标定义

当前这版 dashboard 固定记录下面几类指标。

### 3.1 Coverage 指标

- `coverage_positive_rows`
  - 当前 band 的正 truth 样本数
- `coverage_positive_families`
  - 当前 band 中出现正样本的 family 数
- `coverage_mean_positive_cover_ratio`
  - 当前 band 正样本中的平均 cover ratio
- `coverage_deficiency_score`
  - 当前 band 的补数缺口分数，越高说明越值得继续补

### 3.2 Shortlist 指标

这里使用当前冻结主线下的 predictor：

- 分类器：RF
- 回归器：HGB

短名单分数仍按：

- `shortlist_score = cls_prob * max(reg_pred, 0)`

dashboard 当前记录：

- `family_cv_top20_mean_cover`
- `family_cv_top20_cover_lift`
- `lobo_top20_mean_cover`
- `lobo_top20_cover_lift`

也就是：

- family-CV 下，前 20 个候选的质量
- leave-one-band 下，前 20 个候选的质量

### 3.3 Inverse-Design Usefulness 指标

这里主要取当前最强主线：

- `band_supplement_exploratory_v2`

记录：

- `mainline_real_open_rate`
- `mainline_best_overlap_Hz`
- `mainline_best_cover_ratio`
- `mainline_best_shape_id`
- `mainline_family_diversity`

并和旧 baseline 对比：

- `delta_cover_vs_conservative`
- `delta_overlap_vs_conservative`
- `delta_cover_vs_catalog`
- `delta_overlap_vs_catalog`

## 4. 当前 Dashboard 结果

### 4.1 `band200_240`

- positive rows: `1916`
- positive families: `53`
- mean positive cover: `0.4941`
- deficiency score: `5.7721`
- mainline best cover: `1.0000`
- mainline best overlap: `40.00 Hz`
- best shape: `ep193_step51_contour_xy`
- 相对 conservative supplement：
  - cover `+0.6769`
  - overlap `+27.08 Hz`
- 相对 old band-catalog real GA：
  - cover `+0.7036`
  - overlap `+28.14 Hz`

### 解读

`band200_240` 仍然是当前最重要的弱 band。

原因是：

- deficiency score 最高
- positive family 数仍明显少于高频另外两个 band
- 但 inverse-design usefulness 已经非常强

所以它既是当前最成功的突破案例，也是后面最值得持续跟踪的主战场。

### 4.2 `band240_280`

- positive rows: `2985`
- positive families: `81`
- mean positive cover: `0.0610`
- deficiency score: `4.9776`
- family-CV top20 mean cover: `0.0334`
- leave-one-band top20 mean cover: `0.0445`
- mainline best cover: `0.8982`
- mainline best overlap: `35.93 Hz`
- best shape: `ep253_step54_contour_xy`
- 相对 conservative supplement：
  - cover `+0.8124`
  - overlap `+32.49 Hz`

### 解读

`band240_280` 的特点是：

- 正样本很多
- family 覆盖也已经很宽
- 但 mean positive cover ratio 仍然很低

这意味着：

- 这个 band 上“沾边样本”不少
- 但真正高质量 target-band 设计仍然难

所以它在 dashboard 中排第二很合理：

- 不是因为没数据
- 而是因为“高质量数据仍然不够多”

### 4.3 `band220_260`

- positive rows: `2709`
- positive families: `81`
- mean positive cover: `0.1506`
- deficiency score: `4.5943`
- family-CV top20 mean cover: `0.0304`
- leave-one-band top20 mean cover: `0.0263`
- mainline best cover: `1.0000`
- mainline best overlap: `40.00 Hz`
- best shape: `ep253_step54_contour_xy`
- 相对 conservative supplement：
  - cover `+0.9142`
  - overlap `+36.57 Hz`

### 解读

`band220_260` 和 `band240_280` 有一点不同：

- 平均正样本 cover 更高
- 说明它不是纯 sparse-overlap band
- 但 predictor shortlist 的平均质量还不算特别强

所以它当前排第三是合理的：

- 已经被打通
- 但仍值得持续跟踪 predictor 是否真正把高质量候选排稳

### 4.4 `band180_220`

- positive rows: `3918`
- positive families: `70`
- mean positive cover: `0.4385`
- deficiency score: `3.6541`
- family-CV top20 mean cover: `0.2841`
- leave-one-band top20 mean cover: `0.3914`
- mainline best cover: `1.0000`
- mainline best overlap: `40.00 Hz`
- best shape: `ep248_step27_contour_xy`
- 相对 conservative supplement：
  - cover `+0.2271`
  - overlap `+9.08 Hz`
- 相对 old band-catalog real GA：
  - cover `+0.2778`
  - overlap `+11.11 Hz`

### 解读

`band180_220` 现在更像是：

- thesis 主线里的成熟参考 band
- 已经不是最需要补 coverage 的 band
- 更适合当稳定展示 band，而不是持续补数的第一优先级

## 5. 当前固定优先级

当前 dashboard 给出的 tracking priority 是：

1. `band200_240`
2. `band240_280`
3. `band220_260`
4. `band180_220`

这个顺序和我们前面的讨论是一致的。

### 如何理解这个优先级

不是简单看谁最差，而是同时看：

- coverage 缺口
- shortlist 质量
- 最终 inverse-design usefulness

所以：

- `band200_240` 排第一，是因为它虽然已被打通，但仍是最核心、最有证明价值的弱 band
- `band240_280` 排第二，是因为它高质量样本仍稀缺
- `band220_260` 排第三，是因为已经有完整覆盖案例，但 shortlist 端仍需继续跟
- `band180_220` 排第四，是因为已经更接近“成熟展示 band”

## 6. Dashboard 的真正用途

这套 dashboard 的作用不是再造一份模型指标表，而是：

### 用途 1：解释“这轮补数据有没有用”

如果只看总体 `f1 / R²`，你很难判断项目有没有真推进。

但如果看 dashboard，就能直接看到：

- 弱 band 的正样本数有没有增加
- family 覆盖有没有变宽
- shortlist 质量有没有抬升
- mainline best result 有没有进一步超过 baseline

### 用途 2：决定下一轮算力往哪里打

现在就可以直接用它来回答：

- 先补哪个 band？
- 哪个 band 已经更像展示 band？
- 哪个 band 还缺高质量 truth？

### 用途 3：支持论文与汇报

这套表以后可以直接支撑：

- 弱 band coverage 的阶段性变化
- predictor readiness 和 inverse-design usefulness 的联系
- 为什么某些 band 要继续补、某些 band 可以转入展示

## 7. 正式结论

从现在开始，弱 band 进展不应再只通过总体模型分数来判断。

应该固定使用这套 dashboard 同时观察：

- coverage
- family diversity
- shortlist quality
- inverse-design usefulness

这样才能真正解释：

**当前 target-band 主线是不是在我们最关心的 band 上持续前进。**

## 8. 后续使用规则

后面每次出现以下情况之一，都应该更新这套 dashboard：

- 新一轮 weak-band truth 被 harvest
- 新一版主数据集形成
- predictor 重新训练
- exploratory / supplement / target-band real search 有新结果

也就是说：

**weak-band dashboard 现在应该成为 frozen target-band mainline 的常规分析面板。**
