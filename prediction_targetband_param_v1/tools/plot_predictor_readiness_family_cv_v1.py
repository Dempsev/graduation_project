from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
FREEZE_CONFIG = ROOT / "prediction_targetband_param_v1" / "configs" / "targetband_mainline_freeze_v1.json"
ANALYSIS_DIR = ROOT / "data" / "analysis" / "predictor_readiness_v1"
FIG_DIR = ANALYSIS_DIR / "figures"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_div(num: float, den: float) -> float:
    return float("nan") if den == 0 else float(num) / float(den)


def load_thesis_band_tags() -> list[str]:
    freeze_cfg = load_json(FREEZE_CONFIG)
    catalog_path = ROOT / freeze_cfg["frozen_mainline"]["thesis_band_catalog"]
    catalog = load_json(catalog_path)
    return [item["target_band_tag"] for item in catalog["bands"]]


def thesis_band_filter(df: pd.DataFrame, catalog_tags: set[str]) -> pd.DataFrame:
    return df[df["target_band_tag"].isin(catalog_tags)].copy()


def calc_cls_metrics(df: pd.DataFrame) -> dict:
    y_true = df["y_true"].astype(int)
    y_pred = df["y_pred"].astype(int)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    f1 = float("nan") if np.isnan(precision) or np.isnan(recall) or (precision + recall) == 0 else 2 * precision * recall / (precision + recall)
    tpr = safe_div(tp, tp + fn)
    tnr = safe_div(tn, tn + fp)
    bal_acc = np.nanmean([tpr, tnr])
    acc = safe_div(tp + tn, len(df))
    return {
        "rows": int(len(df)),
        "positive_rate": float(y_true.mean()),
        "accuracy": float(acc),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "balanced_accuracy": float(bal_acc),
    }


def build_calibration_table(df: pd.DataFrame, bins: int = 10) -> pd.DataFrame:
    work = df[["y_true", "y_prob"]].copy()
    work["bin"] = pd.qcut(work["y_prob"], q=bins, duplicates="drop")
    rows = []
    for _, part in work.groupby("bin", observed=True):
        rows.append(
            {
                "rows": int(len(part)),
                "mean_pred_prob": float(part["y_prob"].mean()),
                "actual_positive_rate": float(part["y_true"].mean()),
                "gap_pred_minus_actual": float(part["y_prob"].mean() - part["y_true"].mean()),
            }
        )
    return pd.DataFrame(rows)


def build_monotonicity_table(df: pd.DataFrame, bins: int = 10) -> pd.DataFrame:
    work = df[["y_true", "y_pred"]].copy()
    work["bin"] = pd.qcut(work["y_pred"], q=bins, duplicates="drop")
    rows = []
    for _, part in work.groupby("bin", observed=True):
        rows.append(
            {
                "rows": int(len(part)),
                "mean_pred_cover": float(part["y_pred"].mean()),
                "mean_true_cover": float(part["y_true"].mean()),
                "mean_abs_error": float((part["y_pred"] - part["y_true"]).abs().mean()),
            }
        )
    return pd.DataFrame(rows)


def merge_cls_reg(cls_df: pd.DataFrame, reg_df: pd.DataFrame) -> pd.DataFrame:
    cls_work = cls_df.rename(columns={"y_true": "cls_true", "y_prob": "cls_prob", "y_pred": "cls_pred"})
    reg_work = reg_df.rename(columns={"y_true": "reg_true", "y_pred": "reg_pred"})
    merged = cls_work.merge(
        reg_work[
            [
                "fold",
                "param_sample_id",
                "design_id",
                "shape_id",
                "shape_family",
                "target_band_tag",
                "target_band_low_Hz",
                "target_band_high_Hz",
                "reg_true",
                "reg_pred",
            ]
        ],
        on=[
            "fold",
            "param_sample_id",
            "design_id",
            "shape_id",
            "shape_family",
            "target_band_tag",
            "target_band_low_Hz",
            "target_band_high_Hz",
        ],
        how="inner",
    )
    merged["shortlist_score"] = merged["cls_prob"] * merged["reg_pred"].clip(lower=0)
    return merged


