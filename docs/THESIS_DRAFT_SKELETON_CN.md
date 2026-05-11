# 毕业论文正文初稿骨架（中文）

## 使用说明

这份文档不是最终论文，而是按照当前仓库冻结后的 thesis mainline 整理出的“正文初稿骨架”。它的作用是帮你把“章节标题”推进成“可以直接改写的段落”。你后续写作时，建议采用下面的使用方式：

1. 保留每节的基本逻辑与段落顺序。
2. 把文中的 `[待补文献]`、`[待补数据]`、`[待补图表]`、`[待补结果]` 替换成真实内容。
3. 如果学校模板要求更正式的风格，可以在不改变逻辑的前提下，对语气进行学术化改写。
4. 如果某一节篇幅过长，可以把本稿中的某些段落改写后移入附录或结果补充材料。

当前默认论文主线为：

> 面向 thesis band catalog 的 target-band 条件预测与预测驱动逆向设计流程。

建议始终坚持以下角色划分：

- predictor 负责 shortlist generation
- shape-aware candidate construction 负责提升候选池质量
- real COMSOL validation 负责给出最终物理确认

---

# 第一章 绪论

## 1.1 研究背景与意义

声子晶体与机械超结构因其能够调控弹性波传播、形成频带禁带以及实现振动与噪声控制，近年来在工程减振、隔声降噪和波传播功能器件等方向受到广泛关注。[待补文献] 对于此类结构而言，带隙位置与宽度通常对结构几何参数、材料配置以及结构族形态高度敏感，因此如何在复杂设计空间中高效地获得满足性能要求的结构方案，始终是该领域的核心问题之一。

传统研究通常采用“给定结构参数，计算其频带特性”的正向分析路径。这一路径在物理机制研究与参数规律总结方面具有重要价值，但当设计目标从“分析某个结构的带隙”转变为“给定一个目标频带，反向寻找可用结构”时，其效率和适用性都会明显下降。其主要原因在于：一方面，参数化结构通常具有较高维度，设计空间大；另一方面，不同 shape family 之间的性能分布存在显著差异，仅靠人工经验或密集扫描难以稳定找到满足目标频带要求的候选方案。此外，真实物理验证往往依赖 MATLAB/COMSOL 等高成本求解流程，进一步限制了暴力搜索的可行性。

在这一背景下，机器学习方法为逆向设计问题提供了新的思路。相比完全依赖高成本物理求解的方式，数据驱动预测器可以在已有真值样本的基础上快速评估候选结构，从而为后续搜索提供方向感。然而，需要强调的是，在本研究中，预测器的角色并不是替代真实物理求解器，而是作为一个面向指定目标频带的 shortlist engine。换言之，机器学习模型的价值不在于直接给出最终可用结构，而在于从庞大的候选空间中优先筛出更值得进入真实验证与进一步精修的结构。

因此，围绕“给定目标频带，如何建立一条可解释、可复现、可验证的逆向设计主线”这一问题展开研究，不仅具有明确的学术意义，也具有较强的工程应用价值。对于毕业设计而言，这一问题还具有额外的重要性：相较于单纯追求某个模型指标的提升，更关键的是建立一条从物理真值生产、条件预测建模、候选结构筛选到真实物理验证的完整技术闭环。这正是本文工作的主要目标。

## 1.2 国内外研究现状

### 1.2.1 声子晶体带隙分析与结构设计研究现状

现有关于声子晶体与机械超结构的研究，大多从带隙形成机理、结构参数敏感性和优化设计三个方向展开。在带隙分析方面，研究者通常通过有限元仿真、Bloch 周期边界分析和参数扫描等方式，研究几何参数、材料对比和结构单胞形态对频带特性的影响。[待补文献] 在结构设计方面，已有工作尝试通过参数优化、启发式搜索以及拓扑优化等方法寻找具有较宽带隙或特定中心频率的结构方案。这些工作为理解结构性能关系提供了丰富经验，也为后续数据驱动设计奠定了基础。

然而，传统方法往往更适合“分析一个结构是否好”，而不擅长“给定目标频带后，快速找到可用结构”。尤其是在结构族较多、参数维度较高且真实物理验证成本较高的情况下，仅依赖参数扫描或单纯的优化算法，常常难以兼顾效率、解释性与实际可用性。

### 1.2.2 机器学习在超结构设计中的应用现状

随着数据驱动方法的发展，越来越多研究开始将机器学习模型引入到超结构和声子晶体设计中。例如，部分工作使用回归模型预测带隙宽度或中心频率，部分工作使用分类模型判断结构是否具有带隙，也有研究尝试通过代理模型、生成模型或强化学习方法辅助结构搜索。[待补文献] 这些方法的共同优点在于能够在已有样本基础上快速近似结构性能，从而降低高保真物理求解的调用频率。

尽管如此，现有工作仍然存在几个明显不足。第一，很多研究的任务定义仍是“无条件”的结构性能预测，即输入一个结构，输出其整体性能，而不是“给定一个目标频带，判断该结构对这一目标 band 是否有用”的条件预测。第二，很多研究在模型精度层面给出了较好的结果，但缺少与真实物理验证闭环相结合的完整流程。第三，部分方法在强 band 条件下表现较好，但对于弱 band 或困难 band 的推进作用不足。第四，现有文献中往往没有明确区分 predictor、candidate construction 和 real validation 三者的角色，导致叙事上容易把预测器误写成最终设计器。

### 1.2.3 现有工作的不足与本文切入点

综合来看，现有研究虽然为数据驱动设计提供了丰富方法，但仍缺少一条围绕“目标频带条件化设计”的系统主线。尤其是在毕设场景下，如果没有清晰的边界和完整的工程闭环，就很容易出现“模型能跑，但方法讲不清；结果看起来多，但主线并不稳定”的问题。

因此，本文的切入点并不是继续追求一个更复杂、更黑箱的模型，而是建立一条清晰的 workflow：先由真实物理真值支撑 target-band 数据基础，再构建面向目标频带的条件预测器，并通过 shape-aware candidate construction、prediction-guided shortlist、局部精修和最终的 MATLAB/COMSOL 真实验证，将整条逆向设计主线串联起来。本文的目标不是证明一个万能模型，而是建立一个在 thesis band catalog 范围内真实成立的 target-band inverse-design workflow。

## 1.3 本文研究问题

围绕上述背景与现状，本文重点回答以下三个研究问题。

第一，能否建立一个面向指定目标频带的条件预测器，使其在当前参数化结构族与 thesis band catalog 范围内具有实际可用的 shortlist 价值。这里的“可用”并不单纯指离线评价指标较高，而是指模型输出能够真实改善候选结构的排序质量，从而优先暴露更值得验证的结构。

第二，条件预测器能否真正驱动后续真实搜索与精修过程。对于逆向设计而言，单纯的分类精度或回归误差并不足以说明问题，更重要的是：预测器输出的高分候选是否能够在后续局部搜索和真实物理验证中表现出更高的成功率与更好的 target-band 特性。

