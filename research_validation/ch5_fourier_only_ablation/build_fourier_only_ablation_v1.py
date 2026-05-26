from __future__ import annotations

import csv
from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "research_validation" / "ch5_fourier_only_ablation"
FIG_DIR = OUT_DIR / "figures"

BANDS = ["band200_240", "band220_260", "band240_280"]
BAND_LABELS = {
    "band200_240": "200-240 Hz",
    "band220_260": "220-260 Hz",
    "band240_280": "240-280 Hz",
}

FOURIER_RUN_DIR = ROOT / "data" / "comsol_batch"
CURRENT_GA20_SUMMARY = ROOT / "research_validation" / "ch4_ga_real_optimization" / "ch4_ga_summary_20gen.csv"
FOURIER_SHAPE_POOL = (
    ROOT / "data" / "ml_runs" / "fourier_only_real_ga_v1" / "fourier_only_real_ga_shape_pool_v1.csv"
)
CURRENT_SHAPE_POOL = ROOT / "data" / "ml_runs" / "targetband_baseline_abc_v1" / "real_ga_shape_pool_v1.csv"


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path, encoding="utf-8-sig")


def read_search_summary(run_id: str) -> dict:
    path = FOURIER_RUN_DIR / run_id / "ga_search_summary_v1.csv"
    df = read_csv(path)
    if df.empty:
        raise ValueError(f"Empty search summary: {path}")
    return df.iloc[0].to_dict()


def build_summary() -> pd.DataFrame:
    current = read_csv(CURRENT_GA20_SUMMARY)
    current = current[current["target_band_tag"].isin(BANDS)].copy()
    current["current_best_overlap_Hz"] = pd.to_numeric(current["best_target_overlap_Hz"], errors="coerce")
    current["current_best_cover_ratio"] = pd.to_numeric(current["best_cover_ratio"], errors="coerce")
    current["current_evaluations"] = pd.to_numeric(current["n_evaluations_actual"], errors="coerce").astype(int)
    current = current[
        [
            "target_band_tag",
            "current_best_overlap_Hz",
            "current_best_cover_ratio",
            "current_evaluations",
        ]
    ]

    rows = []
    for band in BANDS:
        run_id = f"comsol_in_loop_fourier_pure_boundary_{band}_ga_v1"
        summary = read_search_summary(run_id)
        rows.append(
            {
                "target_band_tag": band,
                "target_band": BAND_LABELS[band],
                "fourier_only_run_id": run_id,
                "fourier_only_evaluations": int(float(summary["evaluated_count"])),
                "fourier_only_generations": int(float(summary["generation_count"])),
                "fourier_only_best_overlap_Hz": float(summary["best_active_overlap_Hz"]),
                "fourier_only_best_cover_ratio": float(summary["best_active_cover_ratio"]),
                "fourier_only_best_shape_id": str(summary["best_shape_id"]),
                "fourier_only_stop_reason": str(summary["stop_reason"]),
            }
        )

    merged = pd.DataFrame(rows).merge(current, on="target_band_tag", how="left")
    merged["fourier_minus_current_overlap_Hz"] = (
        merged["fourier_only_best_overlap_Hz"] - merged["current_best_overlap_Hz"]
    )
    merged["fourier_to_current_overlap_ratio"] = (
        merged["fourier_only_best_overlap_Hz"] / merged["current_best_overlap_Hz"]
    )
    merged["conclusion_tag"] = merged["fourier_minus_current_overlap_Hz"].map(
        lambda delta: "fourier_only_better" if delta > 0 else "current_combined_better"
    )
    return merged[
        [
            "target_band",
            "target_band_tag",
            "fourier_only_run_id",
            "fourier_only_evaluations",
            "fourier_only_generations",
            "fourier_only_best_overlap_Hz",
            "fourier_only_best_cover_ratio",
            "fourier_only_best_shape_id",
            "current_evaluations",
            "current_best_overlap_Hz",
            "current_best_cover_ratio",
            "fourier_minus_current_overlap_Hz",
            "fourier_to_current_overlap_ratio",
            "conclusion_tag",
            "fourier_only_stop_reason",
        ]
    ]


