# 第六章补图清单：ML 结果图 + 物理机制图

这份清单的目标很简单：把第六章从“机器学习结果章”拉回到“可解释的物理设计章”。

当前仓库里，第六章已经有一层完整的 ML 结果图，适合回答“模型有没有用”。
但如果正文只停在这层，读起来确实会偏机器学习。

所以建议第六章采用两层结构：

1. ML 结果图层
2. 物理机制图层

## 1. 已有的 ML 结果图

这些图已经在成品目录里，可以直接用于正文：

- [output/thesis_charts/chapter6/figure_6_1_predictor_readiness.png](/d:/graduation_project/coad/output/thesis_charts/chapter6/figure_6_1_predictor_readiness.png)
- [output/thesis_charts/chapter6/figure_6_2_canonical_cases.png](/d:/graduation_project/coad/output/thesis_charts/chapter6/figure_6_2_canonical_cases.png)
- [output/thesis_charts/chapter6/figure_6_3_baseline_comparison.png](/d:/graduation_project/coad/output/thesis_charts/chapter6/figure_6_3_baseline_comparison.png)
- [output/thesis_charts/chapter6/figure_6_4_weak_band_dashboard.png](/d:/graduation_project/coad/output/thesis_charts/chapter6/figure_6_4_weak_band_dashboard.png)
- [output/thesis_charts/chapter6/figure_6_5_stage4_validation.png](/d:/graduation_project/coad/output/thesis_charts/chapter6/figure_6_5_stage4_validation.png)
- [output/thesis_charts/chapter6/figure_6_6_local_robustness.png](/d:/graduation_project/coad/output/thesis_charts/chapter6/figure_6_6_local_robustness.png)

## 2. 建议一次性补齐的物理机制图

### P6-1 canonical band-edge mode shapes

用途：

- 解释 canonical case 为什么能“进带”
- 把 `predictor readiness` 和真实物理带边机制接起来
- 让第六章出现最像声子晶体论文的图

优先级：

- 4 个 canonical cases
- 每个 case 最少 2 张图，lower edge + upper edge

输出目录：

- `data/analysis/canonical_mode_shapes_v1/`

MATLAB 命令：

```matlab
run('d:/graduation_project/coad/runners/run_export_canonical_mode_shapes_v1.m')
```

### P6-2 archetype band-edge mode shapes

用途：

- 展示 `bilobe / asym / neck` 这类更“物理机理化”的候选
- 让第六章不只围绕 canonical cases
- 作为形状机制补强图放在正文或附录

优先级：

- 3 个 pilot archetype case
- 每个 case 2 张图，lower edge + upper edge

输出目录：

- `data/analysis/shape_archetype_targetband_mode_shapes_v1/`
- `output/thesis_charts/chapter6/physical_mechanism/shape_archetype_targetband_mode_shapes_v1/`

MATLAB 命令：

```matlab
run('d:/graduation_project/coad/runners/run_export_shape_archetype_targetband_mode_shapes_v1.m')
```

### P6-3 ep17 bilobe witness mode shapes

用途：

- 这是当前仓库里最像“物理证据”的强案例之一
- 适合解释 weak-band breakthrough 不是纯排序结果
- 可以直接给出 lower / upper edge 的模态图

输出目录：

- `data/analysis/ep17_bilobe_witness_case_v1/mode_shapes/`

MATLAB 命令：

```matlab
run('d:/graduation_project/coad/runners/run_export_ep17_bilobe_witness_mode_shapes_v1.m')
```

### P6-4 ep17 bilobe witness dispersion

用途：

- 这是 band diagram / dispersion 图
- 用来说明同一结构在不同 target band 下的边带关系
- 和 mode shape 搭配后，物理感会明显增强

输出目录：

- `data/analysis/ep17_bilobe_witness_case_v1/dispersion/`

Python 命令：

```powershell
python D:\graduation_project\coad\prediction_targetband_param_v1\tools\plot_ep17_bilobe_witness_dispersion_v1.py
```

### P6-5 canonical local robustness dispersion

用途：

- 这组图能把 `r0` 敏感性说得更直观
- 适合做“局部扰动下边带漂移”的物理说明
- 比单独的 robustness 表格更有论文感

