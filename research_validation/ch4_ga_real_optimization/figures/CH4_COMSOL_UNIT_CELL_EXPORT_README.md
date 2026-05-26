# 第4章 COMSOL 完整单胞图导出说明

本次导出基于六个目标频带 20 代真实 COMSOL-GA 的最优候选记录，重新构建 COMSOL 几何并导出完整单胞图。导出过程只构建几何，不重新运行频散求解，不改动原始 GA 数据。

- 拼图 PNG：`ch4_fig4_6_best_unit_cells_6bands_comsol.png`
- 拼图 SVG：`ch4_fig4_6_best_unit_cells_6bands_comsol.svg`
- 拼图 PDF：`ch4_fig4_6_best_unit_cells_6bands_comsol.pdf`
- 导出清单：`ch4_fig4_6_comsol_unit_cell_export_manifest.csv`
- 拼图字体：Microsoft YaHei

## 单图文件

| 目标频带 | shape_id | target_overlap_Hz | PNG | SVG | PDF |
| --- | --- | ---: | --- | --- | --- |
| 140–180 Hz | `ep172_step75_contour_xy` | 22.27 | `ch4_fig4_6_unit_cell_band140_180_comsol.png` | `ch4_fig4_6_unit_cell_band140_180_comsol.svg` | `ch4_fig4_6_unit_cell_band140_180_comsol.pdf` |
| 160–200 Hz | `ep206_step33_contour_xy` | 32.45 | `ch4_fig4_6_unit_cell_band160_200_comsol.png` | `ch4_fig4_6_unit_cell_band160_200_comsol.svg` | `ch4_fig4_6_unit_cell_band160_200_comsol.pdf` |
| 180–220 Hz | `ep206_step33_contour_xy` | 40.00 | `ch4_fig4_6_unit_cell_band180_220_comsol.png` | `ch4_fig4_6_unit_cell_band180_220_comsol.svg` | `ch4_fig4_6_unit_cell_band180_220_comsol.pdf` |
| 200–240 Hz | `ep253_step54_contour_xy` | 35.28 | `ch4_fig4_6_unit_cell_band200_240_comsol.png` | `ch4_fig4_6_unit_cell_band200_240_comsol.svg` | `ch4_fig4_6_unit_cell_band200_240_comsol.pdf` |
| 220–260 Hz | `ep248_step27_contour_xy` | 4.10 | `ch4_fig4_6_unit_cell_band220_260_comsol.png` | `ch4_fig4_6_unit_cell_band220_260_comsol.svg` | `ch4_fig4_6_unit_cell_band220_260_comsol.pdf` |
| 240–280 Hz | `ep248_step27_contour_xy` | 3.93 | `ch4_fig4_6_unit_cell_band240_280_comsol.png` | `ch4_fig4_6_unit_cell_band240_280_comsol.svg` | `ch4_fig4_6_unit_cell_band240_280_comsol.pdf` |

说明：单图为 MATLAB LiveLink 调用 COMSOL `mphgeom` 导出的几何视图；2×3 拼图由上述 COMSOL 导出 PNG 组版生成。