# 第4章柱状图配色方案对比说明

本次仅重画第4章三张柱状统计图，未修改收敛曲线图，未重新运行 COMSOL，未改动原始 GA 数据。

- 中文字体：Microsoft YaHei
- 是否检测到中文字体缺失：否
- 图尺寸：`figsize=(6.2, 3.7)`；PNG 分辨率：300 dpi。
- 网格线：仅保留 y 方向浅灰网格线 `#E6E6E6`，线宽 0.6，alpha=0.8。
- 坐标轴：去除顶部和右侧边框，左侧和底部边框使用 `#333333`，线宽 0.8。

## 配色方案

### 方案 B：Okabe-Ito 科研色盲友好版

| 颜色 | 色值 |
| --- | --- |
| 蓝色 | `#0072B2` |
| 橙色 | `#E69F00` |
| 天蓝 | `#56B4E9` |
| 蓝绿 | `#009E73` |
| 朱红 | `#D55E00` |
| 紫色 | `#CC79A7` |
| 深灰文字 | `#333333` |
| 浅灰网格 | `#E6E6E6` |

### 方案 C：莫兰迪低饱和版

| 颜色 | 色值 |
| --- | --- |
| 雾蓝 | `#7895B2` |
| 沙橙 | `#D8A47F` |
| 鼠尾草绿 | `#9CAF88` |
| 灰紫 | `#A69CAC` |
| 砖红 | `#B56576` |
| 青灰 | `#8AA6A3` |
| 浅雾蓝 | `#B7C9D9` |
| 深灰文字 | `#333333` |
| 浅灰网格 | `#E6E6E6` |

## 图文件清单

| 方案 | 论文图号 | 图名 | 推荐插入 Word 的 PNG | SVG | PDF |
| --- | --- | --- | --- | --- | --- |
| 方案 B | 图4-4 | 不同目标频带最优重叠宽度对比 | `ch4_fig4_4_best_overlap_bar_20gen_okabe.png` | `ch4_fig4_4_best_overlap_bar_20gen_okabe.svg` | `ch4_fig4_4_best_overlap_bar_20gen_okabe.pdf` |
| 方案 B | 图4-5 | 成功求解率与有效候选比例 | `ch4_fig4_5_success_active_rates_20gen_okabe.png` | `ch4_fig4_5_success_active_rates_20gen_okabe.svg` | `ch4_fig4_5_success_active_rates_20gen_okabe.pdf` |
| 方案 B | 图4-8 | 12代与20代最优重叠宽度对比 | `ch4_ga_12gen_vs_20gen_overlap_okabe.png` | `ch4_ga_12gen_vs_20gen_overlap_okabe.svg` | `ch4_ga_12gen_vs_20gen_overlap_okabe.pdf` |
| 方案 C | 图4-4 | 不同目标频带最优重叠宽度对比 | `ch4_fig4_4_best_overlap_bar_20gen_morandi.png` | `ch4_fig4_4_best_overlap_bar_20gen_morandi.svg` | `ch4_fig4_4_best_overlap_bar_20gen_morandi.pdf` |
| 方案 C | 图4-5 | 成功求解率与有效候选比例 | `ch4_fig4_5_success_active_rates_20gen_morandi.png` | `ch4_fig4_5_success_active_rates_20gen_morandi.svg` | `ch4_fig4_5_success_active_rates_20gen_morandi.pdf` |
| 方案 C | 图4-8 | 12代与20代最优重叠宽度对比 | `ch4_ga_12gen_vs_20gen_overlap_morandi.png` | `ch4_ga_12gen_vs_20gen_overlap_morandi.svg` | `ch4_ga_12gen_vs_20gen_overlap_morandi.pdf` |

## 使用建议

- 方案 B 色彩区分度更强，更适合强调不同统计量之间的对比。
- 方案 C 饱和度更低、版面更柔和，更适合正文中连续插入多张统计图。
- 若论文整体已有较多蓝色系图件，优先考虑方案 B；若希望第4章图面更统一克制，优先考虑方案 C。