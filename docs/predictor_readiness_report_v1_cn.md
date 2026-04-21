# Predictor Readiness Report V1

## 1. 目的

本报告用于回答一个非常具体的问题：

**当前冻结主线下的 target-band predictor，是否已经足以正式进入逆向设计主线，作为 shortlist / screening 前端使用？**

这里的判断标准不是“模型是不是完美”，而是：

- 它能不能把值得验证的候选排到前面
- 它能不能在 thesis band catalog 内保持可用
- 它的概率和分数是否至少具有基本可解释性
- 它是否已经足以支撑“predictor-guided inverse design”这一主线表述

本报告严格基于当前冻结主线：

- 冻结配置：
  - [targetband_mainline_freeze_v1.json](/d:/graduation_project/coad/prediction_targetband_param_v1/configs/targetband_mainline_freeze_v1.json)
- 数据集：
  - `windows_dense_v8_truth_plus_exploratory_aug_v1`
- 分类器：
  - RF
- 回归器：
  - HGB
- thesis band catalog：
  - `band140_180`
  - `band160_200`
  - `band180_220`
  - `band200_240`
  - `band220_260`
  - `band240_280`

分析输出目录：

- [predictor_readiness_v1](/d:/graduation_project/coad/data/analysis/predictor_readiness_v1)

## 2. 最终判断

**结论：通过。**

但这个“通过”是有边界的：

- **通过的部分**：已经足以作为 thesis band catalog 内逆向设计主线的 predictor front-end
- **保留的部分**：还不适合被表述成“对未见 band 具有很强外推能力的通用条件模型”

更准确地说：

**当前 predictor 已经具备进入 target-band inverse design mainline 的 readiness，但它的最佳定位仍然是 “catalog 内条件预测 + shortlist engine”，而不是“强连续-band extrapolator”。**

## 3. Family-CV 表现

这里看的是：

- 未见 `shape_family` 下，predictor 是否仍然稳定
- 这是当前逆向设计用途下最重要的主指标

来自：

- [readiness_summary.json](/d:/graduation_project/coad/data/analysis/predictor_readiness_v1/readiness_summary.json)

的 thesis catalog 汇总结果：

### 分类器（RF）

- rows: `5352`
- positive_rate: `0.7530`
- accuracy: `0.9396`
- precision: `0.9478`
- recall: `0.9734`
- f1: `0.9605`
- balanced_accuracy: `0.9050`

### 回归器（HGB）

- MAE: `0.0513`
- RMSE: `0.0862`
- R²: `0.8774`

### 解读

这组结果说明：

- 在 thesis catalog 内，predictor 对未见 family 的表现是足够稳定的
- RF 做 `open / not-open` screening 已经具备主线可用性
- HGB 做 cover ratio ranking 的 family-CV 表现也已经达到“可驱动逆向设计”的水平

这部分可以直接判定为：

**family-CV readiness: pass**

## 4. Leave-One-Band 表现

这里看的是：

- 当某个 band 完全不出现在训练 fold 中时，模型是否还能保持可用性

来自：

- [readiness_summary.json](/d:/graduation_project/coad/data/analysis/predictor_readiness_v1/readiness_summary.json)

的 thesis catalog 汇总结果：

### 分类器（RF）

- rows: `5352`
- accuracy: `0.6162`
- precision: `0.7557`
- recall: `0.7246`
- f1: `0.7398`
- balanced_accuracy: `0.5052`

### 回归器（HGB）

- MAE: `0.1044`
- RMSE: `0.1575`
- R²: `0.5908`

### 解读

这部分一定要谨慎解释。

先说结论：

- leave-one-band **没有塌掉**
- 但也**没有强到可以支撑“任意未见 band 泛化”**

尤其是分类器整体 `balanced_accuracy=0.5052`，如果只看这一行，会显得很差。  
但这里有两个背景必须同时说明：

1. thesis catalog 内不同 band 的正负样本极不均衡  
2. 一些 band 的正样本率非常高或非常低，导致整体 balanced accuracy 的解释力下降

所以这一项不能只看总体一行，必须结合逐 band 表现看。

## 5. 逐 Band 结果

相关表：

