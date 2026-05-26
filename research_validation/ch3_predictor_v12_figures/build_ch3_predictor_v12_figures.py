from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "research_validation" / "ch3_predictor_v12_figures"
DATA_DIR = ROOT / "data" / "prediction_targetband_param_v1" / "v1" / "windows_dense_v12_all_history_ga20_clean_v1"
READINESS_DIR = ROOT / "data" / "analysis" / "predictor_readiness_v12_all_history_ga20_clean_v1"

THESIS_BANDS = ["band140_180", "band160_200", "band180_220", "band200_240", "band220_260", "band240_280"]
THESIS_LABELS = ["140-180", "160-200", "180-220", "200-240", "220-260", "240-280"]
FONT_CANDIDATES = ["Microsoft YaHei", "SimHei", "SimSun", "DejaVu Sans"]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_figure(fig: plt.Figure, stem: str) -> tuple[Path, Path]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    png = OUT_DIR / f"{stem}.png"
    svg = OUT_DIR / f"{stem}.svg"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    plt.close(fig)
    return png, svg


def set_style() -> None:
    plt.rcParams["font.sans-serif"] = FONT_CANDIDATES
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.facecolor"] = "white"
    plt.rcParams["savefig.facecolor"] = "white"
    plt.rcParams["axes.titleweight"] = "bold"
    plt.rcParams["axes.grid"] = True
    plt.rcParams["grid.alpha"] = 0.22
    plt.rcParams["svg.fonttype"] = "none"


def plot_dataset_flow(info: dict) -> tuple[Path, Path]:
    fig, ax = plt.subplots(figsize=(12.8, 5.8))
    ax.axis("off")
    boxes = [
        ("历史目标频带数据\n291,106 行", 0.08, 0.68, "#DCEEFF"),
        ("补充真值与主动学习数据\n已包含于历史版本", 0.08, 0.38, "#EAF7EA"),
        ("20 代 GA active-band 真值\n651 条有效记录", 0.08, 0.08, "#FFF2CC"),
        ("堆叠数据\n291,757 行", 0.42, 0.50, "#F0F0F0"),
        ("physical_key 去重\n冲突物理键 57 个", 0.66, 0.50, "#F8E8E8"),
        ("v12 条件预测数据集\n46,754 行\n3,363 个结构设计", 0.86, 0.50, "#E8F4F8"),
    ]
    for text, x, y, color in boxes:
        ax.text(
            x,
            y,
            text,
            ha="center",
            va="center",
            fontsize=12,
            bbox={"boxstyle": "round,pad=0.45", "facecolor": color, "edgecolor": "#4A5568", "linewidth": 1.2},
            transform=ax.transAxes,
        )
    arrows = [
        ((0.22, 0.68), (0.34, 0.56)),
        ((0.22, 0.38), (0.34, 0.50)),
        ((0.22, 0.08), (0.34, 0.44)),
        ((0.50, 0.50), (0.58, 0.50)),
        ((0.74, 0.50), (0.80, 0.50)),
    ]
    for start, end in arrows:
        ax.annotate("", xy=end, xytext=start, xycoords=ax.transAxes, arrowprops={"arrowstyle": "->", "lw": 1.8, "color": "#2D3748"})
    ax.text(
        0.50,
        0.16,
        "清洗规则：同一 physical_key 的重复样本折叠；冲突样本优先保留 origin band 与 target band 一致的真值；20 代 GA 只追加 active-band 标签。",
        ha="center",
        va="center",
        fontsize=10.5,
        color="#2D3748",
        transform=ax.transAxes,
    )
    ax.set_title("v12 数据集构建流程", fontsize=15, pad=16)
    return save_figure(fig, "ch3_dataset_construction_flow")


