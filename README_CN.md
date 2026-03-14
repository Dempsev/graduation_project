# COAD：面向带隙设计的声子晶体/力学超结构流程仓库

## 项目目标

本仓库对应一个毕设项目，目标是围绕**声子晶体 / 力学超结构的带隙优化设计**，逐步建立如下研究流程：

```text
结构生成
-> COMSOL 有限元仿真
-> 能带计算
-> 带隙提取
-> 数据集构建
-> 代理模型训练
-> 优化设计 / 逆向设计
```

当前仓库主要落在这条链路的**前半段**，也就是：

- 生成结构
- 批量进行 COMSOL 建模与计算
- 导出特征频率结果
- 对导出的 `tbl1` 数据做带隙分析

## 结构表达方式

当前项目中的结构可以理解为由两部分共同构成：

1. **连续边界参数化**
   COMSOL 几何侧保留了基于傅里叶参数的连续边界建模思路，用于描述整体轮廓。
2. **离散局部拓扑**
   局部拓扑来自贪吃蛇流程生成的 `32 x 32` 二值矩阵。这里所说的“32×32 二值结构”，本质上就是这些贪吃蛇生成出来的矩阵样本。

从当前代码的可执行主线来看，最明确的流程是：

```text
贪吃蛇矩阵
-> 轮廓提取
-> COMSOL 重建几何
-> 求解并导出 tbl1
-> 带隙后处理
```

## 当前仓库状态

目前仓库已经具备以下基础能力：

- 批量生成贪吃蛇状态矩阵
- 将二值矩阵转换为轮廓点 CSV
- 根据轮廓点批量重建 COMSOL 模型
- 运行 study/batch compute 并导出 `tbl1`
- 从 `tbl1` 中提取 band table 与 bandgap 汇总
- 生成带隙统计图和单 case 的 band diagram

当前**尚未完全完成**的部分主要是面向机器学习的数据工程，包括：

- 稳定的单样本打包格式
- 统一的数据集组织方式
- `structure -> bandgap` 训练集构建
- 代理模型训练与优化闭环

## 当前主流程

1. 在 [`snake/`](/d:/graduation_project/coad/snake) 中生成二值状态
2. 在 [`preprocess/`](/d:/graduation_project/coad/preprocess) 中提取轮廓点
3. 通过 [`runners/run_shape_batch.m`](/d:/graduation_project/coad/runners/run_shape_batch.m) 批量建模与求解
4. 在 [`postprocess/`](/d:/graduation_project/coad/postprocess) 中做 `tbl1` 后处理

## 主要目录

```text
coad/
  model_core/           COMSOL 建模模块
  runners/              批处理入口脚本
  snake/                贪吃蛇环境与状态生成
  preprocess/           二值矩阵 -> 轮廓点
  postprocess/          tbl1 解析、带隙分析、绘图
  data/
    snake_state_matrices/      生成的 32 x 32 二值矩阵
    snake_run_checkpoints/     贪吃蛇检查点与元数据
    shape_contours/            轮廓点 CSV
    shape_contour_previews/    轮廓预览图
    comsol_batch/
      models/           保存的 .mph 文件
      tbl1_exports/     COMSOL 导出的 tbl1 CSV
      logs/             批处理错误日志
      perturb_skip_log.csv
    postprocess_out/
      case_band_tables/        分 case 的 band 表
      manual_band_diagrams/    单次导出的手动画图
      plots/                   汇总图和 case 能带图
```

## 主要运行入口

### 1. 生成贪吃蛇状态

```bash
python snake/generate_states.py --episodes 200 --max-steps 500 --n 32 --agent q
```

输出目录：[`data/snake_state_matrices/`](/d:/graduation_project/coad/data/snake_state_matrices)

### 2. 将矩阵转成轮廓点

```bash
python preprocess/main.py --dir data/snake_state_matrices --sample 0 --preview 1
```

输出目录：

- [`data/shape_contours/`](/d:/graduation_project/coad/data/shape_contours)
- [`data/shape_contour_previews/`](/d:/graduation_project/coad/data/shape_contour_previews)

### 3. 批量运行 COMSOL

```matlab
cd('d:\graduation_project\coad\runners');
run('run_shape_batch.m');
```

当前 runner 里需要注意：

- `startIndex` 控制起始样本
- `maxCount = 8` 目前默认一次处理 8 个样本，改成 `0` 才会处理全部样本
- `saveModel` 控制是否保留 `.mph` 文件

导出目录：[`data/comsol_batch/tbl1_exports/`](/d:/graduation_project/coad/data/comsol_batch/tbl1_exports)

### 4. 带隙后处理

```bash
python postprocess/analyze_bandgaps.py
python postprocess/plot_bandgap_summary.py
```

输出目录：[`data/postprocess_out/`](/d:/graduation_project/coad/data/postprocess_out)

## 批处理行为说明

- 不满足几何接触条件的离散扰动样本会被跳过
- 跳过记录写入 [`data/comsol_batch/perturb_skip_log.csv`](/d:/graduation_project/coad/data/comsol_batch/perturb_skip_log.csv)
- 运行期错误写入 [`data/comsol_batch/logs/run_shape_batch_errors.csv`](/d:/graduation_project/coad/data/comsol_batch/logs/run_shape_batch_errors.csv)
- 周期边界条件按矩形位置自动选边，不依赖固定边界编号
- 历史脚本保留在 [`runners/legacy_run/`](/d:/graduation_project/coad/runners/legacy_run) 供参考

## 下一阶段开发方向

下一阶段应把当前仓库从“能跑通的脚本集合”推进为“稳定的数据流水线”：

1. 统一单个样本的保存格式
2. 批量生成足够数量的结构与仿真结果
3. 将 bandgap 指标整理成可用于机器学习的标签
4. 构建第一版 `structure -> bandgap` 数据集
5. 训练 baseline MLP 代理模型
6. 将代理模型接入优化搜索

当前阶段的首要任务仍然是：**提高 pipeline 稳定性，并积累有效样本数据。**
