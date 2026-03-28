# graduation_project 最小侵入式模块化改造方案

## 目标与边界

本方案的目标不是把当前研究仓库重写成“通用软件平台”，而是在**不破坏现有 `main / v11` 工作流**、**不搬大目录**、**不删除现有 runner**、**不引入复杂框架**的前提下，为以下变化预留稳定入口：

- 换目标
- 换材料
- 换 scoring
- 换验证策略

本轮建议遵循四条原则：

1. 保留现有 `v*.py` / `v*.m` 文件名和 runner 名称，外部入口不变。
2. 新增“共享 helper / profile / policy”层，旧脚本先改成薄包装器。
3. 优先抽“策略参数”和“文件路径映射”，暂不抽 COMSOL 物理求解核心。
4. 每一阶段都保证可以通过回退单个新增 helper 或恢复单个包装脚本来撤销。

## 当前结构诊断

### A. 目前属于“写死的研究设定”的内容

| 类别 | 当前落点 | 典型写死内容 | 说明 |
| --- | --- | --- | --- |
| 物理母体与求解基线 | `stage2_harmonics_refine/get_stage2_harmonics_refine_config.m` | `materialCase='soft_matrix_hard_inclusion'`、`fixedGapBand=3`、`studyNeigs=20`、`studyShiftHz=200`、`baseParamOverrides` | 这是论文主线设定，不应直接“泛化重构”，但应被识别为 profile。 |
| 已知可信点与 DOE 研究域 | `stage2_harmonics_refine/get_stage2_harmonics_refine_config.m` | `mainPointSpecs`、`mainlineShapeIds`、`specialCaseShapeIds`、`b3/a4/b5` 扫描值 | 这些本质上是当前研究假设，不是通用框架参数。 |
| 数据集纳入范围 | `stage3_dataset/build_v1_training_dataset.py`、`build_v5_training_dataset.py`、`build_v7_training_dataset.py` | `STAGES`、`SURROGATE_CORE_STAGES`、`SPECIALCASE_SHAPE_FAMILIES` | 这是“本轮训练用哪些历史真值”的研究决策。 |
| 候选点定义 | `stage3_training/build_candidate_pool_v10.py`、`build_candidate_pool_v11.py` | `POINT_SPECS` 里的 `rf09_h00_center`、`rf09_h09_b5_002_a4_0015` | 这不是程序结构常量，而是实验策略。 |
| 家族排除规则 | `stage3_training/build_candidate_pool_v10.py`、`build_candidate_pool_v11.py` | 从 `stage4_validation_ab_v1~v10` 结果里排除已验证 family | 属于候选池策略，应可配置。 |
| 评分阈值与权重 | `stage3_training/run_seed_discovery_scoring_v7.py`、`seed_discovery_scoring_calibration_v1.json` | `contact_threshold`、`positive_threshold`、`contact_weight`、`positive_weight` | 这是策略参数，不应继续散落在脚本默认值和 runner 命令串里。 |
| 验证配额策略 | `stage3_training/build_validation_manifest_v10.py`、`build_validation_manifest_v11.py`、对应 runners | `primary-k`、`probe-k`、`diversity-k`、`max-per-shape`、`max-per-family` | 这是 manifest policy，不是流程骨架。 |
| GA 搜索边界 | `stage3_training/run_parametric_ga_seed_search_v1.py`、`ga_shape_whitelist_v1.json` | `GLOBAL_BOUNDS`、`LOCAL_HALF_WIDTHS`、白名单 shape ids、fitness 权重 | 高度实验性，应保留为 profile/policy。 |

### B. 目前适合抽象成“可配置模块”的内容

