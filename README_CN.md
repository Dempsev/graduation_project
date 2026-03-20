# COAD：力学超结构物理-数据协同优化代码仓库

## 项目概述

本仓库对应毕业课题“**基于物理-数据协同优化算法的一种力学超结构设计**”，核心不是做一个孤立的代理模型，而是搭建并反复验证一条完整闭环：

1. 用 COMSOL + MATLAB 做物理筛样
2. 从随机 snake、低阶 Fourier 邻域、高阶 harmonics 中建立数据库
3. 训练分类器 / 回归器
4. 用 cascade 方式筛候选
5. 再回到 COMSOL 做物理验证

当前仓库已经保留了从 `v1` 到 `v10` 的主要实验链路，代码组织方式也已经从“能跑通的一组脚本”发展成了“按阶段和版本管理的研究代码仓库”。

## 当前研究状态

项目主线已经比较明确：

- 物理评价基线已经固定：
  - 材料为“软基体 + 硬夹杂”
  - 可信母体参数固定
  - 主标签固定为 `3-4` 带带隙，即 `gap34_Hz / gap34_gain_Hz`
- broad rollout 经过多轮物理回证已经被否掉
- 当前唯一明确成立的 exploitation 点仍然是：
  - `rf09_h09_b5_002_a4_0015`
- 已经确认的两种有效迁移模式是：
  - 已验证 family 上的 **directional exploitation**
  - 未见 family 上的 **seed-only discovery**
- 在后期 seed-only discovery 中，当前最稳定的新 family 入口是：
  - `stage1 weak_positive` seed

因此，这个仓库当前代表的不是“全局盲搜”流程，而是一个已经被物理实验收缩出来的 **family-aware / step-aware targeted exploitation** 流程。

## 仓库结构

```text
coad/
  model_core/                COMSOL 核心建模、材料、结果提取函数
  stage1/                    Stage1 相关辅助逻辑
  stage2/                    低阶 Fourier 鲁棒性筛样逻辑
  stage2_refine/             低阶参数精化逻辑
  stage2_harmonics/          高阶 harmonics 筛样逻辑
  stage2_harmonics_refine/   高阶 refine 逻辑
  stage3_dataset/            各版本训练数据集构建脚本
  stage3_training/           模型训练、打分、候选池构建、manifest 构建
  stage4_validation/         Stage4 验证配置与汇总表写出逻辑
  runners/                   MATLAB 主入口脚本
  preprocess/                预处理与轮廓提取
  postprocess/               tbl1 解析、带隙分析、绘图
  snake/                     随机 snake 形状生成
  data/                      所有生成产物（已加入 gitignore）
  README.md
  README_CN.md
  .gitignore
```

### 各目录职责

- `model_core/`：共享的 COMSOL 侧函数，如材料设定、几何构造、边界选择、特征频率求解、结果封装。
- `stage1/` 到 `stage2_harmonics_refine/`：机器学习之前的物理筛样逻辑。
- `stage3_dataset/`：把历史物理结果整理成版本化训练集。
- `stage3_training/`：训练 MLP 分类器 / 回归器，构建 candidate pool，做 cascade 打分，输出验证 manifest。
- `stage4_validation/`：集中管理 `stage4_validation_ab_v*.m` 的配置和汇总表生成逻辑。
- `runners/`：实际从 MATLAB 调用的主入口。
- `data/`：所有运行产生的 CSV、模型、manifest、COMSOL 输出、图像和日志。该目录不纳入 git 提交。

## 阶段化流程

## 1. 物理筛样阶段

### Stage1：随机 snake 形状筛样

主入口：
- `runners/run_stage1_shape_screening.m`

作用：
- 在可信母体点上筛随机 snake
- 得到 geometry / contact / solve / positive 的第一批真值
- 为后续 transfer 与机器学习提供 seed 库

### Stage2：低阶 Fourier 鲁棒性与 refine

主入口：
- `runners/run_stage2_fourier_robustness_screening.m`
- `runners/run_stage2_refine_screening.m`

作用：
- 验证强正例不是偶然命中
- 收缩低阶有效区，稳定 `a2 < 0`、`a1 ~ 0.45-0.50`、`b2 ~ 0-0.04` 的主结论

### Stage2 harmonics：高阶 exploitation 信号

主入口：
- `runners/run_stage2_harmonics_screening.m`
- `runners/run_stage2_harmonics_refine_screening.m`

