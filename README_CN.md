# COAD：目标频带声子晶体设计研究代码库

COAD 是一个面向二维声子晶体单胞目标频带设计的研究工作区。它不是打包好的终端软件，而是保留最终研究流程背后可追溯代码、配置和证据链的仓库。

最终论文主线是：

```text
COMSOL 频散物理真值
-> 目标频带条件预测
-> 真实 COMSOL-in-loop 遗传优化
-> 预测 Top5 / 随机候选 / GA 结果对比验证
-> 高频弱频带边界分析
```

## 方法边界

本项目不声称机器学习模型替代有限元计算。更准确的边界是：

- COMSOL 频散计算是物理真值来源。
- 预测模型只负责候选筛选和排序。
- 真实 COMSOL-in-loop GA 是优化基线。
- 最终性能结论必须回到 COMSOL 验证后的重叠宽度和覆盖率。
- 220-260 Hz 与 240-280 Hz 高频弱频带主要体现当前结构族和参数化空间的边界。

最终使用的六个目标频带为：

```text
140-180 Hz
160-200 Hz
180-220 Hz
200-240 Hz
220-260 Hz
240-280 Hz
```

## 仓库导览

仓库保留公开代码布局、公共脚本入口、历史路线归档和复现索引，便于检查或重新运行最终工作流。

建议先阅读：

- [项目结构](docs/project/PROJECT_STRUCTURE.md)
- [COMSOL 脚本索引](docs/project/COMSOL_SCRIPT_INDEX.md)
- [Runner 风险索引](docs/project/RUNNER_RISK_INDEX.md)
- [最终复现流程](docs/reproducibility/FINAL_RUNBOOK.md)
- [最终结果索引](docs/reproducibility/FINAL_RESULTS_INDEX.md)
- [数据集清单](docs/reproducibility/DATASET_MANIFEST.md)

公共入口现在放在 `scripts/`，包括数据集构建、模型训练、结果导出、COMSOL/GA 入口包装，以及论文图表和报告生成。

## 当前代码区域

| 模块 | 当前路径 | 作用 |
| --- | --- | --- |
| 几何生成 | `snake/`, `preprocess/` | 结构生成和参数化几何构造 |
| COMSOL 流程 | `model_core/`, `physics_pipeline/` | COMSOL 模型构建与物理真值流程 |
| 数据集 | `src/prediction/targetband_param/dataset/` | 目标频带数据集构建 |
| 预测模型 | `src/prediction/targetband_param/` | 条件分类、条件回归和推理工具 |
| 优化 | `optimization/real_comsol_ga/` | 真实 COMSOL-in-loop GA |
| 候选排序 | `src/optimization/seed_ranking/` | 候选池、Top-k 排序和验证清单 |
| 验证 | `stage4_validation/`, `src/shared/` | Stage4 验证配置、共享契约和 IO |
| 图表与报告 | `postprocess/`, `research_validation/` | 论文图表、表格和章节证据 |

旧的 `prediction_targetband_param_v1/`、`prediction_v*`、`shared/` 和 `optimization/seed_ranking/` 根目录已经改为轻量兼容入口，真实主线代码位于 `src/` 或历史归档位于 `archive/`。

## 数据和产物策略

仓库只追踪代码、配置、轻量报告和复现索引，不直接追踪大型生成结果。

本地忽略目录和文件包括：

- `data/`：COMSOL 输出、训练集、模型结果、验证清单。
- `output/`：论文 PDF、导出图、答辩素材。
- `tmp/`, `tmp_ppt_rebuild/`, `tmp_ppt_render/`：临时构建产物。
- `research_validation/` 下生成的 CSV、PNG、SVG、PDF、JSON 和 TXT 结果。

需要定位结果时，请查看 `docs/reproducibility/` 下的索引文档，不要把大文件直接提交进 Git。

## 环境

常用环境：

- Windows / PowerShell
- Python 3.12 或兼容 Python 3
- MATLAB
- COMSOL with MATLAB LiveLink
- 常用 Python 包：`numpy`, `pandas`, `matplotlib`, `scikit-learn`, `joblib`

机器相关路径请参考 `configs/local.example.json`，不要把个人机器路径硬编码进公开脚本。

## 安全检查

轻量检查命令：

```powershell
python scripts\check_project\check_public_layout.py
python -m unittest tests.test_thesis_mainline_smoke
```

这些检查不应启动大型 COMSOL 作业。运行任何可能启动 COMSOL 的脚本前，请先阅读：

- [COMSOL 脚本索引](docs/project/COMSOL_SCRIPT_INDEX.md)

## 许可证

当前尚未选择公开许可证。在项目作者正式添加 `LICENSE` 文件前，本仓库代码和论文材料默认按保留所有权利处理。

## 归档快照

清理前的基线已保留为 Git 标签：

- 标签：`defense-final-snapshot-2026`
