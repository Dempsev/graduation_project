# Fourier-only 对比实验最终优化几何模型图

本目录记录 3 个高频目标频段中，Fourier-only GA20 与当前组合模型 GA20 的最终最佳个体几何导出结果。
导出过程只重建 COMSOL 几何模型，不重新运行频散求解。

- 对比拼图 PNG：`figures\ch5_fourier_only_ablation_final_geometry_compare.png`
- 对比拼图 SVG：`figures\ch5_fourier_only_ablation_final_geometry_compare.svg`
- 对比拼图 PDF：`figures\ch5_fourier_only_ablation_final_geometry_compare.pdf`
- 单图目录：`figures\geometry_exports`
- 导出清单：`fourier_only_ablation_geometry_export_manifest.csv`
- 个体清单：`fourier_only_ablation_geometry_cases.csv`

| 目标频段 | 方法 | overlap_Hz | shape_id | generation | PNG | SVG | PDF |
| --- | --- | ---: | --- | ---: | --- | --- | --- |
| 200-240 Hz | 仅傅里叶边界 GA20 | 34.364 | `pas253_step36_contour_xy` | 19 | `ch5_fourier_ablation_unit_cell_band200_240_fourier_only_ga20.png` | `ch5_fourier_ablation_unit_cell_band200_240_fourier_only_ga20.svg` | `ch5_fourier_ablation_unit_cell_band200_240_fourier_only_ga20.pdf` |
| 200-240 Hz | 当前模型 GA20 | 35.283 | `ep253_step54_contour_xy` | 19 | `ch5_fourier_ablation_unit_cell_band200_240_combined_ga20.png` | `ch5_fourier_ablation_unit_cell_band200_240_combined_ga20.svg` | `ch5_fourier_ablation_unit_cell_band200_240_combined_ga20.pdf` |
| 220-260 Hz | 仅傅里叶边界 GA20 | 7.783 | `pbi253_step24_contour_xy` | 20 | `ch5_fourier_ablation_unit_cell_band220_260_fourier_only_ga20.png` | `ch5_fourier_ablation_unit_cell_band220_260_fourier_only_ga20.svg` | `ch5_fourier_ablation_unit_cell_band220_260_fourier_only_ga20.pdf` |
| 220-260 Hz | 当前模型 GA20 | 4.098 | `ep248_step27_contour_xy` | 20 | `ch5_fourier_ablation_unit_cell_band220_260_combined_ga20.png` | `ch5_fourier_ablation_unit_cell_band220_260_combined_ga20.svg` | `ch5_fourier_ablation_unit_cell_band220_260_combined_ga20.pdf` |
| 240-280 Hz | 仅傅里叶边界 GA20 | 2.922 | `pne130_step12_contour_xy` | 20 | `ch5_fourier_ablation_unit_cell_band240_280_fourier_only_ga20.png` | `ch5_fourier_ablation_unit_cell_band240_280_fourier_only_ga20.svg` | `ch5_fourier_ablation_unit_cell_band240_280_fourier_only_ga20.pdf` |
| 240-280 Hz | 当前模型 GA20 | 3.934 | `ep248_step27_contour_xy` | 20 | `ch5_fourier_ablation_unit_cell_band240_280_combined_ga20.png` | `ch5_fourier_ablation_unit_cell_band240_280_combined_ga20.svg` | `ch5_fourier_ablation_unit_cell_band240_280_combined_ga20.pdf` |
