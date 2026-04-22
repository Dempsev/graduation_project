from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_CSV = ROOT / "data" / "analysis" / "canonical_local_robustness_v1" / "canonical_local_robustness_merged_v1.csv"
DEFAULT_OUT_DIR = ROOT / "data" / "analysis" / "canonical_local_robustness_v1" / "plots"

VARIANT_ORDER = [
    "center",
    "a1_plus",
    "a1_minus",
    "a2_plus",
    "a2_minus",
    "b2_plus",
    "b2_minus",
    "r0_plus",
    "r0_minus",
]

VARIANT_LABELS = {
    "center": "center",
    "a1_plus": "a1+",
    "a1_minus": "a1-",
    "a2_plus": "a2+",
    "a2_minus": "a2-",
    "b2_plus": "b2+",
    "b2_minus": "b2-",
    "r0_plus": "r0+",
    "r0_minus": "r0-",
}

FAMILY_COLORS = {
    "center": "#111111",
    "a1": "#1f77b4",
    "a2": "#2ca02c",
    "b2": "#ff7f0e",
    "r0": "#d62728",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot canonical local robustness gap-edge drift figures.")
    parser.add_argument("--input-csv", type=Path, default=DEFAULT_INPUT_CSV)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--dpi", type=int, default=240)
    return parser.parse_args()


def family_of_variant(variant: str) -> str:
    if variant == "center":
        return "center"
    if variant.startswith("a1"):
        return "a1"
    if variant.startswith("a2"):
        return "a2"
    if variant.startswith("b2"):
        return "b2"
    if variant.startswith("r0"):
        return "r0"
    return "center"


def prepare_case(sub: pd.DataFrame) -> pd.DataFrame:
    ordered = sub.copy()
    ordered["variant_order"] = ordered["canonical_variant"].map(
        {name: idx for idx, name in enumerate(VARIANT_ORDER)}
    )
    ordered = ordered.sort_values(["variant_order", "canonical_variant"]).reset_index(drop=True)
    ordered["variant_label"] = ordered["canonical_variant"].map(VARIANT_LABELS).fillna(ordered["canonical_variant"])
    ordered["variant_family"] = ordered["canonical_variant"].map(family_of_variant)
    return ordered


def annotate_failed_points(ax: plt.Axes, x: np.ndarray, sub: pd.DataFrame, y_floor: float) -> None:
    failed = sub["solve_success"].fillna(0).astype(int) == 0
    if not failed.any():
        return
    failed_x = x[failed.to_numpy()]
    ax.scatter(failed_x, np.full_like(failed_x, y_floor), marker="x", color="#d62728", s=48, linewidths=1.4, zorder=5)
    for xi in failed_x:
        ax.text(xi, y_floor, " fail", color="#d62728", fontsize=8, ha="left", va="bottom")


def plot_case(sub: pd.DataFrame, out_path: Path, dpi: int) -> dict[str, object]:
    sub = prepare_case(sub)
    x = np.arange(len(sub), dtype=float)

    target_low = float(sub["target_band_low_Hz"].iloc[0])
    target_high = float(sub["target_band_high_Hz"].iloc[0])
    center_row = sub[sub["canonical_variant"] == "center"].iloc[0]
    center_lower = float(center_row["gap34_lower_edge_Hz"]) if pd.notna(center_row["gap34_lower_edge_Hz"]) else np.nan
    center_upper = float(center_row["gap34_upper_edge_Hz"]) if pd.notna(center_row["gap34_upper_edge_Hz"]) else np.nan

    lowers = pd.to_numeric(sub["gap34_lower_edge_Hz"], errors="coerce").to_numpy(dtype=float)
    uppers = pd.to_numeric(sub["gap34_upper_edge_Hz"], errors="coerce").to_numpy(dtype=float)
    cover = pd.to_numeric(sub["target_cover_ratio_actual"], errors="coerce").fillna(0.0).to_numpy(dtype=float)
    lower_shift = lowers - center_lower
    upper_shift = uppers - center_upper

    fig, (ax_top, ax_bottom) = plt.subplots(
        2,
        1,
        figsize=(10.5, 7.2),
        sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1.2]},
    )

    ax_top.axhspan(target_low, target_high, color="#f1c40f", alpha=0.18, label="target band")
    ax_top.axhline(target_low, color="#c49a00", linestyle="--", linewidth=1.0)
    ax_top.axhline(target_high, color="#c49a00", linestyle="--", linewidth=1.0)

    for i, row in sub.iterrows():
        family = str(row["variant_family"])
        color = FAMILY_COLORS.get(family, "#111111")
        if np.isfinite(lowers[i]) and np.isfinite(uppers[i]):
            ax_top.vlines(x[i], lowers[i], uppers[i], color=color, linewidth=2.0, alpha=0.9, zorder=2)
            ax_top.scatter([x[i]], [lowers[i]], color=color, s=36, zorder=3)
            ax_top.scatter([x[i]], [uppers[i]], color=color, s=36, zorder=3)

    y_floor = min(
        np.nanmin(np.concatenate([lowers[np.isfinite(lowers)], [target_low]])),
        target_low,
    ) - 0.08 * max(1.0, target_high - target_low)
    annotate_failed_points(ax_top, x, sub, y_floor)

    finite_edges = np.concatenate([lowers[np.isfinite(lowers)], uppers[np.isfinite(uppers)], [target_low, target_high]])
    y_pad = max(2.0, 0.08 * (float(np.nanmax(finite_edges)) - float(np.nanmin(finite_edges))))
    ax_top.set_ylim(float(np.nanmin(finite_edges)) - y_pad, max(float(np.nanmax(finite_edges)) + y_pad, y_floor + y_pad))
    ax_top.set_ylabel("Gap edge (Hz)")
    ax_top.grid(True, axis="y", alpha=0.25)
    ax_top.set_title(
        f"{sub['canonical_case_id'].iloc[0]}  |  target={sub['target_band_tag'].iloc[0]}  |  shape={sub['shape_id'].iloc[0]}"
    )

    ax_cover = ax_top.twinx()
    ax_cover.plot(x, cover, color="#7f7f7f", linestyle=":", linewidth=1.2, marker="o", markersize=3.5, alpha=0.8)
    ax_cover.set_ylabel("Cover ratio")
    ax_cover.set_ylim(-0.05, 1.05)

    for i, row in sub.iterrows():
        family = str(row["variant_family"])
        color = FAMILY_COLORS.get(family, "#111111")
        if np.isfinite(lower_shift[i]):
            ax_bottom.scatter([x[i]], [lower_shift[i]], color=color, s=34)
        if np.isfinite(upper_shift[i]):
            ax_bottom.scatter([x[i]], [upper_shift[i]], color=color, s=34, marker="s")
        if np.isfinite(lower_shift[i]) and np.isfinite(upper_shift[i]):
            ax_bottom.vlines(x[i], lower_shift[i], upper_shift[i], color=color, linewidth=1.6, alpha=0.9)

    ax_bottom.axhline(0.0, color="#444444", linestyle="--", linewidth=1.0)
    ax_bottom.grid(True, axis="y", alpha=0.25)
    ax_bottom.set_ylabel("Shift vs center (Hz)")
    ax_bottom.set_xticks(x, sub["variant_label"].tolist(), rotation=0)

    legend_handles = [
        plt.Line2D([0], [0], color=FAMILY_COLORS["center"], marker="o", linewidth=2, label="center"),
        plt.Line2D([0], [0], color=FAMILY_COLORS["a1"], marker="o", linewidth=2, label="a1 perturb"),
        plt.Line2D([0], [0], color=FAMILY_COLORS["a2"], marker="o", linewidth=2, label="a2 perturb"),
        plt.Line2D([0], [0], color=FAMILY_COLORS["b2"], marker="o", linewidth=2, label="b2 perturb"),
        plt.Line2D([0], [0], color=FAMILY_COLORS["r0"], marker="o", linewidth=2, label="r0 perturb"),
        plt.Rectangle((0, 0), 1, 1, fc="#f1c40f", alpha=0.18, label="target band"),
    ]
    ax_top.legend(handles=legend_handles, loc="upper left", fontsize=8, frameon=True)

    fig.tight_layout()
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)

    return {
        "canonical_case_id": str(sub["canonical_case_id"].iloc[0]),
        "target_band_tag": str(sub["target_band_tag"].iloc[0]),
        "shape_id": str(sub["shape_id"].iloc[0]),
        "plot_path": str(out_path),
    }


