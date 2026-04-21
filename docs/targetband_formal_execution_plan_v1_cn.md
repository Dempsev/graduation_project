# Target-Band 逆向设计正式执行方案（中文版）

## 1. 当前项目定位

项目现在已经不再处于“能不能开始做 target-band 优化”的阶段。

这个问题其实已经被当前仓库和最近一轮真实 COMSOL 结果回答了：

- 真值生产链已经完整
- target-band 条件预测器已经可用
- shape 前端已经从旧的 `gap34` 逻辑升级成了 band-aware shape selection
- exploratory real search 已经把保守搜索打不开的弱 band 顶起来了
- 新真值已经回灌进训练集，并形成了 `v8`

所以现在更准确的项目定位应该是：

**面向 thesis band catalog 的 target-band 条件预测与逆向设计主线**

但边界要控制清楚：

- 当前二维声子晶体流程
- 当前参数化结构族群
- 当前 thesis band catalog
- 对未见 shape family 的泛化
- 对 catalog 内 band 的部分迁移能力

同时明确不主张：

- 任意连续频率范围上的完全泛化
- 任意材料体系上的完全泛化
- 任意结构表示下的通用逆向设计

## 2. 论文主张

现在可以正式固定的主张是：

**我们建立了一套面向 thesis band catalog 的 target-band 条件预测与逆向设计流程：条件预测器先为指定目标频带提出候选，band-aware search/refinement 再在真实 COMSOL 约束下改进候选，最终得到经过验证的目标频带可用结构。**

这条主张由 4 个子主张支撑：

1. 预测器学到了有用的 target-band 结构响应规律。
2. 预测器不仅能做离线预测，还能作为搜索前端使用。
3. shape-aware selection 是必要的，而且会实质改变弱 band 的搜索效果。
4. 只有在 band-aware + exploratory 的真实搜索下，弱 band 逆向设计才真正变得可行。

## 3. 当前系统主线结构

现在项目最合理的写法是 5 层结构：

1. **Truth Production**
   - 真实 COMSOL 数据生产与验证
   - 对应 stage1/stage2/stage4 等主线

2. **Conditional Prediction**
   - target-band 固定窗口预测
   - target-band 参数化条件预测
   - 当前主数据版本：`windows_dense_v8_truth_plus_exploratory_aug_v1`

3. **Band-Aware Shape Selection**
   - shape atlas
   - family-balanced、band-aware 的 shape pool
   - `strong / near-miss / weak-band contributor / hard-negative` 角色划分

4. **Prediction-Guided Search and Refinement**
   - RF 分类器做 likely-open screening
   - HGB 回归器做 cover ratio 排序
   - 形成 target-band shortlist
   - 再进入真实 COMSOL refinement / search

5. **Validation and Truth Harvesting**
   - COMSOL 验证
   - 新真值回收到训练集
   - 形成 model-search co-evolution

这才是现在项目真实存在的系统结构，已经不适合再把它只描述成一个“小型优化原型”。

## 4. 已经成立的结论

下面这些结论现在应该被视为“已成立”，而不是“待验证”。

### 4.1 预测主线已经成立

当前主模型组合已经固定为：

- 分类器：RF
- 回归器：HGB
- 数据集：`windows_dense_v8_truth_plus_exploratory_aug_v1`

除非后面有明确更强的替代证据，否则不建议再频繁换模型路线。

### 4.2 Shape 已经成为正式任务变量

项目已经不再只是“调 Fourier 参数”。

现在 shape 前端已经通过下面这条线被正式建模：

- `prediction_targetband_param_v1/tools/build_targetband_shape_atlas_v1.py`
- `data/analysis/targetband_shape_atlas_v1/`

这一层应该在论文里被明确写成方法升级，而不是辅助工程细节。

### 4.3 弱 band 搜索已经被实质推进

exploratory supplement search 已经说明：

以前弱 band 起不来，并不是这些 band 天生做不到，而是之前的搜索入口和探索方式过于保守。

来自：

- `data/comsol_batch/comsol_in_loop_band_supplement_exploratory_v2/ga_band_catalog_summary_v1.csv`

的代表性结果包括：

- `band200_240`: cover `1.000`
- `band220_260`: cover `1.000`
- `band240_280`: cover `0.898`
- `band180_220`: cover `1.000`

和旧保守补数线相比，这是一个非常明显的跃迁。

### 4.4 真值回灌闭环已经成立

现在项目已经形成完整闭环：

- 搜索产出新的弱 band 真值
- 真值被回收为 fixed-window 数据
- 再堆叠回参数化 target-band 数据集
- 再用于重训预测器

这是项目里非常强的一条证据链，后面应该重点强调。

## 5. 论文里的核心证据结构

后面的核心证据建议围绕 3 个问题组织。

### 问题 A：预测器是否真的有 shortlist 价值？

用这些指标回答：

- family-CV
- leave-one-band-tag-out
- top-k / shortlist 质量
- 概率校准和单调性检查

核心解释是：

预测器不需要把每个样本都预测得特别准，但它必须能把真正值得验证的候选排到前面。

### 问题 B：预测器是否真的能驱动真实搜索？

用这些证据回答：

- predictor-guided candidate proposal
- 真实 COMSOL search / refinement
- 最终验证结果
- 与 baseline 的对比

核心解释是：

预测器不是在替代物理，而是在把逆向设计从“盲搜”变成“有方向的搜索”。

### 问题 C：弱 band 是否真的被打通了？

