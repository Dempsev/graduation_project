# predictor-guided、shape-aware 与 exploratory real search 的关系说明（中文版）

## 1. 这份说明要解决什么问题

当前主线已经不再是单纯的：

- 做一个预测器
- 或做一个真实 GA

而是逐步形成了一条更完整的系统：

**target-band conditional prediction -> band-aware shape selection -> exploratory real search -> COMSOL validation -> truth harvesting**

这条线已经能跑通，也已经在弱 band 上拿到了关键结果。  
但如果不把三者关系讲清楚，后面在论文、汇报或答辩里很容易出现两种误解：

1. 误以为 `exploratory v2` 已经完全脱离 predictor，自成一套 brute-force 搜索。
2. 误以为 predictor 已经单独解决了 target-band inverse design，真实搜索只是形式上的补充。

这两个理解都不准确。

---

## 2. 当前系统的正确理解

当前主线更准确的描述是：

**prediction-guided + shape-aware + real-search refinement**

也可以展开成三层：

1. `predictor-guided shortlist`
2. `shape-aware front-end`
3. `exploratory real search`

这三层不是替代关系，而是分工关系。

---

## 3. 三层分别在做什么

### 3.1 Predictor-guided shortlist：负责“给搜索方向”

predictor 的当前最佳定位，不是最终裁判，也不是单独完成逆向设计，而是：

- 对给定 target band 做条件预测
- 识别哪些候选更可能开带隙
- 估计哪些候选更可能有更高 cover ratio
- 把候选排序，形成 shortlist

它承担的是**搜索前端**的角色。

换句话说，predictor 负责回答：

> “如果目标 band 是 `200-240 Hz`，哪些候选最值得优先看？”

它做的是：

- 减少盲搜
- 提高 shortlist 命中率
- 把真实搜索预算尽量花在更有希望的方向上

它**不负责**最终证明某个候选一定成立。  
最终物理真实性仍然要靠 COMSOL。

---

### 3.2 Shape-aware front-end：负责“把 shape 入口改对”

之前主线里最大的问题之一，是搜索虽然换成了 target band，但 shape pool 仍然主要来自旧的 `gap34 / 200Hz` 世界观。  
这会导致一个很典型的现象：

- 目标 band 变了
- score 变了
- 但 shape 还是旧 family/旧 basin
- 最后搜索还是容易在老地方打转

`shape-aware front-end` 的作用，就是把这个入口纠正过来。

它不再按单一 `gap34_gain_Hz` 排 shape，而是按：

- `shape x family x band`
- 的 target-band 表现
- 再加上 role-aware 选择

来构造每个 band 自己的 shape pool。

它负责回答：

> “对于 `200-240 Hz` 这个 band，哪些 family/shape 值得进搜索池？”

所以，shape-aware front-end 决定的是：

- 搜索起点质量
- family diversity
- 是否还被旧强 family 绑架
- 弱 band 能不能真正跳出旧盆地

它是 predictor 和 real search 之间非常关键的一层桥。

---

### 3.3 Exploratory real search：负责“把弱 band 真正打开”

当 predictor 和 shape-aware front-end 已经把方向收窄以后，真正把弱 band 顶开的，仍然是：

- 真实 COMSOL 求解
- exploratory 参数范围
- 历史已算点避碰
- cooperative 多会话搜索

也就是说，`exploratory real search` 的作用不是替代 predictor，  
而是把 predictor 给出的方向和 shape-aware front-end 给出的入口，进一步变成：

- 真正的 target-band candidate
- 真正的高覆盖率样本
- 真正能回灌训练集的新 truth asset

它负责回答：

> “在这些更有希望的 shape 和参数区域里，真实物理上到底能不能把目标 band 打开？”

所以它承担的是：

- 真实 refinement
- 弱 band 攻坚
- 真值闭环
- 新数据采集

---

## 4. 三者不是谁替代谁，而是逐层收缩搜索空间

更直观地看，这三层是一个逐层收缩搜索空间的系统：

### 第 1 层：predictor-guided shortlist

从大量候选里先排出“更像目标 band 解”的一批。

### 第 2 层：shape-aware front-end

把搜索真正聚焦到对该 band 有潜力的 family/shape，而不是继续沿旧 `gap34` shape 池走。

### 第 3 层：exploratory real search

在更合理的 shape 和更开放的参数范围内，做真实 COMSOL 搜索，把 band 真正打开，并把结果回灌为新 truth。

所以这条主线的本质不是：

- predictor 替代 physics

而是：

- predictor 负责提案
- shape-aware 负责改正确入口
- real search 负责最后把物理解找出来

---

## 5. 这也是为什么 exploratory v2 不能被理解成“脱离 predictor”

表面上看，`exploratory v2` 是真实 COMSOL 搜索，好像和 predictor 没直接绑定。  
但它并不是一条“完全与 predictor 无关”的独立支线，原因有三点。

### 5.1 它继承了 target-band 任务定义

`exploratory v2` 的目标 band 定义，本身就是从 target-band conditional prediction 这条主线长出来的。  
如果没有前面的：

- target-band label
- overlap / cover ratio 定义
- thesis band catalog

就不会有后面的弱 band 搜索目标。

### 5.2 它继承了 shape-aware 改造，而 shape-aware 来自前面的问题诊断

