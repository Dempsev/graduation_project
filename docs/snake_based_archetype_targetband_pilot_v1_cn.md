# snake_based_archetype_targetband_pilot_v1

## 目标

把 snake-based archetype expansion pilot 中的 top 候选，接到 target-band 专用 stage4 评估里。

这一步仍然是隔离 pilot，不并入 frozen mainline。

## 候选来源

来自：

- `data/snake_based_archetype_expansion_pilot_v1/analysis/snake_based_archetype_pilot_top_by_type_v1.csv`

选择规则：

- 每个 archetype 类型取 top `4` 个 shape
- archetype 类型：
  - `bilobe`
  - `asym`
  - `neck`

总计：

- `12` 个代表 shape
- 每个代表 shape 跑 `3` 个 target band
- 共 `36` 个 stage4 点

## 当前评估设置

使用固定 baseline point：

- `a1 = 0.45`
- `a2 = 0.0`
- `b2 = 0.0`
- `r0 = 0.012`

目的不是直接做最终优化，而是先看：

1. 新 snake shape 的 `best_band_tag` 是否上移；
2. 有没有新的 weak-band contributor / strong 候选；
3. 哪类 snake-grown archetype 最值得继续扩展。

## 文件

- manifest builder:
  [build_snake_based_archetype_targetband_manifest_v1.py](/d:/graduation_project/coad/optimization/seed_ranking/build_snake_based_archetype_targetband_manifest_v1.py)
- stage4 config:
  [get_stage4_validation_config_sbatp_v1.m](/d:/graduation_project/coad/stage4_validation/get_stage4_validation_config_sbatp_v1.m)
- runner:
  [run_stage4_validation_sbatp_v1.m](/d:/graduation_project/coad/runners/run_stage4_validation_sbatp_v1.m)

## 运行方式

先生成 manifest：

```powershell
python D:\graduation_project\coad\optimization\seed_ranking\build_snake_based_archetype_targetband_manifest_v1.py
```

再在 MATLAB 中运行：

```matlab
run('d:/graduation_project/coad/runners/run_stage4_validation_sbatp_v1.m')
```

## 后续分析

跑完以后，建议复用 target-band 后处理思路，重点看：

1. `best_band_tag`
2. `target_gap_overlap_Hz`
3. `target_gap_cover_ratio`
4. `target_gap_lower_band / upper_band`
5. `actual_role`

如果这一轮确认：

- `bilobe` 继续最强
- `asym` 次之
- `neck` 仍偏局部连接控制

那么下一阶段就可以更明确地把 snake-based 扩展优先级固定为：

1. `bilobe`
2. `asym`
3. `neck`