用这些证据回答：

- 保守弱 band 搜索 vs exploratory 弱 band 搜索
- 旧 shape pool vs band-aware shape pool
- exploratory truth 回灌前后的 coverage 变化
- 最终弱 band 最优结构的 overlap / cover

这里最近的 `exploratory v2` 结果应该被放到最核心的位置。

## 6. 更新后的研究推进策略

接下来建议把项目理解成两条耦合但不完全对等的线：

### A 线：预测器加强线

目标：

- 提高 target-band predictor 作为 shortlist engine 的可靠性
- 提高 catalog 内 band 迁移能力
- 让弱 band 排序更稳定

### B 线：逆向设计展示线

目标：

- 做出更强的真实 COMSOL target-band 案例
- 证明 band-aware search 和 refinement 的价值
- 形成论文里的图表和案例

这两条线是互相喂数据的：

- 搜索产出弱 band 真值
- 真值提升预测器
- 预测器提升未来的 shortlist 质量

但现在它们不再同等紧急。

在当前阶段，**逆向设计证据收口与案例成型** 应该优先于新的大规模模型试验。

## 7. 接下来的正式执行顺序

后面建议固定按下面这个顺序推进。

### 第一步：冻结当前主线定义

把下面几件事锁定：

- thesis 主张
- thesis band catalog
- 当前默认模型组合：RF + HGB
- 当前默认数据版本：`v8`
- 当前 shape-aware 前端

除非后面有非常强的新证据，否则不要再频繁重开模型路线讨论。

### 第二步：做 predictor readiness 报告

做一份简洁但完整的 readiness 报告，回答：

- family-CV 怎样？
- leave-one-band 怎样？
- top-k shortlist 质量怎样？
- 概率和分数是否至少具备基本可用性？

这份报告就是后面证明“预测器足以进入逆向设计主线”的正式依据。

### 第三步：固定逆向设计案例

第一批 canonical case 建议固定为：

1. `band200_240`
   - `ep193_step51_contour_xy`
2. `band220_260`
   - `ep253_step54_contour_xy`
3. `band240_280`
   - `ep253_step54_contour_xy`
4. `band180_220`
   - `ep248_step27_contour_xy`

每个案例都要整理：

- shape identity
- 优化参数
- 目标 band
- 真实 gap 边界
- overlap Hz
- cover ratio
- 与旧 baseline 的差别

### 第四步：系统化做 baseline 对照

后面每个 target band 的对照组应该尽量标准化：

- 随机 / generic candidate baseline
- 旧 seed/local 线
- 旧 conservative supplement 线
- 旧 band-catalog real-GA 线
- predictor-guided / shape-aware / exploratory 主线

重点比较：

- 真实 open rate
- 真实 overlap Hz
- 真实 cover ratio
- top-k hit count
- best candidate quality
- family diversity
- budget efficiency

### 第五步：把弱 band coverage 作为常规分析项

以后不要只看平均模型指标。

每轮都要跟：

- 各弱 band 的正样本数
- 各弱 band 的正样本 family 数
- 各弱 band 的 mean positive cover ratio
- 各弱 band 的 shortlist 质量
- 各弱 band 的最终 inverse-design usefulness

这会比只看平均分更能解释项目有没有真实推进。

### 第六步：在主线稳定后再补 robustness

robustness 很重要，但不是当前最紧迫的 blocker。

等主线证据稳定后再加：

- threshold sensitivity
- ranking stability
- 局部参数扰动稳定性
- 最优候选邻域稳定性

## 8. 当前不该成为主焦点的内容

下面这些内容现在不建议作为主推进方向：

- 大规模材料 profile 扩展
- 任意连续 band 的强主张
- 再大幅更换 predictor 模型路线
- 重跑旧保守搜索线
- 回到只按 `gap34_gain_Hz` 选 shape

这些不是没价值，而是当前都不是最应该优先的事。

## 9. 论文写法建议

论文结构建议按下面这个顺序展开。

### 章节逻辑

1. **真实数据生产与积累**
2. **target-band 条件预测**
3. **为什么需要 shape-aware selection**
4. **预测驱动的逆向设计流程**
5. **通过 exploratory real search 打通弱 band**
6. **验证、对照与局限性**

### 叙事转变

不要再把项目表述成：

- “寻找带隙最宽的结构”

而应该表述成：

- “建立面向指定目标频带的条件预测与逆向设计流程”
- “预测器负责提出 shortlist”
- “shape-aware + exploratory real search 负责跳出旧的 `gap34 / 200Hz` 盆地”
- “整个流程在 thesis band catalog 内得到验证”

### 推荐用词

优先使用：

- “catalog 内 target-band 条件预测”
- “target-band 逆向设计”
- “predictor-guided shortlist and real refinement”
- “band-aware shape selection”
- “weak-band truth harvesting”

避免过度主张的说法：

- “任意频带通用预测”
- “完全通用逆向设计”
- “完全解决未见 band 泛化”

## 10. 最终执行结论

现在项目真正的问题已经不是：

- “预测驱动优化能不能开始”

而应该变成：

**“如何把现在已经得到的 target-band 条件预测、band-aware shape selection 和 exploratory real-search 结果，整理成一条清楚、可对照、可写入论文的逆向设计主线。”**

所以接下来最应该做的是：

- 更清楚的证据收口
- 更清楚的 baseline 对照
- 更强的案例表达
- 更稳定的弱 band coverage 跟踪

而不是再重新怀疑主方向本身。
