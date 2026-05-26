# 第4章设计变量与约束条件表

## 设计变量

| variable_name | physical_meaning | variable_type | lower_bound | upper_bound | used_in_ga | note |
| --- | --- | --- | --- | --- | --- | --- |
| shape_id | 单胞夹杂轮廓/结构族离散基因 | categorical | shape_pool候选集合 | 54个候选轮廓 | True | 形状基因来自预筛选轮廓库，非连续参数 |
| a1 | 一阶余弦形状参数 | continuous | 0.4600 | 0.5400 | True | clip_to_bounds约束在全局上下限内 |
| a2 | 二阶余弦形状参数 | continuous | -0.1800 | -0.0600 | True | clip_to_bounds约束在全局上下限内 |
| b1 | 一阶正弦形状参数 | continuous | -0.0500 | 0.0500 | True | clip_to_bounds约束在全局上下限内 |
| b2 | 二阶正弦形状参数 | continuous | 0 | 0.0800 | True | clip_to_bounds约束在全局上下限内 |
| a3 | 三阶余弦形状参数 | continuous | -0.0400 | 0.0400 | True | clip_to_bounds约束在全局上下限内 |
| b3 | 三阶正弦形状参数 | continuous | -0.0400 | 0.0400 | True | clip_to_bounds约束在全局上下限内 |
| a4 | 四阶余弦形状参数 | continuous | -0.0300 | 0.0300 | True | clip_to_bounds约束在全局上下限内 |
| b4 | 四阶正弦形状参数 | continuous | -0.0300 | 0.0300 | True | clip_to_bounds约束在全局上下限内 |
| a5 | 五阶余弦形状参数 | continuous | -0.0200 | 0.0200 | True | clip_to_bounds约束在全局上下限内 |
| b5 | 五阶正弦形状参数 | continuous | -0.0200 | 0.0200 | True | clip_to_bounds约束在全局上下限内 |
| r0 | 基准半径/尺度参数 | continuous | 0.0100 | 0.0140 | True | clip_to_bounds约束在全局上下限内 |

## 约束条件

| constraint_name | mathematical_form | implementation | role_in_ga |
| --- | --- | --- | --- |
| parameter_range_constraint | x_j in [lower_j, upper_j] | 连续变量交叉和变异后通过 clip_to_bounds 截断到 globalBounds | 限定设计变量可行域 |
| geometry_valid constraint | geometry_valid = 1 | 几何无效时 fitness = failurePenaltyGeometry | 排除不可建模几何 |
| contact_valid constraint | contact_valid = 1 | 接触无效时 fitness = failurePenaltyContact | 保证夹杂/基体接触关系满足计算要求 |
| solve_success constraint | solve_success = 1 | COMSOL 求解失败时 fitness = failurePenaltySolve | 保证频散结果可用于适应度评价 |
| target_overlap_Hz > 0 active constraint | target_overlap_Hz > 0 | 统计有效候选时使用，不作为硬约束；适应度直接最大化 target_overlap_Hz | 定义有效候选并衡量目标频带命中情况 |
