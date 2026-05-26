from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "research_validation" / "ch5_strict_holdout_validation"
FIG_DIR = OUT_DIR / "figures"
CH4_SUMMARY = ROOT / "research_validation" / "ch4_ga_real_optimization" / "ch4_ga_summary_20gen.csv"
STRICT_RESULTS = OUT_DIR / "ch5_strict_holdout_comsol_results_top5_random5.csv"
STEM = "ch5_strict_fig6_budget_efficiency_band180_220"


def configure_fonts() -> None:
    for path in [Path(r"C:\Windows\Fonts\msyh.ttc"), Path(r"C:\Windows\Fonts\simhei.ttf"), Path(r"C:\Windows\Fonts\simsun.ttc")]:
        if path.exists():
            font_manager.fontManager.addfont(str(path))
            font_name = font_manager.FontProperties(fname=str(path)).get_name()
            break
    else:
        font_name = "DejaVu Sans"
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [font_name, "DejaVu Sans"],
            "axes.unicode_minus": False,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "axes.edgecolor": "#222222",
            "axes.labelcolor": "#222222",
            "text.color": "#222222",
            "xtick.color": "#222222",
            "ytick.color": "#222222",
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
        }
    )


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    configure_fonts()

    summary = pd.read_csv(CH4_SUMMARY)
    ga_dir = Path(summary.loc[summary["target_band_tag"].eq("band180_220"), "output_dir"].iloc[0])
    history = pd.read_csv(ga_dir / "ga_history_v1.csv")
    overlap = pd.to_numeric(history["active_target_overlap_Hz"], errors="coerce").fillna(0.0)
    x_ga = np.arange(1, len(overlap) + 1)
    best_so_far = overlap.cummax()

    strict = pd.read_csv(STRICT_RESULTS)
    band = strict[strict["target_band_tag"].eq("band180_220")].copy()
    pred_best = float(pd.to_numeric(band.loc[band["method"].eq("predicted_top5"), "true_overlap_Hz"], errors="coerce").fillna(0.0).max())
    random_best = float(pd.to_numeric(band.loc[band["method"].eq("random5"), "true_overlap_Hz"], errors="coerce").fillna(0.0).max())

    fig, ax = plt.subplots(figsize=(6.4, 3.7))
    ax.plot(
        x_ga,
        best_so_far,
        color="#4E79A7",
        linewidth=1.8,
        marker="o",
        markersize=2.4,
        markevery=1,
        label="真实 GA20 当前最优",
        zorder=2,
    )
    ax.scatter([5], [pred_best], s=78, color="#2CA58D", edgecolor="#222222", linewidth=0.9, label="预测 Top5", zorder=4)
    ax.scatter([5], [random_best], s=78, color="#BDBDBD", edgecolor="#222222", linewidth=0.9, label="随机5", zorder=4)
    ax.annotate(f"预测 Top5 {pred_best:.2f} Hz", xy=(5, pred_best), xytext=(12, pred_best - 1.2), fontsize=9)
    ax.annotate(f"随机5 {random_best:.2f} Hz", xy=(5, random_best), xytext=(12, random_best - 1.2), fontsize=9)

    ax.set_xlabel("真实 COMSOL 评价次数", fontsize=11)
    ax.set_ylabel("当前最优目标频带重叠宽度 / Hz", fontsize=11)
    ax.set_xlim(0, max(122, len(overlap) + 2))
    ax.set_ylim(0, max(42, float(best_so_far.max()) + 2))
    ax.grid(axis="both", color="#D9D9D9", linewidth=0.6, alpha=0.65)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(True)
    ax.spines["right"].set_visible(True)
    for spine in ax.spines.values():
        spine.set_linewidth(0.8)
        spine.set_color("#222222")
    ax.tick_params(labelsize=10)
    ax.legend(loc="lower right", fontsize=9, frameon=True)
    fig.tight_layout()

    outputs = []
    for ext in ["png", "svg", "pdf"]:
        path = FIG_DIR / f"{STEM}.{ext}"
        if ext == "png":
            fig.savefig(path, dpi=300, bbox_inches="tight")
        else:
            fig.savefig(path, bbox_inches="tight")
        outputs.append(path)
    plt.close(fig)

    print("Generated budget efficiency figure:")
    print(f"GA20 history: {ga_dir / 'ga_history_v1.csv'}")
    print(f"predicted Top5 best: {pred_best:.6f} Hz")
    print(f"random5 best: {random_best:.6f} Hz")
    for path in outputs:
        print(path)


if __name__ == "__main__":
    main()
