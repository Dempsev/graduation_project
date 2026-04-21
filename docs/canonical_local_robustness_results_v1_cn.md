# Canonical Local Robustness Results V1

## 总结论

这轮 local neighborhood robustness 的结果很清楚：

- 当前 canonical inverse-design case **整体不是“极尖的单点偶然解”**
- 在 `a1 / a2 / b2` 这三个方向上，4 个案例都表现出**明显的局部稳定性**
- 真正敏感的方向主要是 **`r0`**
- 因此更准确的说法是：
  - 当前最优解更像是“**沿大部分 Fourier 参数方向较稳，但对半径参数更敏感的局部盆地**”
  - 而不是“所有方向都一样稳”的宽盆地

这对后面论文叙事是有利的，因为它说明：

- 我们不是只碰巧命中了一个点
- 但也确实识别出了最需要精修和鲁棒性约束的参数方向

## 数据位置

原始验证结果：

- [stage4_validation_results.csv](/d:/graduation_project/coad/data/comsol_batch/stage4_validation_targetband_local_robustness_v1/stage4_validation_results.csv)

后处理结果：

- [canonical_local_robustness_case_summary_v1.csv](/d:/graduation_project/coad/data/analysis/canonical_local_robustness_v1/canonical_local_robustness_case_summary_v1.csv)
- [canonical_local_robustness_variant_summary_v1.csv](/d:/graduation_project/coad/data/analysis/canonical_local_robustness_v1/canonical_local_robustness_variant_summary_v1.csv)
- [canonical_local_robustness_merged_v1.csv](/d:/graduation_project/coad/data/analysis/canonical_local_robustness_v1/canonical_local_robustness_merged_v1.csv)

## 各案例结果

### 1. `band180_220` -> `ep248_step27_contour_xy`

中心点：

- cover ratio = `1.000`
- overlap = `40.00 Hz`
- gap edges = `179.77 ~ 226.44 Hz`

局部保持率：

- `>= 90%` 中心点 cover 的扰动点：`6 / 8`
- `>= 80%` 中心点 cover 的扰动点：`6 / 8`
- 平均 cover 保持率：`0.940`

解释：

- `a1 / a2 / b2` 扰动后几乎都还能保持完整覆盖
- `r0` 扰动明显更敏感
  - `r0_plus` 下降到 `0.758`
  - `r0_minus` 下降到 `0.795`

判断：

- 这是一个**相当稳的局部盆地**
- 但 `r0` 不是自由乱调的变量

### 2. `band200_240` -> `ep193_step51_contour_xy`

中心点：

- cover ratio = `1.000`
- overlap = `40.00 Hz`
- gap edges = `197.86 ~ 259.60 Hz`

局部保持率：

- `>= 90%` 中心点 cover 的扰动点：`7 / 8`
- `>= 80%` 中心点 cover 的扰动点：`7 / 8`
- 平均 cover 保持率：`0.870`

解释：

- `a1 / a2 / b2` 六个扰动点全部保持 `1.000`
- `r0_minus` 仍有较高保持率：`0.961`
- 只有 `r0_plus` 完全塌掉，cover = `0`

判断：

- 这是一个**很稳的 target-band 设计解**
- 而且比 `band180_220` 更有意思，因为它说明弱 band 上也能找到局部稳定解
- 但 `r0` 向增大方向非常敏感

### 3. `band220_260` -> `ep253_step54_contour_xy`

中心点：

- cover ratio = `1.000`
- overlap = `40.00 Hz`
- gap edges = `208.43 ~ 275.92 Hz`

局部保持率：

- `>= 90%` 中心点 cover 的扰动点：`6 / 8`
- `>= 80%` 中心点 cover 的扰动点：`7 / 8`
- 平均 cover 保持率：`0.851`

解释：

- `a1 / a2 / b2` 六个扰动点全部保持 `1.000`
- `r0_minus` 下降到 `0.805`
- `r0_plus` 直接塌到 `0`

判断：

- 这是一个**结构上稳、但半径方向偏敏感**的解
- 对 `220-260 Hz` 这样更高一点的 band，这个结果已经很强

### 4. `band240_280` -> `ep253_step54_contour_xy`

中心点：

- cover ratio = `0.898`
- overlap = `35.93 Hz`
- gap edges = `208.43 ~ 275.93 Hz`

局部保持率：

- `>= 90%` 中心点 cover 的扰动点：`6 / 8`
- `>= 80%` 中心点 cover 的扰动点：`6 / 8`
- 平均 cover 保持率：`0.786`

解释：

- `a1 / a2 / b2` 扰动后，仍大致保持在 `0.84 ~ 0.94`
- 其中 `a1_plus` 还略有提升，达到 `0.940`
- `r0_minus` 明显掉到 `0.305`
- `r0_plus` 直接塌到 `0`

判断：

- 这是 4 个案例里**最难的 band**
- 但即便如此，`a1 / a2 / b2` 方向仍表现出局部稳定性
- 真正不稳定的依然是 `r0`

## 统一解释

4 个案例放在一起看，规律非常一致：

### 稳定方向

- `a1`
- `a2`
- `b2`

这几个方向的小范围扰动，通常只会造成：

- 很小的 gap edge 平移
- 或很小的 cover 波动

并不会立刻把 target-band 设计打崩。

### 敏感方向

- `r0`

在 4 个案例中：

- `r0_plus` 有 `3` 个案例直接掉到 `0`
- `r0_minus` 虽然不总是完全崩，但也显著下降

这说明：

- 半径参数是当前 canonical 解最敏感的局部方向
- 后面如果要做 refinement-aware 或 robustness-aware optimization，`r0` 应该被单独重点约束

## 对论文主线意味着什么

这轮结果可以支持下面这个更成熟的表述：

- 当前 thesis band catalog 内的 canonical inverse-design solutions 并非单点偶然命中
- 在主要 Fourier 参数方向上存在局部稳定邻域
- 但半径参数 `r0` 显著更敏感，因此后续 refinement 和 robustness-aware optimization 应将其作为重点控制变量

也就是说，最准确的话不是：

- “我们的设计完全稳健”

而是：

- “我们的设计已经形成局部稳定盆地，但稳定性具有明显各向异性；`a1/a2/b2` 相对稳，`r0` 更敏感。”

这个结论比简单说“稳”或“不稳”都更有说服力。

## 建议后续动作

基于这轮结果，后面最自然的两个动作是：

1. 在 refinement 阶段对 `r0` 加更明确的约束或更细的局部搜索策略
2. 在 robustness-aware 分析里，把 `r0` 单列成重点敏感变量

这样后面“预测 + 优化 + 精修”的故事会更完整：

- predictor 给方向
- real search 找到可用解
- local robustness 告诉我们哪些参数可以放心微调，哪些参数必须谨慎控制
