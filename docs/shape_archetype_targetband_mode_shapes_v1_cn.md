# shape_archetype_targetband_mode_shapes_v1

## 目标

为 hand-made archetype pilot 中最值得解释“不同带边机制”的 3 个代表 case 导出 band-edge mode shape 图。

## 当前选中的 case

1. `band220_260__bilobe__ep195`
   - `shape_id = pbi195_step36_contour_xy`
   - best cover = `1.000`
   - gap pair = `1-2`
   - 这是当前最强的“明显不同于 canonical 3-4”候选。

2. `band240_280__asym__ep130`
   - `shape_id = pas130_step12_contour_xy`
   - best cover = `1.000`
   - gap pair = `2-3`
   - 用于看更强非对称是否稳定把优势推到更低 band pair。

3. `band240_280__neck__ep253`
   - `shape_id = pne253_step24_contour_xy`
   - best cover = `0.6885`
   - gap pair = `2-3`
   - 用于看窄颈 / 桥接 archetype 是否也引入了和 canonical 不同的 mode organization。

## 导出入口

在 MATLAB + COMSOL LiveLink 中运行：

```matlab
run('d:/graduation_project/coad/runners/run_export_shape_archetype_targetband_mode_shapes_v1.m')
```

## 输出目录

导出结果会写到：

- `data/analysis/shape_archetype_targetband_mode_shapes_v1/`
- `output/thesis_charts/chapter6/physical_mechanism/shape_archetype_targetband_mode_shapes_v1/`

并生成：

- 每个 case 一个子目录
- `lower_edge.png`
- `upper_edge.png`
- `shape_archetype_targetband_mode_shapes_summary_v1.csv`

## 解释重点

这批图的目标不是证明“手工 shape 已经正式进主库”，而是验证：

1. `1-2 / 2-3` 的高 weak-band strong 候选是否真的对应不同于 canonical `3-4` 的 band-edge 模态组织；
2. `bilobe / asym / neck` 三种 archetype 里，哪一种最明显地引入了新机制；
3. 是否值得把这些有效 archetype 翻译成下一阶段更正式的 snake-based 定向生成目标。
