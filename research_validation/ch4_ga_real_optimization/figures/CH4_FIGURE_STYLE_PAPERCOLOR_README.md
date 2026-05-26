# 第4章统计图统一论文配色版本说明

本目录中的 `_papercolor` 文件为第4章统计图的统一论文插图风格版本。所有图均基于已有 CSV 与 20 代 GA 历史结果重新绘制，未重新运行 COMSOL，未改动原始 GA 数据。

## 统一规范

- 字体：Microsoft YaHei；若环境支持，中文优先 Microsoft YaHei / SimHei。
- 标题字号：12；坐标轴标签字号：11；刻度字号：10；图例字号：9。
- 背景：白色。
- 网格线：仅保留 y 方向浅灰网格线 `#D9D9D9`，线宽 0.5。
- 坐标轴和文字：`#222222`。
- 目标频带标签：`140–180 Hz`、`160–200 Hz`、`180–220 Hz`、`200–240 Hz`、`220–260 Hz`、`240–280 Hz`。
- 柱状图尺寸：`figsize=(6.0, 3.6)`；收敛曲线尺寸：`figsize=(6.8, 3.8)`；PNG 分辨率 300 dpi。

## 配色

| 名称 | 色值 |
| --- | --- |
| 主蓝色 | `#4E79A7` |
| 辅助橙色 | `#F28E2B` |
| 辅助绿色 | `#59A14F` |
| 辅助红色 | `#E15759` |
| 辅助紫色 | `#B07AA1` |
| 辅助青色 | `#76B7B2` |
| 浅蓝 | `#A0CBE8` |
| 深蓝 | `#1F4E79` |

## 图文件清单

| 论文图号 | 图名 | 推荐插入 Word 的 PNG | SVG | PDF |
| --- | --- | --- | --- | --- |
| 图4-3 | 六个目标频带 GA 收敛曲线 | `ch4_fig4_3_ga_convergence_20gen_papercolor.png` | `ch4_fig4_3_ga_convergence_20gen_papercolor.svg` | `ch4_fig4_3_ga_convergence_20gen_papercolor.pdf` |
| 图4-4 | 不同目标频带最优目标频带重叠宽度对比 | `ch4_fig4_4_best_overlap_bar_20gen_papercolor.png` | `ch4_fig4_4_best_overlap_bar_20gen_papercolor.svg` | `ch4_fig4_4_best_overlap_bar_20gen_papercolor.pdf` |
| 图4-5 | 成功求解率与有效候选比例 | `ch4_fig4_5_success_active_rates_20gen_papercolor.png` | `ch4_fig4_5_success_active_rates_20gen_papercolor.svg` | `ch4_fig4_5_success_active_rates_20gen_papercolor.pdf` |
| 图4-8 | 12代与20代最优目标频带重叠宽度对比 | `ch4_ga_12gen_vs_20gen_overlap_papercolor.png` | `ch4_ga_12gen_vs_20gen_overlap_papercolor.svg` | `ch4_ga_12gen_vs_20gen_overlap_papercolor.pdf` |
