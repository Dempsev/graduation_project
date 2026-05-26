from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from postprocess.tbl1_post_utils import load_tbl1_data


MERGED_CSV = ROOT / "data" / "analysis" / "canonical_local_robustness_v1" / "canonical_local_robustness_merged_v1.csv"
TBL1_DIR = ROOT / "data" / "comsol_batch" / "stage4_validation_targetband_local_robustness_v1" / "tbl1_exports"
OUT_DIR = ROOT / "data" / "analysis" / "canonical_local_robustness_v1" / "dispersion_plots"

PREFERRED_STABLE_VARIANTS = [
    "b2_plus",
    "b2_minus",
    "a1_plus",
    "a1_minus",
    "a2_plus",
    "a2_minus",
]

PANEL_VARIANTS = ["center", "r0_plus", "r0_minus", "stable"]

PANEL_TITLES = {
    "center": "Center",
    "r0_plus": "r0+",
    "r0_minus": "r0-",
    "stable": "Stable direction",
}

COLORS = {
    "center": "#111111",
    "r0_plus": "#c73e1d",
    "r0_minus": "#e07a5f",
    "stable": "#2a6fdb",
}

BACKGROUND_BAND_COLOR = "#c7c7c7"
TARGET_FILL_COLOR = "#e9c46a"
TARGET_EDGE_COLOR = "#b88700"
TARGET_MARGIN_HZ = 85.0
Y_PAD_BELOW = 95.0
Y_PAD_ABOVE = 135.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot local-robustness dispersion comparisons for canonical cases.")
    parser.add_argument("--merged-csv", type=Path, default=MERGED_CSV)
    parser.add_argument("--tbl1-dir", type=Path, default=TBL1_DIR)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--dpi", type=int, default=240)
    return parser.parse_args()


def tbl1_path_for_sample(tbl1_dir: Path, sample_id: str) -> Path:
    return tbl1_dir / f"{sample_id}_tbl1.csv"


def choose_stable_variant(case_df: pd.DataFrame) -> str:
    candidates = case_df[case_df["canonical_variant"].isin(PREFERRED_STABLE_VARIANTS)].copy()
    if candidates.empty:
        return "a1_plus"

    center = case_df[case_df["canonical_variant"].astype(str) == "center"].copy()
    if center.empty:
        return "a1_plus"
    center_lower = float(pd.to_numeric(center["gap34_lower_edge_Hz"], errors="coerce").iloc[0])
    center_upper = float(pd.to_numeric(center["gap34_upper_edge_Hz"], errors="coerce").iloc[0])

    candidates["solve_success"] = pd.to_numeric(candidates["solve_success"], errors="coerce").fillna(0).astype(int)
    candidates = candidates[candidates["solve_success"] > 0].copy()
    if candidates.empty:
        return "a1_plus"

    lower_edge = pd.to_numeric(candidates["gap34_lower_edge_Hz"], errors="coerce")
    upper_edge = pd.to_numeric(candidates["gap34_upper_edge_Hz"], errors="coerce")
    lower_shift = (lower_edge - center_lower).fillna(np.inf)
    upper_shift = (upper_edge - center_upper).fillna(np.inf)
    cover = pd.to_numeric(candidates.get("target_cover_ratio_actual"), errors="coerce").fillna(0.0)
    candidates["stability_score"] = np.abs(lower_shift) + np.abs(upper_shift) + 0.25 * (1.0 - cover)

    order_map = {name: idx for idx, name in enumerate(PREFERRED_STABLE_VARIANTS)}
    candidates["pref_order"] = candidates["canonical_variant"].map(order_map).fillna(999)
    candidates = candidates.sort_values(["stability_score", "pref_order"]).reset_index(drop=True)
    return str(candidates["canonical_variant"].iloc[0])


def split_band_groups(sub: pd.DataFrame, target_low: float, target_high: float) -> tuple[list[pd.DataFrame], list[pd.DataFrame]]:
    highlight_groups: list[pd.DataFrame] = []
    background_groups: list[pd.DataFrame] = []
    low = target_low - TARGET_MARGIN_HZ
    high = target_high + TARGET_MARGIN_HZ

    for _, group in sub.groupby("band_index"):
        group = group.sort_values("k").copy()
        band_min = float(group["freq_real"].min())
        band_max = float(group["freq_real"].max())
        if band_max >= low and band_min <= high:
            highlight_groups.append(group)
        else:
            background_groups.append(group)
    return highlight_groups, background_groups