- [family_cv_classifier_by_band.csv](/d:/graduation_project/coad/data/analysis/predictor_readiness_v1/family_cv_classifier_by_band.csv)
- [leave_one_band_classifier_by_band.csv](/d:/graduation_project/coad/data/analysis/predictor_readiness_v1/leave_one_band_classifier_by_band.csv)
- [family_cv_regressor_by_band.csv](/d:/graduation_project/coad/data/analysis/predictor_readiness_v1/family_cv_regressor_by_band.csv)
- [leave_one_band_regressor_by_band.csv](/d:/graduation_project/coad/data/analysis/predictor_readiness_v1/leave_one_band_regressor_by_band.csv)

### 5.1 Family-CV 下的 thesis bands

分类器在 thesis bands 上整体是可用的，尤其：

- `band160_200`：`f1=1.0000`
- `band180_220`：`f1=0.9435`
- `band220_260`：`f1=0.9135`
- `band240_280`：`f1=0.9382`

回归器在 thesis bands 上：

- `band140_180`：`mae=0.0344`
- `band160_200`：`mae=0.0631`
- `band180_220`：`mae=0.0566`
- `band220_260`：`mae=0.0092`
- `band240_280`：`mae=0.0088`

说明：

- 在已定义 catalog 内，这条预测器主线对 band-dependent ranking 已经具备稳定性

### 5.2 Leave-One-Band 下的 thesis bands

这里最关键的是弱 band：

#### 分类器

- `band200_240`：`f1=0.0166`，`bal_acc=0.5976`
- `band220_260`：`f1=0.6890`，`bal_acc=0.5826`
- `band240_280`：`f1=0.2311`，`bal_acc=0.5653`

#### 回归器

- `band220_260`：`mae=0.0089`
- `band240_280`：`mae=0.0095`

这说明两件事：

1. 对完全留出的 band，分类器表现仍然不稳定，尤其 `band200_240 / band240_280` 依然难。
2. 但在高频稀疏 band 上，回归器并没有完全失效，说明 cover-ratio 信号并非不可迁移。

所以最稳的口径应该是：

**leave-one-band 说明模型具备一定 band 迁移能力，但还不足以支撑“强未见 band 泛化”主张。**

## 6. Top-k Shortlist 质量

这是本报告里最关键的一部分，因为逆向设计真正关心的是：

- 前 5、前 10、前 20 个候选是不是值得验证

相关表：

- [family_cv_topk_summary.csv](/d:/graduation_project/coad/data/analysis/predictor_readiness_v1/family_cv_topk_summary.csv)
- [leave_one_band_topk_summary.csv](/d:/graduation_project/coad/data/analysis/predictor_readiness_v1/leave_one_band_topk_summary.csv)
- [leave_one_band_topk_by_fold.csv](/d:/graduation_project/coad/data/analysis/predictor_readiness_v1/leave_one_band_topk_by_fold.csv)

这里的 shortlist score 用的是：

- `shortlist_score = cls_prob * max(reg_pred, 0)`

这和当前主线逻辑是一致的：

- 分类器先判断 likely-open
- 回归器再判断 cover ratio 大小

### Family-CV Top-k

以 thesis catalog 子集看：

- top-5 mean cover: `0.5821`
- top-10 mean cover: `0.5049`
- top-20 mean cover: `0.4043`
- top-50 mean cover: `0.3377`

对应的 mean cover lift 分别为：

- top-5: `+0.3642`
- top-10: `+0.2870`
- top-20: `+0.1864`
- top-50: `+0.1198`

这说明：

- predictor 选出来的前排候选，不只是“更可能开”，而是**真实 cover ratio 也明显更高**

### Leave-One-Band Top-k

以 thesis catalog 子集看：

- top-5 mean cover: `0.3926`
- top-10 mean cover: `0.3737`
- top-20 mean cover: `0.3537`
- top-50 mean cover: `0.3289`

对应 mean cover lift：

- top-5: `+0.1883`
- top-10: `+0.1694`
- top-20: `+0.1494`
- top-50: `+0.1246`

虽然比 family-CV 弱，但仍然是**稳定正提升**。

### 弱 Band 视角

在 leave-one-band 下看最难的 thesis bands：

