# 第5章图5-7独立性与绘图来源审计报告

## 结论

- predicted_top5 和 GA20 是否 physical_key 完全不同：True
- 是否存在 shape_id 相同：True。180–220 Hz 与 200–240 Hz 相同，240–280 Hz 不同。
- 连续参数是否高度接近：False。按当前阈值 max_norm<0.03 且 L2<0.08 未触发近重复。
- 图5-7是否误用了同一份几何绘图数据：False。manifest 中 predicted_top5 与 GA20 输出文件不同。
- 是否存在 fallback 到 GA20/默认/矩形占位图：False。脚本使用各自 case row 的 Fourier 参数与 shape_file 调用 `validate_stage2_harmonics_geometry`。
- 当前图是否可以放入论文：True。
- 推荐方案：方案A更适合论文：保留 predicted Top5 vs GA20，并在图注/正文说明 180–220 Hz 与 200–240 Hz 的 predicted Top5 与 GA20 使用相同 shape_id，说明预测模型在独立候选集中识别到与真实 GA20 相似的高性能结构；同时强调 physical_key 与连续参数不同。

## 每个频带配对审计

| target_band | physical_key_same | shape_parameter_band_key_same | shape_id_same | shape_family_same | max_normalized_difference | normalized_l2_distance | near_duplicate | near_duplicate_by_parameters | pred_in_v12 | pred_in_ga20 | pred_shape_param_in_v12 | pred_shape_param_in_ga20 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 180–220 Hz | False | False | True | True | 0.114387 | 0.193472 | False | False | False | False | False | False |
| 200–240 Hz | False | False | True | True | 0.10167 | 0.189651 | False | False | False | False | False | False |
| 240–280 Hz | False | False | False | False | 0.693089 | 1.28696 | False | False | False | False | False | False |

## 候选身份表

完整表见 `ch5_fig7_candidate_identity_audit.csv`。下表保留核心字段：

| target_band | method | candidate_id | point_id | shape_id | shape_family | physical_key | overlap_Hz | cover_ratio | in_v12_training_set | in_ga20_history | in_existing_ch5 | shape_parameter_band_in_v12 | shape_parameter_band_in_ga20 | strict_holdout_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 180–220 Hz | predicted_top5 | strict_band180_220_c0436 | strict_band180_220_p0436 | ep206_step33_contour_xy | ep206 | strict_band180_220_p0436\|ep206_step33_contour_xy\|0.512846\|-0.070763\|-0.035257\|0.06783\|0.04\|-0.032867\|0.024405\|-0.000958\|-0.006368\|0.009497\|0.0137855\|180\|220 | 39.9681 | 0.999202 | False | False | False | False | False | True |
| 180–220 Hz | ga20 | band_catalog_ga_g18_i005 | rf09_h00_center | ep206_step33_contour_xy | ep206 | rf09_h00_center\|ep206_step33_contour_xy\|0.521718836065\|-0.0675023899767\|-0.0314114903924\|0.0645978949359\|0.04\|-0.023716\|0.03\|-0.00529150485032\|-0.00936275490473\|0.0089763\|0.013679\|180\|220 | 40 | 1 | True | True | True | True | True |  |
| 200–240 Hz | predicted_top5 | strict_band200_240_c0136 | strict_band200_240_p0136 | ep253_step54_contour_xy | ep253 | strict_band200_240_p0136\|ep253_step54_contour_xy\|0.53799\|-0.092125\|-0.033883\|0.065031\|0.031321\|-0.02153\|0.02261\|-0.010071\|0.00661\|-0.001227\|0.014\|200\|240 | 34.7976 | 0.86994 | False | False | False | False | False | True |
| 200–240 Hz | ga20 | band_catalog_ga_g19_i001 | rf09_h00_center | ep253_step54_contour_xy | ep253 | rf09_h00_center\|ep253_step54_contour_xy\|0.53923\|-0.088966\|-0.023716\|0.057717\|0.030829\|-0.016402\|0.028701\|-0.0094562\|0.0038602\|0.0019635\|0.014\|200\|240 | 35.2829 | 0.882073 | True | True | True | True | True |  |
| 240–280 Hz | predicted_top5 | strict_band240_280_c0459 | strict_band240_280_p0459 | ep209_step15_contour_xy | ep209 | strict_band240_280_p0459\|ep209_step15_contour_xy\|0.399316\|-0.078178\|-0.002313\|0.03928\|0.003314\|0.017098\|-1e-06\|0.002571\|0.000903\|-0.001732\|0.0118965\|240\|280 | 1.20465 | 0.0301162 | False | False | False | False | False | True |
| 240–280 Hz | ga20 | band_catalog_ga_g20_i005 | rf09_h00_center | ep248_step27_contour_xy | ep248 | rf09_h00_center\|ep248_step27_contour_xy\|0.523454594754\|-0.125770562941\|0.0151194794808\|0.0439746812646\|-0.0133200148559\|-0.0383491067751\|-0.0200634132466\|-0.02146\|-0.00846025561394\|-0.0198177883348\|0.01\|240\|280 | 3.93445 | 0.0983613 | True | True | True | True | True |  |

