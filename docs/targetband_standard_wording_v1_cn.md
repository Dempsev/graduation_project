# Target-Band 标准口径 V1

## 1. 文档目的

本文档用于冻结当前 thesis-facing target-band 主线的标准口径。

它不是论文正文，也不是最终定稿，而是后续所有材料的统一说法来源，包括：

- 论文写作
- 阶段汇报
- 图表说明
- 结果文档
- 后续分析笔记

本文档的目标很简单：

- 先把主张说法固定下来
- 先把方法分工说清楚
- 先把边界划清楚
- 先把术语统一好

后续正式写论文时，可以在此基础上扩展，但原则上不再频繁改口径。

## 2. 标准 Thesis Claim

### 2.1 英文版

> We establish a target-band inverse-design workflow within the thesis band catalog based on prediction-guided shortlist generation, shape-aware candidate construction, and real COMSOL search/refinement, and validate the resulting structures as usable target-band designs.

### 2.2 中文版

> 本项目建立了一条面向 thesis band catalog 的 target-band 逆向设计流程：由条件预测器生成面向指定目标频带的 shortlist，由 shape-aware 候选构造改善候选池质量与 family 结构，再由真实 COMSOL 搜索与精修将候选推进为经过验证的可用 target-band 设计。

### 2.3 更短的答辩口径

> 我们已经建立了一条面向指定目标频带的预测驱动逆向设计主线：预测器负责提 shortlist，shape-aware 前端负责改善候选池，真实 COMSOL search/refinement 负责把候选推进成最终可用设计。

## 3. 标准方法定义

### 3.1 方法总名称

当前统一将主线方法定义为：

`prediction-guided + shape-aware + real-search refinement`

后续文档、汇报和图表说明中，优先使用这组说法，不建议频繁切换成其他近义表述。

### 3.2 三层角色分工

#### predictor

标准说法：

- predictor 负责面向目标 band 的 shortlist generation
- predictor 提供方向感，而不是替代真实物理求解
- predictor 的主要任务是把更值得验证的候选排到前面

建议复用表述：

> The predictor serves as a shortlist engine for a specified target band rather than a replacement for the physical solver.

#### shape-aware front-end

标准说法：

- shape-aware front-end 负责改善候选池质量
- 它负责让候选构造更加 band-aware、family-aware
- 它不只是被动继承旧的 `gap34` 逻辑，而是正式方法组成部分

建议复用表述：

> The shape-aware front-end improves the candidate pool by introducing band-aware and family-aware shape selection, rather than relying on legacy unconditional shape preference.

#### real COMSOL search/refinement

标准说法：

- real COMSOL search/refinement 负责把候选推进成真实可用设计
- 它是最终真实性验证与进一步优化的核心环节
- weak band 的突破不是靠 predictor 单独完成，而是靠真实搜索与精修完成

建议复用表述：

> Real COMSOL search/refinement converts predictor-proposed candidates into validated usable target-band designs under true physical evaluation.

## 4. 标准边界说明

下面这些边界建议固定下来，后续尽量反复使用，不要每次重新想一遍。

### 4.1 当前主张成立的范围

当前项目的主张成立于：

- thesis band catalog 内
- 当前二维声子晶体参数化结构族内
- 当前数据生产、预测、shape-aware 候选构造和真实 COMSOL 验证这条集成主线内

### 4.2 当前不主张的内容

当前不主张：

- 任意连续频带上的完全通用反设计
- 任意材料体系上的完全泛化
- 任意结构表示下的通用逆向设计
- predictor 单独即可替代真实物理搜索
- 当前结果已经解决了所有 robustness 或 manufacturing 问题

### 4.3 建议复用的 limitations 表述

#### 英文版

> The current workflow is established within the thesis band catalog and the present parameterized phononic-crystal family. It does not claim universal inverse design over arbitrary continuous frequency ranges, arbitrary material systems, or arbitrary structural representations.

#### 中文版

> 当前流程的成立范围限定在 thesis band catalog 与当前参数化声子晶体结构族内。本文并不主张其已经实现对任意连续频带、任意材料体系或任意结构表示的完全通用逆向设计。

## 5. 标准证据链定义

后续正文、汇报和图表组织，建议统一围绕以下四段证据链展开：

1. predictor readiness
2. canonical inverse-design cases
3. baseline comparison
4. weak-band coverage and usefulness

对应回答四个问题：

1. predictor 是否足以作为 shortlist engine 使用
2. 主线是否真的找到了可用的 target-band 设计
3. 新主线相对旧 baseline 到底强在哪里
4. 弱 band 是否真的被打通，而不是只在强 band 上有效

## 6. 标准术语表

下面这些词建议统一使用，避免后续不同文档里来回换叫法。

### 6.1 建议固定使用的术语

- `thesis band catalog`
- `target-band inverse design`
- `prediction-guided shortlist`
- `shape-aware candidate construction`
- `real COMSOL search/refinement`
- `canonical inverse-design cases`
- `weak-band breakthrough`
- `weak-band truth harvesting`
- `baseline comparison`
- `local robustness`

### 6.2 建议避免频繁替换的说法

下面这些说法不是完全不能用，而是不建议和主口径混着乱用：

- “模型自动找到最优结构”
- “预测器直接完成逆向设计”
- “完全通用 target-band 设计”
- “任意 band 泛化”
- “无条件 shape 筛选”

### 6.3 一些推荐对应关系

- 不说“预测器解决了设计”
  改说“预测器提供 shortlist 和方向感”

- 不说“shape 只是辅助变量”
  改说“shape-aware front-end 是正式方法组成部分”

- 不说“COMSOL 只是验证”
  改说“real COMSOL search/refinement 负责把候选推进成真实可用设计”

- 不说“我们证明了完全通用逆向设计”
  改说“我们在 thesis band catalog 内建立了 target-band inverse-design workflow”

## 7. 现在最值得立即复用的三段话

### 7.1 一段主张

> 本项目建立了一条面向 thesis band catalog 的 target-band 逆向设计流程：由条件预测器生成面向指定目标频带的 shortlist，由 shape-aware 候选构造改善候选池质量与 family 结构，再由真实 COMSOL 搜索与精修将候选推进为经过验证的可用 target-band 设计。

### 7.2 一段方法分工

> 在这条主线中，predictor 的角色不是替代物理求解，而是作为 target-band shortlist engine 提供方向感；shape-aware front-end 的角色是改善候选池质量并引入 band-aware、family-aware 的候选构造；real COMSOL search/refinement 的角色则是在真实物理约束下把候选推进成最终可用设计。

### 7.3 一段边界说明

> 当前工作成立于 thesis band catalog 与当前参数化结构族内。本文并不主张其已经实现对任意连续频带、任意材料体系或任意结构表示的完全通用逆向设计。

## 8. 使用建议

后续建议这样使用本文档：

1. 写分析文档时，优先直接复用第 2、3、4 节的标准表述。
2. 做汇报时，优先使用第 7 节的三段话。
3. 写论文时，以本文档为口径基线，再做更正式的学术化改写。
4. 如果后续确实要升级主张或边界，应先修改本文档，再同步其他材料。

## 9. 当前结论

到当前阶段，最重要的不是再扩展口径，而是先把口径冻结。

本文档冻结后的执行原则是：

- 主张尽量不改
- 分工尽量不改
- 边界尽量不改
- 术语尽量统一

只有在后续出现明确更强的新证据时，才考虑升级版本。