def plot_band_distribution(info: dict) -> tuple[Path, Path]:
    df = pd.DataFrame(info["thesis_band_summary"]).set_index("target_band_tag").loc[THESIS_BANDS].reset_index()
    x = np.arange(len(df))
    neg = df["rows"] - df["positive_rows"]
    fig, ax1 = plt.subplots(figsize=(11.8, 5.8), constrained_layout=True)
    ax1.bar(x, df["positive_rows"], color="#2E86AB", label="正样本数")
    ax1.bar(x, neg, bottom=df["positive_rows"], color="#B8C2CC", label="非正样本数")
    ax1.set_xticks(x)
    ax1.set_xticklabels(THESIS_LABELS)
    ax1.set_ylabel("样本数")
    ax1.set_xlabel("目标频带 / Hz")
    ax1.legend(loc="upper left", frameon=True)
    for idx, row in df.iterrows():
        ax1.text(idx, row["rows"] + 18, f"{row['positive_rate']:.2f}", ha="center", va="bottom", fontsize=9)
    ax2 = ax1.twinx()
    ax2.plot(x, df["mean_cover_ratio"], color="#D1495B", marker="o", linewidth=2.2, label="平均覆盖率")
    ax2.set_ylim(0, max(0.5, df["mean_cover_ratio"].max() * 1.25))
    ax2.set_ylabel("平均覆盖率")
    ax2.legend(loc="upper right", frameon=True)
    ax1.set_title("六个目标频带样本分布与平均覆盖率")
    ax1.text(4.5, 1180, "柱顶数字为正样本率\n高频段平均覆盖率较低", ha="center", va="top", fontsize=10, color="#7A2E2E")
    return save_figure(fig, "ch3_target_band_sample_distribution")


def draw_box(ax: plt.Axes, text: str, x: float, y: float, color: str, width: float = 0.21, height: float = 0.16) -> None:
    ax.text(
        x,
        y,
        text,
        ha="center",
        va="center",
        fontsize=11.5,
        bbox={"boxstyle": "round,pad=0.42", "facecolor": color, "edgecolor": "#4A5568", "linewidth": 1.2},
        transform=ax.transAxes,
    )


def plot_model_structure() -> tuple[Path, Path]:
    fig, ax = plt.subplots(figsize=(12.2, 5.5))
    ax.axis("off")
    draw_box(ax, "结构参数 x\n傅里叶/几何参数", 0.13, 0.72, "#DCEEFF")
    draw_box(ax, "结构族与形状特征 s\nshape_family + 统计特征", 0.13, 0.48, "#EAF7EA")
    draw_box(ax, "目标频带条件 B\nlow/high/center/width", 0.13, 0.24, "#FFF2CC")
    draw_box(ax, "特征拼接与缺失值填充", 0.40, 0.48, "#F0F0F0")
    draw_box(ax, "HGB 分类器\n输出 p_open", 0.64, 0.62, "#E8F4F8")
    draw_box(ax, "HGB 回归器\n输出覆盖率 c_hat", 0.64, 0.34, "#F8E8E8")
    draw_box(ax, "候选排序分数\np_open × c_hat", 0.86, 0.48, "#EFE6FF")
    for start, end in [
        ((0.25, 0.72), (0.31, 0.52)),
        ((0.25, 0.48), (0.31, 0.48)),
        ((0.25, 0.24), (0.31, 0.44)),
        ((0.49, 0.48), (0.55, 0.60)),
        ((0.49, 0.48), (0.55, 0.36)),
        ((0.73, 0.62), (0.78, 0.52)),
        ((0.73, 0.34), (0.78, 0.44)),
    ]:
        ax.annotate("", xy=end, xytext=start, xycoords=ax.transAxes, arrowprops={"arrowstyle": "->", "lw": 1.7, "color": "#2D3748"})
    ax.text(0.64, 0.18, "回归器仅在 target_gap_is_open=1 的正样本上训练", ha="center", fontsize=10, color="#4A5568", transform=ax.transAxes)
    ax.set_title("目标频带条件预测模型结构", fontsize=15, pad=16)
    return save_figure(fig, "ch3_model_structure")


