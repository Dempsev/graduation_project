# Target-Band Baseline Comparison V1

## 1. 目的

本文件用于把当前 thesis 主线里的几条关键路线，放到同一个 baseline ladder 中系统比较。

目标不是追求“所有路线完全同构”，而是回答两个更实际的问题：

1. 当前 predictor-guided / shape-aware / exploratory 主线到底比旧路线强在哪里？
2. 这些提升是来自更好的 shape-aware 入口、exploratory 搜索，还是只是偶然碰到的个例？

本轮对照聚焦于 4 个 canonical target bands：

- `band180_220`
- `band200_240`
- `band220_260`
- `band240_280`

分析输出在：

- [targetband_baseline_ladder_v1](/d:/graduation_project/coad/data/analysis/targetband_baseline_ladder_v1)

核心表：

- [canonical_band_comparison_v1.csv](/d:/graduation_project/coad/data/analysis/targetband_baseline_ladder_v1/canonical_band_comparison_v1.csv)
- [baseline_ladder_info_v1.json](/d:/graduation_project/coad/data/analysis/targetband_baseline_ladder_v1/baseline_ladder_info_v1.json)

## 2. 本轮纳入的对照线

本轮 baseline ladder 包含以下几条线：

### A. `generic_dataset_prior_v8`

角色：

- generic / random-like unconditional baseline

含义：

- 用当前 `v8` truth 分布给出一个无搜索、无优化条件的先验参考
- 它不是一条真实 random search 线，但能提供“如果不做有方向搜索，平均水平大概在哪里”的参考

### B. `targetband_local_ga_v1_probe`

角色：

- 旧 predictor-guided local GA 的小规模 probe 验证线

特点：

- 目前只在 `band180_220` 上有真实验证
- 预算很小，代表最早的预测驱动局部优化原型

### C. `targetband_local_ga_v1_top6`

角色：

- 旧 predictor-guided local GA 的 top6 shape 扩展验证线

特点：

- 同样主要服务 `band180_220`
- 用于说明“早期 predictor + local GA”能做到什么程度

### D. `band_catalog_real_ga_v1`

角色：

- 旧 band-catalog real GA baseline

特点：

- 不依赖 predictor
- 是旧 target-band real-search 的强基线
- 但 shape pool 和搜索逻辑还没有切到 band-aware 主线

### E. `band_supplement_ga_v1`

角色：

- 旧 conservative supplement baseline

特点：

- 开始尝试补弱 band
- 但参数范围和 shape 入口仍然偏保守

### F. `band_supplement_exploratory_v2`

角色：

- 当前 predictor-guided / shape-aware / exploratory 主线

特点：

- band-aware shape pool
- exploratory 参数范围
- 历史避碰
- cooperative 多会话 real search

这是当前 thesis 主线里最重要的 inverse-design route。

## 3. 统一比较指标

本轮统一使用这些指标：

- `real_open_rate`
- `mean_overlap_Hz`
- `mean_cover_ratio`
- `best_overlap_Hz`
- `best_cover_ratio`
- `best_shape_id`
- `family_diversity`
- `budget_proxy`

需要说明两点：

1. 不是每条线都能提供完整相同粒度的数据  
2. `generic_dataset_prior_v8` 是 truth prior，不是 dedicated random real-search run

所以这份对照的重点是：

- 方法位置对照
- best-case 能力对照
- 弱 band 突破对照

而不是做一个完全苛刻的“同预算、同协议 benchmark”。

## 4. 各 Band 对照结果

### 4.1 `band180_220`

#### Generic prior

- open rate: `0.7926`
- mean cover: `0.1278`
- best cover: `0.5946`
- best shape: `ep193_step51_contour_xy`

#### 旧 local GA 验证

`targetband_local_ga_v1_probe`

- open rate: `1.000`
- mean overlap: `22.15 Hz`
- mean cover: `0.5537`
- best cover: `0.5552`
- best shape: `ep253_step54_contour_xy`

`targetband_local_ga_v1_top6`

- open rate: `1.000`
- mean overlap: `18.11 Hz`
- mean cover: `0.4526`
- best cover: `0.5552`
- best shape: `ep253_step54_contour_xy`

#### 旧 band-catalog real GA

- open rate: `0.7337`
- best overlap: `28.89 Hz`
- best cover: `0.7222`
- best shape: `ep205_step69_contour_xy`

#### 旧 conservative supplement

- open rate: `0.6517`
- best overlap: `30.92 Hz`
- best cover: `0.7729`
- best shape: `ep571_step57_contour_xy`

#### 当前 exploratory 主线

- open rate: `0.8782`
- best overlap: `40.00 Hz`
- best cover: `1.0000`
- best shape: `ep248_step27_contour_xy`

#### 解读

`band180_220` 上，当前主线不仅优于 generic prior，也明显优于：

- 旧 local GA 真实验证线
- 旧 band-catalog GA
- 旧 conservative supplement

这说明当前主线在“成熟中频目标 band”上已经不是试探性方法，而是明显更强的逆向设计路线。

### 4.2 `band200_240`

#### Generic prior

- open rate: `0.0067`
- mean cover: `0.00032`
- best cover: `0.0946`
- positive families: 极少

#### 旧 band-catalog real GA

- open rate: `0.0556`
- best overlap: `11.86 Hz`
- best cover: `0.2964`
- best shape: `ep205_step69_contour_xy`

#### 旧 conservative supplement