| 模块 | 当前问题 | 推荐抽象方式 |
| --- | --- | --- |
| 版本到路径的映射 | v10/v11 脚本大量重复，只差路径和少量参数 | 共享 `profile` / `policy` 模块，由 `v10/v11` 包装器调用 |
| 候选池策略 | `POINT_SPECS`、排除 family 逻辑散落在独立脚本 | 抽成 Python profile 字典或 JSON |
| scoring 策略 | 阈值、权重、排序字段同时分布在 Python 默认参数、JSON、MATLAB runner | 抽成单一 scoring policy 输入 |
| manifest 策略 | v10/v11 逻辑几乎一致，只差输出名和名额 | 抽成共享 builder + 版本化 policy |
| stage4 验证配置 | `get_stage4_validation_config_v10.m`、`v11.m`、`ga_v1.m` 大段重复 | 抽成共享 MATLAB config builder |
| stage4 runner 元数据拼接 | `run_stage4_validation_ab_v10.m`、`v11.m` 基本复制 | 抽成共享 runner helper，旧 runner 保留名字 |
| 数据集 stage 注册 | `build_v1` 到 `build_v7` 用继承式复制，新增版本成本高 | 抽成 stage registry / dataset profile |

## 分阶段改造计划

以下阶段按优先级从高到低排序。

### 阶段 1：先把 v10 / v11 的候选池、scoring、manifest 改成“薄包装 + 共享策略层”

**建议改动文件**

- 新增 `stage3_training/seed_discovery_profiles.py`
- 新增 `stage3_training/seed_discovery_pipeline.py`
- 调整 `stage3_training/build_candidate_pool_v10.py`
- 调整 `stage3_training/build_candidate_pool_v11.py`
- 调整 `stage3_training/build_validation_manifest_v10.py`
- 调整 `stage3_training/build_validation_manifest_v11.py`
- 调整 `runners/run_stage3_build_score_and_manifest_candidate_pool_v10.m`
- 调整 `runners/run_stage3_build_score_and_manifest_candidate_pool_v11.m`
- 调整 `runners/run_stage3_build_validation_manifest_v10.m`
- 调整 `runners/run_stage3_build_validation_manifest_v11.m`

**为什么改**

- 这是当前重复度最高、收益最大、风险最低的一段。
- `build_candidate_pool_v10.py` 与 `build_candidate_pool_v11.py` 几乎只有输出目录、排除到哪一轮 stage4、profile 名称不同。
- `build_validation_manifest_v10.py` 与 `build_validation_manifest_v11.py` 逻辑几乎相同，主要差异只是默认输入输出和名额策略。
- 当前 MATLAB runner 把 Python 命令和参数写死在字符串里，不利于后续“换 scoring / 换验证策略”。

**推荐做法**

- 保留现有 `v10` / `v11` 文件名不变。
- 让 `build_candidate_pool_v10.py` / `v11.py` 只做两件事：选择 profile，调用共享 builder。
- 让 `build_validation_manifest_v10.py` / `v11.py` 只做两件事：选择 manifest policy，调用共享 builder。
- 让 MATLAB runner 继续存在，但只负责调用对应脚本，不再自己拼一长串策略参数。

**是否影响现有 v10 / v11 主流程**

- 低影响。
- 外部入口名、输出目录名、runner 名都不变时，`v10 / v11` 主流程应保持等价。

**如何保证回滚简单**

- 包装器文件保留原名，必要时只需把共享调用改回原始实现。
- 新增共享模块是附加层，删掉即可回退。
- 不改 `data/` 产物目录结构，不影响已有结果复用。

### 阶段 2：把“scoring policy / manifest policy / GA policy”从脚本常量中抽出来

**建议改动文件**

- 新增 `stage3_training/policies/seed_discovery_v10.json`
- 新增 `stage3_training/policies/seed_discovery_v11.json`
- 新增 `stage3_training/policies/ga_v1.json`
- 调整 `stage3_training/run_seed_discovery_scoring_v7.py`
- 调整 `stage3_training/build_validation_manifest_v10.py`
- 调整 `stage3_training/build_validation_manifest_v11.py`
- 调整 `stage3_training/run_parametric_ga_seed_search_v1.py`
- 调整 `stage3_training/build_ga_validation_manifest_v1.py`
- 调整 `runners/run_stage3_run_seed_discovery_scoring_v10.m`
- 调整 `runners/run_stage3_run_seed_discovery_scoring_v11.m`
- 调整 `runners/run_stage3_parametric_ga_seed_search_v1.m`
- 调整 `runners/run_stage3_build_ga_validation_manifest_v1.m`

