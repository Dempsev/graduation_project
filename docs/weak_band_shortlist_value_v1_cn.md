# 弱 band shortlist 价值小实验（中文版）

## 1. 这个实验想回答什么

前面的 readiness 报告已经说明：

- predictor 在 family-CV 下是可用的
- top-k shortlist 在整体上有提升

但如果要让这个结论更直观，仍然还差一个问题：

> 对弱 band 来说，predictor 排出来的前 20 个候选，到底是不是比随便选的更好？

这个问题如果只用平均指标回答，会不够直观。  
所以这里专门补了一个很小、但非常直接的实验。

---

## 2. 实验设计

在每个 weak band 上，我们都固定从**同一个 band-specific 候选池**里，比较三组 `top20`：

1. `predictor_top20`
   - 用当前主分类器 RF 的 `y_prob` 排名前 20
   - 这一步故意只看 classifier probability
   - 目的是隔离出 predictor 作为 **shortlist engine** 的前端价值

2. `generic_unconditional_top20`
   - 不看当前 target band
   - 只按该 design 在 tracked weak-band catalog 上的平均真实 cover 做 band-unconditional 排序
   - 这代表一种“只挑总体看起来强的候选”的 generic 候选策略

3. `random20_mean`
   - 从同一个 band-specific pool 随机抽 20 个
   - 重复 `500` 次，取平均

也就是说，我们比较的是：

- target-band 条件 shortlist
- 不带条件的 generic shortlist
- 随机 shortlist

---

## 3. 数据与输出位置

分析脚本：

- [analyze_weak_band_shortlist_value_v1.py](/d:/graduation_project/coad/prediction_targetband_param_v1/tools/analyze_weak_band_shortlist_value_v1.py)

输出目录：

- [weak_band_shortlist_value_v1](/d:/graduation_project/coad/data/analysis/weak_band_shortlist_value_v1)

关键文件：

- [weak_band_shortlist_summary_v1.csv](/d:/graduation_project/coad/data/analysis/weak_band_shortlist_value_v1/weak_band_shortlist_summary_v1.csv)
- [weak_band_shortlist_candidates_v1.csv](/d:/graduation_project/coad/data/analysis/weak_band_shortlist_value_v1/weak_band_shortlist_candidates_v1.csv)
- [weak_band_random20_distribution_v1.csv](/d:/graduation_project/coad/data/analysis/weak_band_shortlist_value_v1/weak_band_random20_distribution_v1.csv)
- [weak_band_shortlist_info_v1.json](/d:/graduation_project/coad/data/analysis/weak_band_shortlist_value_v1/weak_band_shortlist_info_v1.json)

本次固定 band：

- `band180_220`
- `band200_240`
- `band220_260`
- `band240_280`

---

## 4. 最重要的总体结论

这次小实验给出的结论是：

**predictor shortlist 在弱 band 上确实具有直接价值，因为它稳定优于 random20；但它并不是在每个 band 上都绝对优于 generic unconditional shortlist。**

这句话需要拆成两半理解：

### 4.1 结论一：predictor 不是“没用的排序器”

在所有 4 个目标 band 上，`predictor_top20` 相对 `random20_mean` 都有正提升：

- 平均 true cover 更高
- 平均 true overlap 更高
- 在部分 band 上，open hit 数也明显更高

所以 predictor 的 shortlist 价值是存在的，而且不是随机波动。

### 4.2 结论二：predictor 也不是“任何时候都最强”

和 `generic_unconditional_top20` 相比：

- 有些 band 上 predictor 更好
- 有些 band 上两者接近
- 也有 band 上 generic unconditional 反而更强

这个结果其实很有价值，因为它说明：

- 当前 predictor 的最佳角色是 **target-band shortlist engine**
- 但它还不应该被夸成“已经在所有 weak band 上全面统治候选排序”

这个结论比“全面赢”更真实，也更适合写进 thesis。

---

## 5. 分 band 结果

### 5.1 `band180_220`

`predictor_top20`：

- mean true cover：`0.322`
- mean true overlap：`12.89 Hz`
- open hit：`20`
- strong hit：`3`

`random20_mean`：

- mean true cover：`0.129`
- mean true overlap：`5.16 Hz`
- open hit：`15.89`
- strong hit：`0.146`

所以 predictor 相对 random 的提升很明显：

- cover `+0.193`
- overlap `+7.73 Hz`
- open hit `+4.11`
- strong hit `+2.86`

但这里 `generic_unconditional_top20` 更强：

- mean true cover：`0.457`
- strong hit：`6`

这说明：

**在较成熟的 `180-220` 上，generic unconditional 候选本身就已经很强；predictor 仍然优于随机，但还不是这一个 band 上最强的 shortlist 方式。**

---

### 5.2 `band200_240`

`predictor_top20`：

