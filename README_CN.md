# 毕业设计
## k–amplitude 相关能带结构分析（COMSOL + MATLAB + Python）

本仓库用于工程力学本科毕设：研究**机械超材料**在不同激励幅值下的**k–amplitude 相关能带结构**。工作流覆盖了 COMSOL 建模与参数化扫频、MATLAB 批处理导出、Python 后处理与可视化。

---

## 项目背景
机械超材料的带隙特性与几何参数和激励幅值密切相关。本项目使用 COMSOL 进行本征频率计算，并通过参数化 sweep 得到不同 k 路径与幅值条件下的频散数据，随后用 Python 进行清洗、整理与绘图。

---

## 最近工作进展
- COMSOL 建模流程脚本集中在 `model_core/`（00–07），入口为 `create_open_00.m`。
- 批处理运行脚本集中在 `runners/`，主入口为 `main_batch.m`。
- Python 预处理与后处理分别放在 `preprocess/` 与 `postprocess/`。

---

## 仓库结构
```text
coad/
├─ model_core/                 # COMSOL MATLAB 核心建模函数（00–07）
├─ runners/                    # MATLAB 运行脚本（单次/批量）
│  └─ legacy_run/              # 旧脚本保留参考
├─ preprocess/                 # Python 预处理
├─ postprocess/                # Python 后处理
├─ data/                       # 输入/输出数据与模型
├─ README.md
└─ README_CN.md
```

---

## 运行环境
- COMSOL Multiphysics 6.3（建模与求解）
- MATLAB（批处理与导出）
- Python 3.x（后处理）
  - numpy
  - pandas
  - matplotlib

---

## 使用流程（推荐）
1. **COMSOL 建模**
   - 运行 `model_core/create_open_00.m` 生成基础模型。
2. **参数化 sweep + 导出**
   - 运行 `runners/main_batch.m`（推荐）。
   - CSV 输出在 `data/` 下。
3. **Python 后处理**
   - 使用 `data/` 中的 CSV，必要时修改路径；
   - 运行：
     ```bash
     python postprocess/k_amp_analyse.py
     ```

---

## 快速开始（按当前结构）
1. **生成基础模型**
   - 在 MATLAB 中运行：
     ```matlab
     run('model_core/create_open_00.m')
     ```
   - 会在 `data/` 下保存 `mother_rebuild.mph`。
2. **扫频并导出 CSV**
   - 在 MATLAB 中运行：
     ```matlab
     run('runners/main_batch.m')
     ```
3. **查看输出**
   - `data/batch_out/band_k_a1.csv`
4. **Python 后处理**
   - 需要时修改 `postprocess/k_amp_analyse*.py` 中的 CSV 路径，然后运行：
     ```bash
     python postprocess/k_amp_analyse.py
     ```

---

## 常见问题排查
- **CSV 为空或全 0**
  - 确认全局评估 (`gev`) 绑定到最新的数据集 (`dsetX`)。
  - 导出前清除表缓存（`clearTableData`）并重新运行 `gev`。
- **扫频结果卡在固定幅值（如 0.45）**
  - 同时更新 `k` 与 `amp` 的扫频列表。
  - 确认 `gev` 使用最新数据集并写入正确的表格。
- **扫频后没有新的 dataset**
  - 检查 `std1` 是否真正运行、参数化功能是否启用。
  - 在 MATLAB 中用 `model.result.dataset.tags()` 查看数据集标签。
- **导出的 CSV 列不正确**
  - 确认评估表达式（如 `freq` 或 `solid.freq`）与模型一致。
  - 重新创建临时 `gev` 与 `tbl`，避免隐藏 GUI 设置干扰。
- **COMSOL server 相关问题**
  - 使用 server 时需先 `mphstart()` 再加载模型。

---

## 输出说明
Python 脚本会自动完成：
- 清洗 COMSOL 导出的原始 CSV（含注释行）
- 复数频率格式转换并提取实部
- 按幅值整理 band 数据
- 绘制能带结构图

输出文件默认保存在 `post_out/`（由脚本自动创建）。

---

## 作者
- XuanCheng Su
- Engineering Mechanics, Undergraduate
