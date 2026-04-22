# Target-Band 项目优先级执行方案 V1

## 1. 文档目的

本文档用于把当前项目状态、已冻结主线、已有分析结论，以及后续建议，统一收成一份可以边执行边查看的行动方案。

它服务的不是“继续发散探索”，而是：

- 在 thesis 收官阶段保持主线稳定
- 明确什么是现在必须做的
- 明确什么是可以加分但不该抢主线的
- 明确什么属于下一阶段工作，不在当前阶段抢资源

本文默认前提如下：

- thesis-facing mainline 已冻结
- target-band thesis band catalog 已冻结
- 当前默认数据集、模型组合、shape-aware front-end 已冻结
- canonical inverse-design cases 已经形成
- local robustness 已经给出第一轮方向性结论

对应参考：

- [targetband_mainline_freeze_v1.md](/d:/graduation_project/coad/docs/architecture/targetband_mainline_freeze_v1.md)
- [targetband_formal_execution_plan_v1_cn.md](/d:/graduation_project/coad/docs/targetband_formal_execution_plan_v1_cn.md)
- [canonical_inverse_design_cases_v1_cn.md](/d:/graduation_project/coad/docs/canonical_inverse_design_cases_v1_cn.md)
- [canonical_local_robustness_results_v1_cn.md](/d:/graduation_project/coad/docs/canonical_local_robustness_results_v1_cn.md)
- [evidence_consolidation_and_robustness_plan_v1_cn.md](/d:/graduation_project/coad/docs/evidence_consolidation_and_robustness_plan_v1_cn.md)

## 2. 总判断

当前项目已经不再处于“要不要做 target-band 主线”的阶段，而是处于“如何把已经成立的主线收紧、补强并写成论文”的阶段。

最重要的判断有四条：

1. 当前主线已经够支撑 thesis 完成，后续不应再频繁重开模型路线、数据路线和问题定义。
2. 现在最值钱的工作不是再开新主线，而是把已有证据链补完整，特别是把数值结果变成图证和标准案例。
3. 精修有价值，但它是增强项，不是当前证明主线成立的必要条件。
4. 扩样本和扩 shape 只有在引入新 weak band、新 family、新 profile 或新机制时才值得，否则容易耗时大于收益。

因此，后续工作应严格按优先级推进，而不是把“封口、补图、精修、扩展”混在一起做。

## 3. 当前项目状态概括

### 3.1 已经可以视为成立的部分

下面这些内容，当前应视为“已成立的主线组成”，而不是“仍待反复验证的方向”：

- target-band conditional prediction 主线已建立
- 当前 thesis band catalog 已冻结
- 默认模型对已经冻结为 `RF + HGB`
- shape-aware front-end 已经是正式方法组成部分
- exploratory real search 已经实质性打通若干 weak band
- canonical inverse-design cases 已经形成
- local neighborhood robustness 已经给出明确结论

### 3.2 当前最关键的不足

当前真正的不足，不是“没有结果”，而是“结果组织和图证还不够完整”。

主要缺口包括：

- 论文叙事虽然已有雏形，但还没有被整理成一套完全稳定的结果章节骨架
- 很多强结论目前主要是表格和 CSV 结论，图证还不足
- COMSOL 中可用的 mode shape / band diagram 还没有系统导出和组织
- refinement 还没有被明确限制在轻量、局部、服务主线的边界内
- 数据扩展这件事容易失控，需要延后并设定硬条件

### 3.3 当前可直接拿来用的核心案例

建议持续固定为 canonical cases 的对象：

1. `band200_240`
   `ep193_step51_contour_xy`
2. `band220_260`
   `ep253_step54_contour_xy`
3. `band240_280`
   `ep253_step54_contour_xy`
4. `band180_220`
   `ep248_step27_contour_xy`

这些案例的作用不是“展示几个好结果”，而是作为整条主线的标准样本，用于：

- 论文结果展示
- baseline 对照
- COMSOL 图证展示
- local robustness 分析
- 后续轻量 refinement

## 4. 优先级 1：先完成论文主线封口

### 4.1 目标

这一优先级的目标是：

**把项目从“很多结果并列存在”收成“有一条固定主张、固定证据链、固定标准案例的 thesis-facing mainline”。**

