from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager


ROOT = Path(__file__).resolve().parents[2]
BASE_DIR = ROOT / "research_validation" / "ch4_ga_real_optimization"
FIG_DIR = BASE_DIR / "figures"

COLORS = {
    "blue": "#4E79A7",
    "orange": "#F28E2B",
    "green": "#59A14F",
    "red": "#E15759",
    "purple": "#B07AA1",
    "cyan": "#76B7B2",
    "light_blue": "#A0CBE8",
    "dark_blue": "#1F4E79",
    "grid": "#D9D9D9",
    "text": "#222222",
    "edge": "#333333",
}

BAND_LABELS = ["140–180 Hz", "160–200 Hz", "180–220 Hz", "200–240 Hz", "220–260 Hz", "240–280 Hz"]
LINE_COLORS = [COLORS["blue"], COLORS["orange"], COLORS["green"], COLORS["red"], COLORS["purple"], COLORS["cyan"]]
LINE_STYLES = ["-", "--", "-.", ":", (0, (3, 1, 1, 1)), (0, (5, 2))]
MARKERS = ["o", "s", "^", "D", "v", "P"]


def configure_fonts() -> str:
    candidates = [
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\NotoSansSC-Regular.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
    ]
    font_name = "DejaVu Sans"
    for path in candidates:
        if path.exists():
            font_manager.fontManager.addfont(str(path))
            font_name = font_manager.FontProperties(fname=str(path)).get_name()
            break

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": [font_name, "DejaVu Sans"],
        "axes.unicode_minus": False,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 9,
        "text.color": COLORS["text"],
        "axes.labelcolor": COLORS["text"],
        "axes.edgecolor": COLORS["text"],
        "xtick.color": COLORS["text"],
        "ytick.color": COLORS["text"],
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
    })
    return font_name


def style_axes(ax: plt.Axes) -> None:
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5, alpha=1.0)
    ax.grid(axis="x", visible=False)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color(COLORS["text"])
        spine.set_linewidth(0.8)


def save_all(fig: plt.Figure, stem: str) -> Dict[str, Path]:
    paths: Dict[str, Path] = {}
    for ext in ["png", "svg", "pdf"]:
        path = FIG_DIR / f"{stem}_papercolor.{ext}"
        if ext == "png":
            fig.savefig(path, dpi=300, bbox_inches="tight")
        else:
            fig.savefig(path, bbox_inches="tight")
        paths[ext] = path
    plt.close(fig)
    return paths


def load_summary() -> pd.DataFrame:
    df = pd.read_csv(BASE_DIR / "ch4_ga_summary_20gen.csv")
    df = df.sort_values("target_band_tag").reset_index(drop=True)
    order = ["band140_180", "band160_200", "band180_220", "band200_240", "band220_260", "band240_280"]
    df["order"] = df["target_band_tag"].map({tag: idx for idx, tag in enumerate(order)})
    return df.sort_values("order").reset_index(drop=True)


def load_improvement() -> pd.DataFrame:
    df = pd.read_csv(BASE_DIR / "ch4_ga_12to20_improvement.csv")
    order = ["band140_180", "band160_200", "band180_220", "band200_240", "band220_260", "band240_280"]
    df["order"] = df["target_band_tag"].map({tag: idx for idx, tag in enumerate(order)})
    return df.sort_values("order").reset_index(drop=True)


def add_value_labels(ax: plt.Axes, bars, values: np.ndarray, y_offset: float) -> None:
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + y_offset,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
            color=COLORS["text"],
        )


def plot_best_overlap(summary_df: pd.DataFrame) -> Dict[str, Path]:
    fig, ax = plt.subplots(figsize=(6.0, 3.6))
    values = summary_df["best_target_overlap_Hz"].to_numpy(dtype=float)
    x = np.arange(len(values))
    bars = ax.bar(x, values, width=0.62, color=COLORS["blue"], edgecolor=COLORS["edge"], linewidth=0.7)
    ax.set_title("不同目标频带最优重叠宽度对比", pad=8)
    ax.set_xlabel("目标频带")
    ax.set_ylabel("目标频带重叠宽度 / Hz")
    ax.set_xticks(x)
    ax.set_xticklabels(BAND_LABELS, rotation=25, ha="right")
    ax.set_ylim(0, 45)
    style_axes(ax)
    add_value_labels(ax, bars, values, 0.8)
    fig.tight_layout()
    return save_all(fig, "ch4_fig4_4_best_overlap_bar_20gen")