def plot_overall_validation(readiness: dict) -> tuple[Path, Path]:
    rows = [
        ("Family-CV", readiness["family_cv"]["classifier"], readiness["family_cv"]["regressor_overall"]),
        ("Band-LOO", readiness["leave_one_band"]["classifier"], readiness["leave_one_band"]["regressor_overall"]),
    ]
    cls_metrics = pd.DataFrame(
        [{"验证方式": name, "Accuracy": cls["accuracy"], "F1": cls["f1"], "Balanced Acc": cls["balanced_accuracy"]} for name, cls, _ in rows]
    )
    reg_metrics = pd.DataFrame([{"验证方式": name, "MAE": reg["mae"], "RMSE": reg["rmse"], "R2": reg["r2"]} for name, _, reg in rows])
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.4), constrained_layout=True)
    x = np.arange(len(cls_metrics))
    width = 0.24
    for i, col in enumerate(["Accuracy", "F1", "Balanced Acc"]):
        axes[0].bar(x + (i - 1) * width, cls_metrics[col], width=width, label=col)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(cls_metrics["验证方式"])
    axes[0].set_ylim(0, 1.05)
    axes[0].set_ylabel("分类指标")
    axes[0].legend(frameon=True)
    axes[0].set_title("分类器总体验证")
    x2 = np.arange(len(reg_metrics))
    axes[1].bar(x2 - 0.18, reg_metrics["MAE"], width=0.18, label="MAE", color="#2E86AB")
    axes[1].bar(x2, reg_metrics["RMSE"], width=0.18, label="RMSE", color="#F18F01")
    axes[1].bar(x2 + 0.18, reg_metrics["R2"], width=0.18, label="R²", color="#6A994E")
    axes[1].set_xticks(x2)
    axes[1].set_xticklabels(reg_metrics["验证方式"])
    axes[1].set_ylim(0, 1.05)
    axes[1].set_ylabel("回归指标")
    axes[1].legend(frameon=True)
    axes[1].set_title("覆盖率回归器总体验证")
    fig.suptitle("Family-CV 与 leave-one-band 验证结果对比", fontsize=15)
    return save_figure(fig, "ch3_overall_validation_comparison")


def plot_band_classification() -> tuple[Path, Path]:
    family = pd.read_csv(READINESS_DIR / "family_cv_classifier_by_band.csv").set_index("target_band_tag").loc[THESIS_BANDS]
    lobo = pd.read_csv(READINESS_DIR / "leave_one_band_classifier_by_band.csv").set_index("target_band_tag").loc[THESIS_BANDS]
    x = np.arange(len(THESIS_BANDS))
    width = 0.20
    fig, ax = plt.subplots(figsize=(12.6, 5.8), constrained_layout=True)
    ax.bar(x - 1.5 * width, family["f1"], width=width, label="Family-CV F1", color="#2E86AB")
    ax.bar(x - 0.5 * width, family["balanced_accuracy"], width=width, label="Family-CV 平衡准确率", color="#F18F01")
    ax.bar(x + 0.5 * width, lobo["f1"], width=width, label="Band-LOO F1", color="#6A994E")
    ax.bar(x + 1.5 * width, lobo["balanced_accuracy"], width=width, label="Band-LOO 平衡准确率", color="#D1495B")
    ax.set_xticks(x)
    ax.set_xticklabels(THESIS_LABELS)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("目标频带 / Hz")
    ax.set_ylabel("分类指标")
    ax.legend(frameon=True, ncol=2)
    ax.set_title("六个目标频带分类结果")
    return save_figure(fig, "ch3_band_classification_metrics")


