# 毕业论文大纲（中文详细版）

## 0. 使用说明

这份大纲是按当前仓库已经冻结的 thesis mainline 来写的，默认论文主线为：

> 面向 thesis band catalog 的 target-band 条件预测与预测驱动逆向设计流程。

写作时建议始终坚持下面这条主线：

1. 先有物理真值生产
2. 再有面向目标频带的条件预测
3. 再有 prediction-guided shortlist 与局部精修
4. 最后用 MATLAB/COMSOL 做真实验证

当前仓库中最重要的主线材料是：

- `docs/THESIS_MAINLINE.md`
- `docs/THESIS_METHOD_MAP.md`
- `docs/THESIS_RUNBOOK.md`
- `docs/architecture/targetband_mainline_freeze_v1.md`
- `docs/targetband_formal_execution_plan_v1_cn.md`
- `docs/predictor_readiness_report_v1_cn.md`
- `docs/canonical_inverse_design_cases_v1_cn.md`
- `docs/targetband_baseline_comparison_v1_cn.md`
- `docs/weak_band_shortlist_value_v1_cn.md`
- `docs/canonical_local_robustness_v1_cn.md`

建议你把这篇论文写成“方法建立 + 主线验证 + 对照比较 + 局限讨论”的结构，而不是写成“我做了很多实验的流水账”。

---

# 论文题目建议

可以从下面几种里选一个，再按学校格式微调。

## 题目版本 A

**面向目标频带的声子晶体结构条件预测与预测驱动逆向设计方法研究**

## 题目版本 B

**基于条件预测与真实物理验证的目标频带声子晶体逆向设计方法**

## 题目版本 C

**面向指定频带的声子晶体预测驱动逆向设计流程构建与验证**

如果你想让题目更稳、更像工科毕设，推荐版本 A。

---

# 摘要部分大纲

## 中文摘要

建议摘要按 6 句展开：

1. 研究背景
   声子晶体/机械超结构的带隙调控具有重要应用价值，但面向指定目标频带的逆向设计仍然困难。
2. 研究问题
   传统做法要么依赖高成本物理搜索，要么缺少对指定目标频带的条件化建模能力。
3. 方法概述
   本文构建了一个面向 thesis band catalog 的 target-band 条件预测与预测驱动逆向设计流程。
4. 技术路线
   该流程包括物理真值生产、目标频带参数化数据集构建、条件分类/回归预测、prediction-guided shortlist 与局部精修，以及 MATLAB/COMSOL 真实验证。
5. 核心结果
   预测器在 family-CV 与 leave-one-band 条件下表现出可用的 shortlist 价值；预测驱动主线能够在多个目标频带上找到可验证的设计；弱 band 也得到实质推进。
6. 结论与意义
   结果表明，该流程在当前 thesis band catalog 与参数化结构族范围内建立了一条可解释、可复现、可验证的 target-band inverse-design workflow。

## 英文摘要

英文摘要对应中文摘要逐句翻译即可，核心关键词建议统一为：

- target-band inverse design
- conditional prediction
- shortlist generation
- shape-aware candidate construction
- real COMSOL validation
- phononic crystal / mechanical metastructure

## 关键词建议

- 声子晶体
- 目标频带
- 逆向设计
- 条件预测
- 机器学习
- COMSOL 验证

---

# 第一章 绪论

## 1.1 研究背景与意义

这一节回答“为什么这个问题值得做”。

建议写法：

1. 介绍声子晶体/机械超结构在带隙调控、隔振降噪、波传播控制中的应用背景。
2. 说明传统正向分析流程的局限。
   重点强调：
   - 设计变量多
   - 结构族复杂
   - 目标频带具有明确指定性
   - 真实物理评估成本高
3. 引出逆向设计需求。
   不是“找一个有带隙的结构”，而是“给定一个 band，找到可用设计”。
4. 引出机器学习/预测模型的潜力。
   但要强调：预测器不是物理求解器替代品，而是 shortlist engine。

## 1.2 国内外研究现状

建议分三块写：

### 1.2.1 声子晶体带隙分析与结构设计研究

写传统数值模拟、参数扫描、拓扑优化、启发式搜索的路线。

### 1.2.2 机器学习在超结构设计中的应用

