# COAD：力学超结构物理-数据协同优化代码仓库

## 项目概述

本仓库对应毕业课题“基于物理-数据协同优化算法的一种力学超结构设计”。它不是面向终端用户打包的软件包，而是一套研究型代码仓库：用 COMSOL 与 MATLAB 产生可信物理真值，用数据模型完成目标频带条件预测，再用预测结果引导候选结构搜索，并回到 COMSOL 做真实物理验证。

当前论文主线已经收敛为 **冻结 target-band 条件预测与逆向设计工作流**。旧的 `v10/v11`、`ga_v1` 和更早 `stage3_training/` 路线仍然保留，但它们主要承担历史桥接、基线比较和复现实验的作用，不再是默认叙事主线。

## 当前主线

项目主线可以概括为一条物理-数据闭环：

1. 物理真值生产：用 COMSOL + MATLAB 生成结构样本、带隙结果和验证记录。
2. target-band 数据构造：围绕论文目标频带建立可训练、可解释的条件预测数据集。
3. 条件预测建模：训练面向给定频带的分类/回归模型，把模型定位为候选筛选器，而不是物理求解器替代品。
4. 预测引导搜索：在候选种子与局部参数空间中筛出更可能满足目标频带的结构。
5. Stage4 物理验证：把 shortlist 交回 COMSOL 验证，形成论文第 6 章使用的真实证据。

这条主线对应的核心叙事是：

```text
物理真值生产 -> 目标频带数据构造 -> 条件预测 -> 预测引导搜索/精化 -> COMSOL 验证
```

## 仓库结构

```text
coad/
  physics_pipeline/                 物理真值生产入口
  prediction_targetband_param_v1/    target-band 条件预测主线
  optimization/                     预测引导搜索与局部精化
  stage4_validation/                COMSOL 验证配置与共享验证逻辑
  runners/                          MATLAB/COMSOL 批处理入口
  postprocess/                      结果解析、场图导出与论文图表辅助
  docs/                             论文主线、方法映射、写作材料与说明文档
  shared/                           共享契约与工具
  baselines/                        历史或比较工作流

  stage1/、stage2*/、stage3_*        历史真值生产、数据集和模型路线
  data/                             本地生成产物，不纳入 git
  output/                           本地图表与导出结果，不纳入 git
  tmp/                              临时文件，不纳入 git
```

## 推荐阅读顺序

如果要理解当前主线，建议按这个顺序阅读：

1. `README.md` 或 `README_CN.md`
2. `docs/THESIS_MAINLINE.md`
3. `docs/THESIS_RUNBOOK.md`
4. `docs/THESIS_METHOD_MAP.md`
5. `docs/architecture/targetband_mainline_freeze_v1.md`
6. `physics_pipeline/`
7. `prediction_targetband_param_v1/`
8. `optimization/`
9. `stage4_validation/`

如果需要解释历史演化或做对比，再阅读 `stage3_training/`、`baselines/` 以及旧验证 runner。

## 关键代码入口

- 物理真值层：`physics_pipeline/`
- 条件预测训练：`prediction_targetband_param_v1/runners/`
- target-band 搜索：`optimization/runners/`
- Stage4 验证：`runners/run_stage4_validation_targetband_top6_v1.m`
- 论文图表辅助：`prediction_targetband_param_v1/tools/`、`postprocess/`

## 环境

项目通常使用：

- MATLAB
- COMSOL with MATLAB LiveLink
- Python 3
- Python 常用库：`numpy`、`pandas`、`torch`、`matplotlib`、`scikit-learn`

## 数据管理原则

本仓库保存的是代码、配置和流程定义；运行后生成的数据、图表、模型与日志保留在本地输出目录中。

- `data/`：仿真结果、训练表、manifest、模型检查点和批处理输出。
- `output/`：论文图表、导出图片和文档中间产物。
- `tmp/`：临时构建、渲染和检查文件。

这些目录已通过 `.gitignore` 排除，仓库主线保持轻量、可读、可复现。

## 本仓库适合做什么

- 复现毕业论文中的物理-数据协同设计流程。
- 追踪 target-band 条件预测模型如何进入逆向设计。
- 说明候选结构如何从预测筛选进入 COMSOL 验证。
- 为论文方法、实验、讨论和附录提供真实代码与文档依据。