- `band180_220`：
  - top-5 mean cover `0.4952`
  - 相对随机基线 lift `+0.3339`
- `band220_260`：
  - top-20 mean cover `0.0263`
  - 相对随机基线 lift `+0.0077`
- `band240_280`：
  - top-20 mean cover `0.0445`
  - 相对随机基线 lift `+0.0249`

弱 band 的绝对值仍然不高，但方向是对的：

- predictor 在最难 band 上仍能把更好的 cover 候选排到前面

所以这部分可以明确判为：

**top-k shortlist readiness: pass**

## 7. 概率校准与分数单调性

### 7.1 分类器概率校准

相关表：

- [family_cv_classifier_calibration.csv](/d:/graduation_project/coad/data/analysis/predictor_readiness_v1/family_cv_classifier_calibration.csv)
- [leave_one_band_classifier_calibration.csv](/d:/graduation_project/coad/data/analysis/predictor_readiness_v1/leave_one_band_classifier_calibration.csv)

以 family-CV 为例：

- 最低概率桶 `mean_pred_prob≈0.0138`，实际正例率 `≈0.0177`
- 中间概率桶 `mean_pred_prob≈0.9006`，实际正例率 `≈0.8983`
- 最高概率桶 `mean_pred_prob≈0.9996`，实际正例率 `≈0.9980`

说明：

- RF 的概率虽然不是专门校准过的，但已经具备基本可解释性
- 高概率桶对应高真实正例率，这对 shortlist screening 已经足够

### 7.2 回归器单调性

相关表：

- [family_cv_regressor_monotonicity.csv](/d:/graduation_project/coad/data/analysis/predictor_readiness_v1/family_cv_regressor_monotonicity.csv)
- [leave_one_band_regressor_monotonicity.csv](/d:/graduation_project/coad/data/analysis/predictor_readiness_v1/leave_one_band_regressor_monotonicity.csv)

以 family-CV 为例：

- 最低预测 cover 桶：`mean_pred≈0.0064`，`mean_true≈0.0157`
- 中间预测桶：`mean_pred≈0.2104`，`mean_true≈0.2152`
- 最高预测桶：`mean_pred≈0.5973`，`mean_true≈0.5932`

说明：

- HGB 的预测分数总体上具备比较好的单调性
- 这已经满足“higher predicted cover -> higher expected true cover”的优化前端要求

所以这部分可以判为：

**calibration / monotonicity readiness: pass**

## 8. 正式结论

基于以上证据，本报告给出正式判断：

### 结论 1

**当前 predictor 已经足以进入 thesis band catalog 内的逆向设计主线。**

原因是：

- family-CV 稳定
- top-k shortlist 质量明显优于随机/平均水平
- 概率与 cover 分数都具备基本可解释性

### 结论 2

**当前 predictor 的最佳角色是 shortlist engine，而不是最终裁判。**

也就是说：

- predictor 负责筛选和排序
- COMSOL 负责最终 refinement 和 validation

这正符合我们当前的 target-band inverse-design 主线定义。

### 结论 3

**当前还不适合把 predictor 写成“强未见 band extrapolation 模型”。**

因为：

- leave-one-band 仍然存在明显弱项
- `band200_240 / band240_280` 等难 band 在完全留出时仍不稳定

因此论文主张应继续保持为：

- **catalog 内条件预测与逆向设计**

而不是：

- 任意连续 band 的通用强外推

## 9. 最终 Readiness 判定

本报告的最终判定如下：

- family-CV：**pass**
- leave-one-band：**review**
- top-k shortlist：**pass**
- calibration / monotonicity：**pass**

综合结论：

**Predictor readiness = pass with boundary control**

也就是说：

**它已经足以进入逆向设计主线，但主张边界必须收在 thesis band catalog 内。**

## 10. 后续直接动作

基于本报告，下一步最自然的动作是：

1. 把 predictor 正式写成 inverse-design front-end
2. 用 canonical target-band cases 做主线展示
3. 做 predictor-guided line 与 baseline 的系统对照
4. 把弱 band coverage 继续作为 standing metric 跟踪

这也是为什么本报告应该被视为：

**“预测器足以进入逆向设计主线”的正式依据。**