**为什么改**

- 现在最影响“换 scoring / 换验证策略”的不是模型代码，而是阈值、权重、top-k、白名单、GA bounds 这些策略被埋在多个脚本里。
- `seed_discovery_scoring_calibration_v1.json` 已经证明 JSON policy 在这个仓库里是可接受的。
- 这一步可以让“换策略”变成改 policy，而不是复制新版本脚本。

**推荐做法**

- Python 端统一支持 `--policy-json`。
- CLI 参数仍保留，并允许覆盖 policy 默认值。
- `seed_discovery_scoring_calibration_v1.json` 继续保留，但只负责产出推荐值，不直接充当流程总配置。

**是否影响现有 v10 / v11 主流程**

- 低影响。
- 只要默认 policy 内容与当前硬编码值一致，现有 `v10 / v11` 行为不会改变。

**如何保证回滚简单**

- runner 可继续直接传旧参数。
- 即使 policy 文件出问题，也能退回脚本默认值。
- 不改模型 checkpoint 格式，不影响已训练模型。

### 阶段 3：把 stage3 dataset 的 stage 注册与特征增强规则集中管理

**建议改动文件**

- 新增 `stage3_dataset/dataset_stage_registry.py`
- 新增 `stage3_dataset/dataset_profiles.py`
- 调整 `stage3_dataset/build_v5_training_dataset.py`
- 调整 `stage3_dataset/build_v7_training_dataset.py`
- 视情况轻调 `stage3_dataset/build_v1_training_dataset.py`

**为什么改**

- 当前 dataset 构建是“上一版 import 下一版”的演化式复制，便于研究迭代，但不利于后续“换目标 / 换材料 / 追加新验证轮”。
- `STAGES`、`SURROGATE_CORE_STAGES`、`SPECIALCASE_SHAPE_FAMILIES`、`validation_round_index` 这些内容本质都是数据纳入策略，适合集中定义。
- 这一步对训练数据构建最有帮助，但不必碰模型训练逻辑本身。

**推荐做法**

- `build_v7_training_dataset.py` 仍保留为入口。
- 将“纳入哪些 stage”“每个 stage 的 baseline 方式”“是否带 manifest 补充字段”移到 registry/profile 中。
- 将“stage1 reference enrichment”保留为独立函数，但从 profile 决定是否启用。

**是否影响现有 v10 / v11 主流程**

- 中低影响。
- 会影响后续重建数据集和重训，但不会直接影响已经存在的 `v10 / v11` COMSOL runner。

**如何保证回滚简单**

- 旧版 `build_v7_training_dataset.py` 保留入口名和输出位置。
- registry 只负责喂参数；出现问题时可直接切回原本的 `STAGES` 常量定义。

### 阶段 4：把 stage4 validation 的配置和 runner 公共部分合并成共享 helper

**建议改动文件**

- 新增 `stage4_validation/build_stage4_validation_config.m`
- 新增 `stage4_validation/run_stage4_validation_from_manifest.m`
- 调整 `stage4_validation/get_stage4_validation_config_v10.m`
- 调整 `stage4_validation/get_stage4_validation_config_v11.m`
- 调整 `stage4_validation/get_stage4_validation_config_ga_v1.m`
- 调整 `runners/run_stage4_validation_ab_v10.m`
- 调整 `runners/run_stage4_validation_ab_v11.m`
- 调整 `runners/run_stage4_validation_ab_ga_v1.m`

**为什么改**

- `get_stage4_validation_config_v10.m`、`v11.m`、`ga_v1.m` 基本是同一模板。
- `run_stage4_validation_ab_v10.m`、`v11.m` 几乎是复制粘贴，只差 config 入口和少量报错标签。
- 这一层重复很重，但因为牵涉 COMSOL 执行，所以优先级放在 stage3 Python 抽象之后。

**推荐做法**