写 surrogate model、regression/classification、生成式设计、数据驱动筛选等。

### 1.2.3 现有工作的不足

重点落在：

- 很多工作是“无条件”的结构性能预测，不是“给定 band 的条件预测”
- 很多工作强调代理模型拟合，但没有真实物理闭环验证
- 很多工作在强 band 上有效，但对弱 band 的推进不足
- 很多工作不能清楚区分 predictor、candidate construction 和 real validation 的角色

## 1.3 本文研究问题

这一节要明确写成几个问题，不要泛泛写“提高性能”。

推荐写成三个研究问题：

1. 能否建立一个面向指定目标频带的条件预测器，使其具有 shortlist 价值？
2. 条件预测器能否真正驱动后续真实物理搜索，而不是只在离线指标上看起来有效？
3. 在 thesis band catalog 范围内，这条 prediction-guided inverse-design 流程能否推动弱 band 的真实设计发现？

## 1.4 本文技术路线与总体框架

这一节建议直接画总流程图。

推荐图名：

**图 1-1 本文 target-band 逆向设计总体框架**

图中包含五个模块：

1. physical truth production
2. parametric target-band dataset construction
3. conditional prediction
4. target-band seed scoring and local refinement
5. stage4 real validation and result packaging

对应仓库主线：

- `physics_pipeline/`
- `prediction_targetband_param_v1/`
- `optimization/`
- `stage4_validation/`

## 1.5 本文主要工作与创新点

这一节建议写成 3 到 4 条。

推荐写法：

1. 建立了一个面向 thesis band catalog 的 target-band 条件预测框架，实现了“结构 + 指定 band -> 开启概率/覆盖质量”的建模。
2. 构建了 prediction-guided + shape-aware + real-search refinement 的逆向设计主线，将预测、候选构造和真实验证统一为一个可复现流程。
3. 通过 canonical inverse-design cases、baseline comparison 和 weak-band analysis，证明了该主线不仅在强 band 上有效，而且对弱 band 具有实质推进作用。
4. 建立了 Python 与 MATLAB/COMSOL 之间的 manifest-contract 闭环，使整个 thesis-facing 主线具备可复现和可维护性。

## 1.6 论文结构安排

这一节可以简洁写：

- 第 1 章：绪论
- 第 2 章：问题定义与系统框架
- 第 3 章：物理真值生产与目标频带数据基础
- 第 4 章：面向目标频带的条件预测方法
- 第 5 章：预测驱动的目标频带逆向设计方法
- 第 6 章：实验设计与结果分析
- 第 7 章：讨论与局限性分析
- 第 8 章：结论与展望

---

# 第二章 问题定义与系统框架

## 2.1 目标频带逆向设计问题定义

这一节要把“输入、输出、约束、目标”写清楚。

建议分四点：

1. 输入
   - 参数化结构表示
   - 目标频带区间
   - 固定材料配置与物理求解条件
2. 输出
   - 满足指定目标频带要求的结构候选
   - 对应真实物理验证结果
3. 目标
   - 尽可能提高目标频带开启/覆盖质量
   - 同时保证结构物理可用性
4. 约束
   - 当前方法成立于 thesis band catalog 与当前参数化结构族内

## 2.2 Thesis Band Catalog 的定义

这一节要解释为什么不是任意连续频带，而是一个冻结后的 thesis band catalog。

可写内容：

- thesis band catalog 的具体 band 范围
- 采用 band catalog 的原因
  - 控制实验边界
  - 保证样本规模
  - 对应已有真实真值
- 这不是方法的“缺点”，而是毕设阶段的合理研究边界

建议引用：

- `docs/THESIS_MAINLINE.md`
- `docs/architecture/targetband_mainline_freeze_v1.md`

## 2.3 三层系统架构

这一节建议直接按项目结构写：

### 2.3.1 Truth Layer

对应 `physics_pipeline/`，负责：

- 真实物理样本生产
- 结构筛选与参数探测
- 阶段性 COMSOL 验证

### 2.3.2 Model Layer

对应 `prediction/` 与 `prediction_targetband_param_v1/`，负责：

- 参数化数据集构建
- 条件分类/回归建模
- 预测器评估与 readiness 判断

### 2.3.3 Search Layer