输出目录：

- `data/analysis/canonical_local_robustness_v1/dispersion_plots/`

Python 命令：

```powershell
python D:\graduation_project\coad\prediction_targetband_param_v1\tools\plot_canonical_local_robustness_dispersion_v1.py
```

### P6-6 单 case 的 band diagram

用途：

- 需要一个更标准的“结构 - k 路径 - 能带”图时用
- 适合放在 canonical case 之后，作为单案例放大图
- 也适合放附录

输出方式：

```powershell
python D:\graduation_project\coad\postprocess\plot_tbl1_bands.py <某个_tbl1.csv>
```

建议挑的 case：

- 一个 canonical case
- 一个 weak-band case

可直接用的例子：

```powershell
python D:\graduation_project\coad\postprocess\plot_tbl1_bands.py D:\graduation_project\coad\data\comsol_batch\stage4_validation_targetband_top6_v1\tbl1_exports\stage4_validation_targetband_top6_v1_targetband_val001_tbl1.csv
python D:\graduation_project\coad\postprocess\plot_tbl1_bands.py D:\graduation_project\coad\data\comsol_batch\stage4_validation_targetband_local_robustness_v1\tbl1_exports\stage4_validation_targetband_local_robustness_v1_band200_240_ep193_center_tbl1.csv
python D:\graduation_project\coad\postprocess\plot_tbl1_bands.py D:\graduation_project\coad\data\comsol_batch\stage4_validation_shape_archetype_targetband_pilot_v1\tbl1_exports\stage4_validation_shape_archetype_targetband_pilot_v1_band240_280_pne253_center_tbl1.csv
```

推荐补图 case:
- `band220_260_pbi195`
- `band240_280_pas130`
- `band240_280_pne253`

### P6-7 bandgap summary / screening comparison

用途：

- 给“为什么这些 case 值得讲”再补一层 bandgap 总览
- 更适合附录，不建议抢正文主位

输出方式：

```powershell
python D:\graduation_project\coad\postprocess\analyze_bandgaps.py
python D:\graduation_project\coad\postprocess\plot_bandgap_summary.py --out-dir D:\graduation_project\coad\data\postprocess_out
```

## 3. 一次性补齐顺序

建议按这个顺序跑：

1. canonical band-edge mode shapes
2. ep17 bilobe witness mode shapes
3. archetype band-edge mode shapes
4. ep17 dispersion
5. local robustness dispersion
6. 单 case band diagram
7. bandgap summary
8. energy density / von Mises field maps

如果你想少敲命令，直接跑这个 MATLAB bundle 也可以：

```matlab
run('d:/graduation_project/coad/runners/run_ch6_physical_figure_bundle_v1.m')
```

这个顺序的好处是：

- 先把最能支撑正文的图拿到
- 再补更像机制解释的图
- 最后再补附录型图

## 4. 第六章建议写法

正文可以把第六章改成两层：

- `6.3 - 6.7` 主要讲 ML 结果和闭环验证
- `6.4 / 6.6 / 6.8` 或附录补物理机制图

如果你想让第六章更像声子晶体论文，而不是机器学习报告，最有效的组合是：

1. predictor readiness
2. canonical mode shapes
3. dispersion 图
4. weak-band / local robustness 机制图
5. stage4 validation

## 5. 关于能量密度、应力图

这类图现在已经补成了通用导出入口，和前面的 mode shape / dispersion 一样可以批处理跑。

新增脚本：

```matlab
run('d:/graduation_project/coad/runners/run_export_ch6_mechanism_field_maps_v1.m')
```

默认会导出两类场图：

- `solid.Ws`，对应 strain energy density
- `solid.mises`，对应 von Mises stress

默认会覆盖三组案例：

- canonical center cases
- ep17 bilobe witness case
- shape archetype target-band cases

输出目录：

- `data/analysis/ch6_mechanism_field_maps_v1/`
- `output/thesis_charts/chapter6/physical_mechanism/ch6_mechanism_field_maps_v1/`

如果你后面还想再加别的场量，只需要在这个 exporter 里再加一个 `fieldSpecs` 条目就行，不需要重写整条流程。
