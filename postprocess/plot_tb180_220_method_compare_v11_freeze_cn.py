from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "analysis" / "targetband_180_220_method_compare_v11_12gen_freeze_v1"
FIG_DIR = OUT_DIR / "figures"

PRED_RESULTS = (
    ROOT
    / "data"
    / "comsol_batch"
    / "stage4_validation_targetband180_220_predictor_top6_v11_12gen_freeze_v1"
    / "stage4_validation_results.csv"
)
RAND_RESULTS = (
    ROOT
    / "data"
    / "comsol_batch"
    / "stage4_validation_targetband180_220_random6_v11_12gen_freeze_v1"
    / "stage4_validation_results.csv"
)
GA_HISTORY = ROOT / "data" / "comsol_batch" / "comsol_in_loop_targetband180_220_overlap_ga_v1" / "ga_history_v1.csv"

TARGET_LOW = 180.0
TARGET_HIGH = 220.0


def configure_fonts() -> None:
    available = {font.name for font in font_manager.fontManager.ttflist}
    for name in ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Source Han Sans SC", "Arial Unicode MS"]:
        if name in available:
            plt.rcParams["font.sans-serif"] = [name]
            break
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["svg.fonttype"] = "none"
    plt.rcParams["font.size"] = 10


def add_target_overlap(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    solve_success = out["solve_success"].astype(str).str.lower().isin(["1", "true"])
    out["target_overlap_Hz"] = 0.0
    overlap = (
        out.loc[solve_success, "gap34_upper_edge_Hz"].clip(upper=TARGET_HIGH)
        - out.loc[solve_success, "gap34_lower_edge_Hz"].clip(lower=TARGET_LOW)
    ).clip(lower=0)
    out.loc[solve_success, "target_overlap_Hz"] = overlap
    return out


def load_method_rows() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    pred = add_target_overlap(pd.read_csv(PRED_RESULTS))
    rand = add_target_overlap(pd.read_csv(RAND_RESULTS))
    ga = pd.read_csv(GA_HISTORY)
    ga["eval_index"] = range(1, len(ga) + 1)
    ga["target_overlap_Hz"] = pd.to_numeric(ga["fitness"], errors="coerce").clip(lower=0)
    ga["best_so_far_target_overlap_Hz"] = ga["target_overlap_Hz"].cummax()
    return pred, rand, ga


def summarize(pred: pd.DataFrame, rand: pd.DataFrame, ga: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for method, label, df in [
        ("random6", "随机均衡筛选", rand),
        ("predictor_top6", "条件预测筛选", pred),
    ]:
        solve_success = df["solve_success"].astype(str).str.lower().isin(["1", "true"])
        contact_valid = df["contact_valid"].astype(str).str.lower().isin(["1", "true"])
        rows.append(
            {
                "method": method,
                "label_cn": label,
                "true_evals": int(len(df)),
                "solve_success_count": int(solve_success.sum()),
                "contact_valid_count": int(contact_valid.sum()),
                "best_target_overlap_Hz": float(df["target_overlap_Hz"].max()),
                "mean_target_overlap_Hz": float(df["target_overlap_Hz"].mean()),
            }
        )
    rows.append(
        {
            "method": "real_ga_120",
            "label_cn": "真实 GA",
            "true_evals": int(len(ga)),
            "solve_success_count": int((ga["solve_success"].astype(str).str.lower().isin(["1", "true"])).sum()),
            "contact_valid_count": int((ga["contact_valid"].astype(str).str.lower().isin(["1", "true"])).sum()),
            "best_target_overlap_Hz": float(ga["best_so_far_target_overlap_Hz"].max()),
            "mean_target_overlap_Hz": float("nan"),
        }
    )
    return pd.DataFrame(rows)


def plot_budget_curve(summary: pd.DataFrame, ga: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.plot(
        ga["eval_index"],
        ga["best_so_far_target_overlap_Hz"],
        color="#355C9A",
        marker="o",
        markersize=3,
        linewidth=1.8,
        label="真实 GA 当前最优",
    )

    rand_best = float(summary.loc[summary["method"] == "random6", "best_target_overlap_Hz"].iloc[0])
    pred_best = float(summary.loc[summary["method"] == "predictor_top6", "best_target_overlap_Hz"].iloc[0])
    ax.scatter([6], [rand_best], s=90, color="#9e9e9e", edgecolor="black", zorder=5, label="随机 6 次")
    ax.scatter([6], [pred_best], s=110, color="#2E9F7E", edgecolor="black", zorder=6, label="条件预测 6 次")
    ax.annotate(f"条件预测 {pred_best:.1f} Hz", xy=(6, pred_best), xytext=(10, pred_best + 1.0), fontsize=9)
    ax.annotate(f"随机 {rand_best:.1f} Hz", xy=(6, rand_best), xytext=(10, rand_best - 2.0), fontsize=9)

    ax.set_xlim(0, max(ga["eval_index"]) + 3)
    ax.set_ylim(0, 43)
    ax.set_xlabel("真实 COMSOL 评价次数")
    ax.set_ylabel("当前最优目标频带重叠宽度 / Hz")
    ax.grid(alpha=0.22)
    ax.legend(frameon=True, loc="lower right")
    fig.tight_layout()
    stem = FIG_DIR / "figure_5_6a_budget_efficiency_tb180_220_v11_cn_titleless"
    fig.savefig(f"{stem}.svg", bbox_inches="tight")
    fig.savefig(f"{stem}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_method_best(summary: pd.DataFrame) -> None:
    pred = pd.read_csv(OUT_DIR / "predictor_top6_comsol_truth_tb180_220_v11.csv")
    pred_best = float(summary.loc[summary["method"] == "predictor_top6", "best_target_overlap_Hz"].iloc[0])
    pred_model_best = float(pd.to_numeric(pred["surrogate_pred_gap34_gain_Hz"], errors="coerce").max())
    pred_of_truth_best = float(
        pred.loc[pd.to_numeric(pred["target_overlap_Hz"], errors="coerce").idxmax(), "surrogate_pred_gap34_gain_Hz"]
    )

    plot_df = pd.DataFrame(
        [
            {
                "label_cn": "随机均衡筛选\nCOMSOL 真值",
                "value": float(summary.loc[summary["method"] == "random6", "best_target_overlap_Hz"].iloc[0]),
                "evals": 6,
                "color": "#9E9E9E",
                "hatch": "",
            },
            {
                "label_cn": "条件预测筛选\n对应预测值",
                "value": pred_of_truth_best,
                "evals": 0,
                "color": "#78C5AE",
                "hatch": "//",
            },
            {
                "label_cn": "条件预测筛选\nCOMSOL 真值",
                "value": pred_best,
                "evals": 6,
                "color": "#2E9F7E",
                "hatch": "",
            },
            {
                "label_cn": "真实 GA\nCOMSOL 真值",
                "value": float(summary.loc[summary["method"] == "real_ga_120", "best_target_overlap_Hz"].iloc[0]),
                "evals": 120,
                "color": "#355C9A",
                "hatch": "",
            },
        ]
    )
    summary_extra = pd.DataFrame(
        [
            {
                "metric": "predictor_top6_model_predicted_best_Hz",
                "value": pred_model_best,
                "note": "maximum model-predicted target overlap among predictor Top-6",
            },
            {
                "metric": "predictor_top6_prediction_of_truth_best_Hz",
                "value": pred_of_truth_best,
                "note": "model prediction for the predictor Top-6 candidate with the best COMSOL truth",
            },
        ]
    )
    summary_extra.to_csv(OUT_DIR / "method_compare_prediction_extra_tb180_220_v11.csv", index=False, encoding="utf-8-sig")

    fig, ax = plt.subplots(figsize=(6.3, 4.1))
    bars = ax.bar(
        plot_df["label_cn"],
        plot_df["value"],
        color=plot_df["color"],
        edgecolor="#333333",
        linewidth=0.8,
    )
    for bar, (_, row) in zip(bars, plot_df.iterrows()):
        if row["hatch"]:
            bar.set_hatch(row["hatch"])
        eval_text = "无真实求解" if int(row["evals"]) == 0 else f"{int(row['evals'])} 次"
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.7,
            f"{row['value']:.1f} Hz\n{eval_text}",
            ha="center",
            va="bottom",
            fontsize=8.3,
        )
    ax.set_ylim(0, 44)
    ax.set_ylabel("目标频带重叠宽度 / Hz")
    ax.tick_params(axis="x", labelsize=8.2)
    ax.grid(axis="y", alpha=0.22)
    fig.tight_layout()
    stem = FIG_DIR / "figure_5_6b_best_overlap_tb180_220_v11_cn_titleless"
    fig.savefig(f"{stem}.svg", bbox_inches="tight")
    fig.savefig(f"{stem}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    configure_fonts()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    pred, rand, ga = load_method_rows()

    summary = summarize(pred, rand, ga)
    summary.to_csv(OUT_DIR / "method_compare_summary_tb180_220_v11.csv", index=False, encoding="utf-8-sig")

    pred.to_csv(OUT_DIR / "predictor_top6_comsol_truth_tb180_220_v11.csv", index=False, encoding="utf-8-sig")
    rand.to_csv(OUT_DIR / "random6_comsol_truth_tb180_220_v11.csv", index=False, encoding="utf-8-sig")
    ga[["eval_index", "sample_id", "shape_id", "fitness", "target_overlap_Hz", "best_so_far_target_overlap_Hz"]].to_csv(
        OUT_DIR / "real_ga_120_best_so_far_tb180_220_v11.csv",
        index=False,
        encoding="utf-8-sig",
    )

    plot_budget_curve(summary, ga)
    plot_method_best(summary)
    print(summary)
    print(FIG_DIR)


if __name__ == "__main__":
    sys.exit(main())