作用：
- 在低阶可信区基础上测试高阶项
- 保留主线规律：`a4 > 0` 最值得保留，`b5 / b3` 次之

## 2. 数据集与模型阶段

数据集构建脚本位于：
- `stage3_dataset/`

模型训练与候选池打分脚本位于：
- `stage3_training/`

目前比较关键的数据集版本：
- `build_v5_training_dataset.py`：引入方向性上下文特征
- `build_v6_training_dataset.py`：并入更后面的 validation 真值
- `build_v7_training_dataset.py`：训练集并入到 `stage4_validation_ab_v8`，并补入 `stage1` 参考特征，支持 seed-only discovery

当前模型结构保持为三头：
- `contact_valid` 分类器
- `is_positive_shape` 分类器
- `gap34_gain_Hz` surrogate 回归器

整个 cascade 始终坚持“**分类前级主导，回归后级辅助**”的原则。

## 3. 候选生成与物理验证阶段

候选池和验证 manifest 都按版本管理。

代表性脚本包括：
- `stage3_training/build_candidate_pool_v5.py`
- `stage3_training/build_candidate_pool_v8.py`
- `stage3_training/build_candidate_pool_v9.py`
- `stage3_training/build_candidate_pool_v10.py`

验证 runner 包括：
- `runners/run_stage4_validation_ab_v5.m`
- `runners/run_stage4_validation_ab_v6.m`
- `runners/run_stage4_validation_ab_v7.m`
- `runners/run_stage4_validation_ab_v8.m`
- `runners/run_stage4_validation_ab_v9.m`
- `runners/run_stage4_validation_ab_v10.m`

这些 runner 的共同作用是：
- 读取 validation manifest
- 在 COMSOL 中逐条跑 shape-point 组合
- 写出逐样本结果表
- 自动生成 arm / point / shape 三类汇总表

## 版本演化摘要

### `v1`
- 第一次成功证明 cascade 值得做
- 说明分类前级是必须的

### `v2` 到 `v4`
- 重点测试 broad-transfer 假设
- 物理回证说明 broad transfer 不成立

### `v5` 到 `v6`
- 转向 targeted exploitation
- 在已验证 family 上建立 directional step exploitation

### `v7`
- 测试 optional 新 family 的局部转移
- 结果说明新 family 不支持直接做 step 邻域扩展

### `v8`
- 第一轮较强的 seed-only discovery

### `v9`
- 引入更保守的 seed-only 模型辅助排序
- 说明模型有排序价值，但不能在尾部候选上做硬 gate

### `v10`
- refined shortlist 版本
- 主清单优先 `weak_positive / strong_positive`
- `neutral` 只保留极少量 probe 名额

## 当前推荐使用方式

如果继续沿当前主线推进，推荐顺序是：

1. 新真值并回训练集
2. 按需要重训 directional 或 seed-only 模型
3. 构建并打分下一版 candidate pool
4. 生成 validation manifest
5. 用对应的 `stage4_validation_ab_v*.m` 跑 COMSOL
6. 分析 arm / point / shape 汇总表

按当前仓库状态，最新一条 seed-only refined 路线是：

- 候选池：`stage3_training/build_candidate_pool_v10.py`
- 打分：`stage3_training/run_seed_discovery_scoring_v7.py`
- manifest：`stage3_training/build_validation_manifest_v10.py`
- COMSOL 验证：`runners/run_stage4_validation_ab_v10.m`

## 环境说明

本项目通常使用以下环境：

- MATLAB
- COMSOL with MATLAB LiveLink
- Python 3
- Python 常用库：
  - `numpy`
  - `pandas`
  - `torch`
  - `matplotlib`

## 提交与数据管理原则

本仓库提交的是 **源代码和说明文档**，不是运行产物。

- 所有仿真结果表、manifest、模型检查点、COMSOL 输出、图像和日志都放在 `data/` 下。
- `data/` 已加入 `.gitignore`。
- 提交时只提交定义流程的代码，不提交运行后生成的研究数据。

## 本仓库适合做什么

本仓库适合用于：
- 复现实验链路和方法流程
- 继续追加 targeted validation 轮次
- 继续扩展数据集和训练脚本
- 为论文方法部分和流程部分提供真实代码依据

它不是一个面向最终用户打包好的通用软件，而是一个保留了完整实验演化历史的研究代码仓库。
