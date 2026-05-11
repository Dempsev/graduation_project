# COAD：力学超结构物理-数据协同优化代码仓库

## 项目概述

本仓库对应毕业课题“基于物理-数据协同优化算法的一种力学超结构设计”。它不是一个面向终端用户打包的软件包，而是一套研究型代码仓库：用物理仿真产生可信真值，用数据模型进行条件预测，再用预测结果引导候选结构搜索，并通过 COMSOL 回到物理层验证。

当前真正的论文主线已经收敛为 **冻结 target-band 条件预测与逆向设计工作流**。旧的 `v10/v11`、`ga_v1` 和更早 `stage3_training/` 路线仍然保留，但它们现在主要承担历史桥接、基线比较和可追溯复现实验的作用，不再是默认叙事主线。

## 当前主线

论文与项目介绍建议统一采用下面这条闭环：

1. 物理真值生产：用 COMSOL + MATLAB 生成结构样本、带隙结果和验证记录。
2. target-band 数据构造：围绕论文目标频带建立可训练、可解释的条件预测数据集。
3. 条件预测建模：训练面向给定频带的分类/回归模型，把模型定位为候选筛选器，而不是物理求解器替代品。
4. 预测引导搜索：在候选种子与局部参数空间中筛出更可能满足目标频带的结构。
5. Stage4 物理验证：把 shortlist 交回 COMSOL 验证，形成论文第 6 章使用的真实证据。

这条线对应的主线分支是当前工作分支 `codex/research-architecture-refactor`。原来的 `main` 可以理解为历史默认分支；如果要让 GitHub 首页反映当前研究状态，后续应把该分支合并到 `main`，或在 GitHub 仓库设置中把默认分支切到当前主线分支。

## 说明文件是否上传

应该上传。这里的说明文件不是临时笔记，而是论文和复现实验的“源材料”：

- `README.md` / `README_CN.md`：项目入口与主线说明。
- `docs/THESIS_MAINLINE.md`：论文主线边界与入口文件。
- `docs/THESIS_RUNBOOK.md`：复现实验顺序与命令。
- `docs/THESIS_METHOD_MAP.md`：方法章节、代码入口和证据产物之间的映射。
- `docs/architecture/targetband_mainline_freeze_v1.md`：冻结 target-band 主线的架构依据。
- `docs/THESIS_*.md` 和 `docs/*_cn.md`：论文写作、图表插入、结果解释和修订依据。

不上传的是运行后生成的产物，例如 `data/`、`output/`、`tmp/`、模型 checkpoint、COMSOL 批处理结果、导出的图像和临时日志。这些内容体积大、可再生成，也容易暴露本地路径或中间状态。

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
  data/                             生成产物，本地保留，不纳入 git
  output/                           论文图表/导出结果，本地保留，不纳入 git
  tmp/                              临时文件，本地保留，不纳入 git
```

## 推荐阅读顺序

如果要理解当前真正主线，建议按这个顺序看：

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
- 论文图表辅助：`prediction_targetband_param_v1/tools/`、`postprocess/`、`scripts/`

## 环境

项目通常使用：

- MATLAB
- COMSOL with MATLAB LiveLink
- Python 3
- Python 常用库：`numpy`、`pandas`、`torch`、`matplotlib`、`scikit-learn`

## 提交与数据管理原则

本仓库提交的是 **源代码、配置、实验流程定义和说明文档**。

- 上传：`.m`、`.py`、`.json`、`.md`、共享契约、配置文件、README、论文写作和复现实验说明。
- 不上传：`data/`、`output/`、`tmp/`、`.worktrees/`、模型权重、仿真结果、导出图像、临时缓存。
- 主线叙事：以冻结 target-band workflow 为准；历史分支和旧流程作为 baseline 或 appendix 材料保留。

## 本仓库适合做什么

- 复现毕业论文中的物理-数据协同设计流程。
- 追踪 target-band 条件预测模型如何进入逆向设计。
- 说明候选结构如何从预测筛选进入 COMSOL 验证。
- 为论文方法、实验、讨论和附录提供真实代码与文档依据。