def plot_success_active(summary_df: pd.DataFrame) -> Dict[str, Path]:
    fig, ax = plt.subplots(figsize=(6.0, 3.6))
    x = np.arange(len(summary_df))
    width = 0.34
    success = summary_df["solve_success_rate"].to_numpy(dtype=float)
    active = summary_df["active_rate"].to_numpy(dtype=float)
    ax.bar(x - width / 2, success, width=width, label="成功求解率", color=COLORS["blue"], edgecolor=COLORS["edge"], linewidth=0.7)
    ax.bar(x + width / 2, active, width=width, label="有效候选比例", color=COLORS["orange"], edgecolor=COLORS["edge"], linewidth=0.7)
    ax.set_title("成功求解率与有效候选比例", pad=8)
    ax.set_xlabel("目标频带")
    ax.set_ylabel("比例")
    ax.set_xticks(x)
    ax.set_xticklabels(BAND_LABELS, rotation=25, ha="right")
    ax.set_ylim(0, 1.1)
    style_axes(ax)
    ax.legend(loc="upper right", frameon=True, edgecolor=COLORS["grid"], facecolor="white")
    fig.tight_layout()
    return save_all(fig, "ch4_fig4_5_success_active_rates_20gen")


def plot_12_vs_20(improvement_df: pd.DataFrame) -> Dict[str, Path]:
    fig, ax = plt.subplots(figsize=(6.0, 3.6))
    x = np.arange(len(improvement_df))
    width = 0.34
    gen12 = improvement_df["best_overlap_at_gen12"].to_numpy(dtype=float)
    gen20 = improvement_df["best_overlap_at_gen20"].to_numpy(dtype=float)
    bars12 = ax.bar(x - width / 2, gen12, width=width, label="第12代", color=COLORS["light_blue"], edgecolor=COLORS["edge"], linewidth=0.7)
    bars20 = ax.bar(x + width / 2, gen20, width=width, label="第20代", color=COLORS["dark_blue"], edgecolor=COLORS["edge"], linewidth=0.7)
    ax.set_title("12代与20代最优重叠宽度对比", pad=8)
    ax.set_xlabel("目标频带")
    ax.set_ylabel("目标频带重叠宽度 / Hz")
    ax.set_xticks(x)
    ax.set_xticklabels(BAND_LABELS, rotation=25, ha="right")
    ax.set_ylim(0, 45)
    style_axes(ax)
    add_value_labels(ax, bars12, gen12, 0.6)
    add_value_labels(ax, bars20, gen20, 0.6)
    ax.legend(loc="upper right", frameon=True, edgecolor=COLORS["grid"], facecolor="white")
    fig.tight_layout()
    return save_all(fig, "ch4_ga_12gen_vs_20gen_overlap")


def load_history(path_text: str) -> pd.DataFrame:
    hist = pd.read_csv(Path(path_text) / "ga_history_v1.csv")
    hist = hist.sort_values(["generation", "individual_index"], kind="stable").reset_index(drop=True)
    hist["evaluation_index"] = np.arange(1, len(hist) + 1)
    hist["best_so_far_target_overlap_Hz"] = pd.to_numeric(hist["active_target_overlap_Hz"], errors="coerce").fillna(0).cummax()
    return hist


def plot_convergence(summary_df: pd.DataFrame) -> Dict[str, Path]:
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    for idx, (_, row) in enumerate(summary_df.iterrows()):
        hist = load_history(row["output_dir"])
        ax.plot(
            hist["evaluation_index"],
            hist["best_so_far_target_overlap_Hz"],
            label=BAND_LABELS[idx],
            color=LINE_COLORS[idx],
            linestyle=LINE_STYLES[idx],
            marker=MARKERS[idx],
            markevery=12,
            markersize=3.2,
            linewidth=1.6,
        )
    ax.set_title("六个目标频带GA收敛曲线", pad=8)
    ax.set_xlabel("评价次数")
    ax.set_ylabel("历史最优目标频带重叠宽度 / Hz")
    ax.set_xlim(0, 122)
    ax.set_ylim(0, 42)
    style_axes(ax)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=True, edgecolor=COLORS["grid"], facecolor="white")
    fig.tight_layout()
    return save_all(fig, "ch4_fig4_3_ga_convergence_20gen")


