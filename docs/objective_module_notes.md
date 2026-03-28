# Objective Module Notes

## 本次改动目标

这次重构只做 Python 侧的“小规模目标函数可插拔”，核心原则是：

- 默认行为不变
- 默认 objective 仍然是 `gap34_gain_Hz`
- 不改 MATLAB / COMSOL 目标提取主链
- 不强行把所有 legacy 脚本一次性抽象完

## 已完成

### 1. 新增 objective registry

新增根目录文件：

- `objective_registry.py`

当前 registry 中可用 objective：

- `gap34_gain_Hz`
- `gap34_Hz`
- `gap34_rel`
- `max_gap_Hz`

兼容保留：

- `gap34_gain_rel`

其中默认 objective 仍是：

- `gap34_gain_Hz`

### 2. 回归训练入口改为通过 objective registry 读取

已接入文件：

- `stage3_training/train_mlp_regressor_v1.py`
- `stage3_training/train_mlp_regressor_v2.py`
- `stage3_training/train_mlp_regressor_v3.py`
- `stage3_training/train_mlp_regressor_v4.py`
- `stage3_training/train_mlp_regressor_v5.py`
- `stage3_training/train_mlp_regressor_v6.py`
- `stage3_training/train_mlp_regressor_v7.py`

现在这些脚本不再各自写死一份 target choices，而是统一从 registry 读取。

默认输出行为没有变：

- 默认 target 仍然是 `gap34_gain_Hz`
- 默认 run-name 仍保留原命名习惯

### 3. dataset metadata 不再把 surrogate target 写死

已接入文件：

- `stage3_dataset/build_v1_training_dataset.py`
- `stage3_dataset/build_v2_training_dataset.py`
- `stage3_dataset/build_v3_training_dataset.py`
- `stage3_dataset/build_v4_training_dataset.py`
- `stage3_dataset/build_v5_training_dataset.py`
- `stage3_dataset/build_v6_training_dataset.py`
- `stage3_dataset/build_v7_training_dataset.py`

这一步没有改数据列本身，只改了任务说明元数据：

- `build_dataset_info()` 里的 surrogate task target 现在读取 `DEFAULT_OBJECTIVE_NAME`
- dataset info 里新增：
  - `default_objective`
  - `supported_objectives`

### 4. seed discovery scoring 改成 objective aware

已接入文件：

- `stage3_training/run_seed_discovery_scoring_v7.py`

新增参数：

- `--objective`

默认仍是：

- `gap34_gain_Hz`

当前行为：

- 默认情况下，输出列仍会包含原来的 `surrogate_pred_gap34_gain_Hz`
- 同时新增通用列：
  - `surrogate_objective_name`
  - `surrogate_prediction_column`
  - `surrogate_pred_objective_value`

这样做的目的，是在不破坏默认 CSV 兼容性的前提下，为后续 objective 切换留接口。

## 最小切换示例

### 示例 1：训练 `max_gap_Hz` surrogate

```powershell
python stage3_training/train_mlp_regressor_v7.py `
  --dataset data/ml_dataset/v7/tasks/surrogate_regression_core_v7.csv `
  --feature-preset surrogate_seed_discovery `
  --target max_gap_Hz `
  --run-name mlp_max_gap_surrogate_v7_full
```

### 示例 2：用 `max_gap_Hz` 做 seed discovery scoring

```powershell
python stage3_training/run_seed_discovery_scoring_v7.py `
  --dataset data/ml_dataset/v10/candidate_pool_v10_seed_only_refined/candidate_pool_v10.csv `
  --reg-run-root data/ml_runs/mlp_max_gap_surrogate_v7_full `
  --objective max_gap_Hz `
  --run-name candidate_pool_seed_discovery_v10_max_gap
```

注意：

- `--objective` 必须和你传入的 regressor checkpoint target 一致
- scoring 脚本现在会校验 checkpoint 内部保存的 `target`

## 默认兼容性说明

这次改动特意保持了下面几件事不变：

- 默认训练 target 还是 `gap34_gain_Hz`
- 默认 seed discovery scoring 还是按 `gap34_gain_Hz` surrogate 列工作
- 现有默认 run-name、默认输出路径、默认 CSV 文件名都没有改

所以：

- 旧 runner 不传新参数时，行为应与之前一致

## 本轮明确没有硬改的地方

以下内容我刻意没有在这轮强行抽象，避免把默认主流程搅乱：

- `stage3_training/build_validation_manifest_v10.py`
- `stage3_training/build_validation_manifest_v11.py`
- `stage3_training/run_parametric_ga_seed_search_v1.py`
- `stage3_training/build_ga_validation_manifest_v1.py`
- `stage3_training/calibrate_seed_discovery_scoring_v1.py`
- `stage3_training/run_cascade_surrogate_v*.py`
- 更老的 candidate pool / cascade legacy 脚本

## TODO

### TODO 1：manifest 侧读取 objective-aware surrogate 列

当前 manifest builder 默认仍按旧的 surrogate 列约定工作。

原因：

- 这部分已经和 MATLAB stage4 validation manifest 格式耦合
- 这轮先保证 Python 侧 objective module 成型，不直接改 stage4 接口

### TODO 2：GA / calibration 侧统一读取 objective policy

当前 GA 和 calibration 逻辑仍然更偏向：

- `gap34_gain_Hz`

原因：

- 它们不只是“预测目标列”问题，还涉及 fitness 定义、正样本判据、历史验证回放口径

### TODO 3：目标方向与阈值语义进一步抽象

现在 registry 假设的是一类“越大越好”的 objective。

未来如果引入：

- 目标频带中心偏差
- 峰值抑制
- 惩罚项

还需要继续抽象：

- optimize direction
- positive threshold rule
- rank direction / gate rule

## 验证

本轮已做的最小验证：

- 对新增/修改的 Python 文件执行了 `python -m py_compile`
- 通过语法检查的范围包括：
  - `objective_registry.py`
  - `stage3_training/train_mlp_regressor_v1.py` 到 `v7.py`
  - `stage3_training/run_seed_discovery_scoring_v7.py`
  - `stage3_dataset/build_v1_training_dataset.py` 到 `v7.py`
