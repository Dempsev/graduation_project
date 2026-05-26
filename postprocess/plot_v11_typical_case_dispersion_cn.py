from __future__ import annotations

from pathlib import Path
import re
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from postprocess.tbl1_post_utils import load_tbl1_data

VALIDATION_DIR = ROOT / "data" / "comsol_batch" / "stage4_validation_multiband_predictor_top1_v11_12gen_freeze_v1"
TBL1_DIR = VALIDATION_DIR / "tbl1_exports"
SUMMARY_CSV = ROOT / "data" / "analysis" / "targetband_active_learning_v11_12gen_freeze_v1" / "sixband_predictor_top1_comsol_vs_ga12_summary_v1.csv"
OUT_DIR = ROOT / "data" / "analysis" / "targetband_active_learning_v11_12gen_freeze_v1" / "figures"

PANEL_ORDER = [
    "band140_180",
    "band160_200",
    "band180_220",
    "band200_240",
    "band220_260",
    "band240_280",
]

PANEL_LETTERS = ["a", "b", "c", "d", "e", "f"]


def configure_fonts() -> None:
    available = {font.name for font in font_manager.fontManager.ttflist}
    for name in ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Source Han Sans SC", "Arial Unicode MS"]:
        if name in available:
            plt.rcParams["font.sans-serif"] = [name]
            break
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["svg.fonttype"] = "none"
    plt.rcParams["font.size"] = 9


def parse_band_edges(tag: str) -> tuple[float, float]:
    low, high = tag.replace("band", "").split("_")
    return float(low), float(high)


def band_label(tag: str) -> str:
    low, high = parse_band_edges(tag)
    return f"{int(low)}-{int(high)} Hz"


def tbl1_for_validation(validation_id: str) -> Path:
    matches = sorted(TBL1_DIR.glob(f"*_{validation_id}_tbl1.csv"))
    if not matches:
        raise FileNotFoundError(f"No tbl1 export for {validation_id}")
    return matches[0]


def split_groups(df: pd.DataFrame, low: float, high: float) -> tuple[list[pd.DataFrame], list[pd.DataFrame]]:
    highlight: list[pd.DataFrame] = []
    background: list[pd.DataFrame] = []
    for _, group in df.groupby("band_index", sort=True):
        group = group.sort_values("k").copy()
        if float(group["freq_real"].max()) >= low - 70 and float(group["freq_real"].min()) <= high + 80:
            highlight.append(group)
        else:
            background.append(group)
    return highlight, background


def draw_panel(ax: plt.Axes, row: pd.Series, letter: str) -> None:
    tag = str(row["target_band_tag"])
    low, high = parse_band_edges(tag)
    tbl1_path = tbl1_for_validation(str(row["validation_id"]))
    df, param_name = load_tbl1_data(tbl1_path)
    param_values = sorted(pd.to_numeric(df[param_name], errors="coerce").dropna().unique().tolist())
    sub = df[np.isclose(df[param_name], param_values[0])].copy()

    ax.axhspan(low, high, color="#f2c86b", alpha=0.24, zorder=0)
    ax.axhline(low, color="#c08a00", linestyle="--", linewidth=0.75, alpha=0.95, zorder=1)
    ax.axhline(high, color="#c08a00", linestyle="--", linewidth=0.75, alpha=0.95, zorder=1)

    highlight, background = split_groups(sub, low, high)
    for group in background:
        ax.plot(group["k"], group["freq_real"], color="#b7b7b7", linewidth=0.55, alpha=0.75, zorder=2)
    for group in highlight:
        ax.plot(group["k"], group["freq_real"], color="#1f1f1f", linewidth=1.0, alpha=0.95, zorder=3)

    truth = float(row["predictor_top1_comsol_truth_overlap_Hz"])
    gap_low = float(row["gap34_lower_edge_Hz"])
    gap_high = float(row["gap34_upper_edge_Hz"])
    text_color = "#1f1f1f" if truth > 0 else "#9b2f2f"
    ax.text(
        0.02,
        0.96,
        f"重叠 {truth:.1f} Hz\n带隙 {gap_low:.1f}-{gap_high:.1f} Hz",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        color=text_color,
        bbox=dict(facecolor="white", edgecolor="#cccccc", linewidth=0.5, alpha=0.9),
    )

    shape = re.sub(r"_contour_xy$", "", str(row["shape_id"]))
    ax.set_title(f"({letter}) {band_label(tag)} / {shape}", fontsize=9.5)
    ax.set_xlim(0, 3)
    ax.set_xticks([0, 1, 2, 3], ["Γ", "X", "M", "Γ"])
    ax.set_ylim(80, 360)
    ax.set_ylabel("频率 / Hz")
    ax.grid(axis="y", alpha=0.16)


def main() -> None:
    configure_fonts()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(SUMMARY_CSV)
    df["_order"] = df["target_band_tag"].map({tag: idx for idx, tag in enumerate(PANEL_ORDER)})
    df = df.sort_values("_order").reset_index(drop=True)

    fig, axes = plt.subplots(3, 2, figsize=(8.4, 9.2), sharex=False, sharey=True)
    for ax, (_, row), letter in zip(axes.flatten(), df.iterrows(), PANEL_LETTERS):
        draw_panel(ax, row, letter)
    for ax in axes[-1, :]:
        ax.set_xlabel("波矢路径")

    fig.tight_layout(h_pad=1.7, w_pad=1.0)
    stem = "figure_5_5_v11_typical_case_dispersion_cn_titleless"
    fig.savefig(OUT_DIR / f"{stem}.svg", bbox_inches="tight")
    fig.savefig(OUT_DIR / f"{stem}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(OUT_DIR / f"{stem}.svg")
    print(OUT_DIR / f"{stem}.png")


if __name__ == "__main__":
    main()
