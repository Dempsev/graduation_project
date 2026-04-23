# Shape Archetype Target-Band Pilot v1

## 1. 目标

把手工 archetype pilot 从 `stage1` 的可行性 smoke test，推进到 `target-band` 专用评估。

这一轮不追求大规模扩样本，只做一个小而干净的代表子集：

- 每个 `seed family x archetype` 只保留 1 个代表 shape
- 代表 shape 的选择依据：`stage1` 中 `gap_gain_Hz` 最优
- 对每个代表 shape，分别评估：
  - `band200_240`
  - `band220_260`
  - `band240_280`

## 2. 当前规模

- seed family: `ep130`, `ep183`, `ep195`, `ep253`
- archetype: `asym`, `bilobe`, `neck`
- 代表 shape: `12`
- target bands: `3`
- manifest rows: `36`

## 3. 关键文件

- manifest builder:
  [build_shape_archetype_targetband_pilot_manifest_v1.py](/d:/graduation_project/coad/optimization/seed_ranking/build_shape_archetype_targetband_pilot_manifest_v1.py)
- manifest:
  [shape_archetype_targetband_pilot_manifest_v1.csv](/d:/graduation_project/coad/data/ml_runs/shape_archetype_targetband_pilot_v1/validation_manifest_v1/shape_archetype_targetband_pilot_manifest_v1.csv)
- representatives:
  [shape_archetype_targetband_pilot_representatives_v1.csv](/d:/graduation_project/coad/data/ml_runs/shape_archetype_targetband_pilot_v1/validation_manifest_v1/shape_archetype_targetband_pilot_representatives_v1.csv)
- summary:
  [shape_archetype_targetband_pilot_manifest_summary_v1.json](/d:/graduation_project/coad/data/ml_runs/shape_archetype_targetband_pilot_v1/validation_manifest_v1/shape_archetype_targetband_pilot_manifest_summary_v1.json)

## 4. 如何运行

MATLAB:

```matlab
run('d:/graduation_project/coad/runners/run_stage4_validation_satbp_v1.m')
```

stage4 配置入口：

- [get_stage4_validation_config_satbp_v1.m](/d:/graduation_project/coad/stage4_validation/get_stage4_validation_config_satbp_v1.m)
- [run_stage4_validation_satbp_v1.m](/d:/graduation_project/coad/runners/run_stage4_validation_satbp_v1.m)

## 5. 这一轮最想回答的问题

1. 这批 hand-made pilot shape 的 `best_band_tag` 会不会向高 weak band 上移
2. 是否有某类 archetype 在 `200-240 / 220-260 / 240-280` 上更容易形成有效 overlap
3. 是否会出现和当前 canonical family 不同的 weak-band 行为模式
4. 哪些 archetype 只是“能跑”，但并没有带来 target-band 新信息
