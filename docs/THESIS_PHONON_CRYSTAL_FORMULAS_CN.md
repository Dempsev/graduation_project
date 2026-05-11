# 声子晶体物理与力学公式补充建议

本文的算法部分是目标频带数据集构建、条件预测与候选优化，但这些结果都依赖前端的 COMSOL 频散求解。因此论文中建议补一个较短的物理基础小节，说明“频带、带隙、目标频带覆盖率”不是经验标签，而是由弹性波本征值问题与后处理指标得到。

## 建议放置位置

推荐在第 3 章开头新增一节：

**3.1 声子晶体频带计算的物理基础**

然后把现有的“参数化结构表示与结构族定义”等内容顺延为 3.2。理由是第 3 章通常承担“数据集和物理真值来源”的说明，把控制方程、Bloch 周期边界和带隙定义放在这里最自然。

如果不想大幅调整章节编号，也可以放在第 2 章理论基础中，标题可写为：

**2.x 弹性波频散关系与声子晶体带隙定义**

但本文后续会马上使用 `target_gap_cover_ratio`、`target_gap_is_open`、`gap34_gain_Hz` 等字段，所以更推荐放在第 3 章数据集构建之前。

第 4 章只需保留标签和预测任务定义，第 6 章再补验证增益和应变能/应力解释公式即可。

## 可直接写入第 3 章的公式与文字

二维周期声子晶体可视为材料参数和几何结构在空间中周期变化的弹性介质。设位移场为 \(\mathbf{u}(\mathbf{x},t)\)，密度为 \(\rho(\mathbf{x})\)，应力张量为 \(\boldsymbol{\sigma}\)。忽略体力时，线弹性动力学平衡方程为

\[
\nabla\cdot\boldsymbol{\sigma}(\mathbf{x},t)=\rho(\mathbf{x})\ddot{\mathbf{u}}(\mathbf{x},t).
\]

小变形条件下，应变张量定义为

\[
\boldsymbol{\varepsilon}=\frac{1}{2}\left(\nabla\mathbf{u}+\nabla\mathbf{u}^{T}\right).
\]

各向同性线弹性材料的本构关系可写为

\[
\boldsymbol{\sigma}=\mathbb{C}:\boldsymbol{\varepsilon}
=\lambda\,\mathrm{tr}(\boldsymbol{\varepsilon})\mathbf{I}+2\mu\boldsymbol{\varepsilon},
\]

其中 Lamé 常数与弹性模量 \(E\)、泊松比 \(\nu\) 的关系为

\[
\lambda=\frac{E\nu}{(1+\nu)(1-2\nu)},\qquad
\mu=\frac{E}{2(1+\nu)}.
\]

对自由振动问题，令

\[
\mathbf{u}(\mathbf{x},t)=\hat{\mathbf{u}}(\mathbf{x})e^{i\omega t},
\]

可得到频域形式的弹性波本征值问题：

\[
\nabla\cdot\boldsymbol{\sigma}(\hat{\mathbf{u}})+\rho\omega^{2}\hat{\mathbf{u}}=0.
\]

有限元离散后，可写为含波矢 \(\mathbf{k}\) 的广义本征值问题：

\[
\mathbf{K}(\mathbf{k})\boldsymbol{\phi}
=\omega^{2}\mathbf{M}\boldsymbol{\phi},
\]

其中 \(\mathbf{K}(\mathbf{k})\) 为引入周期边界相位后的刚度矩阵，\(\mathbf{M}\) 为质量矩阵，\(\boldsymbol{\phi}\) 为模态向量。

对于周期结构，Bloch-Floquet 条件为

\[
\mathbf{u}(\mathbf{x}+\mathbf{R})
=\mathbf{u}(\mathbf{x})e^{i\mathbf{k}\cdot\mathbf{R}},
\]

其中 \(\mathbf{R}\) 为晶格平移矢量，\(\mathbf{k}\) 为第一布里渊区中的波矢。本文的 COMSOL 扫描脚本通过归一化参数路径对波矢进行遍历，并导出不同分支的本征频率。频散关系可表示为

\[
\omega_n=\omega_n(\mathbf{k}),\qquad
f_n(\mathbf{k})=\frac{\omega_n(\mathbf{k})}{2\pi},
\]

其中 \(n\) 表示频散分支编号。

对于相邻的第 \(n\) 和第 \(n+1\) 条频散分支，若低分支在扫描路径上的最大频率小于高分支的最小频率，则存在带隙：

\[
f_n^{\max}=\max_{\mathbf{k}} f_n(\mathbf{k}),\qquad
f_{n+1}^{\min}=\min_{\mathbf{k}} f_{n+1}(\mathbf{k}),
\]

\[
g_n=\max\left(0,\ f_{n+1}^{\min}-f_n^{\max}\right).
\]

相对带隙宽度可定义为

\[
g_n^{rel}=
\frac{g_n}{\left(f_{n+1}^{\min}+f_n^{\max}\right)/2}.
\]

