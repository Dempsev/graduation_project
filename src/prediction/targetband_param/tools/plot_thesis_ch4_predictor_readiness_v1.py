from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[4]
ANALYSIS_DIR = ROOT / "data" / "analysis"
READINESS_DIR = ANALYSIS_DIR / "predictor_readiness_v1"
CH4_DIR = ANALYSIS_DIR / "thesis_ch4_v1"
FIG_DIR = CH4_DIR / "figures"

FONT_CANDIDATES = ["Microsoft YaHei", "SimHei", "SimSun", "DejaVu Sans"]


def set_plot_style() -> None:
    plt.rcParams["font.sans-serif"] = FONT_CANDIDATES
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.facecolor"] = "white"
    plt.rcParams["savefig.facecolor"] = "white"
    plt.rcParams["axes.titleweight"] = "bold"


def load_csv(name: str) -> pd.DataFrame:
    path = READINESS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing predictor readiness CSV: {path}")
    return pd.read_csv(path)


def save(fig: plt.Figure, filename: str) -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / filename
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_classifier_by_band(ax: plt.Axes, df: pd.DataFrame, title: str) -> None:
    order = df["target_band_tag"].tolist()
    x = np.arange(len(order))
    width = 0.36
    ax.bar(x - width / 2, df["f1"], width=width, label="F1", color="#2E86AB")
    ax.bar(x + width / 2, df["balanced_accuracy"], width=width, label="Balanced Acc", color="#F18F01")
    ax.set_xticks(x)
    ax.set_xticklabels(order, rotation=25, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title(title)
    ax.legend(frameon=True)


def plot_regressor_alignment(ax: plt.Axes, df: pd.DataFrame, title: str) -> None:
    ax.scatter(df["mean_true_cover"], df["mean_pred_cover"], s=70, color="#6C757D")
    for _, row in df.iterrows():
        ax.annotate(
            row["target_band_tag"],
            (row["mean_true_cover"], row["mean_pred_cover"]),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=8,
        )
    lim_max = max(df["mean_true_cover"].max(), df["mean_pred_cover"].max()) * 1.05
    lim_max = max(lim_max, 0.05)
    ax.plot([0, lim_max], [0, lim_max], linestyle="--", color="black", linewidth=1)
    ax.set_xlim(0, lim_max)
    ax.set_ylim(0, lim_max)
    ax.set_xlabel("Mean true cover")
    ax.set_ylabel("Mean predicted cover")
    ax.set_title(title)


def plot_topk_quality(ax: plt.Axes, df: pd.DataFrame, title: str) -> None:
    ax.plot(df["k"], df["mean_topk_cover"], marker="o", linewidth=2.2, color="#3A7CA5", label="Top-k mean cover")
    ax.plot(df["k"], df["mean_lift_cover"], marker="s", linewidth=2.2, color="#D1495B", label="Lift over random")
    for _, row in df.iterrows():
        ax.annotate(
            f"{row['mean_topk_cover']:.3f}",
            (row["k"], row["mean_topk_cover"]),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            fontsize=8,
        )
    ax.set_xticks(df["k"])
    ax.set_xlabel("k")
    ax.set_ylabel("Score")
    ax.set_title(title)
    ax.legend(frameon=True, ncol=2)


def plot_calibration(ax: plt.Axes, df: pd.DataFrame, title: str) -> None:
    ax.plot([0, 1], [0, 1], linestyle="--", color="black", linewidth=1, label="Ideal")
    ax.plot(df["mean_pred_prob"], df["actual_positive_rate"], marker="o", linewidth=2.2, color="#2E86AB", label="Observed")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Actual positive rate")
    ax.set_title(title)
    ax.legend(frameon=True)


def plot_monotonicity(ax: plt.Axes, df: pd.DataFrame, title: str) -> None:
    ax.plot(df["mean_pred_cover"], df["mean_true_cover"], marker="o", linewidth=2.2, color="#3A7CA5", label="Observed")
    lim_max = max(df["mean_pred_cover"].max(), df["mean_true_cover"].max()) * 1.05
    lim_max = max(lim_max, 0.05)
    ax.plot([0, lim_max], [0, lim_max], linestyle="--", color="black", linewidth=1, label="Ideal")
    ax.set_xlim(0, lim_max)
    ax.set_ylim(0, lim_max)
    ax.set_xlabel("Mean predicted cover")
    ax.set_ylabel("Mean true cover")
    ax.set_title(title)
    ax.legend(frameon=True)


def make_family_bandwise_detail() -> Path:
    cls_band = load_csv("family_cv_classifier_by_band.csv")
    reg_band = load_csv("family_cv_regressor_by_band.csv")

    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.8), constrained_layout=True)
    plot_classifier_by_band(axes[0], cls_band, "Family-CV classifier by band")
    plot_regressor_alignment(axes[1], reg_band, "Family-CV regressor alignment by band")
    fig.suptitle("Chapter 4 family-CV band-wise detail", y=1.02, fontsize=13)
    return save(fig, "figure_4_3_family_cv_bandwise_detail.png")