def summarize_topk(merged: pd.DataFrame, ks: list[int]) -> pd.DataFrame:
    rows = []
    for fold, part in merged.groupby("fold"):
        part = part.sort_values(["shortlist_score", "cls_prob", "reg_pred"], ascending=False).reset_index(drop=True)
        random_positive_rate = float(part["cls_true"].mean())
        random_cover_mean = float(part["reg_true"].mean())
        for k in ks:
            top = part.head(min(k, len(part)))
            rows.append(
                {
                    "fold": fold,
                    "k": int(k),
                    "rows_considered": int(len(top)),
                    "topk_hit_rate": float(top["cls_true"].mean()),
                    "topk_mean_cover": float(top["reg_true"].mean()),
                    "topk_total_cover": float(top["reg_true"].sum()),
                    "topk_mean_prob": float(top["cls_prob"].mean()),
                    "topk_mean_pred_cover": float(top["reg_pred"].mean()),
                    "random_positive_rate": random_positive_rate,
                    "random_mean_cover": random_cover_mean,
                    "lift_hit_rate": float(top["cls_true"].mean() - random_positive_rate),
                    "lift_mean_cover": float(top["reg_true"].mean() - random_cover_mean),
                }
            )
    return pd.DataFrame(rows)


def aggregate_topk(topk_df: pd.DataFrame) -> pd.DataFrame:
    return topk_df.groupby("k", as_index=False).agg(
        folds=("fold", "nunique"),
        mean_topk_hit_rate=("topk_hit_rate", "mean"),
        mean_topk_cover=("topk_mean_cover", "mean"),
        mean_lift_hit_rate=("lift_hit_rate", "mean"),
        mean_lift_cover=("lift_mean_cover", "mean"),
        mean_topk_prob=("topk_mean_prob", "mean"),
        mean_topk_pred_cover=("topk_mean_pred_cover", "mean"),
    )


def prepare_outputs() -> dict[str, Path]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "analysis": ANALYSIS_DIR,
        "figures": FIG_DIR,
    }


def set_style() -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update(
        {
            "figure.dpi": 160,
            "savefig.dpi": 300,
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
        }
    )


