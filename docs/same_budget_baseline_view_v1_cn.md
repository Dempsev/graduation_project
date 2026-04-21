# 同预算 baseline 视角说明（中文版）

## 1. 为什么要补这一层

在 baseline ladder 已经建立之后，一个非常自然的追问是：

> 当前 strongest line 更强，是不是只是因为它花了更多真实评估预算？

如果这个问题不正面回答，后面即使 strongest line 的最终结果很好，仍然会留下一个解释空白：

- 是方法本身更有效？
- 还是只是因为跑得更久、评估得更多？

所以这一步的目标不是再做一套新的主实验，而是把已有 real-search history 按**相同真实评估预算**切片，看看在前 `N` 次评估里，各条线到底能做到什么程度。

---

## 2. 这次同预算分析纳入了哪些线

本次只纳入**真正具备连续 real-search budget 含义**的三条线：

1. `band_catalog_real_ga_v1`
   - 旧 band-catalog real GA baseline
2. `band_supplement_ga_v1`
   - 旧 conservative supplement baseline
3. `band_supplement_exploratory_v2`
   - 当前 predictor-guided / shape-aware / exploratory 主线

排除的线有：

- `generic_dataset_prior_v8`
- `targetband_local_ga_v1_probe`
- `targetband_local_ga_v1_top6`

原因不是它们没价值，而是它们不代表一条按时间推进的真实搜索轨迹：

- `generic prior` 是 truth distribution baseline，不是 chronological real search
- local validation 子集是已验证样本集合，不是连续 budget trace

所以如果要回答“同预算谁更强”，最干净的比较对象就是上面这三条 real-search 线。

---

## 3. 分析口径

本次固定预算切片为：

- `N = 100`
- `N = 200`
- `N = 400`
- `N = 800`

固定 band 为：

- `band180_220`
- `band200_240`
- `band220_260`
- `band240_280`

每个预算切片下，比较这些量：

- `best_cover_ratio`
- `best_overlap_Hz`
- `open_hit_count`
- `strong_hit_count`

其中：

- `open_hit_count`：该预算内 target band 有正 overlap 的样本数
- `strong_hit_count`：该预算内 `cover_ratio >= 0.5` 的样本数

这比只看最终一个 best 值更能说明：

- 哪条线更早进入正确区域
- 哪条线更早打出强样本
- 哪条线在弱 band 上是不是前期就开始领先

---

## 4. 数据输出位置

本次分析脚本：

- [analyze_same_budget_baselines_v1.py](/d:/graduation_project/coad/prediction_targetband_param_v1/tools/analyze_same_budget_baselines_v1.py)

输出目录：

- [same_budget_baselines_v1](/d:/graduation_project/coad/data/analysis/same_budget_baselines_v1)

关键文件：

- [same_budget_summary_v1.csv](/d:/graduation_project/coad/data/analysis/same_budget_baselines_v1/same_budget_summary_v1.csv)
- [same_budget_best_lines_v1.csv](/d:/graduation_project/coad/data/analysis/same_budget_baselines_v1/same_budget_best_lines_v1.csv)
- [same_budget_info_v1.json](/d:/graduation_project/coad/data/analysis/same_budget_baselines_v1/same_budget_info_v1.json)

---

## 5. 最重要的总体结论

这次同预算切片给出的结论很清楚：

**当前 strongest line 的优势，并不只是因为它最终总预算更大。**

更准确地说：

- 在 `band180_220 / band200_240 / band220_260` 上，
  `band_supplement_exploratory_v2` 在前 `100-200` 次真实评估内就已经开始领先。
- 在最难的 `band240_280` 上，
  `exploratory v2` 并不是一上来就赢，但在预算继续增加后会明显反超旧保守线。

所以 strongest line 的优势是两部分共同造成的：

1. **更好的前端**
   - predictor-guided
   - shape-aware
2. **更有效的搜索**
   - exploratory 参数范围
   - 历史避碰

而不是单纯“多跑一会儿”。

---

## 6. 分 band 解读

### 6.1 `band200_240`

这是最能说明问题的 band。

在 `N=100` 时：

- old band-catalog GA：best cover `0.296`
- conservative supplement：best cover `0.296`
- exploratory mainline：best cover `0.809`

同时，`exploratory` 在前 `100` 次评估里已经有：

- `open_hit_count = 19`
- `strong_hit_count = 4`

而旧两条线在同预算下：

- `strong_hit_count = 0`

