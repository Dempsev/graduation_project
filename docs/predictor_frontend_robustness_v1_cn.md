# predictor 前端稳健性分析（中文版）

## 1. 这一步要回答什么

当前主线里，predictor 的定位已经比较清楚：

- 它不是最终物理裁判
- 它的最佳角色是 target-band shortlist engine

在这个定位下，真正需要回答的不是“它是不是完美模型”，而是：

1. 阈值小改时，shortlist 会不会大变？
2. top20 排名在不同评估视角下还有没有连续性？
3. 排名在小扰动下是完全乱掉，还是仍保留一定核心结构？

所以这一步的目标，是评估 predictor **前端稳健性**，而不是重新评估整体模型精度。

---

## 2. 本次分析包含哪两层

### 2.1 Threshold sensitivity

使用 family-CV 的 RF 分类器概率 `y_prob`，在每个 weak band 上分别取：

- `threshold = 0.3`
- `threshold = 0.4`
- `threshold = 0.5`
- `threshold = 0.6`
- `threshold = 0.7`

然后在每个阈值下：

- 先保留 `y_prob >= threshold` 的候选
- 再从中按 `y_prob` 取 top20 shortlist

看：

- shortlist 质量
- eligible pool 大小
- 不同阈值之间的 top20 重叠度

### 2.2 Ranking stability

这层分成两个小问题：

1. `family-CV top20` 和 `leave-one-band top20` 之间的连续性
2. `family-CV top20` 在小 score 扰动下是否稳定

第二个问题中，我对 `y_prob` 加了一个很小的高斯扰动：

- `sigma = 0.02`
- 重复 `500` 次

然后看：

- design-level Jaccard
- family-level Jaccard
- 有多少 top20 里的 design / family 在超过 50% 的扰动下还能保留下来

---

## 3. 数据与输出位置

分析脚本：

- [analyze_predictor_frontend_robustness_v1.py](/d:/graduation_project/coad/prediction_targetband_param_v1/tools/analyze_predictor_frontend_robustness_v1.py)

输出目录：

- [predictor_frontend_robustness_v1](/d:/graduation_project/coad/data/analysis/predictor_frontend_robustness_v1)

关键文件：

- [threshold_sensitivity_summary_v1.csv](/d:/graduation_project/coad/data/analysis/predictor_frontend_robustness_v1/threshold_sensitivity_summary_v1.csv)
- [threshold_pairwise_stability_v1.csv](/d:/graduation_project/coad/data/analysis/predictor_frontend_robustness_v1/threshold_pairwise_stability_v1.csv)
- [ranking_cross_split_stability_v1.csv](/d:/graduation_project/coad/data/analysis/predictor_frontend_robustness_v1/ranking_cross_split_stability_v1.csv)
- [ranking_perturbation_stability_v1.csv](/d:/graduation_project/coad/data/analysis/predictor_frontend_robustness_v1/ranking_perturbation_stability_v1.csv)
- [predictor_frontend_robustness_info_v1.json](/d:/graduation_project/coad/data/analysis/predictor_frontend_robustness_v1/predictor_frontend_robustness_info_v1.json)

---

## 4. 最重要的总体结论

这一步给出的总体结论可以概括成一句话：

**当前 predictor 前端在阈值层面是稳定的，但在跨 split 和 design-level 排名层面只有“中等稳健性”；family-level continuity 明显强于 exact-design continuity。**

这个结论其实很符合我们当前对主线的定位：

- 可以当 shortlist engine
- 不能被夸成完全稳定、完全可替代真实搜索的最终排序器

---

## 5. Threshold sensitivity：阈值层面其实很稳

### 5.1 `band180_220`

从阈值 `0.3` 一直到 `0.7`：

- top20 shortlist 完全不变
- design Jaccard 全部 `1.0`
- family Jaccard 全部 `1.0`
- shortlist 质量也完全不变

同时，eligible pool 虽然从 `737` 缩到 `592`，  
但 top20 本身没有受到影响。

这说明：

**对于 `180-220`，前端 shortlist 对 threshold 变化几乎不敏感。**

### 5.2 `band220_260`

这里结果也一样：

- `0.3 -> 0.7` 所有阈值下，top20 完全不变
- design/family Jaccard 也都是 `1.0`

这说明：

**在 `220-260` 这个 weak band 上，当前 shortlist 也已经有很强的 threshold robustness。**

### 5.3 `band240_280`

这里仍然很稳：

- `0.3 -> 0.7` 的 top20 也完全一致
- design/family Jaccard 同样全是 `1.0`

这说明：

**最难的 `240-280` 上，shortlist 至少对 threshold 不敏感。**

### 5.4 `band200_240`

这个 band 略有变化，但变化也不大：

- `0.3` 时 shortlist 有 `8` 个
- `0.4` 到 `0.7` 时 shortlist 变成 `7` 个
- `0.3` 和更高阈值相比：
  - design Jaccard `0.875`
  - family Jaccard `0.833`
- `0.4` 到 `0.7` 之间则完全一致

这说明：

**`200-240` 的 threshold sensitivity 也不大，只是当前高置信候选本身数量偏少，所以阈值一提，少掉的是边缘第 8 个样本。**

### 5.5 这一层的结论

这部分可以明确写成：

**在 thesis 关心的 weak bands 上，当前 predictor front-end 对合理范围内的 threshold 扰动总体稳定。**