def plot_band_regression() -> tuple[Path, Path]:
    family = pd.read_csv(READINESS_DIR / "family_cv_regressor_by_band.csv").set_index("target_band_tag").loc[THESIS_BANDS]
    lobo = pd.read_csv(READINESS_DIR / "leave_one_band_regressor_by_band.csv").set_index("target_band_tag").loc[THESIS_BANDS]
    x = np.arange(len(THESIS_BANDS))
    width = 0.34
    fig, ax = plt.subplots(figsize=(11.6, 5.4), constrained_layout=True)
    ax.bar(x - width / 2, family["mae"], width=width, label="Family-CV MAE", color="#2E86AB")
    ax.bar(x + width / 2, lobo["mae"], width=width, label="Band-LOO MAE", color="#F18F01")
    ax.set_xticks(x)
    ax.set_xticklabels(THESIS_LABELS)
    ax.set_xlabel("目标频带 / Hz")
    ax.set_ylabel("覆盖率 MAE")
    ax.legend(frameon=True)
    ax.set_title("六个目标频带覆盖率回归误差")
    return save_figure(fig, "ch3_band_regression_mae")


def plot_topk() -> tuple[Path, Path]:
    family = pd.read_csv(READINESS_DIR / "family_cv_topk_summary.csv")
    lobo = pd.read_csv(READINESS_DIR / "leave_one_band_topk_summary.csv")
    keep = [5, 10]
    family = family[family["k"].isin(keep)].copy()
    lobo = lobo[lobo["k"].isin(keep)].copy()
    labels = ["Top-5", "Top-10"]
    x = np.arange(len(labels))
    width = 0.18
    fig, ax1 = plt.subplots(figsize=(10.8, 5.5), constrained_layout=True)
    ax1.bar(x - 1.5 * width, family["mean_topk_hit_rate"], width=width, label="Family-CV 命中率", color="#2E86AB")
    ax1.bar(x - 0.5 * width, lobo["mean_topk_hit_rate"], width=width, label="Band-LOO 命中率", color="#6A994E")
    ax1.set_ylim(0, 1.08)
    ax1.set_ylabel("命中率")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax2 = ax1.twinx()
    ax2.plot(x + 0.12, family["mean_topk_cover"], marker="o", linewidth=2.2, label="Family-CV 平均真实覆盖率", color="#F18F01")
    ax2.plot(x + 0.12, lobo["mean_topk_cover"], marker="s", linewidth=2.2, label="Band-LOO 平均真实覆盖率", color="#D1495B")
    ax2.set_ylim(0, 0.85)
    ax2.set_ylabel("平均真实覆盖率")
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2, frameon=True, loc="lower center", ncol=2)
    ax1.set_title("Top-k 候选排序能力")
    return save_figure(fig, "ch3_topk_shortlist_quality")


def main() -> None:
    set_style()
    info = load_json(DATA_DIR / "dataset_info.json")
    readiness = load_json(READINESS_DIR / "readiness_summary.json")
    outputs = [
        ("ch3_dataset_construction_flow", *plot_dataset_flow(info), "v12 数据集构建与清洗流程示意图"),
        ("ch3_target_band_sample_distribution", *plot_band_distribution(info), "六个目标频带样本分布与平均覆盖率"),
        ("ch3_model_structure", *plot_model_structure(), "目标频带条件预测模型结构示意图"),
        ("ch3_overall_validation_comparison", *plot_overall_validation(readiness), "Family-CV 与 leave-one-band 总体验证结果对比"),
        ("ch3_band_classification_metrics", *plot_band_classification(), "六个目标频带分类性能对比"),
        ("ch3_band_regression_mae", *plot_band_regression(), "六个目标频带覆盖率回归 MAE 对比"),
        ("ch3_topk_shortlist_quality", *plot_topk(), "Top-k 候选排序能力对比"),
    ]
    pd.DataFrame(outputs, columns=["figure_id", "png_path", "svg_path", "caption_suggestion"]).to_csv(
        OUT_DIR / "ch3_figure_index.csv", index=False, encoding="utf-8-sig"
    )
    for figure_id, png, svg, caption in outputs:
        print(f"{figure_id}\\n  PNG: {png}\\n  SVG: {svg}\\n  caption: {caption}")


if __name__ == "__main__":
    main()