这是当前最优先的工作，因为它直接决定：

- 论文写作是否稳定
- 汇报时叙事是否清楚
- 后续补充工作是否会把主线带偏

### 4.2 这一优先级为什么排第一

因为目前主线本身已经够用了，不缺“有没有结果”，缺的是“怎么稳定讲清楚、讲完整、讲成一套”。

如果这一步不先做，后面哪怕再补很多图、跑一些精修，也会出现下面的问题：

- 结果越来越多，但不知道该把哪条放正文、哪条放补充
- 结论时强时弱，口径来回变化
- baseline、predictor、shape-aware、exploratory 之间关系讲不顺
- 后续每加一点东西，就会重新怀疑是否要改主线定义

### 4.3 要完成的具体任务

#### 任务 1：固定项目主张与边界

把论文主张统一到一版标准表述上，后续所有文档和汇报尽量复用。

建议固定口径为：

`prediction-guided + shape-aware + real-search refinement`

需要明确：

- predictor 负责 shortlist 和方向感
- shape-aware front-end 负责改善起始池质量与 family 结构
- real COMSOL search/refinement 负责把候选推进成真实可用设计

同时也要明确边界：

- 当前不是任意连续频带的通用反设计
- 当前不是任意材料体系的完全泛化
- 当前不是任意结构表示的通用逆向设计

#### 任务 2：固定证据链结构

建议把正文结果链固定为四段：

1. predictor readiness
2. canonical inverse-design cases
3. baseline comparison
4. weak-band coverage and usefulness

每一段都回答一个明确问题：

1. predictor 是否足以作为 shortlist engine 使用
2. 主线是否真的找到了可用的 target-band 设计
3. 新主线相对旧 baseline 到底强在哪里
4. 弱 band 是否真的被打通，而不是只在强 band 上有效

#### 任务 3：给 canonical cases 建标准化卡片

每个 canonical case 都建议统一收成同一种模板，至少包含：

- target band
- shape id / shape family
- 关键参数
- 真实 gap 边界
- overlap Hz
- cover ratio
- 与 conservative supplement 的对比
- 与 band-catalog real GA 的对比
- 这一案例在论文里要说明什么

#### 任务 4：给论文结果章定骨架

建议结果章按下面顺序组织：

1. 数据与真值生产链
2. target-band conditional prediction
3. shape-aware selection 的必要性
4. predictor-guided inverse-design workflow
5. weak-band breakthrough cases
6. validation、baseline、robustness 与局限

### 4.4 建议产出物

这一优先级建议至少产出这些成品：

- 一页主线结构图
- 一张 canonical cases 总表
- 一张 baseline comparison 总表
- 一张 weak-band coverage 总表
- 一段标准 thesis claim
- 一段标准方法描述
- 一段标准 limitations 描述

### 4.5 完成标准

这一优先级完成后，应满足：

- 你可以在 5 分钟内稳定讲清楚整条主线
- 论文正文结构已经不再需要大改
- 后续任何补充实验都只是增强项，而不是重新定义主线

## 5. 优先级 2：补 COMSOL 图证，把表格结论升级成可视化证据

### 5.1 目标

这一优先级的目标是：

**把当前已经成立的数值结论，升级成更直观、更适合论文和答辩展示的物理图证。**

当前仓库里，COMSOL 结果对象并不是没有图，而是自动管线主要稳定吃了 `tbl1`。因此，现在最值得做的不是盲目抓更多表，而是把最能支撑论文内容的图导出来。

### 5.2 为什么这一步排第二

因为你现在已经有很多“数字上很强”的结论，但图像层面的说服力还不够强。

特别是在下面这些问题上，图证比单纯表格更有用：

- 为什么这个 target-band gap 会在这里打开
- 结构变化到底影响了哪一类 band edge
- `r0` 为什么会更敏感
- 某些 weak band 为什么虽然能打通，但更接近边界状态

### 5.3 只建议优先做的三类图

#### 任务 1：canonical cases 的 band-edge mode shape 图

对每个 canonical case，优先导出：

- lower edge mode
- upper edge mode

这类图的作用是：