到 `N=800` 时，`exploratory` 进一步到：

- best cover `1.000`
- best overlap `40.0 Hz`

这说明：

**在 `band200_240` 上，当前主线的优势从很早的预算阶段就已经出现，不是后期靠堆预算才追回来的。**

---

### 6.2 `band220_260`

这里的结论也很强。

在 `N=100` 时：

- old band-catalog GA：best cover `0.000`
- conservative supplement：best cover `0.086`
- exploratory mainline：best cover `0.309`

到 `N=800` 时：

- conservative supplement：best cover 仍只有 `0.086`
- exploratory mainline：best cover 已到 `1.000`

更重要的是：

- 保守线虽然 `open_hit_count` 很多，但一直打不出强样本
- `exploratory` 则真正把 cover 拉高了

这再次说明：

**只看 open rate 会误判，真正有意义的是强样本质量和 best cover 的增长。**

---

### 6.3 `band240_280`

这是最难的 band，也是最适合说明“预算视角不能偷懒”的 band。

在 `N=100` 时：

- conservative supplement：best cover `0.086`
- exploratory mainline：best cover `0.063`

这里保守线略高一点。

但从 `N=200` 开始，`exploratory` 反超：

- conservative supplement：`0.086`
- exploratory mainline：`0.112`

到 `N=800` 时差距被彻底拉开：

- conservative supplement：`0.086`
- exploratory mainline：`0.724`

所以在这个最难 band 上，结论不是：

- exploratory 一开始就全面碾压

而是：

- **exploratory 需要一定预算才能显出优势，但它一旦进入对的 basin，就能把旧保守线远远甩开。**

这其实更有说服力，因为它说明：

- 当前主线不是“碰巧首发抽中”
- 而是在更长一点的真实搜索里，能够逐渐把最难 band 打开

---

### 6.4 `band180_220`

这是相对成熟的 band。

在 `N=100` 时：

- old band-catalog GA：best cover `0.722`
- conservative supplement：best cover `0.749`
- exploratory mainline：best cover `0.915`

到 `N=800` 时：

- exploratory mainline：best cover `1.000`

而且它在强样本数上也明显领先：

- `N=400` 时，strong hit 已到 `69`
- `N=800` 时，strong hit 到 `215`

所以即便在相对成熟 band 上，当前 strongest line 也不是只在最终结果上赢，而是在预算早期就更快进入高质量区域。

---

## 7. 这一步最关键的解释意义

这次同预算分析帮助我们把 strongest line 的优势解释得更准确了。

### 7.1 能说明的

它可以说明：

- strongest line 的强，不只是“最终预算更大”
- 在多个 band 上，它在早期预算内就已经开始产生更高质量候选
- 尤其在 `200-240` 和 `220-260` 上，这种早期领先非常明显
- 在最难的 `240-280` 上，它虽然不是立刻领先，但随着预算推进会逐渐体现出真实优势

### 7.2 不能误说的

它不能被误写成：

- strongest line 在所有 band、所有预算阶段都从一开始绝对碾压

特别是 `band240_280`，更准确的说法是：

- 它需要一定预算去进入正确 basin
- 但一旦进入，提升幅度远大于旧保守线

这种写法更真实，也更可信。

---

## 8. 论文/汇报推荐口径

后面如果要用一句话讲这件事，我建议直接用：

> 同预算切片表明，当前 predictor-guided / shape-aware / exploratory 主线的优势并不只是来自更高总预算；在 `200-240` 和 `220-260` 等关键弱 band 上，它在前期真实评估阶段就已表现出更高的候选质量，而在最难的 `240-280` 上，则随着预算增加逐步展现出明显优势。

如果要更口语一点，可以说：

> 不是因为我们多跑了一会儿才赢，而是这条新主线在相同预算下就更容易更早找到对的区域，只是最难 band 需要稍微更多一点预算才能把优势完全体现出来。

---

## 9. 当前结论

这一步的最终结论是：

**“当前 strongest line 更强，是不是只是因为花了更多预算？”这个问题，现在可以明确回答：不是。**

更准确的答案是：

- strongest line 的优势主要来自更好的方向感和更合理的搜索入口
- 真实预算仍然重要，尤其对最难 band
- 但它的强，不是单纯靠“多跑”堆出来的

这也使得后面在论文中把 strongest line 定义为：

**predictor-guided + shape-aware + exploratory real-search mainline**

会更加站得住。