第三，在 thesis band catalog 范围内，本文建立的 prediction-guided inverse-design 流程能否不仅在强 band 上有效，而且对弱 band 也具有实质推进作用。换言之，本文不仅关注“是否能找到一些成功案例”，还关注“这条主线是否真正拓展了弱频带条件下的可设计性边界”。

## 1.4 本文技术路线与总体框架

为回答上述研究问题，本文构建了一条由 truth layer、model layer 与 search layer 组成的三层技术路线。首先，在 truth layer 中，通过历史物理求解流程生成结构样本及其真实频带信息，并在必要时通过 stage4 validation 回补真实真值。其次，在 model layer 中，围绕 thesis band catalog 构建 target-band 参数化数据集，并分别训练条件分类器与条件回归器，用于评估结构在指定目标 band 上的开启概率和覆盖质量。最后，在 search layer 中，基于预测器输出对候选结构进行评分与排序，并结合 shape-aware candidate construction 与局部精修策略，形成预测驱动的逆向设计主线，最终通过 MATLAB/COMSOL 完成真实物理验证。

从实现上看，本文的技术路线并不是一个“单模型解决一切”的系统，而是一条强调边界清晰和角色分工的 workflow。其中，predictor 提供 shortlist generation，shape-aware front-end 提升候选池质量，local refinement 负责在局部设计空间中进一步改良候选结构，real validation 则负责给出最终物理确认。这样的组织方式，使得本文方法既能保持工程可执行性，又能在论文叙事中保持逻辑上的清晰与可信。

建议在本节中给出一张总体框架图，以直观呈现各模块之间的输入输出关系。[待补图 1-1] 图中应至少包含以下内容：物理真值生产、target-band 数据集构建、条件预测、候选评分与局部精修、stage4 真实验证以及结果汇总分析。

## 1.5 本文主要工作与创新点

本文围绕目标频带逆向设计问题，完成了以下几方面工作。

第一，构建了一个面向 thesis band catalog 的 target-band 条件预测框架，将“结构 + 指定目标频带”映射到“开启概率 + 覆盖质量”等与目标 band 直接相关的预测量。与传统无条件性能预测不同，该框架强调 band-conditioned prediction，使预测器具备面向指定 band 进行 shortlist generation 的能力。

第二，建立了 prediction-guided + shape-aware + real-search refinement 的逆向设计主线。本文并未将 shape 仅仅视为普通输入特征，而是将其提升为正式任务变量，引入 shape-aware candidate construction 以改善候选池质量，并通过局部 refinement 将预测高分候选进一步推进为真实物理可验证的设计。

第三，通过 predictor readiness、canonical inverse-design cases、baseline comparison、weak-band shortlist value 以及 stage4 real validation 等多层证据，证明了该主线不仅在离线指标上可用，而且能够在真实物理约束下得到可验证结果。尤其是在弱 band 条件下，本文主线表现出实质性的推进作用，而不仅是对强 band 的重复验证。

第四，围绕 thesis-facing mainline 对仓库进行了收口式重构，明确了 official thesis mainline 与 historical baselines 的边界，建立了 Python 与 MATLAB 之间的 manifest contract 及对应的 smoke checks，使整条主线具备更好的可解释性、可复现性与可维护性。这一部分虽然属于工程支持，但对毕业设计的可信度和完整性具有重要作用。

## 1.6 论文结构安排

全文共分为八章，各章内容安排如下。第一章为绪论，介绍研究背景、国内外研究现状、本文研究问题及总体技术路线。第二章给出问题定义、thesis band catalog 的边界、三层系统架构以及论文主线与历史基线的关系。第三章介绍物理真值生产流程、参数化结构表示和 target-band 数据基础。第四章重点讨论面向目标频带的条件预测方法及其 readiness。第五章介绍 prediction-guided inverse-design workflow 的具体实现，包括 shape-aware candidate construction、seed scoring、local refinement、manifest contract 与 real validation。第六章围绕 predictor readiness、canonical cases、baseline comparison、weak-band analysis 和 stage4 validation 等方面给出实验结果与分析。第七章讨论本文方法的成立范围、局限性与可扩展方向。第八章总结全文工作并展望未来研究方向。

---

# 第二章 问题定义与系统框架

## 2.1 目标频带逆向设计问题定义

本文研究的问题可以概括为：在给定参数化结构表示、固定材料配置与指定目标频带区间的条件下，寻找能够在该 target band 上表现出有效开启与较好覆盖质量，并最终通过真实物理验证的结构方案。与传统“固定结构、分析性能”的正向问题不同，本文面对的是“固定目标 band、反向寻找结构”的逆向问题，因此其任务目标、评价方式和方法组织方式都需要做相应调整。

从输入角度看，本文方法的输入主要包括三类信息：一是参数化结构几何表示，用于描述候选结构；二是目标频带区间，用于明确当前设计目标；三是固定的材料与物理求解配置，用于保证不同实验之间的可比性。从输出角度看，本文最终输出的不是单纯的预测分数，而是经过 prediction-guided shortlist、局部精修和真实物理验证之后得到的可用设计候选，以及与之对应的真实 stage4 结果。

从优化目标看，本文并不是简单追求某一个连续指标最大，而是在 target-band 条件下同时关注“是否开启”“覆盖质量如何”“是否满足真实物理可用性”等多个维度。因此，本文采用分类与回归相结合的方式来建模这一任务，并在后续 candidate ranking 中综合使用这些信息。与此同时，本文也明确承认其边界：当前方法成立于 thesis band catalog 与当前参数化结构族内，而非任意结构表示、任意材料体系和任意连续频带上的完全通用逆向设计。

## 2.2 Thesis Band Catalog 的定义

为避免在研究问题上无限扩张，本文采用 thesis band catalog 作为正式实验边界。所谓 thesis band catalog，是指在当前毕设阶段，根据已有真实真值分布、样本规模与实验预算所冻结的一组目标频带集合。这一集合并非任意选择，而是综合考虑了已有数据覆盖、结构族有效性以及真实验证可执行性之后得到的研究边界。

采用 thesis band catalog 有三个主要原因。首先，它保证了不同 band 上都能获得足够的训练与分析样本，从而使条件预测模型的训练和比较具有基础支撑。其次，它使整个实验系统的“输入空间”具有明确边界，避免论文叙事滑向“任意 band 的通用逆向设计”这种超出当前工作真实能力的表述。再次，它与仓库中的 frozen mainline 配置、runbook 和后续分析材料保持一致，有利于论文与代码之间形成一一对应关系。

因此，本文并不将使用 band catalog 视为方法的局限性缺陷，而将其视为一个合理的研究边界。正是在这一边界内，本文才能把核心问题收敛为“如何在若干明确目标 band 上建立一条可解释、可复现、可验证的 target-band inverse-design workflow”。后续所有方法与结果，都围绕这一边界展开。[待补 thesis band catalog 具体 band 列表或表格]

## 2.3 三层系统架构

### 2.3.1 Truth Layer

