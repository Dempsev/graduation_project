# bilobe_only_contact_aware_snake_pilot_v1

## 目标

在**不修改主线几何/接触判定规则**的前提下，启动一个 `bilobe-only` 的 snake 扩展 pilot。

这条线的目标不是“放宽规则”，而是：

1. 继续保持与原 snake 库同源；
2. 只优先追已经被 hand-made pilot 和 snake pilot 同时支持的 `bilobe` 方向；
3. 在进入 COMSOL 之前，加一层更强的 contact-aware 预筛；
4. 让下一轮候选更容易在**同一条老规则**下通过 `contact_valid`。

## 不做什么

这一版明确**不做**下面这些事：

1. 不改 `build_geom / validate_geometry / stage4` 里的接触判定标准；
2. 不把生成好的 shape 事后在单胞里手动平移；
3. 不继续平均投入 `asym / neck / bilobe` 三类；
4. 不为了追求更多样本量而继续放大低质量候选池。

## 为什么现在只做 bilobe

基于前面两轮证据：

1. hand-made archetype pilot 里，`bilobe` 最明确地把强覆盖推到高 weak band，且 mode-shape 最像新带边机制；
2. snake-based archetype pilot 里，唯一明确跑出的 strong 正例也是 `bilobe`；
3. `asym` 和 `neck` 在当前 snake 分布里还没有形成稳定 target-band 正信号。

所以当前最合理的策略是：

**先把 `bilobe` 做稳，再讨论是否回头继续扩 `asym / neck`。**

## 这版所谓 contact-aware，指的是什么

这里的 `contact-aware` 不是“改接触规则”，而是：

1. 结合现有 snake pilot 的真实 stage4 反馈；
2. 优先保留那些在几何尺度、紧凑度、双叶分布、局部脆弱性上更像“可通过老规则”的 bilobe；
3. 提前拒绝那些虽然形态上像 bilobe，但高概率会：
   - `no_contact_with_fourier_boundary`
   - `geometry_has_tiny_fragments`

也就是说，这是一层**候选入场筛选**，不是一层**物理规则修改**。

## 当前预筛逻辑

这一版先使用现有 snake pilot 目录中的 contour 与 stage4 结果，构建一版 `bilobe-only shortlist`。

核心思路：

1. 只保留 `priority_archetype = bilobe` 的 contour；
2. 读取已有 snake target-band pilot 的真实反馈：
   - `any_contact_valid`
   - `any_solve_success`
   - `best_target_gap_cover_ratio`
3. 按下列指标构建 contact-aware score：
   - `bilobe_candidate_score`
   - 面积偏好
   - 紧凑度偏好
   - 宽高比偏好
   - 最小尺寸偏好
   - 真实 contact/solve/cover 历史加权
4. 对下列候选设置 reject：
   - 过小尺寸
   - 极端扁长
   - 紧凑度过低
   - neck 过深、明显脆弱

## 这条线真正想回答的问题

这一版不是为了直接给论文新增主结论，而是要回答：

1. 如果我们只追 `bilobe`，并且加入 contact-aware 预筛，下一轮候选质量会不会更高？
2. 能不能在不改老规则的前提下，提高 `contact_valid` 比例？
3. `bilobe` 是否值得进入更正式的 snake-based 第二轮扩展？

## 输出物

这一版会生成：

1. `bilobe` 候选总表；
2. `bilobe` contact-aware shortlist；
3. `bilobe` whitelist JSON；
4. summary JSON；
5. 后续接 stage4 的代表 shape 清单。

## 判断标准

这一版成功不看“样本更多”，而看：

1. shortlist 的 shape 是否明显比原 snake pilot 更少出现 `no_contact_with_fourier_boundary`；
2. shortlist 是否继续保留已经跑出正信号的 `bilobe` 家族；
3. 后续小批量 stage4 验证时，`contact_valid` 比例是否明显高于当前 snake pilot。

## 当前建议

这条线优先作为：

**`bilobe-only contact-aware snake pilot`**

而不是：

**`all-archetype snake expansion v2`**

等 `bilobe` 这条线确认有效后，再决定是否把同样思路推广到 `asym / neck`。