- open rate: `0.0249`
- best overlap: `12.92 Hz`
- best cover: `0.3231`
- best shape: `ep571_step57_contour_xy`

#### 当前 exploratory 主线

- open rate: `0.6693`
- best overlap: `40.00 Hz`
- best cover: `1.0000`
- best shape: `ep193_step51_contour_xy`

#### 解读

这是本轮对照里最关键的一条。

`band200_240` 以前几乎就是弱 band 代表：

- generic prior 几乎没有正样本
- 旧 band-catalog GA 和旧 conservative supplement 只能做到 0.30 左右的 cover

而当前 exploratory 主线已经把它推进到：

- 完整 `40 Hz` overlap
- `1.000` cover

这说明：

**弱 band 不是不可设计，而是旧搜索入口和旧 shape/parameter 世界观太保守。**

### 4.3 `band220_260`

#### Generic prior

- open rate: `0.8330`
- mean cover: `0.0155`
- best cover: `0.0531`

这里的 open rate 看起来高，但要特别注意：

- 平均 cover 非常低
- 说明大量样本只是“沾边”或轻微 overlap
- 并不意味着 generic 结构就能做出高质量 target-band 解

#### 旧 conservative supplement

- open rate: `0.7479`
- best overlap: `3.43 Hz`
- best cover: `0.0858`
- best shape: `ep195_step39_contour_xy`

#### 当前 exploratory 主线

- open rate: `0.5213`
- best overlap: `40.00 Hz`
- best cover: `1.0000`
- best shape: `ep253_step54_contour_xy`

#### 解读

这里最重要的是不要被 open rate 迷惑。

真正重要的是：

- 旧线虽然 open rate 不低，但 best cover 非常差
- 当前主线虽然 open rate 没那么高，但 best candidate 质量极高，已经达到了完整覆盖

也就是说：

**当前主线的优势不是“什么都开”，而是“更有方向地找到真正可用的设计”。**

### 4.4 `band240_280`

#### Generic prior

- open rate: `0.8924`
- mean cover: `0.0175`
- best cover: `0.0749`

同样，这里 open rate 不能直接被解释为“设计容易”，因为：

- 平均 cover 很低
- best cover 也很低
- 本质上仍然是高频 sparse overlap 为主

#### 旧 conservative supplement

- open rate: `0.9320`
- best overlap: `3.43 Hz`
- best cover: `0.0858`
- best shape: `ep195_step39_contour_xy`

#### 当前 exploratory 主线

- open rate: `0.5692`
- best overlap: `35.93 Hz`
- best cover: `0.8982`
- best shape: `ep253_step54_contour_xy`

#### 解读

`band240_280` 是当前最能说明“高频弱 band 设计难点”的例子：

- 旧线的 open rate 也许看起来高
- 但几乎都是低质量 overlap
- 当前主线虽然不是所有候选都开得多，但 best result 已经接近完整覆盖

所以在逆向设计语境下：

**当前主线对 `band240_280` 的意义，远大于简单比较 open rate。**

## 5. 家族多样性与预算

### 家族多样性

从当前输出看：

- 旧 band-catalog GA：family diversity 偏低
- 旧 conservative supplement：也偏低
- exploratory 主线在部分 band 上 family diversity 更高

这和我们前面关于 shape-aware selection 的判断一致：

- 不同 target band 需要不同 shape pool
- 否则搜索很容易被旧 family 绑架

### 预算

budget proxy 大致是：

- old local validation: `4~6`
- old band-catalog GA: `522`
- old conservative supplement: `603`
- exploratory mainline: `1149`

所以这次对照里必须诚实说明：

- 当前 exploratory 主线不是“更省预算”的版本
- 它是“更强、更有方向、能够真正打通弱 band”的版本

后面如果要讲预算效率，应该进一步比较：

- predictor shortlist 质量
- 单位真实评估成本下的弱 band 命中率

而不是只看这轮完整 exploratory search 的总花费。

## 6. 本轮对照的正式结论

### 结论 1

当前主线已经明显优于旧保守补数线和旧 band-catalog GA，尤其在弱 band 上。

最典型的是：

- `band200_240`
- `band220_260`
- `band240_280`

这三条线上，当前主线的 best candidate 质量已经远高于旧线。

### 结论 2

旧 local GA 线依然有价值，但更适合作为“早期 predictor-guided inverse-design 原型”基线。

它说明：

- predictor-driven local refinement 这个想法本身是成立的

但它已经不是当前 strongest line。

### 结论 3

generic prior 的高 open rate 不能被误读成“弱 band 已经容易”。

真正需要看的是：

- mean cover
- best cover
- best overlap

从这三个角度看，弱 band 的设计难点仍然非常真实。

### 结论 4

当前 predictor-guided / shape-aware / exploratory 主线已经可以被正式表述为：

**当前 thesis band catalog 内最强的 target-band inverse-design line。**

这句话是成立的。

## 7. 对第四步的落点

所以第四步现在已经能形成比较清楚的论文/汇报口径：

1. generic prior 提供无条件参考
2. 旧 local GA 提供最早的 predictor-driven 原型基线
3. 旧 band-catalog GA 提供 pre-shape-aware real-search 基线
4. 旧 conservative supplement 提供保守 weak-band 补数基线
5. 当前 exploratory 主线提供 strongest target-band inverse-design line

这套 baseline ladder 现在已经够完整，可以支撑后续写作和结果章节。 