本文系统的第一层是 truth layer，对应仓库中的 `physics_pipeline/` 及其所重新解释的一组历史阶段目录。该层的核心职责是生成和维护真实物理真值，包括初始结构筛选、参数方向探测、高阶修正分析以及最终 stage4 验证等。换言之，truth layer 负责回答“在引入任何预测或优化逻辑之前，真实物理世界中哪些结构在什么条件下表现出怎样的 target-band 特征”。

这一层的存在确保了整个系统不会变成脱离物理约束的纯数据拟合流程。无论后续预测模型如何设计，最终都需要以这一层产生的真实真值作为训练基础、比较标准和最终确认依据。因此，在本文框架中，truth layer 不是附属模块，而是整个工作最根本的支撑层。

### 2.3.2 Model Layer

第二层是 model layer，对应 `prediction/` 以及 thesis-facing 的 `prediction_targetband_param_v1/`。这一层的核心任务是在真实真值基础上构建 target-band 数据集，并训练能够面向指定目标频带进行条件预测的模型。与传统无条件预测不同，本文 model layer 的任务定义是“结构 + target band -> 与该 band 相关的预测量”，因此其训练策略、标签设计和评估方式都围绕 band-conditioned prediction 展开。

在当前 frozen mainline 中，model layer 采用条件分类器与条件回归器的双模型结构。前者用于判断指定 target band 上是否存在有效开启的可能性，后者用于估计覆盖质量与相关连续指标。这样做的目的在于把“是否值得继续看”和“可能表现得多好”拆分开来，从而为后续的 candidate ranking 与局部精修提供更细粒度的信息支持。

### 2.3.3 Search Layer

第三层是 search layer，对应 `optimization/`。该层承担的任务不是从零开始构造设计，而是在真实真值和预测模型基础上组织一条 prediction-guided inverse-design 主线。具体而言，它包括 target-band seed scoring、shape-aware candidate construction、local refinement、validation manifest construction 以及对接 stage4 real validation 等步骤。

从角色上看，search layer 起到了把“预测层输出的高分候选”推进为“真实物理可验证设计”的桥梁作用。它既不同于单纯的 predictor，也不同于传统完全依赖高保真评估的 brute-force search，而是在两者之间建立了一个兼顾效率与可信度的中间层。因此，本文的“方法成立”并不意味着某个 predictor 特别强，而意味着这三层结构能够共同组成一条真正可运行的 workflow。

## 2.4 论文主线与历史基线的边界

在本文中，需要特别区分“官方 thesis mainline”和“baseline / historical bridge lines”。当前官方 thesis mainline 是 frozen target-band stack，其主要流程包括 target-band 参数化数据集构建、条件分类/回归训练、prediction-guided seed scoring、local refinement、validation manifest 构建和 stage4 real validation。该主线是本文讨论方法、结果和结论时默认指代的对象。

与之相对，仓库中保留的 `v10/v11/ga_v1` 等路线，虽然在项目演化历史中具有重要作用，但在本文中应被明确定位为 baseline 或 historical bridge。它们的价值主要体现在三个方面：第一，提供历史可追溯性，说明当前主线并非凭空构造；第二，作为比较线，用于说明 frozen target-band mainline 相对于旧线路的改进；第三，在某些分析中提供补充视角，例如 gap34 方向的传统搜索基线。

这种边界划分对于论文叙事非常关键。如果不把主线和基线分开，论文很容易陷入“做了很多路线，但不知道哪一条才是正式贡献”的混乱状态。相反，只要明确“target-band frozen stack 是正式主线，其他路线用于对照和说明项目演化”，全文逻辑就会清晰得多。

## 2.5 本章小结

本章从问题定义、band catalog 边界、三层系统架构以及主线与基线关系四个角度，对本文的整体研究对象进行了界定。可以看到，本文并不是追求一个任意结构、任意频带、任意材料体系上的通用逆向设计框架，而是在 thesis band catalog 与当前参数化结构族范围内，建立一条由 truth layer、model layer 和 search layer 共同支撑的 target-band inverse-design workflow。后续章节中涉及的所有方法与结果，均围绕这一边界展开。

---

# 第三章 物理真值生产与目标频带数据基础

## 3.1 参数化结构表示与结构族定义

本文采用二维参数化结构表示来描述候选声子晶体单胞。该表示方式通过一组几何参数刻画结构轮廓、局部形状及相关关键几何特征，使得结构既能够被统一地输入到预测模型中，又能够在后续局部精修阶段被连续地调节。相较于完全离散的拓扑表示，参数化表示在当前毕设阶段更适合与现有 MATLAB/COMSOL 物理流程对接，也更有利于控制设计空间复杂度。

除几何参数外，本文还特别引入了 shape family 的概念，用于描述不同结构原型之间的类别差异。实践表明，不同 family 在 target-band 任务中的行为并不完全相同，某些 family 更擅长形成特定 band 上的开启，另一些 family 则更适合作为局部 refinement 的起点。因此，在本文方法中，shape 并不是一个普通输入特征，而是正式任务变量的一部分。换言之，本文不仅关心“某个参数点好不好”，还关心“某一类 shape 是否更适合某个 target band”。

这一点对于后续方法设计具有直接影响。一方面，shape family 作为输入特征参与条件预测建模；另一方面，shape-aware candidate construction 也以 family-aware 的方式改善候选池质量。因此，第三章中对结构族与参数表示的介绍，不仅是为了说明数据来源，更是为了为后续的 shape-aware 主线提供概念基础。[待补结构示意图与参数说明表]

## 3.2 物理真值生产流程

本文所有数据驱动方法都建立在真实物理真值之上，因此有必要首先说明真值是如何产生的。当前仓库中的 `physics_pipeline/` 作为 truth layer 的统一入口，重新组织了 `stage1/`、`stage2/`、`stage2_refine/`、`stage2_harmonics/`、`stage2_harmonics_refine/` 以及 `stage4_validation/` 等历史目录。这些目录虽然形成于项目不同阶段，但在本文中应被视为一条连续的真实物理样本生产流水线。

在这一流水线中，早期阶段主要负责结构筛选与基础物理样本生成，中间阶段负责对关键参数方向和高阶效应进行进一步探测与修正，最终的 stage4 validation 则负责对 shortlist 样本进行真实高保真确认。这样的结构说明：预测模型并不是系统的起点，而是建立在一套已有真实真值积累机制之上的中间层工具。

从论文写作角度看，这一节的重点不是逐个解释每个历史脚本，而是突出两个事实。第一，本文的 target-band workflow 不是纯数据拟合，而是始终以真实物理真值为依据。第二，stage4 validation 不只是最终展示结果的工具，同时也是“真值回灌”闭环的一部分，为后续数据积累、主线验证和局部鲁棒性分析提供基础。

## 3.3 目标频带参数化数据集构建

在真实物理真值的基础上，本文进一步构建了面向目标频带任务的参数化数据集。该数据集的核心思想是，将原始结构参数、shape family、目标 band 信息以及与该 band 相关的监督标签整合到统一样本表中，从而把问题从“某个结构整体性能如何”重构为“某个结构在指定目标 band 下是否有设计价值”的条件学习任务。