def plot_overview(df: pd.DataFrame, out_path: Path, dpi: int) -> None:
    case_ids = list(dict.fromkeys(df["canonical_case_id"].astype(str).tolist()))
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), sharex=False, sharey=False)
    axes_flat = axes.flatten()

    for ax, case_id in zip(axes_flat, case_ids):
        sub = prepare_case(df[df["canonical_case_id"].astype(str) == case_id].copy())
        x = np.arange(len(sub), dtype=float)
        target_low = float(sub["target_band_low_Hz"].iloc[0])
        target_high = float(sub["target_band_high_Hz"].iloc[0])
        lowers = pd.to_numeric(sub["gap34_lower_edge_Hz"], errors="coerce").to_numpy(dtype=float)
        uppers = pd.to_numeric(sub["gap34_upper_edge_Hz"], errors="coerce").to_numpy(dtype=float)

        ax.axhspan(target_low, target_high, color="#f1c40f", alpha=0.18)
        ax.axhline(target_low, color="#c49a00", linestyle="--", linewidth=0.9)
        ax.axhline(target_high, color="#c49a00", linestyle="--", linewidth=0.9)

        for i, row in sub.iterrows():
            color = FAMILY_COLORS.get(str(row["variant_family"]), "#111111")
            if np.isfinite(lowers[i]) and np.isfinite(uppers[i]):
                ax.vlines(x[i], lowers[i], uppers[i], color=color, linewidth=1.8)
                ax.scatter([x[i]], [lowers[i]], color=color, s=22)
                ax.scatter([x[i]], [uppers[i]], color=color, s=22)

        failed = sub["solve_success"].fillna(0).astype(int) == 0
        if failed.any():
            y_floor = target_low - 0.12 * max(1.0, target_high - target_low)
            ax.scatter(x[failed.to_numpy()], np.full(failed.sum(), y_floor), marker="x", color="#d62728", s=34, linewidths=1.2)

        ax.set_title(f"{case_id}\n{sub['target_band_tag'].iloc[0]}", fontsize=10)
        ax.set_xticks(x, sub["variant_label"].tolist(), rotation=45, ha="right")
        ax.set_ylabel("Hz")
        ax.grid(True, axis="y", alpha=0.2)

    for ax in axes_flat[len(case_ids):]:
        ax.axis("off")

    fig.tight_layout()
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    input_csv = args.input_csv.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_csv)
    required_columns = {
        "canonical_case_id",
        "canonical_variant",
        "target_band_tag",
        "target_band_low_Hz",
        "target_band_high_Hz",
        "shape_id",
        "solve_success",
        "gap34_lower_edge_Hz",
        "gap34_upper_edge_Hz",
        "target_cover_ratio_actual",
    }
    missing = sorted(required_columns - set(df.columns))
    if missing:
        raise ValueError(f"missing columns in {input_csv}: {missing}")

    plot_records: list[dict[str, object]] = []
    for case_id, sub in df.groupby("canonical_case_id", sort=False):
        case_slug = str(case_id)
        out_path = out_dir / f"{case_slug}_edge_drift_v1.png"
        plot_records.append(plot_case(sub.copy(), out_path, args.dpi))

    overview_path = out_dir / "canonical_local_robustness_edge_drift_overview_v1.png"
    plot_overview(df.copy(), overview_path, args.dpi)

    info = {
        "input_csv": str(input_csv),
        "out_dir": str(out_dir),
        "overview_plot": str(overview_path),
        "case_plots": plot_records,
    }
    (out_dir / "canonical_local_robustness_edge_drift_info_v1.json").write_text(
        json.dumps(info, indent=2),
        encoding="utf-8",
    )
    print(out_dir)


if __name__ == "__main__":
    main()
