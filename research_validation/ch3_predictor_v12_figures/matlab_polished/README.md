# 第三章 MATLAB 精修图表说明

本目录中的图表由 `redraw_ch3_predictor_v12_polished.m` 生成，只读取既有第三章 v12 结果文件，不重新训练模型。

## 源数据文件

- Family-CV 分类结果：`D:\graduation_project\coad\data\analysis\predictor_readiness_v12_all_history_ga20_clean_v1\family_cv_classifier_by_band.csv`
- Band-LOO 分类结果：`D:\graduation_project\coad\data\analysis\predictor_readiness_v12_all_history_ga20_clean_v1\leave_one_band_classifier_by_band.csv`
- Family-CV 回归结果：`D:\graduation_project\coad\data\analysis\predictor_readiness_v12_all_history_ga20_clean_v1\family_cv_regressor_by_band.csv`
- Band-LOO 回归结果：`D:\graduation_project\coad\data\analysis\predictor_readiness_v12_all_history_ga20_clean_v1\leave_one_band_regressor_by_band.csv`
- Family-CV Top-k 结果：`D:\graduation_project\coad\data\analysis\predictor_readiness_v12_all_history_ga20_clean_v1\family_cv_topk_summary.csv`
- Band-LOO Top-k 结果：`D:\graduation_project\coad\data\analysis\predictor_readiness_v12_all_history_ga20_clean_v1\leave_one_band_topk_summary.csv`
- v12 数据集统计：`D:\graduation_project\coad\data\prediction_targetband_param_v1\v1\windows_dense_v12_all_history_ga20_clean_v1\dataset_info.json`

## 图表清单

| 图题建议 | 源数据文件 | MATLAB 脚本 | PNG | 矢量文件 |
| --- | --- | --- | --- | --- |
| 六个目标频带分类性能对比 | D:\graduation_project\coad\data\analysis\predictor_readiness_v12_all_history_ga20_clean_v1\family_cv_classifier_by_band.csv<br>D:\graduation_project\coad\data\analysis\predictor_readiness_v12_all_history_ga20_clean_v1\leave_one_band_classifier_by_band.csv | `D:\graduation_project\coad\research_validation\ch3_predictor_v12_figures\matlab_polished\redraw_ch3_predictor_v12_polished.m` | `D:\graduation_project\coad\research_validation\ch3_predictor_v12_figures\matlab_polished\ch3_matlab_band_classification_lines.png` | `D:\graduation_project\coad\research_validation\ch3_predictor_v12_figures\matlab_polished\ch3_matlab_band_classification_lines.pdf<br>D:\graduation_project\coad\research_validation\ch3_predictor_v12_figures\matlab_polished\ch3_matlab_band_classification_lines.svg` |
| 六个目标频带覆盖率回归 MAE 对比 | D:\graduation_project\coad\data\analysis\predictor_readiness_v12_all_history_ga20_clean_v1\family_cv_regressor_by_band.csv<br>D:\graduation_project\coad\data\analysis\predictor_readiness_v12_all_history_ga20_clean_v1\leave_one_band_regressor_by_band.csv | `D:\graduation_project\coad\research_validation\ch3_predictor_v12_figures\matlab_polished\redraw_ch3_predictor_v12_polished.m` | `D:\graduation_project\coad\research_validation\ch3_predictor_v12_figures\matlab_polished\ch3_matlab_band_regression_mae_lines.png` | `D:\graduation_project\coad\research_validation\ch3_predictor_v12_figures\matlab_polished\ch3_matlab_band_regression_mae_lines.pdf<br>D:\graduation_project\coad\research_validation\ch3_predictor_v12_figures\matlab_polished\ch3_matlab_band_regression_mae_lines.svg` |
| Top-k 候选平均真实覆盖率对比 | D:\graduation_project\coad\data\analysis\predictor_readiness_v12_all_history_ga20_clean_v1\family_cv_topk_summary.csv<br>D:\graduation_project\coad\data\analysis\predictor_readiness_v12_all_history_ga20_clean_v1\leave_one_band_topk_summary.csv | `D:\graduation_project\coad\research_validation\ch3_predictor_v12_figures\matlab_polished\redraw_ch3_predictor_v12_polished.m` | `D:\graduation_project\coad\research_validation\ch3_predictor_v12_figures\matlab_polished\ch3_matlab_topk_mean_cover_lines.png` | `D:\graduation_project\coad\research_validation\ch3_predictor_v12_figures\matlab_polished\ch3_matlab_topk_mean_cover_lines.pdf<br>D:\graduation_project\coad\research_validation\ch3_predictor_v12_figures\matlab_polished\ch3_matlab_topk_mean_cover_lines.svg` |
| 六个目标频带样本分布与平均覆盖率 | D:\graduation_project\coad\data\prediction_targetband_param_v1\v1\windows_dense_v12_all_history_ga20_clean_v1\dataset_info.json | `D:\graduation_project\coad\research_validation\ch3_predictor_v12_figures\matlab_polished\redraw_ch3_predictor_v12_polished.m` | `D:\graduation_project\coad\research_validation\ch3_predictor_v12_figures\matlab_polished\ch3_matlab_band_sample_distribution.png` | `D:\graduation_project\coad\research_validation\ch3_predictor_v12_figures\matlab_polished\ch3_matlab_band_sample_distribution.pdf<br>D:\graduation_project\coad\research_validation\ch3_predictor_v12_figures\matlab_polished\ch3_matlab_band_sample_distribution.svg` |

## 版式约定

- MATLAB 图宽约 14 cm，高约 8.6 cm。
- PNG 按 600 dpi 导出。
- PDF/SVG 按矢量格式导出，便于插入 Word 后继续排版。
- 配色采用低饱和蓝灰、棕灰和浅灰，避免 MATLAB 默认高饱和配色。
- 字体优先使用 Microsoft YaHei；如系统字体不可用，由 MATLAB 自动回退。