- 支撑机理解释
- 支撑“为什么这个 band gap 在该处形成”
- 为后续 `r0` 敏感性解释提供物理图像基础

#### 任务 2：center vs local perturbation 的 dispersion 对照图

对每个 canonical case，至少绘制：

- canonical center dispersion
- 1 到 2 个代表性局部扰动点 dispersion

建议优先扰动：

- `r0_plus`
- `r0_minus`
- 一个相对稳定方向，如 `a1_plus` 或 `b2_plus`

这类图的作用是：

- 说明当前分析不是只盯着一个 gap 指标
- 说明局部扰动如何改变整条 band structure
- 把 robustness 结论做得更直观

#### 任务 3：gap-edge 漂移图

建议把 local robustness 结果做成图：

- 横轴为 perturbation variant
- 纵轴为 lower edge / upper edge
- 同图叠加 target band window

这类图很适合直接回答：

- 哪些参数扰动只造成轻微漂移
- 哪些扰动会使边界明显偏移
- `r0` 为什么应当成为 refinement 和 robustness-aware 优化的重点变量

### 5.4 执行边界

这一步一定要限制范围，避免沦为“把所有 COMSOL 结果都抓出来”。

建议边界如下：

- 只针对 4 个 canonical cases
- 每个案例最多补 2 到 4 张核心图
- 先解决论文最需要的图，不追求全自动覆盖全部 case

### 5.5 建议执行顺序

建议顺序如下：

1. 先补 `band200_240`
2. 再补 `band220_260`
3. 再补 `band240_280`
4. 最后补 `band180_220`

原因是前 3 个案例对 weak-band 突破的说明价值更高。

### 5.6 完成标准

这一优先级完成后，应满足：

- 每个 canonical case 至少有可用于正文的 mode shape 图
- 至少有 1 组中心点 vs 扰动点的 dispersion 对照图
- 至少有 1 张可支撑 `r0` 敏感性结论的边界漂移图

## 6. 优先级 3：做轻量 refinement 收尾，但严格限制范围

### 6.1 目标

这一优先级的目标是：

**不是重新开一轮大优化，而是在 canonical cases 附近做小范围、低风险、高解释价值的精修。**

这一步的定位一定要清楚：

- 它不是 thesis 主线成立的前提
- 它是把当前结果从“可用解”推向“更像设计方法”的增强项

### 6.2 为什么它有价值

虽然 GA 已经足以证明“能找到 target-band 可用解”，但并不自动等于：

- 这个点已经最贴目标
- 这个点已经最稳
- 这个点已经最适合做最终设计展示

你当前的 local robustness 已经给出清楚信号：

- `a1 / a2 / b2` 相对稳
- `r0` 更敏感

所以 refinement 的价值不在于“再大范围搜一遍”，而在于：

- 能否让目标带边界更贴
- 能否在不损失太多 cover 的前提下降低敏感性
- 能否把某些 canonical case 修到更像最终设计点

### 6.3 必须遵守的范围限制

这一步建议设置硬边界：

- 只做 canonical cases
- 只做局部微调
- 只动少量参数
- 不重新开大规模真实 GA
- 不把 refinement 变成新的独立主线

### 6.4 参数优先级

建议参数优先级如下：

1. `r0`
2. `a1`
3. `a2`
4. `b2`

`a4 / b5` 暂不作为主轴，除非某个案例明确显示有必要。

### 6.5 建议优化目标

建议只用下面三类目标，不要重新回到“总带隙最大化”：

1. 目标带边界更贴目标窗口
2. cover ratio 基本不降的前提下提高局部稳健性
3. 降低 `r0` 扰动导致的明显塌陷风险

### 6.6 建议先做的 case

优先顺序建议如下：

1. `band240_280`
2. `band220_260`
3. `band200_240`
4. `band180_220`

原因：

- `240-280` 当前最难，最值得试图向更完整覆盖推进
- `220-260` 结果强，但也更适合用来证明高 band 设计可进一步稳固
- `200-240` 是弱 band 打通的标志性案例，适合做“从可用到更稳”的展示
- `180-220` 相对成熟，可以放后

### 6.7 成功标准

这一步不要求“大幅刷新纪录”，以下任一情况都算成功：