从数据字段上看，该数据集至少应包含以下几类信息：第一类是结构参数与几何表示信息；第二类是 family 和角色等结构身份信息；第三类是 target band 定义；第四类是与 target band 直接相关的监督目标，例如开启概率标签、覆盖率或 overlap 指标等。通过这种构造方式，数据集天然支持后续的 conditional classification 与 conditional regression。

在当前主线中，target-band 参数化数据集由专门的数据构建入口生成，其默认输出对应 frozen dataset。对于论文而言，这一节需要重点说明数据集“为什么要这样构建”，而不是仅仅罗列字段。其核心逻辑在于：只有把 target band 明确写入样本定义，预测器才真正有可能学到 band-conditioned behavior，而不是退化成无条件结构性能回归。[待补数据集构建脚本、输出路径与字段示例]

## 3.4 标签定义与监督目标

为支持目标频带条件预测，本文将监督目标拆分为分类目标与回归目标两类。分类目标主要回答“该结构在给定 target band 下是否值得继续关注”，例如是否存在有效开启的可能性。与之对应，分类器输出的是一种面向 shortlist generation 的概率或置信度，它不等价于真实物理结果，但能够为后续候选排序提供重要先验。

回归目标则进一步回答“如果值得关注，那么它可能有多好”。在本文中，回归目标主要围绕 target band 的覆盖质量、overlap 或与 band 边界相关的连续性能展开。相比单纯的二元标签，这类连续指标能够提供更丰富的排序信息，并在局部 refinement 中帮助区分“可能成功的候选”和“更优先值得尝试的候选”。

这种“双目标建模”的设计反映了本文对逆向设计任务的理解：对于 target-band inverse design 来说，先判断“有没有可能”，再判断“可能表现得怎样”，往往比直接用一个统一指标回归更稳妥。后续第四章中的模型设计、评估与排序规则，都建立在这一标签拆分方式之上。

## 3.5 数据集边界与统计概况

由于本文工作明确限定在 thesis band catalog 与当前参数化结构族范围内，因此有必要对数据集的统计概况进行说明。首先，不同 band 的样本数量通常并不完全均衡，某些较强 band 可能拥有更丰富的历史真值，而某些弱 band 则更稀缺。其次，不同 family 在各 band 上的表现也存在显著差异，这意味着简单的随机划分并不足以反映模型的真实泛化能力。

基于这一认识，本文采用 family-CV 与 leave-one-band 两类评估策略来刻画模型能力。family-CV 更关注在已有 thesis band 范围内跨 family 的泛化；leave-one-band 则更关注跨 band 的迁移边界。前者更接近“当前主线实际使用时的预期场景”，后者则有助于回答模型对新 band 的适应程度。

从论文写作上看，这一节建议给出一张 band 与样本统计表，并在文字中明确指出：本文后续所有 predictor readiness 与 baseline comparison 结论，都建立在这一数据分布基础之上，因此读者需要结合数据集边界理解模型表现。[待补表 3-1 样本统计]

## 3.6 本章小结

本章介绍了参数化结构表示、物理真值生产流程、target-band 数据集构建方式以及监督标签定义。可以看出，本文的预测与逆向设计主线并不是从模型出发，而是首先建立在真实物理样本支撑下的数据基础之上。在这一基础上，target band 被正式纳入样本定义，shape family 被正式纳入任务边界，这为后续条件预测与 shape-aware candidate construction 提供了统一的数据语义。

---

# 第四章 面向目标频带的条件预测方法

## 4.1 条件预测任务定义

本文中的预测任务不是传统意义上的“结构性能预测”，而是“面向指定目标频带的条件预测”。具体来说，模型输入不仅包括结构参数与 shape family，还包括明确的 target band 信息；模型输出则是该结构在当前 target band 条件下的开启可能性与覆盖质量估计。这样的任务定义使得模型能够直接服务于 inverse-design workflow，而不只是提供一个与设计目标弱耦合的全局性能分数。

从论文表述上看，这一任务定义非常关键。因为如果不强调“条件”二字，读者很容易将本文理解为又一个普通的 bandgap predictor；而一旦明确目标是 band-conditioned prediction，就能更自然地解释为什么本文需要 band catalog、为什么需要 leave-one-band 评估，以及为什么 predictor 的主要用途是 shortlist generation 而不是终局求解。

因此，本节建议在图示或公式层面明确写出任务映射关系，例如：给定结构表示 $x$、family 标识 $f$ 与目标频带 $b$，模型输出分类概率 $\hat{p}(x,f,b)$ 与回归评分 $\hat{r}(x,f,b)$。[待补公式与图 4-1]

## 4.2 分类器与回归器设计

在当前 frozen mainline 中，本文采用随机森林作为条件分类器，采用 HGB 作为条件回归器。分类器主要负责识别“该结构在指定 band 上是否具有值得继续搜索的潜力”，回归器则进一步估计其覆盖质量或 overlap 水平。这种双模型结构使得系统在面对 target-band inverse design 任务时，既能形成概率性的 shortlist prior，又能形成连续性的排序依据。

选择这两类模型的原因并不在于它们一定在所有可能模型中最复杂或最新，而在于它们在当前任务中具备较好的稳定性、可解释性与工程可复现性。对于毕业设计而言，这一取舍是合理的：如果方法部分过度依赖难以解释的复杂模型，而主线闭环与真实验证不够稳定，论文整体反而会失去说服力。相反，采用稳定模型、明确边界，再通过完整 workflow 证明有效性，更符合本文的目标。

从写作上看，本节可以简单介绍模型家族及主要超参数，并指出：本文的贡献重点并不在于发明一个新模型，而在于把条件预测器有效嵌入到 target-band inverse-design workflow 中。因此，模型本身应被视为主线中的一个模块，而不是全文唯一中心。

## 4.3 训练与验证设置

为全面评估条件预测器的能力，本文采用了 family-CV 与 leave-one-band 两类验证设置。前者主要检验模型在已知 thesis bands 范围内跨不同 structure family 的泛化能力，后者则检验模型在保留 band 维度外推边界时的表现。由于 target-band inverse design 的目标并不是简单追求整体误差最小，而是更关注 shortlist quality，因此本文在评价指标设置上同时兼顾分类能力、回归质量与 top-k 排序质量。

对于分类器而言，AUC、AP 和 Precision-Recall 等指标可以反映整体区分能力；但对本文而言，更重要的是 top-k shortlist 命中率，因为主线真正使用 predictor 的方式，是把高分结构送入后续 refinement 与真实验证。对于回归器而言，MAE、RMSE 等指标可以作为参考，但更关键的是排序单调性和 top-k coverage quality，即高分候选是否真的更接近有价值的 target-band 结构。

因此，本节应强调：本文的训练与验证设置并不是为了追求某一个单点指标，而是为了评估 predictor 是否具备“进入 workflow”的资格。换言之，本节的最终目标不是报告模型成绩，而是为下一节的 predictor readiness 判断提供依据。

## 4.4 Predictor Readiness 分析

