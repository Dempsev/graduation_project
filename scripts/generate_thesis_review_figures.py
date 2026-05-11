from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "output" / "doc" / "thesis_figures"

BAND_ORDER = [
    "band140_180",
    "band160_200",
    "band180_220",
    "band200_240",
    "band220_260",
    "band240_280",
]


def setup_style() -> None:
    font_path = Path(r"C:\Windows\Fonts\msyh.ttc")
    if font_path.exists():
        font_manager.fontManager.addfont(str(font_path))
        plt.rcParams["font.family"] = "Microsoft YaHei"
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 150
    plt.rcParams["savefig.dpi"] = 300


def save_fig(fig: plt.Figure, stem: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / f"{stem}.png", bbox_inches="tight", facecolor="white")
    fig.savefig(OUT_DIR / f"{stem}.svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def draw_box(ax, xy, wh, text, fc="#f7fbff", ec="#476a8a", size=10, lw=1.2):
    x, y = xy
    w, h = wh
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.025",
        facecolor=fc,
        edgecolor=ec,
        linewidth=lw,
    )
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, linespacing=1.35)
    return box


def arrow(ax, start, end, color="#4b5563", lw=1.3, style="-|>"):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle=style,
            mutation_scale=12,
            linewidth=lw,
            color=color,
            shrinkA=4,
            shrinkB=4,
        )
    )


def load_dataset_rows() -> tuple[list[dict], dict]:
    info_path = (
        ROOT
        / "data"
        / "prediction_targetband_param_v1"
        / "v1"
        / "windows_dense_v8_truth_plus_exploratory_aug_v1"
        / "dataset_info.json"
    )
    info = json.loads(info_path.read_text(encoding="utf-8"))
    by_tag = {row["target_band_tag"]: row for row in info["per_tag_summary"]}
    rows = []
    for tag in BAND_ORDER:
        source_parts = {
            "base": by_tag[tag],
            "gapdiversity": by_tag[f"{tag}_gapdiversity_v1"],
            "truth_assets": by_tag[f"{tag}_truth_assets_v3"],
        }
        total_rows = sum(int(p["rows"]) for p in source_parts.values())
        positive_rows = sum(int(p["positive_rows"]) for p in source_parts.values())
        weighted_cover_sum = sum(
            float(p["cover_ratio_mean_positive"]) * int(p["positive_rows"]) for p in source_parts.values()
        )
        rows.append(
            {
                "tag": tag.replace("band", "").replace("_", "-"),
                "rows": total_rows,
                "base_rows": int(source_parts["base"]["rows"]),
                "gapdiversity_rows": int(source_parts["gapdiversity"]["rows"]),
                "truth_assets_rows": int(source_parts["truth_assets"]["rows"]),
                "positive_rows": positive_rows,
                "positive_rate": positive_rows / total_rows if total_rows else 0.0,
                "cover": weighted_cover_sum / positive_rows if positive_rows else 0.0,
            }
        )
    return rows, info


