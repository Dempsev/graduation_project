from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from postprocess.tbl1_post_utils import load_tbl1_data


MERGED_CSV = ROOT / "data" / "analysis" / "bilobe_contact_aware_targetband_pilot_v2" / "snake_based_archetype_targetband_pilot_merged_v1.csv"
TBL1_DIR = ROOT / "data" / "comsol_batch" / "stage4_validation_bilobe_contact_aware_targetband_pilot_v2" / "tbl1_exports"
OUT_DIR = ROOT / "data" / "analysis" / "ep17_bilobe_witness_case_v1" / "dispersion"
TARGET_BANDS = ["band200_240", "band220_260", "band240_280"]
TARGET_FILL_COLOR = "#e9c46a"
TARGET_EDGE_COLOR = "#b88700"
HIGHLIGHT_COLOR = "#1d3557"
BACKGROUND_COLOR = "#c6c6c6"
TITLE_MAP = {
    "band200_240": "Target 200-240 Hz",
    "band220_260": "Target 220-260 Hz",
    "band240_280": "Target 240-280 Hz",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot dispersion witness panels for ep17_step156 bilobe case.")
    parser.add_argument("--merged-csv", type=Path, default=MERGED_CSV)
    parser.add_argument("--tbl1-dir", type=Path, default=TBL1_DIR)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--dpi", type=int, default=240)
    return parser.parse_args()


def split_band_groups(sub: pd.DataFrame, target_low: float, target_high: float) -> tuple[list[pd.DataFrame], list[pd.DataFrame]]:
    highlight_groups: list[pd.DataFrame] = []
    background_groups: list[pd.DataFrame] = []
    low = target_low - 90.0
    high = target_high + 110.0

    for _, group in sub.groupby("band_index"):
        group = group.sort_values("k").copy()
        band_min = float(group["freq_real"].min())
        band_max = float(group["freq_real"].max())
        if band_max >= low and band_min <= high:
            highlight_groups.append(group)
        else:
            background_groups.append(group)
    return highlight_groups, background_groups


def sample_id_for_band(merged: pd.DataFrame, band_tag: str) -> str:
    sub = merged[
        (merged["shape_id"].astype(str) == "ep17_step156_contour_xy")
        & (merged["target_band_tag"].astype(str) == band_tag)
    ].copy()
    if sub.empty:
        raise ValueError(f"missing merged row for {band_tag}")
    return str(sub["sample_id"].iloc[0])


def plot_panel(ax: plt.Axes, tbl1_csv: Path, band_tag: str, target_low: float, target_high: float) -> tuple[float, float]:
    df, param_name = load_tbl1_data(tbl1_csv)
    if df.empty:
        raise RuntimeError(f"no valid rows in {tbl1_csv}")
    param_values = sorted(pd.to_numeric(df[param_name], errors="coerce").dropna().unique().tolist())
    if not param_values:
        raise RuntimeError(f"no valid param values in {tbl1_csv}")
    sub = df[np.isclose(df[param_name], param_values[0])].copy()

    ax.axhspan(target_low, target_high, color=TARGET_FILL_COLOR, alpha=0.24, zorder=0)
    ax.axhline(target_low, color=TARGET_EDGE_COLOR, linestyle="--", linewidth=1.0, alpha=0.95, zorder=1)
    ax.axhline(target_high, color=TARGET_EDGE_COLOR, linestyle="--", linewidth=1.0, alpha=0.95, zorder=1)

    highlight_groups, background_groups = split_band_groups(sub, target_low, target_high)
    for group in background_groups:
        ax.plot(group["k"], group["freq_real"], color=BACKGROUND_COLOR, linewidth=0.75, alpha=0.8, zorder=2)
    for group in highlight_groups:
        ax.plot(group["k"], group["freq_real"], color=HIGHLIGHT_COLOR, linewidth=1.55, alpha=0.98, zorder=3)

    ax.set_xlim(0, 3)
    ax.set_xticks([0, 1, 2, 3], ["Gamma", "X", "M", "Gamma"])
    ax.set_xlabel("k")
    ax.set_ylabel("Frequency (Hz)")
    ax.set_title(TITLE_MAP.get(band_tag, band_tag), fontsize=12)
    ax.grid(True, axis="y", alpha=0.16)
    ax.grid(True, axis="x", alpha=0.10)
    return float(sub["freq_real"].min()), float(sub["freq_real"].max())


def main() -> None:
    args = parse_args()
    merged_csv = args.merged_csv.resolve()
    tbl1_dir = args.tbl1_dir.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    merged = pd.read_csv(merged_csv)
    fig, axes = plt.subplots(1, 3, figsize=(15.2, 5.0), sharey=True)
    freq_bounds: list[float] = []
    panel_info: list[dict[str, object]] = []

    for ax, band_tag in zip(axes, TARGET_BANDS):
        band_low, band_high = [float(x) for x in band_tag.replace("band", "").split("_")]
        sample_id = sample_id_for_band(merged, band_tag)
        tbl1_csv = tbl1_dir / f"{sample_id}_tbl1.csv"
        local_min, local_max = plot_panel(ax, tbl1_csv, band_tag, band_low, band_high)
        freq_bounds.extend([local_min, local_max, band_low, band_high])
        row = merged[
            (merged["shape_id"].astype(str) == "ep17_step156_contour_xy")
            & (merged["target_band_tag"].astype(str) == band_tag)
        ].iloc[0]
        panel_info.append(
            {
                "band_tag": band_tag,
                "sample_id": sample_id,
                "tbl1_csv": str(tbl1_csv),
                "target_gap_cover_ratio": float(pd.to_numeric(row["target_gap_cover_ratio"], errors="coerce")),
                "target_gap_overlap_Hz": float(pd.to_numeric(row["target_gap_overlap_Hz"], errors="coerce")),
                "actual_role": str(row["actual_role"]),
            }
        )

    y_min = max(0.0, min(freq_bounds) - 8.0)
    y_max = max(freq_bounds) + 16.0
    for ax in axes:
        ax.set_ylim(y_min, y_max)

    fig.suptitle("ep17_step156 snake-based bilobe witness dispersion", fontsize=14, y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out_path = out_dir / "ep17_bilobe_witness_dispersion_compare_v1.png"
    fig.savefig(out_path, dpi=args.dpi)
    plt.close(fig)

    summary = {
        "merged_csv": str(merged_csv),
        "tbl1_dir": str(tbl1_dir),
        "out_dir": str(out_dir),
        "plot_path": str(out_path),
        "panels": panel_info,
    }
    (out_dir / "ep17_bilobe_witness_dispersion_summary_v1.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(out_dir)


if __name__ == "__main__":
    main()