def make_family_operating_characteristics() -> Path:
    cal_df = load_csv("family_cv_classifier_calibration.csv")
    mon_df = load_csv("family_cv_regressor_monotonicity.csv")

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.8), constrained_layout=True)
    plot_calibration(axes[0], cal_df, "Classifier calibration")
    plot_monotonicity(axes[1], mon_df, "Regressor monotonicity")
    fig.suptitle("Chapter 4 operating characteristics", y=1.02, fontsize=13)
    return save(fig, "figure_4_4_family_cv_operating_characteristics.png")


def make_leave_one_band_detail() -> Path:
    cls_band = load_csv("leave_one_band_classifier_by_band.csv")
    reg_band = load_csv("leave_one_band_regressor_by_band.csv")
    topk = load_csv("leave_one_band_topk_summary.csv")

    fig, axes = plt.subplots(1, 3, figsize=(16.0, 4.8), constrained_layout=True)
    plot_classifier_by_band(axes[0], cls_band, "Leave-one-band classifier by band")
    plot_regressor_alignment(axes[1], reg_band, "Leave-one-band regressor alignment by band")
    plot_topk_quality(axes[2], topk, "Leave-one-band shortlist quality")
    fig.suptitle("Chapter 4 leave-one-band detail", y=1.02, fontsize=13)
    return save(fig, "figure_4_5_leave_one_band_detail.png")


def make_family_classifier_by_band() -> Path:
    cls_band = load_csv("family_cv_classifier_by_band.csv")
    fig, ax = plt.subplots(figsize=(10.5, 4.8), constrained_layout=True)
    plot_classifier_by_band(ax, cls_band, "Family-CV classifier by band")
    return save(fig, "figure_4_2_family_cv_classifier_by_band.png")


def make_family_regressor_alignment() -> Path:
    reg_band = load_csv("family_cv_regressor_by_band.csv")
    fig, ax = plt.subplots(figsize=(6.8, 5.8), constrained_layout=True)
    plot_regressor_alignment(ax, reg_band, "Family-CV regressor alignment by band")
    return save(fig, "figure_4_3_family_cv_regressor_alignment.png")


def make_family_calibration() -> Path:
    cal_df = load_csv("family_cv_classifier_calibration.csv")
    fig, ax = plt.subplots(figsize=(6.5, 5.5), constrained_layout=True)
    plot_calibration(ax, cal_df, "Classifier calibration")
    return save(fig, "figure_4_4_family_cv_classifier_calibration.png")


def make_family_monotonicity() -> Path:
    mon_df = load_csv("family_cv_regressor_monotonicity.csv")
    fig, ax = plt.subplots(figsize=(6.5, 5.5), constrained_layout=True)
    plot_monotonicity(ax, mon_df, "Regressor monotonicity")
    return save(fig, "figure_4_5_family_cv_regressor_monotonicity.png")


def make_family_shortlist_quality() -> Path:
    topk = load_csv("family_cv_topk_summary.csv")
    fig, ax = plt.subplots(figsize=(6.8, 5.2), constrained_layout=True)
    plot_topk_quality(ax, topk, "Family-CV shortlist quality")
    return save(fig, "figure_4_6_family_cv_shortlist_quality.png")


def make_leave_one_band_classifier_by_band() -> Path:
    cls_band = load_csv("leave_one_band_classifier_by_band.csv")
    fig, ax = plt.subplots(figsize=(10.5, 4.8), constrained_layout=True)
    plot_classifier_by_band(ax, cls_band, "Leave-one-band classifier by band")
    return save(fig, "figure_4_7_leave_one_band_classifier_by_band.png")


def make_leave_one_band_regressor_alignment() -> Path:
    reg_band = load_csv("leave_one_band_regressor_by_band.csv")
    fig, ax = plt.subplots(figsize=(6.8, 5.8), constrained_layout=True)
    plot_regressor_alignment(ax, reg_band, "Leave-one-band regressor alignment by band")
    return save(fig, "figure_4_8_leave_one_band_regressor_alignment.png")


def make_leave_one_band_shortlist_quality() -> Path:
    topk = load_csv("leave_one_band_topk_summary.csv")
    fig, ax = plt.subplots(figsize=(6.8, 5.2), constrained_layout=True)
    plot_topk_quality(ax, topk, "Leave-one-band shortlist quality")
    return save(fig, "figure_4_9_leave_one_band_shortlist_quality.png")


def main() -> None:
    set_plot_style()
    outputs = [
        make_family_classifier_by_band(),
        make_family_regressor_alignment(),
        make_family_calibration(),
        make_family_monotonicity(),
        make_family_shortlist_quality(),
        make_leave_one_band_classifier_by_band(),
        make_leave_one_band_regressor_alignment(),
        make_leave_one_band_shortlist_quality(),
    ]
    for path in outputs:
        print(path)


if __name__ == "__main__":
    main()