基于上述训练与验证设置，本文进一步对条件预测器进行 predictor readiness 分析。所谓 readiness，并不是指模型已经在所有条件下足够强，而是指它是否已经达到可以稳定进入 target-band inverse-design workflow 的程度。围绕这一问题，本文主要从 family-CV、leave-one-band、top-k shortlist quality 以及校准/单调性四个角度进行分析。

在 family-CV 条件下，模型表现反映了其在当前 thesis band catalog 范围内对不同结构族的区分与排序能力。如果 family-CV 表现稳定，则说明 predictor 至少可以作为当前主线的 practical shortlist engine 使用。在 leave-one-band 条件下，模型表现则揭示了跨 band 迁移的边界：即使性能可能低于 family-CV，其结果仍然能够说明 predictor 是否具备一定程度的 target-band generalization。对于毕设叙事而言，这种区分非常重要，因为它能帮助我们诚实地说明“模型现在能做到什么，还做不到什么”。

除此之外，top-k shortlist quality 是本文最关心的 readiness 指标之一。本文并不要求 predictor 必须在所有样本上都给出完美预测，而更关注它能否把更值得真实验证的样本排在前面。若 predictor 能够在 top-k 范围内明显提高高价值候选的密度，那么即使它不是一个最终最优排序器，也已经足以为后续 refinement 和 stage4 validation 提供方向支持。与此对应，概率校准和回归分数单调性则进一步说明 predictor 输出是否适合作为排名依据，而不仅仅是“能分对一些标签”。

## 4.5 Predictor 的作用边界

尽管 predictor readiness 分析表明条件预测器已经具备进入 workflow 的能力，但本文并不将其夸大为一个完整设计器。更准确地说，predictor 在本文中的地位是 shortlist engine：它负责把设计空间中更值得继续看的结构提前暴露出来，并为后续局部 refinement 提供方向，而不是直接替代真实搜索与真实物理求解。

这一区分对论文整体叙事十分关键。如果把 predictor 写成“自动找到最优结构”的万能模块，论文很容易与实际结果脱节，也不符合当前系统的真实能力。相反，只要明确 predictor 的作用在于 shortlist generation，就可以更自然地解释后续 shape-aware candidate construction、local refinement 与 stage4 real validation 的必要性。尤其是在 weak-band 分析中，predictor 的贡献更适合被写成“提供了实质排序价值”，而不是“单独解决了弱 band 设计问题”。

因此，本节建议在结尾明确给出一句边界性表述：本文的 predictor 已经具备 workflow-ready 的 shortlist value，但尚不应被表述为可以独立完成 target-band inverse design 的最终模型。

## 4.6 本章小结

本章围绕 target-band 条件预测任务，介绍了任务定义、双模型设计、训练与验证设置以及 predictor readiness 判断。结果表明，在当前 thesis band catalog 与参数化结构族范围内，本文建立的条件预测器已经能够作为 target-band inverse-design workflow 的 shortlist engine 使用。它的价值不在于替代真实物理求解，而在于为后续的 shape-aware candidate construction、局部 refinement 和 real validation 提供有效的方向感。

---

# 第五章 预测驱动的目标频带逆向设计方法

## 5.1 总体方法描述

在第四章获得可用的条件预测器之后，本文进一步构建了 prediction-guided target-band inverse-design workflow。该 workflow 的核心思想是：不是直接在整个设计空间中进行高成本真实搜索，而是首先基于真实真值和结构先验构造候选种子，再借助条件预测器对其进行 target-band scoring，随后通过 shape-aware candidate construction 和 conservative local refinement 对高价值候选做进一步推进，最终以 MATLAB/COMSOL 完成 stage4 real validation。

从方法论上看，这条主线体现的是“多模块协作”而不是“单模块替代”。其中，predictor 负责提供方向性优先级，shape-aware front-end 负责改善候选池质量，local refinement 负责在局部参数空间内挖掘可用设计，real validation 则负责给出最终物理确认。这样的组织方式既降低了直接全局搜索的成本，又避免了纯预测方法脱离真实物理验证的风险。

本节建议配一张总流程图，并在图中清晰标出各步骤之间的输入输出关系。[待补图 5-1] 对于后续章节的读者来说，理解这一张图，基本就能把本文方法主线与各子模块之间的关系把握清楚。

## 5.2 Shape-Aware Candidate Construction

本文并不把 shape 仅视为一个普通特征，而是将其正式纳入候选构造逻辑中。实践中，如果忽略 shape family 差异，仅凭某一组无条件先验进行候选筛选，往往会导致候选池过于集中于历史强势结构，进而削弱 target-band 任务下的探索能力。为此，本文引入了 shape-aware candidate construction，通过 band-aware 与 family-aware 的方式改善候选池质量，使后续 seed scoring 面对的是一个更合理的候选集合。

这一设计的意义在于，它把“结构族差异”从被动存在转化为主动利用。也就是说，本文并不是简单承认不同 family 的性能分布不一样，而是进一步利用这种差异去构造更适合 target-band inverse design 的候选池。这样一来，后续 predictor 输出的排序分数就不再建立在一个过于随意或历史偏置过强的候选集合之上，而建立在一个经过 shape-aware 整理的输入空间之上。

从论文写作上看，本节可以适当结合 shape atlas、archetype pilot 或相关 exploratory 文档，用于说明“shape-aware”并非额外包装，而是当前主线中的正式组成部分。[待补相关图表与案例说明]

## 5.3 Target-Band Seed Scoring

在候选池构造完成之后，本文使用条件预测器对候选 seed 进行打分。这个过程对应的是“target-band seed scoring”，即把每个候选结构放入指定 band 条件下进行评估，得到其开启概率、覆盖质量预测以及相应的组合评分。通过这一过程，系统可以在进入真实局部 refinement 之前，优先保留那些更有可能形成有效 target-band 结果的结构。

这一阶段的关键点在于：打分逻辑不是一个简单的单指标排序，而是结合分类与回归信息形成针对 target band 的综合评价。因此，seed scoring 的目标不是声称某个候选“必然成功”，而是尽可能提高前列候选的真实命中密度。换言之，它服务的是后续搜索预算的有效分配。

本节写作时，建议明确说明候选 seed 的来源、打分字段、组合规则以及输出结果在主线中的位置。尤其要强调：seed scoring 仍然是 prediction-guided shortlist，而不是最终设计结论。它的主要价值在于通过模型 prior 改善后续局部搜索的起点质量。

## 5.4 Conservative Local Refinement

在 seed scoring 之后，本文采用 conservative local refinement 对高价值候选进行进一步推进。之所以强调“conservative”，是因为本文并没有采用完全开放的大范围全局搜索，而是围绕高分 seed 的局部参数邻域进行较为稳健的 refinement。这样的设计符合当前毕设的研究边界和计算预算，也更适合作为 thesis-facing mainline 的正式方法。

从方法角度看，这一局部 refinement 具有两个作用。第一，它帮助修正 predictor 与真实物理之间可能存在的偏差，使高分 seed 有机会在真实可行的局部方向上进一步优化。第二，它使 workflow 不再停留在“排序”层面，而真正具备“把好候选推进成更好设计”的能力。尤其在 weak-band 场景下，单纯排序往往不足以得到最终结果，而 conservative local refinement 可以提供决定性的补充。