def plot_dispersion(ax: plt.Axes, tbl1_csv: Path, color: str, title: str, target_low: float, target_high: float) -> tuple[float, float]:
    df, param_name = load_tbl1_data(tbl1_csv)
    if df.empty:
        raise RuntimeError(f"no valid rows in {tbl1_csv}")

    # For these stage4 exports, each csv normally corresponds to a single case; still keep it generic.
    param_values = sorted(pd.to_numeric(df[param_name], errors="coerce").dropna().unique().tolist())
    if not param_values:
        raise RuntimeError(f"no valid param values in {tbl1_csv}")
    sub = df[np.isclose(df[param_name], param_values[0])].copy()

    ax.axhspan(target_low, target_high, color=TARGET_FILL_COLOR, alpha=0.22, zorder=0)
    ax.axhline(target_low, color=TARGET_EDGE_COLOR, linestyle="--", linewidth=1.0, alpha=0.9, zorder=1)
    ax.axhline(target_high, color=TARGET_EDGE_COLOR, linestyle="--", linewidth=1.0, alpha=0.9, zorder=1)

    highlight_groups, background_groups = split_band_groups(sub, target_low, target_high)

    for group in background_groups:
        ax.plot(group["k"], group["freq_real"], color=BACKGROUND_BAND_COLOR, linewidth=0.75, alpha=0.8, zorder=2)

    for group in highlight_groups:
        ax.plot(group["k"], group["freq_real"], color=color, linewidth=1.55, alpha=0.98, zorder=3)

    ax.set_xlim(0, 3)
    ax.set_xticks([0, 1, 2, 3], ["Gamma", "X", "M", "Gamma"])
    ax.set_xlabel("k")
    ax.set_ylabel("Frequency (Hz)")
    ax.grid(True, axis="y", alpha=0.16)
    ax.grid(True, axis="x", alpha=0.10)
    ax.set_title(title, fontsize=12)
    return float(sub["freq_real"].min()), float(sub["freq_real"].max())


def plot_missing_panel(ax: plt.Axes, title: str, target_low: float, target_high: float, note: str) -> None:
    ax.axhspan(target_low, target_high, color=TARGET_FILL_COLOR, alpha=0.22, zorder=0)
    ax.axhline(target_low, color=TARGET_EDGE_COLOR, linestyle="--", linewidth=1.0, alpha=0.9)
    ax.axhline(target_high, color=TARGET_EDGE_COLOR, linestyle="--", linewidth=1.0, alpha=0.9)
    ax.set_xlim(0, 3)
    ax.set_xticks([0, 1, 2, 3], ["Gamma", "X", "M", "Gamma"])
    ax.set_xlabel("k")
    ax.set_ylabel("Frequency (Hz)")
    ax.set_title(title, fontsize=12)
    ax.grid(True, axis="y", alpha=0.16)
    ax.grid(True, axis="x", alpha=0.10)
    y_mid = 0.5 * (target_low + target_high)
    ax.text(
        1.5,
        y_mid,
        note,
        ha="center",
        va="center",
        fontsize=11,
        color="#c73e1d",
        bbox=dict(boxstyle="round,pad=0.28", facecolor="white", edgecolor="none", alpha=0.9),
    )


def case_variant_row(case_df: pd.DataFrame, variant: str) -> pd.Series | None:
    sub = case_df[case_df["canonical_variant"].astype(str) == variant]
    if sub.empty:
        return None
    return sub.iloc[0]