对应 `optimization/`，负责：

- 候选 seed 评分
- 局部 refinement
- 验证 manifest 构建
- 对接真实 stage4 validation

## 2.4 论文主线与历史基线的边界

这一节非常重要，建议单独写。

要明确：

- 正式论文主线是 frozen target-band stack
- `v10/v11/ga_v1` 是 baseline / historical bridge
- 它们用于对照，不再作为论文默认主流程

建议引用：

- `docs/THESIS_MAINLINE.md`
- `docs/THESIS_METHOD_MAP.md`
- `docs/targetband_baseline_comparison_v1_cn.md`

## 2.5 本章小结

总结一句话：

本文不是在做“任意结构的通用逆向设计”，而是在 thesis band catalog 内建立一条完整、可解释、可验证的 target-band inverse-design workflow。

---

# 第三章 物理真值生产与目标频带数据基础

## 3.1 参数化结构表示与结构族定义

这一节介绍结构表示。

建议内容：

- 当前采用的二维参数化结构族
- 主要几何参数含义
- 不同 shape family 的角色
- 为什么 shape 不能只视为普通输入变量，而要成为正式任务变量

可配图：

**图 3-1 典型结构族与参数化几何示意图**

## 3.2 物理真值生产流程

按 `physics_pipeline/` 的实际结构写：

1. `stage1/`：初始结构与基础样本生成
2. `stage2/`：参数方向筛选与带隙分析
3. `stage2_refine/`、`stage2_harmonics/`、`stage2_harmonics_refine/`：高阶方向与更稳定的物理真值修正
4. `stage4_validation/`：对 shortlist 做真实 COMSOL 验证

这里要强调“真值先于预测模型存在”。

## 3.3 目标频带参数化数据集构建

这一节写数据集的形成逻辑。

建议内容：

- 从真实物理样本到 target-band parametric dataset 的映射
- 样本字段
  - 几何参数
  - shape family
  - target band 标签
  - 开启/覆盖等监督信号
- 数据来源与合并逻辑
- 训练集覆盖范围

建议引用运行入口：

- `prediction_targetband_param_v1/runners/run_build_parametric_targetband_dataset_v1.py`

## 3.4 标签定义与监督目标

建议拆成两类：

### 3.4.1 分类目标

- 是否在指定 target band 上形成有效开启
- 概率意义下的 open probability

### 3.4.2 回归目标

- 带隙覆盖率
- overlap / cover 质量
- 与 band 边界的关系

## 3.5 数据集边界与统计概况

可写内容：

- 各 band 样本量
- 各 family 分布
- 强 band 与弱 band 的不平衡性
- 为什么要用 family-CV 和 leave-one-band 两类评估

推荐表格：

**表 3-1 thesis band catalog 及样本统计**

## 3.6 本章小结

强调：

本文后续所有预测与逆向设计结论都建立在一个由真实物理样本支撑的 target-band 数据基础之上。

---

# 第四章 面向目标频带的条件预测方法

## 4.1 条件预测任务定义

写清楚输入输出：

- 输入：结构参数 + shape family + target band
- 输出：开启概率 / 覆盖质量

要突出“条件预测”而不是“无条件性能回归”。

## 4.2 分类器与回归器设计

对应当前冻结主线：

- 分类器：RF
- 回归器：HGB

建议写法：

1. 为什么分类器与回归器分开建模
2. 为什么选择这两类模型作为冻结主线
3. 为什么这里不追求最复杂模型，而强调稳定、可解释、可复现

## 4.3 训练与验证设置

这里建议详细写：

### 4.3.1 Family-CV

用于验证模型在已知 band、不同 family 间的泛化能力。

### 4.3.2 Leave-One-Band

用于验证模型对 band 维度变化的迁移能力。

### 4.3.3 评价指标

分类部分：

- AUC
- AP / Precision-Recall
- top-k 命中率

回归部分：

- MAE / RMSE
- rank monotonicity
- top-k coverage quality

## 4.4 Predictor Readiness 分析

这一节几乎可以直接按 `docs/predictor_readiness_report_v1_cn.md` 写。

建议结构：

### 4.4.1 Family-CV 表现

说明模型是否在当前 family 范围内可用。

### 4.4.2 Leave-One-Band 表现

