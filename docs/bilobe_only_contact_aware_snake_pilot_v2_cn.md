# bilobe_only_contact_aware_snake_pilot_v2

## 目标

在 `v1` 的基础上，补齐两项关键基础设施：

1. **冻结 shortlisted contour**
2. **把 prefilter 从排序器升级成更强的 reject + 更保守 shortlist**

这一版依然**不修改主线老接触规则**，只改：

- 候选如何进入 shortlist
- shortlist 如何冻结成独立 shape snapshot

## 为什么要做 v2

`v1` 暴露了两个问题：

1. shortlist 对坏候选仍然过于宽松；
2. 同名 `shape_id` 在后续不同 run 中可能已经不是同一个 contour，导致比较污染。

因此 `v2` 的核心不再是“多跑一点”，而是先把 **候选稳定性** 和 **可比性** 补起来。

## v2 的变化

### 1. 冻结 contour snapshot

对最终 shortlist 中的每个 shape：

- 将 contour CSV 复制到独立目录；
- 生成固定 whitelist；
- 后续 target-band stage4 只读取这份冻结目录。

这样即使上游 snake contour 继续变化，`v2` 选中的代表 shape 也不会漂移。

### 2. 更强 reject

相比 `v1`，`v2` 更强调：

- 历史上没有任何 `contact_valid` 且没有任何 target-band cover 的 shape 直接重罚；
- 细长、过小、松散、脆弱 neck 的形状更积极 reject；
- shortlist 缩小为更保守的 `4-6` 个 shape。

### 3. 优先保留“已知能活”的 bilobe

`v2` 明确优先保留：

- 在旧 snake pilot 中出现过 `contact_valid = 1`
- 或出现过正 target-band cover

的 bilobe 候选。

## 这版想回答的问题

1. 在不改老规则的前提下，冻结后的 bilobe shortlist 能不能更稳定复现？
2. 更强 reject 后，下一轮 stage4 的 `contact_valid` 比例能否高于 `v1`？
3. 最值得继续推进的 bilobe 是否真的只剩少数几个核心候选？

## 输出物

这一版会生成：

1. `bilobe_contact_aware_catalog_v2.csv`
2. `bilobe_contact_aware_shortlist_v2.csv`
3. `bilobe_contact_aware_whitelist_v2.json`
4. `frozen_shape_contours/`
5. `bilobe_contact_aware_summary_v2.json`

## 判断标准

如果 `v2` 之后：

- shortlist 显著更小、更稳；
- 冻结 contour 后不再出现“同名 shape 实际不同”的问题；
- 后续 stage4 的 `contact_valid` 比例高于 `v1`；

那这条 bilobe-only snake 路线就值得继续。
