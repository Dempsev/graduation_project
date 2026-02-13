# COAD 项目流程（COMSOL + MATLAB + Python）

本项目用于从贪吃蛇状态生成几何形状，批量建模求解 COMSOL，并导出 `tbl1` 结果。

## 当前主流程
1. `snake/` 生成状态
2. `preprocess/` 将状态转换为轮廓点
3. `runners/run_shape_batch.m` 批量建模与计算
4. `postprocess/` 做后处理分析

## 主要目录
```text
coad/
  model_core/
    create_open_00.m
    build_geom_02.m
    set_material_03.m
    set_physics_04.m
    set_mesh_05.m
    set_study_06.m
    set_results_07.m
  runners/
    run_shape_batch.m
    legacy_run/
      main_batch.m
      run_comsol_once.m
      run_sweep_export_eig*.m
  snake/
  preprocess/
  postprocess/
  data/
    shape_points/
    shape_batch/
      models/
      tbl1_exports/
      logs/
        run_shape_batch_errors.csv
      perturb_skip_log.csv
    snake_states/
    snake_checkpoints/
    shape_previews/
```

## 批处理运行入口
```matlab
cd('d:\graduation_project\coad\runners');
run('run_shape_batch.m');
```

## 批处理行为说明
- 与傅里叶边界不接触的离散扰动样本会被跳过。
- 跳过记录写入：`data/shape_batch/perturb_skip_log.csv`。
- 运行期错误写入：`data/shape_batch/logs/run_shape_batch_errors.csv`，并自动继续下一个样本。
- 有效模型保存到：`data/shape_batch/models/`。
- `tbl1` 仅输出到：`data/shape_batch/tbl1_exports/`。
- `tbl1` 文件名使用形状名（例如 `ep1084_step120_tbl1.csv`），不再用时间戳。

## 备注
- 周期边界条件已改为按矩形位置自动选边：`kx` 选左右边，`ky` 选上下边，不再依赖固定边界编号。
- 历史脚本已归档到 `runners/legacy_run/`。
