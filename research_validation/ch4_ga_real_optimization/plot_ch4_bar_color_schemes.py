from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager


ROOT = Path(__file__).resolve().parents[2]
BASE_DIR = ROOT / "research_validation" / "ch4_ga_real_optimization"
FIG_DIR = BASE_DIR / "figures"

BAND_ORDER = [
    "band140_180",
    "band160_200",
    "band180_220",
    "band200_240",
    "band220_260",
    "band240_280",
]
BAND_LABELS = [
    "140–180 Hz",
    "160–200 Hz",
    "180–220 Hz",
    "200–240 Hz",
    "220–260 Hz",
    "240–280 Hz",
]


@dataclass(frozen=True)
class ColorScheme:
    suffix: str
    name: str
    description: str
    text: str
    grid: str
    alpha_single: float
    alpha_group: float
    alpha_12_20: float
    best_bar: str
    success: str
    active: str
    gen12: str
    gen20: str
    colors: Dict[str, str]


SCHEMES = [
    ColorScheme(
        suffix="okabe",
        name="方案 B",
        description="Okabe-Ito 科研色盲友好版",
        text="#333333",
        grid="#E6E6E6",
        alpha_single=0.82,
        alpha_group=0.82,
        alpha_12_20=0.82,
        best_bar="#0072B2",
        success="#0072B2",
        active="#E69F00",
        gen12="#56B4E9",
        gen20="#0072B2",
        colors={
            "蓝色": "#0072B2",
            "橙色": "#E69F00",
            "天蓝": "#56B4E9",
            "蓝绿": "#009E73",
            "朱红": "#D55E00",
            "紫色": "#CC79A7",
            "深灰文字": "#333333",
            "浅灰网格": "#E6E6E6",
        },
    ),
    ColorScheme(
        suffix="morandi",
        name="方案 C",
        description="莫兰迪低饱和版",
        text="#333333",
        grid="#E6E6E6",
        alpha_single=0.88,
        alpha_group=0.88,
        alpha_12_20=0.90,
        best_bar="#7895B2",
        success="#7895B2",
        active="#D8A47F",
        gen12="#B7C9D9",
        gen20="#7895B2",
        colors={
            "雾蓝": "#7895B2",
            "沙橙": "#D8A47F",
            "鼠尾草绿": "#9CAF88",
            "灰紫": "#A69CAC",
            "砖红": "#B56576",
            "青灰": "#8AA6A3",
            "浅雾蓝": "#B7C9D9",
            "深灰文字": "#333333",
            "浅灰网格": "#E6E6E6",
        },
    ),
]


def configure_fonts() -> tuple[str, bool]:
    candidates = [
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
    ]
    font_name = "DejaVu Sans"
    missing_chinese_font = True
    for path in candidates:
        if path.exists():
            font_manager.fontManager.addfont(str(path))
            font_name = font_manager.FontProperties(fname=str(path)).get_name()
            missing_chinese_font = False
            break

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [font_name, "DejaVu Sans"],
            "axes.unicode_minus": False,
            "axes.titlesize": 12,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 9.5,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )
    return font_name, missing_chinese_font


def ordered_frame(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    order_map = {tag: i for i, tag in enumerate(BAND_ORDER)}
    df["__order"] = df["target_band_tag"].map(order_map)
    return df.sort_values("__order").reset_index(drop=True)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    summary = ordered_frame(BASE_DIR / "ch4_ga_summary_20gen.csv")
    improvement = ordered_frame(BASE_DIR / "ch4_ga_12to20_improvement.csv")
    return summary, improvement


def style_axes(ax: plt.Axes, scheme: ColorScheme) -> None:
    ax.grid(axis="y", color=scheme.grid, linewidth=0.6, alpha=0.8)
    ax.grid(axis="x", visible=False)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for side in ["left", "bottom"]:
        ax.spines[side].set_color(scheme.text)
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(axis="both", colors=scheme.text, width=0.8)
    ax.title.set_color(scheme.text)
    ax.xaxis.label.set_color(scheme.text)
    ax.yaxis.label.set_color(scheme.text)


def set_band_axis(ax: plt.Axes, x: np.ndarray) -> None:
    ax.set_xticks(x)
    ax.set_xticklabels(BAND_LABELS, rotation=25, ha="right")


def add_value_labels(
    ax: plt.Axes,
    bars,
    values: np.ndarray,
    scheme: ColorScheme,
    y_offset: float,
) -> None:
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + y_offset,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
            color=scheme.text,
        )