## 参数距离表

完整表见 `parameter_distance_table.csv`。下表为每个频带的归一化距离摘要：

| target_band | shape_id_same | shape_family_same | max_normalized_difference | normalized_l2_distance | near_duplicate | near_duplicate_by_parameters |
| --- | --- | --- | --- | --- | --- | --- |
| 180–220 Hz | True | True | 0.114387 | 0.193472 | False | False |
| 200–240 Hz | True | True | 0.10167 | 0.189651 | False | False |
| 240–280 Hz | False | False | 0.693089 | 1.28696 | False | False |

## 绘图来源检查

完整表见 `ch5_fig7_plotting_source_audit.csv`。

| target_band | method | candidate_id | shape_id | shape_file_input | unit_cell_png | unit_cell_status | uses_method_specific_output_file | geometry_png_duplicated | shape_file_duplicated_within_band | export_uses_case_row_params | export_fallback_to_default_or_ga20 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 180–220 Hz | predicted_top5 | strict_band180_220_c0436 | ep206_step33_contour_xy | D:\graduation_project\coad\data\shape_contours\ep206_step33_contour_xy.csv | D:\graduation_project\coad\research_validation\ch5_strict_holdout_validation\figures\unit_cell_redraw_exports\ch5_unit_cell_band180_220_predicted_top5.png | ok | True | False | True | True | False |
| 180–220 Hz | ga20 | band_catalog_ga_g18_i005 | ep206_step33_contour_xy | D:\graduation_project\coad\data\shape_contours\ep206_step33_contour_xy.csv | D:\graduation_project\coad\research_validation\ch5_strict_holdout_validation\figures\unit_cell_redraw_exports\ch5_unit_cell_band180_220_ga20.png | ok | True | False | True | True | False |
| 200–240 Hz | predicted_top5 | strict_band200_240_c0136 | ep253_step54_contour_xy | D:\graduation_project\coad\data\shape_contours\ep253_step54_contour_xy.csv | D:\graduation_project\coad\research_validation\ch5_strict_holdout_validation\figures\unit_cell_redraw_exports\ch5_unit_cell_band200_240_predicted_top5.png | ok | True | False | True | True | False |
| 200–240 Hz | ga20 | band_catalog_ga_g19_i001 | ep253_step54_contour_xy | D:\graduation_project\coad\data\shape_contours\ep253_step54_contour_xy.csv | D:\graduation_project\coad\research_validation\ch5_strict_holdout_validation\figures\unit_cell_redraw_exports\ch5_unit_cell_band200_240_ga20.png | ok | True | False | True | True | False |
| 240–280 Hz | predicted_top5 | strict_band240_280_c0459 | ep209_step15_contour_xy | D:\graduation_project\coad\data\shape_contours\ep209_step15_contour_xy.csv | D:\graduation_project\coad\research_validation\ch5_strict_holdout_validation\figures\unit_cell_redraw_exports\ch5_unit_cell_band240_280_predicted_top5.png | ok | True | False | False | True | False |
| 240–280 Hz | ga20 | band_catalog_ga_g20_i005 | ep248_step27_contour_xy | D:\graduation_project\coad\data\shape_contours\ep248_step27_contour_xy.csv | D:\graduation_project\coad\research_validation\ch5_strict_holdout_validation\figures\unit_cell_redraw_exports\ch5_unit_cell_band240_280_ga20.png | ok | True | False | False | True | False |

## 解释建议

180–220 Hz 和 200–240 Hz 中 predicted Top5 与 GA20 的 shape_id 相同，因此单胞轮廓形态会非常接近；但 point_id、physical_key 和 Fourier 连续参数不同，且 predicted_top5 未命中 v12、GA20 或旧第5章候选集合，也未命中不含 point_id 的 shape-parameter-band key。这里更像是预测模型在 strict_holdout 候选池中找到了与 GA20 同结构族/同离散轮廓但连续参数不同的高性能邻域，而不是抄用了 GA20 候选。

若担心读者把“形态接近”误解为重复样本，建议在图注中补一句：`其中 180–220 Hz 与 200–240 Hz 的预测候选和 GA20 最优候选具有相同离散轮廓编号，但 Fourier 连续参数与 physical_key 不同，属于独立候选集中搜索到的相近高性能结构。`