说明模型跨 band 的迁移边界。

### 4.4.3 Top-k Shortlist 质量

这是最重要的一节之一。

要强调：

- predictor 的角色不是给最终物理答案
- predictor 的核心价值是把更值得验证的样本排到前面

### 4.4.4 概率校准与分数单调性

解释为什么分数可以用来驱动候选排序。

## 4.5 Predictor 的作用边界

建议明确写：

- predictor 已经足够作为 shortlist engine
- 但 predictor 还不应该被写成最终最强排序器
- predictor 不能替代真实 COMSOL search/refinement

这一节可结合：

- `docs/weak_band_shortlist_value_v1_cn.md`
- `docs/targetband_standard_wording_v1_cn.md`

## 4.6 本章小结

总结为一句：

本文建立的条件预测器已经具备 target-band shortlist generation 的能力，并能够为后续真实逆向设计提供有效方向感。

---

# 第五章 预测驱动的目标频带逆向设计方法

## 5.1 总体方法描述

本章是全文方法核心。

建议开头先放一张流程图：

**图 5-1 prediction-guided target-band inverse-design workflow**

流程：

1. candidate pool / truth-derived seed preparation
2. target-band seed scoring
3. shape-aware candidate selection
4. local GA refinement
5. validation manifest construction
6. MATLAB/COMSOL real validation

## 5.2 Shape-Aware Candidate Construction

这一节非常关键，建议单独立起来。

要写明：

- shape 不只是输入特征
- shape-aware front-end 用于改善候选池质量
- family-aware 选择可以避免旧 baseline 中无条件 shape preference 的局限

可结合：

- `data/analysis/targetband_shape_atlas_v1/`
- `docs/shape_archetype_targetband_pilot_v1_cn.md`
- `docs/snake_based_archetype_targetband_pilot_v1_cn.md`
- `docs/targetband_shape_expansion_execution_plan_v1_cn.md`

## 5.3 Target-Band Seed Scoring

对应入口：

- `optimization/runners/run_targetband_seed_scoring_v1.py`

要写内容：

- seed 数据来源
- 条件分类/回归分数如何组合
- ranking 的设计原则
- 为什么这是 prediction-guided shortlist，而不是最终答案

## 5.4 Conservative Local Refinement

对应入口：

- `optimization/runners/run_targetband_local_ga_v1.py`

可写：

- 为什么采用 conservative local refinement，而不是直接全局搜索
- 局部搜索变量空间
- 与 baseline 中真实 GA 的关系
- 为什么此处更适合毕设主线

## 5.5 Validation Manifest 与 Python-MATLAB 契约

这一节可以突出你的工程完整性。

写清楚：

- Python 端如何构建 validation manifest
- MATLAB 端如何读取 manifest
- shared contract 如何检查字段、类型、空值

对应文件：

- `optimization/runners/run_targetband_validation_manifest_v1.py`
- `shared/contracts/stage4_validation_manifest_contract_v1.json`
- `shared/io/stage4_validation_manifest.py`
- `stage4_validation/validate_stage4_validation_manifest_contract_v1.m`

## 5.6 Stage4 Real Validation

对应入口：

- `runners/run_stage4_validation_targetband_v1.m`
- `stage4_validation/run_stage4_validation_from_manifest.m`

要解释：

- 为什么最终必须回到真实物理验证
- stage4 输出哪些结果
- 如何判断结构有效

## 5.7 Baseline / Historical Bridge 的定位

写清楚：

- `v10/v11/ga_v1` 是比较线
- 它们用于证明新主线的进步，不是论文默认主流程

## 5.8 本章小结

总结：

本文方法并不是单个预测器，而是一条由条件预测、shape-aware 候选构造、局部精修与真实物理验证构成的完整 workflow。

---

# 第六章 实验设计与结果分析

这一章建议按“证据链”组织，而不是按脚本组织。

## 6.1 实验目标与证据结构

建议开头明确三个问题：

1. predictor 是否真的有 shortlist 价值？
2. 预测驱动主线是否真的能找到可用设计？
3. 弱 band 是否真的被打通？

## 6.2 实验设置

写：

- thesis band catalog
- 固定材料与物理配置
- 训练/验证设置
- baseline lines
- 真实验证流程