def fig_dataset_band_stats() -> None:
    rows, info = load_dataset_rows()
    tags = [r["tag"] for r in rows]
    x = list(range(len(rows)))
    base = [r["base_rows"] for r in rows]
    gapdiversity = [r["gapdiversity_rows"] for r in rows]
    truth_assets = [r["truth_assets_rows"] for r in rows]
    totals = [r["rows"] for r in rows]
    positive_rates = [r["positive_rate"] for r in rows]
    covers = [r["cover"] for r in rows]

    fig, (ax_counts, ax_ratio) = plt.subplots(
        2,
        1,
        figsize=(11.2, 7.4),
        gridspec_kw={"height_ratios": [1.05, 1.0], "hspace": 0.36},
    )

    width = 0.58
    b1 = ax_counts.bar(x, base, width=width, color="#c7e9f1", edgecolor="white", label="base")
    b2 = ax_counts.bar(x, gapdiversity, bottom=base, width=width, color="#67a9cf", edgecolor="white", label="gap-diversity")
    bottoms = [a + b for a, b in zip(base, gapdiversity)]
    b3 = ax_counts.bar(x, truth_assets, bottom=bottoms, width=width, color="#2166ac", edgecolor="white", label="truth-assets-v3")
    ax_counts.set_ylabel("样本数 / 条", fontsize=11)
    ax_counts.set_ylim(0, max(totals) * 1.22)
    ax_counts.set_xticks(x, tags)
    ax_counts.grid(axis="y", alpha=0.22, linestyle="--")
    ax_counts.spines["top"].set_visible(False)
    ax_counts.spines["right"].set_visible(False)
    ax_counts.legend(loc="upper center", bbox_to_anchor=(0.5, 1.02), frameon=False, ncols=3)

    for bars in (b1, b2, b3):
        for rect in bars:
            value = int(rect.get_height())
            if value >= 700:
                ax_counts.text(
                    rect.get_x() + rect.get_width() / 2,
                    rect.get_y() + rect.get_height() / 2,
                    f"{value}",
                    ha="center",
                    va="center",
                    fontsize=8.5,
                    color="#0f172a" if rect.get_facecolor()[0] > 0.6 else "white",
                )
    for i, total in enumerate(totals):
        ax_counts.text(i, total + max(totals) * 0.025, f"合计 {total}", ha="center", fontsize=9, color="#334155")

    ratio_width = 0.32
    r1 = ax_ratio.bar([i - ratio_width / 2 for i in x], positive_rates, width=ratio_width, color="#d97706", label="正例率")
    r2 = ax_ratio.bar([i + ratio_width / 2 for i in x], covers, width=ratio_width, color="#15803d", label="正例平均覆盖率")
    ax_ratio.set_ylabel("比例", fontsize=11)
    ax_ratio.set_ylim(0, 1.05)
    ax_ratio.set_xticks(x, tags)
    ax_ratio.set_xlabel("目标频带 / Hz", fontsize=11)
    ax_ratio.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax_ratio.grid(axis="y", alpha=0.22, linestyle="--")
    ax_ratio.spines["top"].set_visible(False)
    ax_ratio.spines["right"].set_visible(False)
    ax_ratio.legend(loc="upper right", frameon=False, ncols=2)
    for bars in (r1, r2):
        for rect in bars:
            value = rect.get_height()
            ax_ratio.text(
                rect.get_x() + rect.get_width() / 2,
                value + 0.025,
                f"{value:.1%}",
                ha="center",
                va="bottom",
                fontsize=8.2,
            )

    title = "目标频带数据集统计"
    subtitle = (
        f"聚合口径：base + gap-diversity + truth-assets-v3；总计 {info['rows']:,} 条样本，"
        f"{info['unique_designs']:,} 个唯一结构，{info['unique_families']} 个结构族"
    )
    fig.text(0.5, 0.985, title, ha="center", va="top", fontsize=15, weight="bold")
    fig.text(0.5, 0.945, subtitle, ha="center", va="top", fontsize=10.3, color="#374151")
    fig.tight_layout(rect=[0, 0, 1, 0.91])
    save_fig(fig, "fig3_targetband_dataset_statistics")