def write_readme(font_name: str, outputs: Dict[str, Dict[str, Path]]) -> None:
    lines: List[str] = [
        "# 第4章统计图统一论文配色版本说明",
        "",
        "本目录中的 `_papercolor` 文件为第4章统计图的统一论文插图风格版本。所有图均基于已有 CSV 与 20 代 GA 历史结果重新绘制，未重新运行 COMSOL，未改动原始 GA 数据。",
        "",
        "## 统一规范",
        "",
        f"- 字体：{font_name}；若环境支持，中文优先 Microsoft YaHei / SimHei。",
        "- 标题字号：12；坐标轴标签字号：11；刻度字号：10；图例字号：9。",
        "- 背景：白色。",
        "- 网格线：仅保留 y 方向浅灰网格线 `#D9D9D9`，线宽 0.5。",
        "- 坐标轴和文字：`#222222`。",
        "- 目标频带标签：`140–180 Hz`、`160–200 Hz`、`180–220 Hz`、`200–240 Hz`、`220–260 Hz`、`240–280 Hz`。",
        "- 柱状图尺寸：`figsize=(6.0, 3.6)`；收敛曲线尺寸：`figsize=(6.8, 3.8)`；PNG 分辨率 300 dpi。",
        "",
        "## 配色",
        "",
        "| 名称 | 色值 |",
        "| --- | --- |",
        "| 主蓝色 | `#4E79A7` |",
        "| 辅助橙色 | `#F28E2B` |",
        "| 辅助绿色 | `#59A14F` |",
        "| 辅助红色 | `#E15759` |",
        "| 辅助紫色 | `#B07AA1` |",
        "| 辅助青色 | `#76B7B2` |",
        "| 浅蓝 | `#A0CBE8` |",
        "| 深蓝 | `#1F4E79` |",
        "",
        "## 图文件清单",
        "",
        "| 论文图号 | 图名 | 推荐插入 Word 的 PNG | SVG | PDF |",
        "| --- | --- | --- | --- | --- |",
    ]

    meta = {
        "ch4_fig4_3_ga_convergence_20gen": ("图4-3", "六个目标频带 GA 收敛曲线"),
        "ch4_fig4_4_best_overlap_bar_20gen": ("图4-4", "不同目标频带最优目标频带重叠宽度对比"),
        "ch4_fig4_5_success_active_rates_20gen": ("图4-5", "成功求解率与有效候选比例"),
        "ch4_ga_12gen_vs_20gen_overlap": ("图4-8", "12代与20代最优目标频带重叠宽度对比"),
    }
    for stem, (fig_no, title) in meta.items():
        paths = outputs[stem]
        rel_png = paths["png"].relative_to(FIG_DIR)
        rel_svg = paths["svg"].relative_to(FIG_DIR)
        rel_pdf = paths["pdf"].relative_to(FIG_DIR)
        lines.append(f"| {fig_no} | {title} | `{rel_png}` | `{rel_svg}` | `{rel_pdf}` |")
    lines.append("")
    (FIG_DIR / "CH4_FIGURE_STYLE_PAPERCOLOR_README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    font_name = configure_fonts()
    summary_df = load_summary()
    improvement_df = load_improvement()

    outputs = {
        "ch4_fig4_3_ga_convergence_20gen": plot_convergence(summary_df),
        "ch4_fig4_4_best_overlap_bar_20gen": plot_best_overlap(summary_df),
        "ch4_fig4_5_success_active_rates_20gen": plot_success_active(summary_df),
        "ch4_ga_12gen_vs_20gen_overlap": plot_12_vs_20(improvement_df),
    }
    write_readme(font_name, outputs)

    print("# 第4章统计图统一论文配色重画完成")
    print(f"中文字体: {font_name}")
    print("中文字体缺失: 否" if font_name != "DejaVu Sans" else "中文字体缺失: 是")
    for stem, paths in outputs.items():
        print(f"- {stem}")
        for ext in ["png", "svg", "pdf"]:
            print(f"  - {ext}: {paths[ext]}")
    print("建议替换论文旧图: 图4-3、图4-4、图4-5、图4-8")
    print(f"README: {FIG_DIR / 'CH4_FIGURE_STYLE_PAPERCOLOR_README.md'}")


if __name__ == "__main__":
    main()