在论文表述中，本节可以适当对比历史上的全局 GA 或其他 baseline 线路，指出当前局部 refinement 主线并不是追求最大化搜索规模，而是追求在预测 prior 支持下实现更可控、更解释性强的 target-band inverse design。

## 5.5 Validation Manifest 与 Python-MATLAB 契约

为将 Python 侧产生的高价值候选稳定地交给 MATLAB/COMSOL 进行 stage4 验证，本文构建了统一的 validation manifest 及其共享 contract。manifest 的作用是把待验证候选的结构标识、参数、排序来源及必要元数据整理成一份稳定的中间描述，使不同运行阶段之间的数据传递不再依赖零散字符串或临时字段拼接。

在此基础上，本文进一步抽取了 Python 与 MATLAB 共享的 manifest contract，对必需字段、字段角色、空值与数值合法性进行约束。这样做有两个直接好处：第一，任何 manifest 结构错误都能在进入 COMSOL 之前暴露出来，避免把问题拖到高成本求解阶段；第二，整个 thesis mainline 的配置语义得到统一，有利于后续的可复现与可维护性。

对于毕业论文而言，这部分内容非常值得强调。因为它不仅说明本文“能跑”，更说明本文“能稳定地跑、能重复地跑、能让别人按主线复现”。这类工程化闭环在毕设答辩中通常具有很强的说服力。[待补 manifest 字段示意、contract 结构说明或代码映射表]

## 5.6 Stage4 Real Validation

无论前面的 predictor、seed scoring 或 local refinement 表现如何，最终都必须回到真实物理验证。为此，本文将 stage4 real validation 作为整个 inverse-design workflow 的终点与闭环确认环节。该阶段通过 MATLAB/COMSOL 读取 validation manifest 中的候选结构，对其进行真实求解，并输出几何有效性、接触有效性、求解成功与否以及最终 gap/gain 等结果。

stage4 validation 在本文中的角色至少有三重。首先，它是主线结果可信性的最终来源。其次，它是把“预测高分候选”与“真实可用设计”区分开来的关键步骤。再次，它也是一个真值回灌节点，可为后续数据集维护、局部鲁棒性分析和主线进一步扩展提供新的真实样本。因此，本文不会把 stage4 写成附录式验证，而会把它写成方法闭环中不可替代的一环。

本节建议在写作时明确说明：如果没有 stage4 real validation，本文最多只能声称建立了一个条件预测与候选排序系统；正因为有了这一环，本文才有资格把自己的工作描述为一个真正的 target-band inverse-design workflow。

## 5.7 Baseline / Historical Bridge 的定位

除正式主线外，仓库中还保留了一系列历史路线与 baseline 线路，例如 `v10/v11/ga_v1` 等。这些路线在项目演化过程中发挥了重要作用，也为本文主线提供了比较与解释基础。然而，在论文中，它们不应再作为默认流程出现，而应被明确定位为 comparison baselines 或 historical bridge lines。

这样处理有两个好处。第一，可以保持论文叙事的聚焦：读者清楚知道哪一条才是本文的正式方法。第二，可以更合理地使用 baseline：不是为了“把所有历史工作都写进去”，而是为了用它们来说明 frozen target-band mainline 的优势、边界与演化路径。因此，基线的价值不在于喧宾夺主，而在于为主线提供参照系。

## 5.8 本章小结

本章介绍了 prediction-guided target-band inverse-design workflow 的方法构成。可以看到，本文方法并不是单个 predictor 的延伸，而是一条由 shape-aware candidate construction、target-band seed scoring、conservative local refinement、validation manifest contract 与 stage4 real validation 共同组成的完整流程。正是这些模块的协同作用，使本文能够在 thesis band catalog 范围内建立一条真正可运行、可解释、可验证的 inverse-design 主线。

---

# 第六章 实验设计与结果分析

## 6.1 实验目标与证据结构

本文的实验并不是围绕若干零散脚本展开，而是围绕一条证据链展开。具体来说，全文实验部分主要回答三个问题：第一，条件预测器是否已经具备 shortlist value；第二，prediction-guided 主线是否能够真正驱动真实设计发现；第三，这条主线是否不仅在强 band 上有效，而且对弱 band 也具有推进作用。

为了回答这三个问题，本文将实验结果组织为五类证据：predictor readiness、canonical inverse-design cases、baseline comparison、weak-band shortlist value 以及 stage4 real validation。这样的安排与传统“按实验顺序写结果”不同，它更接近一种论证结构：每一类结果都在支撑一个明确结论，而这些结论共同构成本文的总体论点。

因此，本章最重要的任务不是罗列所有数值，而是说明这些结果如何层层支撑本文主线。建议在本节结尾用一张总表或示意图概括各实验块的作用定位。[待补表 6-1 或图示]

## 6.2 实验设置

本文实验统一在 thesis band catalog、固定材料与物理配置的边界内展开，并使用 frozen target-band mainline 作为正式流程。预测相关实验主要围绕 target-band 参数化数据集、条件分类器与条件回归器的训练与验证进行；逆向设计相关实验则以 prediction-guided shortlist、local refinement、validation manifest 和 stage4 real validation 为核心流程。

作为对照，本文同时保留若干 baseline 路线，包括 generic prior、targetband local probe/top-k 变体、band-catalog real GA 以及补充型真实搜索线路等。这些 baseline 并不是为了展示项目“做了很多事”，而是为了构成一个合理的参照框架，帮助判断 frozen target-band mainline 的有效性究竟来自哪里。

建议在本节中给出一张实验线总表，对每条实验线的目标、作用和在论文中的身份做简要说明。这样可以显著降低读者后续阅读 baseline comparison 时的认知负担。[待补表 6-1]

## 6.3 Predictor Readiness 结果

在 predictor readiness 方面，本文首先考察了 family-CV 条件下的分类与回归表现。结果表明，在当前 thesis band catalog 与参数化结构族范围内，条件预测器能够较稳定地区分不同结构在指定 target band 上的潜力，并在 top-k 维度上表现出实际可用的 shortlist 价值。[待补 family-CV 指标与图表] 这说明 predictor 至少在“当前主线实际使用场景”下已经具备进入 workflow 的资格。

进一步地，在 leave-one-band 评估中，模型表现虽然相较 family-CV 更为保守，但仍揭示出一定程度的 band-conditioned migration ability。对本文而言，这一结果的意义并不在于宣称 predictor 已经完全解决了跨 band 泛化问题，而在于说明：即使在更严格的设定下，模型仍保留一定的结构化信息，而不是完全失效。

更关键的是，top-k shortlist 结果说明 predictor 的高分候选确实更集中于后续值得验证的结构。这一点比单纯的分类精度更贴近本文的设计目标。结合概率校准与分数单调性分析，可以认为当前 predictor 已足以作为 workflow-ready shortlist engine 使用。换言之，predictor readiness 在本文主线中已经成立。

## 6.4 Canonical Inverse-Design Cases

