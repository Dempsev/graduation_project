# Shape Archetype Pilot v1

## 1. 目标

这是“优先级 2：做小而异质的新 shape 子库”的第一版 pilot。

目标不是一次扩很多 shape，而是先引入三类与当前库机制不同的 archetype：

1. 更强非对称 family
2. 更明显窄颈 / 桥接 family
3. 更明显双叶 / 偏心质量分布 family

## 2. 当前生成策略

本版不重新跑 snake，而是基于现有 weak-band 相关 seed contour 做几何变换，生成一批 pilot contour：

- seed 形状：
  - `ep130_step66_contour_xy`
  - `ep183_step60_contour_xy`
  - `ep195_step9_contour_xy`
  - `ep253_step54_contour_xy`

- archetype：
  - `asym`
  - `neck`
  - `bilobe`

- strength：
  - `mild`
  - `medium`
  - `strong`

总计：

- `3` 个 archetype
- `4` 个 seed
- `3` 个强度
- 共 `36` 个新 shape

## 3. 命名规则

为兼容现有 family 提取逻辑，shape id 采用：

- `pas***_step**_contour_xy`：asymmetry
- `pne***_step**_contour_xy`：neck-bridge
- `pbi***_step**_contour_xy`：bilobe-offset

其中 family 由 id 第一个 `_` 前的前缀确定。

## 4. 已生成文件

### 生成脚本

- [generate_shape_archetype_pilot_v1.py](/d:/graduation_project/coad/preprocess/generate_shape_archetype_pilot_v1.py)

### 输出目录

- contour CSV：`D:\graduation_project\coad\data\shape_contours`
- catalog / summary / whitelist：`D:\graduation_project\coad\data\analysis\shape_archetype_pilot_v1`

### 关键输出

- [shape_archetype_pilot_catalog_v1.csv](/d:/graduation_project/coad/data/analysis/shape_archetype_pilot_v1/shape_archetype_pilot_catalog_v1.csv)
- [shape_archetype_pilot_whitelist_v1.json](/d:/graduation_project/coad/data/analysis/shape_archetype_pilot_v1/shape_archetype_pilot_whitelist_v1.json)
- [shape_archetype_pilot_summary_v1.json](/d:/graduation_project/coad/data/analysis/shape_archetype_pilot_v1/shape_archetype_pilot_summary_v1.json)

### 预览图

- [asym preview](/d:/graduation_project/coad/data/analysis/shape_archetype_pilot_v1/shape_archetype_asym_preview_v1.png)
- [neck preview](/d:/graduation_project/coad/data/analysis/shape_archetype_pilot_v1/shape_archetype_neck_preview_v1.png)
- [bilobe preview](/d:/graduation_project/coad/data/analysis/shape_archetype_pilot_v1/shape_archetype_bilobe_preview_v1.png)

## 5. 这一批怎么用

这批 pilot shape 当前最适合三种用途：

1. 做 whitelist pilot screening  
   用 whitelist 只让这 36 个 shape 进入一轮小筛选。

2. 做 atlas upgrade pilot  
   先局部加入 atlas，观察 `best_band_tag` 和 weak-band role 是否变化。

3. 做少量 stage4 probe  
   先挑部分 archetype shape 在固定点或小范围 trust-region 下做真验证。

## 6. 何时算成功

这批 pilot 至少满足下面一项，才值得继续扩大：

1. 出现新的高 weak-band strong family
2. 新 shape 的 `best_band_tag` 明显上移
3. mode shape 机制明显不同于 `ep248 / ep253`
4. 形成稳定的新 near-miss / failure pattern

如果这些都没出现，就说明这批 archetype 只是“换了外形”，但没有带来新物理信息。
