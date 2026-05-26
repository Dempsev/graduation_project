from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "data" / "analysis" / "targetband_active_learning_v11_12gen_freeze_v1"
FIG_DIR = ANALYSIS_DIR / "figures"
INPUT_CSV = ANALYSIS_DIR / "holdout_origin_band_top1_prediction_v11_12gen_freeze_v1.csv"


def configure_fonts() -> None:
    available = {font.name for font in font_manager.fontManager.ttflist}
    for name in ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Source Han Sans SC", "Arial Unicode MS"]:
        if name in available:
            plt.rcParams["font.sans-serif"] = [name]
            break
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["svg.fonttype"] = "none"
    plt.rcParams["font.size"] = 11


def band_label(tag: str) -> str:
    return tag.replace("band", "").replace("_", "-") + " Hz"


def main() -> None:
    configure_fonts()
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_CSV)
    labels = [band_label(tag) for tag in df["origin_band_tag"].astype(str)]
    x = range(len(df))
    width = 0.36

    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    truth_bars = ax.bar(
        [i - width / 2 for i in x],
        df["truth_overlap_Hz"],
        width,
        label="真实重叠宽度",
        color="#4F81BD",
        edgecolor="#222222",
        linewidth=0.7,
    )
    pred_bars = ax.bar(
        [i + width / 2 for i in x],
        df["pred_overlap_Hz"],
        width,
        label="模型预测值",
        color="#E08A3E",
        edgecolor="#222222",
        linewidth=0.7,
    )

    for bars in [truth_bars, pred_bars]:
        for bar in bars:
            value = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + 0.45,
                f"{value:.1f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

    ax.set_ylabel("目标频带重叠宽度 / Hz")
    ax.set_xticks(list(x), labels, rotation=25, ha="right")
    ax.set_ylim(0, max(df["truth_overlap_Hz"].max(), df["pred_overlap_Hz"].max()) + 6)
    ax.grid(axis="y", alpha=0.28)
    ax.legend(frameon=True, fancybox=False, edgecolor="#333333", loc="upper left")
    fig.tight_layout()

    stem = "figure_5_1_model_truth_vs_prediction_cn_titleless"
    fig.savefig(FIG_DIR / f"{stem}.svg", bbox_inches="tight")
    fig.savefig(FIG_DIR / f"{stem}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(FIG_DIR / f"{stem}.svg")
    print(FIG_DIR / f"{stem}.png")


if __name__ == "__main__":
    main()