为验证 prediction-guided 主线的真实设计能力，本文进一步固定若干 canonical inverse-design cases，并对其进行逐案分析。这些案例覆盖 `band180_220`、`band200_240`、`band220_260` 与 `band240_280` 等关键目标频带，用于展示本文主线在不同 band 条件下的设计发现能力。

对于每个 case，本文均从结构身份、优化参数、真实结果、与旧 baseline 的对比以及物理解释五个角度进行分析。[待补各 case 的结果表与图] 这种写法的优点在于：它不仅展示“找到了一些结果”，还展示“这些结果来自怎样的 workflow、相比旧路线好在哪里、其物理意义是什么”。尤其对于 `band180_220` 等关键案例，应突出其在当前 frozen target-band mainline 中的代表性。

从总体上看，canonical cases 的结果支持了这样一个判断：条件预测器与局部 refinement 的结合，并不是停留在离线分数层面的改进，而是真正能够在真实物理约束下推动目标频带设计发现。这也是本文将该 workflow 称为 inverse-design mainline 的核心依据之一。

## 6.5 Baseline Comparison

为进一步评估 frozen target-band mainline 的有效性，本文引入多条 baseline 线路进行系统比较。比较线既包括更泛化但缺乏 target-band 条件性的 generic prior，也包括 local probe/top-k 变体，以及更传统的 real GA 或补充搜索路线。通过这种多层对比，本文希望回答的不是“哪条线在任何指标上都绝对最好”，而是“当前 thesis mainline 相比已有可选路线，是否具有更合理的综合优势”。

从各 band 的对照结果来看，frozen target-band mainline 在多个关键 band 上表现出更好的 shortlist 质量、更合理的 family 多样性以及更高的真实验证转化价值。[待补 baseline comparison 的 band 分析] 这说明 target-band conditioning 与 prediction-guided refinement 的组合并不是形式上的改名，而是在结构发现效率与设计有效性上具有实际收益。

此外，baseline comparison 也帮助本文更克制地界定主线的优势边界。例如，在某些场景下，传统 real GA 或 exploratory 路线仍可能表现出竞争力，这提醒我们不应把 predictor-driven mainline 写成唯一最强方案，而应写成“在当前 thesis band catalog 与预算约束下更适合作为正式主线的方案”。这种表述更符合真实结果，也更符合学术写作的谨慎原则。

## 6.6 Weak-Band Shortlist Value 与 Coverage 分析

本文特别重视 weak-band 场景，因为这类场景更能检验 predictor-driven workflow 的实际价值。如果一个方法仅在强 band 上有效，它的研究意义往往会受到限制；而如果它能够在弱 band 上提供实质推进，那么其作为 inverse-design workflow 的说服力就会显著增强。

相关实验结果表明，predictor 并不是一个“没有用的排序器”。在若干 weak-band 条件下，它仍能够显著改善高价值候选的集中度，为后续 refinement 与真实验证提供更好的起点。[待补 weak-band 图表与结果] 但与此同时，结果也显示 predictor 不是任何时候都最强的最终排序器，其效果仍需与 shape-aware candidate construction 和 local refinement 结合后才能充分发挥。

因此，本文对 weak-band 结果的正式表述应当是：predictor 已经在弱 band 场景中体现出明确的 shortlist value，并对后续 target-band inverse-design 主线形成实质支撑，但这并不意味着弱 band 问题已经被 predictor 单独完全解决。

## 6.7 Stage4 Real Validation 结果

在完成 predictor-driven refinement 之后，本文对 target-band validation manifest 中的候选结构进行了 stage4 real validation。当前结果显示，主线 manifest 中的样本已完成真实验证，输出包括 `stage4_validation_results.csv`、point/shape summary 等结果文件。[待补结果表与统计图]

从当前 stage4 结果看，至少可以从以下几个方面进行汇总：验证样本数量、几何有效率、接触有效率、求解成功率以及正向 gain 情况。如果这些指标整体稳定且表现积极，那么就可以说明当前 frozen mainline 不仅能在 predictor 层和 refinement 层给出可行候选，而且能够在真实高保真验证中得到有效响应。

对论文整体而言，stage4 real validation 的通过意味着本文的主线已经完成从“数据与预测”到“真实物理结果”的闭环。这是全文最重要的落点之一，因为它决定了本文是否有资格把自己的方法描述为一个真实成立的 inverse-design workflow，而不仅是一个数据分析流程。

## 6.8 Local Robustness 分析

除主结果之外，本文还对若干 canonical inverse-design cases 的局部鲁棒性进行了分析。该分析主要关注中心点保真度、局部保持率、边界漂移以及敏感变量等问题，用于回答：即使一个设计在中心点上表现良好，它在局部扰动下是否仍能保持 target-band 性能趋势。[待补 robustness 结果图表]

局部鲁棒性分析的意义在于，它为本文主线增加了“设计稳定性”这一层解释。如果一个 canonical case 仅在极窄参数点上成立，那么其工程意义会受到限制；相反，如果它在局部扰动下仍保留较好的 band 行为，那么就能进一步说明该设计不是偶然结果，而是具有一定结构稳定性。

从篇幅安排上看，这部分内容既可以作为主结果的一节，也可以在篇幅有限时适当压缩并转移到附录。但无论放在哪里，它都适合被写成对 canonical cases 的补充支撑，而不是另起一条与主线平行的新叙事。

## 6.9 本章小结

本章围绕 predictor readiness、canonical inverse-design cases、baseline comparison、weak-band shortlist value、stage4 real validation 和 local robustness 等方面，构建了本文的核心证据链。综合来看，可以得出以下判断：第一，条件预测器已经具备 workflow-ready 的 shortlist value；第二，prediction-guided inverse-design 主线能够在多个目标频带上发现可验证设计；第三，与历史 baseline 相比，frozen target-band mainline 具有更清晰、更有效的综合优势；第四，弱 band 也得到了实质推进；第五，stage4 real validation 使整条主线完成了真实物理闭环。

---

# 第七章 讨论与局限性分析

## 7.1 本文方法真正成立的范围

基于前文分析，本文方法的成立范围可以明确概括为：thesis band catalog 范围内、当前参数化结构族范围内以及当前材料与物理求解配置条件下。也就是说，本文建立的是一个在明确边界内成立的 target-band inverse-design workflow，而不是一个对任意结构表示、任意 band 和任意材料体系都自动成立的通用框架。

这种边界的明确不是对方法的削弱，而恰恰是其可信度的重要来源。因为对于毕业设计而言，最有价值的并不是做出无限扩张的口头主张，而是在清晰边界内给出一条真正闭环的工作流。正因如此，本文选择冻结 thesis band catalog，冻结 target-band mainline，并在文档、代码与实验中保持一致语义。

## 7.2 本文不能过度宣称的内容

尽管本文已经建立了完整 workflow，并在多个关键 band 上获得了真实物理结果，但仍有若干内容不应被过度宣称。首先，本文不能宣称已经实现了完全通用的 target-band inverse design；因为当前工作仍明显依赖于 thesis band catalog、现有结构族与当前物理配置。其次，本文不能把 predictor 写成真实求解器的替代品；因为 predictor 的主要作用仍然是 shortlist generation，而非最终物理确认。再次，本文不能宣称弱 band 问题已经被完全解决；更准确的说法应当是，weak-band design discovery 在当前主线下得到了实质推进。

