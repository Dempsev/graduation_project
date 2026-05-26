# 第5章图5-7/图5-8重绘数据检查报告

## 绘图原则

- 单胞结构图由 MATLAB/COMSOL 几何生成流程 `export_ch5_pred_vs_ga20_unit_cells_v1.m` 重新导出，Python 仅负责排版。
- 频散曲线均来自真实 COMSOL 导出的 `tbl1` 数据，不使用占位图或简化矩形。

## 候选与数据路径

| target_band | method | candidate_id | shape_id | shape_family | overlap_Hz | cover_ratio | geometry_png | dispersion_tbl1_csv | geometry_status | dispersion_exists |
| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- |
| 180–220 Hz | predicted_top5 | strict_band180_220_c0436 | ep206_step33_contour_xy | ep206 | 39.968 | 0.999 | D:\graduation_project\coad\research_validation\ch5_strict_holdout_validation\figures\unit_cell_redraw_exports\ch5_unit_cell_band180_220_predicted_top5.png | D:\graduation_project\coad\data\comsol_batch\ch5_strict_holdout_validation_top5_random5\tbl1_exports\strict_band180_220_c0436_tbl1.csv | ok | True |
| 180–220 Hz | ga20 | band_catalog_ga_g18_i005 | ep206_step33_contour_xy | ep206 | 40.000 | 1.000 | D:\graduation_project\coad\research_validation\ch5_strict_holdout_validation\figures\unit_cell_redraw_exports\ch5_unit_cell_band180_220_ga20.png | D:\graduation_project\coad\data\comsol_batch\comsol_in_loop_targetband180_220_overlap_ga_v1\tbl1_exports\comsol_in_loop_targetband180_220_overlap_ga_v1__g18__i005__ep206_step33_contour_xy_tbl1.csv | ok | True |
| 200–240 Hz | predicted_top5 | strict_band200_240_c0136 | ep253_step54_contour_xy | ep253 | 34.798 | 0.870 | D:\graduation_project\coad\research_validation\ch5_strict_holdout_validation\figures\unit_cell_redraw_exports\ch5_unit_cell_band200_240_predicted_top5.png | D:\graduation_project\coad\data\comsol_batch\ch5_strict_holdout_validation_top5_random5\tbl1_exports\strict_band200_240_c0136_tbl1.csv | ok | True |
| 200–240 Hz | ga20 | band_catalog_ga_g19_i001 | ep253_step54_contour_xy | ep253 | 35.283 | 0.882 | D:\graduation_project\coad\research_validation\ch5_strict_holdout_validation\figures\unit_cell_redraw_exports\ch5_unit_cell_band200_240_ga20.png | D:\graduation_project\coad\data\comsol_batch\comsol_in_loop_thesis_band200_240_overlap_ga_v1\tbl1_exports\comsol_in_loop_thesis_band200_240_overlap_ga_v1__g19__i001__ep253_step54_contour_xy_tbl1.csv | ok | True |
| 240–280 Hz | predicted_top5 | strict_band240_280_c0459 | ep209_step15_contour_xy | ep209 | 1.205 | 0.030 | D:\graduation_project\coad\research_validation\ch5_strict_holdout_validation\figures\unit_cell_redraw_exports\ch5_unit_cell_band240_280_predicted_top5.png | D:\graduation_project\coad\data\comsol_batch\ch5_strict_holdout_validation_top5_random5\tbl1_exports\strict_band240_280_c0459_tbl1.csv | ok | True |
| 240–280 Hz | ga20 | band_catalog_ga_g20_i005 | ep248_step27_contour_xy | ep248 | 3.934 | 0.098 | D:\graduation_project\coad\research_validation\ch5_strict_holdout_validation\figures\unit_cell_redraw_exports\ch5_unit_cell_band240_280_ga20.png | D:\graduation_project\coad\data\comsol_batch\comsol_in_loop_thesis_band240_280_overlap_ga_v1\tbl1_exports\comsol_in_loop_thesis_band240_280_overlap_ga_v1__g20__i005__ep248_step27_contour_xy_tbl1.csv | ok | True |

## MATLAB/COMSOL 单胞导出

- 是否成功调用 MATLAB 绘制真实单胞：True
- COMSOL 单胞导出 manifest：`D:\graduation_project\coad\research_validation\ch5_strict_holdout_validation\ch5_pred_vs_ga20_unit_cell_export_manifest.csv`

## 频散数据检查

- 是否成功找到所有频散曲线数据：True
- 若某个候选缺少几何或频散数据，本报告会在上表中显示 `False` 或 `failed`；本次未使用任何矩形示意或假图顶替。

## 输出图件

- 图5-7 单胞结构对比:
  - png: `D:\graduation_project\coad\research_validation\ch5_strict_holdout_validation\figures\ch5_strict_fig7_unit_cells_pred_vs_ga20_redraw.png`
  - svg: `D:\graduation_project\coad\research_validation\ch5_strict_holdout_validation\figures\ch5_strict_fig7_unit_cells_pred_vs_ga20_redraw.svg`
  - pdf: `D:\graduation_project\coad\research_validation\ch5_strict_holdout_validation\figures\ch5_strict_fig7_unit_cells_pred_vs_ga20_redraw.pdf`
- 图5-8 频散曲线对比:
  - png: `D:\graduation_project\coad\research_validation\ch5_strict_holdout_validation\figures\ch5_strict_fig8_dispersion_pred_vs_ga20_redraw.png`
  - svg: `D:\graduation_project\coad\research_validation\ch5_strict_holdout_validation\figures\ch5_strict_fig8_dispersion_pred_vs_ga20_redraw.svg`
  - pdf: `D:\graduation_project\coad\research_validation\ch5_strict_holdout_validation\figures\ch5_strict_fig8_dispersion_pred_vs_ga20_redraw.pdf`