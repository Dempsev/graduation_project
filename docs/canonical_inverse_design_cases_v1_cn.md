# Canonical Inverse-Design Cases V1

## 1. 目的

本文件用于固定当前 thesis 主线下的第一批 canonical inverse-design cases。

它们的作用不是简单展示“找到了几个好结果”，而是作为后续论文、汇报、对照实验中的标准案例，用来回答：

- predictor-guided / shape-aware / exploratory 主线到底找到了什么
- 弱 band 是否真的被打通了
- 与旧 baseline 相比，提升有多大

当前案例全部来自：

- [ga_band_catalog_summary_v1.csv](/d:/graduation_project/coad/data/comsol_batch/comsol_in_loop_band_supplement_exploratory_v2/ga_band_catalog_summary_v1.csv)

对照基线来自：

- 旧 conservative supplement：
  - [ga_band_catalog_summary_v1.csv](/d:/graduation_project/coad/data/comsol_batch/comsol_in_loop_band_supplement_ga_v1/ga_band_catalog_summary_v1.csv)
- 旧 band-catalog real GA：
  - [ga_band_catalog_summary_v1.csv](/d:/graduation_project/coad/data/comsol_batch/comsol_in_loop_band_catalog_ga_v1/ga_band_catalog_summary_v1.csv)

## 2. 当前固定案例

当前建议固定的第一批 canonical cases 为：

1. `band200_240`
   - `ep193_step51_contour_xy`
2. `band220_260`
   - `ep253_step54_contour_xy`
3. `band240_280`
   - `ep253_step54_contour_xy`
4. `band180_220`
   - `ep248_step27_contour_xy`

## 3. Case A: `band200_240`

### 结构身份

- target band: `200-240 Hz`
- shape id: `ep193_step51_contour_xy`
- shape family: `ep193`

### 优化参数

- `a1 = 0.527790`
- `a2 = -0.007262`
- `b2 = -0.005107`
- `a4 = -0.014955`
- `b5 = -0.014820`
- `r0 = 0.015544`

### 真实结果

- cover ratio: `1.0000`
- overlap: `40.00 Hz`
- gap lower edge: `197.87 Hz`
- gap upper edge: `259.61 Hz`
- gap width: `61.73 Hz`
- gap34 gain: `60.59 Hz`

### 与旧 baseline 对比

相对 conservative supplement：

- cover 提升：`+0.6769`
- overlap 提升：`+27.08 Hz`
- 旧 best shape：`ep571_step57_contour_xy`

相对旧 band-catalog real GA：

- cover 提升：`+0.7036`
- overlap 提升：`+28.14 Hz`
- 旧 best shape：`ep205_step69_contour_xy`

### 解读

这是当前最能说明“弱 band 已被真正打通”的案例。

它的重要性在于：

- `band200_240` 以前正是最难、最缺、最不稳定的目标 band
- 现在不仅打开了，而且实现了完整 `40 Hz` 覆盖
- 相比旧保守线和旧 catalog GA，都不是小幅改善，而是质变

## 4. Case B: `band220_260`

### 结构身份

- target band: `220-260 Hz`
- shape id: `ep253_step54_contour_xy`
- shape family: `ep253`

### 优化参数

- `a1 = 0.539290`
- `a2 = -0.008477`
- `b2 = 0.018033`
- `a4 = 0.014288`
- `b5 = -0.000140`
- `r0 = 0.016000`

### 真实结果

- cover ratio: `1.0000`
- overlap: `40.00 Hz`
- gap lower edge: `208.43 Hz`
- gap upper edge: `275.93 Hz`
- gap width: `67.49 Hz`
- gap34 gain: `66.35 Hz`

### 与旧 baseline 对比

相对 conservative supplement：

- cover 提升：`+0.9142`
- overlap 提升：`+36.57 Hz`
- 旧 best shape：`ep195_step39_contour_xy`

旧 band-catalog real GA 没有这个 band 的直接案例，因此这里主要和 conservative supplement 比。

### 解读

这个案例说明：

- `220-260` 这种更高、更稀疏的 band 不是只能擦边命中
- 在 shape-aware + exploratory 主线下，已经可以做到完整覆盖

这是支持“catalog 内 target-band inverse design 已成立”的关键案例之一。

## 5. Case C: `band240_280`

### 结构身份

- target band: `240-280 Hz`
- shape id: `ep253_step54_contour_xy`
- shape family: `ep253`

### 优化参数

与 `band220_260` 最优案例相同：

- `a1 = 0.539290`
- `a2 = -0.008477`
- `b2 = 0.018033`
- `a4 = 0.014288`
- `b5 = -0.000140`
- `r0 = 0.016000`

### 真实结果

- cover ratio: `0.8982`
- overlap: `35.93 Hz`
- gap lower edge: `208.43 Hz`
- gap upper edge: `275.93 Hz`
- gap width: `67.49 Hz`
- gap34 gain: `66.35 Hz`

### 与旧 baseline 对比

相对 conservative supplement：

- cover 提升：`+0.8124`
- overlap 提升：`+32.49 Hz`
- 旧 best shape：`ep195_step39_contour_xy`

旧 band-catalog real GA 没有这个 band 的直接案例。

### 解读

这是当前最强的高频稀疏 band 案例。

它说明：

- 即使 `240-280` 还没有做到完整 `1.000` 覆盖
- 但已经从旧 baseline 的几乎打不开，推进到了接近完整覆盖的水平

在论文里，这个案例非常适合作为“高难 target-band”展示。

## 6. Case D: `band180_220`

### 结构身份

- target band: `180-220 Hz`
- shape id: `ep248_step27_contour_xy`
- shape family: `ep248`

### 优化参数

- `a1 = 0.556440`
- `a2 = 0.000000`
- `b2 = 0.067982`
- `a4 = 0.041097`
- `b5 = -0.021030`
- `r0 = 0.014240`

### 真实结果

- cover ratio: `1.0000`
- overlap: `40.00 Hz`
- gap lower edge: `179.77 Hz`
- gap upper edge: `226.44 Hz`
- gap width: `46.67 Hz`
- gap34 gain: `45.53 Hz`

### 与旧 baseline 对比

相对 conservative supplement：

- cover 提升：`+0.2271`
- overlap 提升：`+9.08 Hz`
- 旧 best shape：`ep571_step57_contour_xy`

相对旧 band-catalog real GA：

- cover 提升：`+0.2778`
- overlap 提升：`+11.11 Hz`
- 旧 best shape：`ep205_step69_contour_xy`

### 解读

`180-220` 不是最难 band，但它仍然重要，因为：

- 它是 thesis 主线里最自然的中频参考 band
- 现在也已经被提升到完整覆盖
- 适合做“成熟 target-band 设计能力”的标准展示案例

## 7. 整体结论

这一批 canonical cases 共同说明：

1. 现在的主线已经不只是“会筛选”
   - 而是能在真实 COMSOL 约束下得到明确的 target-band 结构

2. 弱 band 的突破是真实存在的
   - `band200_240`
   - `band220_260`
   - `band240_280`
   都已经显著优于旧 baseline

3. shape-aware + exploratory 是关键
   - 这批案例不是靠旧保守搜索自然冒出来的
   - 它们依赖新的 shape pool、探索范围和避碰策略

## 8. 建议用途

这四个案例建议后续固定用于：

- 论文结果展示
- 汇报主案例
- predictor-guided line 与 baseline 的定性比较
- 后续 robustness 分析的候选对象

后面如果要再扩案例，建议优先在这四个之外增加：

- 一个失败/near-miss 反例
- 一个“预测前排但真实 refinement 没成功”的边界案例

这样案例体系会更完整。 