可加表格：

**表 6-1 全部实验线与作用定位**

## 6.3 Predictor Readiness 结果

直接按 readiness 报告写。

### 6.3.1 Family-CV 结果

### 6.3.2 Leave-One-Band 结果

### 6.3.3 Top-k shortlist 结果

### 6.3.4 校准与单调性分析

结论应落在：

- predictor 已可作为 shortlist engine
- 但真实效果还依赖后续 refinement 与 validation

## 6.4 Canonical Inverse-Design Cases

这一节建议按 band 分成多个 case。

可直接参考：

- `docs/canonical_inverse_design_cases_v1_cn.md`

推荐结构：

### 6.4.1 band180_220

### 6.4.2 band200_240

### 6.4.3 band220_260

### 6.4.4 band240_280

每个 case 建议按 5 小段写：

1. 结构身份
2. 优化参数
3. 真实结果
4. 与旧 baseline 对比
5. 物理解释

## 6.5 Baseline Comparison

这一节直接承接 `docs/targetband_baseline_comparison_v1_cn.md`。

建议先说明纳入的对照线：

- generic_dataset_prior_v8
- targetband_local_ga_v1_probe
- targetband_local_ga_v1_top6
- band_catalog_real_ga_v1
- band_supplement_ga_v1
- band_supplement_exploratory_v2

然后分 band 写结果，再总结：

### 6.5.1 band180_220 对照结果

### 6.5.2 band200_240 对照结果

### 6.5.3 band220_260 对照结果

### 6.5.4 band240_280 对照结果

### 6.5.5 家族多样性与预算分析

### 6.5.6 小结

## 6.6 Weak-Band Shortlist Value 与 Coverage 分析

对应：

- `docs/weak_band_shortlist_value_v1_cn.md`

这一节要说明：

- predictor 不是没用的排序器
- predictor 也不是任何时候最强
- 但 predictor 为弱 band 推进提供了实质价值

## 6.7 Stage4 Real Validation 结果

这一节写真实验证结果。

你现在已经有：

- `data/comsol_batch/stage4_validation_targetband_v1/stage4_validation_results.csv`
- `data/comsol_batch/stage4_validation_targetband_v1/stage4_validation_point_summary.csv`
- `data/comsol_batch/stage4_validation_targetband_v1/stage4_validation_shape_summary.csv`

这一节建议写：

1. 验证样本数
2. 几何有效率
3. 接触有效率
4. 求解成功率
5. 正向 gain 情况

如果想写得更正式，可以做：

**表 6-2 Stage4 real validation 结果汇总**

## 6.8 Local Robustness 分析

如果篇幅够，可以作为主结果的一部分；如果篇幅紧，可以放到讨论章或附录。

参考：

- `docs/canonical_local_robustness_v1_cn.md`
- `docs/canonical_local_robustness_results_v1_cn.md`

可写内容：

- 中心点保真度
- 局部保持率
- 边界漂移
- 敏感变量

## 6.9 本章小结

这一节要用“证据链闭环”来总结：

- predictor readiness 成立
- canonical cases 成立
- baseline comparison 支持新主线
- weak band 得到实质推进
- stage4 real validation 完成闭环

---

# 第七章 讨论与局限性分析

## 7.1 本文方法真正成立的范围

建议明确写：

- thesis band catalog 内成立
- 当前参数化结构族内成立
- 当前材料和求解配置下成立

## 7.2 本文不能过度宣称的内容

这里非常重要，建议直接写得克制。

不要写成：

- 完全通用逆向设计
- predictor 替代真实物理求解
- 任意 band 一步到位

建议写成：

- 当前工作建立了 workflow，而不是完成了通用最终形态
- predictor 提供 shortlist value，而不是直接产出最终答案
- 弱 band 被推进，但并不等于所有困难 band 都已完全解决

## 7.3 为什么采用“条件预测 + 局部精修 + 真实验证”的组合

这一节可以做方法层面的反思：

- 单独 predictor 不够
- 单独真实搜索成本太高
- 单独 shape heuristic 不够稳定
- 组合后才形成可用主线

## 7.4 工程可复现性与系统可维护性

这一节可以写你的重构成果：