def save_all(fig: plt.Figure, stem: str, suffix: str) -> Dict[str, Path]:
    paths: Dict[str, Path] = {}
    for ext in ["png", "svg", "pdf"]:
        path = FIG_DIR / f"{stem}_{suffix}.{ext}"
        if ext == "png":
            fig.savefig(path, dpi=300, bbox_inches="tight")
        else:
            fig.savefig(path, bbox_inches="tight")
        paths[ext] = path
    plt.close(fig)
    return paths


def plot_best_overlap(summary: pd.DataFrame, scheme: ColorScheme) -> Dict[str, Path]:
    fig, ax = plt.subplots(figsize=(6.2, 3.7))
    values = summary["best_target_overlap_Hz"].to_numpy(dtype=float)
    x = np.arange(len(values))
    bars = ax.bar(
        x,
        values,
        width=0.62,
        color=scheme.best_bar,
        alpha=scheme.alpha_single,
        edgecolor=scheme.text,
        linewidth=0.8,
    )
    ax.set_title("不同目标频带最优重叠宽度对比", pad=8)
    ax.set_xlabel("目标频带")
    ax.set_ylabel("目标频带重叠宽度 / Hz")
    set_band_axis(ax, x)
    ax.set_ylim(0, 45)
    style_axes(ax, scheme)
    add_value_labels(ax, bars, values, scheme, 0.75)
    fig.tight_layout(pad=0.8)
    return save_all(fig, "ch4_fig4_4_best_overlap_bar_20gen", scheme.suffix)


def plot_success_active(summary: pd.DataFrame, scheme: ColorScheme) -> Dict[str, Path]:
    fig, ax = plt.subplots(figsize=(6.2, 3.7))
    x = np.arange(len(summary))
    width = 0.34
    success = summary["solve_success_rate"].to_numpy(dtype=float)
    active = summary["active_rate"].to_numpy(dtype=float)
    ax.bar(
        x - width / 2,
        success,
        width=width,
        label="成功求解率",
        color=scheme.success,
        alpha=scheme.alpha_group,
        edgecolor=scheme.text,
        linewidth=0.8,
    )
    ax.bar(
        x + width / 2,
        active,
        width=width,
        label="有效候选比例",
        color=scheme.active,
        alpha=scheme.alpha_group,
        edgecolor=scheme.text,
        linewidth=0.8,
    )
    ax.set_title("成功求解率与有效候选比例", pad=8)
    ax.set_xlabel("目标频带")
    ax.set_ylabel("比例")
    set_band_axis(ax, x)
    ax.set_ylim(0, 1.1)
    style_axes(ax, scheme)
    ax.legend(loc="upper right", frameon=True, edgecolor=scheme.grid, facecolor="white")
    fig.tight_layout(pad=0.8)
    return save_all(fig, "ch4_fig4_5_success_active_rates_20gen", scheme.suffix)


def plot_12_vs_20(improvement: pd.DataFrame, scheme: ColorScheme) -> Dict[str, Path]:
    fig, ax = plt.subplots(figsize=(6.2, 3.7))
    x = np.arange(len(improvement))
    width = 0.34
    gen12 = improvement["best_overlap_at_gen12"].to_numpy(dtype=float)
    gen20 = improvement["best_overlap_at_gen20"].to_numpy(dtype=float)
    bars12 = ax.bar(
        x - width / 2,
        gen12,
        width=width,
        label="第12代",
        color=scheme.gen12,
        alpha=scheme.alpha_12_20,
        edgecolor=scheme.text,
        linewidth=0.8,
    )
    bars20 = ax.bar(
        x + width / 2,
        gen20,
        width=width,
        label="第20代",
        color=scheme.gen20,
        alpha=scheme.alpha_12_20,
        edgecolor=scheme.text,
        linewidth=0.8,
    )
    ax.set_title("12代与20代最优重叠宽度对比", pad=8)
    ax.set_xlabel("目标频带")
    ax.set_ylabel("目标频带重叠宽度 / Hz")
    set_band_axis(ax, x)
    ax.set_ylim(0, 45)
    style_axes(ax, scheme)
    add_value_labels(ax, bars12, gen12, scheme, 0.65)
    add_value_labels(ax, bars20, gen20, scheme, 0.65)
    ax.legend(loc="upper right", frameon=True, edgecolor=scheme.grid, facecolor="white")
    fig.tight_layout(pad=0.8)
    return save_all(fig, "ch4_ga_12gen_vs_20gen_overlap", scheme.suffix)


