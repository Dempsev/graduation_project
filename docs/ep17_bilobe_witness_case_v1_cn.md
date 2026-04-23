# ep17 Bilobe Witness Case v1

## 1. 这份文档的目的

把 `ep17_step156_contour_xy` 收成一个可直接写进论文/汇报的 snake-based bilobe witness case。

当前这条 witness case 的定位是：

- 它不是一个已经扩成稳定盆地的大 family
- 它是一个稳定复现的高价值单点 archetype witness
- 它的价值在于：
  - 证明 snake-based bilobe 确实能推到高 weak band
  - 证明这条线对应的 band-edge mechanism 不同于现有 canonical `3-4`

## 2. 当前最稳的核心结论

- 在 `bilobe-only contact-aware snake v2` 中，`ep17_step156_contour_xy` 稳定打出 `band220_260`
- 该 case 的最优 target band 为：
  - `band220_260`
  - `target_gap_cover_ratio = 0.5462`
  - `target_gap_overlap_Hz = 21.85`
  - `target_gap_lower_band = 2`
  - `target_gap_upper_band = 3`
- `ep17` 其他近邻成员目前没有一起站起来，因此它更适合被解释成：
  - `bilobe snake witness case`
  - 而不是已经成熟的 `ep17 family basin`

## 3. witness case 图证包

建议固定这两类图：

### 3.1 mode shape

只导出 `band220_260` 这一个 strong case 的上下边界模态图。

原因：

- 这是唯一稳定 strong 的 band
- 也是最适合做 snake-based bilobe 物理解释的 case
- 不需要把 `200-240 / 240-280` 的 hard negative 也做成 mode shape 主图

对应脚本：

- MATLAB 导出脚本：
  [export_ep17_bilobe_witness_mode_shapes_v1.m](/d:/graduation_project/coad/postprocess/export_ep17_bilobe_witness_mode_shapes_v1.m)
- MATLAB runner：
  [run_export_ep17_bilobe_witness_mode_shapes_v1.m](/d:/graduation_project/coad/runners/run_export_ep17_bilobe_witness_mode_shapes_v1.m)

输出目录：

- [ep17_bilobe_witness_case_v1/mode_shapes](/d:/graduation_project/coad/data/analysis/ep17_bilobe_witness_case_v1/mode_shapes)

### 3.2 dispersion 对照

把同一个 `ep17_step156` 在：

- `band200_240`
- `band220_260`
- `band240_280`

这三个 target band 下的 dispersion 放在一张 1x3 图里。

这样可以直接回答：

- 为什么它在 `220-260` 打出来
- 为什么同一个 shape 在 `200-240 / 240-280` 没有同样强的 cover

对应脚本：

- Python 画图脚本：
  [plot_ep17_bilobe_witness_dispersion_v1.py](/d:/graduation_project/coad/prediction_targetband_param_v1/tools/plot_ep17_bilobe_witness_dispersion_v1.py)

输出目录：

- [ep17_bilobe_witness_case_v1/dispersion](/d:/graduation_project/coad/data/analysis/ep17_bilobe_witness_case_v1/dispersion)

## 4. 推荐运行方式

### 4.1 导出 mode shape

在 MATLAB 中运行：

```matlab
run('d:/graduation_project/coad/runners/run_export_ep17_bilobe_witness_mode_shapes_v1.m')
```

### 4.2 生成 dispersion 图

在终端中运行：

```powershell
python D:\graduation_project\coad\prediction_targetband_param_v1\tools\plot_ep17_bilobe_witness_dispersion_v1.py
```

## 5. 关于“优先级 2 是否已经完成”的判断

我的判断是：

**可以认为优先级 2 已经完成。**

但这里的“完成”是指：

- 已完成 `mechanism-probe + direction-selection`
- 不等于已经完成“大规模正式扩库”

之所以可以算完成，是因为它已经满足了当初定义的目标：

1. hand-made pilot 把 `best_band_tag` 明显推向更高 weak band
2. mode shape 已经显示出不同于 canonical `3-4` 的机制
3. snake-based follow-up 明确筛出了：
   - `bilobe` 是第一优先级
   - `asym` 第二
   - `neck` 第三
4. `bilobe-only contact-aware v2` 已经给出了一个稳定的 snake-based witness case：`ep17_step156`

所以现在最合理的说法不是“第二步还没做完”，而是：

> 第二步作为机制探索与方向筛选阶段已经完成；如果后续继续做，那属于基于既有结论的下一阶段放大，而不是还在补第二步本身。

## 6. 后续如何使用这条 witness case

最合适的使用方式是：

- 论文里把它作为 snake-based bilobe witness case
- 用来支撑“新的 shape mechanism 可以把自然优势推向更高 weak band”
- 同时明确说明：
  - 它是稳定 witness
  - 但目前还不是大面积 family basin

这会比硬把它写成“已经找到成熟 bilobe family”更稳。 