def fig_cv_split_schematic() -> None:
    fig, ax = plt.subplots(figsize=(11.2, 6.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.text(0.5, 0.965, "Family-CV 与 Leave-One-Band 验证划分示意", ha="center", va="top", fontsize=15, weight="bold")

    ax.text(0.23, 0.86, "Family-CV：按结构族留出", ha="center", fontsize=12, weight="bold")
    ax.text(0.74, 0.86, "Leave-One-Band：按目标频带留出", ha="center", fontsize=12, weight="bold")

    family_names = ["ep239", "ep253", "ep218", "ep237", "ep206", "ep252"]
    colors = ["#dbeafe", "#dcfce7", "#fef3c7", "#fae8ff", "#fee2e2", "#e0f2fe"]
    for i, (name, color) in enumerate(zip(family_names, colors)):
        x = 0.06 + (i % 3) * 0.12
        y = 0.61 - (i // 3) * 0.16
        draw_box(ax, (x, y), (0.095, 0.09), name, fc=color, ec="#64748b", size=9)
    draw_box(ax, (0.08, 0.22), (0.19, 0.09), "训练集\n其余结构族", fc="#edf6ff", ec="#2563eb", size=10)
    draw_box(ax, (0.31, 0.22), (0.12, 0.09), "验证集\n留出结构族", fc="#fff7ed", ec="#d97706", size=10)
    arrow(ax, (0.24, 0.55), (0.24, 0.34), color="#2563eb")
    arrow(ax, (0.36, 0.55), (0.36, 0.34), color="#d97706")
    ax.text(0.245, 0.12, "检验：模型能否迁移到未见结构族", ha="center", fontsize=10, color="#334155")

    band_names = ["140-180", "160-200", "180-220", "200-240", "220-260", "240-280"]
    for i, name in enumerate(band_names):
        x = 0.55 + (i % 3) * 0.12
        y = 0.61 - (i // 3) * 0.16
        fc = "#fee2e2" if name == "200-240" else "#f8fafc"
        ec = "#dc2626" if name == "200-240" else "#64748b"
        draw_box(ax, (x, y), (0.095, 0.09), name, fc=fc, ec=ec, size=9)
    draw_box(ax, (0.57, 0.22), (0.19, 0.09), "训练集\n其余目标频带", fc="#edf6ff", ec="#2563eb", size=10)
    draw_box(ax, (0.80, 0.22), (0.12, 0.09), "验证集\n留出频带", fc="#fff7ed", ec="#d97706", size=10)
    arrow(ax, (0.72, 0.55), (0.72, 0.34), color="#2563eb")
    arrow(ax, (0.84, 0.55), (0.84, 0.34), color="#d97706")
    ax.text(0.745, 0.12, "检验：模型面对未见目标频带的迁移边界", ha="center", fontsize=10, color="#334155")

    ax.plot([0.5, 0.5], [0.10, 0.88], color="#cbd5e1", linewidth=1)
    save_fig(fig, "fig4_cv_split_schematic")


def fig_stage4_funnel() -> None:
    path = ROOT / "data" / "comsol_batch" / "stage4_validation_targetband_top6_v1" / "stage4_validation_arm_summary.csv"
    with path.open(encoding="utf-8", newline="") as f:
        row = next(csv.DictReader(f))
    submitted = int(row["rows_total"])
    geom = submitted - int(row["geometry_invalid_count"])
    contact = geom - int(row["no_contact_count"])
    solved = int(row["solve_success_count"])
    positive = int(row["positive_gap34_gain_count"])
    values = [submitted, geom, contact, solved, positive]
    labels = ["提交候选", "几何有效", "接触有效", "成功求解", "正增益"]
    notes = [
        "验证清单输入",
        "通过几何检查",
        "满足接触约束",
        "COMSOL 求解完成",
        "gap34 增益为正",
    ]

    fig, ax = plt.subplots(figsize=(11, 5.8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.text(0.5, 0.965, "Stage4 真实验证漏斗", ha="center", va="top", fontsize=15, weight="bold")

    max_v = max(values)
    y0 = 0.76
    for i, (label, note, value) in enumerate(zip(labels, notes, values)):
        width = 0.76 * (value / max_v)
        x = 0.5 - width / 2
        y = y0 - i * 0.145
        color = ["#1d4ed8", "#2563eb", "#0284c7", "#059669", "#16a34a"][i]
        rect = FancyBboxPatch((x, y), width, 0.09, boxstyle="round,pad=0.01,rounding_size=0.025", facecolor=color, edgecolor="none", alpha=0.92)
        ax.add_patch(rect)
        ax.text(0.5, y + 0.045, f"{label}  {value}/{submitted}", color="white", ha="center", va="center", fontsize=12, weight="bold")
        ax.text(0.88, y + 0.045, note, ha="left", va="center", fontsize=9.5, color="#334155")
        if i < len(values) - 1:
            arrow(ax, (0.5, y - 0.005), (0.5, y - 0.048), color="#94a3b8", lw=1.0)

    ax.text(
        0.5,
        0.065,
        f"数据来源：stage4_validation_targetband_top6_v1；正增益率 {float(row['positive_gap34_gain_rate']):.1%}，平均 gap34 增益 {float(row['mean_gap34_gain_Hz']):.2f} Hz",
        ha="center",
        fontsize=10,
        color="#475569",
    )
    save_fig(fig, "fig6_stage4_validation_funnel")


def fig_method_boundary() -> None:
    fig, ax = plt.subplots(figsize=(11.2, 6.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.text(0.5, 0.965, "方法适用边界与结论表述范围", ha="center", va="top", fontsize=15, weight="bold")

    draw_box(ax, (0.08, 0.76), (0.84, 0.09), "本文主张的成立条件", fc="#eef6ff", ec="#2563eb", size=12)
    conditions = [
        ("目标空间", "thesis band catalog\n内的有限目标频带"),
        ("结构空间", "当前二维参数化\n结构族与形状表示"),
        ("物理配置", "当前材料参数、周期边界\n与 COMSOL 求解流程"),
        ("模型角色", "候选筛选与排序前端\n不是物理求解器替代品"),
    ]
    for i, (head, body) in enumerate(conditions):
        x = 0.08 + i * 0.22
        draw_box(ax, (x, 0.56), (0.18, 0.12), f"{head}\n{body}", fc="#f8fafc", ec="#94a3b8", size=8.6)
        arrow(ax, (x + 0.09, 0.76), (x + 0.09, 0.69), color="#64748b", lw=1)

    left = FancyBboxPatch((0.08, 0.22), 0.38, 0.22, boxstyle="round,pad=0.02,rounding_size=0.025", facecolor="#ecfdf5", edgecolor="#16a34a", linewidth=1.8)
    right = FancyBboxPatch((0.54, 0.22), 0.38, 0.22, boxstyle="round,pad=0.02,rounding_size=0.025", facecolor="#fff1f2", edgecolor="#e11d48", linewidth=1.8)
    ax.add_patch(left)
    ax.add_patch(right)
    ax.text(0.27, 0.40, "可以主张", ha="center", va="center", fontsize=12, weight="bold")
    ax.text(
        0.27,
        0.31,
        "目标频带目录内\n条件预测 + 结构族感知候选构造\n局部精修 + 真实验证\n形成可运行、可复现、可验证闭环",
        ha="center",
        va="center",
        fontsize=9.2,
        linespacing=1.45,
    )
    ax.text(0.73, 0.40, "不宜主张", ha="center", va="center", fontsize=12, weight="bold")
    ax.text(
        0.73,
        0.31,
        "任意连续频带自动设计\n跨材料通用泛化\n预测器替代 COMSOL\n全设计空间最优性证明",
        ha="center",
        va="center",
        fontsize=9.2,
        linespacing=1.45,
    )
    arrow(ax, (0.29, 0.56), (0.27, 0.45), color="#16a34a")
    arrow(ax, (0.72, 0.56), (0.73, 0.45), color="#e11d48")
    ax.text(
        0.5,
        0.11,
        "推荐答辩表述：本文建立的是边界清晰、可复现、可验证的目标频带逆向设计流程。",
        ha="center",
        fontsize=10.5,
        color="#334155",
    )
    save_fig(fig, "fig7_method_claim_boundary")


def fig_dataset_summary_table() -> None:
    rows, info = load_dataset_rows()
    fig, ax = plt.subplots(figsize=(11.4, 5.0))
    ax.axis("off")
    fig.text(0.5, 0.965, "目标频带数据集统计表", ha="center", va="top", fontsize=14, weight="bold")
    fig.text(
        0.5,
        0.86,
        f"总样本 {info['rows']:,} 条；唯一结构 {info['unique_designs']:,} 个；结构族 {info['unique_families']} 个；每个目标频带切片由三类来源聚合",
        ha="center",
        fontsize=9.8,
        color="#475569",
    )
    table_rows = [
        [
            r["tag"],
            f"{r['base_rows']:,}",
            f"{r['gapdiversity_rows']:,}",
            f"{r['truth_assets_rows']:,}",
            f"{r['rows']:,}",
            f"{r['positive_rate']:.1%}",
            f"{r['cover']:.3f}",
        ]
        for r in rows
    ]
    table = ax.table(
        cellText=table_rows,
        colLabels=["目标频带 / Hz", "base", "gap-div", "truth-assets", "合计", "正例率", "正例平均覆盖率"],
        cellLoc="center",
        colLoc="center",
        loc="center",
        bbox=[0.03, 0.08, 0.94, 0.70],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10.5)
    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor("#cbd5e1")
        if r == 0:
            cell.set_facecolor("#e2e8f0")
            cell.set_text_props(weight="bold")
        elif r % 2 == 0:
            cell.set_facecolor("#f8fafc")
    save_fig(fig, "fig3_targetband_dataset_summary_table")


def main() -> None:
    setup_style()
    fig_dataset_band_stats()
    fig_dataset_summary_table()
    fig_cv_split_schematic()
    fig_stage4_funnel()
    fig_method_boundary()
    print(f"generated figures in {OUT_DIR}")


if __name__ == "__main__":
    main()