- mean true cover：`0.0143`
- mean true overlap：`0.573 Hz`
- open hit：`6`

`random20_mean`：

- mean true cover：`0.00042`
- mean true overlap：`0.0167 Hz`
- open hit：`0.174`

提升非常明显：

- cover `+0.0139`
- overlap `+0.557 Hz`
- open hit `+5.826`

这里 predictor 和 generic unconditional 基本持平。

这说明：

**在 `200-240` 这种更弱、更稀的 band 上，predictor shortlist 至少已经显著优于随机；它和 generic unconditional 接近，说明当前这部分候选知识还没有完全只被条件模型独占。**

---

### 5.3 `band220_260`

`predictor_top20`：

- mean true cover：`0.0260`
- mean true overlap：`1.040 Hz`
- open hit：`20`

`random20_mean`：

- mean true cover：`0.0155`
- mean true overlap：`0.618 Hz`
- open hit：`16.69`

提升为：

- cover `+0.0105`
- overlap `+0.422 Hz`
- open hit `+3.308`

同时，这里 predictor 也明显优于 generic unconditional：

- generic mean true cover 只有 `0.0159`
- open hit 只有 `10`

这说明：

**在 `220-260` 这个 band 上，predictor shortlist 的 target-band 条件价值已经比较明显。**

---

### 5.4 `band240_280`

`predictor_top20`：

- mean true cover：`0.0310`
- mean true overlap：`1.239 Hz`
- open hit：`20`

`random20_mean`：

- mean true cover：`0.0176`
- mean true overlap：`0.702 Hz`
- open hit：`17.84`

提升是：

- cover `+0.0134`
- overlap `+0.536 Hz`
- open hit `+2.158`

但这里 generic unconditional 更强一点：

- mean true cover：`0.0371`
- mean true overlap：`1.482 Hz`

所以 `240-280` 的结论和 `180-220` 有点像：

- predictor 明显优于随机
- 但 generic unconditional 仍然有竞争力

这说明这个最难 band 上，当前 predictor 的条件排序优势还没有完全“碾压式”建立起来。

---

## 6. 这一步真正说明了什么

### 6.1 能明确说明的

这一步已经足够支持下面这句话：

**predictor 不是只有离线指标好看，它作为 shortlist engine 在 weak band 上具有真实的排序价值。**

因为它相对 random20 的提升是稳定存在的，而且不止体现在一个 band 上。

### 6.2 不能过度说的

这一步还不能支持下面这种说法：

**“predictor shortlist 在所有 weak band 上都已经明显优于一切 generic baseline。”**

因为从 `180-220` 和 `240-280` 来看，generic unconditional top20 仍然可能更强。

所以更准确的表述应该是：

**predictor 已经能稳定提高 weak-band shortlist 质量，但它与 generic unconditional prior 之间仍然存在 band-dependent 竞争关系。**

---

## 7. 这对 thesis 主线意味着什么

这个小实验其实正好把 predictor 的角色界定得更清楚了。

### 7.1 Predictor 的作用已经足够成立

它已经足够被表述成：

- 目标 band 条件 shortlist engine
- inverse design 的搜索前端

因为它明显优于随机。

### 7.2 但 predictor 还不应该被写成“单独最强的最终排序器”

generic unconditional baseline 在部分 band 上仍然有竞争力，说明：

- 当前 predictor 的能力是真实存在的
- 但还没有强到可以完全替代其他先验

这和我们前面主线的判断是一致的：

- predictor 给方向
- shape-aware 改入口
- real search 做 refinement 和弱 band 攻坚

它不是单独完成一切的模块。

---

## 8. 推荐写法

后面如果要把这个结果写进论文或汇报，我建议用下面这句：

> 弱 band shortlist 实验表明，当前 RF 条件预测器在 `180-220 / 200-240 / 220-260 / 240-280` 等目标 band 上均能稳定优于随机候选抽样，说明其已具备作为 inverse-design shortlist engine 的直接价值；但其相对 generic unconditional 候选的优势具有 band 依赖性，因而更适合作为 guided search front-end，而非单独的最终设计裁判。

如果想更口语一点，可以说：

> 现在 predictor 已经不是“看起来有点准”，而是真的能把 shortlist 质量提上去；只是它还不是每个 band 都绝对最强，所以最合理的位置仍然是搜索前端，而不是最终裁判。

---

## 9. 当前结论

这一步让我们能更稳地回答：

> predictor 到底有没有用？

答案是：

**有，而且是直接有用。**

但更准确地说是：

- 它已经足以作为 weak-band shortlist engine
- 明显优于随机基线
- 但与 generic unconditional baseline 之间仍然存在 band-dependent 的竞争关系

这恰好支持我们现在已经冻结的主线定位：

**predictor 负责给方向，shape-aware 负责选入口，real search 负责把物理解打开。**