shape-aware front-end 之所以被正式引入，是因为我们先通过 predictor / baseline / weak-band 诊断，明确发现：

- 旧 shape 池被 `gap34 / 200Hz` 偏置锁住了

所以 exploratory v2 虽然是 real search，但它的入口修正，是在整个 predictor-driven 主线的问题诊断中形成的。

### 5.3 它的结果会反向提升 predictor

`exploratory v2` 的结果不是只拿来展示“某次搜索很强”，更重要的是：

- 它会被回收到 truth assets
- 再并入 `v8` 数据
- 再重训 RF + HGB
- 再提升弱 band 的 conditional prediction

所以它不是 predictor 之外的平行宇宙，  
而是 predictor 主线里的 **truth-harvesting accelerator**。

---

## 6. 这也是为什么 predictor 也不能被表述成“已经单独解决一切”

反过来，当前 predictor 也还不能被讲成：

- 给一个目标 band
- 模型就能直接产出最终设计

这同样不准确。

原因也很明确：

### 6.1 当前 predictor 最强的角色仍然是 shortlist engine

我们已经通过 readiness report 确认：

- family-CV：通过
- leave-one-band：有边界
- top-k shortlist：有价值
- calibration / monotonicity：基本可用

这说明 predictor **足以驱动 shortlist 和方向感**，  
但还不应该被说成“强未见-band extrapolator”。

### 6.2 弱 band 的真正打开仍然依赖真实搜索

尤其是：

- `200-240`
- `220-260`
- `240-280`

这些 band 的突破，最终不是靠 predictor 单独实现的，而是靠：

- shape-aware shape pool
- exploratory 参数范围
- 历史避碰
- 多会话 cooperative real search

所以 predictor 的最佳表述是：

**它让 inverse design 变成有方向的搜索，而不是取代真实搜索。**

---

## 7. 现在最准确的主线表述

结合当前结果，我建议后面统一使用下面这句：

**我们建立了一条面向 thesis band catalog 的条件逆向设计流程，其中 predictor 负责候选提案与排序，shape-aware front-end 负责按 band 重构搜索入口，exploratory real search 负责真实 refinement、弱 band 攻坚与 truth harvesting。**

如果要再压缩一点，可以用：

**predictor 负责给方向，shape-aware 负责选入口，real search 负责把物理解打开。**

---

## 8. 对论文写法的建议

后面写论文时，这三层建议分别放在不同段落里，不要糊成一段。

### 8.1 Prediction chapter

重点写：

- conditional target-band prediction
- readiness
- shortlist value

### 8.2 Shape-aware selection chapter / section

重点写：

- 旧 `gap34 / 200Hz` shape pool 的偏置
- 为什么必须做 `family x band` 的 shape atlas
- 为什么 band-specific shape pool 会改变弱 band 搜索行为

### 8.3 Search / inverse-design chapter

重点写：

- conservative search 为什么不够
- exploratory v2 如何在弱 band 上取得突破
- predictor / shape-aware / real search 如何形成闭环

---

## 9. 当前最容易被问到的问题，以及推荐回答

### 问题 1：既然 exploratory real search 这么强，predictor 还有什么用？

推荐回答：

predictor 的作用不是替代真实搜索，而是提高搜索前端的方向感。  
它决定候选排序和 shortlist 质量，也决定后续真实预算花在哪里更值。  
exploratory real search 负责真正把物理解打开，两者是分工，不是替代。

### 问题 2：既然 predictor 已经能做 shortlist，为什么还要 real search？

推荐回答：

因为 predictor 现在最强的角色仍然是 catalog 内的条件排序器，不是最终物理裁判。  
真实 gap 是否成立、覆盖率是否真的达到目标 band，仍然必须靠 COMSOL 验证和 refinement。

### 问题 3：shape-aware 是不是只是工程细节？

推荐回答：

不是。  
它实际上是 current target-band inverse design 成功的关键条件之一。  
因为旧问题不仅是参数范围不够，更是 shape pool 被旧 `gap34 / 200Hz` 偏置锁住了。  
shape-aware 把“搜索入口”从旧主线改成了按 band 条件化的入口。

---

## 10. 一分钟汇报版

如果后面你要用很短的话讲清楚这件事，可以直接用下面这个版本：

> 我们现在的逆向设计不是单靠预测器，也不是单靠真实搜索，而是三层配合。  
> 第一层是 predictor，它负责在给定 target band 下做条件排序，提出 shortlist。  
> 第二层是 shape-aware front-end，它按 band 重构 shape pool，避免搜索一直被旧 `gap34 / 200Hz` 盆地锁住。  
> 第三层是 exploratory real search，它在更合理的 shape 和更开放的参数范围下做真实 COMSOL refinement，把弱 band 真正打开。  
> 所以这条主线最准确的理解是：predictor 给方向，shape-aware 选入口，real search 把物理解打开，并把新 truth 再反哺预测器。

---

## 11. 当前结论

到目前为止，最准确的系统定位不是：

- “predictor 已经单独完成 inverse design”

也不是：

- “exploratory search 和 predictor 没关系”

而是：

**当前 thesis 主线已经形成了一个 prediction-guided + shape-aware + real-search refinement 的 target-band inverse-design 系统。**

这也是后面所有对照、案例、robustness 和论文写法都应该统一采用的口径。