def plot_family_cv_main(
    out_path: Path,
    thesis_band_order: list[str],
    cls_band: pd.DataFrame,
    reg_band: pd.DataFrame,
    topk_summary: pd.DataFrame,
) -> None:
    band_order = thesis_band_order
    cls_band = cls_band.set_index("target_band_tag").reindex(band_order).reset_index()
    reg_band = reg_band.set_index("target_band_tag").reindex(band_order).reset_index()

    fig = plt.figure(figsize=(14, 9), constrained_layout=True)
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.05])
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, :])

    x = np.arange(len(band_order))
    width = 0.36
    ax1.bar(x - width / 2, cls_band["f1"], width=width, label="F1", color="#2E86AB")
    ax1.bar(x + width / 2, cls_band["balanced_accuracy"], width=width, label="Balanced Acc", color="#F18F01")
    ax1.set_xticks(x)
    ax1.set_xticklabels(band_order, rotation=25, ha="right")
    ax1.set_ylim(0, 1.05)
    ax1.set_ylabel("Score")
    ax1.set_title("Classifier by band")
    ax1.legend(frameon=True)

    ax2.scatter(reg_band["mean_true_cover"], reg_band["mean_pred_cover"], s=70, color="#6C757D")
    for _, row in reg_band.iterrows():
        ax2.annotate(row["target_band_tag"], (row["mean_true_cover"], row["mean_pred_cover"]), xytext=(4, 4), textcoords="offset points", fontsize=8)
    lim_max = max(reg_band["mean_true_cover"].max(), reg_band["mean_pred_cover"].max()) * 1.05
    ax2.plot([0, lim_max], [0, lim_max], linestyle="--", color="black", linewidth=1)
    ax2.set_xlim(0, lim_max)
    ax2.set_ylim(0, lim_max)
    ax2.set_xlabel("Mean true cover")
    ax2.set_ylabel("Mean predicted cover")
    ax2.set_title("Regressor alignment by band")

    ax3.plot(topk_summary["k"], topk_summary["mean_topk_cover"], marker="o", linewidth=2.2, color="#3A7CA5", label="Top-k mean cover")
    ax3.plot(topk_summary["k"], topk_summary["mean_lift_cover"], marker="s", linewidth=2.2, color="#D1495B", label="Lift over random")
    for _, row in topk_summary.iterrows():
        ax3.annotate(f"{row['mean_topk_cover']:.3f}", (row["k"], row["mean_topk_cover"]), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=8)
    ax3.set_xticks(topk_summary["k"])
    ax3.set_xlabel("k")
    ax3.set_ylabel("Score")
    ax3.set_title("Shortlist quality")
    ax3.legend(frameon=True, ncol=2)

    fig.suptitle("Family-CV predictor readiness summary", y=1.02, fontsize=13)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def plot_family_cv_classifier_by_band(out_path: Path, thesis_band_order: list[str], cls_band: pd.DataFrame) -> None:
    cls_band = cls_band.set_index("target_band_tag").reindex(thesis_band_order).reset_index()
    x = np.arange(len(thesis_band_order))
    width = 0.36

    fig, ax = plt.subplots(figsize=(10.5, 4.8), constrained_layout=True)
    ax.bar(x - width / 2, cls_band["f1"], width=width, label="F1", color="#2E86AB")
    ax.bar(x + width / 2, cls_band["balanced_accuracy"], width=width, label="Balanced Acc", color="#F18F01")
    ax.set_xticks(x)
    ax.set_xticklabels(thesis_band_order, rotation=25, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("Family-CV classifier by band")
    ax.legend(frameon=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def plot_family_cv_regressor_alignment(out_path: Path, reg_band: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(6.8, 5.8), constrained_layout=True)
    ax.scatter(reg_band["mean_true_cover"], reg_band["mean_pred_cover"], s=70, color="#6C757D")
    for _, row in reg_band.iterrows():
        ax.annotate(row["target_band_tag"], (row["mean_true_cover"], row["mean_pred_cover"]), xytext=(4, 4), textcoords="offset points", fontsize=8)
    lim_max = max(reg_band["mean_true_cover"].max(), reg_band["mean_pred_cover"].max()) * 1.05
    ax.plot([0, lim_max], [0, lim_max], linestyle="--", color="black", linewidth=1)
    ax.set_xlim(0, lim_max)
    ax.set_ylim(0, lim_max)
    ax.set_xlabel("Mean true cover")
    ax.set_ylabel("Mean predicted cover")
    ax.set_title("Family-CV regressor alignment by band")
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def plot_family_cv_shortlist_quality(out_path: Path, topk_summary: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(6.8, 5.2), constrained_layout=True)
    ax.plot(topk_summary["k"], topk_summary["mean_topk_cover"], marker="o", linewidth=2.2, color="#3A7CA5", label="Top-k mean cover")
    ax.plot(topk_summary["k"], topk_summary["mean_lift_cover"], marker="s", linewidth=2.2, color="#D1495B", label="Lift over random")
    for _, row in topk_summary.iterrows():
        ax.annotate(f"{row['mean_topk_cover']:.3f}", (row["k"], row["mean_topk_cover"]), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=8)
    ax.set_xticks(topk_summary["k"])
    ax.set_xlabel("k")
    ax.set_ylabel("Score")
    ax.set_title("Family-CV shortlist quality")
    ax.legend(frameon=True, ncol=1)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def plot_family_cv_calibration(out_path: Path, cal_df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(6.5, 5.5), constrained_layout=True)
    ax.plot([0, 1], [0, 1], linestyle="--", color="black", linewidth=1, label="Ideal")
    ax.plot(cal_df["mean_pred_prob"], cal_df["actual_positive_rate"], marker="o", linewidth=2.2, color="#2E86AB", label="Observed")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Actual positive rate")
    ax.set_title("Classifier calibration")
    ax.legend(frameon=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def plot_family_cv_monotonicity(out_path: Path, mon_df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(6.5, 5.5), constrained_layout=True)
    ax.plot(mon_df["mean_pred_cover"], mon_df["mean_true_cover"], marker="o", linewidth=2.2, color="#3A7CA5", label="Observed")
    ax.plot([0, 1], [0, 1], linestyle="--", color="black", linewidth=1, label="Ideal")
    ax.set_xlim(0, max(1.0, float(max(mon_df["mean_pred_cover"].max(), mon_df["mean_true_cover"].max()) * 1.05)))
    ax.set_ylim(0, max(1.0, float(max(mon_df["mean_pred_cover"].max(), mon_df["mean_true_cover"].max()) * 1.05)))
    ax.set_xlabel("Mean predicted cover")
    ax.set_ylabel("Mean true cover")
    ax.set_title("Regressor monotonicity")
    ax.legend(frameon=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    set_style()
    paths = prepare_outputs()

    cls_path = ROOT / "data" / "prediction_targetband_param_v1_runs" / "param_targetband_cls_rf_dense_v8_cmp_v1" / "stratified_group_kfold" / "predictions.csv"
    reg_path = ROOT / "data" / "prediction_targetband_param_v1_runs" / "param_targetband_cover_hgb_dense_v8_cmp_v1" / "stratified_group_kfold" / "predictions.csv"

    cls_df = pd.read_csv(cls_path)
    reg_df = pd.read_csv(reg_path)

    thesis_band_order = load_thesis_band_tags()
    catalog_tags = set(thesis_band_order)

    cls_thesis = thesis_band_filter(cls_df, catalog_tags)
    reg_thesis = thesis_band_filter(reg_df, catalog_tags)

    cls_rows = []
    for tag, part in cls_thesis.groupby("target_band_tag", observed=True):
        row = {"target_band_tag": tag}
        row.update(calc_cls_metrics(part))
        cls_rows.append(row)
    cls_by_band = pd.DataFrame(cls_rows)
    reg_by_band = reg_thesis.groupby("target_band_tag", as_index=False).agg(
        rows=("y_true", "size"),
        mean_true_cover=("y_true", "mean"),
        mean_pred_cover=("y_pred", "mean"),
        mae=("abs_error", "mean"),
    )

    merged = merge_cls_reg(cls_thesis, reg_thesis)
    topk = summarize_topk(merged, ks=[5, 10, 20, 50])
    topk_summary = aggregate_topk(topk)
    cal_df = build_calibration_table(cls_thesis)
    mon_df = build_monotonicity_table(reg_thesis)

    cls_by_band.to_csv(paths["analysis"] / "family_cv_classifier_by_band.csv", index=False)
    reg_by_band.to_csv(paths["analysis"] / "family_cv_regressor_by_band.csv", index=False)
    topk.to_csv(paths["analysis"] / "family_cv_topk_by_fold.csv", index=False)
    topk_summary.to_csv(paths["analysis"] / "family_cv_topk_summary.csv", index=False)
    cal_df.to_csv(paths["analysis"] / "family_cv_classifier_calibration.csv", index=False)
    mon_df.to_csv(paths["analysis"] / "family_cv_regressor_monotonicity.csv", index=False)

    readiness = {
        "family_cv": {
            "classifier": calc_cls_metrics(cls_thesis),
            "topk": topk_summary.to_dict(orient="records"),
        }
    }
    (paths["analysis"] / "readiness_summary.json").write_text(json.dumps(readiness, indent=2), encoding="utf-8")

    plot_family_cv_main(paths["figures"] / "family_cv_readiness_summary.png", thesis_band_order, cls_by_band, reg_by_band, topk_summary)
    plot_family_cv_classifier_by_band(paths["figures"] / "family_cv_classifier_by_band.png", thesis_band_order, cls_by_band)
    plot_family_cv_regressor_alignment(paths["figures"] / "family_cv_regressor_alignment.png", reg_by_band)
    plot_family_cv_shortlist_quality(paths["figures"] / "family_cv_shortlist_quality.png", topk_summary)
    plot_family_cv_calibration(paths["figures"] / "family_cv_classifier_calibration.png", cal_df)
    plot_family_cv_monotonicity(paths["figures"] / "family_cv_regressor_monotonicity.png", mon_df)

    print(f"Saved analysis CSVs to: {paths['analysis']}")
    print(f"Saved figures to: {paths['figures']}")


if __name__ == "__main__":
    main()