- 保留 `get_stage4_validation_config_v10.m` / `v11.m` / `ga_v1.m` 文件名。
- 这些文件改成向共享 builder 传入 `validationId`、manifest 路径、输出目录等最小差异参数。
- 共享 runner helper 统一处理 manifest 读取、resume、metadata attach、结果表输出、summary 写出。

**是否影响现有 v10 / v11 主流程**

- 中等影响。
- 这是最接近 COMSOL 执行的一层，建议只先覆盖 `v10 / v11 / ga_v1`，不要第一轮就回扫 `v1~v9`。

**如何保证回滚简单**

- 旧 runner 名称保持不变。
- 任一版本出问题，都可以仅恢复该版本 runner 和 config 文件，不影响其他版本。
- 不改 `evaluate_stage2_harmonics_refine_case_internal.m` 这类求解核心。

### 阶段 5：最后再把“物理 profile / 目标定义”做成显式 profile，而不是隐式常量

**建议改动文件**

- 新增 `stage2_harmonics_refine/get_physics_profile.m`
- 新增 `stage2_harmonics_refine/get_target_profile.m`
- 调整 `stage2_harmonics_refine/get_stage2_harmonics_refine_config.m`
- 视情况调整 `stage3_dataset/build_v1_training_dataset.py`
- 视情况调整 `stage4_validation/build_stage4_validation_config.m`

**为什么改**

- 真正决定“换目标 / 换材料”的，是这层物理 profile。
- 但这层也是最贴近研究结论的，过早抽象容易把当前论文主线搅乱。
- 因此建议最后做，而且只做“显式 profile 化”，不做“完全通用化”。

**推荐做法**

- 先把当前默认 profile 固化为 `soft_matrix_hard_inclusion + fixed_gap_band_3_4`。
- 新 profile 只允许在有限字段上切换：`materialCase`、`fixedGapBand`、`studyShiftHz`、`studyNeigs`、基线点族。
- 仍然保留当前默认 profile 为仓库主线。

**是否影响现有 v10 / v11 主流程**

- 中等偏高影响。
- 会影响 stage2/stage4 基线定义和 dataset 标签定义，因此必须放在最后。

**如何保证回滚简单**

- 默认 profile 名称和默认值必须与当前一致。
- 所有调用方不传 profile 时，行为等同当前仓库。
- 新 profile 仅以新增文件形式存在，不覆盖旧研究设定。

## 推荐优先抽象的“模块边界”

如果只做最小侵入式改造，建议优先建立下面 5 个共享边界：

1. `seed_discovery profile`
2. `scoring policy`
3. `manifest selection policy`
4. `dataset stage registry`
5. `stage4 validation config builder`

这 5 个边界可以覆盖“换目标、换材料、换 scoring、换验证策略”中的后三项，并为前两项留出接口，但不会强迫仓库立刻通用化。

## 不建议本轮做的事

- 不建议合并或删除现有 `v1~v11` 脚本。
- 不建议大规模移动目录。
- 不建议引入 Hydra、Pydantic、Click、完整实验管理框架。
- 不建议把 MATLAB/COMSOL 求解核心提前改造成插件式系统。
- 不建议把历史版本 runner 统一重写；先覆盖 `v10 / v11 / ga_v1` 即可。

## 建议的实际落地顺序

1. 先做阶段 1，解决 `v10 / v11` 的重复候选池与 manifest 构建。
2. 再做阶段 2，把策略参数从脚本里抽出来。
3. 然后做阶段 3，整理 dataset stage registry。
4. 确认 Python 侧稳定后，再做阶段 4 的 MATLAB stage4 helper。
5. 最后才做阶段 5 的 physics / target profile。

## 预期收益

- 新增一个 `v12` 候选线时，更接近“加一个 profile”而不是“复制 3 个脚本再手改路径”。
- 更换 scoring 或验证配额时，不需要同时改 Python 脚本和 MATLAB runner 命令串。
- 更换材料或目标时，能够明确知道要改的是 profile，而不是到处找常量。
- 现有 `main / v11` 路线仍然保持为仓库默认主线，不会被“模块化”反向稀释掉研究结论。