- 官方 thesis mainline 固定
- profile / policy / run config 边界明确
- Python-MATLAB manifest contract 建立
- smoke tests 建立
- runbook / method map / mainline docs 完成

这部分对毕设答辩很加分。

## 7.5 后续可扩展方向

建议写：

- 扩展更多 thesis bands
- 扩展更多结构族
- 更系统的弱 band truth harvesting
- 更强的局部鲁棒性与制造约束分析
- 更高层级的 candidate generation / active learning

## 7.6 本章小结

强调：

本文工作最重要的成果不是某个单点最好成绩，而是建立了一条可解释、可验证、可扩展的 target-band inverse-design 主线。

---

# 第八章 结论与展望

## 8.1 全文工作总结

建议按三条总结：

1. 建立了目标频带条件预测框架
2. 建立了 prediction-guided inverse-design 主线
3. 用真实物理验证完成了闭环

## 8.2 主要结论

建议拆成 4 条：

1. 条件预测器已经具备 shortlist 价值
2. shape-aware candidate construction 是正式方法组成部分
3. prediction-guided inverse-design 主线相对 baseline 有明确优势
4. 在 thesis band catalog 范围内，弱 band 也获得了真实推进

## 8.3 工作不足

建议写：

- band catalog 范围仍有限
- 结构族范围仍有限
- 样本规模与真实验证预算仍有限
- 鲁棒性与制造约束分析仍可加强

## 8.4 未来工作展望

建议写：

- 引入更多真实验证反馈形成 active loop
- 扩大结构表示能力
- 加强对弱 band 的数据采集
- 提升模型跨 band 泛化能力
- 把流程推广到更完整的工程设计场景

---

# 附录建议

## 附录 A 主要符号说明

把几何参数、band 定义、评价指标统一列出来。

## 附录 B 主要脚本与运行入口

直接参考：

- `docs/THESIS_RUNBOOK.md`

## 附录 C 论文术语与代码入口对照表

直接参考：

- `docs/THESIS_METHOD_MAP.md`

## 附录 D 关键补充图表

可以放：

- 更多 band 的对照图
- 更多局部鲁棒性图
- 额外 shape archetype 图

---

# 建议插图与表格清单

## 推荐插图

1. 图 1-1 论文总体框架图
2. 图 3-1 参数化结构与 shape family 示意图
3. 图 4-1 条件预测任务定义图
4. 图 5-1 prediction-guided inverse-design workflow 图
5. 图 6-1 predictor readiness 结果图
6. 图 6-2 canonical cases 真实结果图
7. 图 6-3 baseline comparison 对照图
8. 图 6-4 weak-band coverage / shortlist 价值图
9. 图 6-5 stage4 validation 结果统计图
10. 图 6-6 local robustness 分析图

## 推荐表格

1. 表 3-1 thesis band catalog 与样本统计
2. 表 4-1 分类器与回归器训练配置
3. 表 4-2 predictor readiness 核心指标
4. 表 5-1 主线与 baseline 路线定位对照
5. 表 6-1 实验线与作用定位
6. 表 6-2 canonical inverse-design cases 汇总
7. 表 6-3 baseline comparison 汇总
8. 表 6-4 stage4 real validation 汇总
9. 表 7-1 方法成立范围与局限性

---

# 写作提醒

## 最重要的三条原则

1. 不要把论文写成脚本说明书。
   要写“问题—方法—证据—结论”。
2. 不要把 predictor 写成万能模型。
   要始终强调它是 shortlist engine。
3. 不要把 baseline 和主线混着讲。
   主线是 frozen target-band stack，baseline 只用于比较。

## 最推荐的正文口径

建议在摘要、绪论、方法、结论里反复使用下面这句的变体：

> 本文建立了一条面向 thesis band catalog 的 target-band 条件预测与预测驱动逆向设计主线，其中条件预测器负责 shortlist generation，shape-aware candidate construction 负责提升候选质量，real COMSOL validation 负责给出最终物理确认。

## 最后建议

如果你后面真的按这份大纲写，最稳的顺序不是从第一章开始硬写，而是：

1. 先写第六章实验结果
2. 再写第五章方法
3. 再补第三章数据与真值
4. 然后写第二章系统框架
5. 最后再收第一章和第八章

这样会快很多，也更不容易空话太多。
