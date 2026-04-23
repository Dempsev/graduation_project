# Target-Band 定向扩样本与扩 Shape 执行方案 v1

## 1. 总目标与执行原则

这一部分工作的目标不是把数据做得更大，而是只在能够带来**新信息**时，定向补样本、补 family、补 shape archetype。

这里的“新信息”只认下面四类：

1. weak-band strong family 数增加  
   例如 `band240_280` 的 strong family 从 `10` 增到 `15+`。

2. `best_band_tag` 分布往高 band 移动  
   新增 shape/family 的最佳 band 更常落在 `band200_240 / band220_260 / band240_280`。

3. 出现新的 band-edge mode / dispersion 机制  
   新 shape 的 lower/upper edge 模态分布，不再只是 `ep248/ep253` 那类已知模式。

4. 出现新的 failure / near-miss 类型  
   某些新 family 系统性失败，本身也能告诉我们当前表示空间哪些方向不值得继续。

执行总原则：

- 不做无差别大扩 shape。
- 不为了“看起来更大”而堆数据量。
- 扩完后优先重建 atlas 和主模型，不全量重跑历史主线。
- 所有新增结果都必须与 frozen mainline 显式对比。
- 一旦发现新增 shape 主要重复旧分布，就停止。

---

## 2. 现状判断与为什么要这样扩

从当前 shape atlas 来看，问题不是“完全没有 family”，而是 weak band 的 family **转 strong 效率不高**。

### 2.1 当前关键现状

- 当前 shape pool 约有 `222` 个 shape、`81` 个 family。
- `band200_240`：pool 中 `47` 个 family，但只有 `19` 个 strong family。
- `band220_260`：pool 中 `81` 个 family，但只有 `16` 个 strong family，`64` 个 family 的 best role 只是 `near_miss`。
- `band240_280`：pool 中 `81` 个 family，但只有 `10` 个 strong family，`66` 个 family 的 best role 是 `near_miss`。

### 2.2 这说明什么

1. `band220_260` 和 `band240_280` 的主要瓶颈，不是 pool 里 family 太少，而是很多 family 只能到 near-miss，进不了 strong。
2. 当前库整体更偏低中频。shape role 统计里，大多数 shape 的 `best_band_tag` 仍集中在 `band140_180` 和 `band160_200`。
3. 当前 shape 表示空间仍以低阶 Fourier 轮廓和离散 contour perturbation 为主，表示能力并不算宽。

所以，最优策略不是：

- 直接再造几百个同风格简单 shape；

而是：

- 先在 weak-band near-miss family 内定向补样本；
- 再补一小批与现有机制明显不同的新 archetype。

---

## 3. 优先级 1：先做 weak-band near-miss family 内定向补样本

### 3.1 目标

把当前 weak band 中已经表现出潜力、但还没转成 strong 的 family，优先往 strong 推。

### 3.2 为什么排第一

这是当前最省成本、最可能立刻带来新信息的一步。

因为这些 family 已经证明：

- 不是纯 hard negative；
- 在 weak band 有正 overlap；
- 只是还差一点没进入 strong 区。

这类 family 最适合补少量新变体，观察它们能不能从 near-miss / weak contributor 转成 strong family。

### 3.3 建议优先补的 family

#### `band240_280`

- `ep183`
- `ep195`
- `ep205`
- `ep209`
- `ep218`
- `ep252`
- `ep253`

#### `band220_260`

- `ep195`
- `ep205`
- `ep206`
- `ep248`
- `ep252`
- `ep253`

#### `band200_240`

- `ep36`
- `ep130`
- `ep193`
- `ep195`
- `ep253`

### 3.4 每个 family 怎么补

建议每个 family 只补 `5-15` 个新变体，不多做。

优先围绕已有证据支持的方向补：

- `ep253` 类高 band 家族：优先沿 `a1+ / a2- / b2+`
- 其他 family：优先先做一轮小 trust-region 定向采样
- `r0` 不作为主扩展方向，只做窄范围控制

建议对每个 family 采用三类补点：

1. 已知有利方向点  
   例如 `a1+`、`a2-`、`b2+` 一类。

2. near-miss 修正点  
   用少量点尝试把 overlap 从低值推向 `0.15+ / 0.50+`。

3. failure-boundary 点  
   刻意贴近失败边界，补 failure mode 信息。

### 3.5 推荐批次规模

建议先做一个小批次：