def fmt(value: float | int, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def write_report(summary: pd.DataFrame) -> None:
    lines = [
        "# 傅里叶边界模型 GA 优化与当前结合模型 GA 优化对比实验",
        "",
        "## 实验目的",
        "",
        "本实验用于回应“没有贪吃蛇结构族，仅采用傅里叶边界模型时，经过同样 GA 优化后的结果如何”的问题。对比口径为：",
        "",
        "- 傅里叶-only GA：形状池仅使用傅里叶边界原型 `fourier_only_real_ga_shape_pool_v1.csv`，优化过程仍采用 COMSOL-in-loop GA。",
        "- 当前结合模型 GA：使用第 4 章当前 20 代真实 GA 结果，即现有贪吃蛇/傅里叶结合候选空间下的 COMSOL-in-loop GA 基准。",
        "- 二者均采用 `target_overlap_Hz` 作为适应度函数；每个频带均为 20 代、种群规模 6，共 120 次真实 COMSOL 评价。",
        "",
        "## 数据来源",
        "",
        f"- 傅里叶-only shape pool：`{FOURIER_SHAPE_POOL.relative_to(ROOT).as_posix()}`。",
        f"- 当前结合模型 shape pool：`{CURRENT_SHAPE_POOL.relative_to(ROOT).as_posix()}`。",
        "- 傅里叶-only GA 输出目录：`data/comsol_batch/comsol_in_loop_fourier_only_<band>_ga_v1/`。",
        f"- 当前结合模型 GA20 汇总：`{CURRENT_GA20_SUMMARY.relative_to(ROOT).as_posix()}`。",
        "",
        "## 结果汇总",
        "",
        "| 目标频带 | 傅里叶-only GA20 最佳 overlap/Hz | 当前结合模型 GA20 最佳 overlap/Hz | 差值/Hz | 傅里叶-only / 当前 | 结论 |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for _, row in summary.iterrows():
        conclusion = "傅里叶-only 略优" if row["fourier_minus_current_overlap_Hz"] > 0 else "当前结合模型略优"
        lines.append(
            "| "
            + " | ".join(
                [
                    row["target_band"],
                    fmt(row["fourier_only_best_overlap_Hz"]),
                    fmt(row["current_best_overlap_Hz"]),
                    fmt(row["fourier_minus_current_overlap_Hz"]),
                    fmt(row["fourier_to_current_overlap_ratio"]),
                    conclusion,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## 主要观察",
            "",
            "1. 在 200-240 Hz 频带，傅里叶-only GA20 获得 34.364 Hz，接近当前结合模型 GA20 的 35.283 Hz，但仍略低，说明当前结合候选空间在该频带保留了小幅优势。",
            "2. 在 220-260 Hz 频带，傅里叶-only GA20 获得 7.783 Hz，高于当前结合模型 GA20 的 4.098 Hz，说明该高频目标并不完全依赖贪吃蛇形态来源，傅里叶边界模型经 GA 搜索后也能找到更好的局部解。",
            "3. 在 240-280 Hz 频带，傅里叶-only GA20 获得 2.922 Hz，低于当前结合模型 GA20 的 3.934 Hz，说明更高频段中结合候选空间仍有一定优势，但两者都属于较低 overlap，仍应作为困难频带讨论。",
            "4. 因此，这组消融实验不支持“贪吃蛇结构族单独决定优化效果”的说法。更稳妥的论文结论是：傅里叶边界模型本身具备可优化性，贪吃蛇结构族的价值主要体现在扩充形态来源和改善部分频带的搜索机会；最终效果随目标频带变化，并由 COMSOL-in-loop GA 真值决定。",
            "",
            "## 论文可用表述",
            "",
            "为检验贪吃蛇路径结构族对优化结果的影响，本文进一步构建了傅里叶边界模型的 GA 消融实验。在该实验中，形状池仅保留傅里叶边界原型，连续设计变量、适应度函数和 COMSOL-in-loop GA 设置均与当前优化流程保持一致。每个目标频带执行 20 代、种群规模为 6 的真实 GA 搜索，并与现有贪吃蛇/傅里叶结合候选空间下的 GA20 结果进行比较。结果表明，在 200-240 Hz 频带，傅里叶-only GA20 的最佳重叠宽度为 34.364 Hz，略低于当前结合模型的 35.283 Hz；在 220-260 Hz 频带，傅里叶-only GA20 达到 7.783 Hz，高于当前结合模型的 4.098 Hz；在 240-280 Hz 频带，傅里叶-only GA20 为 2.922 Hz，低于当前结合模型的 3.934 Hz。该结果说明，傅里叶边界模型本身具有可优化性，贪吃蛇结构族并不是获得目标带隙的唯一来源；其主要作用是扩展候选形态空间，并在部分频带中提高搜索到有效结构的机会。不同频带下两类候选空间的优劣并不完全一致，因此最终结论仍需以 COMSOL 频散计算和真实 GA 搜索结果为准。",
            "",
            "## 输出文件",
            "",
            "- `fourier_only_ablation_summary.csv`：傅里叶-only GA20 与当前结合模型 GA20 的数值对比。",
            "- `figures/ch5_fourier_only_ga20_vs_current_ga20_overlap.svg`：同口径 overlap 柱状图。",
            "- `thesis_insert_fourier_only_ablation_cn.md`：可粘贴入论文的段落。",
        ]
    )
    (OUT_DIR / "FOURIER_ONLY_ABLATION_REPORT_CN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_insert() -> None:
    report = (
        "### 傅里叶边界模型 GA 优化消融实验\n\n"
        "为检验贪吃蛇路径结构族对优化结果的影响，本文进一步构建了傅里叶边界模型的 GA 消融实验。"
        "在该实验中，形状池仅保留傅里叶边界原型，连续设计变量、适应度函数和 COMSOL-in-loop GA 设置均与当前优化流程保持一致。"
        "每个目标频带执行 20 代、种群规模为 6 的真实 GA 搜索，并与现有贪吃蛇/傅里叶结合候选空间下的 GA20 结果进行比较。\n\n"
        "结果表明，在 200-240 Hz 频带，傅里叶-only GA20 的最佳目标频带重叠宽度为 34.364 Hz，略低于当前结合模型的 35.283 Hz；"
        "在 220-260 Hz 频带，傅里叶-only GA20 达到 7.783 Hz，高于当前结合模型的 4.098 Hz；"
        "在 240-280 Hz 频带，傅里叶-only GA20 为 2.922 Hz，低于当前结合模型的 3.934 Hz。"
        "该结果说明，傅里叶边界模型本身具有可优化性，贪吃蛇结构族并不是获得目标带隙的唯一来源；"
        "其主要作用是扩展候选形态空间，并在部分频带中提高搜索到有效结构的机会。"
        "不同频带下两类候选空间的优劣并不完全一致，因此最终结论仍需以 COMSOL 频散计算和真实 GA 搜索结果为准。\n"
    )
    (OUT_DIR / "thesis_insert_fourier_only_ablation_cn.md").write_text(report, encoding="utf-8")


def make_svg(summary: pd.DataFrame) -> str:
    width, height = 920, 520
    left, right, top, bottom = 86, 34, 56, 90
    plot_w = width - left - right
    plot_h = height - top - bottom
    ymax = 40.0

    def sy(value: float) -> float:
        return top + plot_h - (value / ymax) * plot_h

    group_w = plot_w / len(summary)
    bar_w = 72
    gap = 18
    colors = [("#3572A5", "傅里叶-only GA20", "fourier_only_best_overlap_Hz"), ("#4F7D4A", "当前结合模型 GA20", "current_best_overlap_Hz")]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text{font-family:"Microsoft YaHei","Noto Sans CJK SC",Arial,sans-serif;fill:#222}.axis{stroke:#333;stroke-width:1.2}.grid{stroke:#d8dee6;stroke-width:1}.small{font-size:13px}.label{font-size:15px}.title{font-size:21px;font-weight:600}</style>',
        f'<text class="title" x="{width/2}" y="30" text-anchor="middle">傅里叶-only GA20 与当前结合模型 GA20 对比</text>',
    ]
    for tick in range(0, 41, 10):
        y = sy(tick)
        parts.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}"/>')
        parts.append(f'<text class="small" x="{left-12}" y="{y+4:.1f}" text-anchor="end">{tick}</text>')
    parts.append(f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}"/>')
    parts.append(f'<line class="axis" x1="{left}" y1="{top+plot_h}" x2="{width-right}" y2="{top+plot_h}"/>')
    parts.append(f'<text class="label" x="22" y="{top+plot_h/2}" text-anchor="middle" transform="rotate(-90 22 {top+plot_h/2})">最佳目标频带重叠宽度 / Hz</text>')

    for group_idx, row in summary.iterrows():
        center = left + group_w * (group_idx + 0.5)
        x0 = center - (2 * bar_w + gap) / 2
        for series_idx, (color, _, column) in enumerate(colors):
            value = float(row[column])
            x = x0 + series_idx * (bar_w + gap)
            y = sy(value)
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w}" height="{top+plot_h-y:.1f}" fill="{color}" rx="2"/>')
            parts.append(f'<text class="small" x="{x+bar_w/2:.1f}" y="{y-6:.1f}" text-anchor="middle">{value:.1f}</text>')
        parts.append(f'<text class="label" x="{center:.1f}" y="{height-48}" text-anchor="middle">{escape(str(row["target_band"]))}</text>')

    legend_x = left + 170
    legend_y = height - 24
    for idx, (color, label, _) in enumerate(colors):
        x = legend_x + idx * 230
        parts.append(f'<rect x="{x}" y="{legend_y-12}" width="18" height="12" fill="{color}" rx="2"/>')
        parts.append(f'<text class="small" x="{x+26}" y="{legend_y-2}">{escape(label)}</text>')

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    summary = build_summary()
    summary.to_csv(OUT_DIR / "fourier_only_ablation_summary.csv", index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)
    write_report(summary)
    write_insert()
    (FIG_DIR / "ch5_fourier_only_ga20_vs_current_ga20_overlap.svg").write_text(make_svg(summary), encoding="utf-8")
    print(f"[DONE] wrote {OUT_DIR}")
    print(summary[["target_band", "fourier_only_best_overlap_Hz", "current_best_overlap_Hz", "fourier_minus_current_overlap_Hz"]].to_string(index=False))


if __name__ == "__main__":
    main()