def write_readme(
    outputs: Dict[str, Dict[str, Dict[str, Path]]],
    font_name: str,
    missing_chinese_font: bool,
) -> Path:
    readme = FIG_DIR / "CH4_BAR_FIGURE_COLOR_COMPARISON_README.md"
    lines: List[str] = [
        "# 第4章柱状图配色方案对比说明",
        "",
        "本次仅重画第4章三张柱状统计图，未修改收敛曲线图，未重新运行 COMSOL，未改动原始 GA 数据。",
        "",
        f"- 中文字体：{font_name}",
        f"- 是否检测到中文字体缺失：{'是' if missing_chinese_font else '否'}",
        "- 图尺寸：`figsize=(6.2, 3.7)`；PNG 分辨率：300 dpi。",
        "- 网格线：仅保留 y 方向浅灰网格线 `#E6E6E6`，线宽 0.6，alpha=0.8。",
        "- 坐标轴：去除顶部和右侧边框，左侧和底部边框使用 `#333333`，线宽 0.8。",
        "",
        "## 配色方案",
        "",
    ]
    for scheme in SCHEMES:
        lines.extend([f"### {scheme.name}：{scheme.description}", "", "| 颜色 | 色值 |", "| --- | --- |"])
        for label, color in scheme.colors.items():
            lines.append(f"| {label} | `{color}` |")
        lines.append("")

    lines.extend(
        [
            "## 图文件清单",
            "",
            "| 方案 | 论文图号 | 图名 | 推荐插入 Word 的 PNG | SVG | PDF |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    figure_meta = [
        ("ch4_fig4_4_best_overlap_bar_20gen", "图4-4", "不同目标频带最优重叠宽度对比"),
        ("ch4_fig4_5_success_active_rates_20gen", "图4-5", "成功求解率与有效候选比例"),
        ("ch4_ga_12gen_vs_20gen_overlap", "图4-8", "12代与20代最优重叠宽度对比"),
    ]
    for scheme in SCHEMES:
        for stem, fig_no, title in figure_meta:
            paths = outputs[scheme.suffix][stem]
            png = paths["png"].name
            svg = paths["svg"].name
            pdf = paths["pdf"].name
            lines.append(f"| {scheme.name} | {fig_no} | {title} | `{png}` | `{svg}` | `{pdf}` |")
    lines.append("")
    lines.extend(
        [
            "## 使用建议",
            "",
            "- 方案 B 色彩区分度更强，更适合强调不同统计量之间的对比。",
            "- 方案 C 饱和度更低、版面更柔和，更适合正文中连续插入多张统计图。",
            "- 若论文整体已有较多蓝色系图件，优先考虑方案 B；若希望第4章图面更统一克制，优先考虑方案 C。",
        ]
    )
    readme.write_text("\n".join(lines), encoding="utf-8")
    return readme


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    font_name, missing_chinese_font = configure_fonts()
    summary, improvement = load_data()

    outputs: Dict[str, Dict[str, Dict[str, Path]]] = {}
    for scheme in SCHEMES:
        outputs[scheme.suffix] = {
            "ch4_fig4_4_best_overlap_bar_20gen": plot_best_overlap(summary, scheme),
            "ch4_fig4_5_success_active_rates_20gen": plot_success_active(summary, scheme),
            "ch4_ga_12gen_vs_20gen_overlap": plot_12_vs_20(improvement, scheme),
        }

    readme = write_readme(outputs, font_name, missing_chinese_font)

    print("# 第4章三张柱状图配色方案重画完成")
    print("未重新运行 COMSOL；未改动原始 GA 数据；未修改收敛曲线图。")
    print(f"中文字体: {font_name}")
    print(f"中文字体缺失: {'是' if missing_chinese_font else '否'}")
    for scheme in SCHEMES:
        print(f"\n{scheme.name} {scheme.description}:")
        for stem, paths in outputs[scheme.suffix].items():
            print(f"- {stem}_{scheme.suffix}")
            for ext in ["png", "svg", "pdf"]:
                print(f"  {ext}: {paths[ext]}")
    print(f"\nREADME: {readme}")
    print("图面效果建议: 优先推荐方案 C（莫兰迪低饱和版）用于论文正文；方案 B 适合需要更强区分度的汇报或答辩材料。")


if __name__ == "__main__":
    main()
