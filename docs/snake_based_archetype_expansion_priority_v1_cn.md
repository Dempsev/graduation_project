# snake_based_archetype_expansion_priority_v1

## 目标

把 hand-made archetype pilot 的有效方向，翻译成更正式的 snake-based 扩展优先级。

这里的核心原则不是“让 shape 更不圆”，而是：

1. 让 snake 更容易生成与高 weak-band 相关的有效机制；
2. 保持与原 snake 库同源；
3. 在不污染 frozen mainline 的前提下，先做隔离 pilot。

## 当前证据总结

基于 hand-made pilot 的 target-band 结果和 mode-shape 图：

1. `bilobe / 偏心质量分布` 最像真正引发了不同带边机制。
   - `band240_280__bilobe__ep195` 在 `1-2` gap pair 上打出了完整覆盖；
   - lower / upper mode shape 的空间组织差异最大；
   - 这是目前最强的新机制证据。

2. `asym / 强非对称` 次之。
   - `ep130 / ep183` 在 `240-280` 上表现强；
   - 更像是在紧凑主体上引入全局偏置和模态重心偏转；
   - 机制改变明确，但不如 bilobe 剧烈。

3. `neck / 窄颈桥接` 第三。
   - 有效果，但更像局部连接控制；
   - 比 bilobe / asym 更偏局部耦合调制。

4. `notch / 开口 / chord`
   - 还没正式测；
   - 建议作为下一批补充 archetype。

5. `更高阶 Fourier`
   - 仍然放最后；
   - 当前不建议靠升阶堆自由度。

## 优先级排序

### 1. bilobe-first

优先级最高。

原因：

- 最符合“新带边机制”目标；
- 最值得继续看能否稳定把 gap pair 推到 `1-2 / 2-3`；
- 即使整体轮廓仍较圆，也已经显示出不同于 canonical 的 mode organization。

snake 扩展时应优先追求：

- 主体质量中心偏离几何中心；
- inclusion 周边左右或上下质量分布失衡；
- 不要求整体高度夸张，但要允许一侧更鼓、一侧更收。

### 2. asym-second

优先级第二。

原因：

- 在 `220-260 / 240-280` 上已有稳定信号；
- 更适合做“全局不对称偏置”方向的系统补样本；
- 可能比 bilobe 更容易在 snake 里自然长出来。

snake 扩展时应优先追求：

- 主体整体左右不对称；
- 局部连接区偏向一侧；
- 允许紧凑主体上叠加小范围偏心凸起。

### 3. neck-third

优先级第三。

原因：

- 说明局部连接控制有效；
- 但目前证据显示它更像局部调制，而不是最强的新机制来源。

snake 扩展时应优先追求：

- 连接区更细、更长；
- 主体与局部 protrusion 之间存在明显颈部；
- 不追求整体复杂度，而追求局部桥接特征。

### 4. notch / chord-next

建议作为下一批新 archetype，而不是本轮首批重点。

原因：

- 可能在 band-edge 附近引入新的局部约束；
- 但当前还没有 hand-made pilot 证据；
- 适合作为 bilobe / asym / neck 之后的补充方向。

### 5. higher-order Fourier-last

当前不建议优先做。

原因：

- 容易只增加边界粗糙度；
- 不一定带来新的物理机制；
- 还会增加几何/接触不稳定风险。

## 生成时该控制什么

snake-based 扩展的控制重点应是：

1. **质量分布偏心**
   - 对应 bilobe。

2. **全局不对称偏置**
   - 对应 asym。

3. **局部细颈连接**
   - 对应 neck。

4. **保持尺度与主体紧凑性**
   - 不以“极端不圆”为目标；
   - 先保持与现有 snake 库接近的面积、宽高比和主体紧凑性。

## 哪些先不要碰

当前阶段不建议：

1. 直接追求极端复杂、不规则轮廓；
2. 一开始就大量引入高阶边界自由度；
3. 把新 snake shape 直接并入 frozen mainline；
4. 不做 isolation pilot 就大规模重跑全流程。

## 当前执行策略

本轮先做一个隔离的 snake pilot：

1. 新生成一批 snake states；
2. 提 contour 到独立目录；
3. 对 contour 做 archetype scoring；
4. 形成 `bilobe-first / asym-second / neck-third` 的候选池；
5. 后续再决定哪些值得接到 target-band 筛选。

## 当前判断

最值得转成 snake-based 扩展的优先级是：

1. `bilobe`
2. `asym`
3. `neck`

而且当前证据支持：

真正值得追的是**局部质量/连接组织方式**，不是“整体离圆形越远越好”。
