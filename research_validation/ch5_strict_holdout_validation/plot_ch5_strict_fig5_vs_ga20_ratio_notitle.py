from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from build_ch5_strict_holdout_validation_v1 import FIG_DIR, PALETTE, configure_fonts, style_axis


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "research_validation" / "ch5_strict_holdout_validation"
SOURCE = OUT_DIR / "ch5_strict_holdout_vs_ga20.csv"
STEM = "ch5_strict_fig5_vs_ga20_ratio_notitle"


def main() -> None:
    configure_fonts()
    plt.rcParams.update(
        {
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
        }
    )
    comp = pd.read_csv(SOURCE, low_memory=False)
    labels = [
        "140–180 Hz",
        "160–200 Hz",
        "180–220 Hz",
        "200–240 Hz",
        "220–260 Hz",
        "240–280 Hz",
    ]
    values = [
        float(comp.loc[comp["target_band"].eq(label), "strict_pred_top5_to_ga_overlap_ratio"].iloc[0])
        if len(comp.loc[comp["target_band"].eq(label)])
        else 0.0
        for label in labels
    ]

    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    x = range(len(labels))
    ax.bar(x, values, width=0.55, color=PALETTE["predicted_top5"], edgecolor="#333333", linewidth=0.7, alpha=0.88)
    ax.axhline(1.0, color="#666666", linewidth=0.9, linestyle="--")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_xlabel("目标频带", fontsize=10)
    ax.set_ylabel("Top-5 / GA20 最优重叠宽度", fontsize=10)
    ax.tick_params(axis="both", labelsize=9)
    style_axis(ax)
    fig.tight_layout()

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ["png", "svg", "pdf"]:
        path = FIG_DIR / f"{STEM}.{ext}"
        if ext == "png":
            fig.savefig(path, dpi=300, bbox_inches="tight")
        else:
            fig.savefig(path, bbox_inches="tight")
        print(path)
    plt.close(fig)


if __name__ == "__main__":
    main()