这种克制性的表述并不会削弱本文价值，反而会使论文更符合真实结果。因为一条可信的 inverse-design workflow，首先需要建立清楚的边界与角色，而不是通过夸大表述来制造“无所不能”的印象。

## 7.3 为什么采用“条件预测 + 局部精修 + 真实验证”的组合

本文之所以采用“条件预测 + 局部精修 + 真实验证”的组合，是因为单独依赖任何一个模块都难以稳定解决 target-band inverse-design 问题。单独 predictor 虽然可以提供排序 prior，但难以保证真实物理结果；单独真实搜索虽然可信，但成本高、效率低；单独 shape heuristic 则容易固化为经验规则，缺乏系统可扩展性。只有把三者结合起来，才能在当前毕设边界内形成既有方向感、又能闭环验证的主线。

这种组合式方法也解释了本文相较一些单模型工作或单优化工作的重要区别。本文的贡献重点不是把某一个子模块做到极致，而是把多个模块以更合理的边界组织起来，形成一条实际可运行的 workflow。从工程与答辩角度看，这样的系统性往往比单点最优更重要。

## 7.4 工程可复现性与系统可维护性

除方法与结果本身外，本文还对 thesis-facing mainline 做了系统性收口。具体来说，当前仓库已经明确了 frozen thesis mainline 与 baseline/historical bridge 的边界，统一了 profile、policy 与 run config 的语义，并建立了 Python 与 MATLAB 之间共享的 validation manifest contract。同时，围绕主线又增加了 smoke tests、runbook 和 method map 等辅助文档。

这些工程改动的意义在于，它们使本文工作不再只是“作者本人知道怎么跑”的一次性实验，而是一条在仓库层面可追踪、可复现、可解释的主线流程。这对于毕业设计非常重要，因为答辩老师和后续读者最终关心的，不只是结果是否存在，还包括“这条主线能否被讲清楚、能否被重现、能否继续维护”。

## 7.5 后续可扩展方向

尽管当前工作已经建立了较完整的 target-band inverse-design workflow，但其扩展空间仍然很大。首先，可以进一步扩展 thesis band catalog，纳入更多 target bands，并研究 predictor 在更宽 band 空间中的条件泛化。其次，可以扩展结构表示能力，引入更丰富的 structure family 或更高自由度的参数表示。再次，可以加强 weak-band truth harvesting，通过更系统的真实验证回灌，提高困难 band 的数据密度。

除此之外，局部鲁棒性、制造约束和 active learning 都是值得进一步推进的方向。特别是如果未来能把 stage4 真实验证结果更系统地回灌到训练数据中，那么整个 workflow 有望进一步演化为一个更完整的 closed-loop inverse-design system。

## 7.6 本章小结

本章从成立范围、不可过度宣称之处、方法组合原因、工程可复现性和未来扩展方向等方面，对本文工作进行了讨论。总体来看，本文最重要的成果并不是某一个 isolated best score，而是在明确边界内建立了一条可解释、可验证、可复现并具备后续扩展潜力的 target-band inverse-design mainline。

---

# 第八章 结论与展望

## 8.1 全文工作总结

本文围绕目标频带逆向设计问题，构建了一个面向 thesis band catalog 的 target-band 条件预测与预测驱动逆向设计流程。全文首先从真实物理真值出发，建立了 target-band 参数化数据基础；然后构建了条件分类器与条件回归器，并通过 predictor readiness 证明其具备 shortlist value；在此基础上，进一步结合 shape-aware candidate construction、local refinement 与 stage4 real validation，建立了完整的 prediction-guided inverse-design 主线。

从系统结构看，本文将整个流程组织为 truth layer、model layer 和 search layer 三层架构，使得每一层的角色都具有明确边界。truth layer 提供真实物理真值与最终验证依据，model layer 提供条件预测能力，search layer 则将二者连接为真正可执行的 inverse-design workflow。这样的组织方式既提高了方法可解释性，也提高了工程可复现性。

## 8.2 主要结论

结合全文分析，本文可以得到以下主要结论。

第一，面向目标频带的条件预测器已经具备实际可用的 shortlist value。其价值主要体现在 target-band candidate ranking 上，而不是作为真实求解器的替代品。

第二，shape-aware candidate construction 是本文方法的正式组成部分，而非附属启发式规则。通过将 family-aware 与 band-aware 逻辑纳入候选池构造，本文显著改善了 prediction-guided search 的输入质量。

第三，prediction-guided inverse-design mainline 相较若干历史 baseline 与 comparison routes，表现出更清晰和更有效的综合优势。其意义不在于任何单一指标绝对最优，而在于在当前 thesis band catalog 与预算边界内提供了更合理的正式主线。

第四，本文方法不仅在若干强 band 上取得了真实结果，也对 weak band 的设计推进提供了实质支持。结合 stage4 real validation，可以认为本文已经在当前边界内建立了一条真实成立的 target-band inverse-design workflow。

## 8.3 工作不足

尽管本文取得了一定进展，但仍存在若干不足。首先，当前方法的成立范围仍主要局限于 thesis band catalog，尚未覆盖更广泛的连续 band 条件。其次，本文采用的结构表示仍然主要基于当前参数化结构族，尚未扩展到更高自由度或更复杂的结构形式。再次，真实验证预算仍然有限，因此当前 stage4 结果更多体现了 workflow 成立，而不是对全部候选空间进行穷尽验证。

此外，局部鲁棒性与制造约束分析虽然已经开始展开，但其深度仍有进一步提升空间。对于未来工作而言，这些问题既是限制，也是继续扩展本研究的自然方向。

## 8.4 未来工作展望

未来的工作可以沿以下几个方向继续推进。第一，扩展 thesis band catalog 并增加跨 band 的真实验证样本，以提高条件预测器的泛化边界。第二，丰富结构表示与结构族覆盖范围，使 workflow 能够处理更复杂的 candidate space。第三，将更多 stage4 real validation 结果系统回灌到训练数据中，形成更强的 active feedback loop。第四，进一步引入制造约束、鲁棒性约束等工程因素，使方法更贴近实际设计需求。

总体而言，本文已经在当前边界内建立了一条较为完整的 target-band inverse-design 主线。未来若能在数据规模、结构表示与真实验证反馈上继续推进，这条主线有望发展为一个更强、更广义、更工程化的闭环逆向设计系统。

---

# 最后建议

如果你接下来要继续把这份骨架写成正式论文，最推荐的顺序仍然是：

1. 先把第六章的结果数字、表格和图填进去。
2. 再回过头精修第五章方法部分。
3. 然后补第三章的数据与真值细节。
4. 最后再润色第一章与第八章，让摘要、绪论、结论三处口径完全一致。

如果你愿意，下一步我可以继续帮你把这份骨架再推进一层，直接把“摘要、第一章、第二章”扩写成更接近正式论文语言的连续初稿。
