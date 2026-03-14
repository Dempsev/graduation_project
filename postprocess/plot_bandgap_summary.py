from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

try:
    from .tbl1_post_utils import project_root
except ImportError:
    from tbl1_post_utils import project_root


def apply_k_path_ticks(ax: plt.Axes, x: pd.Series) -> None:
    if not x.notna().any():
        return

    xmin = float(x.min())
    xmax = float(x.max())
    if xmin <= 1e-9 and xmax >= 3.0 - 1e-9:
        ax.set_xlim(0, 3)
        ax.set_xticks([0, 1, 2, 3], ["Gamma", "X", "M", "Gamma"])
        ax.axvline(1, color="0.8", linewidth=0.8)
        ax.axvline(2, color="0.8", linewidth=0.8)


def plot_bandgap_summary(case_df: pd.DataFrame, fig_dir: Path) -> None:
    for param_name, param_group in case_df.groupby("param_name"):
        width_fig, width_ax = plt.subplots()
        edge_fig, edge_ax = plt.subplots()

        for model_name, model_group in param_group.groupby("model"):
            g = model_group.sort_values("param_value")
            label = model_name if param_group["model"].nunique() > 1 else None

            width_ax.plot(g["param_value"], g["max_gap_Hz"], marker="o", label=label)
            edge_ax.plot(g["param_value"], g["gap_lower_edge_Hz"], marker="o", label=f"{model_name} lower")
            edge_ax.plot(g["param_value"], g["gap_upper_edge_Hz"], marker="o", linestyle="--", label=f"{model_name} upper")

        width_ax.set_xlabel(param_name)
        width_ax.set_ylabel("Bandgap width (Hz)")
        width_ax.set_title(f"Bandgap width vs {param_name}")
        width_ax.grid(True, alpha=0.3)
        if param_group["model"].nunique() > 1:
            width_ax.legend(fontsize=8)
        width_fig.tight_layout()
        width_fig.savefig(fig_dir / f"bandgap_width_vs_{param_name}.png", dpi=300)
        plt.close(width_fig)

        edge_ax.set_xlabel(param_name)
        edge_ax.set_ylabel("Frequency (Hz)")
        edge_ax.set_title(f"Bandgap edges vs {param_name}")
        edge_ax.grid(True, alpha=0.3)
        edge_ax.legend(fontsize=8)
        edge_fig.tight_layout()
        edge_fig.savefig(fig_dir / f"bandgap_edges_vs_{param_name}.png", dpi=300)
        plt.close(edge_fig)


def plot_band_diagrams(out_dir: Path) -> int:
    bands_dir = out_dir / "case_band_tables"
    if not bands_dir.is_dir():
        return 0

    band_fig_dir = out_dir / "plots" / "case_band_diagrams"
    band_fig_dir.mkdir(parents=True, exist_ok=True)

    plotted = 0
    for csv_path in sorted(bands_dir.glob("bands_*.csv")):
        df = pd.read_csv(csv_path)
        if df.empty or "k" not in df.columns:
            continue

        band_cols = [c for c in df.columns if c.startswith("band")]
        if not band_cols:
            continue

        fig, ax = plt.subplots(figsize=(6.4, 4.8))
        x = pd.to_numeric(df["k"], errors="coerce")
        for col in band_cols:
            y = pd.to_numeric(df[col], errors="coerce")
            ax.plot(x, y, color="black", linewidth=0.8, alpha=0.95)

        ax.set_xlabel("k")
        ax.set_ylabel("Frequency (Hz)")
        ax.set_title(csv_path.stem.removeprefix("bands_"))
        apply_k_path_ticks(ax, x)
        ax.grid(True, alpha=0.25)
        fig.tight_layout()
        fig.savefig(band_fig_dir / f"{csv_path.stem}.png", dpi=300)
        plt.close(fig)
        plotted += 1

    return plotted


def main() -> None:
    out_dir = project_root() / "data" / "postprocess_out"
    case_path = out_dir / "bandgap_by_case.csv"
    if not case_path.is_file():
        raise FileNotFoundError(f"summary file not found: {case_path}")

    df = pd.read_csv(case_path)
    if df.empty:
        raise RuntimeError("bandgap_by_case.csv is empty")

    fig_dir = out_dir / "plots"
    fig_dir.mkdir(parents=True, exist_ok=True)

    plot_bandgap_summary(df, fig_dir)
    band_count = plot_band_diagrams(out_dir)

    print(f"[DONE] summary plots written to: {fig_dir}")
    print(f"[DONE] band diagrams written: {band_count}")


if __name__ == "__main__":
    main()