def make_case_plot(case_df: pd.DataFrame, tbl1_dir: Path, out_path: Path, dpi: int) -> dict[str, object]:
    case_id = str(case_df["canonical_case_id"].iloc[0])
    band_tag = str(case_df["target_band_tag"].iloc[0])
    shape_id = str(case_df["shape_id"].iloc[0])
    target_low = float(case_df["target_band_low_Hz"].iloc[0])
    target_high = float(case_df["target_band_high_Hz"].iloc[0])
    stable_variant = choose_stable_variant(case_df)

    variant_plan = {
        "center": "center",
        "r0_plus": "r0_plus",
        "r0_minus": "r0_minus",
        "stable": stable_variant,
    }

    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.6), sharex=False, sharey=True)
    axes_flat = axes.flatten()

    plotted_variants: list[dict[str, object]] = []
    all_freqs: list[np.ndarray] = []
    pending_panels: list[tuple[plt.Axes, str, str, str]] = []

    for ax, panel_key in zip(axes_flat, PANEL_VARIANTS):
        variant = variant_plan[panel_key]
        row = case_variant_row(case_df, variant)
        panel_title = PANEL_TITLES[panel_key] if panel_key != "stable" else f"Stable: {variant}"
        if row is None:
            pending_panels.append((ax, panel_title, variant, "missing row"))
            continue

        sample_id = str(row["sample_id"])
        solve_success = int(pd.to_numeric(row["solve_success"], errors="coerce")) == 1
        tbl1_csv = tbl1_path_for_sample(tbl1_dir, sample_id)
        if not solve_success:
            pending_panels.append((ax, panel_title, variant, "solve failed"))
            plotted_variants.append({"panel": panel_key, "variant": variant, "status": "solve_failed"})
            continue
        if not tbl1_csv.is_file():
            pending_panels.append((ax, panel_title, variant, "tbl1 missing"))
            plotted_variants.append({"panel": panel_key, "variant": variant, "status": "tbl1_missing"})
            continue

        color = COLORS.get(panel_key, "#111111")
        local_min, local_max = plot_dispersion(ax, tbl1_csv, color, panel_title, target_low, target_high)
        df, param_name = load_tbl1_data(tbl1_csv)
        param_values = sorted(pd.to_numeric(df[param_name], errors="coerce").dropna().unique().tolist())
        sub = df[np.isclose(df[param_name], param_values[0])].copy()
        all_freqs.append(sub["freq_real"].to_numpy(dtype=float))
        all_freqs.append(np.array([local_min, local_max], dtype=float))
        plotted_variants.append({"panel": panel_key, "variant": variant, "status": "ok", "tbl1_csv": str(tbl1_csv)})

    y_min = max(0.0, target_low - Y_PAD_BELOW)
    y_max = target_high + Y_PAD_ABOVE
    if all_freqs:
        concat = np.concatenate(all_freqs)
        finite = concat[np.isfinite(concat)]
        if finite.size > 0:
            y_min = max(0.0, min(target_low - Y_PAD_BELOW, float(np.min(finite)) - 8.0))
            y_max = min(max(target_high + Y_PAD_ABOVE, float(np.max(finite)) + 8.0), target_high + 210.0)

    for ax in axes_flat:
        ax.set_ylim(y_min, y_max)

    for ax, panel_title, variant, note in pending_panels:
        plot_missing_panel(ax, panel_title, target_low, target_high, note)
        ax.set_ylim(y_min, y_max)

    fig.suptitle(f"{case_id}  |  {band_tag}  |  {shape_id}", fontsize=14, y=0.985)
    fig.tight_layout(rect=[0, 0, 1, 0.965])
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)

    return {
        "canonical_case_id": case_id,
        "target_band_tag": band_tag,
        "shape_id": shape_id,
        "stable_variant": stable_variant,
        "plot_path": str(out_path),
        "panels": plotted_variants,
    }


def main() -> None:
    args = parse_args()
    merged_csv = args.merged_csv.resolve()
    tbl1_dir = args.tbl1_dir.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(merged_csv)
    required = {
        "canonical_case_id",
        "canonical_variant",
        "sample_id",
        "shape_id",
        "target_band_tag",
        "target_band_low_Hz",
        "target_band_high_Hz",
        "solve_success",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"missing columns in {merged_csv}: {missing}")

    outputs: list[dict[str, object]] = []
    for case_id, case_df in df.groupby("canonical_case_id", sort=False):
        out_path = out_dir / f"{case_id}_dispersion_compare_v1.png"
        outputs.append(make_case_plot(case_df.copy(), tbl1_dir, out_path, args.dpi))

    info = {
        "merged_csv": str(merged_csv),
        "tbl1_dir": str(tbl1_dir),
        "out_dir": str(out_dir),
        "case_plots": outputs,
    }
    (out_dir / "canonical_local_robustness_dispersion_compare_info_v1.json").write_text(
        json.dumps(info, indent=2),
        encoding="utf-8",
    )
    print(out_dir)


if __name__ == "__main__":
    main()