- `8-12` 个 family
- 每个 family `8-10` 个新点
- 总量控制在 `80-120` 个 shape/case`

### 3.6 这一优先级的完成标准

满足以下任一项即可算成功：

1. `band220_260` strong family 数从 `16` 提升到 `20+`
2. `band240_280` strong family 数从 `10` 提升到 `13+`
3. `band200_240` strong family 数从 `19` 提升到 `24+`
4. 明确识别出一批“怎么补也上不去”的 family，并形成剔除名单

### 3.7 如果失败，怎么判断

如果补完后出现下面情况，就说明这条线收益有限：

- strong family 数几乎没涨
- 新样本大多只是重复旧 near-miss 分布
- best band 分布基本不动

这时就不要继续在同风格 family 上追加大量样本。

---

## 4. 优先级 2：做“小而异质”的新 shape 子库

### 4.1 目标

不是把 shape 做得更复杂，而是引入**当前库里不充分存在的新机制 archetype**。

### 4.2 为什么要单独开这一层

当前库的问题不是完全没 family，而是高弱 band 中：

- family 多
- strong 少
- near-miss 很多

这意味着同风格 shape 的增量，很可能继续制造 near-miss，而不是新 strong family。

所以第二步必须是“机制差异”导向，而不是“数量差异”导向。

### 4.3 建议的 archetype 方向

这里的方向是执行建议，不是当前仓库既有结论。

建议优先尝试 `3-5` 个 archetype：

1. 更强非对称 family  
   目标：打破当前较平滑、较均匀的轮廓分布。

2. 更明显窄颈 / 桥接 family  
   目标：改变局部连接区域与主轮廓的耦合方式。

3. 更明显双叶 / 偏心质量分布 family  
   目标：改变 inclusion 周边与 matrix 的 mode 组织方式。

4. 更强 notch / 开口 / chord 型 family  
   目标：在 band-edge 附近引入不同的局部约束与边界效应。

5. 必要时再考虑更高阶 Fourier 主导 family  
   但这项排最后，不建议一开始就单纯靠升阶堆自由度。

### 4.4 推荐规模

建议每个 archetype 先做 `20-30` 个 shape。

总量控制在：

- `60-150` 个新 shape

先小批次看分布变化，不要一开始就扩成几百上千。

### 4.5 如何判断这些 archetype 值不值

至少满足下面一项，才算值得继续：

1. 新 archetype 出现了高 weak band strong family
2. 新 archetype 的 `best_band_tag` 明显上移
3. 新 archetype 的 mode shape 与现有 canonical 机制明显不同
4. 新 archetype 形成一类稳定的新 near-miss / failure pattern

如果这些都没出现，就说明只是“换了外形，但没带来新物理信息”。

### 4.6 这一优先级的停止条件

如果首批 `60-150` 个新 shape` 已经跑完，但：

- `band200_240+` 的 best band 分布没明显改善
- strong family 数没明显增加
- mode shape 机制没有新东西

那就停止，不继续放大这条线。

---

## 5. 优先级 3：只在 shape 扩展确实有效后，再考虑 profile/material

### 5.1 目标

验证当前方法是不是只会在一个 physics/material profile 下成立。

### 5.2 为什么排第三

在没证明 shape 扩展本身有效之前，先加 material/profile 只会把问题维度放大。

如果 shape 这一步还没带来：

- 更多 strong family
- 更高 weak-band best-band 占比
- 新的 band-edge mechanism

那先加 material/profile 的收益通常不高。

### 5.3 建议怎么做

只做非常小规模扩展：

- `1-2` 个 material/profile
- 每个 profile 只跑第一步里最有价值的 family 子集

优先看：

- 原 strong family 是否还能保持 strong
- 原 near-miss family 的排序是否被明显改写
- canonical case 的 band-edge mode 是否发生机制变化

### 5.4 成功标准

只要满足下面一项，就有继续价值：

1. 原 weak-band strong family 在新 profile 下仍具有可迁移性
2. 某些旧 near-miss family 在新 profile 下转 strong
3. 新 profile 改写了 weak-band family 排序，为下一篇文章提供新的 generalization 结论

---

## 6. 优先级 4：重训 atlas 和主模型，但不全量重跑旧主线

### 6.1 目标

把新扩展的数据接回你当前 pipeline，但不推倒既有 frozen mainline。

### 6.2 推荐做法

扩完后，只做下面这些：

1. 重建 shape/family atlas
2. 重训 target-band classifier / regressor 主模型
3. 重新生成 weak-band dashboard
4. 重新统计 strong family / best-band 分布

不建议做：

- 整套历史 stage 全量重跑
- 静默替换 canonical mainline
- 把新结果和旧结果混在一起不做显式比较

### 6.3 必须做的显式对比

每次扩展后，至少要和 frozen mainline 比下面几项：

1. `band200_240 / 220_260 / 240_280` 的 strong family 数
2. `best_band_tag` 在高 band 的占比
3. weak-band canonical shortlist 的质量变化
4. 新增 failure / near-miss 类型

### 6.4 最终写作定位

这一部分即使做成，也不应改写你已经冻结的 thesis 主线。

更合理的定位是：

- 作为 mainline 的 upgrade / extension
- 或作为下一阶段工作的前导实验

---

## 7. 推荐的实际执行顺序

建议严格按下面顺序做：

1. 先做 weak-band near-miss family 内定向补样本  
   目标：把已有潜力 family 往 strong 推。

2. 看 strong family 数和 best-band 分布是否真的改善  
   如果没改善，就停止，不进入大扩 shape。

3. 只有在第一步有明显收益时，再做一小批新 archetype shape 子库  
   目标：引入新机制，而不是堆旧分布。

4. 只有在 shape 扩展已经证明有效后，再考虑 `1-2` 个 material/profile  
   目标：验证泛化，而不是提前放大维度。

5. 最后才重建 atlas 和主模型，并和 frozen mainline 显式对比  
   目标：把新增结果收成可解释 upgrade，而不是推翻旧主线。

---

## 8. 一句话执行建议

如果你现在就要开始做，我最推荐的第一批工作是：

1. 先挑 `band240_280 / 220_260 / 200_240` 中最有价值的 `8-12` 个 near-miss family
2. 每个 family 只补 `8-10` 个定向新点
3. 先看 strong-family 数和 best-band 分布有没有动
4. 如果动了，再做 `3-5` 个新 archetype，小规模建立第二代 shape 子库

换句话说：

**先做“把已有潜力 family 往 strong 推”的定向补样本，再做“引入新机制”的 shape 扩展；不要一开始就大扩全库。**