- target band 边界更贴目标窗口
- 某个 canonical case 在 `r0` 扰动下不再立刻塌
- 同样 cover 下得到更自然的参数位置
- 证明某个案例已经很接近稳定局部最优

### 6.8 什么时候停止

建议给 refinement 设置停止条件：

- 一旦发现收益变得很小，就停止
- 不允许为了追求很小的数值提升而延长主线
- 如果 1 到 2 轮微调后没有实质性收益，应回到写作和图证工作

## 7. 优先级 4：最后才考虑定向扩样本和扩 shape

### 7.1 目标

这一优先级的目标不是“把数据做得更大”，而是：

**只在能带来新信息的时候，定向补样本、补 family、补 profile。**

### 7.2 为什么这一步要排最后

因为当前 thesis 主线已经够了。

现在真正缺的不是“更多相似样本”，而是：

- 更强的图证
- 更稳的案例叙事
- 更清楚的 baseline 对照
- 更完整的论文封口

如果现在直接去扩 shape、扩样本、全量重跑，很容易出现：

- 时间消耗巨大
- 新增样本大多只是重复旧分布
- 模型指标有变化，但论文主线并没有本质增强
- 工作重心从“收口”又被拉回“重开探索”

### 7.3 只有在以下条件下才值得扩

新增数据必须至少满足下列之一：

- 增加 weak-band 正样本
- 增加新的 shape family
- 增加新的物理条件或材料 profile
- 增加新的 near-miss / failure mode 类型

如果不能满足这些条件，扩样本的性价比通常较低。

### 7.4 建议扩展顺序

如果后面真的有余力，建议扩展顺序如下：

1. 补 `band200_240 / 220_260 / 240_280` 的 family 缺口
2. 补 weak-band 正样本稀缺的 shape families
3. 小规模增加 1 到 2 个 material/profile
4. 视情况再讨论更大规模扩展

### 7.5 不建议现在做的事情

当前阶段不建议：

- 大规模无差别扩 shape
- 为了“看起来更大”而堆数据量
- 把整套历史主线从头全量重跑
- 在没有新信息增量的情况下重新比较大量模型 family

### 7.6 真要做时的原则

如果进入这一优先级，建议遵守：

- 扩完后只重训主模型，不推倒整套流程
- 所有新结果必须与 frozen mainline 做显式对比
- 新结果只能作为 upgrade，不应静默替换主线

## 8. 推荐执行顺序

后续建议严格按下面顺序推进：

1. 完成主线封口
2. 补 COMSOL 图证
3. 做轻量 refinement
4. 最后再考虑定向扩样本和扩 shape

更简短地说：

1. 先把故事讲稳
2. 再把图补强
3. 再把 case 修漂亮
4. 最后才谈扩展

## 9. 论文视角下的“必做 / 可选 / 下阶段”

### 9.1 Thesis 必做

- 固定 thesis claim、方法描述和边界
- 固定 canonical cases 与标准案例表
- 固定 baseline 对照表
- 输出 weak-band usefulness / shortlist value 结果
- 补至少一轮核心 COMSOL 图证
- 把 local robustness 结果写进论文主线

### 9.2 有时间就做

- canonical cases 的轻量 refinement
- 增加更漂亮的 band-edge / dispersion 图组
- 把局部边界漂移做成更正式的 robustness 图表

### 9.3 下一阶段工作

- 定向扩 weak-band family
- 加 material/profile 扩展
- 更重的能量分布、模式连续性分析
- 更一般化的 robustness-aware optimization
- 更大范围的数据和模型升级

## 10. 最终结论

当前项目最合理的推进策略不是继续无差别扩张，而是围绕已经成立的 thesis-facing mainline 做收口增强。

最明确的执行判断可以固定为：

1. 先封口，把项目主张、证据链、案例体系稳定下来。
2. 再补图，把当前数值结论升级成论文级图证。
3. 再精修，只围绕 canonical cases 做有限、服务主线的 refinement。
4. 最后才扩展，而且只扩真正带来新信息的 weak-band / family / profile。

如果严格按这个顺序推进，项目最稳，论文也最容易收官，而且后续若要往更强版本推进，也保留了清晰的升级路径。