也就是说：

- 不是阈值微调一下，top20 就完全换人
- 当前 shortlist 的基本结构是稳的

这对后面把 predictor 用作 inverse-design front-end 非常重要。

---

## 6. Ranking stability：跨 split 时 exact design 不够稳，但 family 还有连续性

### 6.1 family-CV vs leave-one-band

这里最能说明当前 predictor 的边界。

#### `band180_220`

- design overlap：`3`
- design Jaccard：`0.081`
- family overlap：`4`
- family Jaccard：`0.400`

#### `band200_240`

- design overlap：`0`
- design Jaccard：`0.000`
- family overlap：`5`
- family Jaccard：`0.385`

#### `band220_260`

- design overlap：`2`
- design Jaccard：`0.053`
- family overlap：`3`
- family Jaccard：`0.150`

#### `band240_280`

- design overlap：`0`
- design Jaccard：`0.000`
- family overlap：`4`
- family Jaccard：`0.167`

### 6.2 怎么理解

这个结果说明：

**跨到 leave-one-band 以后，exact top20 design 本身并不稳定。**

也就是说，我们现在还不能说：

- 换一个 band，模型仍会几乎挑出同一批具体设计

但也不能把结果解读成“完全没连续性”，因为：

- family overlap 仍然存在
- 某些 band 上 family-level continuity 还不低

所以更准确的理解是：

**当前 predictor 在跨 band 时保留的是“family-level 倾向”，而不是“精确到 design-level 的强稳定排序”。**

这和我们前面 freezing 的主张边界是一致的：

- catalog 内可迁移
- 但不是强未见-band exact ranking model

---

## 7. 小扰动稳定性：比跨 split 稳，但也不是“铁板一块”

### 7.1 `band200_240` 最稳

在 `sigma = 0.02` 的小扰动下：

- mean design Jaccard：`0.484`
- mean family Jaccard：`0.715`
- 超过 50% 扰动下仍保留的核心 design：`12`
- 核心 family：`9`

这是四个 band 里最稳的。

说明：

**当前 `200-240` 的 shortlist 在小 score 扰动下，已经形成了一个相对稳定的核心集合。**

### 7.2 `band180_220` 和 `band240_280` 属于中等稳健

`band180_220`：

- mean design Jaccard：`0.247`
- mean family Jaccard：`0.365`

`band240_280`：

- mean design Jaccard：`0.234`
- mean family Jaccard：`0.402`

说明：

- exact design 会换
- 但 family-level 还保留了一部分连续性

### 7.3 `band220_260` 最敏感

- mean design Jaccard：`0.147`
- mean family Jaccard：`0.305`
- core design：`5`
- core family：`6`

说明：

**`220-260` 的前端排序对小 score 扰动最敏感。**

这个结果也很合理，因为这个 band 既不算最成熟，也不像 `200-240` 那样已经被非常明确地打通。

### 7.4 这一层的结论

这一步表明：

**当前 predictor front-end 的稳定性是“有核心、但不是完全刚性”的。**

也就是说：

- 它不是一碰就散
- 但也不是微扰后 top20 纹丝不动

这恰恰符合 shortlist engine 的预期定位：

- 给方向
- 保留一批核心候选
- 不承担完全精确、完全刚性的 design-level ranking 承诺

---

## 8. 这一步对主线意味着什么

### 8.1 能支持的结论

这一步足够支持下面这句：

**当前 predictor front-end 具有可接受的 operational robustness：阈值层面稳定，排名层面存在可识别核心，能够支撑其作为 inverse-design shortlist engine 的角色。**

### 8.2 不能过度写的结论

它还不能支持：

**当前 predictor 已经具备强未见-band exact design ranking robustness。**

因为从：

- family-CV vs leave-one-band
- exact design overlap

来看，这一层显然还不够强。

所以最准确的说法还是：

**它在 family-level 和 shortlist-level 上可用，但在跨 band exact-design ranking 上仍有明显边界。**

---

## 9. 推荐写法

如果后面要把这部分写进论文或汇报，我建议直接用下面这句：

> predictor 前端稳健性分析表明，在 thesis 关心的 weak-band catalog 上，shortlist 对合理范围内的 classification threshold 扰动总体稳定；同时，top20 排名在小 score 扰动下能够保留一批核心 design/family，说明其具备作为 shortlist engine 的操作稳健性。但在 family-CV 与 leave-one-band 的跨 split 对照下，exact design-level 排名连续性仍然有限，因而当前 predictor 更适合被界定为 catalog 内条件提案器，而非强未见-band 的最终排序器。

更口语一点可以说：

> 现在这个 predictor 前端已经稳到可以当 shortlist engine 用了，阈值怎么小调都不会把名单打乱；但如果要求它跨 band 以后还精确到“同一批具体 design”，那就还没到那个程度。

---

## 10. 当前结论

这一步最终让我们能更稳地说：

- predictor 前端在操作上是稳的
- shortlist 不是靠脆弱阈值堆出来的
- 当前最自然的 robustness 结论是：

**threshold-stable, shortlist-usable, family-aware, but not yet exact-design-stable across held-out bands**

这正好和我们已经冻结的 thesis 主线一致。  
下一步就可以更有把握地进入：

**canonical inverse-design cases 的 local neighborhood robustness**

也就是去回答：

> 我们现在找到的那些最优解，周围到底是“小盆地”，还是“尖点”。  