这一带隙提取方式与仓库中 `stage1/extract_gap_metrics_from_tbl1.m` 和 `stage2/extract_stage2_gap_metrics_from_tbl1.m` 的处理一致：脚本对相邻分支计算 `lowerEdge = max(lower)`、`upperEdge = min(upper)`，并以 `upperEdge - lowerEdge > 0` 作为有效带隙条件。

## 目标频带标签定义

本文不是只追求任意带隙，而是面向指定目标频带进行条件预测。设目标频带为

\[
B=[f_L,f_U],
\]

某一有效带隙区间为

\[
G=[f_n^{\max},f_{n+1}^{\min}].
\]

二者的重叠宽度定义为

\[
o(B,G)=
\max\left(0,\ \min(f_U,f_{n+1}^{\min})-\max(f_L,f_n^{\max})\right).
\]

目标频带覆盖率定义为

\[
c(B,G)=\frac{o(B,G)}{f_U-f_L}.
\]

因此，目标频带是否打开可写为

\[
y_{open}=\mathbb{I}\left[c(B,G)>0\right].
\]

仓库中 `prediction_targetband_param_v1/tools/analyze_snake_based_archetype_targetband_pilot_v1.py` 对应实现为：

```python
overlap = max(0.0, min(upper_edge, band_high) - max(lower_edge, band_low))
target_gap_cover_ratio = best_overlap / (band_high - band_low)
```

第 4 章在介绍条件预测模型时，可以把输入和输出写成：

\[
p_{open}=C(\mathbf{x},s,B),\qquad
\hat{c}=R(\mathbf{x},s,B),
\]

其中 \(\mathbf{x}\) 表示参数化几何变量，\(s\) 表示结构族或形状类别，\(B\) 表示目标频带，\(C\) 输出目标频带打开概率，\(R\) 输出目标频带覆盖率预测值。

## 候选排序与优化阶段可用公式

候选排序不是新的物理定律，而是工程上的多指标优先级函数。当前项目中 `optimization/seed_ranking/run_targetband_seed_scoring_v1.py` 使用的排序分数可概括为

\[
S=0.30p_{contact}+0.45p_{open}+0.20\hat{c}+0.05s_{prior},
\]

其中 \(p_{contact}\) 表示接触有效概率，\(p_{open}\) 表示目标频带打开概率，\(\hat{c}\) 表示预测覆盖率，\(s_{prior}\) 表示历史或先验增益项。论文中应说明：该权重是当前工程流程中的候选筛选策略，用于减少真实 COMSOL 验证成本，不应表述为普适最优权重。

第 6 章验证部分可定义真实验证增益：

\[
\Delta g_{34}=g_{34}^{val}-g_{34}^{ref}.
\]

对应到仓库字段就是 `gap34_gain_Hz`。当 \(\Delta g_{34}>0\) 时，说明候选相对于参考结构在第 3-4 分支带隙宽度上取得正增益。

## 模态与力学解释可选公式

如果第 6 章需要解释模态形态、应变集中或局部结构变形机理，可以补充应变能密度：

\[
w_s=\frac{1}{2}\boldsymbol{\sigma}:\boldsymbol{\varepsilon}.
\]

若展示二维平面问题中的等效应力云图，可使用 von Mises 应力表达式：

\[
\sigma_{vm}
=\sqrt{\sigma_x^2-\sigma_x\sigma_y+\sigma_y^2+3\tau_{xy}^{2}}.
\]

这部分适合放在第 6 章“真实验证结果与物理机理分析”中，配合模态位移图、应变能云图或关键几何参数变化图使用。不要把它放在第 4 章机器学习模型部分，否则会打断预测模型的叙事。

## 推荐论文落点

1. 第 3 章新增“3.1 声子晶体频带计算的物理基础”：放控制方程、应变-应力关系、Bloch 条件、频散关系、带隙定义。
2. 第 3 章数据集构建小节：放目标频带 \(B\)、重叠宽度 \(o(B,G)\)、覆盖率 \(c(B,G)\)、打开标签 \(y_{open}\)。
3. 第 4 章模型方法：只保留 \(p_{open}=C(\mathbf{x},s,B)\)、\(\hat{c}=R(\mathbf{x},s,B)\)，说明分类器和回归器的任务。
4. 第 6 章验证分析：放 \(\Delta g_{34}\)、应变能密度、von Mises 应力，用来解释真实验证和物理机理。

## 建议配图

建议在新增第 3 章小节后放一张“物理真值生成流程图”：参数化结构 \(\rightarrow\) Bloch 周期边界 \(\rightarrow\) COMSOL 本征频率求解 \(\rightarrow\) 频散曲线 \(\rightarrow\) 相邻分支带隙 \(\rightarrow\) 目标频带覆盖率标签。这样能把公式和项目数据字段连接起来，避免公式显得孤立。
